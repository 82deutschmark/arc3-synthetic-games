# Author: Claude Sonnet 5.5
# Date: 07-November-2026
# PURPOSE: WB03, the glow-up of WB02 (Windy Boats), at Mark Barney's call: the small fixed harbour becomes a large
#   open sea you see through a 64x64 window that follows the boat you steer, with far more to look at and sail
#   round. The heart is WB02's: you steer ONE sailboat, and every move of the boat you steer is a gust for every
#   other boat with its sail up, so the boats you are not touching are the real puzzle; a boat drops anchor only
#   when you hand control away while it sits in its own berth, in its own colour. Eight different seas (open
#   water, lee shores, a kraken, pirate ships, streams, a night sea where the wind turns, a serpent strait, and a
#   great sea that mixes them), each a world several screens across, dressed with palm islands, lighthouses,
#   huts and fires, reefs, shoals, buoys, wrecks, barrels, wind socks and flags. Boats that drift out of the
#   window are shown by arrows in their colour on the window edge (click one to steer that boat). Every deadly
#   thing is drawn and moves on a rhythm tied to your moves, and the water it will threaten after your next move
#   is marked with red stripes. A move counter (a draining bar, no text) ends the run when it is empty.
# SRP/DRY check: Pass. One self-contained file, as the other games here are. The rules are small pure functions
#   (part one) used both by the game and by the search that sized the counters; the art is drawn from text rows and
#   small functions (parts three to five) and never touches the rules; the game class (part six) only owns the
#   state, the counter and the animation frames. Nothing is copied from another game here except the idea of a
#   scrolling window drawn by a display layer.
# CHANGELOG: 07-Nov-2026 (Claude Sonnet 5.5) -- first version of WB03, a new game id built from WB02's idea.
"""WB03 -- a windy sea of boats.

Arrows steer the boat with the white corner marks, one sea cell at a time. Each time it moves, every other
boat that has its sail up catches a gust and is blown one cell downwind (the flag and the arrow under the sea show
the wind). A sail hangs slack, and the boat stays put, when an island or another sail stands between it and the
wind, or when the boat sits on a shoal. Space (action five) or a click on a boat, or on its arrow at the window
edge, hands control to another boat; if the boat you leave is in its own coloured berth it drops anchor and stays
there. Bring every boat to its berth before the bar empties. Water marked with red stripes is deadly after your
next move: whirlpools, tentacles, serpents and the broadside of a pirate ship (its gun ports light one by one,
and when all are lit the next move fires). Undo (action seven) takes a move back but not the move spent.
"""
from __future__ import annotations

import math

import numpy as np

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay

# ====================================================================================================
# PART ONE: THE RULES. Pure functions on a small immutable state, shared by the game (which animates
# what they decide) and by the search that sized the counters. Nothing here draws.
# ====================================================================================================

# Palette names (the 16-colour ARC palette). There is no grey in this game on purpose.
WHT, BLK, MAG, PNK, RED, BLU, LBL, YEL, ORG, MAR, GRN, PUR = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15

UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)
STEER = {1: UP, 2: DOWN, 3: LEFT, 4: RIGHT}
SHELTER_REACH = 3        # an upright sail or an island breaks the wind for this many cells downwind
FIRE_REACH = 7           # a pirate broadside carries this far unless something solid stops it
BOAT_COLOURS = (ORG, MAG, GRN)
COUNTER_UNIT = 4         # one block of the move bar is this many moves; the fine row under it drains by one per move

CELL = 6                 # pixels per sea cell
VIEW_W, VIEW_H = 64, 54  # the window onto the sea; the strip under it (10 rows) is the fixed HUD


class Sea:
    """One level's sea: the grid, the boats' berths, the wind, and every creature with its fixed rhythm."""

    def __init__(self, w, h, theme):
        self.w, self.h, self.theme = w, h, theme
        self.grid = [['.'] * w for _ in range(h)]
        self.current = {}            # (x, y) -> (dx, dy): the stream that carries any boat sailing on it
        self.starts, self.goals = [], []
        self.winds, self.wind_every = [RIGHT], 0
        self.krakens, self.serpents, self.ships = [], [], []
        self.barrels = ()
        self.reserved = []           # cells the scatter of extra reefs and islets must leave alone
        self.props = []              # (kind, x, y): huts, fires, lighthouses, wrecks, wind socks on the islands
        self.counter = 0

    # ---- building helpers -------------------------------------------------------------------------------
    def put(self, ch, cells):
        for (x, y) in cells:
            self.grid[y][x] = ch
        return self

    def blob(self, ch, cx, cy, rx, ry, cut=()):
        """An island or reef patch: an ellipse of cells, minus any listed cells."""
        for y in range(self.h):
            for x in range(self.w):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0 and (x, y) not in cut:
                    self.grid[y][x] = ch
        return self

    def rect(self, ch, x0, y0, x1, y1):
        return self.put(ch, [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)])

    def stream(self, cells, heading):
        for c in cells:
            self.current[c] = heading
        return self

    def kraken(self, x, y, arms):
        """A 2x2 body at (x, y); arms is a list of phases, each a list of cells reached in that phase."""
        self.krakens.append(dict(x=x, y=y, arms=[[tuple(c) for c in phase] for phase in arms]))
        return self

    def serpent(self, path, offset=0):
        """A sea serpent (head and two humps) sailing back and forth along path; offset staggers two of them."""
        self.serpents.append(dict(path=[tuple(c) for c in path], offset=offset))
        return self

    def ship(self, path, aim, every):
        """A pirate ship sailing back and forth along path; its broadside (aim) fires on every `every`th move."""
        self.ships.append(dict(path=[tuple(c) for c in path], aim=aim, every=every))
        return self

    def sprinkle(self, rocks=0, islets=0, seed=1, gap=3):
        """Fill empty water with a few more reefs and islets, chosen by a fixed scramble (so the sea is always
        the same sea), never closer than `gap` cells to a start, a berth, a creature's patch or a stream."""
        keep = list(self.starts) + list(self.goals) + list(self.barrels) + list(self.current) + self.reserved
        keep += [(x, y) for y in range(self.h) for x in range(self.w) if self.grid[y][x] in 'WS']
        for k in self.krakens:
            keep += [(k['x'] + i, k['y'] + j) for i in range(-3, 5) for j in range(-3, 5)]
        for s in self.serpents:
            keep += list(s['path'])
        for s in self.ships:
            keep += list(s['path']) + [(s['path'][0][0] + s['aim'][0] * d, s['path'][0][1] + s['aim'][1] * d)
                                       for d in range(1, FIRE_REACH + 1)]
        order = sorted(((hashed(x, y, seed), x, y) for y in range(self.h) for x in range(self.w)))
        placed = 0
        for _, x, y in order:
            if placed >= rocks + islets:
                break
            if self.grid[y][x] != '.' or any(max(abs(x - a), abs(y - b)) < gap for a, b in keep):
                continue
            around = [(x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
            if any(not (0 <= a < self.w and 0 <= b < self.h) or self.grid[b][a] != '.' for a, b in around):
                continue
            if placed < islets:
                self.blob('L', x, y, 1.45, 1.45)
            else:
                self.put('R', [(x, y)])
            keep.append((x, y))
            placed += 1
        return self

    def finish(self):
        """Precompute everything the rules read: the solid cells, the rhythm's length."""
        self.solid = {(x, y) for y in range(self.h) for x in range(self.w) if self.grid[y][x] in 'LRY'}
        for k in self.krakens:
            self.solid |= {(k['x'] + i, k['y'] + j) for i in (0, 1) for j in (0, 1)}
        self.cycle = 1
        for k in self.krakens:
            self.cycle = math.lcm(self.cycle, len(k['arms']))
        for s in self.serpents:
            self.cycle = math.lcm(self.cycle, 2 * (len(s['path']) - 1))
        for s in self.ships:
            self.cycle = math.lcm(self.cycle, s['every'], max(1, 2 * (len(s['path']) - 1)))
        if self.wind_every:
            self.cycle = math.lcm(self.cycle, self.wind_every * len(self.winds))
        assert all(c not in self.solid and self.grid[c[1]][c[0]] not in 'LRY' for c in self.current), 'a stream may not cross land'
        self.whirlpools = frozenset((x, y) for y in range(self.h) for x in range(self.w) if self.grid[y][x] == 'W')
        self._hazard_memo = {}
        return self


def hashed(x, y, salt=0):
    """A small repeatable scramble of numbers: all the 'random' scenery comes from this, never a clock."""
    n = (x * 73856093 ^ y * 19349663 ^ salt * 83492791) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFFFF


def path_index(length, t):
    """Where a creature sailing back and forth along a path of `length` cells stands at move t."""
    if length == 1:
        return 0
    i = t % (2 * (length - 1))
    return i if i < length else 2 * (length - 1) - i


def serpent_cells(s, t):
    """Head first, then the two humps behind it (where the head stood one and two moves earlier)."""
    path = s['path']
    return tuple(path[path_index(len(path), t + s['offset'] - k)] for k in range(3))


def ship_cell(s, t):
    return s['path'][path_index(len(s['path']), t)]


def fire_line(sea, ship, t, barrels):
    """Cells a broadside from the ship's position at move t sweeps: from its bow cell out to FIRE_REACH."""
    x, y = ship_cell(ship, t)
    dx, dy = ship['aim']
    cells = []
    for _ in range(FIRE_REACH):
        x, y = x + dx, y + dy
        if not (0 <= x < sea.w and 0 <= y < sea.h) or (x, y) in sea.solid or (x, y) in barrels:
            break
        cells.append((x, y))
    return cells


def firing(ship, t):
    return t % ship['every'] == ship['every'] - 1


def movers(sea, t):
    """Cells held by serpents and ship hulls at move t: a boat may not sail through them either."""
    out = set()
    for s in sea.serpents:
        out.update(serpent_cells(s, t))
    for s in sea.ships:
        out.add(ship_cell(s, t))
    return out


def hazards(sea, t, barrels):
    """Every cell that is deadly to end a move on once the tide has turned to move t."""
    key = (t % sea.cycle, barrels)
    got = sea._hazard_memo.get(key)
    if got is None:
        out = movers(sea, t)
        for k in sea.krakens:
            out.update(k['arms'][t % len(k['arms'])])
        for s in sea.ships:
            if firing(s, t):
                out.update(fire_line(sea, s, t, barrels))
        got = sea._hazard_memo[key] = frozenset(out) | sea.whirlpools
    return got


def wind_at(sea, t):
    if not sea.wind_every:
        return sea.winds[0]
    return sea.winds[(t // sea.wind_every) % len(sea.winds)]


def blocked(sea, cell, positions, barrels):
    x, y = cell
    return (not (0 <= x < sea.w and 0 <= y < sea.h) or cell in sea.solid or cell in positions
            or cell in barrels)


def sheltered(sea, positions, moored, boat, wind):
    """Wind is broken by an island, or by another boat with its sail up, within reach upwind."""
    x, y = positions[boat]
    dx, dy = wind
    for k in range(1, SHELTER_REACH + 1):
        cell = (x - k * dx, y - k * dy)
        if not (0 <= cell[0] < sea.w and 0 <= cell[1] < sea.h):
            break
        if sea.grid[cell[1]][cell[0]] == 'L':
            return True
        if cell in positions:
            other = positions.index(cell)
            if other != boat and not moored & (1 << other):
                return True
    return False


def calm_cells(sea, wind):
    """Water an island shields from this wind (drawn as calm water): the lee, SHELTER_REACH cells downwind."""
    out = set()
    dx, dy = wind
    for y in range(sea.h):
        for x in range(sea.w):
            if sea.grid[y][x] != 'L':
                continue
            for k in range(1, SHELTER_REACH + 1):
                c = (x + k * dx, y + k * dy)
                if 0 <= c[0] < sea.w and 0 <= c[1] < sea.h and sea.grid[c[1]][c[0]] != 'L':
                    out.add(c)
    return out


def initial(sea):
    return (tuple(sea.starts), 0, 0, tuple(sorted(sea.barrels)), 0)


def won(sea, state):
    return state[0] == tuple(sea.goals)


def advance(sea, state, action):
    """One command. Returns (new_state, outcome); outcome is 'refused', 'switched', 'sailed' or 'sunk'.

    Steering moves the chosen boat one cell, and that is a gust for every other boat with its sail up (not
    anchored, not sheltered, not on a shoal), all moved together from one snapshot. Streams then carry any
    boat sailing on them. The creatures take one step, and any boat left on a deadly cell is lost. A boat
    anchors only when control is handed away while it sits in its own berth."""
    positions, selected, moored, barrels, t = state
    if action == 5 or action >= 10:
        target = (selected + 1) % len(positions) if action == 5 else action - 10
        if not 0 <= target < len(positions) or target == selected:
            return state, 'refused'
        if positions[selected] == sea.goals[selected]:
            moored |= 1 << selected
        return (positions, target, moored, barrels, t), 'switched'
    if action not in STEER:
        return state, 'refused'
    dx, dy = STEER[action]
    x, y = positions[selected]
    cell = (x + dx, y + dy)
    barrels = list(barrels)
    if cell in barrels:                       # a barrel is shoved along if there is room behind it
        beyond = (cell[0] + dx, cell[1] + dy)
        if blocked(sea, beyond, positions, barrels) or beyond in sea.whirlpools:
            return state, 'refused'
        barrels[barrels.index(cell)] = beyond
    elif blocked(sea, cell, positions, barrels):
        return state, 'refused'
    moved = list(positions)
    moved[selected] = cell
    moored &= ~(1 << selected)
    barrels = tuple(sorted(barrels))
    wind = wind_at(sea, t)
    snapshot = tuple(moved)
    proposals = {}
    for boat, here in enumerate(snapshot):
        if (boat == selected or moored & (1 << boat) or sea.grid[here[1]][here[0]] == 'S'
                or sheltered(sea, snapshot, moored, boat, wind)):
            continue
        ahead = (here[0] + wind[0], here[1] + wind[1])
        if not blocked(sea, ahead, snapshot, barrels):
            proposals[boat] = ahead
    for boat, ahead in proposals.items():     # one wind never sends two boats to one cell
        moved[boat] = ahead
    for boat in range(len(moved)):            # streams: one cell each, boats in order, anchored boats hold
        flow = sea.current.get(moved[boat])
        if flow is None or moored & (1 << boat):
            continue
        ahead = (moved[boat][0] + flow[0], moved[boat][1] + flow[1])
        if not blocked(sea, ahead, tuple(moved), barrels):
            moved[boat] = ahead
    after = hazards(sea, t + 1, barrels)
    before_movers = movers(sea, t)
    now_movers = movers(sea, t + 1)
    sunk = any(c in after for c in moved) or any(
        end in before_movers and start in now_movers for start, end in zip(positions, moved))
    return (tuple(moved), selected, moored, barrels, t + 1), 'sunk' if sunk else 'sailed'


# ====================================================================================================
# PART TWO: THE EIGHT SEAS. Coordinates are (column, row) in sea cells, row 0 at the top. Each sea is built
# from islands (L), reefs (R), shoals (S), buoys (Y), whirlpools (W), streams, barrels and creatures; props
# (huts, fires, lighthouses, wrecks, wind socks) are set dressing placed on island cells.
# ====================================================================================================

def sea_one():
    """Open water: two boats, a steady east wind, palm islands and reefs to sail round."""
    s = Sea(32, 24, 'day')
    s.starts, s.goals = [(4, 17), (11, 5)], [(27, 5), (26, 19)]
    s.blob('L', 15, 12, 3.2, 2.6).blob('L', 7, 10, 1.4, 1.4).blob('L', 24, 12, 1.8, 1.8)
    s.blob('L', 2, 3, 1.3, 1.3).blob('L', 15, 2, 1.6, 1.1).blob('L', 29, 20, 1.5, 1.3).blob('L', 19, 21, 1.3, 1.0)
    s.blob('L', 5, 21, 1.5, 1.0).blob('L', 29, 12, 1.0, 1.0)
    s.put('R', [(19, 4), (19, 5), (20, 17), (21, 17), (10, 19), (11, 19), (29, 9), (6, 14), (22, 8), (23, 8),
                (13, 18), (7, 6), (3, 9)])
    s.put('Y', [(27, 14), (27, 15), (27, 16), (9, 3), (9, 4)])
    s.props = [('hut', 15, 12), ('fire', 17, 13), ('sock', 24, 12), ('crab', 14, 13), ('chest', 13, 11)]
    s.sprinkle(rocks=8, islets=5, seed=3)
    return s


def sea_two():
    """Lee shores: wind from the north; islands break it and shoals hold a boat still."""
    s = Sea(28, 30, 'cove')
    s.winds = [DOWN]
    s.starts, s.goals = [(6, 4), (21, 6)], [(20, 24), (7, 25)]
    s.blob('L', 13, 14, 3.4, 3.0).blob('L', 22, 19, 1.6, 1.6).blob('L', 5, 20, 1.6, 1.6)
    s.blob('L', 24, 2, 1.4, 1.0).blob('L', 2, 8, 1.2, 1.5).blob('L', 14, 28, 1.6, 1.0).blob('L', 25, 26, 1.3, 1.3)
    s.blob('S', 8, 9, 2.0, 1.2).blob('S', 18, 26, 2.0, 1.2).blob('S', 23, 11, 1.4, 1.4).blob('S', 3, 15, 1.2, 1.5)
    s.put('R', [(11, 5), (12, 5), (16, 22), (9, 22), (14, 24), (3, 12), (19, 8), (26, 15)])
    s.props = [('light', 13, 12), ('hut', 15, 15), ('fire', 12, 15), ('sock', 5, 20), ('hut', 22, 19), ('chest', 12, 15), ('crab', 14, 16)]
    s.sprinkle(rocks=6, islets=3, seed=5)
    return s


def sea_three():
    """The kraken: it guards the only gaps in a wall of reef, two neighbouring tentacles out at a time, turning clockwise from the
    north. Wind from the east."""
    s = Sea(30, 30, 'deep')
    s.winds = [LEFT]
    s.starts, s.goals = [(24, 6), (4, 23)], [(5, 6), (25, 24)]
    s.rect('R', 14, 0, 14, 11).rect('R', 14, 20, 14, 29).put('R', [(15, 11), (15, 20), (13, 11), (13, 20)])
    north, east = [(14, 14), (14, 13), (14, 12)], [(16, 15), (17, 15), (18, 15)]
    south, west = [(14, 17), (14, 18), (14, 19)], [(13, 16), (12, 16), (11, 16)]
    s.kraken(14, 15, [north + east, east + south, south + west, west + north])
    s.blob('L', 8, 12, 1.6, 1.5).blob('L', 22, 18, 1.6, 1.5).blob('L', 7, 3, 1.6, 1.2).blob('L', 22, 26, 1.6, 1.2)
    s.blob('L', 4, 17, 1.2, 1.2).blob('L', 25, 11, 1.2, 1.2)
    s.put('R', [(18, 3), (20, 8), (9, 24), (10, 27), (26, 21), (3, 28), (27, 3)])
    s.props = [('wreck', 8, 12), ('fire', 22, 18), ('torch', 4, 17), ('chest', 7, 3)]
    s.sprinkle(rocks=6, islets=3, seed=7)
    return s


def sea_four():
    """Pirate waters: a galleon guards the only way up to one berth, firing straight up a narrow channel every
    fourth move (its gun ports light one by one); two side bays are the places to wait. Another patrols and fires
    across the open sea. Wind from the south."""
    s = Sea(30, 28, 'pirate')
    s.winds = [UP]
    s.starts, s.goals = [(5, 22), (24, 22)], [(25, 4), (4, 4)]
    s.rect('R', 24, 0, 24, 12).rect('R', 26, 0, 26, 12).put('.', [(24, 8), (26, 8), (24, 11), (26, 11)])
    s.reserved = [(x, y) for x in range(22, 29) for y in range(0, 17)]
    s.ship([(25, 14)], UP, 4)
    s.ship([(6, 13), (7, 13), (8, 13), (9, 13), (10, 13)], DOWN, 3)
    s.blob('L', 15, 8, 2.4, 1.8).blob('L', 15, 20, 2.4, 1.8).blob('L', 3, 14, 1.2, 1.8)
    s.blob('L', 5, 8, 1.3, 1.3).blob('L', 10, 25, 1.3, 1.0).blob('L', 21, 25, 1.3, 1.0)
    s.put('R', [(12, 13), (13, 13), (18, 3), (8, 2), (27, 24), (2, 25), (12, 17), (17, 14), (20, 12)])
    s.props = [('hut', 15, 8), ('fire', 16, 9), ('wreck', 15, 20), ('light', 3, 14), ('chest', 14, 21),
               ('crab', 16, 21)]
    s.sprinkle(rocks=6, islets=3, seed=9)
    return s


def sea_five():
    """Streams: two rivers of current run east and west; whirlpools wait where they end. Wind from the west."""
    s = Sea(34, 24, 'stream')
    s.winds = [RIGHT]
    s.starts, s.goals = [(3, 18), (4, 5)], [(30, 5), (29, 19)]
    s.stream([(x, 9) for x in range(5, 27)], RIGHT)
    s.stream([(x, 14) for x in range(8, 30)], LEFT)
    s.put('W', [(27, 9), (7, 14)])
    s.blob('L', 16, 11.5, 5, 1.0).blob('L', 30, 11, 1.5, 1.8).blob('L', 3, 11, 1.5, 1.8)
    s.blob('L', 12, 2, 1.5, 1.2).blob('L', 21, 21, 1.8, 1.2).blob('L', 26, 3, 1.3, 1.0).blob('L', 10, 20, 1.3, 1.0)
    s.put('R', [(20, 20), (21, 20), (12, 3), (13, 3), (5, 7), (32, 17), (16, 6), (17, 17)])
    s.props = [('hut', 16, 11), ('sock', 30, 11), ('fire', 3, 11), ('tent', 31, 11), ('crab', 17, 11)]
    s.sprinkle(rocks=6, islets=3, seed=11)
    return s


def sea_six():
    """Night sea: the wind turns clockwise every five moves (east, south, west, north), shown on the vane."""
    s = Sea(34, 30, 'night')
    s.winds, s.wind_every = [RIGHT, DOWN, LEFT, UP], 5
    s.starts, s.goals = [(4, 5), (28, 24)], [(28, 5), (4, 24)]
    s.blob('L', 16, 14, 3.4, 3.0).blob('L', 8, 14, 1.4, 1.4).blob('L', 25, 15, 1.4, 1.4)
    s.blob('L', 4, 28, 1.6, 1.0).blob('L', 29, 2, 1.6, 1.0).blob('L', 31, 24, 1.0, 1.5).blob('L', 1, 20, 1.0, 1.5)
    s.blob('S', 16, 5, 2.4, 1.0).blob('S', 16, 24, 2.4, 1.0)
    s.put('R', [(10, 6), (22, 23), (24, 8), (9, 22), (16, 9), (16, 20), (6, 26), (27, 20)])
    s.put('Y', [(20, 4), (20, 5), (12, 25), (12, 26)])
    s.props = [('light', 16, 12), ('fire', 8, 14), ('fire', 25, 15), ('tent', 18, 15), ('crab', 14, 16), ('torch', 14, 13)]
    s.sprinkle(rocks=6, islets=4, seed=13)
    return s


def sea_seven():
    """Serpent strait: the only way east is one narrow channel through a wide band of reef, and a sea serpent
    patrols it end to end. Side bays are the only places to let it pass, and you can only wait in one by moving
    another boat. Barrels can chock a boat the wind is pushing."""
    s = Sea(36, 26, 'serpent')
    s.winds = [RIGHT]
    s.starts, s.goals = [(3, 5), (3, 12), (3, 20)], [(31, 20), (32, 12), (31, 5)]
    s.rect('R', 10, 0, 20, 25).rect('.', 10, 12, 20, 12)
    s.put('.', [(12, 11), (12, 13), (15, 11), (15, 13), (18, 11), (18, 13)])
    s.serpent([(x, 12) for x in range(10, 21)])
    s.reserved = [(x, y) for x in range(8, 23) for y in range(0, 26)]
    s.blob('L', 26, 8, 2.0, 1.6).blob('L', 26, 18, 2.0, 1.6).blob('L', 6, 16, 1.2, 1.2)
    s.blob('L', 33, 1, 1.5, 1.0).blob('L', 33, 24, 1.5, 1.0).blob('L', 4, 1, 1.2, 1.0)
    s.barrels = ((7, 6), (7, 19))
    s.props = [('hut', 26, 8), ('fire', 27, 9), ('totem', 25, 9), ('totem', 26, 18), ('hut', 27, 18)]
    s.sprinkle(rocks=4, islets=3, seed=17)
    return s


def sea_eight():
    """The great sea: three boats, a wind that swings east then south, and everything seen so far."""
    s = Sea(40, 38, 'dusk')
    s.winds, s.wind_every = [RIGHT, DOWN], 6
    s.starts, s.goals = [(4, 6), (4, 30), (34, 4)], [(34, 31), (35, 22), (6, 18)]
    s.kraken(19, 17, [[(19, 16), (19, 15)], [(21, 17), (22, 17)], [(20, 19), (20, 20)], [(18, 18), (17, 18)]])
    s.serpent([(x, 9) for x in range(12, 26)])
    s.ship([(28, 27), (28, 28), (28, 29), (28, 30)], LEFT, 3)
    s.stream([(x, 21) for x in range(8, 20)], RIGHT)
    s.blob('L', 8, 8, 2.0, 1.6).blob('L', 30, 14, 2.4, 2.0).blob('L', 12, 25, 2.4, 2.0).blob('L', 34, 33, 2.0, 1.6)
    s.blob('S', 24, 31, 2.0, 1.2)
    s.put('R', [(16, 15), (23, 15), (16, 19), (23, 19), (17, 23), (22, 13)])
    s.barrels = ((14, 7), (30, 22))
    s.props = [('light', 30, 12), ('hut', 8, 8), ('wreck', 12, 25), ('tent', 29, 15), ('chest', 35, 33), ('crab', 12, 26), ('totem', 9, 9)]
    s.sprinkle(rocks=12, islets=7, seed=19)
    return s


SEAS = [build().finish() for build in
        (sea_one, sea_two, sea_three, sea_four, sea_five, sea_six, sea_seven, sea_eight)]

# The move counter of each sea is twice the length of the shortest winning line found by a search over these same
# rules (a best-first search over every boat's cell, which boat is steered, which are anchored, the tide's move and
# any pushed barrels). Seas 1, 2, 3 and 5 are exact (the search ran until no shorter line could exist): 37, 36, 49
# and 37 moves. Seas 4, 6, 7 and 8 are the best line the search found, 49, 38, 78 and 85, so a shorter line may exist
# and those counters may be a little over twice the true shortest. Every one of those lines was replayed through the
# real game from a fresh start and wins all eight seas in a row.
COUNTERS = [74, 72, 98, 98, 74, 76, 156, 170]


# ====================================================================================================
# PART THREE: THE ART. Sprites are drawn from text rows ('.' is see-through, a letter is a palette colour)
# and every animated piece is a small function of a beat number, so nothing is stored per frame.
# ====================================================================================================

LEGEND = dict(k=BLK, w=WHT, r=RED, o=ORG, y=YEL, g=GRN, b=BLU, l=LBL, m=MAR, p=PNK, c=MAG, u=PUR)


def art(rows, legend=None):
    """Draw a sprite from text rows into an int array; -1 is see-through."""
    legend = {**LEGEND, **(legend or {})}
    out = np.full((len(rows), len(rows[0])), -1, dtype=np.int16)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != '.':
                out[y, x] = legend[ch]
    return out


def blit(dst, x, y, spr):
    """Put a sprite on a picture at (x, y), clipped, skipping see-through pixels."""
    h, w = spr.shape
    H, W = dst.shape
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    sub = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    mask = sub >= 0
    dst[y0:y1, x0:x1][mask] = sub[mask]


def flip(spr):
    return spr[:, ::-1].copy()


def disc(frame, cx, cy, r, colour, ring=False):
    """A filled (or ring-only) disc, clipped: splashes, sparkles and the whirlpool's rim."""
    H, W = frame.shape
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        for x in range(max(0, cx - r), min(W, cx + r + 1)):
            d = (x - cx) ** 2 + (y - cy) ** 2
            if d <= r * r + r // 2 and (not ring or d >= (r - 1) ** 2):
                frame[y, x] = colour


# ---- theme colours -------------------------------------------------------------------------------------------
# water and its ripples, a glint colour, and what a shoal is dotted with; one look per sea
THEMES = {
    'day':     dict(water=BLU, ripple=LBL, glint=WHT, shoal=LBL, speck=YEL, density=9),
    'cove':    dict(water=GRN, ripple=LBL, glint=WHT, shoal=YEL, speck=GRN, density=7),
    'deep':    dict(water=BLK, ripple=PUR, glint=LBL, shoal=BLU, speck=LBL, density=7),
    'pirate':  dict(water=PUR, ripple=PNK, glint=YEL, shoal=PNK, speck=YEL, density=8),
    'stream':  dict(water=LBL, ripple=BLU, glint=WHT, shoal=YEL, speck=WHT, density=7),
    'night':   dict(water=BLK, ripple=BLU, glint=WHT, shoal=BLU, speck=LBL, density=4),
    'serpent': dict(water=BLU, ripple=GRN, glint=YEL, shoal=YEL, speck=GRN, density=8),
    'dusk':    dict(water=BLU, ripple=ORG, glint=YEL, shoal=ORG, speck=YEL, density=4),
}

# ---- the boats ------------------------------------------------------------------------------------------------
BOAT_W, BOAT_H = 9, 12

# Sails by wind. Rows 0-7 sit over the hull; 'h' is the boat's own colour (pennant), 'w' the cloth.
SAIL_FULL_E = ("........."
               "....khhh."
               "....kw..."
               "....kww.."
               "....kwww."
               "....kwwww"
               "....kwwww"
               "..kkkkkkk")
SAIL_FRONT = (".....h..."
              "....khh.."
              "...wkw..."
              "..wwkww.."
              "..wwkww.."
              ".wwwkwww."
              ".wwwkwww."
              "..kkkkk..")
SAIL_FRONT_DOWN = ("........."
                   "....kh..."
                   "...wkh..."
                   "..wwkwh.."
                   "..wwkww.."
                   ".wwwkwww."
                   ".wwwkwww."
                   "..kkkkk..")
SAIL_SLACK = (".........",
              "....kh...",
              "....kh...",
              "...wk....",
              "....kw...",
              "...wk....",
              "....kw...",
              "..kkkkk..")
SAIL_SLACK_B = (".........",
                "....kh...",
                "....kh...",
                "....kw...",
                "...wk....",
                "....kw...",
                "...wk....",
                "..kkkkk..")
SAIL_FURLED = (".........",
               "....kh...",
               "....kh...",
               "....k....",
               "....k....",
               "....k....",
               ".wwwkwww.",
               "..kkkkk..")

HULL = (".kwwwwwk.",
        "khhhhhhhk",
        ".khhhhhk.",
        "..kkkkk..")


def split_rows(flat):
    return [flat[i:i + 9] for i in range(0, len(flat), 9)] if isinstance(flat, str) else list(flat)


def boat_art(boat, face, sail, wind, beat):
    """A sloop in side view. Hull in the boat's colour; white (yellow for the second boat) sail that billows
    downwind, hangs slack, or is furled; a pennant at the masthead that streams with the wind or droops.
    A furled boat wears a white anchor on its hull. face is 1 (bow right) or -1 (bow left)."""
    hull = BOAT_COLOURS[boat]
    legend = dict(h=hull, w=YEL if boat == 1 else WHT)
    dx, dy = wind
    if sail == 'furled':
        rows = split_rows(SAIL_FURLED)
    elif sail == 'slack':
        rows = split_rows(SAIL_SLACK_B if beat % 2 else SAIL_SLACK)
    elif dx:
        rows = split_rows(SAIL_FULL_E)
        if beat % 2:                                         # the pennant flaps
            rows[1] = "....khh.."
            rows[0] = ".....h..."
    else:
        rows = split_rows(SAIL_FRONT if dy < 0 else SAIL_FRONT_DOWN)
    sprite = art(list(rows) + list(HULL), legend)
    if sail == 'full' and dx < 0:
        # the sail billows toward -x: mirror the sail rows only, then the hull is dressed below
        sprite[:8] = flip(sprite[:8])
    stern = 2 if face > 0 else 6                            # the hull is the same either way; only the cabin window moves
    sprite[9, stern] = YEL if sail != 'furled' else hull   # a lit stern window
    lo, hi = (7, 9) if face > 0 else (0, 2)
    sprite[7, lo:hi] = BLK                                   # a short bowsprit shows which way she points
    if sail == 'furled':
        sprite[9, 4], sprite[10, 3], sprite[10, 4], sprite[10, 5] = WHT, WHT, WHT, WHT
        sprite[9, 3] = hull
    return sprite


# ---- scenery --------------------------------------------------------------------------------------------------
PALM_A = art(("..kk.kk..",
              ".kggkggk.",
              "kgggkgggk",
              "kgkgygkgk",
              ".k.kmk.k.",
              "....m....",
              "....mm...",
              "...mm....",
              "...mm...."))
PALM_B = art(("...kkk...",
              ".kgggggk.",
              "kgggkgggk",
              "kgkgygkgk",
              "k..kmk..k",
              "....m....",
              "....mm...",
              "...mm....",
              "...mm...."))
BUSH = art((".ggg.", "gkgkg", "ggggg"))
HUT = art((".....oo.....",
           "...ooyyoo...",
           "..ooyyyyoo..",
           ".oyyyyyyyyo.",
           "..mmmmmmmm..",
           "..mmkkkmmm..",
           "..mmkkkmmm.."))
FIRE_A = art((".y.", "yor", "rkr"))
FIRE_B = art(("y..", "oyr", "rkr"))
FIRE_C = art((".y.", "ryo", "rkr"))
TOTEM = art((".rrr.",
             "rwkwr",
             "rrkrr",
             ".yyy.",
             "ykkky",
             "yyyyy",
             ".ooo.",
             "okwko",
             "ooooo",
             ".mmm.",
             "mmmmm",
             "kkkkk"))
CHEST = art((".mmmm.",
             "moooom",
             "kyyyyk",
             "kmmmmk"))
TENT = art(("...ww...",
            "..wrrw..",
            ".wrrrrw.",
            "wrrkkrrw",
            "wrrkkrrw"))
TORCH = (art((".y.", "yoy", ".m.", ".m.", ".m.")), art((".o.", "yoy", ".m.", ".m.", ".m.")))
CRAB = (art(("r...r", "rrrrr", ".k.k.")), art(("r...r", "rrrrr", "k...k")))
SMOKE = (art(("w",)), art(("l",)))
LIGHTHOUSE = art(("..yy..",
                  ".kkkk.",
                  ".wwww.",
                  ".wrrw.",
                  ".wwww.",
                  ".wrrw.",
                  ".wwww.",
                  ".wrrw.",
                  "wwwwww",
                  "wrrrrw",
                  "wwwwww",
                  "wkkkkw",
                  "wkkkkw",
                  "kkkkkk"))
WRECK = art(("..m..m..m.",
             ".mkm.mkm.m",
             "mm.mmm.mmm",
             "m........m"))
BUOY = art(("..y..",
            "..k..",
            ".www.",
            ".rrr.",
            ".www.",
            ".rrr.",
            "..k.."))
BARREL = art((".kkk.",
              "kmmmk",
              "oooko",
              "kmmmk",
              ".kkk."))
ROCKS = [
    art(("..kkk...",
         ".kmmok..",
         "kmmmomk.",
         "kmmmmmmk",
         "kmmmmmmk",
         ".kkkkkk.")),
    art(("...kk...",
         "..kmmk..",
         ".kmomk.k",
         ".kmmmkmk",
         "kmmmmmmk",
         ".kkkkkk.")),
    art((".k..kk..",
         "kmk.kmk.",
         "kmmkmmmk",
         "kmomommk",
         "kmmmmmmk",
         ".kkkkkk.")),
]
SKULL_ROCK = art(("..kkkk..",
                  ".kmmmmk.",
                  "kmwkmwkm",
                  "kmmmmmmk",
                  ".kmwwmk.",
                  "..kkkk.."))
SPARK = (art(("w",)), art((".w.", "www", ".w.")), art(("w.w", ".w.", "w.w")))


FLAG_E = ("k.......", "kcccc...", "kcccccc.", "k.cccc..", "k.......", "k.......", "k.......", "k.......")
FLAG_E2 = ("k.......", "kcccc...", "kccccc..", "k.ccccc.", "k.......", "k.......", "k.......", "k.......")
FLAG_UP = ("..c.....", ".cc.....", ".cc.....", "kc......", "k.......", "k.......", "k.......", "k.......")
FLAG_UP2 = (".c......", ".cc.....", "..cc....", "kc......", "k.......", "k.......", "k.......", "k.......")
FLAG_DN = ("k.......", "kcc.....", "kcc.....", "kc......", "k.......", "k.......", "k.......", "k.......")
FLAG_DN2 = ("k.......", "kc......", "kcc.....", "k.cc....", "k.......", "k.......", "k.......", "k.......")
SOCK_E = ("k.......", "kwwrrw..", "kwwrrw..", "k.wrrw..", "k.......", "k.......", "k.......", "k.......")
SOCK_E2 = ("k.......", "kwwrrw..", "kwwrrw..", "k.wrr...", "k.......", "k.......", "k.......", "k.......")


def streamer(kind, wind, wave, colour=RED):
    """A flag or windsock on a pole, its cloth streaming the way the wind blows (8x8). wave alternates the
    cloth between two shapes on alternate beats so it ripples."""
    dx, dy = wind
    if kind == 'sock':
        if dy:   # a sock across the pole's top, pointing along the wind
            rows = FLAG_UP if dy < 0 else FLAG_DN
            return art(rows, dict(c=RED))
        east = art(SOCK_E2 if wave else SOCK_E)
        return east if dx > 0 else flip(east)
    if dy:
        return art((FLAG_UP2 if wave else FLAG_UP) if dy < 0 else (FLAG_DN2 if wave else FLAG_DN), dict(c=colour))
    east = art(FLAG_E2 if wave else FLAG_E, dict(c=colour))
    return east if dx > 0 else flip(east)


def whirlpool(phase):
    """A dark spiral with a foam rim, 12x12, turning a quarter step each beat."""
    out = np.full((12, 12), -1, dtype=np.int16)
    for y in range(12):
        for x in range(12):
            fx, fy = x - 5.5, y - 5.5
            r = math.hypot(fx, fy)
            if r > 5.9:
                continue
            if r < 1.5:
                out[y, x] = BLK
                continue
            turn = (math.atan2(fy, fx) / (2 * math.pi) * 2 + r * 0.32 - phase / 4.0) % 1.0
            if r > 4.9:
                out[y, x] = WHT if turn < 0.5 else LBL
            else:
                out[y, x] = BLK if turn < 0.5 else BLU
    return out


# ---- sea monsters -----------------------------------------------------------------------------------------------
def kraken_body(gaze):
    """The kraken's head, 16x14 (a 2x2 block of cells with two pixels to spare each side): purple, warty,
    black-outlined, two slit yellow eyes whose pupils look toward gaze=(-1/0/1, -1/0/1), red brows, a
    toothed black mouth, and six curled stubs of tentacle along the bottom."""
    s = np.full((14, 16), -1, dtype=np.int16)
    for y in range(11):
        for x in range(16):
            d = ((x - 7.5) / 6.4) ** 2 + ((y - 5.2) / 5.6) ** 2
            if d <= 1.0:
                s[y, x] = BLK if d > 0.72 else PUR
                if d <= 0.72 and hashed(x, y, 3) % 9 == 0:
                    s[y, x] = PNK
    for ex in (3, 9):                                        # eyes: 4x3 yellow with a 1x3 black slit
        s[3:6, ex:ex + 4] = YEL
        s[2, ex:ex + 4] = RED
        s[3:6, ex + 1 + max(0, min(2, 1 + gaze[0]))] = BLK
    s[7:9, 5:11] = BLK                                       # mouth with a row of teeth
    s[7, 6:10:2] = WHT
    for i, x in enumerate((0, 2, 4, 6, 9, 11, 13)):          # tentacle stubs curling out under the head
        top = 9 + (i % 2)
        s[top:top + 4 - (i % 2), x:x + 2] = PUR
        s[top + 3 - (i % 2), x:x + 2] = BLK
        s[top + 1, x + (i % 2)] = PNK
    return s


ARM_MID = art(("......",
               "kkkkkk",
               "uuuuuu",
               "upupup",
               "kkkkkk",
               "......"))
ARM_TIP = art(("......",
               "kkkkk.",
               "uuuuuk",
               "upupuk",
               "kkkkuk",
               "....kk"))


def arm_tile(direction, tip, index=0):
    """One 6x6 piece of a reaching tentacle, turned to point along direction. Alternate pieces sit a pixel
    off line so the arm looks like it writhes; the last piece curls."""
    base = ARM_TIP if tip else ARM_MID
    if index % 2 and not tip:
        base = np.vstack([base[1:], base[:1]])
    if direction == (1, 0):
        return base
    if direction == (-1, 0):
        return flip(base)
    return np.rot90(base, 1 if direction == (0, -1) else -1).copy()


SERPENT_HEAD = art(("..o..o....",
                    ".koookok..",
                    "krrrrrrrk.",
                    "krrrrwkrrk",
                    "krrrrrrrrk",
                    ".kyyyyrrrk",
                    "..kkyyyyp.",
                    "....kkk.pp"))
SERPENT_HUMP = art((".kkkkkk.",
                    "krrrrrrk",
                    "kroyoyrk",
                    "krrrrrrk",
                    "wwwwwwww"))


def serpent_head(heading):
    if heading == (1, 0):
        return SERPENT_HEAD
    if heading == (-1, 0):
        return flip(SERPENT_HEAD)
    return np.rot90(SERPENT_HEAD, 1 if heading == (0, -1) else -1).copy()


SHIP = art(("....kkk.....kkk....",
            "....kwk.....kwk....",
            ".....k.......k.....",
            "..rrrkrr..rrrkrr...",
            ".rrrrkrrr.rrrkrrr..",
            ".rryrkryr.rryrkryr.",
            ".rrrrkrrr.rrrkrrr..",
            "..yyykyy...yyykyy..",
            "kkkkkkkkkkkkkkkkkkk",
            ".kmmymmymmymmymmymk",
            "..kmmmmmmmmmmmmmk..",
            "...kkkkkkkkkkkkk..."))


PORT_COLUMNS = (5, 8, 11, 14, 17)       # where the gun ports sit along the hull (sprite columns)


def ship_art(aim, every, phase, beat):
    """A pirate galleon, 21x14 with a margin for the gun: black hull, maroon planking, red sails, a black flag
    with a white skull. The gun pokes out of the side it fires at. Its gun ports are the reload clock: one is
    lit just after a broadside, one more each move, and when every port is lit the next move fires (and the
    muzzle sparks)."""
    s = np.full((14, 21), -1, dtype=np.int16)
    s[0:12, 1:20] = SHIP
    s[2, 5] = WHT if beat % 2 else BLK               # the flag stirs
    until = (every - 2 - phase) % every              # 0 means the next move fires
    for i, col in enumerate(PORT_COLUMNS):
        s[9, col] = YEL if i < every - until else MAR
        if i >= every:
            s[9, col] = MAR
    muzzle = {(1, 0): (20, 9), (-1, 0): (0, 9), (0, 1): (10, 13), (0, -1): (10, 7)}[aim]
    gx, gy = muzzle
    s[gy, gx] = BLK
    if aim[0]:
        s[gy + 1, gx] = BLK
        s[gy, gx - aim[0]] = BLK
    else:
        s[gy, gx + 1] = BLK
        s[gy - aim[1], gx] = BLK
    if until == 0:
        sx, sy = gx + aim[0], gy + aim[1]
        if 0 <= sx < 21 and 0 <= sy < 14:
            s[sy, sx] = YEL if beat % 2 else ORG
    return s


# ====================================================================================================
# PART FOUR: PAINTING THE SEA. Everything that never moves (water, coasts, shoals, reefs, buoys, berths) is
# painted once per level into two pictures that differ only in where the ripples sit; the window shows one or
# the other on alternate moves. Everything that moves or sways is drawn over it each frame (part five).
# ====================================================================================================

def erode(mask):
    out = mask.copy()
    out[1:, :] &= mask[:-1, :]
    out[:-1, :] &= mask[1:, :]
    out[:, 1:] &= mask[:, :-1]
    out[:, :-1] &= mask[:, 1:]
    out[0, :] = False
    out[-1, :] = False
    out[:, 0] = False
    out[:, -1] = False
    return out


def dilate(mask):
    out = mask.copy()
    out[1:, :] |= mask[:-1, :]
    out[:-1, :] |= mask[1:, :]
    out[:, 1:] |= mask[:, :-1]
    out[:, :-1] |= mask[:, 1:]
    return out


def blur5(f):
    """A 5-tap box blur along each axis, used to round blocky coasts into soft shapes."""
    for axis in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (2, 2)
        p = np.pad(f, pad)
        n = f.shape[axis]
        f = sum(np.take(p, range(k, k + n), axis=axis) for k in range(5)) / 5.0
    return f


def cell_mask(sea, chars):
    """A pixel mask of the cells whose letter is in chars, blurred and cut at one half so that coasts and
    shoals come out as rounded organic shapes instead of squares."""
    cells = np.array([[sea.grid[y][x] in chars for x in range(sea.w)] for y in range(sea.h)], dtype=np.float32)
    f = np.kron(cells, np.ones((CELL, CELL), dtype=np.float32))
    return blur5(blur5(blur5(f))) > 0.5


def paint_ripples(img, sea, phase, theme, rng_salt):
    """Short ripple dashes and the odd glint on open water; phase 0/1 puts them in different places."""
    H, W = img.shape
    for cy in range(sea.h):
        for cx in range(sea.w):
            v = hashed(cx, cy, rng_salt + phase * 7)
            for k in range(2):
                n = (v >> (k * 5)) & 31
                if n < theme['density']:
                    x = cx * CELL + (n % 4)
                    y = cy * CELL + (1 + (n // 4 + k * 3) % 5)
                    if x + 2 < W and y < H:
                        img[y, x:x + 2 + (n % 2)] = theme['ripple']
            if v % 29 == 0:
                img[cy * CELL + 2, cx * CELL + 3] = theme['glint']


def paint_island(img, sea, mask, theme, phase):
    """Sand along the shore, grass inside, white surf round the outside; shapes come from the cell mask."""
    inner1 = erode(mask)
    inner2 = erode(inner1)
    inner3 = erode(inner2)
    H, W = img.shape
    ring1 = dilate(mask) & ~mask
    ring2 = dilate(ring1) & ~mask & ~ring1
    yy, xx = np.mgrid[0:H, 0:W]
    img[ring2 & ((xx + yy * 2 + phase * 2) % 5 == 0)] = theme['ripple']
    img[ring1 & ((xx + yy + phase) % 2 == 0)] = WHT
    img[ring1 & ((xx + yy + phase) % 2 == 1)] = theme['ripple']
    img[mask] = YEL
    img[mask & ~inner1 & ((xx * 3 + yy * 5) % 7 == 0)] = ORG
    img[inner2] = GRN
    img[inner2 & ((xx * 7 + yy * 3) % 11 == 0)] = YEL
    img[inner3 & ((xx * 5 + yy * 7) % 53 == 0)] = PNK


def paint_shoal(img, sea, theme, phase):
    mask = cell_mask(sea, 'S')
    if not mask.any():
        return
    H, W = img.shape
    yy, xx = np.mgrid[0:H, 0:W]
    img[mask] = theme['shoal']
    img[mask & ((xx * 5 + yy * 3) % 6 == 0)] = theme['speck']
    img[mask & ((xx + yy * 4) % 9 == 0)] = theme['water']
    edge = dilate(mask) & ~mask
    img[edge & ((xx + yy + phase) % 3 == 0)] = WHT


def paint_reef(img, sea, theme, phase):
    """Reefs: a lone rock is a boulder with surf at its foot; rocks packed together become a solid dark reef
    wall (a flat maroon field with a few glints) edged by boulders, so a wide band reads as one thing."""
    def rocky(x, y):
        return 0 <= x < sea.w and 0 <= y < sea.h and sea.grid[y][x] in 'RL'
    for cy in range(sea.h):
        for cx in range(sea.w):
            if sea.grid[cy][cx] != 'R':
                continue
            x0, y0 = cx * CELL, cy * CELL
            sides = [rocky(cx, cy - 1), rocky(cx, cy + 1), rocky(cx - 1, cy), rocky(cx + 1, cy)]
            if all(sides):
                img[y0:y0 + CELL, x0:x0 + CELL] = MAR
                for k in range(3):
                    h = hashed(cx, cy, 30 + k)
                    img[y0 + h % CELL, x0 + (h >> 4) % CELL] = ORG if k == 0 else BLK
                continue
            for k in range(CELL):                                   # surf only on the sides that face the water
                if (k + phase) % 2:
                    continue
                if not sides[1]:
                    img[min(img.shape[0] - 1, y0 + 6), x0 + k] = WHT
                if not sides[0] and y0 > 0:
                    img[y0 - 1, x0 + k] = WHT
            if sides[0] and sides[1] and (sides[2] or sides[3]):    # a horizontal run: keep the wall flat between boulders
                img[y0:y0 + CELL, x0:x0 + CELL] = MAR
                img[y0, x0:x0 + CELL] = BLK if not sides[0] else MAR
                continue
            pick = hashed(cx, cy, 11) % 3
            spr = SKULL_ROCK if theme is THEMES['pirate'] and hashed(cx, cy, 5) % 3 == 0 else ROCKS[pick]
            blit(img, x0 - 1, y0 + 1, spr)


def paint_berth(img, cell, boat):
    """A slip marked in the boat's colour: four tall pilings with white caps, and a painted ring on the water
    that shows when the slip is empty. The flag on the pole is drawn live (it streams downwind)."""
    colour = BOAT_COLOURS[boat]
    x0, y0 = cell[0] * CELL, cell[1] * CELL
    ring = [(2, 0), (3, 0), (1, 1), (4, 1), (0, 2), (5, 2), (0, 3), (5, 3), (1, 4), (4, 4), (2, 5), (3, 5)]
    for (px, py) in ring:
        img[y0 + py, x0 + px] = colour
    for (ox, oy) in ((-1, -1), (CELL - 1, -1), (-1, CELL - 2), (CELL - 1, CELL - 2)):
        img[y0 + oy:y0 + oy + 3, x0 + ox:x0 + ox + 2] = colour
        img[y0 + oy, x0 + ox:x0 + ox + 2] = WHT
        img[y0 + oy + 2, x0 + ox:x0 + ox + 2] = BLK


PLANK = art(("mmoo", "kmmm"))
TUFT = art(("g.g", "ggg"), dict(g=GRN))
LILY = art((".ggg.", "gggpg", ".ggg."))
BUBBLES = art(("w.", ".w", "w."))
RIBS = art(("m.m.m", "mmmmm"))
DECOR = {'day': (PLANK, BUBBLES), 'cove': (TUFT, TUFT, BUBBLES), 'deep': (BUBBLES, RIBS), 'pirate': (PLANK, RIBS),
         'stream': (BUBBLES, TUFT), 'night': (BUBBLES,), 'serpent': (LILY, LILY, TUFT), 'dusk': (PLANK, BUBBLES)}


def paint_decor(img, sea, theme, phase):
    """Small things that float or grow in open water and never block a boat: planks, tufts, lilies, bubbles."""
    kinds = DECOR[sea.theme]
    for cy in range(sea.h):
        for cx in range(sea.w):
            v = hashed(cx, cy, 21)
            if v % 13 != 0 or sea.grid[cy][cx] != '.' or (cx, cy) in sea.current:
                continue
            spr = kinds[(v >> 4) % len(kinds)]
            blit(img, cx * CELL + (v >> 8) % 3, cy * CELL + 1 + (v >> 10) % 3, np.where(spr == WHT, theme['glint'], spr))


def paint_world(sea, phase):
    """The finished still picture of the sea for one ripple phase."""
    theme = THEMES[sea.theme]
    H, W = sea.h * CELL, sea.w * CELL
    img = np.full((H, W), theme['water'], dtype=np.int16)
    paint_ripples(img, sea, phase, theme, 1)
    paint_decor(img, sea, theme, phase)
    if sea.theme == 'night':
        yy, xx = np.mgrid[0:H, 0:W]
        img[(hashed(xx, yy, 9) % 211 == 0)] = theme['glint']
    paint_shoal(img, sea, theme, phase)
    paint_island(img, sea, cell_mask(sea, 'L'), theme, phase)
    paint_reef(img, sea, theme, phase)
    for cy in range(sea.h):
        for cx in range(sea.w):
            if sea.grid[cy][cx] == 'Y':
                blit(img, cx * CELL, cy * CELL, BUOY)
    for boat, cell in enumerate(sea.goals):
        paint_berth(img, cell, boat)
    return img


def neighbours_land(sea, x, y):
    return sum(0 <= x + dx < sea.w and 0 <= y + dy < sea.h and sea.grid[y + dy][x + dx] == 'L'
               for dx, dy in (UP, DOWN, LEFT, RIGHT))


def scenery(sea):
    """Trees and props standing on the islands, as (kind, cell_x, cell_y); computed from the grid alone."""
    taken = {(x + i, y + j) for kind, x, y in sea.props for i in (-1, 0, 1) for j in (-1, 0, 1)}
    out = list(sea.props)
    seen = set()
    for y in range(sea.h):
        for x in range(sea.w):
            if sea.grid[y][x] != 'L' or (x, y) in seen:
                continue
            comp, stack = [], [(x, y)]
            seen.add((x, y))
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                for dx, dy in (UP, DOWN, LEFT, RIGHT):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < sea.w and 0 <= ny < sea.h and sea.grid[ny][nx] == 'L' and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            mx = sum(c[0] for c in comp) / len(comp)
            my = sum(c[1] for c in comp) / len(comp)
            trees = [c for c in comp if c not in taken and neighbours_land(sea, *c) >= 3 and hashed(*c, 4) % 10 < 2]
            if not trees:
                free = [c for c in comp if c not in taken]
                if free:
                    trees = [min(free, key=lambda c: (c[0] - mx) ** 2 + (c[1] - my) ** 2)]
            for c in trees:
                out.append(('palm', c[0], c[1]))
                taken.add(c)
            bushy = [c for c in comp if c not in taken and neighbours_land(sea, *c) == 4 and hashed(*c, 8) % 7 == 0]
            out.extend(('bush', c[0], c[1]) for c in bushy)
    return out


# ====================================================================================================
# PART FIVE: THE WINDOW. One display paints the whole 64x64 frame from the game's current 'view' (a plain
# description of where everything is, in pixels, at this instant of an animation). The rules never read it.
# ====================================================================================================

STREAM_BASE = {'day': LBL, 'cove': BLU, 'deep': BLU, 'pirate': LBL, 'stream': BLU, 'night': BLU,
               'serpent': LBL, 'dusk': LBL}
MINI_BOAT = ("..ww...",
             ".wwww..",
             "hhhhhhh",
             ".hhhhh.")


def stream_tile(heading, phase, base):
    """A 6x6 patch of running water: a coloured bed with white chevrons that move along the current."""
    tile = np.full((CELL, CELL), base, dtype=np.int16)
    for y in range(CELL):
        for x in range(CELL):
            u, v = x, y
            if heading[0] < 0:
                u = CELL - 1 - x
            if heading[1]:
                u, v = y, x
                if heading[1] < 0:
                    u = CELL - 1 - y
            if (u - abs(2 * v - 5) // 2 - 2 * phase) % 6 == 0:
                tile[y, x] = WHT
    return tile


def hatch_tile(beat):
    """The warning on the water: red diagonal stripes that flicker. A cell wearing it is deadly after your
    next move."""
    tile = np.full((CELL, CELL), -1, dtype=np.int16)
    for y in range(CELL):
        for x in range(CELL):
            if (x + y + beat) % 3 == 0:
                tile[y, x] = RED if beat % 2 == 0 else PNK
    return tile


def sail_status(sea, positions, moored, t):
    """'furled' (anchored), 'slack' (sheltered or on a shoal: the next gust will not move it) or 'full'."""
    wind = wind_at(sea, t)
    out = []
    for boat, here in enumerate(positions):
        if moored & (1 << boat):
            out.append('furled')
        elif sea.grid[here[1]][here[0]] == 'S' or sheltered(sea, positions, moored, boat, wind):
            out.append('slack')
        else:
            out.append('full')
    return out


def camera_for(sea, centre):
    """Pixel top-left of the window that keeps a pixel centre in the middle of the view, held inside the sea."""
    x = int(round(centre[0] - 32))
    y = int(round(centre[1] - VIEW_H / 2))
    return (max(0, min(sea.w * CELL - 64, x)), max(0, min(sea.h * CELL - VIEW_H, y)))


def cell_centre(cell):
    return (cell[0] * CELL + CELL // 2, cell[1] * CELL + CELL // 2)


def edge_markers(cam, centres):
    """For each boat out of the window: where its arrow sits on the window edge (screen pixels), pointing at it."""
    out = []
    mx, my = 32.0, VIEW_H / 2
    for boat, (px, py) in enumerate(centres):
        sx, sy = px - cam[0], py - cam[1]
        if -4 <= sx <= 67 and -6 <= sy <= VIEW_H + 4 and 0 <= sx < 64 and 0 <= sy < VIEW_H:
            continue
        vx, vy = sx - mx, sy - my
        scale = min((mx - 4) / abs(vx) if vx else 1e9, (my - 4) / abs(vy) if vy else 1e9)
        out.append((boat, int(round(mx + vx * scale)), int(round(my + vy * scale)), (vx, vy)))
    return out


def arrow_sprite(vx, vy, colour, size=7):
    """An arrowhead in a boat's colour, black-edged, turned toward (vx, vy); size is its width in pixels."""
    n = math.hypot(vx, vy) or 1.0
    ux, uy = vx / n, vy / n
    k = 7.0 / size
    c = (size - 1) / 2.0
    out = np.full((size, size), -1, dtype=np.int16)
    for y in range(size):
        for x in range(size):
            fx, fy = (x - c) * k, (y - c) * k
            along = fx * ux + fy * uy
            across = abs(-fx * uy + fy * ux)
            if -2.6 <= along <= 3.0 and across <= (3.0 - along) * 0.62 + 0.15:
                edge = (along < -1.7 or across > (3.0 - along) * 0.62 - 0.6 or along > 2.2)
                out[y, x] = BLK if edge and size >= 7 else colour
    return out


ARROW_RIGHT = ("..a..",
               "...a.",
               "aaaaa",
               "...a.",
               "..a..")
ARROW_UP = ("..a..",
            ".aaa.",
            "a.a.a",
            "..a..",
            "..a..")


def wind_arrow(wind, colour):
    """A 5x5 arrow for the strip under the sea."""
    dx, dy = wind
    base = art(ARROW_RIGHT if dx else ARROW_UP, dict(a=colour))
    if dx < 0:
        return flip(base)
    if dy > 0:
        return base[::-1].copy()
    return base


class Window(RenderableUserDisplay):

    def __init__(self, game):
        super().__init__()
        self._g = game

    # ---- the sea itself ----------------------------------------------------------------------------------
    def render_interface(self, frame):
        g = self._g
        v = g.view
        if v is None:
            return frame
        sea = g.sea
        theme = THEMES[sea.theme]
        cam_x, cam_y = v['cam']
        beat = v['beat']
        frame[:VIEW_H, :] = g.worlds[beat % 2][cam_y:cam_y + VIEW_H, cam_x:cam_x + 64]
        c0, c1 = cam_x // CELL, (cam_x + 63) // CELL
        r0, r1 = cam_y // CELL, (cam_y + VIEW_H - 1) // CELL
        calm = g.calm_for(v['wind'])
        warn = v['warn'] - sea.solid
        for cy in range(r0, min(r1, sea.h - 1) + 1):
            for cx in range(c0, min(c1, sea.w - 1) + 1):
                x, y = cx * CELL - cam_x, cy * CELL - cam_y
                cell = (cx, cy)
                if cell in sea.current:
                    blit(frame, x, y, stream_tile(sea.current[cell], beat % 3, STREAM_BASE[sea.theme]))
                elif cell in calm:                              # the lee of an island: glassy water, a lattice of glints
                    for py in range(CELL):
                        for px in range(CELL):
                            if 0 <= x + px < 64 and 0 <= y + py < VIEW_H and (px + beat % 2) % 3 == 1 and py % 3 == 1:
                                frame[y + py, x + px] = theme['glint']
                            elif 0 <= x + px < 64 and 0 <= y + py < VIEW_H and frame[y + py, x + px] == theme['ripple']:
                                frame[y + py, x + px] = theme['water']
                if cell in sea.whirlpools:
                    blit(frame, x - 3, y - 3, whirlpool(beat % 4))
                if cell in warn:
                    blit(frame, x, y, hatch_tile(beat))

        things = []                                              # (baseline, x, y, sprite): drawn back to front
        for kind, cx, cy in g.scenery:
            x, y = cx * CELL - cam_x, cy * CELL - cam_y
            if not (-14 <= x < 66 and -16 <= y < VIEW_H + 14):
                continue
            if kind == 'palm':
                things.append((y + CELL, x - 1, y + CELL - 10, PALM_A if (beat + cx + cy) % 2 else PALM_B))
            elif kind == 'bush':
                things.append((y + CELL, x, y + 3, BUSH))
            elif kind in ('hut', 'fire'):
                if kind == 'hut':
                    things.append((y + CELL, x - 3, y - 1, HUT))
                    chimney = (x + 5, y - 2)
                else:
                    things.append((y + CELL, x + 1, y + 1, (FIRE_A, FIRE_B, FIRE_C)[beat % 3]))
                    chimney = (x + 2, y)
                for puff in range(3):                            # smoke climbs and thins with each beat
                    things.append((y + CELL + 9, chimney[0] + ((puff + beat) % 2),
                                   chimney[1] - 2 - 3 * puff - (beat % 2), SMOKE[puff % 2]))
            elif kind == 'totem':
                things.append((y + CELL, x, y + CELL - 12, TOTEM))
            elif kind == 'chest':
                things.append((y + CELL, x, y + 2, CHEST))
            elif kind == 'tent':
                things.append((y + CELL, x - 1, y + 1, TENT))
            elif kind == 'torch':
                things.append((y + CELL, x + 1, y, TORCH[beat % 2]))
            elif kind == 'crab':
                things.append((y + CELL, x + 1, y + 3, CRAB[beat % 2]))
            elif kind == 'wreck':
                things.append((y + CELL, x - 2, y + 2, WRECK))
            elif kind == 'light':
                lamp = LIGHTHOUSE.copy()
                lamp[0, 2:4] = YEL if beat % 2 else WHT
                things.append((y + CELL, x, y + CELL - 14, lamp))
                things.append((y + CELL + 1, x + 3, y + CELL - 20, streamer('flag', v['wind'], beat % 2, RED)))
            elif kind == 'sock':
                things.append((y + CELL, x, y - 1, streamer('sock', v['wind'], beat % 2)))
        for boat, cell in enumerate(sea.goals):                  # each slip's flag streams downwind
            x, y = cell[0] * CELL - cam_x, cell[1] * CELL - cam_y
            if -8 <= x < 66 and -8 <= y < VIEW_H + 8:
                things.append((y + CELL - 1, x + 4, y - 8, streamer('flag', v['wind'], beat % 2, BOAT_COLOURS[boat])))
        for (px, py) in v['barrels']:
            things.append((py + 3, px - cam_x - 2, py - cam_y - 2 + (beat % 2), BARREL))
        self.creatures(things, v, sea, beat, cam_x, cam_y)
        for boat, (px, py) in enumerate(v['boats']):
            if boat in v['hidden']:
                continue
            bob = (beat + boat) % 2
            spr = boat_art(boat, v['face'][boat], v['status'][boat], v['wind'], beat)
            things.append((int(py) - cam_y + 3, int(px) - cam_x - 4, int(py) - cam_y - 8 + bob, spr))
        for (wx, wy, dx, dy) in v['wake']:                      # foam trailing behind a boat that is sliding
            for k in (1, 2, 3):
                fx = int(wx) - cam_x - dx * (2 + 2 * k) + (dy and (k % 2 * 2 - 1) * 2)
                fy = int(wy) - cam_y + 3 - dy * (2 + 2 * k) + (dx and (k % 2) - 1)
                if 0 <= fx < 64 and 0 <= fy < VIEW_H:
                    frame[fy, fx] = WHT
        for _, x, y, spr in sorted(things, key=lambda item: item[0]):
            blit(frame, int(x), int(y), spr)

        # the steered boat wears white corner marks
        sel = v['selected']
        px, py = v['boats'][sel]
        bx, by = int(px) - cam_x - 4, int(py) - cam_y - 4
        mark = RED if v['refused'] else WHT
        for (ox, oy, w, h) in ((-1, -1, 3, 1), (-1, -1, 1, 3), (7, -1, 3, 1), (9, -1, 1, 3),
                               (-1, 8, 3, 1), (-1, 6, 1, 3), (7, 8, 3, 1), (9, 6, 1, 3)):
            for yy in range(h):
                for xx in range(w):
                    sx, sy = bx + ox + xx, by + oy + yy
                    if 0 <= sx < 64 and 0 <= sy < VIEW_H:
                        frame[sy, sx] = mark

        if v['streak'] is not None:                              # the gust: white dashes sweeping downwind
            self.gust(frame, v['wind'], v['streak'])
        for (bx, by, r, colour) in v['bursts']:
            disc(frame, int(bx) - cam_x, int(by) - cam_y, r, colour, ring=True)
            disc(frame, int(bx) - cam_x, int(by) - cam_y, max(1, r - 2), WHT if colour != WHT else LBL, ring=True)
        for (sx, sy, k, colour) in v['sparks']:
            spr = SPARK[k % 3]
            blit(frame, int(sx) - cam_x - spr.shape[1] // 2, int(sy) - cam_y - spr.shape[0] // 2, np.where(spr >= 0, colour, -1))
        for boat, mx, my, (vx, vy) in edge_markers(v['cam'], v['boats']):
            spr = arrow_sprite(vx, vy, BOAT_COLOURS[boat])
            blit(frame, mx - 3, my - 3, spr)
        if v['flash'] is not None:
            frame[0, :VIEW_H] = v['flash']
            frame[0, :] = v['flash']
            frame[VIEW_H - 1, :] = v['flash']
            frame[:VIEW_H, 0] = v['flash']
            frame[:VIEW_H, 63] = v['flash']
        frame[VIEW_H:, :] = BLK                                  # the strip is cleared last so nothing spills into it
        frame[VIEW_H, :] = PUR                                   # the rule between the sea and the strip
        self.hud(frame, v, sea)
        return frame

    def creatures(self, things, v, sea, beat, cam_x, cam_y):
        """Sea monsters and pirate ships, interpolated between the move's start and end."""
        t0, t1, u = v['t_from'], v['t_to'], v['u']
        shown = t1 if u >= 0.5 else t0
        gaze_target = v['boats'][v['selected']]
        for k in sea.krakens:
            bx, by = k['x'] * CELL - cam_x, k['y'] * CELL - cam_y
            if not (-30 <= bx < 78 and -30 <= by < VIEW_H + 30):
                continue
            cxm, cym = (k['x'] + 1) * CELL, (k['y'] + 1) * CELL
            gaze = (int(np.sign(gaze_target[0] - cxm)) if abs(gaze_target[0] - cxm) > 8 else 0,
                    int(np.sign(gaze_target[1] - cym)) if abs(gaze_target[1] - cym) > 8 else 0)
            things.append(((k['y'] + 2) * CELL - cam_y, bx - 2, by - 2, kraken_body(gaze)))
            cells = k['arms'][shown % len(k['arms'])]
            for i, (ax, ay) in enumerate(cells):
                dx = (ax >= k['x'] + 2) - (ax < k['x'])
                dy = (ay >= k['y'] + 2) - (ay < k['y'])
                heading = (dx, 0) if dx else (0, dy)
                things.append(((k['y'] + 2) * CELL - cam_y - 1 + i, ax * CELL - cam_x, ay * CELL - cam_y,
                               arm_tile(heading, i == len(cells) - 1, i + shown)))
        for s in sea.serpents:
            body0, body1 = serpent_cells(s, t0), serpent_cells(s, t1)
            for k in (2, 1, 0):
                a, b = body0[k], body1[k]
                hx = (a[0] + (b[0] - a[0]) * u) * CELL + CELL // 2
                hy = (a[1] + (b[1] - a[1]) * u) * CELL + CELL // 2
                if k == 0:
                    near, back = (body1[0], body1[1]) if u >= 0.5 else (body0[0], body0[1])
                    heading = (int(np.sign(near[0] - back[0])), int(np.sign(near[1] - back[1])))
                    spr = serpent_head(heading if heading != (0, 0) else (1, 0))
                else:
                    spr = SERPENT_HUMP
                h, w = spr.shape
                things.append((int(hy) - cam_y + h // 2 - k, int(hx) - cam_x - w // 2, int(hy) - cam_y - h // 2, spr))
        for s in sea.ships:
            a, b = ship_cell(s, t0), ship_cell(s, t1)
            px = (a[0] + (b[0] - a[0]) * u) * CELL + CELL // 2
            py = (a[1] + (b[1] - a[1]) * u) * CELL + CELL // 2
            spr = ship_art(s['aim'], s['every'], t1 % s['every'], beat)
            things.append((int(py) - cam_y + 5, int(px) - cam_x - 10, int(py) - cam_y - 9 + (beat % 2), spr))

    def gust(self, frame, wind, progress):
        """Streaks of wind blown across the window; they move with the wind's own direction."""
        dx, dy = wind
        for k in range(9):
            n = hashed(k, 3, 5)
            along = int((n % 70) + progress * 26) % 80 - 8
            across = (n >> 6) % (VIEW_H - 4) + 2 if dx else (n >> 6) % 60 + 2
            for i in range(5):
                x, y = (along + i * dx, across) if dx else (across, along + i * dy)
                if dx < 0:
                    x = 63 - x
                if dy < 0:
                    y = VIEW_H - 1 - y
                if 0 <= x < 64 and 0 <= y < VIEW_H:
                    frame[y, x] = WHT

    # ---- the strip under the sea ----------------------------------------------------------------------------
    def hud(self, frame, v, sea):
        """The strip under the sea: a boat badge for each boat (white underline for the one you steer, a
        filled square when it sits in its berth), the wind now and next, the moves until the wind turns, a
        thin line of one segment per sea, and the move counter."""
        hud = v['hud']
        for boat in range(len(sea.goals)):
            x0 = 1 + boat * 11
            sprite = art(MINI_BOAT, dict(h=BOAT_COLOURS[boat], w=YEL if boat == 1 else WHT))
            blit(frame, x0, 55, sprite)
            if boat == v['selected']:
                frame[59, x0:x0 + 7] = WHT
            colour = BOAT_COLOURS[boat]
            frame[56:59, x0 + 8:x0 + 11] = colour
            if not hud['home'] >> boat & 1:                      # empty ring until the boat is home
                frame[57, x0 + 9] = BLK
        blit(frame, 36, 55, wind_arrow(v['wind'], WHT))
        if sea.wind_every:
            far = sea.wind_every - hud['tick'] % sea.wind_every
            nxt = wind_at(sea, hud['tick'] + far)
            blit(frame, 43, 55, wind_arrow(nxt, YEL))
            for i in range(sea.wind_every):
                frame[57:59, 50 + i * 2] = YEL if i < far else MAR
        for i in range(len(SEAS)):
            frame[60, 1 + i * 8:8 + i * 8] = GRN if i < hud['level'] else WHT if i == hud['level'] else MAR
        full, left = hud['counter'], hud['left']
        blocks_full = -(-full // COUNTER_UNIT)
        blocks = -(-max(0, left) // COUNTER_UNIT)
        fine = left - COUNTER_UNIT * (blocks - 1) if left > 0 else 0
        frame[61:63, 1:1 + blocks_full] = MAR
        frame[61:63, 1:1 + blocks] = RED if blocks <= 6 else YEL
        frame[63, 1:1 + fine] = WHT


# ====================================================================================================
# PART SIX: THE GAME. It owns the state and the move counter, asks part one what a command does, and turns
# the answer into a few animation frames (part five draws each one from a 'view').
# ====================================================================================================

_PICTURES = {}


def pictures(index):
    """The two ripple phases of a sea's still picture, and its scenery, painted once and kept."""
    if index not in _PICTURES:
        sea = SEAS[index]
        _PICTURES[index] = ((paint_world(sea, 0), paint_world(sea, 1)), scenery(sea))
    return _PICTURES[index]


def lerp(a, b, u):
    return a + (b - a) * u


class Wb03(ARCBaseGame):

    def __init__(self):
        self.index = 0
        self.sea = SEAS[0]
        self.state = initial(self.sea)
        self.face = [1] * len(self.sea.starts)
        self.used = 0
        self.history = []
        self.frames = []
        self.pending = None
        self.beat = 0
        self.view = None
        self.worlds = None
        self.scenery = []
        self._calm = {}
        camera = Camera(width=64, height=64, background=BLK, letter_box=BLK, interfaces=[Window(self)])
        super().__init__(game_id='wb03',
                         levels=[Level(sprites=[], name='sea-' + str(i + 1), data={'index': i})
                                 for i in range(len(SEAS))],
                         camera=camera, available_actions=[1, 2, 3, 4, 5, 6, 7])

    # ---- levels ---------------------------------------------------------------------------------------------
    def on_set_level(self, level):
        """All per-level state is made here, so the engine's own RESET refills the counter and the boats."""
        self.index = level.get_data('index')
        self.sea = SEAS[self.index]
        self.worlds, self.scenery = pictures(self.index)
        self.state = initial(self.sea)
        self.face = [1 if goal[0] >= start[0] else -1 for start, goal in zip(self.sea.starts, self.sea.goals)]
        self.used = 0
        self.history = []
        self.frames = []
        self.pending = None
        self.beat = 0
        self.view = self.make_view(self.state)

    def calm_for(self, wind):
        key = (self.index, wind)
        if key not in self._calm:
            self._calm[key] = calm_cells(self.sea, wind)
        return self._calm[key]

    # ---- pictures -------------------------------------------------------------------------------------------
    def make_view(self, state, **over):
        """A description of one instant: boats and barrels in pixels, the window, the warning cells, the HUD."""
        sea = self.sea
        positions, selected, moored, barrels, t = state
        centres = [cell_centre(c) for c in positions]
        view = dict(
            boats=centres, face=list(self.face), status=sail_status(sea, positions, moored, t),
            wind=wind_at(sea, t), selected=selected, barrels=[cell_centre(c) for c in barrels],
            t_from=t, t_to=t, u=1.0, beat=self.beat, refused=False, streak=None, bursts=[], sparks=[], wake=[],
            flash=None, hidden=(), warn=hazards(sea, t + 1, barrels) - sea.whirlpools,
            hud=dict(home=sum(1 << b for b, c in enumerate(positions) if c == sea.goals[b]), tick=t,
                     level=self.index, counter=COUNTERS[self.index], left=COUNTERS[self.index] - self.used))
        view['cam'] = camera_for(sea, centres[selected])
        view.update(over)
        view['hud']['left'] = COUNTERS[self.index] - self.used
        return view

    def sunk_boats(self, before, after):
        sea = self.sea
        harm = hazards(sea, after[4], after[3])
        old, new = movers(sea, before[4]), movers(sea, after[4])
        return [b for b, (start, end) in enumerate(zip(before[0], after[0]))
                if end in harm or (end in old and start in new)]

    def sail_frames(self, before, after, command):
        """Your boat moves; then the gust carries the rest and the creatures take their step."""
        sea = self.sea
        pos0, sel, moored0, barrels0, t0 = before
        pos1, _, moored1, barrels1, t1 = after
        dx, dy = STEER[command]
        mid = list(pos0)
        mid[sel] = (pos0[sel][0] + dx, pos0[sel][1] + dy)
        mid_state = (tuple(mid), sel, moored1, barrels1, t0)
        start = [cell_centre(c) for c in pos0]
        half = [cell_centre(c) for c in mid]
        end = [cell_centre(c) for c in pos1]
        pushed0 = [b for b in barrels0 if b not in barrels1]
        barrels_start = [cell_centre(b) for b in barrels0]
        barrels_mid = [cell_centre((b[0] + dx, b[1] + dy)) if b in pushed0 else cell_centre(b) for b in barrels0]
        frames = []
        base = self.make_view(mid_state, warn=frozenset())
        for u in (0.5, 1.0):
            boats = [(lerp(start[i][0], half[i][0], u), lerp(start[i][1], half[i][1], u)) for i in range(len(start))]
            barrels = [(lerp(a[0], b[0], u), lerp(a[1], b[1], u)) for a, b in zip(barrels_start, barrels_mid)]
            frames.append({**base, 'boats': boats, 'barrels': barrels, 'streak': 0.2 if u == 1.0 else None,
                           'cam': camera_for(sea, boats[sel]), 'status': sail_status(sea, tuple(pos0), moored1, t0),
                           'wake': [(boats[sel][0], boats[sel][1], dx, dy)]})
        for u in (0.5,):
            boats = [(lerp(half[i][0], end[i][0], u), lerp(half[i][1], end[i][1], u)) for i in range(len(half))]
            drifting = [(boats[i][0], boats[i][1], int(np.sign(end[i][0] - half[i][0])), int(np.sign(end[i][1] - half[i][1])))
                        for i in range(len(half)) if end[i] != half[i]]
            frames.append({**base, 'boats': boats, 'barrels': [cell_centre(b) for b in barrels1], 'streak': 0.7,
                           'wake': drifting,
                           't_from': t0, 't_to': t1, 'u': u, 'cam': camera_for(sea, boats[sel]),
                           'beat': self.beat})
        return frames

    def step(self):
        if self.action.id == GameAction.RESET:
            self.complete_action()
            return
        if not self.frames:
            self.plan()
        self.view = self.frames.pop(0)
        if not self.frames:
            if self.pending == 'lose':
                self.lose()
            elif self.pending == 'win':
                self.next_level()
            self.pending = None
            self.complete_action()

    def plan(self):
        """Work out what this command does and queue the frames that show it."""
        sea = self.sea
        command = self.action.id.value
        before = self.state
        if command == 7:
            if self.history:
                self.state, self.face = self.history.pop()      # undo restores the board, never the spent moves
                self.beat += 1
                self.frames = [self.make_view(before, refused=False), self.make_view(self.state)]
            else:
                self.frames = [self.make_view(before, refused=True), self.make_view(before)]
            return
        self.beat += 1
        self.used += 1
        if command == 6:
            command = self.click_target(int(self.action.data.get('x', -1)), int(self.action.data.get('y', -1)))
        after, outcome = advance(sea, before, command)
        if outcome == 'refused':
            self.frames = [self.make_view(before, refused=True), self.make_view(before)]
            if self.used >= COUNTERS[self.index]:
                self.run_out()
            return
        self.history.append((before, list(self.face)))
        self.state = after
        if outcome == 'switched':
            old = camera_for(sea, cell_centre(before[0][before[1]]))
            new = camera_for(sea, cell_centre(after[0][after[1]]))
            self.frames = [self.make_view(before, cam=(int(lerp(old[0], new[0], u)), int(lerp(old[1], new[1], u))))
                           for u in (0.25, 0.5, 0.75)] + [self.make_view(after)]
            if self.used >= COUNTERS[self.index]:
                self.run_out()
            return
        moved_dx = STEER[command][0]
        if moved_dx:
            self.face[before[1]] = moved_dx
        self.frames = self.sail_frames(before, after, command)
        end = self.make_view(after)
        if outcome == 'sunk':
            lost = self.sunk_boats(before, after)
            centres = [cell_centre(after[0][b]) for b in lost]
            for r in (2, 4, 6):
                self.frames.append({**end, 'bursts': [(c[0], c[1], r, WHT if r % 4 else LBL) for c in centres],
                                    'flash': RED, 'hidden': tuple(lost), 'warn': frozenset()})
            self.pending = 'lose'
        elif won(sea, after):
            for k in range(4):
                sparks = []
                for i, c in enumerate(end['boats']):
                    for n in range(8):
                        angle = n * math.pi / 4 + k * 0.3
                        reach = 5 + 4 * (k + 1)
                        sparks.append((c[0] + math.cos(angle) * reach, c[1] - 3 + math.sin(angle) * reach * 0.8,
                                       k + n, (YEL, WHT, BOAT_COLOURS[i])[(n + k) % 3]))
                lift = 1 if k % 2 else 0
                self.frames.append({**end, 'sparks': sparks, 'warn': frozenset(), 'beat': self.beat + k,
                                    'boats': [(c[0], c[1] - lift) for c in end['boats']]})
            self.pending = 'win'
        else:
            self.frames.append(end)
            if self.used >= COUNTERS[self.index]:
                self.run_out()

    def run_out(self):
        """The move counter is empty: the sails go slack and the window flashes red; the run is over."""
        view = self.make_view(self.state, status=['slack'] * len(self.state[0]))
        self.frames += [{**view, 'flash': RED if k % 2 == 0 else None} for k in range(4)]
        self.pending = 'lose'

    def click_target(self, x, y):
        """A click on a boat, or on its arrow at the window edge, hands control to that boat (10 + boat)."""
        v = self.view
        if v is None or not (0 <= x < 64 and 0 <= y < VIEW_H):
            return 0
        cam = v['cam']
        for boat, (px, py) in enumerate(v['boats']):
            sx, sy = int(px) - cam[0], int(py) - cam[1]
            if abs(x - sx) <= 5 and -9 <= y - sy <= 5:
                return 10 + boat
        for boat, mx, my, _ in edge_markers(cam, v['boats']):
            if abs(x - mx) <= 4 and abs(y - my) <= 4:
                return 10 + boat
        return 0
