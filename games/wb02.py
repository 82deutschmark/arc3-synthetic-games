# Author: GPT-6 Astra Ultra; wind flags by Claude Opus 5.5 High (01-November-2026)
# Date: 27-October-2026 (edited 01-November-2026)
# CHANGELOG: 01-Nov-2026 (Claude Opus 5.5 High) -- no arrows on screen. The three wind arrows are now
#   three flags whose banners stream downwind. Art only; rules and levels unchanged.
# PURPOSE: WB02 native ARC game; boats shelter one another from fixed wind,
# steer to matching docks, and lower sails when handing control away at a dock.
# SRP/DRY check: Pass. Native engine sprites/rendering; one shared transition for
# gameplay and verification; no copied renderer, external assets, or hidden text.
# Updated: 05-November-2026, Claude Fable 5.1 -- the dead tie-breaking loop is gone (one fixed wind can never send two
#   boats to one cell).
# Updated: 06-November-2026, Claude Fable 5.1 -- header chat leftover and an unused 'shelter' switch removed.
from arcengine import ARCBaseGame, Camera, GameAction, Level, Sprite, BlockingMode

DIRECTIONS = ((0, -1), (0, 1), (-1, 0), (1, 0))
COLORS = (12, 6, 14)
ALLOWANCE = 240
SPECS = [
    dict(w=4, h=4, start=(3, 11), goal=(12, 0), rocks=(), wind=(1, 0)),
    dict(w=4, h=4, start=(5, 6), goal=(4, 12), rocks=(9, 13), wind=(1, 0)),
    dict(w=5, h=4, start=(3, 6, 13), goal=(15, 0, 10), rocks=(), wind=(1, 0)),
    dict(w=5, h=4, start=(3, 8, 12), goal=(15, 10, 0), rocks=(6, 7, 16), wind=(1, 0)),
    dict(w=5, h=4, start=(4, 9, 6), goal=(16, 12, 18), rocks=(13, 15, 17), wind=(0, 1)),
    dict(w=5, h=4, start=(13, 12, 4), goal=(4, 9, 19), rocks=(3, 8), wind=(-1, 0)),
    dict(w=5, h=4, start=(10, 5, 14), goal=(2, 17, 16), rocks=(6, 7, 12, 13), wind=(0, -1)),
    dict(w=5, h=4, start=(3, 2, 0), goal=(15, 18, 14), rocks=(6, 7, 11, 12, 16), wind=(-1, 0)),
]


def initial(spec):
    return (tuple(spec['start']), 0, 0)


def xy(spec, cell):
    return cell % spec['w'], cell // spec['w']


def geometry(spec):
    scale = 12 if spec['w'] == 4 else 11
    return scale, (64 - scale * spec['w']) // 2, 8


def screen(spec, cell):
    scale, left, top = geometry(spec)
    x, y = xy(spec, cell)
    return left + scale * x + scale // 2, top + scale * y + scale // 2


def sheltered(spec, positions, moored, boat):
    """An upright sail stops wind along the downstream row or column."""
    x, y = xy(spec, positions[boat])
    dx, dy = spec['wind']
    for other, cell in enumerate(positions):
        if other == boat or moored & (1 << other):
            continue
        a, b = xy(spec, cell)
        if (dx and b == y and (x - a) * dx > 0) or (dy and a == x and (y - b) * dy > 0):
            return True
    return False


def destination(spec, positions, boat, direction):
    dx, dy = direction
    x, y = xy(spec, positions[boat])
    x, y = x + dx, y + dy
    cell = y * spec['w'] + x
    if 0 <= x < spec['w'] and 0 <= y < spec['h'] and cell not in spec['rocks'] and cell not in positions:
        return cell
    return positions[boat]


def advance(spec, state, action):
    """Steer once, then resolve all unheld drift from one post-steering snapshot.

    A hull can enter only an empty snapshot cell: no follow-through, swaps or
    iteration-order effects. Raised sails are evaluated in that same snapshot.
    """
    positions, selected, moored = state
    if action == 5 or action >= 10:
        target = (selected + 1) % len(positions) if action == 5 else action - 10
        if not 0 <= target < len(positions) or target == selected:
            return state
        if positions[selected] == spec['goal'][selected]:
            moored |= 1 << selected
        return positions, target, moored
    if action not in (1, 2, 3, 4):
        return state
    target = destination(spec, positions, selected, DIRECTIONS[action - 1])
    if target == positions[selected]:
        return state
    moved = list(positions)
    moved[selected] = target
    moored &= ~(1 << selected)
    snapshot = tuple(moved)
    proposals = {}
    for boat, cell in enumerate(snapshot):
        if boat == selected or moored & (1 << boat) or sheltered(spec,snapshot,moored,boat):
            continue
        candidate = destination(spec,snapshot,boat,spec['wind'])
        if candidate != cell:
            proposals[boat] = candidate
    # One fixed wind can never send two boats to the same cell, so every proposal stands.
    for boat, candidate in proposals.items():
        moved[boat] = candidate
    return tuple(moved), selected, moored


def won(spec, state):
    return state[0] == tuple(spec['goal'])


def sprite(name, x, y, pixels, layer=3, click=False):
    return Sprite(pixels, name=name, x=round(x), y=round(y), layer=layer,
                  blocking=BlockingMode.NOT_BLOCKED, tags=['sys_click'] if click else [])


def box(name, x, y, width, height, color, layer=0):
    return sprite(name, x, y, [[color] * width for _ in range(height)], layer)


def boat_pixels(boat, lowered=False):
    color = COLORS[boat]
    pixels = [[-1] * 9 for _ in range(9)]
    # Full boat is one rigid sprite: tall mast, triangular sail, gunwale and hull.
    for y in range(6):
        pixels[y][4] = 4
    if not lowered:
        for y in range(1, 6):
            for x in range(4 - min(y, 3), 4):
                pixels[y][8-x if boat == 2 else x] = 11 if boat == 1 else 0
        pixels[3][6 if boat == 2 else 2] = color
        pixels[5][5:8] = [color] * 3
    else:
        pixels[4][2:7] = [0, color, 4, color, 0]
        pixels[5][2:7] = [color] * 5
    pixels[6] = [color, color, color, color, color, color, color, color, color]
    pixels[7] = [-1, color, 4, color, color, color, 4, color, -1]
    pixels[8] = [-1, -1, color, color, color, color, color, -1, -1]
    return pixels


def wind_flag(name, x, y, direction, layer=4):
    """A pole across the wind with a swallow-tailed banner streaming downwind."""
    dx, dy = direction
    pixels = [[-1] * 7 for _ in range(7)]
    def put(along, across, color):
        # along runs pole to tail (0-6) in the wind's direction; across runs along the pole.
        px = 3 + (along-3)*dx + (across-3)*abs(dy)
        py = 3 + (along-3)*dy + (across-3)*abs(dx)
        pixels[py][px] = color
    for across in range(7):
        put(0, across, 0)
    for across in range(4):
        # The notch in the tail keeps the banner from reading as a point.
        for along in range(1, 7 if across in (0, 3) else 5):
            put(along, across, 8)
    return sprite(name, x-3, y-3, pixels, layer)


def picture(spec, state, locations=None, lower_fraction=1, refusal=False):
    positions, selected, moored = state
    scale, left, top = geometry(spec)
    out = []
    for cell in range(spec['w'] * spec['h']):
        x, y = screen(spec, cell)
        if cell in spec['rocks']:
            out.append(box('rock-water-'+str(cell), x-scale//2, y-scale//2, scale, scale, 9))
            pixels = [
                [-1,-1,2,2,2,2,-1,-1,-1],[-1,2,1,1,2,2,2,-1,-1],
                [2,1,1,1,2,2,2,3,-1],[2,1,1,2,2,2,3,3,3],
                [2,2,2,2,2,3,3,3,3],[2,2,2,2,3,3,3,3,3],
                [-1,2,2,3,3,3,3,3,-1],[-1,-1,3,3,3,3,3,-1,-1],
                [-1,-1,-1,10,10,10,-1,-1,-1]]
            out.append(sprite('rock-'+str(cell),x-4,y-4,pixels,3))
            continue
        in_shadow = sheltered(spec, positions + (cell,), moored, len(positions))
        out.append(box('water-'+str(cell), x-scale//2, y-scale//2, scale, scale, 10 if in_shadow else 9))
        # The interrupted water strokes show the movement lattice without a harsh grid.
        out.append(box('ripple-'+str(cell), x-3, y+scale//2-2, 5, 1, 9 if in_shadow else 10, 1))
    for boat, cell in enumerate(spec['goal']):
        x, y = screen(spec, cell)
        color = COLORS[boat]
        # Four broad pilings and a matching hull outline make a berth, not a token.
        out.append(box('dock-'+str(boat)+'-left',x-5,y-4,2,9,color,2))
        out.append(box('dock-'+str(boat)+'-right',x+4,y-4,2,9,color,2))
        out.append(box('dock-'+str(boat)+'-floor',x-4,y+4,8,2,color,2))
        out.append(box('dock-'+str(boat)+'-cap-a',x-5,y-4,2,2,0,3))
        out.append(box('dock-'+str(boat)+'-cap-b',x+4,y-4,2,2,11 if boat==1 else 0,3))
    for boat, cell in enumerate(positions):
        x, y = locations[boat] if locations else screen(spec, cell)
        lowered = bool(moored & (1 << boat))
        pixels = boat_pixels(boat, lowered and lower_fraction >= .5)
        out.append(sprite('boat-'+str(boat),x-4,y-4,pixels,8,True))
        if lowered:
            # Rope and a chunky anchor remain visible beside the furled hull.
            out.append(sprite('anchor-'+str(boat),x-3,y-2,
                              [[-1,0,-1],[-1,0,-1],[0,0,0],[0,0,0]],10))
        if boat == selected:
            color = 8 if refusal else 0
            for sx, sy, width, height in ((-5,-5,3,1),(-5,-5,1,3),(3,-5,3,1),(5,-5,1,3),
                                           (-5,4,1,2),(-5,5,3,1),(5,4,1,2),(3,5,3,1)):
                out.append(box('selected-'+str(sx)+'-'+str(sy)+'-'+str(width),x+sx,y+sy,width,height,color,11))
    # Fixed wind is always shown above the water: the banners stream the way it blows.
    for index in range(3):
        out.append(wind_flag('wind-'+str(index),41+index*8,4,spec['wind']))
    return out


class Wb02(ARCBaseGame):
    def __init__(self):
        self.logical = None
        self.frames = []
        self.history = []
        self.used = 0
        super().__init__(game_id='wb02', levels=[Level(sprites=[],name='stage-'+str(i+1),data={'index':i}) for i in range(len(SPECS))],
                         camera=Camera(background=4), available_actions=[1,2,3,4,5,6,7])

    def on_set_level(self, level):
        self.spec = SPECS[level.get_data('index')]
        self.logical = initial(self.spec)
        self.used = 0
        self.history = []
        self.frames = []
        self.show(picture(self.spec,self.logical))

    def handle_reset(self):
        # Retry the current board even before its first move. A completed game
        # follows the engine's normal full restart so completed-level score is sane.
        if self._score >= len(SPECS):
            self.full_reset()
        else:
            self.level_reset()

    def show(self, sprites):
        self.current_level.remove_all_sprites()
        for item in sprites:
            self.current_level.add_sprite(item)
        for index in range(len(SPECS)):
            self.current_level.add_sprite(box('progress-'+str(index),3+index*4,2,2,3,
                                             14 if index < self.level_index else 0 if index == self.level_index else 3,20))
        # Four visibly distinct rows of sixty dots: every command removes one dot.
        remaining = max(0, ALLOWANCE-self.used)
        for row in range(4):
            pixels = [[14 if row*60+col < remaining else 3 for col in range(60)]]
            self.current_level.add_sprite(sprite('allowance-'+str(row),2,57+row*2,pixels,20))

    def click_action(self, x, y):
        scale, left, top = geometry(self.spec)
        column, row = (x-left)//scale, (y-top)//scale
        if not (0 <= column < self.spec['w'] and 0 <= row < self.spec['h']):
            return 0
        cell = row*self.spec['w']+column
        for boat, position in enumerate(self.logical[0]):
            if cell == position:
                return 10+boat
        return 0

    def animate(self, before, after):
        positions, selected, moored = after
        if before[0] == positions:
            return [picture(self.spec,after,lower_fraction=f) for f in (.25,.75,1)]
        # First the held boat moves; then the wind moves all other whole boats together.
        middle = list(before[0])
        middle[selected] = positions[selected]
        segments = [(before[0],tuple(middle)),(tuple(middle),positions)]
        frames = []
        for start, end in segments:
            if start == end:
                continue
            for fraction in (.5,1):
                locations = []
                for old, new in zip(start,end):
                    x,y = screen(self.spec,old)
                    u,v = screen(self.spec,new)
                    locations.append((x+(u-x)*fraction,y+(v-y)*fraction))
                # At the end of steering the shadow already reflects the new sail.
                shown = (end,selected,moored)
                frames.append(picture(self.spec,shown,locations))
        return frames

    def step(self):
        if self.action.id == GameAction.RESET:
            self.complete_action()
            return
        if not self.frames:
            command = self.action.id.value
            before = self.logical
            if command == 7:
                if self.history:
                    self.logical,self.used = self.history.pop()
                    self.frames = [picture(self.spec,self.logical)]
                else:
                    self.frames = [picture(self.spec,before,refusal=True),picture(self.spec,before)]
            else:
                self.history.append((before,self.used))
                self.used += 1
                if command == 6:
                    command = self.click_action(int(self.action.data.get('x',-1)),int(self.action.data.get('y',-1)))
                self.logical = advance(self.spec,before,command)
                self.frames = self.animate(before,self.logical) if before != self.logical else [picture(self.spec,before,refusal=True),picture(self.spec,before)]
        self.show(self.frames.pop(0))
        if not self.frames:
            if won(self.spec,self.logical):
                self.next_level()
            elif self.used >= ALLOWANCE:
                self.lose()
            self.complete_action()
