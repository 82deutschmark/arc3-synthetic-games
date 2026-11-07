# Author: GPT-6 Astra Ultra
# Date: 27-October-2026
# Updated: 07-November-2026, Claude Opus 5.5 -- a second RESET no longer stays on the level (the engine's rule, as in the public games); undo no longer refunds the press.
# PURPOSE: Human-readable NT63 rebuild with fruit ballast, opposite lift pans,
# recoverable cargo, gradual gravity/crystal lessons and genuine engine Undo.
# SRP/DRY check: Pass — native named sprites; one shared pure rule transition is
# used by the engine and offline route verification. No renderer is embedded.
"""Opaque game BL01. Human review remains pending."""

from arcengine import ARCBaseGame, Camera, GameAction, Level, Sprite, BlockingMode
import math

AUTHOR = "GPT-6 Astra Ultra"
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


def block(name, x, y, width, height, color, layer=1):
    return Sprite([[color] * width for _ in range(height)], name=name,
                  x=round(x), y=round(y), layer=layer, blocking=BlockingMode.NOT_BLOCKED)


def icon(name, x, y, pixels, layer=5, clickable=False):
    return Sprite(pixels, name=name, x=round(x), y=round(y), layer=layer,
                  blocking=BlockingMode.NOT_BLOCKED, tags=['sys_click'] if clickable else [])


FARMER = [
    [-1, -1, 12, 12, 12, -1, -1],
    [-1, 11, 11, 11, 11, 11, -1],
    [-1, -1, 12, 5, 12, -1, -1],
    [-1, 10, 12, 12, 12, 10, -1],
    [12, 9, 9, 10, 9, 9, 12],
    [-1, 9, 9, 9, 9, 9, -1],
    [-1, -1, 9, -1, 9, -1, -1],
    [-1, 5, 5, -1, 5, 5, -1],
]
BASKET = [
    [-1, 12, -1, -1, -1, -1, 12, -1],
    [12, -1, -1, -1, -1, -1, -1, 12],
    [12, -1, -1, -1, -1, -1, -1, 12],
    [12, 11, 12, 12, 12, 12, 11, 12],
    [12, 12, 13, 12, 13, 12, 12, 12],
    [-1, 12, 12, 13, 12, 13, 12, -1],
    [-1, 12, 13, 12, 13, 12, 12, -1],
    [-1, -1, 12, 12, 12, 12, -1, -1],
]


def fruit_pixels(weight):
    color = 8 if weight == 2 else 12
    return [
        [-1, -1, -1, 13, 14, -1, -1],
        [-1, -1, color, 13, color, -1, -1],
        [-1, color, 0, color, color, color, -1],
        [color if weight == 3 else -1, color, color, color, color, color, color if weight == 3 else -1],
        [color if weight == 3 else -1, color, 13 if weight == 3 else color, color, 13 if weight == 3 else color, color, color if weight == 3 else -1],
        [-1, color, color, color, color, color, -1],
        [-1, -1, 13, 13, 13, -1, -1],
    ]


def picture(spec, state, remaining):
    at, gravity, heights, carry, bank, polarity = state
    sprites = []
    # Each terrain tile, lift component, fruit and farmer remains a named object.
    if spec['gravity']:
        sprites.append(block('ceiling-beam', 4, 6, 56, 2, 13, 2))
        sprites.append(block('ceiling-contact', 4, 7, 56, 1, 14, 3))
    for index, cell in enumerate(spec['walls']):
        x, y = cell_xy(cell)
        sprites.extend((block(f'earth-{index}', x, y, 8, 5 if cell[1] == 5 else 8, 13),
                        block(f'grass-{index}', x, y, 8, 2, 14, 2)))
        if cell[1] == 5:
            sprites.append(block(f'root-{index}', x + 3, y + 3, 2, 1, 12, 2))
    for index, cell in enumerate(spec['crystals']):
        x, y = cell_xy(cell)
        pixels = [[-1] * 8 for _ in range(8)]
        for yy in range(8):
            for xx in range(8):
                if polarity:
                    pixels[yy][xx] = 10 if xx in (0, 7) or yy in (0, 7) else 9
                    if cell in spec['fruits'] and 1 <= xx <= 6 and 1 <= yy <= 6:
                        pixels[yy][xx] = -1
                elif (xx + yy) % 4 == 0 and (xx in (0, 7) or yy in (0, 7)):
                    pixels[yy][xx] = 10
        sprites.append(icon(f'crystal-{index}', x, y, pixels, 13 if cell in spec['fruits'] else 3))
    pan_cells = pans(spec, heights)
    for index, (left, right, top, bottom, left_weight, right_weight) in enumerate(spec['pairs']):
        left_x = cell_xy((left, top))[0] + 4
        right_x = cell_xy((right, top))[0] + 4
        sprites.append(block(f'cross-rope-{index}', left_x, 9, right_x - left_x + 1, 1, 12, 2))
        for side, (column, weight) in enumerate(((left, left_weight), (right, right_weight))):
            rail_x, rail_y = cell_xy((column, top))
            sprites.append(block(f'guide-{index}-{side}', rail_x + 3, rail_y,
                                 1, (bottom - top) * 8 + 5, 1, 1))
            x, y = cell_xy(pan_cells[index * 2 + side])
            sprites.append(block(f'rope-{index}-{side}', x + 4, 10, 1, max(1, y - 10), 12, 2))
            sprites.append(icon(f'pulley-{index}-{side}', x + 2, 7,
                                [[-1, 13, 13, -1], [13, 11, 11, 13],
                                 [13, 11, 11, 13], [-1, 13, 13, -1]], 4))
            pan = [[12] * 8, [11] * 8, [12, 13, 13, 13, 13, 13, 13, 12],
                   [-1, 12, 12, 12, 12, 12, 12, -1]]
            sprites.append(icon(f'pan-{index}-{side}', x, y, pan, 5, True))
            # Permanent ballast hangs below each pan in large countable blocks.
            for unit in range(weight):
                sprites.append(block(f'weight-{index}-{side}-{unit}', x + 1 + unit * 3,
                                     y + 4, 2, 3, 3, 6))
    bx, by = cell_xy(spec['basket'])
    sprites.append(icon('basket', bx, by, BASKET, 8, True))
    if spec['lever'] is not None:
        x, y = cell_xy(spec['lever'])
        sprites.append(icon('crystal-switch', x, y,
                            [[-1, -1, 10, 10, -1, -1, -1, -1],
                             [-1, 10, 9, 9, 10, -1, -1, -1],
                             [-1, -1, 10, 10, -1, -1, -1, -1],
                             [-1, -1, 12, -1, -1, -1, -1, -1],
                             [-1, -1, 12, -1, -1, -1, -1, -1],
                             [-1, -1, 12, -1, -1, -1, -1, -1],
                             [13, 13, 13, 13, 13, 13, -1, -1],
                             [12, 12, 12, 12, 12, 12, -1, -1]], 7, True))
        sprites.append(block('switch-state', x + 5, y + (1 if polarity else 4), 2, 2, 10, 8))
    x, y = cell_xy(at)
    sprites.append(icon('farmer', x, y, FARMER if gravity == 1 else FARMER[::-1], 10, True))
    for index, cell in enumerate(spec['fruits']):
        sx = 5 + index * 9
        sprites.append(block(f'basket-slot-{index}', sx - 1, 57, 8, 3, 12, 3))
        if carry == index:
            fx, fy = x + 5, y - 3 if gravity == 1 else y + 4
        elif bank & (1 << index):
            fx, fy = sx, 53
        else:
            fx, fy = cell_xy(cell)
        sprites.append(icon(f'fruit-{index}', fx, fy, fruit_pixels(spec['weights'][index]), 12, True))
        if carry == index:
            for unit in range(spec['weights'][index]):
                sprites.append(block(f'carried-weight-{unit}', x + 1 + unit * 2, y + 8, 1, 1, 8, 13))
    if spec['gravity']:
        leaf = [[-1, 14, -1], [14, 14, 14], [-1, 14, -1], [-1, 12, -1]]
        sprites.append(icon('gravity-leaf', 59, 17 if gravity < 0 else 44,
                            leaf if gravity > 0 else leaf[::-1], 9))
    sprites.append(block('allowance-track', 4, 61, 56, 2, 3, 20))
    width = math.ceil(56 * max(0, remaining) / spec['budget'])
    if width:
        sprites.append(block('allowance', 4, 61, width, 2, 14 if remaining > 40 else 8, 21))
    return sprites


def motion(spec, before, after, path, remaining, fraction):
    sprites = picture(spec, after, remaining)
    if fraction >= 1:
        return sprites
    old = {s.name: s for s in picture(spec, before, remaining)}
    # Follow actual horizontal-then-fall cells, never a diagonal through a shelf.
    walk = [before[0]] + path
    progress = fraction * max(0, len(walk) - 1)
    index = min(int(progress), len(walk) - 1)
    start = cell_xy(walk[index])
    finish = cell_xy(walk[min(index + 1, len(walk) - 1)])
    mx = start[0] + (finish[0] - start[0]) * (progress - index)
    my = start[1] + (finish[1] - start[1]) * (progress - index)
    ax, ay = cell_xy(after[0])
    for sprite_index, sprite in enumerate(sprites):
        prior = old.get(sprite.name)
        if prior is None:
            continue
        follows = sprite.name == 'farmer' or (before[3] == after[3] and after[3] >= 0
                    and (sprite.name == f'fruit-{after[3]}' or sprite.name.startswith('carried-weight-')))
        if follows:
            sprite.set_position(round(sprite.x + mx - ax), round(sprite.y + my - ay))
        elif sprite.name.startswith(('pan-', 'weight-', 'fruit-')):
            sprite.set_position(round(prior.x + (sprite.x - prior.x) * fraction),
                                round(prior.y + (sprite.y - prior.y) * fraction))
        elif sprite.name.startswith('rope-'):
            height = round(prior.pixels.shape[0] + (sprite.pixels.shape[0] - prior.pixels.shape[0]) * fraction)
            sprites[sprite_index] = block(sprite.name, sprite.x, sprite.y, 1, max(1, height), 12, 2)
    return sprites


class Bl01(ARCBaseGame):
    def __init__(self):
        self.logical = None
        self.frames = []
        self.history = []
        self.remaining = 0
        self.victory = False
        super().__init__(game_id='bl01', levels=[
            Level(sprites=[], name=f'stage-{i + 1}', data={'index': i}) for i in range(len(SPECS))
        ], camera=Camera(background=0), available_actions=AVAILABLE)

    def on_set_level(self, level):
        self.spec = SPECS[level.get_data('index')]
        self.logical = initial(self.spec)
        self.remaining = self.spec['budget']
        self.frames = []
        self.history = []
        self.victory = False
        self.show(picture(self.spec, self.logical, self.remaining))

    def show(self, sprites):
        self.current_level.remove_all_sprites()
        for sprite in sprites:
            self.current_level.add_sprite(sprite)
        for index in range(len(SPECS)):
            self.current_level.add_sprite(block(f'progress-{index}', 5 + index * 6, 2, 4, 3,
                                               14 if index < self.level_index else 12 if index == self.level_index else 1, 20))

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
            self.victory = won(self.spec, after)
            count = 1 if aid == 7 and before != after else 3 if len(path) <= 1 else min(10, 2 * len(path))
            for frame in range(1, count + 1):
                fraction = frame / count
                sprites = motion(self.spec, before, after, path, self.remaining, fraction)
                if before == after and frame < count:
                    x, y = cell_xy(after[0])
                    sprites.append(block('refusal-left', max(0, x - 1), y, 1, 8, 12, 25))
                    sprites.append(block('refusal-right', min(63, x + 8), y, 1, 8, 12, 25))
                self.frames.append(sprites)
        self.show(self.frames.pop(0))
        if not self.frames:
            if self.victory:
                self.next_level()
            elif self.remaining <= 0:
                self.lose()
            self.complete_action()
