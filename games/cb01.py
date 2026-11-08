# Author: Claude Sonnet 5.5
# Date: 08-Nov-2026
# PURPOSE: CB01, a small card battler in the style of Clash Royale. Three enemy towers stand along the top of the
#   field; you hold a finite hand of unit cards. Action 5 flips to the next card (free), a click inside the blue drop
#   band at the bottom of the field puts the chosen unit down, and the world then plays one beat (two steps): units
#   walk slowly toward the nearest tower, fight whatever is in reach, towers shoot back. Each beat darkens one shade of
#   a sixteen-shade wheel and the shade never comes back. Take down all three towers before the wheel is dark.
#   An arrow key plays one beat with no card (the waiting move, it costs a shade like any beat). Undo takes the board
#   and the hand back one beat but NOT the shade. A lost level is shown (wheel dark, towers flash) in the same press that
#   ends it; RESET follows the engine's rule (no custom reset). There is no text on the play surface.
#   The rules are plain functions at the top (no engine needed), so solutions/cb01_clear_levels.py can search them and
#   then replay the route in the real engine. Art is named Sprites rebuilt from the state on every frame.
# Integration: tools/runtime.py loads the class Cb01; tools/make_media.py renders the opening of every level from
#   on_set_level, so the board is built there, never lazily.
# SRP/DRY check: Pass - searched games/ for a card or tower game: none exists. Sprite helpers follow te01/ss01 idioms.
"""cb01: Beat Wheel card battler (see docs/08-Nov-2026-cb01-card-battler-plan.md)."""
from __future__ import annotations

import numpy as np
from arcengine import ARCBaseGame, BlockingMode, Camera, Level, Sprite

_NOBLOCK = BlockingMode.NOT_BLOCKED

# ---------------------------------------------------------------- geometry (all in 64x64 frame pixels)
COLS, CELL = 8, 8
BAND_ROW = 5                      # the drop band: frame rows 40-47
TOP_FIELD_ROW = 2                 # towers and wall fill rows 0-1, so units stop at row 2
TOWER_C0 = (0, 3, 6)              # first column of each tower; each is two columns wide
GATE_COLS = (2, 5)                # the wall between towers; enemy pushers come out of these
BEAT_STEPS = 2                    # world steps per beat
SHADES = 16                       # eight wedges, two shades each
WHEEL_X, WHEEL_Y, WHEEL_R = 48, 48, 7
CARD_W, CARD_H, CARD_STEP, HAND_Y = 8, 12, 9, 51

# ---------------------------------------------------------------- units
# move: a unit moves one cell every `move` steps (0 = never). every: it attacks every `every` steps with `hits` blows.
KINDS = {
    'walker': dict(hp=2, dmg=1, hits=1, move=1, every=1, reach=1),
    'tank':   dict(hp=6, dmg=2, hits=1, move=2, every=2, reach=1),
    'archer': dict(hp=1, dmg=1, hits=1, move=1, every=1, reach=3),
    'runner': dict(hp=2, dmg=1, hits=2, move=1, every=1, reach=1),
    'guard':  dict(hp=3, dmg=1, hits=1, move=0, every=1, reach=1),
    'pusher': dict(hp=2, dmg=1, hits=1, move=1, every=1, reach=1),
}
ME, FOE = 0, 1

# ---------------------------------------------------------------- levels
# tower_dmg 0 means the towers do not shoot. dark is how many shades start dark. pushers maps a beat count to a gate column.
LEVELS = [
    # 1: straight to the tower. Walkers only, towers do not shoot; the column you click picks the tower.
    dict(name='cb01-1', hand=['walker', 'walker', 'walker'], towers=[2, 2, 2], tower_dmg=0, tower_range=2, tower_every=1,
         guards=[], pushers={}, dark=11),
    # 2: towers shoot, so the walkers need the tank in front soaking the shots.
    dict(name='cb01-2', hand=['tank', 'walker', 'walker', 'walker'], towers=[2, 2, 2], tower_dmg=1, tower_range=2,
         tower_every=1, guards=[], pushers={}, dark=10),
    # 3: towers hit hard but only reach two cells; the archer reaches three. Guards stand in the way of the walkers.
    dict(name='cb01-3', hand=['tank', 'walker', 'archer', 'archer', 'archer'], towers=[2, 2, 2], tower_dmg=3, tower_range=2,
         tower_every=1, guards=[(1, 2), (7, 2)], pushers={}, dark=11),
    # 4: a short wheel: the tank soaks while the runners (two blows a step) finish before time is up.
    dict(name='cb01-4', hand=['walker', 'tank', 'runner', 'runner', 'runner'], towers=[3, 3, 3], tower_dmg=1, tower_range=2,
         tower_every=1, guards=[], pushers={}, dark=10),
    # 5: three different towers: a guarded one, a tough one behind a guard, a plain one. One spammed card cannot win.
    dict(name='cb01-5', hand=['tank', 'archer', 'walker', 'runner', 'archer'], towers=[3, 4, 3], tower_dmg=1, tower_range=2,
         tower_every=1, guards=[(0, 2), (4, 2)], pushers={}, dark=10),
    # 6: the push. Enemy pushers come out of the gates (a lit gate shows one coming); one that reaches the band costs a shade.
    dict(name='cb01-6', hand=['tank', 'archer', 'runner', 'walker', 'archer'], towers=[3, 4, 3], tower_dmg=1, tower_range=2,
         tower_every=1, guards=[(4, 2)], pushers={0: 2, 1: 5, 2: 2}, dark=10),
]


# ================================================================ rules (pure, no engine)
class Unit:
    __slots__ = ('uid', 'kind', 'side', 'col', 'row', 'hp', 'age')

    def __init__(self, uid, kind, side, col, row):
        self.uid, self.kind, self.side, self.col, self.row = uid, kind, side, col, row
        self.hp, self.age = KINDS[kind]['hp'], 0

    def copy(self):
        other = Unit.__new__(Unit)
        for name in Unit.__slots__:
            setattr(other, name, getattr(self, name))
        return other

    def key(self):
        return (self.uid, self.kind, self.col, self.row, self.hp, self.age % 2)


class State:
    """Everything that changes while a level is played. `dark` is the wheel: undo leaves it alone."""
    __slots__ = ('units', 'towers', 'hand', 'sel', 'dark', 'beat', 'tick', 'next_id', 'waiting')

    def copy(self):
        other = State.__new__(State)
        other.units = [u.copy() for u in self.units]
        other.towers, other.hand, other.waiting = list(self.towers), list(self.hand), list(self.waiting)
        other.sel, other.dark, other.beat, other.tick, other.next_id = self.sel, self.dark, self.beat, self.tick, self.next_id
        return other

    def key(self):
        return (tuple(u.key() for u in self.units), tuple(self.towers), tuple(self.hand), self.sel, self.dark, self.beat,
                self.tick % 2, tuple(self.waiting))


def new_state(level):
    st = State()
    st.units, st.towers, st.hand, st.sel = [], list(level['towers']), list(level['hand']), 0
    st.dark, st.beat, st.tick, st.next_id, st.waiting = level['dark'], 0, 0, 1, []
    for col, row in level['guards']:
        st.units.append(Unit(st.next_id, 'guard', FOE, col, row))
        st.next_id += 1
    return st


def tower_distance(col, row, tower):
    """Chebyshev distance from a cell to a tower's two-by-two block (rows 0-1)."""
    c0 = TOWER_C0[tower]
    return max(c0 - col, 0, col - (c0 + 1), row - 1, 0)


def unit_distance(a, b):
    return max(abs(a.col - b.col), abs(a.row - b.row))


def occupied(st, col, row):
    return any(u.col == col and u.row == row for u in st.units)


def pick_target(st, unit):
    """What a unit hits this step: ('u', unit) or ('t', tower index), or None when nothing is in reach."""
    reach = KINDS[unit.kind]['reach']
    best = None
    if unit.side == ME:
        for other in st.units:
            if other.side == FOE and unit_distance(unit, other) <= reach:
                cand = (unit_distance(unit, other), 0, other.uid, ('u', other))
                best = min(best, cand, key=lambda c: c[:3]) if best else cand
        for index, hp in enumerate(st.towers):
            if hp > 0 and tower_distance(unit.col, unit.row, index) <= reach:
                cand = (tower_distance(unit.col, unit.row, index), 1, index, ('t', index))
                best = min(best, cand, key=lambda c: c[:3]) if best else cand
    else:
        for other in st.units:
            if other.side == ME and unit_distance(unit, other) <= reach:
                cand = (unit_distance(unit, other), 0, other.uid, ('u', other))
                best = min(best, cand, key=lambda c: c[:3]) if best else cand
    return best[3] if best else None


def tower_target(st, level, index):
    best = None
    for other in st.units:
        if other.side == ME:
            d = tower_distance(other.col, other.row, index)
            if d <= level['tower_range'] and (best is None or (d, other.uid) < best[:2]):
                best = (d, other.uid, other)
    return best[2] if best else None


def nearest_tower(st, unit):
    best = None
    for index, hp in enumerate(st.towers):
        if hp > 0:
            cand = (tower_distance(unit.col, unit.row, index), index)
            best = cand if best is None or cand < best else best
    return best[1] if best else None


def cell_center(col, row):
    return (col * CELL + CELL // 2, row * CELL + CELL // 2)


def tower_center(index):
    return (TOWER_C0[index] * CELL + CELL, CELL)


def world_step(level, st):
    """One step of the world. Returns (events, leaks). Events are for drawing: ('hit', (x, y), (sx, sy), ranged)."""
    events, leaks = [], 0
    st.tick += 1
    for u in st.units:
        u.age += 1
    # a waiting pusher comes out of the gate as soon as the cell is free
    for col in list(st.waiting):
        if not occupied(st, col, TOP_FIELD_ROW):
            st.units.append(Unit(st.next_id, 'pusher', FOE, col, TOP_FIELD_ROW))
            st.next_id += 1
            st.waiting.remove(col)
    hits, busy = [], set()
    for u in sorted(st.units, key=lambda x: x.uid):
        target = pick_target(st, u)
        if target is not None:
            busy.add(u.uid)
            k = KINDS[u.kind]
            if u.age % k['every'] == 0:
                hits.append((u, target, k['dmg'] * k['hits']))
    if level['tower_dmg'] and st.tick % level['tower_every'] == 0:
        for index, hp in enumerate(st.towers):
            if hp > 0:
                victim = tower_target(st, level, index)
                if victim is not None:
                    hits.append((('tower', index), ('u', victim), level['tower_dmg']))
    for shooter, target, dmg in hits:
        if isinstance(shooter, tuple):
            source, ranged = tower_center(shooter[1]), True
        else:
            source, ranged = cell_center(shooter.col, shooter.row), unit_distance_to(shooter, target) > 1
        if target[0] == 'u':
            target[1].hp -= dmg
            events.append(('hit', cell_center(target[1].col, target[1].row), source, ranged))
        else:
            st.towers[target[1]] = max(0, st.towers[target[1]] - dmg)
            events.append(('hit', tower_center(target[1]), source, ranged))
    st.units = [u for u in st.units if u.hp > 0]
    # movement: friendly units walk up toward the nearest tower, enemy pushers walk down
    for u in sorted(st.units, key=lambda x: (x.row if x.side == ME else -x.row, x.uid)):
        k = KINDS[u.kind]
        if u.uid in busy or not k['move'] or u.age % k['move']:
            continue
        if u.side == ME:
            tower = nearest_tower(st, u)
            if tower is None:
                continue
            options = [(u.col, u.row - 1)]
            centre = TOWER_C0[tower] + 0.5
            if u.col != int(centre):
                step = 1 if centre > u.col else -1
                options.append((u.col + step, u.row))
            for col, row in options:
                if row >= TOP_FIELD_ROW and 0 <= col < COLS and not occupied(st, col, row):
                    u.col, u.row = col, row
                    break
        else:
            if u.row + 1 >= BAND_ROW:
                u.hp = 0
                leaks += 1
            elif not occupied(st, u.col, u.row + 1):
                u.row += 1
    st.units = [u for u in st.units if u.hp > 0]
    return events, leaks


def unit_distance_to(unit, target):
    if target[0] == 'u':
        return unit_distance(unit, target[1])
    return tower_distance(unit.col, unit.row, target[1])


def won(st):
    return all(hp <= 0 for hp in st.towers)


def can_deploy(st, col):
    return bool(st.hand) and 0 <= col < COLS and not occupied(st, col, BAND_ROW)


def run_beat(level, st, deploy=None, frames=None):
    """Play one beat in place. deploy is a column or None (a pass). frames, if given, collects (state copy, events, mark).
    Returns 'win', 'lose' or None. The shade goes dark at the END of the beat, so the last beat still plays out."""
    if deploy is not None:
        kind = st.hand.pop(st.sel)
        st.units.append(Unit(st.next_id, kind, ME, deploy, BAND_ROW))
        st.next_id += 1
        st.sel = min(st.sel, max(0, len(st.hand) - 1))
    if st.beat in level['pushers']:
        st.waiting.append(level['pushers'][st.beat])
    if frames is not None:
        frames.append((st.copy(), [], 'drop'))
    for _ in range(BEAT_STEPS):
        events, leaks = world_step(level, st)
        st.dark = min(SHADES, st.dark + leaks)
        if frames is not None:
            frames.append((st.copy(), events, 'step'))
        if won(st):
            return 'win'
    st.dark = min(SHADES, st.dark + 1)
    st.beat += 1
    if frames is not None:
        frames.append((st.copy(), [], 'shade'))
    return 'lose' if st.dark >= SHADES else None


def cycle(st):
    if len(st.hand) > 1:
        st.sel = (st.sel + 1) % len(st.hand)


# ================================================================ art (named sprites)
def pic(rows):
    return np.array([[-1 if ch == '.' else int(ch, 16) for ch in row] for row in rows], dtype=np.int8)


ART = {
    'walker': pic(['..99..', '.9999.', '.9009.', '.9999.', '..99..', '.5..5.']),
    'tank': pic(['.5555.', '5ffff5', '5f00f5', '5ffff5', '5ffff5', '.5..5.']),
    'archer': pic(['..bb..', '..bb.5', '.bbb5.', '..bb5.', '..bb.5', '.b..b.']),
    'runner': pic(['...aa.', '..aaaa', '0.aa0a', '.0aaaa', '..aaa.', '..a.a.']),
    'guard': pic(['.8888.', '8dddd8', '8d88d8', '8dddd8', '.8dd8.', '.5..5.']),
    'pusher': pic(['..cc..', '.cccc.', '.c55c.', '.cccc.', '..cc..', '.8..8.']),
}
RUBBLE = pic(['................', '................', '................', '................', '................', '................',
              '................', '................', '................', '.....c..........', '..d..cc....d....', '.dd.cddc..dd..c.',
              '8dd8cdd8c.d8d.cc', '88d88dd88dcd88d8', 'd8888d8888d8888d', 'dd8dd8dd8dd8dd8d'])


def tower_pixels(hp, max_hp, flash):
    body, trim = (7, 6) if flash else (8, 13)
    px = np.full((16, 16), body, dtype=np.int8)
    px[0:3, :] = trim
    for x in range(1, 16, 4):
        px[0:2, x:x + 2] = 10                        # battlements (sky shows through)
    px[3:7, 2:4] = px[3:7, 12:14] = 5                 # windows
    px[8:16, 6:10] = trim
    px[10:16, 7:9] = 5                                # door
    px[:, 0] = px[:, 15] = trim
    for i in range(max_hp):                           # health pips along the base
        px[13:15, 1 + i * 3: 3 + i * 3] = 11 if i < hp else 13
    return px


def wall_pixels(gate_open):
    px = np.full((16, 8), 13, dtype=np.int8)
    px[3::4, :] = 8
    if gate_open:
        px[6:16, 1:7] = 5
        px[6:9, 2:6] = 12                              # an enemy is about to come out of this gate
    return px


def card_pixels(kind, selected):
    px = np.full((CARD_H, CARD_W), 5, dtype=np.int8)
    edge = 11 if selected else 0
    px[0, :] = px[-1, :] = edge
    px[:, 0] = px[:, -1] = edge
    art = ART[kind]
    px[3:9, 1:7] = np.where(art >= 0, art, 5)
    return px


def wheel_pixels(dark, flash):
    """Eight wedges, each an outer ring and an inner disc: sixteen shades. Lit = yellow, next to go = orange, gone = maroon."""
    size = WHEEL_R * 2 + 1
    px = np.full((size, size), -1, dtype=np.int8)
    for y in range(size):
        for x in range(size):
            dx, dy = x - WHEEL_R, y - WHEEL_R
            r = (dx * dx + dy * dy) ** 0.5
            if r > WHEEL_R + 0.3:
                continue
            if r > WHEEL_R - 0.8:
                px[y, x] = 0
                continue
            angle = (np.degrees(np.arctan2(dx, -dy)) + 360) % 360
            index = int(angle // 45) * 2 + (1 if r < 3.6 else 0)
            if r < 0.6:
                px[y, x] = 5
            elif index < dark:
                px[y, x] = 13
            elif index == dark:
                px[y, x] = 0 if flash else 12
            else:
                px[y, x] = 11
    return px


def build_sprites(level, view):
    """All the sprites for one frame. view = (state, events, mark). Layers: ground 0, wall/towers 1, units 3, effects 5."""
    st, events, mark = view
    out = []

    def add(name, pixels, x, y, layer):
        out.append(Sprite(pixels=pixels, name=name, x=x, y=y, layer=layer, blocking=_NOBLOCK, tags=[name.split('-')[0]]))

    band_flash = mark == 'refuse'
    add('band', np.full((CELL, 64), 11 if band_flash else 10, dtype=np.int8), 0, BAND_ROW * CELL, 0)
    add('hudbar', np.full((16, 64), 5, dtype=np.int8), 0, 48, 0)
    out[-1].pixels[0, :] = 11
    flash = mark == 'lose-flash'
    for gate in GATE_COLS:
        coming = level['pushers'].get(st.beat) == gate
        add(f'wall-{gate}', wall_pixels(coming or gate in st.waiting), gate * CELL, 0, 1)
    for index, hp in enumerate(st.towers):
        x = TOWER_C0[index] * CELL
        if hp > 0:
            add(f'tower-{index}', tower_pixels(hp, level['towers'][index], flash), x, 0, 2)
        else:
            add(f'rubble-{index}', RUBBLE, x, 0, 2)
    for u in st.units:
        add(f'unit-{u.uid}-{u.kind}', ART[u.kind], u.col * CELL + 1, u.row * CELL + 1, 3)
        k = KINDS[u.kind]
        if u.hp < k['hp']:                                # a shrinking life bar under hurt units
            bar = np.full((1, 6), -1, dtype=np.int8)
            bar[0, :max(1, 6 * u.hp // k['hp'])] = 14 if u.side == ME else 8
            add(f'life-{u.uid}', bar, u.col * CELL + 1, u.row * CELL + 7, 4)
    for index, kind in enumerate(st.hand):
        add(f'card-{index}', card_pixels(kind, index == st.sel), 1 + index * CARD_STEP, HAND_Y - (2 if index == st.sel else 0), 3)
    if not st.hand:
        add('go', pic(['b....', 'bb...', 'bbb..', 'bb...', 'b....']), 6, 54, 3)   # an empty hand: press an arrow to play on
    add('wheel', wheel_pixels(st.dark, mark in ('shade', 'undo')), WHEEL_X, WHEEL_Y, 3)
    for kind, target, source, ranged in events:
        if ranged:
            add('shot', np.full((2, 2), 11, dtype=np.int8), (target[0] + source[0]) // 2 - 1, (target[1] + source[1]) // 2 - 1, 5)
        add('spark', np.full((3, 3), 0, dtype=np.int8), target[0] - 1, target[1] - 1, 5)
    if mark == 'win':
        for i, (sx, sy) in enumerate(((10, 10), (30, 6), (52, 12), (20, 30), (44, 26), (58, 36))):
            add(f'glint-{i}', pic(['.b.', 'bbb', '.b.']), sx, sy, 5)
    return out




# ================================================================ engine glue
class Cb01(ARCBaseGame):
    def __init__(self):
        self.level_def = LEVELS[0]
        self.st = new_state(self.level_def)
        self.history = []
        self.pending = []
        self.after = None
        levels = [Level(sprites=[], grid_size=(64, 64), data={}, name=item['name']) for item in LEVELS]
        camera = Camera(0, 0, 64, 64, 14, 14, [])
        super().__init__('cb01', levels, camera, False, len(levels), [1, 2, 3, 4, 5, 6, 7])

    # RESET follows the engine's rule: everything is rebuilt here, for full resets and level resets alike.
    def on_set_level(self, level):
        self.level_def = LEVELS[self.level_index]
        self.st = new_state(self.level_def)
        self.history, self.pending, self.after = [], [], None
        self.show((self.st, [], None))

    def show(self, view):
        self.current_level.remove_all_sprites()
        for sprite in build_sprites(self.level_def, view):
            self.current_level.add_sprite(sprite)

    def queue_beat(self, deploy):
        """Snapshot for undo, play the beat in the rules, and line its frames up for step()."""
        snapshot = self.st.copy()
        frames = []
        outcome = run_beat(self.level_def, self.st, deploy, frames)
        self.history.append(snapshot)
        self.pending = list(frames)
        last = frames[-1][0]
        if outcome == 'win':
            self.pending += [(last, [], 'win')] * 3
        elif outcome == 'lose':
            self.pending += [(last, [], 'lose-flash'), (last, [], None)] * 2
        self.after = outcome

    def step(self):
        if self.pending:
            self.show(self.pending.pop(0))
            if self.pending:
                return
            self.finish()
            return
        action = self.action.id.value
        data = self.action.data or {}
        if action == 0:
            self.complete_action()
            return
        if action == 5:
            cycle(self.st)
            self.show((self.st, [], None))
        elif action in (1, 2, 3, 4):
            self.queue_beat(None)
            return self.step()
        elif action == 6:
            x, y = data.get('x', -1), data.get('y', -1)
            col = int(x // CELL) if isinstance(x, (int, float)) else -1
            if self.st.hand and BAND_ROW * CELL <= y < (BAND_ROW + 1) * CELL and can_deploy(self.st, col):
                self.queue_beat(col)
                return self.step()
            self.show((self.st, [], 'refuse'))          # a bad click costs nothing; the band flashes
            self.pending = [(self.st, [], None)]
            return
        elif action == 7:
            if self.history:
                dark = self.st.dark
                self.st = self.history.pop()
                self.st.dark = dark                        # undo never gives a shade back
            self.show((self.st, [], 'undo'))
            self.pending = [(self.st, [], None)]
            return
        self.complete_action()

    def finish(self):
        outcome, self.after = self.after, None
        self.complete_action()
        if outcome == 'win':
            self.next_level()
        elif outcome == 'lose':
            self.lose()
