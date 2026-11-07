# Author: Claude Sonnet 5.5
# Date: 07-November-2026
# PURPOSE: BL02 is the art redraw of BL01 (fruit ballast, opposite lift pans, recoverable cargo, gravity and crystal
#          lessons). The RULES ARE UNCHANGED: every level's layout, solution, move allowance, inputs, click geometry and
#          win/loss outcome come from BL01's own rule functions, copied unchanged below. Only the pictures are new.
#          Every object on screen is a named engine Sprite with a layer: eight different settings (each with its own
#          sky, hills, earth, props and drifting life), a farmer with a face that blinks, looks the way he walks and
#          cheers or weeps, fruit with leaves, pulleys that turn as the pans move, a pet on the shelf, a burning fuse
#          for the move allowance, a sparkle burst on a won level and a dimmed red run-over look on a lost one.
# SRP/DRY check: Pass. Rule functions (transition, release, interact, ...) are the single source of truth and contain no
#          drawing; picture() reads a state and returns sprites; motion() only interpolates between two pictures.
#          Nothing is shared with bl01.py, which stays as it is.
#
# CHANGELOG
# 07-Nov-2026 (Claude Sonnet 5.5): final polish pass, behaviour still identical to BL01. A lost run now recolours the whole
#          scene to a dim red-and-purple palette (the farmer, rain cloud and frame stay in full colour) instead of only
#          adding the frame and cloud.
# 07-Nov-2026 (Claude Sonnet 5.5): third art pass (variety and life), behaviour still identical to BL01. Trees now lean in
#          the wind; every setting gets its own furniture and small creature (cow, snail, rabbit, hummingbird, geese,
#          campfire and tent, owl, kite and windsock, torches and a spider, fish and an angler, string lights and
#          doves); far mountains; stone-course cave wall and shafts of light in the deep; things buried in the soil of
#          every earth block; a different pan skin per setting; shelf trinkets; sunset and twilight silhouettes
#          recoloured so the scenery shows; a flat scalloped run-over frame instead of the dither; a longer level-clear
#          shower of confetti and ribbons; gloved hands on the cheering farmer.
# 07-Nov-2026 (Claude Sonnet 5.5): second art pass, behaviour still identical to BL01. Hand-drawn scenery per setting (barn and
#          silo, oaks, cherry trees, cottages, firs, rainbow, hot-air balloons, mine timbers, glow caps, waterfall, ferris
#          wheel, bunting); bigger outlined pets whose eyes follow the farmer; a wider farmer who throws his arms up on a
#          win; a clearer run-over look (frame closing in, weeping farmer left clear, rain cloud); a wooden beam behind the
#          level pips; less pink; drifting life with real frames (bees, kite, jellyfish, smoke, lantern).
# 07-Nov-2026 (Claude Sonnet 5.5): first version of the redraw; behaviour identical to BL01.
"""Opaque game BL02. Human review remains pending."""

from arcengine import ARCBaseGame, Camera, GameAction, Level, Sprite, BlockingMode
import math

AUTHOR = "Claude Sonnet 5.5"
WIDTH = 7
HEIGHT = 6
CELL = 8
AVAILABLE = [1, 2, 3, 4, 5, 6, 7]


def level_spec(start=(1, 4), basket=(0, 4), fruits=((2, 1),), weights=(2,),
               walls=((2, 2),), pairs=((3, 6, 2, 5, 0, 2),), heights=(3,),
               gravity=False, crystals=(), lever=None, bank=0, polarity=0):
    return dict(start=start, basket=basket, fruits=fruits, weights=weights,
                walls=tuple((x, 5) for x in range(WIDTH)) + tuple(walls),
                pairs=pairs, heights=heights, gravity=gravity, crystals=crystals,
                lever=lever, bank=bank, polarity=polarity, budget=320)


SPECS = [
    level_spec(),
    level_spec(fruits=((2, 1), (4, 1)), weights=(2, 2), walls=((2, 2), (4, 2))),
    level_spec(start=(2, 2), basket=(3, 2), fruits=((0, 4), (5, 2)), weights=(2, 2),
               walls=((2, 3), (4, 4), (5, 4)), heights=(1,), bank=1),
    level_spec(fruits=((1, 0), (5, 1)), weights=(2, 2), gravity=True,
               walls=((1, 1), (5, 2))),
    level_spec(fruits=((2, 1), (5, 0), (6, 4)), weights=(2, 3, 2),
               gravity=True, walls=((2, 2), (5, 1))),
    level_spec(fruits=((2, 1), (5, 3)), weights=(2, 2),
               walls=((2, 2), (4, 4), (5, 4)), crystals=((4, 3),), lever=(2, 4), polarity=1),
    level_spec(fruits=((2, 0), (4, 2), (6, 4)), weights=(2, 3, 2),
               gravity=True, walls=((2, 1), (4, 3)),
               crystals=((4, 4), (5, 2)), lever=(2, 4), polarity=1),
    level_spec(start=(1, 4), basket=(0, 1),
               fruits=((2, 1), (4, 0), (6, 3)), weights=(2, 3, 2),
               gravity=True, walls=((0, 2), (1, 2), (2, 2), (4, 1), (6, 4)),
               crystals=((4, 3), (5, 4), (6, 3)), lever=(2, 4), polarity=1),
]


def initial(spec):
    return (spec['start'], 1, tuple(spec['heights']), -1, spec['bank'], spec['polarity'])


def cell_xy(cell):
    return (4 + cell[0] * CELL, 8 + cell[1] * CELL)


def near(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) <= 1


def pans(spec, heights):
    result = []
    for height, (left, right, top, bottom, _, _) in zip(heights, spec['pairs']):
        result.extend(((left, top + height), (right, bottom - height)))
    return tuple(result)


def solid(spec, cell, heights, polarity):
    x, y = cell
    return (not (0 <= x < WIDTH and 0 <= y < HEIGHT) or cell in spec['walls']
            or cell in pans(spec, heights) or bool(polarity and cell in spec['crystals']))


def settle(spec, at, gravity, heights, polarity):
    path = []
    while not solid(spec, (at[0], at[1] + gravity), heights, polarity):
        at = (at[0], at[1] + gravity)
        path.append(at)
    return at, path


def interact(spec, state):
    at, gravity, heights, carry, bank, polarity = state
    if carry >= 0 and near(at, spec['basket']):
        return (at, gravity, heights, -1, bank | (1 << carry), polarity), []
    if carry < 0:
        for index, fruit in enumerate(spec['fruits']):
            if not bank & (1 << index) and near(at, fruit) and not (polarity and fruit in spec['crystals']):
                return (at, gravity, heights, index, bank, polarity), []
        if near(at, spec['basket']) and bank:
            # With one hand, take the largest available ballast first. The broad
            # fruit slots also let the player choose a particular banked fruit.
            index = max((i for i in range(len(spec['fruits'])) if bank & (1 << i)),
                        key=lambda i: (spec['weights'][i], -i))
            return (at, gravity, heights, index, bank ^ (1 << index), polarity), []
    if spec['lever'] is not None and near(at, spec['lever']):
        new = 1 - polarity
        if new and (at in spec['crystals'] or any(c in spec['crystals'] for c in pans(spec, heights))):
            return state, []
        after, path = settle(spec, at, gravity, heights, new)
        return (after, gravity, heights, carry, bank, new), path
    return release(spec, state)


def release(spec, state):
    at, gravity, heights, carry, bank, polarity = state
    old_pans = pans(spec, heights)
    support = (at[0], at[1] + gravity)
    # The farmer counts as one block; fruit adds two or three visible blocks.
    body = gravity * (1 + (spec['weights'][carry] if carry >= 0 else 0))
    new_heights = list(heights)
    for index, (_, _, top, bottom, left_weight, right_weight) in enumerate(spec['pairs']):
        left_weight += body if support == old_pans[2 * index] else 0
        right_weight += body if support == old_pans[2 * index + 1] else 0
        change = (left_weight > right_weight) - (left_weight < right_weight)
        new_heights[index] = max(0, min(bottom - top, heights[index] + change))
    new_heights = tuple(new_heights)
    new_pans = pans(spec, new_heights)
    if any(c in spec['crystals'] for c in new_pans) and polarity:
        return state, []
    # A pan may rest on the ground; it cannot travel through a higher shelf.
    if any(c in spec['walls'] and c[1] < 5 for c in new_pans):
        return state, []
    path = []
    if support in old_pans:
        index = old_pans.index(support)
        at = (at[0], at[1] + new_pans[index][1] - old_pans[index][1])
        path.append(at)
    if solid(spec, at, new_heights, polarity):
        return state, []
    at, fall = settle(spec, at, gravity, new_heights, polarity)
    return (at, gravity, new_heights, carry, bank, polarity), path + fall


def transition(spec, state, command):
    at, gravity, heights, carry, bank, polarity = state
    if isinstance(command, (list, tuple)):
        _, x, y = command
        if 52 <= y <= 60 and carry < 0 and near(at, spec['basket']):
            index = (x - 5) // 9
            if 0 <= index < len(spec['fruits']) and bank & (1 << index):
                return (at, gravity, heights, index, bank ^ (1 << index), polarity), []
        # Clicks select the pictured object; nearby keyboard priority cannot
        # redirect a basket click to a different fruit or switch.
        def hit(cell):
            return (near(at, cell) and abs(x - cell_xy(cell)[0] - 4) <= 4
                    and abs(y - cell_xy(cell)[1] - 4) <= 4)
        if hit(spec['basket']):
            if carry >= 0:
                return (at, gravity, heights, -1, bank | (1 << carry), polarity), []
            if bank:
                index = max((i for i in range(len(spec['fruits'])) if bank & (1 << i)),
                            key=lambda i: (spec['weights'][i], -i))
                return (at, gravity, heights, index, bank ^ (1 << index), polarity), []
            return state, []
        for index, cell in enumerate(spec['fruits']):
            if hit(cell) and carry < 0 and not bank & (1 << index):
                if polarity and cell in spec['crystals']:
                    return state, []
                return (at, gravity, heights, index, bank, polarity), []
        if spec['lever'] is not None and hit(spec['lever']):
            new = 1 - polarity
            if new and (at in spec['crystals'] or any(c in spec['crystals'] for c in pans(spec, heights))):
                return state, []
            after, path = settle(spec, at, gravity, heights, new)
            return (after, gravity, heights, carry, bank, new), path
        if abs(x - cell_xy(at)[0] - 4) <= 6 and abs(y - cell_xy(at)[1] - 4) <= 6:
            return release(spec, state)
        return state, []
    if command == 1:
        if not spec['gravity']:
            return state, []
        gravity = -gravity
        at, path = settle(spec, at, gravity, heights, polarity)
        return (at, gravity, heights, carry, bank, polarity), path
    if command == 2:
        return release(spec, state)
    if command in (3, 4):
        target = (at[0] + (-1 if command == 3 else 1), at[1])
        if solid(spec, target, heights, polarity):
            return state, []
        if not solid(spec, (target[0], target[1] + gravity), heights, polarity):
            return state, []
        at, path = settle(spec, target, gravity, heights, polarity)
        return (at, gravity, heights, carry, bank, polarity), [target] + path
    if command == 5:
        return interact(spec, state)
    return state, []


def advance(spec, state, command):
    return transition(spec, state, command)[0]


def won(spec, state):
    return state[3] < 0 and state[4] == (1 << len(spec['fruits'])) - 1


# Which level a spec belongs to (the art picks its setting by this); the rule functions never look at it.
for _index, _spec in enumerate(SPECS):
    _spec['level'] = _index

# ───────────────────────── drawing kit: colours, letter-art, small helpers ─────────────────────────
# The 16 ARC colours by name. Greys (1-4) are never used.
WHT, BLK, MAG, PNK, RED, BLU, LBL, YEL, ORG, MAR, GRN, PUR = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
# One letter per colour so pictures can be read in the source. '.' is transparent.
LETTER = {'.': -1, 'w': 0, 'k': 5, 'M': 6, 'p': 7, 'r': 8, 'b': 9, 'l': 10, 'y': 11, 'o': 12, 'm': 13, 'g': 14, 'u': 15}


def art(rows, own=None):
    """Letters to colour indexes. `own` adds letters that belong to one picture (a pet's fur, a tile's accent)."""
    table = dict(LETTER)
    table.update(own or {})
    for row in rows:
        assert len(row) == len(rows[0]), (row, len(rows[0]))
    return [[table[ch] for ch in row] for row in rows]


def mirror(grid):
    return [row[::-1] for row in grid]


def canvas(width, height, fill=-1):
    return [[fill] * width for _ in range(height)]


def paste(grid, x, y, src):
    """Copy the opaque pixels of `src` onto `grid` (clipped at the edges)."""
    for dy, row in enumerate(src):
        for dx, value in enumerate(row):
            if value >= 0 and 0 <= y + dy < len(grid) and 0 <= x + dx < len(grid[0]):
                grid[y + dy][x + dx] = value


def disc(radius, fill, rim=None):
    size = radius * 2 + 1
    grid = canvas(size, size)
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - radius, y - radius)
            if d <= radius + 0.3:
                grid[y][x] = rim if (rim is not None and d > radius - 0.7) else fill
    return grid


def sprite(name, grid, x, y, layer, tags=()):
    return Sprite(grid, name=name, x=round(x), y=round(y), layer=layer,
                  blocking=BlockingMode.NOT_BLOCKED, tags=list(tags))


def block(name, x, y, width, height, color, layer=1):
    return Sprite([[color] * width for _ in range(height)], name=name,
                  x=round(x), y=round(y), layer=layer, blocking=BlockingMode.NOT_BLOCKED)


def hashed(a, b=0, salt=0):
    """A small repeatable scatter so decorations are not on a grid, without any random state."""
    return ((a * 73856093) ^ (b * 19349663) ^ (salt * 83492791)) % 1000


# Layers, low to high: backdrop 0-5, earth 6-7, rails and ropes 8-10, pans 11, basket/switch 12, farmer 14, fruit 15,
# crystals that hold a fruit 16, effects 18, shelf and its fittings 20-23, dim and refusal flashes 24-25.
L_EARTH, L_GUIDE, L_ROPE, L_PULLEY, L_PAN, L_STAND, L_FARMER, L_FRUIT, L_GLASS, L_FX = 6, 8, 9, 10, 11, 12, 14, 15, 16, 18

# ───────────────────────── the farmer ─────────────────────────
FARMER = ['..kkkkkk..', '.kyyyyyyk.', 'kyyrrrryyk', '.kppppppk.', '.kppppppk.',
          'prrrrrrrrp', '.rbbyybbr.', '..bbbbbb..', '.kkk..kkk.']
FARMER_STEP = '..kkk.kkk.'


def farmer_grid(mood='idle', face=0, blink=False, step=False, hanging=False):
    """10x9 farmer: straw hat with a red band and a wide brim, a face with eyes that look the way he walks, a red shirt
    with hands, dungarees with buttons and boots. On a win both arms go up; on a loss the tears fall and the mouth
    droops. `hanging` turns him over for the flipped-gravity levels. face: -1 looks left, 0 front, 1 right."""
    rows = [list(r) for r in FARMER]
    if step:
        rows[8] = list(FARMER_STEP)
    eye_at = {-1: (2, 5), 0: (3, 6), 1: (4, 7)}[face]
    for ex in eye_at:
        rows[3][ex] = 'p' if (blink and mood != 'sad') else 'k'
    if mood == 'happy':
        rows[4][4] = rows[4][5] = 'r'
        rows[4][3] = rows[4][6] = 'k'
        rows[3][2] = rows[3][7] = 'M'            # blush
        for x in (0, 9):                          # both arms thrown up, with yellow gloves held high
            rows[5][x] = 'r'
            rows[4][x] = 'r'
            rows[3][x] = 'p'
            rows[2][x] = 'p'
            rows[1][x] = 'y'
            rows[0][x] = 'y'
    elif mood == 'sad':
        rows[4][4] = rows[4][5] = 'k'
        rows[4][3] = rows[4][6] = 'p'
        rows[3][3 if face >= 0 else 2] = 'k'
        rows[4][2] = rows[4][7] = '9'             # tears
        rows[3][1] = rows[3][8] = 'p'
        rows[5][0] = rows[5][9] = 'r'
    else:
        rows[4][4] = rows[4][5] = 'k'
        rows[4][3] = rows[4][6] = 'p'
    grid = art([''.join(r) for r in rows], own={'9': BLU})
    return grid[::-1] if hanging else grid


# ───────────────────────── fruit: an apple (light) and a pumpkin (heavy) ─────────────────────────
APPLE = ['...mg..', '.88m88.', '8w88888', '8w88888', '8888888', '.88888m', '..mmm..']
APPLE_B = ['..gmg..', '.88m88.', '8w88888', '8w88888', '8888888', '.88888m', '..mmm..']   # leaf lifted
GOURD = ['...gg..', '.ooyoo.', 'oyooMoo', 'oyooMoo', 'oooMooo', '.ooMomo', '..mmm..']
GOURD_B = ['..ggg..', '.ooyoo.', 'oyooMoo', 'oyooMoo', 'oooMooo', '.ooMomo', '..mmm..']


def fruit_grid(weight, beat=0):
    rows = (APPLE if beat % 2 == 0 else APPLE_B) if weight == 2 else (GOURD if beat % 2 == 0 else GOURD_B)
    # 'M' is the gourd's ridge: maroon; the apple has none
    return art(rows, own={'M': MAR, '8': RED})


# ───────────────────────── the basket ─────────────────────────
BASKET = ['..yyyy..', '.y....y.', '.y....y.', 'kyyyyyyk', 'komomomk', 'kmomomok', '.kmomok.', '..kkkk..']


def basket_grid(peek):
    """The wicker basket; `peek` is a list of colours of the fruit tucked in (shows through the top)."""
    grid = art(BASKET)
    spots = [(2, 1), (3, 2), (4, 1), (5, 2)]
    for colour, (x, y) in zip(peek, spots):
        grid[y][x] = colour
    return grid


# ───────────────────────── pans, weights, pulleys, crystals, switch ─────────────────────────
PAN = ['kyyyyyyk', 'k' + 'o' * 6 + 'k', '.kmmmmk.', '..kkkk..']
WEIGHT = ['pM', 'MM', 'MM']        # magenta ballast blocks with a pink top (never white dots: they read as eyes)


def pulley_grid(turn):
    """4x4 wheel; the spoke flips with the pan's height so it looks like it turns when the pan moves."""
    spokes = ['kkkk', 'kyok', 'kkyk', 'kkkk'] if turn % 2 else ['kkkk', 'koyk', 'kyok', 'kkkk']
    return [[-1 if (x in (0, 3) and y in (0, 3)) else art([spokes[y]])[0][x] for x in range(4)] for y in range(4)]


CRYSTAL_ON = ['kllllllk', 'lwwbbbbk', 'lwbbbbbk', 'lbbbbwbk', 'lbbbbbbk', 'lbbbwbbk', 'lbbbbbbk', 'kbbbbbbk']
CRYSTAL_SHINE = ['kllllllk', 'lwbbbbbk', 'lbbbbbbk', 'lbbbbbbk', 'lbbbbbwk', 'lbbbbwwk', 'lbbbbbbk', 'kbbbbbbk']


def crystal_grid(active, holds_fruit, beat):
    """Active: a solid blue gem block. Inactive: only dotted corners (the original ghost), with a slow twinkle."""
    grid = canvas(8, 8)
    if active:
        grid = art(CRYSTAL_ON if beat % 6 < 3 else CRYSTAL_SHINE)
        if holds_fruit:        # a fruit is trapped inside: keep only the glassy frame so it can be seen
            for y in range(1, 7):
                for x in range(1, 7):
                    grid[y][x] = -1
            for i in range(1, 7):
                grid[1][i] = grid[6][i] = LBL
                grid[i][1] = grid[i][6] = LBL
            grid[1][1] = WHT
            grid[2][1] = WHT
    else:
        for y in range(8):
            for x in range(8):
                if (x + y) % 4 == 0 and (x in (0, 7) or y in (0, 7)):
                    grid[y][x] = LBL
        if beat % 8 < 2:
            grid[3][3] = WHT
        elif beat % 8 < 4:
            grid[4][4] = LBL
    return grid


def switch_grid(on, beat):
    """Pedestal with a crystal orb. The orb glows when the gems are solid. The slider knob is a separate sprite."""
    orb = ['..ww..', '.wllw.', '.lbbl.', '..ll..'] if on else ['..kk..', '.kbbk.', '.kbbk.', '..kk..']
    grid = canvas(8, 8)
    paste(grid, 1, 0, art(orb))
    for y in range(4, 6):
        grid[y][3] = ORG
        grid[y][4] = YEL
    for x in range(8):
        grid[6][x] = MAR if 0 < x < 7 else -1
        grid[7][x] = BLK if 0 < x < 7 else -1
    for y in range(1, 7):             # the slot the knob rides in
        grid[y][6] = BLK
    if on and beat % 4 < 2:
        grid[0][5] = WHT
    return grid


# ───────────────────────── small decorations used by several settings ─────────────────────────
STAR_BIG = ['..y..', '..y..', 'yywyy', '..y..', '..y..']
STAR_SMALL = ['.y.', 'yyy', '.y.']
CLOUD = ['....www.......', '..wwwwwww.ww..', '.wwwwwwwwwwwww', 'wwwwwwwwwwwwww', '.SSSSSSSSSSSS.']
BIRD = [['k...k', '.k.k.', '..k..'], ['..k..', '.kkk.', 'k...k']]
BUTTERFLY = [['p.p', '.k.', 'p.p'], ['...', 'pkp', '...']]
BAT = [['kk...kk', 'kkkkkkk', '.kwkwk.', '..k.k..'], ['.......', '.kkkkk.', 'kkwkwkk', 'k.k.k.k']]
GEM = ['..w..', '.pMp.', 'pMwMp', '.pMp.', '..p..']


# ───────────────────────── the pets that sit on the shelf (one per setting) ─────────────────────────
# Each is drawn 12x9 and then given a black outline (so no fur colour can melt into the planks), which makes 14x11.
# Eyes are stamped on afterwards at the two anchors (3x2 each, a white eye with a black pupil that follows the farmer,
# shut on a blink, with tears on a loss); the mouth is stamped at `mouth`. Rows keep the fur colour under both.
PETS = [
    dict(name='hen', own={'f': WHT, 's': RED, 'n': ORG, 'd': YEL}, eyes=((2, 3), (7, 3)), mouth=None, fur=WHT,
         rows=['....ssss....', '...ssssss...', '..ffffffff..', '.ffffffffff.', '.ffffffffff.', '.ffffnnffff.',
               'ffffnnsnffff', 'ffffffffffff', '.ff.dd.dd.ff'[:12]]),
    dict(name='cat', own={'f': ORG, 'd': MAR, 'c': WHT, 'n': MAG}, eyes=((2, 3), (7, 3)), mouth=(5, 6), fur=ORG,
         rows=['ff........ff', 'fdf......fdf', '.ffffffffff.', 'ffffffffffff', 'ffffffffffff', 'fdffffnnffdf',
               '.ffcccccffff'[:12], '.fcccccccff.', '.ff.fff.fff.']),
    dict(name='dog', own={'f': YEL, 'd': MAR, 'c': WHT, 'n': BLK}, eyes=((2, 3), (7, 3)), mouth=(5, 6), fur=YEL,
         rows=['.dd......dd.', 'ddf.ffff.fdd', 'ddffffffffdd', 'ddffffffffdd', 'dfffffffffdd'[:12], '.fffffnnffff'[:12],
               '.ffccccccff.', '.fcccccccff.', '.ff.fff.fff.']),
    dict(name='owl', own={'f': PUR, 'd': MAG, 'c': WHT, 'n': ORG, 'e': YEL}, eyes=((2, 3), (7, 3)), mouth=None, fur=YEL,
         rows=['d..........d', 'dd........dd', '.ffffffffff.', '.eeeffffeee.', '.eeefnnfeee.', '.ffffnnffff.',
               'ffccccccccff', 'fcccdcdcdcff', '.ff.nn.nn.ff']),
    dict(name='pig', own={'f': PNK, 'd': MAG, 'c': PNK, 'n': MAG}, eyes=((2, 3), (7, 3)), mouth=(5, 7), fur=PNK,
         rows=['dd........dd', 'dfd......dfd', '.ffffffffff.', 'ffffffffffff', 'ffffffffffff', 'fffnnnnnnfff',
               '.ffnfnnfnff.', '.ffnnnnnnff.', '.ff..ff..ff.']),
    dict(name='mole', own={'f': MAR, 'n': PNK, 'a': ORG, 'd': PUR}, eyes=((2, 3), (7, 3)), mouth=(5, 7), fur=MAR,
         rows=['..ffffffff..', '.ffffffffff.', 'ffffffffffff', 'ffffffffffff', 'ffffffffffff', 'fffffnnfffff',
               '.fffnnnnfff.', '.nnfffffffnn', 'nanf....fnan']),
    dict(name='frog', own={'f': GRN, 'c': YEL, 'a': MAR, 'd': PUR}, eyes=((1, 1), (8, 1)), mouth=(4, 5), fur=GRN,
         rows=['.fff....fff.', 'ffffffffffff', 'ffffffffffff', 'ffffffffffff', 'fdffffffffdf', 'ffffffffffff',
               '.fccccccccf.', '.fccccccccf.', 'ff..ffff..ff']),
    dict(name='bunny', own={'f': WHT, 'n': PNK, 'c': WHT, 'a': MAR}, eyes=((2, 3), (7, 3)), mouth=(5, 6), fur=WHT,
         rows=['.ff......ff.', '.fn......nf.', '.fn......nf.', 'ffffffffffff', 'ffffffffffff', 'ffffffnnffff'[:12],
               '.fffccccfff.', '.ffffffffff.', '.ff.ffff.ff.']),
]
for _pet in PETS:
    for _row in _pet['rows']:
        assert len(_row) == 12, (_pet['name'], _row)


def outlined(grid):
    """Wrap every opaque pixel in a black outline: a character is always readable against any background."""
    h, w = len(grid), len(grid[0])
    out = canvas(w + 2, h + 2)
    for y in range(h):
        for x in range(w):
            if grid[y][x] >= 0:
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
                    if out[y + 1 + dy][x + 1 + dx] < 0:
                        out[y + 1 + dy][x + 1 + dx] = BLK
    for y in range(h):
        for x in range(w):
            if grid[y][x] >= 0:
                out[y + 1][x + 1] = grid[y][x]
    return out


def pet_sprite(index, mood, blink, tick, face=0):
    """The pet on the shelf: its eyes follow the farmer, it blinks, hops for joy on a win and weeps on a loss."""
    pet = PETS[index]
    grid = art(pet['rows'], own=pet['own'])
    for ex, ey in pet['eyes']:
        shut = blink and mood != 'sad'
        for dy in range(2):
            for dx in range(3):
                grid[ey + dy][ex + dx] = pet['fur'] if (shut and dy == 0) else WHT if not (shut and dy == 1) else BLK
        if not shut:
            px = ex + (0 if face < 0 else 2 if face > 0 else 1)
            grid[ey][px] = grid[ey + 1][px] = BLK
        if mood == 'sad':
            grid[ey + 2][ex + 1] = BLU
            grid[ey + 3][ex + 1] = BLU
            grid[ey - 1][ex + (2 if ex < 6 else 0)] = BLK        # brows slanting down toward the middle
    if pet['mouth']:
        mx, my = pet['mouth']
        if mood == 'happy':
            grid[my][mx] = grid[my][mx + 1] = RED
            grid[my][mx - 1] = grid[my][mx + 2] = BLK
        elif mood == 'sad':
            grid[my][mx] = grid[my][mx + 1] = BLK
            grid[my + 1][mx - 1] = grid[my + 1][mx + 2] = BLK
        else:
            grid[my][mx] = grid[my][mx + 1] = BLK
    bob = -3 if mood == 'happy' and tick % 2 else -1 if (mood == 'idle' and tick // 5 % 4 == 0) else 0
    return sprite('pet', outlined(grid), 44, 50 + bob, 22)


# ───────────────────────── the eight settings ─────────────────────────
# sky: horizontal bands (last row, colour); hills: (colour, base row, height, wavelength, phase) far to near;
# soil/speck/grass/bloom: the earth tiles; shelf: (plank, seam); margin: the 4-pixel strips left and right of the board;
# pet: index in PETS; ambient: names of the drifting life, drawn by ambient().
THEMES = [
    dict(key='meadow', sky=((8, BLU), (34, LBL), (64, LBL)), hills=((PUR, 38, 8, 24.0, 0.6), (GRN, 44, 4, 20.0, 1.9)),
         soil=MAR, speck=ORG, grass=GRN, bloom=YEL, shelf=(ORG, MAR), margin='vine', pet=0, shade=LBL,
         ambient=('clouds', 'birds', 'butterflies'), props=('sun',)),
    dict(key='blossom', sky=((14, BLU), (64, LBL)), hills=((PUR, 37, 7, 28.0, 0.4), (GRN, 43, 4, 16.0, 1.2)), soil=MAR,
         speck=ORG, grass=GRN, bloom=WHT, shelf=(GRN, MAR), margin='trunk', pet=1, shade=LBL,
         ambient=('petals', 'butterflies', 'bees', 'clouds', 'smoke'), props=()),
    dict(key='sunset', sky=((12, PUR), (22, MAG), (36, ORG), (64, YEL)), hills=((PUR, 40, 6, 28.0, 0.3), (BLU, 45, 3, 30.0, 0.0)),
         soil=MAR, speck=ORG, grass=GRN, bloom=WHT, shelf=(MAR, BLK), margin='reed', pet=2, shade=MAG,
         ambient=('windmill', 'birds', 'clouds', 'smoke'), props=('sunset',)),
    dict(key='twilight', sky=((12, PUR), (28, BLU), (64, LBL)), hills=((BLU, 37, 7, 26.0, 1.0), (GRN, 45, 3, 18.0, 0.4)), soil=MAR, speck=ORG,
         grass=GRN, bloom=YEL, shelf=(MAR, BLK), margin='vine', pet=3, shade=MAG,
         ambient=('stars', 'fireflies', 'smoke'), props=('moon',)),
    dict(key='balloons', sky=((12, BLU), (64, LBL)), hills=((WHT, 43, 5, 10.0, 0.5),), soil=MAR, speck=ORG,
         grass=GRN, bloom=YEL, shelf=(BLU, BLK), margin='puff', pet=4, shade=LBL,
         ambient=('airships', 'clouds', 'birds', 'smoke'), props=()),
    dict(key='cave', sky=((64, PUR),), floor='cave', hills=((MAR, 45, 5, 12.0, 0.3),), soil=MAR, speck=ORG,
         grass=GRN, bloom=YEL, shelf=(MAR, BLK), margin='rock', pet=5, shade=PUR,
         ambient=('bats', 'fireflies', 'gleam', 'lantern'), props=('spikes-dark',)),
    dict(key='deep', sky=((64, BLK),), floor='deep', hills=((PUR, 38, 9, 18.0, 0.2), (BLK, 46, 4, 7.0, 1.4)), soil=MAR, speck=ORG,
         grass=GRN, bloom=YEL, shelf=(PUR, BLK), margin='rock', pet=6, shade=BLK,
         ambient=('waterfall', 'jellies', 'glow', 'gleam'), props=('spikes-purple',)),
    dict(key='festival', sky=((10, BLK), (30, BLU), (64, BLU)), hills=((PUR, 41, 3, 30.0, 0.0),), soil=MAR, speck=ORG,
         grass=GRN, bloom=YEL, shelf=(MAR, BLK), margin='rock', pet=7, shade=BLU,
         ambient=('ferris', 'fireworks', 'stars', 'windows'), props=('town',)),
]

SMOKE_AT = {'blossom': (56, 35), 'sunset': (16, 33), 'twilight': (31, 32), 'balloons': (55, 34)}

# ───────────────────────── pass three, part two: what is buried in the earth, how the pans look, far mountains ─────────────────────────
# Small pictures pressed into the soil of every earth block, so the big maroon surfaces are not blank. Each setting
# digs up its own things: roots and pebbles in the meadow, bulbs under the blossom, embers at sunset, ore in the mine,
# shells and starfish in the deep, sweets at the fair. `own` recolours a letter for that setting.
MOTIFS = {
    'meadow': [(['.w.', 'www'], {}), (['g..', '.gg', '..g'], {}), (['y.y', '.y.'], {}), (['.pp.', 'pppp'], {'p': ORG})],
    'blossom': [(['.w.', 'www', '.g.'], {}), (['p.p', '.p.'], {'p': PNK}), (['g..', '.gg', '..g'], {}), (['.yy.', 'yyyy'], {})],
    'sunset': [(['.o.', 'oyo'], {}), (['w.w', '.w.', 'w.w'], {}), (['yy', 'yo'], {}), (['.r.', 'rrr'], {})],
    'twilight': [(['.p.', 'ppp', '.w.'], {'p': MAG}), (['b.b', '.b.'], {}), (['g.g', '.g.'], {}), (['.yy', 'yy.'], {})],
    'balloons': [(['.w.', 'www'], {}), (['l.l', '.l.'], {}), (['.yy.', 'yyyy'], {}), (['g..', '.gg', '..g'], {})],
    'cave': [(['.y.', 'yoy', '.y.'], {}), (['.g.', 'ggg', '.g.'], {}), (['l.l', '.l.', 'l.l'], {}), (['ww', 'ow'], {})],
    'deep': [(['.l.', 'lwl'], {}), (['.o.', 'ooo', '.o.'], {}), (['ww', 'ww'], {}), (['u.u', '.u.'], {'u': LBL})],
    'festival': [(['.y.', 'yyy', '.y.'], {}), (['M.M', '.M.'], {}), (['l.l', '.l.'], {}), (['gg', 'g.'], {})],
}

# pan skins: rim, plate, underside colours, so the lift looks made of different things in different places
PAN_SKIN = {'meadow': (YEL, ORG, MAR), 'blossom': (WHT, LBL, BLU), 'sunset': (YEL, YEL, ORG), 'twilight': (LBL, BLU, PUR),
            'balloons': (WHT, LBL, BLU), 'cave': (ORG, ORG, MAR), 'deep': (GRN, LBL, BLU), 'festival': (YEL, MAG, ORG)}
# far mountains pasted into the sky: colour, snow, and (centre x, height, half width) of each peak
PEAKS = {'meadow': (BLU, WHT, ((10, 20, 18), (36, 26, 20), (58, 16, 14))),
         'sunset': (MAR, YEL, ((8, 14, 14), (30, 20, 17), (54, 16, 15))),
         'balloons': (PUR, WHT, ((12, 22, 16), (42, 30, 22)))}

SNAIL = [['..kk..', '.kooyk', 'kooyok', 'kppppk', 'kpppp.'], ['..kk..', '.kooyk', 'kooyok', 'kpppp.', 'kppppp']]
DRAGONFLY = [['w..w.', '.wwww', 'ggggg'], ['.w.w.', 'ggggg', '.w.w.']]
OWL = ['k.....k', 'kkkkkkk', 'kwwkwwk', 'kwkkkwk', 'kkoookk', '.kuuuk.', '.kuuuk.', '..k.k..']
OWL_SHUT = ['k.....k', 'kkkkkkk', 'kkkkkkk', 'kwkkkwk', 'kkoookk', '.kuuuk.', '.kuuuk.', '..k.k..']
GLOWBUG = [['.g.g.', 'ggyg.', '.g.g.'], ['..g..', '.gyg.', 'g.g.g']]
SEAHORSE = [['.yy', 'yky', '.yy', '.y.', '.yy', '.y.', 'yy.'], ['yy.', 'yky', 'yy.', '.y.', 'yy.', '.y.', '.yy']]
DOVE = [['w...w', '.w.w.', '..w..'], ['..w..', '.www.', 'w...w']]


def peaks_into(grid, colour, snow, peaks, base=44):
    """Triangular far mountains with a snowy tip, drawn straight into the sky picture (they never move)."""
    for cx, height, half in peaks:
        for y in range(base - height, base):
            width = half * (y - (base - height)) / height
            for x in range(round(cx - width), round(cx + width) + 1):
                if 0 <= x < 64:
                    grid[y][x] = snow if y - (base - height) < max(3, height // 5) else colour


THEME_EXTRA = {}
for _th in THEMES:
    _th['motifs'] = MOTIFS[_th['key']]
    _th['pan'] = PAN_SKIN[_th['key']]
    if _th['key'] in PEAKS:
        _th['peaks'] = PEAKS[_th['key']]


def pan_grid(th):
    rim, plate, under = th['pan']
    return A(PAN, y=rim, o=plate, m=under)


def life_extra(key, tick):
    """The second small creature of each setting (the first is in life_<setting>)."""
    out = []
    if key == 'meadow':
        out.append(sprite('snail', A(SNAIL[tick // 6 % 2]), 25 + tick // 9 % 8, 42, 3))
        out.append(sprite('dragonfly', A(DRAGONFLY[tick % 2], g=LBL), 36 + round(5 * math.sin(tick / 6)), 22 + round(3 * math.sin(tick / 3.5)), 3))
    elif key == 'blossom':
        out.append(sprite('dragonfly', A(DRAGONFLY[tick % 2], g=GRN), 18 + round(7 * math.sin(tick / 8)), 30 + round(2 * math.sin(tick / 3)), 3))
    elif key == 'twilight':
        out.append(sprite('owl', A(OWL_SHUT if tick % 23 > 20 else OWL, u=BLU), 7, 20, 3))
    elif key == 'cave':
        out.append(sprite('glow-bug', A(GLOWBUG[tick // 4 % 2]), 20 + (tick // 5) % 14, 36, 3))
    elif key == 'deep':
        out.append(sprite('seahorse', A(SEAHORSE[tick // 4 % 2]), 29 + round(2 * math.sin(tick / 9)), 20 + round(3 * math.sin(tick / 7)), 3))
    elif key == 'festival':
        for i in range(2):
            out.append(sprite(f'dove-{i}', A(DOVE[(tick // 2 + i) % 2], w=WHT), (tick // 2 + i * 40) % 84 - 10, 12 + i * 5 + round(math.sin(tick / 6 + i)), 3))
    return out


# 4x8 strip patterns for the margins; the right margin is the left one mirrored.
MARGIN_TILES = {
    'vine': ['.g.g', '.gg.', '..gg', '.yg.', '..g.', 'gg..', '.gwg', '.g..'],
    'trunk': ['kmoo', 'kmoo', 'kmmo', 'kmoo', 'kooo', 'kmoo', 'kmom', 'kmoo'],
    'reed': ['..g.', '..g.', '.mg.', '.mg.', '..g.', '..gg', '.g..', '.g..'],
    'puff': ['..ww', '.www', 'wwww', '.www', '..ww', '.www', 'wwww', '.www'],
    'rock': ['kuuu', 'kuMu', 'kuuu', 'kuuw', 'kMuu', 'kuuu', 'kuuM', 'kuuu'],
}


def margin_strip(kind, right):
    tile = art(MARGIN_TILES[kind])
    height = 5 * 8 + 5
    grid = [list(tile[y % 8]) for y in range(height)]
    return mirror(grid) if right else grid


# ───────────────────────── backdrop pieces ─────────────────────────
def sky_grid(bands):
    grid = canvas(64, 64)
    top = 0
    for end, colour in bands:
        for y in range(top, end):
            grid[y] = [colour] * 64
        top = end
    return grid


def hill_grid(colour, base, height, wave, phase):
    """Rolling hills: a smooth wave filled down to the shelf. Short wavelengths read as tree canopies or rocks."""
    grid = canvas(64, 53)
    for x in range(64):
        top = round(base - height * (0.5 + 0.5 * math.sin(x / wave * 2 * math.pi + phase)))
        for y in range(top, 53):
            grid[y][x] = colour
    return grid


def spikes_grid(colour, items, tip=None):
    """Stalactites hanging from the top: items are (x, width, length)."""
    grid = canvas(64, 22)
    for x0, width, length in items:
        for dy in range(length):
            half = width * (length - dy) / length / 2
            for x in range(round(x0 - half), round(x0 + half) + 1):
                if 0 <= x < 64:
                    grid[dy][x] = tip if (tip is not None and dy >= length - 2) else colour
    return grid


def blossom_dots():
    """Pale blossoms scattered on the canopy hills."""
    grid = canvas(64, 53)
    for i in range(16):
        x = hashed(i, 1, 5) % 62 + 1
        y = 38 + hashed(i, 2, 5) % 8
        grid[y][x] = WHT if i % 3 else MAG
        grid[y][x + 1 if x < 62 else x] = WHT if i % 2 else PNK
    return grid


def town_grid():
    """A village silhouette with lit windows."""
    grid = canvas(64, 53)
    x = 0
    i = 0
    while x < 64:
        width = 6 + hashed(i, 3, 2) % 4
        height = 6 + hashed(i, 4, 2) % 6
        for yy in range(44 - height, 49):
            for xx in range(x, min(64, x + width)):
                grid[yy][xx] = PUR
        for k in range(1, width - 2, 3):
            for row in range(46 - height + 2, 46, 4):
                grid[row][x + k] = YEL
                grid[row + 1][x + k] = YEL
        for k in range(width // 2):                     # a stepped roof
            if 0 <= x + k < 64:
                grid[44 - height - 1 - k // 2][x + k] = PUR
        x += width + 1 + hashed(i, 5, 2) % 2
        i += 1
    return grid


def blades_grid(phase):
    """Windmill sails: four arms turned by `phase` quarter-steps of an eighth turn."""
    grid = canvas(15, 15)
    for arm in range(4):
        angle = (arm * 90 + phase * 22.5) * math.pi / 180
        for r in range(0, 7):
            x = round(7 + math.cos(angle) * r)
            y = round(7 + math.sin(angle) * r)
            grid[y][x] = BLK
            if r > 3:                                    # the cloth of the sail is a little wider
                grid[y][min(14, x + 1)] = YEL if arm % 2 else ORG
    grid[7][7] = WHT
    return grid


def burst_grid(step, colour, second):
    """A firework: eight sparks flying outward, then thinning out."""
    grid = canvas(13, 13)
    if step > 7:
        return grid
    r = 1 + step
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        k = r if (dx == 0 or dy == 0) else round(r * 0.7)
        if step < 6 or (dx + dy) % 2:
            x, y = 6 + dx * k, 6 + dy * k
            if 0 <= x < 13 and 0 <= y < 13:
                grid[y][x] = colour if step < 5 else second
    if step < 2:
        grid[6][6] = WHT
    return grid


# ───────────────────────── hand-drawn scenery (the big pictures behind the board) ─────────────────────────
# Each prop is a named sprite on the backdrop layers. `own` recolours a letter, so one drawing serves a daylight and a
# silhouette version (a cottage that is white by day is black with lit windows at dusk).
OAK = ['....kkkkk....', '..kkgggggkk..', '.kgggyygggkk.', 'kgyyggggggggk', 'kgggggggggykk', 'kggggyggggggk',
       'kgggggggggkgk', '.kggggkggggk.', '..kkkgggkkk..', '....kmmmk....', '....kmomk....', '....kmomk....',
       '...kkmomkk...', '..kmmmommmk..']
CHERRY = ['....kkkkkkk....', '..kkppwwppwkk..', '.kppwwppppwwpk.', 'kppwppMppppwppk', 'kpppppppwwppppk',
          'kpwwppppppppMpk', 'kppppMpppwpppkk', '.kpwppppppppkk.', '..kkppwpppkk...', '....kkkmkkk....',
          '......kmk......', '......kmk......', '.....kkmkk.....', '....kmmmmmk....']
BARN = ['......kkkkkk......', '....kkmmmmmmkk....', '..kkmmmmmmmmmmkk..', '.kmmmmmmmmmmmmmmk.',
        'kmmmmmmmmmmmmmmmmk', 'kkkkkkkkkkkkkkkkkk', 'kyyyyyyyyyyyyyyyyk', 'kyoyyyyyyyyyyyyoyk',
        'kyoyywwwwwwwwyyoyk', 'kyoyywmwwwwmwyyoyk', 'kyoyywwmwwmwwyyoyk', 'kyoyywwwmmwwwyyoyk',
        'kyoyywwmwwmwwyyoyk', 'kyoyywmwwwwmwyyoyk', 'kyoyywwwwwwwwyyoyk', 'kkkkkkkkkkkkkkkkkk']
SILO = ['..kkkk..', '.kbbbbk.', 'kbbwbbbk', 'kkkkkkkk', 'klllwllk', 'kllllllk', 'kkkkkkkk', 'klllwllk', 'kllllllk',
        'kkkkkkkk', 'klllwllk', 'kllllllk', 'kkkkkkkk']
COTTAGE = ['.........kk...', '.......k.kmk..', '......kbkkmk..', '.....kbbbbbk..', '....kbbbbbbbk.',
           '...kbbbbbbbbbk', '..kbbbbbbbbbbk', '.kkkkkkkkkkkkk', '..kwwwwwwwwwk.', '..kwyywwwmmwk.',
           '..kwyywwwmmwk.', '..kwwwwwwmymk.', '..kkkkkkkkkkk.']
TOWER = ['....k....', '...kwk...', '..kwwwk..', '..kwwwk..', '.kwwwwwk.', '.kwwkwwk.', '.kwwwwwk.', 'kwwwwwwwk',
         'kwwmmmwwk', 'kwwmmmwwk', 'kkkkkkkkk']
HAY = ['..kkkkk..', '.kyyyoyk.', 'kyoyyyyyk', 'kyyyoyyyk', 'kkkkkkkkk']
GEM_BIG = ['...k...', '..kwk..', '.kwggk.', 'kwggggk', '.kgggk.', '..kgk..', '...k...']
CAP_TALL = ['...kkkkk...', '.kkgggggkk.', 'kgwggggwggk', 'kggggwgggwk', 'kkkkkkkkkkk', '...kuuuk...', '...kuuuk...',
            '..kkuuukk..']
CAP_SMALL = ['.kkkkk.', 'kyyoyyk', 'kyoyyok', 'kkkkkkk', '..kwwk.', '..kwwk.']
BEE = [['.ww.', 'ykyk', '.kk.'], ['....', 'ykyk', 'wkkw']]
KITE = [['..y..', '.yoy.', 'yoooy', '.yoy.', '..y..', '..k..', '.k...', '..k..', '...k.'],
        ['..y..', '.yoy.', 'yoooy', '.yoy.', '..y..', '..k..', '..k..', '.k...', '.k...']]
JELLY = [['..lll..', '.lwlll.', 'lllllll', 'lllllll', '.l.l.l.', '.l.l.l.', '..l.l..', '.l.l...'],
         ['..lll..', '.lwlll.', 'lllllll', 'lllllll', '.l.l.l.', '..l.l.l', '.l.l.l.', '...l.l.']]
LANTERN = ['..kk..', '.kyyk.', 'kyyyyk', 'kywwyk', 'kyyyyk', '.kyyk.', '..kk..']


def pine(tiers, body, high):
    """A fir tree built from stacked skirts (each tier a little wider than the one above), then a trunk."""
    width = 2 * tiers + 3
    mid = width // 2
    rows = []
    for tier in range(tiers):
        for step in range(3):
            half = min(1 + tier + step, mid)
            row = ['.'] * width
            for x in range(mid - half, mid + half + 1):
                row[x] = body
            row[mid - half] = row[mid + half] = 'k'
            if step == 1 and half > 1:
                row[mid - half + 1] = high
            rows.append(''.join(row))
    stem = ['.'] * width
    stem[mid - 1], stem[mid], stem[mid + 1] = 'k', 'm', 'k'
    return rows + [''.join(stem)] * 2


def bunting(colours, y_sag=3):
    """A string of little flags across the top of the festival: a sagging line with triangles hanging from it."""
    grid = canvas(64, 12)
    for x in range(64):
        sag = round(y_sag * math.sin(x / 63 * math.pi))
        grid[sag][x] = BLK
        if x % 5 == 2:
            colour = colours[(x // 5) % len(colours)]
            for dy in range(1, 4):
                for dx in range(-1, 2):
                    if dy < 3 or dx == 0:          # a flag is a small downward triangle
                        grid[sag + dy][min(63, x + dx)] = colour
    return grid


def rainbow(cx, cy, radius):
    """Six one-pixel bands drawn as arcs (red outside to purple inside), then mirrored smoothly by the circle test."""
    grid = canvas(64, 53)
    for y in range(53):
        for x in range(64):
            d = math.hypot(x - cx, y - cy)
            band = radius - d
            if y <= cy and 0 <= band < 7:
                grid[y][x] = (RED, ORG, YEL, GRN, LBL, BLU, PUR)[int(band)]
    return grid


def hot_air(a, b):
    """A hot-air balloon: striped envelope, rope and a wicker basket. Big and far away, never mistaken for a pickup."""
    grid = canvas(11, 17)
    for y in range(11):
        half = 5 * math.sin((y + 0.7) / 11.5 * math.pi) ** 0.55
        for x in range(11):
            if abs(x - 5) <= half + 0.2:
                edge = abs(abs(x - 5) - half) < 1
                grid[y][x] = BLK if (edge or y in (0, 10)) else (a, b)[(x // 2) % 2]
    for y in (11, 12):
        grid[y][3] = grid[y][7] = BLK
    for y, row in ((13, 'kkkkk'), (14, 'kyoyk'), (15, 'kooyk'), (16, 'kkkkk')):
        for dx, ch in enumerate(row):
            grid[y][3 + dx] = LETTER[ch]
    return grid


def wheel_grid(phase):
    """A ferris wheel: a ring, eight spokes and eight coloured cars that stay level while the wheel turns."""
    size = 25
    grid = canvas(size, size + 7)
    c = 12
    for step in range(120):
        angle = step / 120 * 2 * math.pi
        grid[round(c + math.sin(angle) * 11)][round(c + math.cos(angle) * 11)] = WHT
    for arm in range(8):
        angle = (arm * 45 + phase * 5.625) * math.pi / 180
        for r in range(0, 12):
            grid[round(c + math.sin(angle) * r)][round(c + math.cos(angle) * r)] = YEL if r % 2 else WHT
        cx, cy = round(c + math.cos(angle) * 11), round(c + math.sin(angle) * 11)
        car = (MAG, GRN, YEL, LBL, ORG, WHT, PUR, RED)[arm]
        for dy in range(3):
            for dx in range(-1, 2):
                if 0 <= cy + dy < size + 7 and 0 <= cx + dx < size:
                    grid[cy + dy][cx + dx] = BLK if dy == 0 else car
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            grid[c + dy][c + dx] = ORG
    grid[c][c] = WHT
    for y in range(c + 2, size + 7):                  # the A-frame legs
        grid[y][c - (y - c) // 2 - 1] = ORG
        grid[y][c + (y - c) // 2 + 1] = ORG
    return grid


def waterfall_grid(phase, width=7, height=30):
    """Falling water: white streaks that slide down a blue sheet, with foam at the foot."""
    grid = canvas(width, height)
    for y in range(height):
        for x in range(width):
            streak = (y * 2 + phase * 2 + x * 5) % 9
            grid[y][x] = WHT if streak < 2 else LBL if streak < 5 else BLU
    for x in range(width):
        grid[height - 1][x] = WHT if (x + phase) % 2 else LBL
        grid[0][x] = BLK
    return grid


def beams_grid():
    """Mine timbers: two uprights and a cross beam, with iron brackets, framing the cave."""
    grid = canvas(64, 53)
    for x0 in (3, 56):
        for y in range(6, 48):
            for dx in range(5):
                grid[y][x0 + dx] = BLK if dx in (0, 4) else MAR if (y // 6) % 2 else ORG
    for x in range(3, 61):
        for dy in range(4):
            grid[6 + dy][x] = BLK if dy in (0, 3) else ORG if dy == 1 else MAR
    for x0 in (8, 51):
        for k in range(5):
            grid[10 + k][x0 + (k if x0 < 30 else -k)] = MAR
            grid[11 + k][x0 + (k if x0 < 30 else -k)] = BLK
    return grid


def stalagmites():
    """Maroon teeth growing up from the floor of the cave, drawn over the far hills."""
    grid = canvas(64, 53)
    for x0, width, length in ((9, 7, 9), (21, 5, 6), (33, 8, 10), (45, 6, 7), (57, 7, 8)):
        for dy in range(length):
            half = width * (dy + 1) / length / 2
            for x in range(round(x0 - half), round(x0 + half) + 1):
                if 0 <= x < 64:
                    grid[52 - length + dy][x] = MAR
    return grid


def vines_grid(colour, bulb):
    """Hanging glow-vines for the deep cave: a strand falls from the ceiling and ends in a glowing bulb."""
    grid = canvas(64, 53)
    for x0, length in ((12, 14), (29, 22), (41, 11), (52, 18)):
        for y in range(8, 8 + length):
            grid[y][x0 + (1 if (y // 3) % 2 else 0)] = colour
        grid[8 + length][x0] = grid[8 + length][x0 + 1] = bulb
        grid[9 + length][x0] = bulb
    return grid


# ───────────────────────── pass three: living scenery (pictures) ─────────────────────────
# Everything below is inert. It never reads the puzzle state; it only gives each setting its own furniture and its own
# small bit of life (trees that lean in the wind, a cow that flicks its tail, a campfire, drips, fish, string lights).
ART_CACHE = {}
SWAY_CACHE = {}


def A(rows, **own):
    """art() with a memo: scenery is redrawn every frame, so each distinct picture is converted to colours only once.
    The rows list is kept in the cache so its id can never be reused by another picture."""
    key = (id(rows), tuple(sorted(own.items())))
    if key not in ART_CACHE:
        ART_CACHE[key] = (rows, art(rows, own=own))
    return ART_CACHE[key][1]


def sway(rows, fixed, amount, frame, own=None):
    """A tree leaning in the wind: the bottom `fixed` rows (the trunk) stay put, the rows above slide sideways by a
    little more the higher they are. Four frames: straight, right, straight, left."""
    key = (id(rows), fixed, amount, frame % 4, tuple(sorted((own or {}).items())))
    if key not in SWAY_CACHE:
        lean = amount * (0, 1, 0, -1)[frame % 4]
        top = len(rows) - fixed
        padded = []
        for r, row in enumerate(rows):
            shift = round(lean * (top - r) / top) if r < top else 0
            body = '.' * amount + row + '.' * amount
            padded.append(('.' * shift + body)[:len(body)] if shift >= 0 else (body + '.' * -shift)[-shift:])
        SWAY_CACHE[key] = (rows, art(padded, own=own))
    return SWAY_CACHE[key][1]


SUNFLOWER = ['.y.y.y.', '.yyyyy.', 'yyMMMyy', 'yymkmyy', 'yyMMMyy', '.yyyyy.', '.y.y.y.', '...g...', '..gg...', '...gg..',
             '...g...', '...g...']
TULIP = ['c.c', 'ccc', '.g.', 'gg.', '.g.', '.g.']
COW = ['.kkkkkkkk.k.k.', 'kwwkkwwwwkwwwk', 'kwwwkkwwwwkwkk', 'kwkkwwwwwwkppk', 'kwwwwwkwwwkppk', '.kwwwwwwwwkkk.',
       '..kwk....kwk..', '..kkk....kkk..']
COW_B = ['.kkkkkkkk..kkk.', 'kwwkkwwwwkkwwk.', 'kwwwkkwwwwkwkk.', 'kwkkwwwwwwkppk.', 'kwwwwwkwwwkppk.', '.kwwwwwwwwkkk..',
         '..kwk....kwk...', '..kkk....kkk...']
VANE = ['.......', '.y.....', 'yykkkko', '.y.....', '...k...', '...k...', '...k...', '...k...']
RAB_SIT = ['..ww....', '..wp....', '.wwwww..', '.wkwwww.', '.wwpwww.', 'wwwwwww.', '.ww.ww..']
RAB_EAR = ['.ww.....', '..wp....', '.wwwww..', '.wkwwww.', '.wwpwww.', 'wwwwwww.', '.ww.ww..']
HUM_A = ['..ww...', '.wggggo', '..gggo.', '..g....']
HUM_B = ['.......', '.wggggo', '.wwggo.', '..g....']
PICNIC = ['..kkkk......', '.kyyyyk.....', 'rrwwrrwwrrww', 'wwrrwwrrwwrr', 'rrwwrrwwrrww', 'kkkkkkkkkkkk']
JUG = ['.kk.', 'kllk', 'kllk', 'kbbk', 'kkkk']
FIRE = [['...y...', '..yoy..', '.yooyo.', '.orrro.', 'kmmmmmk', 'mkkkkkm'],
        ['..y....', '.yoy.y.', '.oyyoo.', '.orrro.', 'kmmmmmk', 'mkkkkkm'],
        ['....y..', '..yoy..', '.oyyoy.', 'orrrrro', 'kmmmmmk', 'mkkkkkm']]
TENT = ['......k......', '.....kyk.....', '....kyoyk....', '...kyoyoyk...', '..kyoyoyoyk..', '.kyoyokkkyok.', 'kyoyoykkkyoyk',
        'kkkkkkkkkkkkk']
LOG = ['kmmmmmmmk', 'mkkkkkkkm']
KITE = ['....k....', '...yku...', '..yykuu..', '.yyykuuu.', 'kkkkkkkkk', '.uuukyyy.', '..uukyy..', '...uky...', '....k....']
WINDSOCK = [['kooowwoo', 'kooowwo.', 'koowwo..'], ['koowwo..', 'kooowwo.', 'kooowwoo']]
HAWK = [['k.......k', '.kk...kk.', '...kkk...'], ['....k....', '.kkkkkkk.', 'k.......k']]
TORCH = [['..y..', '.yoy.', '.orr.', '..k..', '..k..', '..k..', '.kkk.'],
         ['.y...', '.yoy.', '.orr.', '..k..', '..k..', '..k..', '.kkk.'],
         ['...y.', '.yoy.', '.oor.', '..k..', '..k..', '..k..', '.kkk.']]
SPIDER = [['.k...k.', '..kkk..', 'kkyrykk', '..kkk..', '.k...k.'], ['k.....k', '.kkkkk.', '.kyryk.', '.kkkkk.', 'k.....k']]
COBWEB = ['wwwwwwww', 'w.w..w..', 'w..w.w..', 'w.w.ww..', 'ww..w.w.', 'w.w..ww.', 'w....w.w', 'w..w..w.']
VEIN = ['....y...', '...yyo..', '..yoy...', '.yyo....', 'yoy.....']
WEED = ['..g.', '.gg.', '.g..', '.gg.', '..g.', '..gg', '..g.', '.gg.', '.g..', '.gg.', '..g.', '..g.', '.gg.', '.g..']
FISH_A = ['.f..ff....', 'ff.ffffff.', 'f.ffwkffff', 'ff.ffffff.', '.f..ff....']
FISH_B = ['....ff....', 'f..ffffff.', 'ff.ffwkfff', 'f..ffffff.', '....ff....']
ANGLER = ['.......y....', '......ky....', '.....k......', '..mmmmmmm...', '.mmmmmmmmm..', 'mmmwmywmmmm.', 'mmmkwkwkmmmm', 'mmmmmmmmmm..',
          '.mmmmmmmm...', '..m.m.m.....']
CORAL = ['.o.....o.', '.oo...oo.', '..oo.oo..', '.ooooooo.', 'ooooooooo', '.oo.o.oo.', '..o.o.o..', '....o....', '....o....']
BUBBLE = ['.l.', 'lwl', '.l.']
BALLOON = ['.kkkk.', 'kcccck', 'kcwcck', 'kcccck', '.kcck.', '..kk..', '...k..']
LANTERN_PAPER = ['..kk..', '.kcck.', 'kcccck', 'kcwcck', 'kcccck', '.kcck.', '..kk..', '...c..']
MAILBOX = ['kkkkk.', 'kbbbbk', 'kbbbbk', 'kkkkkk', '..km..', '..km..']
POP_CART = ['..kkkkkk..', '.kwrwrwrk.', 'kwrwrwrwwk', 'kyyyyyyyyk', 'kyywwwwyyk', 'kyywwwwyyk', 'kkkkkkkkkk', '.kk....kk.']

# the little things that stand on the shelf beside the pet (8 wide at most, nothing with letters or digits)
TRINKETS = {
    'meadow': (['.k...k.', 'kkkkkkk', 'kwwwwwk', '.kwwwk.', '.kyyyk.', '.kyyyk.', '..kkk..'], {}),
    'blossom': (['.c.c.c.', 'ccycycc', '.cycyc.', '..ggg..', 'kkkkkkk', '.kooook', '..kook.'], {'c': LBL}),
    'sunset': (['..y.', '.yoy', '.orr', 'kkkk', '.kyk', '.kyk', 'kkkk'], {}),
    'twilight': (['..y..', '.yoy.', '..k..', 'kkkkk', 'kyyyk', 'kyyyk', '.kkk.'], {}),
    'balloons': (['.u.u.', 'uuuyy', '.uuy.', '..k..', '..k..', '..k..', '.kkk.'], {}),
    'cave': (['..kkkk.', '.kyyyyk', 'kyyyyyk', 'kkkkkkk', '...k...', '...k...', '..kkk..'], {}),
    'deep': (['..lll..', '.lwwll.', 'lwlllll', 'lllllll', '.lllll.', '..lll..', '..kkk..'], {}),
    'festival': (['kkkkkkk', 'kMMMMMk', 'kMwwwMk', 'kMMMMMk', '.k...k.', '.k...k.', '.kk.kk.'], {}),
}
SHELF_SMALL = {
    'meadow': ['.g.', 'ggg', '.m.', '.m.', 'kkk'],
    'blossom': ['y.y', '.y.', '.g.', 'gg.', 'kkk'],
    'sunset': ['.o.', 'ooo', 'ooo', 'kkk', 'k.k'],
    'twilight': ['y.', 'oo', 'kk', 'kk', 'kk'],
    'balloons': ['.b.', 'bbb', 'lll', 'kkk', 'k.k'],
    'cave': ['.y.', 'yyy', 'kkk', 'k.k', 'kkk'],
    'deep': ['.o.', 'ooo', '.o.', 'o.o', 'kkk'],
    'festival': ['y.y', '.y.', 'MMM', 'MMM', 'kkk'],
}


def rays_grid(phase):
    """Sun rays: eight short beams that take turns, so the sun seems to shimmer."""
    grid = canvas(25, 25)
    for k in range(8):
        if k % 2 == phase % 2:
            angle = k * math.pi / 4
            for r in (8, 9, 10, 11):
                px, py = round(12 + math.cos(angle) * r), round(12 + math.sin(angle) * r)
                for ox, oy in ((0, 0), (1, 0), (0, 1)):
                    if 0 <= px + ox < 25 and 0 <= py + oy < 25:
                        grid[py + oy][px + ox] = YEL if r < 10 else ORG
    return grid


def cave_wall():
    """Stone blocks laid in courses, each with a lit top edge and a dark foot, so the cave is a built place rather than a
    flat purple field. The mortar lines are maroon; every few blocks carries a chip of ore."""
    grid = canvas(64, 64, PUR)
    for course in range(0, 64, 8):
        offset = 6 if (course // 8) % 2 else 0
        for y in range(course, min(64, course + 8)):
            for x in range(64):
                local = (x + offset) % 12
                if y == course or local == 0:
                    grid[y][x] = MAR
                elif y == course + 1 and 0 < local < 11:
                    grid[y][x] = MAG
                elif y == course + 7:
                    grid[y][x] = MAR if local % 2 else PUR
        for block in range(-1, 6):
            if hashed(course, block, 3) % 5 == 0:
                x0 = block * 12 - offset + 4 + hashed(course, block, 4) % 4
                for dx, dy in ((0, 3), (1, 3), (1, 4), (2, 4)):
                    if 0 <= x0 + dx < 64 and course + dy < 64:
                        grid[course + dy][x0 + dx] = ORG if dx else YEL
    return grid


def deep_water():
    """The deep: black water with slanting shafts of purple light and a sprinkle of drifting specks."""
    grid = canvas(64, 64, BLK)
    for shaft, width in ((6, 4), (24, 6), (43, 4), (55, 3)):
        for y in range(0, 50):
            left = shaft + y // 3
            for x in range(left, left + width - y // 18):
                if 0 <= x < 64:
                    grid[y][x] = PUR
    for i in range(26):
        grid[4 + hashed(i, 1, 11) % 46][hashed(i, 2, 11) % 62 + 1] = BLU if i % 3 else PUR
    return grid


def pole_lights(phase):
    """A wire of festival bulbs; the colours chase along it as the phase advances."""
    grid = canvas(34, 6)
    colours = (MAG, YEL, GRN, LBL, ORG)
    for x in range(34):
        grid[round(2 * math.sin(x / 33 * math.pi))][x] = BLK
    for k, x in enumerate(range(1, 34, 4)):
        sag = round(2 * math.sin(x / 33 * math.pi))
        colour = colours[(k + phase) % 5]
        grid[sag + 1][x] = grid[sag + 2][x] = colour
        grid[sag + 2][x + 1 if x < 33 else x] = WHT if (k + phase) % 5 == 0 else colour
    return grid


def flock(count, x, y, tick, colour):
    """A V of geese: the leader in front, each follower a little behind and lower, wings beating out of step."""
    out = []
    for i in range(count):
        row = (i + 1) // 2
        side = -1 if i % 2 else 1
        frame = A(BIRD[(tick // 2 + i) % 2], k=colour)
        out.append(sprite(f'goose-{i}', frame, x + side * row * 6 if i else x, y + row * 3 + (1 if (tick // 4 + i) % 2 else 0), 3))
    return out


def shooting_star(tick, cycle=52):
    """Every so often a streak crosses the dusk: a short tail that fades behind a bright head."""
    step = tick % cycle
    if step > 7:
        return []
    x, y = 8 + (tick // cycle * 23) % 40, 8 + (tick // cycle * 7) % 10
    out = [block('shooting-head', x + step * 3, y + step, 2, 1, WHT, 3)]
    for k in range(1, 4):
        out.append(block(f'shooting-tail-{k}', x + (step - k) * 3, y + step - k, 2, 1, YEL if k < 3 else ORG, 3))
    return out


def drips(tick):
    """Cave water: a bead gathers at each stalactite tip, lets go, falls and vanishes in a ring."""
    out = []
    for i, (x, tip, lag) in enumerate(((14, 14, 0), (36, 15, 9), (58, 14, 17))):
        step = (tick // 2 + lag) % 22
        if step < 4:
            out.append(block(f'bead-{i}', x, tip, 1, 1, LBL, 3))
        elif step < 16:
            out.append(block(f'drip-{i}', x, tip + 1 + (step - 4) * 2, 1, 2, LBL, 3))
        elif step < 19:
            out.append(block(f'splash-{i}', x - 1, tip + 26, 3, 1, WHT, 3))
    return out


def prop_sprites(index):
    """The named props of one setting: kind, x, y, colour overrides. Standing props sit with their feet on the near
    hill so they read as scenery, not as something to pick up or push."""
    out = []
    key = THEMES[index]['key']
    def put(name, rows, x, y, layer=3, own=None):
        out.append(sprite(name, art(rows, own=own) if rows and isinstance(rows[0], str) else rows, x, y, layer))
    if key == 'meadow':
        put('barn', BARN, 43, 32)
        put('silo', SILO, 37, 35, own={'b': ORG})
        put('hay', HAY, 29, 43)
    elif key == 'blossom':
        put('cottage', COTTAGE, 47, 37, own={'b': MAR})
    elif key == 'sunset':
        put('cottage', COTTAGE, 7, 35, own={'w': PUR, 'b': PUR, 'm': PUR, 'y': YEL})
        put('hay', HAY, 27, 44, own={'y': ORG, 'o': MAR})
    elif key == 'twilight':
        put('lodge', COTTAGE, 22, 34, own={'w': PUR, 'b': PUR, 'm': PUR, 'y': YEL})
    elif key == 'balloons':
        out.append(sprite('rainbow', rainbow(32, 50, 27), 0, 0, 2))
        put('hilltop-house', COTTAGE, 46, 36, own={'b': GRN})
    elif key == 'cave':
        out.append(sprite('beams', beams_grid(), 0, 0, 3))
        out.append(sprite('teeth', stalagmites(), 0, 0, 2))
        for i, (x, y, colour) in enumerate(((14, 22, GRN), (34, 16, YEL), (52, 30, WHT), (22, 36, YEL))):
            put(f'gem-{i}', GEM_BIG, x, y, 3, own={'g': colour})
        put('cap-0', CAP_SMALL, 25, 41)
        put('cap-1', CAP_SMALL, 53, 38)
    elif key == 'deep':
        out.append(sprite('vines', vines_grid(GRN, YEL), 0, 0, 3))
        put('cap-big-0', CAP_TALL, 24, 38, own={'g': GRN})
        put('cap-big-1', CAP_TALL, 44, 40, own={'g': LBL})
        for i, (x, y, colour) in enumerate(((22, 23, GRN), (40, 18, WHT))):
            put(f'gem-{i}', GEM_BIG, x, y, 3, own={'g': colour})
    elif key == 'festival':
        out.append(sprite('bunting', bunting((MAG, YEL, GRN, LBL, ORG)), 0, 8, 3))
    return out


def backdrop(index):
    """Everything behind the board that never moves: sky, hills, sun or moon, canopy, stalactites, margins."""
    th = THEMES[index]
    wall = {'cave': cave_wall, 'deep': deep_water}.get(th.get('floor'))
    sky = wall() if wall else sky_grid(th['sky'])
    if 'peaks' in th:
        peaks_into(sky, *th['peaks'])
    out = [sprite('sky', sky, 0, 0, 0)]
    for i, (colour, base, height, wave, phase) in enumerate(th['hills']):
        out.append(sprite(f'hills-{i}', hill_grid(colour, base, height, wave, phase), 0, 0, 1 + i))
    for prop in th['props']:
        if prop == 'sun':
            out.append(sprite('sun-rim', disc(6, YEL, ORG), 47, 9, 2))
        elif prop == 'sunset':
            half = disc(9, YEL, ORG)[:10]                # the sun sits half below the hills
            out.append(sprite('sun-setting', half, 27, 33, 1))
        elif prop == 'blossoms':
            out.append(sprite('blossom-dots', blossom_dots(), 0, 0, 3))
        elif prop == 'moon':
            moon = disc(5, WHT)            # a crescent: bite out a second disc offset to the upper right
            for y in range(11):
                for x in range(11):
                    if math.hypot(x - 8, y - 3) <= 4.5:
                        moon[y][x] = -1
            out.append(sprite('moon', moon, 8, 11, 2))
        elif prop == 'gems':
            for i, (x, y) in enumerate(((6, 20), (24, 14), (38, 27), (53, 22), (57, 33))):
                out.append(sprite(f'gem-{i}', art(GEM), x, y, 2))
        elif prop == 'mushrooms':
            cap = art(['.pwpp.', 'pppwpp', '.kyyk.', '..yy..'])
            for i, x in enumerate((14, 41)):
                out.append(sprite(f'mushroom-{i}', cap, x, 44, 3))
        elif prop.startswith('spikes'):
            dark = prop.endswith('dark')
            items = [(5, 6, 9), (14, 5, 6), (25, 7, 10), (36, 5, 6), (47, 8, 9), (58, 6, 8)]
            out.append(sprite('stalactites', spikes_grid(MAR if dark else MAG, items, tip=ORG if dark else PNK), 0, 0, 2))
        elif prop == 'town':
            out.append(sprite('village', town_grid(), 0, 0, 2))
    out.extend(prop_sprites(index))
    out.append(sprite('margin-left', margin_strip(th['margin'], False), 0, 8, 4))
    out.append(sprite('margin-right', margin_strip(th['margin'], True), 60, 8, 4))
    return out


# ───────────────────────── drifting life (nothing here depends on the puzzle) ─────────────────────────
WINDMILL_CACHE = {}
WHEEL_CACHE = {}
AIRSHIP_CACHE = {}


def wheel_cached(phase):
    if phase not in WHEEL_CACHE:
        WHEEL_CACHE[phase] = wheel_grid(phase)
    return WHEEL_CACHE[phase]


def hot_air_cached(a, b):
    if (a, b) not in AIRSHIP_CACHE:
        AIRSHIP_CACHE[(a, b)] = hot_air(a, b)
    return AIRSHIP_CACHE[(a, b)]


def ambient(index, tick):
    th = THEMES[index]
    out = []
    for kind in th['ambient']:
        if kind == 'clouds':
            own = {'S': th['shade']}
            if th['key'] == 'sunset':
                own['w'] = PNK
            elif th['key'] == 'blossom':
                own['w'] = WHT
            grid = art(CLOUD, own=own)
            rows = {'meadow': ((11, 6, 7), (21, 41, 11)), 'blossom': ((17, 20, 9),), 'sunset': ((12, 30, 10),),
                    'balloons': ((13, 8, 6), (24, 44, 9), (34, 24, 13))}[th['key']]
            for i, (y, x0, div) in enumerate(rows):
                out.append(sprite(f'cloud-{i}', grid, (x0 + tick // div) % 92 - 22, y, 3))
        elif kind == 'birds':
            colour = {'meadow': BLK, 'sunset': BLK, 'balloons': MAG}[th['key']]
            for i, (y, x0) in enumerate(((16, 12), (23, 50))):
                frame = art(BIRD[(tick // 2 + i) % 2], own={'k': colour})
                out.append(sprite(f'bird-{i}', frame, (x0 + tick // 2) % 80 - 12, y + (1 if (tick // 4 + i) % 2 else 0), 3))
        elif kind == 'butterflies':
            for i, (x0, y0) in enumerate(((10, 36), (44, 30))):
                frame = art(BUTTERFLY[(tick // 2 + i) % 2], own={'p': (YEL, WHT)[i] if th['key'] == 'meadow' else MAG})
                x = x0 + round(5 * math.sin((tick + i * 9) / 7)) + tick // 6 % 8
                y = y0 + round(3 * math.sin((tick + i * 5) / 4))
                out.append(sprite(f'butterfly-{i}', frame, x, y, 3))
        elif kind == 'petals':
            for i in range(7):
                x = (hashed(i, 1, 9) % 56 + 4 + tick // 3 + round(2 * math.sin((tick + i * 6) / 5))) % 56 + 4
                y = (hashed(i, 2, 9) % 40 + 10 + tick // 4) % 40 + 10
                out.append(sprite(f'petal-{i}', [[WHT if i % 2 else MAG, PNK]], x, y, 3))
        elif kind == 'windmill':
            if tick // 3 % 4 not in WINDMILL_CACHE:
                WINDMILL_CACHE[tick // 3 % 4] = blades_grid(tick // 3 % 4)
            out.append(sprite('windmill-tower', art(TOWER, own={'w': BLK, 'm': BLK}), 52, 38, 2))
            out.append(sprite('windmill-sails', WINDMILL_CACHE[tick // 3 % 4], 49, 31, 2))
        elif kind == 'stars':
            pts = ((6, 9), (15, 5), (24, 11), (36, 7), (47, 12), (55, 6), (60, 17), (30, 20), (12, 24), (52, 26))
            for i, (x, y) in enumerate(pts):
                phase = (tick // 3 + i * 2) % 5
                if phase == 0:
                    out.append(sprite(f'star-{i}', art(STAR_SMALL), x - 1, y - 1, 2))
                else:
                    out.append(block(f'star-{i}', x, y, 1, 1, WHT if i % 2 else YEL, 2))
        elif kind == 'fireflies':
            for i in range(4):
                if (tick // 3 + i * 2) % 4:
                    x = hashed(i, 6, 4) % 50 + 6 + round(3 * math.sin((tick + i * 7) / 6))
                    y = 30 + hashed(i, 7, 4) % 14 + round(2 * math.cos((tick + i * 4) / 5))
                    out.append(block(f'firefly-{i}', x, y, 1, 1, YEL, 3))
        elif kind == 'airships':
            # two hot-air balloons, big and striped with baskets: scenery that sways, nothing like a fruit
            for i, (a, b, x0, y0) in enumerate(((PUR, YEL, 3, 19), (ORG, WHT, 34, 27))):
                out.append(sprite(f'airship-{i}', hot_air_cached(a, b), x0 + round(3 * math.sin((tick + i * 17) / 16)),
                                  y0 + round(2 * math.sin((tick + i * 9) / 11)), 3))
        elif kind == 'smoke':
            sx, sy = SMOKE_AT[th['key']]
            for i in range(3):
                rise = (tick // 2 + i * 5) % 15
                out.append(block(f'smoke-{i}', sx + round(math.sin((rise + i) / 2.2) * 1.5), sy - rise, 2, 2,
                                 WHT if th['key'] != 'sunset' else MAG, 3))
        elif kind == 'bees':
            for i, (x0, y0) in enumerate(((8, 34), (40, 24), (22, 40))):
                x = x0 + round(7 * math.sin((tick + i * 11) / 8))
                y = y0 + round(3 * math.sin((tick + i * 5) / 3))
                out.append(sprite(f'bee-{i}', art(BEE[(tick + i) % 2]), x, y, 3))
        elif kind == 'jellies':
            for i, x0 in enumerate((8, 36, 52)):
                y = (46 - (tick // 3 + i * 17)) % 40 + 8
                out.append(sprite(f'jelly-{i}', art(JELLY[(tick // 2 + i) % 2]), x0 + round(2 * math.sin((tick + i * 7) / 8)), y, 3))
        elif kind == 'lantern':
            out.append(block('lantern-chain', 40, 10, 1, 8, BLK, 3))
            out.append(sprite('lantern', art(LANTERN), 37 + round(1.4 * math.sin(tick / 6)), 18, 3))
        elif kind == 'ferris':
            out.append(sprite('ferris-wheel', wheel_cached(tick // 3 % 8), 36, 12, 2))
        elif kind == 'waterfall':
            out.append(sprite('waterfall', waterfall_grid(tick // 2 % 9), 21, 12, 3))
        elif kind == 'bats':
            for i, (y, x0) in enumerate(((10, 6), (20, 40))):
                frame = art(BAT[(tick // 2 + i) % 2])
                out.append(sprite(f'bat-{i}', frame, (x0 + tick // 2 * (1 if i == 0 else -1)) % 80 - 10, y + round(2 * math.sin((tick + i * 6) / 5)), 3))
        elif kind == 'gleam':
            for i, (x, y) in enumerate(((8, 21), (26, 15), (40, 28), (55, 23), (59, 34))):
                if (tick // 3 + i) % 4 == 0:
                    out.append(sprite(f'gleam-{i}', art(STAR_SMALL, own={'y': WHT}), x - 1 + 2, y - 1 + 2, 3))
        elif kind == 'glow':
            for i in range(6):
                if (tick // 4 + i) % 3:
                    x = hashed(i, 3, 8) % 54 + 5
                    y = 16 + hashed(i, 4, 8) % 24 + round(2 * math.sin((tick + i * 5) / 6))
                    out.append(block(f'glowworm-{i}', x, y, 1, 1, YEL, 3))
        elif kind == 'fireworks':
            for i, (cx, cy, colour, second) in enumerate(((16, 24, MAG, WHT), (46, 17, YEL, ORG))):
                step = (tick // 2 + i * 6) % 14
                out.append(sprite(f'firework-{i}', burst_grid(step, colour, second), cx - 6, cy - 6, 3))
        elif kind == 'windows':
            for i, x in enumerate((9, 27, 44)):
                if (tick // 4 + i) % 2:
                    out.append(block(f'window-{i}', x, 40 + i % 2, 1, 2, YEL, 3))
    out.extend(trees(index, tick))
    out.extend(LIFE[th['key']](tick))
    out.extend(life_extra(th['key'], tick))
    return out


# ───────────────────────── pass three: where each setting's trees stand, and each setting's own life ─────────────────────────
# Trees: (name, picture, x, y, trunk rows that stay still, sway in pixels, colour overrides). They lean in the wind with
# their own phase so a row of them never moves in step.
TREES = {
    'meadow': [('oak-far', OAK, 20, 24, 5, 1, None)],
    'blossom': [('cherry-0', CHERRY, 4, 28, 5, 1, None), ('cherry-1', CHERRY, 41, 27, 5, 1, None),
                ('oak-far', OAK, 26, 29, 5, 1, None)],
    'sunset': [('poplar-0', pine(4, 'u', 'o'), 22, 29, 3, 1, None), ('poplar-1', pine(3, 'u', 'o'), 30, 34, 3, 1, None)],
    'twilight': [('pine-0', pine(4, 'u', 'b'), 5, 28, 3, 1, None), ('pine-1', pine(3, 'u', 'b'), 40, 30, 3, 1, None),
                 ('pine-2', pine(4, 'u', 'b'), 54, 28, 3, 1, None)],
    'balloons': [('hilltop-oak', OAK, 5, 33, 5, 1, None)],
}


def trees(index, tick):
    out = []
    for name, rows, x, y, fixed, amount, own in TREES.get(THEMES[index]['key'], ()):
        out.append(sprite(name, sway(rows, fixed, amount, tick // 4 + hashed(x, y) % 4, own), x - amount, y, 3))
    return out


def tuft_row(name, xs, y, tick, colours):
    """Tulips in a bed: each one leans a pixel one way then the other, out of step with its neighbours."""
    out = []
    for i, x in enumerate(xs):
        out.append(sprite(f'{name}-{i}', sway(TULIP, 3, 1, tick // 4 + i, {'c': colours[i % len(colours)]}), x - 1, y, 3))
    return out


def life_meadow(tick):
    out = [sprite('sun-rays', rays_grid(tick // 4), 41, 3, 2)]
    for i, x in enumerate((7, 17)):
        out.append(sprite(f'sunflower-{i}', sway(SUNFLOWER, 5, 1, tick // 5 + i * 2), x - 1, 31 + i * 2, 3))
    out.extend(tuft_row('tulip', (24, 40), 42, tick, (RED, YEL)))
    cow = A(COW if tick // 7 % 3 else COW_B)
    out.append(sprite('cow', cow, 21, 40, 3))
    flip = tick // 9 % 2
    out.append(sprite('weathervane', A(VANE) if flip else mirror(A(VANE)), 48, 25, 3))
    return out


def life_blossom(tick):
    out = tuft_row('tulip', (12, 16, 52, 56), 42, tick, (YEL, LBL, MAG, WHT))
    rab = RAB_EAR if tick // 6 % 5 == 0 else RAB_SIT
    hop = -3 if tick % 30 in (4, 5) else 0
    out.append(sprite('rabbit', outlined(A(rab)), 9, 38 + hop, 3))
    out.append(sprite('picnic-blanket', A(PICNIC), 28, 42, 3))
    out.append(sprite('picnic-jug', A(JUG), 36, 38, 3))
    hum = A(HUM_A if tick % 2 else HUM_B)
    out.append(sprite('hummingbird', hum, 33 + round(3 * math.sin(tick / 9)), 27 + round(2 * math.sin(tick / 5)), 3))
    return out


def life_sunset(tick):
    out = flock(5, 36, 10 + round(math.sin(tick / 14) * 2), tick, BLK)
    ring = disc(12, -1, ORG if tick // 6 % 2 else YEL)
    out.append(sprite('sun-halo', ring, 23, 21, 1))
    for i, x in enumerate((41, 53)):
        out.append(sprite(f'cow-{i}', A(COW if (tick // 8 + i) % 4 else COW_B, w=PUR, p=MAG), x, 36 + i * 2, 3))
    glow = YEL if tick // 5 % 3 else WHT
    out.append(block('cottage-light', 11, 44, 2, 2, glow, 3))
    return out


def life_twilight(tick):
    out = [sprite('campfire', A(FIRE[tick // 2 % 3]), 33, 40, 3), sprite('campfire-logs', A(LOG), 32, 46, 3)]
    out.append(sprite('tent', A(TENT), 17, 38, 3))
    out.extend(shooting_star(tick))
    for i, (x, y) in enumerate(((35, 36), (31, 33), (38, 31))):      # sparks lifting off the fire
        if (tick // 2 + i * 3) % 6 < 4:
            out.append(block(f'ember-{i}', x + round(math.sin((tick + i * 5) / 3)), y - (tick // 2 + i * 3) % 6, 1, 1,
                             ORG if i % 2 else YEL, 3))
    return out


def life_balloons(tick):
    out = []
    kx = 38 + round(2 * math.sin(tick / 9))
    out.append(sprite('kite', outlined(A(KITE)), kx - 1, 10, 3))
    for k in range(5):                                      # the tail, with a bow every other knot
        tx = kx + 3 + round(1.5 * math.sin((tick / 3) + k))
        out.append(block(f'kite-tail-{k}', tx, 21 + k * 2, 1, 2, BLK, 3))
        if k % 2 == 0:
            out.append(block(f'kite-bow-{k}', tx - 1, 22 + k * 2, 3, 1, (MAG, LBL, GRN)[k // 2], 3))
    out.append(block('windsock-pole', 50, 29, 1, 9, BLK, 3))
    out.append(sprite('windsock', A(WINDSOCK[tick // 4 % 2]), 51, 29, 3))
    out.append(sprite('hawk', A(HAWK[tick // 3 % 2], k=BLK), (tick // 2) % 90 - 14, 18 + round(3 * math.sin(tick / 12)), 3))
    return out


def life_cave(tick):
    out = [sprite('torch-0', A(TORCH[tick // 2 % 3]), 9, 20, 3), sprite('torch-1', mirror(A(TORCH[(tick // 2 + 1) % 3])), 50, 20, 3)]
    out.append(sprite('web', A(COBWEB), 8, 10, 3))
    out.append(sprite('web-mirror', mirror(A(COBWEB)), 48, 10, 3))
    out.append(sprite('vein', A(VEIN), 44, 33, 3))
    drop = 14 + round(5 * (1 + math.sin(tick / 10)))
    out.append(block('spider-thread', 31, 8, 1, drop - 7, WHT, 3))
    out.append(sprite('spider', A(SPIDER[tick // 3 % 2]), 28, drop, 3))
    out.extend(drips(tick))
    return out


def life_deep(tick):
    out = []
    for i, x in enumerate((8, 14, 49, 55)):
        out.append(sprite(f'seaweed-{i}', sway(WEED, 4, 1, tick // 5 + i, {'g': GRN if i % 2 else LBL}), x - 1, 33 - i % 2 * 2, 3))
    for i, (y, speed, colour, face) in enumerate(((20, 1, ORG, 1), (30, 2, MAG, -1), (14, 3, YEL, 1))):
        fish = A(FISH_A if tick // 3 % 2 else FISH_B, f=colour, t=YEL if colour != YEL else ORG)
        x = (tick * speed // 2 + i * 31) % 84 - 14
        out.append(sprite(f'fish-{i}', fish if face > 0 else mirror(fish), x if face > 0 else 64 - x - 10,
                          y + round(2 * math.sin((tick + i * 8) / 8)), 3))
    lure = YEL if tick // 4 % 3 else WHT
    out.append(sprite('angler', A(ANGLER), 7, 38, 3))
    out.append(block('angler-lure', 14, 36 + (1 if tick // 4 % 2 else 0), 2, 2, lure, 3))
    out.append(sprite('coral-0', A(CORAL), 22, 40, 3))
    out.append(sprite('coral-1', A(CORAL, o=LBL), 52, 41, 3))
    for i in range(5):
        rise = (tick + i * 11) % 44
        out.append(sprite(f'bubble-{i}', A(BUBBLE) if i % 2 else [[LBL]], 12 + i * 11 + round(1.5 * math.sin((tick + i * 4) / 4)),
                          48 - rise, 3))
    return out


def life_festival(tick):
    out = [sprite('string-lights', pole_lights(tick // 2 % 5), 4, 14, 3), sprite('string-lights-b', pole_lights((tick // 2 + 2) % 5), 4, 18, 3)]
    for i, (x, colour) in enumerate(((7, MAG), (13, YEL), (19, GRN))):
        bob = round(2 * math.sin((tick + i * 7) / 7))
        out.append(block(f'balloon-string-{i}', x + 2, 31, 1, 6 + bob, BLK, 3))
        out.append(sprite(f'balloon-{i}', A(BALLOON, c=colour), x, 22 + bob, 3))
    out.append(sprite('popcorn-cart', A(POP_CART), 28, 41, 3))
    for i, (x, colour) in enumerate(((10, RED), (24, ORG))):
        sw = round(1.5 * math.sin((tick + i * 9) / 8))
        out.append(sprite(f'paper-lantern-{i}', A(LANTERN_PAPER, c=colour), x + sw, 20 - i * 2, 3))
    return out


LIFE = {'meadow': life_meadow, 'blossom': life_blossom, 'sunset': life_sunset, 'twilight': life_twilight,
        'balloons': life_balloons, 'cave': life_cave, 'deep': life_deep, 'festival': life_festival}


def shelf_things(index, tick):
    """The trinkets that sit on the shelf: one on the left of the pet, one tiny one on the right."""
    key = THEMES[index]['key']
    rows, own = TRINKETS[key]
    out = [sprite('shelf-trinket', A(rows, **own), 34, 53, 21)]
    out.append(sprite('shelf-small', A(SHELF_SMALL[key]), 59, 54, 21))
    return out


# ───────────────────────── the board: earth, shelf, HUD furniture (static per level) ─────────────────────────
def earth_grid(th, cell, walls, under):
    """One 8x8 earth tile (or the 5-high ground strip). Grass on every exposed top, black outline on exposed sides,
    a fringe of grass on exposed undersides when gravity can flip (the farmer walks there too)."""
    x, y = cell
    ground = y == 5
    height = 5 if ground else 8
    grid = [[th['soil']] * 8 for _ in range(height)]
    open_top = (x, y - 1) not in walls
    open_bottom = (not ground) and (x, y + 1) not in walls
    open_left = (x - 1, y) not in walls
    open_right = (x + 1, y) not in walls
    # soil pebbles: two small stones placed by the tile's own position
    for k in range(2):
        px = 1 + hashed(x, y, k + 1) % 5
        py = 3 + hashed(x, y, k + 7) % (height - 4 if height > 5 else 4)
        if 0 <= py < height and (not open_bottom or py < 5):
            grid[py][px] = th['speck']
            grid[py][px + 1] = th['speck']
    if hashed(x, y, 7) % 5 < 3 and height == 8:          # something dug into the soil, away from the grass and the edges
        picture_rows, own = th['motifs'][hashed(x, y, 9) % len(th['motifs'])]
        small = art(picture_rows, own=own)
        paste(grid, 2 + hashed(x, y, 5) % max(1, 5 - len(small[0])), 3 + hashed(x, y, 6) % max(1, 4 - len(small)), small)
    if open_top:
        for xx in range(8):
            grid[0][xx] = th['grass']
            grid[1][xx] = th['grass']
            if (xx + x * 3) % 3 == 0:
                grid[2][xx] = th['grass']
        grid[0][1 + hashed(x, y, 3) % 6] = th['bloom']
    if open_bottom:
        if under:
            for xx in range(8):
                grid[6][xx] = th['grass']
                if (xx + x) % 3 == 1:
                    grid[5][xx] = th['grass']
        for xx in range(8):
            grid[7][xx] = BLK
    if open_left:
        for yy in range(height):
            grid[yy][0] = BLK
    if open_right:
        for yy in range(height):
            grid[yy][7] = BLK
    # rounded corners
    if open_top and open_left:
        grid[0][0] = -1
    if open_top and open_right:
        grid[0][7] = -1
    if open_bottom and open_left:
        grid[7][0] = -1
    if open_bottom and open_right:
        grid[7][7] = -1
    return grid


def shelf_grid(plank, seam):
    """The wooden shelf under the board: planks with seams and nail heads. Holds the fruit slots and the pet."""
    grid = canvas(64, 8, plank)
    grid[0] = [BLK] * 64
    grid[7] = [BLK] * 64
    for x in range(64):
        grid[3][x] = seam
        grid[5][x] = seam
    for x in range(8, 64, 16):
        for y in range(1, 3):
            grid[y][x] = seam
    for x in range(16, 64, 16):
        for y in range(4, 7):
            grid[y][x] = seam
    for x in range(2, 64, 8):
        grid[1][x] = YEL
    return grid


SLOT = ['mmmmmmmmm'] + ['mkkkkkkkm'] * 6 + ['yyyyyyyyy']
PIP = {'done': ['kkkkk', 'kgggk', 'kgygk', 'kgggk', 'kkkkk'],
       'now': ['kkkkk', 'koook', 'kowok', 'koook', 'kkkkk'],
       'later': ['kkkkk', 'kmmmk', 'kmmmk', 'kmmmk', 'kkkkk']}


def build_scene(index):
    spec = SPECS[index]
    th = THEMES[index]
    out = backdrop(index)
    walls = set(spec['walls'])
    if spec['gravity']:
        beam = canvas(64, 2)
        beam[0] = [MAR if x % 7 else th['speck'] for x in range(64)]
        beam[1] = [GRN] * 64
        out.append(sprite('ceiling-beam', beam, 0, 6, L_EARTH))
    else:
        out.append(sprite('gantry', art(['k' + 'y' * 30 + 'k', 'k' + 'o' * 30 + 'k']), 28, 6, L_GUIDE))
    for i, cell in enumerate(spec['walls']):
        x, y = cell_xy(cell)
        out.append(sprite(f'earth-{i}', earth_grid(th, cell, walls, spec['gravity']), x, y, L_EARTH))
    # the lift's guide posts and the cross rope above the pulleys
    for i, (left, right, top, bottom, _, _) in enumerate(spec['pairs']):
        left_x = cell_xy((left, top))[0] + 4
        right_x = cell_xy((right, top))[0] + 4
        out.append(block(f'cross-rope-{i}', left_x, 9, right_x - left_x + 1, 1, ORG, L_GUIDE))
        for side, column in enumerate((left, right)):
            rail_x, rail_y = cell_xy((column, top))
            rail = [[MAR if (y % 4) else BLK] for y in range((bottom - top) * 8 + 5)]
            out.append(sprite(f'guide-{i}-{side}', rail, rail_x + 3, rail_y, L_GUIDE))
    out.append(sprite('shelf', shelf_grid(*th['shelf']), 0, 53, 20))
    for i in range(len(spec['fruits'])):
        out.append(sprite(f'basket-slot-{i}', art(SLOT), 4 + i * 9, 53, 21))
    track = canvas(64, 3, ORG)
    for x in range(4, 60):
        track[0][x] = track[1][x] = BLK
        track[2][x] = MAR
    out.append(sprite('allowance-track', track, 0, 61, 22))
    top = canvas(64, 6, MAR)             # a wooden beam behind the level pips so their frames show on any sky
    top[0] = [ORG] * 64
    top[5] = [BLK] * 64
    out.append(sprite('level-beam', top, 0, 0, 22))
    for i in range(len(SPECS)):
        kind = 'done' if i < index else 'now' if i == index else 'later'
        out.append(sprite(f'progress-{i}', art(PIP[kind]), 5 + i * 6, 1, 23))
    return out


SCENES = {}


def scene(index):
    if index not in SCENES:
        SCENES[index] = build_scene(index)
    return SCENES[index]


# ───────────────────────── the changing parts of a picture ─────────────────────────
ARROW_UP = ['.yy.', 'yyyy', 'yyyy', '.yy.', '.yy.', '.yy.']


def picture(spec, state, remaining, ctx):
    """Every sprite that can change: crystals, lift parts, basket, switch, farmer, fruit, HUD fill, pet and the
    drifting life. The unchanging furniture comes from scene()."""
    at, gravity, heights, carry, bank, polarity = state
    tick = ctx['tick']
    beat = tick // 3
    index = spec['level']
    sprites = []
    for i, cell in enumerate(spec['crystals']):
        x, y = cell_xy(cell)
        holds = cell in spec['fruits']
        sprites.append(sprite(f'crystal-{i}', crystal_grid(bool(polarity), holds, beat + i * 2), x, y,
                              L_GLASS if holds else L_GUIDE))
    pan_cells = pans(spec, heights)
    for i, (left, right, top, bottom, left_weight, right_weight) in enumerate(spec['pairs']):
        for side, (column, weight) in enumerate(((left, left_weight), (right, right_weight))):
            x, y = cell_xy(pan_cells[i * 2 + side])
            sprites.append(sprite(f'rope-{i}-{side}', [[ORG] for _ in range(max(1, y - 10))], x + 4, 10, L_ROPE))
            sprites.append(sprite(f'pulley-{i}-{side}', pulley_grid(y // 2), x + 2, 7, L_PULLEY))
            sprites.append(sprite(f'pan-{i}-{side}', pan_grid(THEMES[index]), x, y, L_PAN, ['sys_click']))
            for unit in range(weight):
                sprites.append(sprite(f'weight-{i}-{side}-{unit}', art(WEIGHT), x + 1 + unit * 3, y + 4, L_PAN))
    peek = [RED if spec['weights'][k] == 2 else ORG for k in range(len(spec['fruits'])) if bank & (1 << k)]
    bx, by = cell_xy(spec['basket'])
    sprites.append(sprite('basket', basket_grid(peek), bx, by, L_STAND, ['sys_click']))
    if spec['lever'] is not None:
        x, y = cell_xy(spec['lever'])
        sprites.append(sprite('crystal-switch', switch_grid(bool(polarity), beat), x, y, L_STAND, ['sys_click']))
        sprites.append(block('switch-state', x + 5, y + (1 if polarity else 4), 2, 2, YEL if polarity else RED, L_STAND + 1))
    x, y = cell_xy(at)
    sprites.append(sprite('farmer', farmer_grid(ctx['mood'], ctx['face'], ctx['blink'], ctx['step'], gravity < 0),
                          x - 1, y if gravity < 0 else y - 1, L_FARMER, ['sys_click']))
    for i, cell in enumerate(spec['fruits']):
        sx = 5 + i * 9
        layer = L_FRUIT
        if carry == i:
            fx, fy = x, (y - 6 if gravity == 1 else y + 9)   # held overhead, clear of the face
        elif bank & (1 << i):
            fx, fy, layer = sx, 53, 22
        else:
            fx, fy = cell_xy(cell)
        sprites.append(sprite(f'fruit-{i}', fruit_grid(spec['weights'][i], beat + i), fx, fy, layer, ['sys_click']))
        if carry == i:
            for unit in range(spec['weights'][i]):
                sprites.append(block(f'carried-weight-{unit}', x + 1 + unit * 2, y + 8 if gravity == 1 else y - 1, 1, 1, RED, L_FRUIT))
    if spec['gravity']:
        top = 17 if gravity < 0 else 44
        sprites.append(block('gravity-plate', 60, top - 1, 4, 8, BLK, L_GUIDE))
        sprites.append(sprite('gravity-leaf', art(ARROW_UP if gravity < 0 else ARROW_UP[::-1]), 60, top, L_ROPE))
    width = math.ceil(56 * max(0, remaining) / spec['budget'])
    if width:
        fill = canvas(width, 2, GRN if remaining > 40 else RED)
        for xx in range(0, width, 4):                 # twisted-rope highlight along the fuse
            fill[0][xx] = YEL if remaining > 40 else ORG
        sprites.append(sprite('allowance', fill, 4, 61, 23))
    sprites.append(block('allowance-spark', 4 + width, 61, 1, 2, WHT if tick % 2 else YEL, 23))
    sprites.append(pet_sprite(th_pet(index), ctx['mood'], ctx['blink'], tick, ctx['face']))
    sprites.extend(shelf_things(index, tick))
    sprites.extend(ambient(index, tick))
    return sprites


def th_pet(index):
    return THEMES[index]['pet']


# ───────────────────────── effects ─────────────────────────
def sparkles(at, phase):
    """Level-clear shower: stars burst around the farmer, then confetti, long streamers and a few petals rain down the
    whole screen. Every piece wobbles sideways as it falls and each phase is further down, so it reads as a shower."""
    x, y = cell_xy(at)
    out = []
    for i in range(7):
        sx = x + 4 + round(math.cos(i * 0.9 + phase * 0.4) * (6 + phase * 2))
        sy = y + 4 + round(math.sin(i * 0.9 + phase * 0.4) * (5 + phase * 2))
        shape = art(STAR_BIG if (i + phase) % 2 else STAR_SMALL, own={'y': (YEL, WHT, PNK, LBL)[(i + phase) % 4]})
        out.append(sprite(f'sparkle-{i}', shape, sx - 2, sy - 2, L_FX))
    colours = (MAG, YEL, LBL, GRN, ORG, PUR, WHT, RED, BLU)
    for i in range(16):
        cx = 3 + hashed(i, 1, 6) % 58 + round(2 * math.sin(phase + i))
        cy = hashed(i, 2, 6) % 14 - 12 + phase * 14
        if 0 <= cy < 62:
            out.append(block(f'confetti-{i}', cx, cy, 2 if i % 3 else 1, 2 if i % 3 else 3, colours[i % 9], L_FX))
    for i in range(4):                                  # ribbons: a wavy line of three colours
        rx = 8 + i * 15
        top = phase * 12 - 20 + i * 4
        for k in range(10):
            ry = top + k * 2
            if 0 <= ry < 62:
                out.append(block(f'ribbon-{i}-{k}', rx + round(2 * math.sin(k / 2 + phase)), ry, 1, 2,
                                 (MAG, YEL, LBL, GRN)[(i + k // 4) % 4], L_FX))
    return out


DIM_CACHE = {}
CLOUD_DARK = ['..kkkk..kkk.', '.kuuuukkuuuk', 'kuuuuuuuuuuk', 'kuuuuuuuuuuk', '.kkkkkkkkkk.']


def dimmer(level, at):
    """The run-over look: a solid black-and-maroon frame closes in from the edges with a scalloped inner rim in red and
    a darker wedge in each corner, but a clear window is left around the farmer so his weeping face stays easy to read.
    Flat shapes only, no dither. No text."""
    key = (level, at)
    if key not in DIM_CACHE:
        fx, fy = cell_xy(at)[0] + 4, cell_xy(at)[1] + 4
        grid = canvas(64, 64)
        for y in range(64):
            for x in range(64):
                if abs(x - fx) <= 11 and abs(y - fy) <= 11:
                    continue
                edge = min(x, 63 - x, y, 63 - y)
                along = x if min(y, 63 - y) < min(x, 63 - x) else y
                band = level * 2 + (1 if (along // 3) % 2 else 0)
                corner = min(x, 63 - x) + min(y, 63 - y) < level * 5
                if edge < level or corner:
                    grid[y][x] = BLK
                elif edge < band:
                    grid[y][x] = MAR
                elif edge == band and level >= 2:
                    grid[y][x] = RED
        DIM_CACHE[key] = grid
    return sprite('run-over', DIM_CACHE[key], 0, 0, 24)


# Run-over palette swap: bright sky, grass and gold fall to dull reds and purples. Colour indexes only; no greys.
LOSS_SWAP = {WHT: PNK, LBL: MAR, BLU: PUR, GRN: PUR, YEL: ORG, ORG: RED, PNK: MAR, MAG: MAR}
LOSS_KEEP = ('farmer', 'run-over', 'storm-cloud', 'rain-', 'pip', 'fuse')


class Tinted(list):
    """A frame's sprite list that show() recolours as it is put on screen (the run-over look)."""


def tinted(spr):
    """A recoloured copy of one sprite, or the sprite itself when it is one of the parts kept in full colour."""
    if spr.name.startswith(LOSS_KEEP):
        return spr
    grid = [[LOSS_SWAP.get(int(v), int(v)) for v in row] for row in spr.pixels.tolist()]
    return Sprite(grid, name=spr.name, x=spr.x, y=spr.y, layer=spr.layer,
                  blocking=BlockingMode.NOT_BLOCKED, tags=list(spr.tags))


def storm(at, gravity, phase):
    """A little rain cloud over the weeping farmer, with drops that fall."""
    x, y = cell_xy(at)
    top = max(0, y - 13) if gravity == 1 else min(52, y + 10)
    out = [sprite('storm-cloud', art(CLOUD_DARK), x - 2, top, 25)]
    for i in range(3):
        out.append(block(f'rain-{i}', x - 1 + i * 4, top + 5 + (phase * 2 + i * 3) % 6, 1, 2, BLU, 25))
    return out


# ───────────────────────── motion between two pictures ─────────────────────────
def motion(spec, before, after, path, remaining, fraction, ctx):
    sprites = picture(spec, after, remaining, ctx)
    if fraction >= 1:
        return sprites
    old = {s.name: s for s in picture(spec, before, remaining, ctx)}
    # Follow the actual horizontal-then-fall cells, never a diagonal through a shelf.
    walk = [before[0]] + path
    progress = fraction * max(0, len(walk) - 1)
    index = min(int(progress), len(walk) - 1)
    start = cell_xy(walk[index])
    finish = cell_xy(walk[min(index + 1, len(walk) - 1)])
    mx = start[0] + (finish[0] - start[0]) * (progress - index)
    my = start[1] + (finish[1] - start[1]) * (progress - index)
    ax, ay = cell_xy(after[0])
    for sprite_index, spr in enumerate(sprites):
        prior = old.get(spr.name)
        if prior is None:
            continue
        follows = spr.name == 'farmer' or (before[3] == after[3] and after[3] >= 0
                    and (spr.name == f'fruit-{after[3]}' or spr.name.startswith('carried-weight-')))
        if follows:
            spr.set_position(round(spr.x + mx - ax), round(spr.y + my - ay))
        elif spr.name.startswith(('pan-', 'weight-', 'fruit-')):
            spr.set_position(round(prior.x + (spr.x - prior.x) * fraction),
                             round(prior.y + (spr.y - prior.y) * fraction))
        elif spr.name.startswith('rope-'):
            height = round(prior.pixels.shape[0] + (spr.pixels.shape[0] - prior.pixels.shape[0]) * fraction)
            sprites[sprite_index] = sprite(spr.name, [[ORG] for _ in range(max(1, height))], spr.x, spr.y, L_ROPE)
    return sprites


class Bl02(ARCBaseGame):
    def __init__(self):
        self.logical = None
        self.frames = []
        self.history = []
        self.remaining = 0
        self.victory = False
        self.tick = 0
        self.face = 0
        super().__init__(game_id='bl02', levels=[
            Level(sprites=[], name=f'stage-{i + 1}', data={'index': i}) for i in range(len(SPECS))
        ], camera=Camera(background=0), available_actions=AVAILABLE)

    def on_set_level(self, level):
        self.spec = SPECS[level.get_data('index')]
        self.logical = initial(self.spec)
        self.remaining = self.spec['budget']
        self.frames = []
        self.history = []
        self.victory = False
        self.face = 0
        self.show(picture(self.spec, self.logical, self.remaining, self.context()))

    def context(self, offset=0, mood='idle', step=False):
        tick = self.tick + offset
        return {'tick': tick, 'mood': mood, 'face': self.face, 'step': step, 'blink': tick % 19 >= 17}

    def show(self, sprites):
        self.current_level.remove_all_sprites()
        lost = isinstance(sprites, Tinted)
        for item in scene(self.spec['level']):
            self.current_level.add_sprite(tinted(item) if lost else item)
        for item in sprites:
            self.current_level.add_sprite(tinted(item) if lost else item)

    def step(self):
        if self.action.id == GameAction.RESET:
            self.complete_action()
            return
        if not self.frames:
            aid = self.action.id.value
            before = self.logical
            if aid == 7:
                if self.history:
                    # undo puts the scene back but, as in the public games, never refunds spent presses
                    self.logical = self.history.pop()
                after, path = self.logical, [self.logical[0]]
            else:
                command = (6, int(self.action.data.get('x', -1)), int(self.action.data.get('y', -1))) if aid == 6 else aid
                self.history.append(before)
                after, path = transition(self.spec, before, command)
                self.logical = after
                self.remaining -= 1
            if after[0][0] != before[0][0]:
                self.face = 1 if after[0][0] > before[0][0] else -1
            self.victory = won(self.spec, after)
            count = 1 if aid == 7 and before != after else 3 if len(path) <= 1 else min(9, 2 * len(path))
            for frame in range(1, count + 1):
                fraction = frame / count
                ctx = self.context(frame, step=frame % 2 == 0)
                sprites = motion(self.spec, before, after, path, self.remaining, fraction, ctx)
                if before == after and frame < count:
                    x, y = cell_xy(after[0])
                    sprites.append(block('refusal-left', max(0, x - 1), y, 1, 8, ORG, 25))
                    sprites.append(block('refusal-right', min(63, x + 8), y, 1, 8, ORG, 25))
                    sprites.append(block('refusal-top', max(0, x - 1), y, 3, 1, YEL, 25))
                self.frames.append(sprites)
            # A won level bursts into sparkles; a lost run dims to red and the farmer weeps.
            if self.victory:
                for phase in range(5):
                    sprites = picture(self.spec, after, self.remaining, self.context(count + phase, mood='happy'))
                    sprites.extend(sparkles(after[0], phase))
                    self.frames.append(sprites)
            elif self.remaining <= 0:
                for phase in range(1, 6):
                    sprites = Tinted(picture(self.spec, after, self.remaining, self.context(count + phase, mood='sad')))
                    sprites.append(dimmer(min(4, phase), after[0]))
                    sprites.extend(storm(after[0], after[1], phase))
                    self.frames.append(sprites)
            self.tick += count + 5
        self.show(self.frames.pop(0))
        if not self.frames:
            if self.victory:
                self.next_level()
            elif self.remaining <= 0:
                self.lose()
            self.complete_action()
