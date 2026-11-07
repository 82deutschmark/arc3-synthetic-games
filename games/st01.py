# ARC-AGI-3 candidate task st01 (Shadow Topple): a moving light, a shadow, and holes to fill.
# Author: Team Turducken agents, under Mark Barney's direction
# Date: October 2026
# PURPOSE: st01: turn the light and click a solid; it topples along its shadow into the holes. Win by levelling the board.
# SRP/DRY check: Pass -- pure rules (cast, fell) first, drawing next, the engine game class last.
# Updated: 05-November-2026, Claude Fable 5.1 -- the game is st01 (it reported itself as g014); a lost position now ends
#   the run as GAME_OVER instead of silently restarting the level; the winnability memo lives on the game, not the
#   module; RESET restarts the level, or the whole game only when nothing has been played or it is won.
# Updated: 07-November-2026, Claude Opus 5.5 -- each level now has a move counter (every light turn and every click
#   spends one) drawn as a white bar under the board; the run ends when it runs out. The game no longer searches
#   ahead to end a stuck run, so the winnability search and its memo are gone.
#
# Designer notes
# --------------
# The light sits on one side of the board. Every solid casts a shadow away from it.
# Click a solid and it topples along that shadow; the shadow is exactly the ground it
# lands on, and every hole it lands on gets one step shallower. The solid itself is gone.
# Win a level by leaving the whole board level: no hole left, no solid left.
#
# What you can do: turn the light (left/right arrows, or Space, which turns it clockwise)
# and click a solid. A solid may only topple when its whole shadow falls into holes, so a
# shadow drawn as a chequer is a solid that is refused: it would hang over floor, run into
# something, or run off the board. A hole deepens the reach of a shadow that crosses it.
#
# Every action spends one step of the white bar under the board: each turn of the light and
# each click, even a refused one. When the bar is empty and the board is not level, the board
# flashes and the run ends (GAME_OVER); RESET starts the level again with a full bar. A stuck
# player is not stopped early: the game never looks ahead to judge whether a level is lost.

import numpy as np

from arcengine import (
    ARCBaseGame,
    BlockingMode,
    Camera,
    GameAction,
    GameState,
    InteractionMode,
    Level,
    RenderableUserDisplay,
    Sprite,
)

N = 11
CELL = 5
INSET = (64 - N * CELL) // 2
WALL = 9

C_INK = 5
C_FLOOR = 11
C_SHADE = 15
C_BLOCK = 14
C_PIT = 9
C_PIP = 0
C_BAD = 8
C_SUN = 11

SUNS = ((0, -1), (1, 0), (0, 1), (-1, 0))

TOPPLE_FRAMES = 8
REFUSE_FRAMES = 5
POKE_FRAMES = 3
TURN_FRAMES = 3
DIE_FRAMES = 16

DEPTHS = {".": 0, "a": -1, "b": -2, "c": -3, "#": WALL}

# Moves per level (light turns plus clicks). Each is twice the shortest winning line, found by an
# exact search over the game's own rules (fell / regions, A-star with a per-room lower bound,
# matching plain breadth-first search on levels 1-6): 1, 12, 11, 15, 15, 19, 23, 27 moves.
BUDGETS = (2, 24, 22, 30, 30, 38, 46, 54)
C_BAR = C_PIP
BAR_ROW = INSET + N * CELL      # the one free row between the board and a light at the bottom

# LEVELS_BEGIN
LEVELS_SPEC = [
    {"sun0": 0, "rows": [
        "###########",
        "##.......##",
        "##..333..##",
        "##..aaa..##",
        "##..aaa..##",
        "##..aaa..##",
        "##.......##",
        "##.......##",
        "###########",
        "###########",
        "###########",
    ]},
    {"sun0": 0, "rows": [
        "###########",
        "#.........#",
        "#2.3.2.3.2#",
        "#b.b.b.b.b#",
        "#b.b.b.b.b#",
        "#2.b.2.b.2#",
        "#..3...3..#",
        "#.........#",
        "###########",
        "###########",
        "###########",
    ]},
    {"sun0": 0, "rows": [
        "###########",
        "#.aa2aaa3.#",
        "#a.......3#",
        "#a.......a#",
        "#2.......a#",
        "#a.......a#",
        "#a.......2#",
        "#a.......a#",
        "#3.......a#",
        "#.3aaa2aa.#",
        "###########",
    ]},
    {"sun0": 0, "rows": [
        "###########",
        "#.aa2aaa3.#",
        "#a.......3#",
        "#a..2.2..a#",
        "#2..b.b..a#",
        "#a..b.b..a#",
        "#a..2.2..2#",
        "#a.......a#",
        "#3.......a#",
        "#.3aaa2aa.#",
        "###########",
    ]},
    {"sun0": 0, "rows": [
        "###########",
        "..3aa#..4..",
        "aaa2.#..a3a",
        "aaa2.#2bba.",
        ".....#3bbaa",
        "ab2..#3bbaa",
        "ab2..#3bbaa",
        "ab2..#a3...",
        "ab2.2#23...",
        ".3.2b#.3...",
        "###########",
    ]},
    {"sun0": 0, "rows": [
        "a....#..4.a",
        "32.4a#a3a.a",
        "3a...#aab23",
        "2b4aa#..a..",
        ".a...#33baa",
        "###########",
        "#aaab3....#",
        "#aa2bba3..#",
        "#...22.2..#",
        "#...224baa#",
        "#......a..#",
    ]},
    {"sun0": 0, "rows": [
        "aa.a.#baa4.",
        "aa242#baa4.",
        "a42b2#a3224",
        "3..aa#bb4aa",
        "...3a#2a.aa",
        "###########",
        "#.aab2..a.#",
        "#4a3a.2aba#",
        "#4abba44a.#",
        "#4abbabb2.#",
        "#..a2.aa..#",
    ]},
    {"sun0": 0, "rows": [
        "bba2.#.aa..",
        "aa3aa#.2a42",
        "234aa#a4a42",
        "...3.#..2aa",
        "...a.#2aaba",
        "###########",
        "bba2.#.aaa.",
        "aa3aa#2333.",
        "234aa#a44aa",
        "...3.#ba2.3",
        "...a.#a3aab",
    ]},
]
# LEVELS_END


def heights(rows):
    rows = [r.ljust(N, "#")[:N] for r in rows]
    while len(rows) < N:
        rows.append("#" * N)
    return tuple(tuple(DEPTHS[c] if c in DEPTHS else int(c) for c in row) for row in rows)


def block_at(field, cell):
    x, y = cell
    if not (0 <= x < N and 0 <= y < N) or not (1 <= field[y][x] < WALL):
        return frozenset()
    tall = field[y][x]
    seen, stack = {cell}, [cell]
    while stack:
        cx, cy = stack.pop()
        for dx, dy in SUNS:
            nx, ny = cx + dx, cy + dy
            if (0 <= nx < N and 0 <= ny < N and (nx, ny) not in seen
                    and field[ny][nx] == tall):
                seen.add((nx, ny))
                stack.append((nx, ny))
    return frozenset(seen)


def regions(field):
    seen, out = set(), []
    for y in range(N):
        for x in range(N):
            if 1 <= field[y][x] < WALL and (x, y) not in seen:
                r = block_at(field, (x, y))
                seen |= r
                out.append((x, y))
    return out


def cast(field, solid, sun):
    """The ground a solid's shadow touches: (cells, ok). A cell at distance d is in the
    shadow while d <= height of the solid minus the height of the ground there, so a
    shadow runs longer over a hole. A wall or the board's edge simply ends a shadow. ok means
    every shadowed cell is a hole: a shadow still alive over floor or over another solid
    is refused."""
    seed = next(iter(solid))
    tall = field[seed[1]][seed[0]]
    fx, fy = -sun[0], -sun[1]
    cells, ok = [], True
    for x, y in solid:
        d = 0
        while True:
            d += 1
            nx, ny = x + fx * d, y + fy * d
            if not (0 <= nx < N and 0 <= ny < N):
                break
            if (nx, ny) in solid:
                break
            g = field[ny][nx]
            if tall - g - d + 1 <= 0:
                break
            if g >= 0:
                ok = False
                if g >= 1:
                    break
            if (nx, ny) not in cells:
                cells.append((nx, ny))
    if not cells:
        ok = False
    return cells, ok


def shadow_of(field, solid, sun):
    if not solid:
        return None
    cells, ok = cast(field, solid, sun)
    return set(cells) if ok else None


def fell(field, cell, sun_index):
    solid = block_at(field, cell)
    landing = shadow_of(field, solid, SUNS[sun_index])
    if not landing:
        return None
    grid = [list(row) for row in field]
    for x, y in landing:
        grid[y][x] += 1
    for x, y in solid:
        grid[y][x] = 0
    return tuple(tuple(row) for row in grid)


def is_flat(field) -> bool:
    return all(v == 0 or v >= WALL for row in field for v in row)


def build_levels() -> list[Level]:
    pad = lambda: Sprite(
        pixels=[[C_INK] * (N * CELL) for _ in range(N * CELL)], name="board",
        blocking=BlockingMode.NOT_BLOCKED, interaction=InteractionMode.INTANGIBLE,
        layer=-2, tags=["sys_click", "sys_every_pixel"],
    ).set_position(INSET, INSET)
    return [Level(sprites=[pad()], grid_size=(64, 64)) for _ in LEVELS_SPEC]


# ---------------------------------------------------------------------------------------
# drawing

DICE = {
    1: ((2, 2),),
    2: ((1, 1), (3, 3)),
    3: ((1, 1), (2, 2), (3, 3)),
    4: ((1, 1), (3, 1), (1, 3), (3, 3)),
    5: ((1, 1), (3, 1), (2, 2), (1, 3), (3, 3)),
    6: ((1, 1), (1, 2), (1, 3), (3, 1), (3, 2), (3, 3)),
}


def dice(frame, px, py, n, colour):
    for dx, dy in DICE[min(max(n, 1), 6)]:
        frame[py + dy, px + dx] = colour


def cell_origin(x, y):
    return INSET + x * CELL, INSET + y * CELL


WEDGE = (4, 3, 2, 1)


def paint_sun(frame, sun, depth=4):
    sx, sy = sun
    for k in range(depth):
        half = WEDGE[k]
        lo, hi = 32 - half, 32 + half
        if sy < 0:
            frame[k, lo:hi] = C_SUN
        elif sy > 0:
            frame[63 - k, lo:hi] = C_SUN
        elif sx < 0:
            frame[lo:hi, k] = C_SUN
        else:
            frame[lo:hi, 63 - k] = C_SUN
    for offset in (-12, 12):
        for k in range(min(depth, 3)):
            if sy < 0:
                frame[k, 32 + offset] = C_SUN
            elif sy > 0:
                frame[63 - k, 32 + offset] = C_SUN
            elif sx < 0:
                frame[32 + offset, k] = C_SUN
            else:
                frame[32 + offset, 63 - k] = C_SUN


def outline_cells(frame, cells, colour):
    cells = set(cells)
    for x, y in cells:
        px, py = cell_origin(x, y)
        if (x, y - 1) not in cells:
            frame[py, px:px + CELL] = colour
        if (x, y + 1) not in cells:
            frame[py + CELL - 1, px:px + CELL] = colour
        if (x - 1, y) not in cells:
            frame[py:py + CELL, px] = colour
        if (x + 1, y) not in cells:
            frame[py:py + CELL, px + CELL - 1] = colour


class ShadowDisplay(RenderableUserDisplay):

    def __init__(self, game: "St01") -> None:
        super().__init__()
        self._game = game

    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        g = self._game
        field = g.field
        frame[:, :] = C_INK
        good, bad = {}, set()
        anchors = set(regions(field))
        for cell in anchors:
            solid = block_at(field, cell)
            cells, ok = cast(field, solid, SUNS[g.sun])
            if ok:
                for c in cells:
                    good[c] = True
            else:
                for c in cells:
                    if field[c[1]][c[0]] < 1:
                        bad.add(c)
        for y in range(N):
            for x in range(N):
                h = field[y][x]
                if h >= WALL:
                    continue
                px, py = cell_origin(x, y)
                if h >= 1:
                    self._paint_block(frame, field, x, y, px, py, h, (x, y) in anchors)
                elif h < 0:
                    base = C_SHADE if (x, y) in good else C_PIT
                    if (x, y) in bad and (x, y) not in good:
                        self._paint_pit(frame, field, x, y, px, py, h, C_PIT, chequer=True)
                    else:
                        self._paint_pit(frame, field, x, y, px, py, h, base)
                else:
                    frame[py:py + CELL, px:px + CELL] = C_FLOOR
                    if (x, y) in bad:
                        for j in range(CELL):
                            for i in range(CELL):
                                if i % 2 == 0 and j % 2 == 0:
                                    frame[py + j, px + i] = C_SHADE
        if g.phase == "topple":
            self._paint_topple(frame, g)
        elif g.phase == "refuse":
            if (g.tick_index() // 2) % 2 == 0:
                outline_cells(frame, g.cue_cells, C_BAD)
        elif g.phase == "poke":
            outline_cells(frame, g.cue_cells, C_BAD)
            if g.cue_point is not None:
                cx, cy = g.cue_point
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        if max(abs(dx), abs(dy)) == 2 and 0 <= cx + dx < 64 and 0 <= cy + dy < 64:
                            frame[cy + dy, cx + dx] = C_BAD
        if g.phase == "turn":
            paint_sun(frame, SUNS[g.prev_sun], depth=max(1, 3 - g.tick_index() * 2))
            paint_sun(frame, SUNS[g.sun], depth=min(4, 1 + g.tick_index() * 2))
        elif g.phase == "die":
            idx = g.tick_index()
            for y in range(INSET, INSET + N * CELL):
                for x in range(INSET, INSET + N * CELL):
                    if (x + y + idx // 3) % 2 == 0 and frame[y, x] != C_INK:
                        frame[y, x] = C_BAD
        else:
            paint_sun(frame, SUNS[g.sun])
        # the move counter: a bar under the board that loses at least one pixel per move
        span = N * CELL
        if g.budget:
            left = -(-span * max(0, g.moves_left) // g.budget)
            frame[BAR_ROW, INSET:INSET + left] = C_BAR
        return frame

    def _paint_block(self, frame, field, x, y, px, py, h, anchor):
        frame[py:py + CELL, px:px + CELL] = C_BLOCK
        same = lambda a, b: 0 <= a < N and 0 <= b < N and field[b][a] == h
        if not same(x, y - 1):
            frame[py, px:px + CELL] = C_INK
        if not same(x, y + 1):
            frame[py + CELL - 1, px:px + CELL] = C_INK
        if not same(x - 1, y):
            frame[py:py + CELL, px] = C_INK
        if not same(x + 1, y):
            frame[py:py + CELL, px + CELL - 1] = C_INK
        if anchor:
            dice(frame, px, py, h, C_PIP)

    def _paint_pit(self, frame, field, x, y, px, py, h, base, chequer=False):
        frame[py:py + CELL, px:px + CELL] = base
        if chequer:
            for j in range(CELL):
                for i in range(CELL):
                    if i % 2 == 0 and j % 2 == 0:
                        frame[py + j, px + i] = C_SHADE
        pit = lambda a, b: 0 <= a < N and 0 <= b < N and -3 <= field[b][a] < 0
        if not pit(x, y - 1):
            frame[py, px:px + CELL] = C_INK
        if not pit(x - 1, y):
            frame[py:py + CELL, px] = C_INK
        dice(frame, px, py, -h, C_PIP)

    def _paint_topple(self, frame, g):
        total = TOPPLE_FRAMES
        progress = (g.tick_index() + 1) / (total + 1)
        fx, fy = -SUNS[g.sun][0], -SUNS[g.sun][1]
        solid, landing = g.topple_from, g.topple_to
        if not landing:
            return
        origin = min(x * fx + y * fy for x, y in solid)
        reach = max(x * fx + y * fy for x, y in landing) - origin + 1
        front = origin * CELL + progress * reach * CELL
        for x, y in landing:
            px, py = cell_origin(x, y)
            for j in range(CELL):
                for i in range(CELL):
                    along = (x * CELL + i) * fx + (y * CELL + j) * fy
                    if along <= front:
                        frame[py + j, px + i] = C_INK if front - along < 1.5 else C_BLOCK
        for x, y in solid:
            px, py = cell_origin(x, y)
            for j in range(CELL):
                for i in range(CELL):
                    along = (x * CELL + i) * fx + (y * CELL + j) * fy
                    if along <= front:
                        frame[py + j, px + i] = C_FLOOR


class St01(ARCBaseGame):

    def __init__(self) -> None:
        spec = LEVELS_SPEC[0]
        self.field = heights(spec["rows"])
        self.sun = spec.get("sun0", 0)
        self.prev_sun = self.sun
        self.phase = None
        self.tick = 0
        self.tick_total = 0
        self.topple_from = frozenset()
        self.topple_to = set()
        self.pending = self.field
        self.cue_cells = set()
        self.cue_point = None
        self.budget = BUDGETS[0]
        self.moves_left = self.budget
        camera = Camera(
            width=64, height=64,
            background=C_INK, letter_box=C_INK,
            interfaces=[ShadowDisplay(self)],
        )
        super().__init__(game_id="st01", levels=build_levels(), camera=camera,
                         available_actions=[3, 4, 5, 6])

    def tick_index(self) -> int:
        return self.tick_total - self.tick

    def on_set_level(self, level: Level) -> None:
        spec = LEVELS_SPEC[self.level_index]
        self.field = heights(spec["rows"])
        self.sun = spec.get("sun0", 0)
        self.prev_sun = self.sun
        self.phase = None
        self.tick = 0
        self.tick_total = 0
        self.topple_from = frozenset()
        self.topple_to = set()
        self.pending = self.field
        self.cue_cells = set()
        self.cue_point = None
        self.budget = BUDGETS[self.level_index]
        self.moves_left = self.budget

    def _begin(self, phase: str, frames: int) -> None:
        self.phase = phase
        self.tick_total = frames
        self.tick = frames

    def _finish_topple(self) -> None:
        self.field = self.pending
        self.topple_from = frozenset()
        self.topple_to = set()
        self.phase = None
        if is_flat(self.field):
            self.next_level()
            self.complete_action()
        else:
            self._settle()

    def _settle(self) -> None:
        """End of a move that did not win: an empty counter flashes the board, then the run is lost."""
        if self.moves_left <= 0:
            self._begin("die", DIE_FRAMES)
        else:
            self.complete_action()

    def step(self) -> None:
        if self.action.id == GameAction.RESET:
            self.complete_action()
            return

        if self.phase is not None:
            self.tick -= 1
            if self.tick > 0:
                return
            phase = self.phase
            if phase == "topple":
                self._finish_topple()
            elif phase == "die":
                self.phase = None
                self.lose()
                self.complete_action()
            else:
                self.phase = None
                self._settle()
            return

        aid = self.action.id
        if aid in (GameAction.ACTION3, GameAction.ACTION4, GameAction.ACTION5, GameAction.ACTION6):
            self.moves_left -= 1
        if aid in (GameAction.ACTION3, GameAction.ACTION4, GameAction.ACTION5):
            self.prev_sun = self.sun
            self.sun = (self.sun + (-1 if aid == GameAction.ACTION3 else 1)) % 4
            self._begin("turn", TURN_FRAMES)
            return
        if aid == GameAction.ACTION6:
            x = self.action.data.get("x", 0)
            y = self.action.data.get("y", 0)
            cell = ((x - INSET) // CELL, (y - INSET) // CELL)
            solid = block_at(self.field, cell)
            if solid:
                landing = shadow_of(self.field, solid, SUNS[self.sun])
                if landing:
                    nxt = fell(self.field, cell, self.sun)
                    self.topple_from = solid
                    self.topple_to = landing
                    self.pending = nxt
                    self._begin("topple", TOPPLE_FRAMES)
                else:
                    self.cue_cells = set(solid)
                    self._begin("refuse", REFUSE_FRAMES)
                return
            self.cue_cells = set()
            self.cue_point = None
            if (0 <= cell[0] < N and 0 <= cell[1] < N
                    and self.field[cell[1]][cell[0]] < WALL):
                self.cue_cells = {cell}
            else:
                self.cue_point = (x, y)
            self._begin("poke", POKE_FRAMES)
            return
        self.complete_action()
