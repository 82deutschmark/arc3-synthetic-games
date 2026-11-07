# ARC-AGI-3 candidate task st02 (Shadow Topple, redrawn): a moving light, a shadow, and holes to fill.
# Author: Claude Sonnet 5.5 (art passes 1 to 4); rules by Team Turducken agents under Mark Barney's direction
# Date: 07-November-2026
# PURPOSE: st02 redraws st01 (Shadow Topple). The RULES ARE UNCHANGED: same eight boards, same light that turns,
#          same click-to-topple along the shadow, same move counter and loss, same inputs. Only the pictures are new:
#          every thing on the screen is a named engine sprite (a sun with a face on the board's edge, one tile sprite
#          per board square, a burning-fuse counter, dust, sparkles, a sad sun and a red haze on a loss), and each of
#          the eight levels has its own world: meadow, snowfield, lava cave, toy workshop, desert, candy land, ocean
#          floor, deep space. Nothing on the play surface speaks; height and depth are still shown by dice pips.
# SRP/DRY check: Pass -- part 1 is st01's rule code copied unchanged (cast, fell, regions), part 2 is pure art data and
#          small painters, part 3 builds each level's sprites, part 4 is the game class, which only moves sprites.
#          st01 stays as it is; nothing is shared with it.
#
# CHANGELOG
# 07-Nov-2026 (Claude Sonnet 5.5): first redraw (pass 1: build). Rules identical to st01 at 07-Nov-2026.
# 07-Nov-2026 (Claude Sonnet 5.5): pass 2 (critique and redraw). A wider sun with two-pixel eyes, blush, tears and a
#   shimmering rim; a faced critter per world on the walls that blinks, cheers and cries (the old decorations are
#   gone); brick walls and a calmer frame; mostly plain floors; surfaces on the blocks (planks, ice, rock, studs);
#   big wall props on every level (ore, toy stacks, totems, cupcakes, lollipops, wrecks, lighthouses, rockets and
#   more); a gem that runs round the frame; a lit slab and a bigger, tinted dust puff; blocks that slump on a loss.
#   No rule changed.
# 07-Nov-2026 (Claude Sonnet 5.5): pass 3 (variety and life). Each world now has its own frame emblem (flowers, flakes,
#   flames, toy blocks, ...); a ploughed-field wall on L1, snow-brick wall on L2, ember-flecked and star-flecked walls,
#   five floor looks per world (flowers, sapling, crystals, sprouts, shells, planets...); many more wall props, several
#   with faces (cupcakes, gumdrops, teddies, skulls, a ghost ship). A new layer of living named sprites per level that
#   mean nothing: trees that ripen, torches that flicker, ore that glints, butterflies, bats, drifting snow and embers,
#   cogs, balloons, a blinking snowman and totems, a scarab, rolling bonbons, falling sprinkles, fish, bubbles, swaying
#   weed, a flashing lamp, a comet, a blinking saucer. Level clear now showers confetti over the sparkles. A lost run
#   brings a weeping rain cloud and the blocks slump a third row. No rule changed.
# 07-Nov-2026 (Claude Sonnet 5.5): pass 4 (final review). Every level opening, a mid-play strip, a win, a loss and the
#   first frame after reset were rendered and read; the sameness check against st01 ran at 60 episodes of 200 steps with
#   no differences. No picture or rule changed in this pass.
#
# How the picture is kept cheap: every board square is a 5x5 sprite named cell-X-Y whose pixels are swapped only when
# the square's look changes (a cached tile, so a swap is a pointer change). The floor, the walls and their props are one
# static sprite (board) under them, so a square that is plain floor is simply hidden. Per action at most about fifteen
# frames are drawn; a step touches only the squares whose look changed plus a handful of small sprites.
#
# The light is drawn as a half sun (15 wide, 4 deep) peeking over the board's edge (four sprites, one per edge, only the live one shown).
# A turn slides the old sun out and the new one in, exactly where st01 shrank and grew its wedge.

from __future__ import annotations

from functools import lru_cache

import numpy as np

from arcengine import (
    ARCBaseGame,
    BlockingMode,
    Camera,
    GameAction,
    InteractionMode,
    Level,
    Sprite,
)

# ═════════════════════════════════════════════════════════════════════════════════════════════
# PART 1 -- THE RULES (copied from st01 unchanged; do not touch when redrawing)
# ═════════════════════════════════════════════════════════════════════════════════════════════

N = 11
CELL = 5
INSET = (64 - N * CELL) // 2
WALL = 9

C_INK = 5

SUNS = ((0, -1), (1, 0), (0, 1), (-1, 0))

TOPPLE_FRAMES = 8
REFUSE_FRAMES = 5
POKE_FRAMES = 3
TURN_FRAMES = 3
DIE_FRAMES = 12          # st01 held the red flash for 16 frames; the picture only needs 12
CHEER_FRAMES = 6         # new: the level-clear sparkle, played before the engine moves on

DEPTHS = {".": 0, "a": -1, "b": -2, "c": -3, "#": WALL}

# Moves per level (light turns plus clicks). Each is twice the shortest winning line, found by an
# exact search over the game's own rules (fell / regions, A-star with a per-room lower bound,
# matching plain breadth-first search on levels 1-6): 1, 12, 11, 15, 15, 19, 23, 27 moves.
BUDGETS = (2, 24, 22, 30, 30, 38, 46, 54)
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


# ═════════════════════════════════════════════════════════════════════════════════════════════
# PART 2 -- THE ART (pure data and painters; nothing here reads or decides game state)
# ═════════════════════════════════════════════════════════════════════════════════════════════

# The 16 ARC colours. Colours 1-4 are greys and are never used for art.
WHT, BLK, MAG, PNK, RED, BLU, LBL, YEL, ORG, MAR, GRN, PUR = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
SHADOW = PUR       # a shadow is always this colour, in every world, so it always reads the same
BAD = RED          # the refusal outline

# One letter per colour so sprites can be drawn as pictures. "." is see-through. "c" is a chip colour that a
# painter swaps for the world's block colour (the dust).
GLYPH = {".": -1, "w": 0, "k": 5, "m": 6, "p": 7, "r": 8, "b": 9, "l": 10, "y": 11,
         "o": 12, "n": 13, "g": 14, "u": 15, "c": 100}


def art(rows):
    """A picture drawn in letters -> int8 pixels (-1 is see-through)."""
    return np.array([[GLYPH[c] for c in row] for row in rows], dtype=np.int8)


def tile(rows):
    """A 5x5 board-square picture; a typo in a row length fails at import, not mid-game."""
    assert len(rows) == 5 and all(len(r) == 5 for r in rows), rows
    return art(rows)


def hashed(x, y, salt=0):
    """Small deterministic scramble so neighbouring squares get different variants, the same every run."""
    return ((x * 73856093) ^ (y * 19349663) ^ (salt * 83492791)) & 0xFFFF


def blit(dst, x, y, src):
    """Paste src onto dst at x, y, skipping see-through pixels and anything off the edge."""
    h, w = src.shape
    for j in range(h):
        for i in range(w):
            v = src[j, i]
            if v >= 0 and 0 <= y + j < dst.shape[0] and 0 <= x + i < dst.shape[1]:
                dst[y + j, x + i] = v


def halo(src, colour):
    """Draw a one-pixel outline around a picture so it stands off any background."""
    h, w = src.shape
    out = np.full((h + 2, w + 2), -1, dtype=np.int8)
    for j in range(h):
        for i in range(w):
            if src[j, i] >= 0:
                for dj in (-1, 0, 1):
                    for di in (-1, 0, 1):
                        if out[j + 1 + dj, i + 1 + di] < 0:
                            out[j + 1 + dj, i + 1 + di] = colour
    for j in range(h):
        for i in range(w):
            if src[j, i] >= 0:
                out[j + 1, i + 1] = src[j, i]
    return out


def recolour(src, colour):
    """Same shape, one colour (for sparkles that change colour)."""
    return np.where(src >= 0, colour, -1).astype(np.int8)


def bricks(fill, seam, hi):
    """Three 5x5 wall tiles that join into a brick wall: a seam row, offset upright seams, a lit corner on each brick."""
    def make(flip, lit):
        t = np.full((5, 5), GLYPH[fill], dtype=np.int8)
        t[2, :] = GLYPH[seam]
        sx_top, sx_bot = (0, 3) if flip else (4, 1)
        t[0:2, sx_top] = GLYPH[seam]
        t[3:5, sx_bot] = GLYPH[seam]
        if lit:
            t[0, (sx_top + 1) % 5] = GLYPH[hi]
            t[3, (sx_bot + 1) % 5] = GLYPH[hi]
        return t
    return [make(False, True), make(True, True), make(False, False)]


# ----------------------------------------------------------------------------------------------
# Dice pips: how tall a solid is, how deep a hole is. Same drawing as st01 so the reading is the same.

DICE = {
    1: ((2, 2),),
    2: ((1, 1), (3, 3)),
    3: ((1, 1), (2, 2), (3, 3)),
    4: ((1, 1), (3, 1), (1, 3), (3, 3)),
    5: ((1, 1), (3, 1), (2, 2), (1, 3), (3, 3)),
    6: ((1, 1), (1, 2), (1, 3), (3, 1), (3, 2), (3, 3)),
}

# ----------------------------------------------------------------------------------------------
# The wall critters: one little creature per world, 5x5, with a face. Each is a body picture (two sway poses),
# where the face goes (eye row, mouth row, mouth colour) and how it reacts: calm (blinks now and then),
# cheer (grin, hops) when a level is cleared, sad (tears) when the run is lost. Eyes sit at columns 1 and 3,
# the mouth at column 2, so every body must be solid on those squares.

CRITTERS = [
    dict(  # meadow: a bee
        a=[".yyy.", "yyyyy", "yyyyy", "kkkkk", ".yyy."],
        b=["wyyyw", "yyyyy", "yyyyy", "kkkkk", ".yyy."], ey=1, my=2, mc="k"),
    dict(  # snowfield: a penguin
        a=[".kkk.", "kwwwk", "kwwwk", "kwwwk", ".o.o."],
        b=[".kkk.", "kwwwk", "kwwwk", "kwwwk", "o...o"], ey=2, my=3, mc="o"),
    dict(  # lava cave: a fire sprite
        a=["..y..", ".yoy.", ".ooo.", ".ooo.", "..r.."],
        b=[".y...", ".yoy.", ".ooo.", ".ooo.", "..r.."], ey=2, my=3, mc="k"),
    dict(  # toy workshop: a tin robot
        a=["..r..", "lllll", "lllll", ".yyy.", ".y.y."],
        b=["..r..", "lllll", "lllll", ".yyy.", "y...y"], ey=1, my=2, mc="k"),
    dict(  # desert: a cactus
        a=["..y..", ".ggg.", "gggg.", ".gggg", ".ggg."],
        b=["..m..", ".ggg.", "gggg.", ".gggg", ".ggg."], ey=1, my=2, mc="k"),
    dict(  # candy land: a gumdrop
        a=[".yyy.", "yyyyy", "yyyyy", "yyyyy", "wwwww"],
        b=[".yyy.", "yyyyy", "yyyyy", "yyyyy", "wowow"], ey=1, my=2, mc="k"),
    dict(  # ocean floor: a jellyfish
        a=[".mmm.", "mmmmm", "mmmmm", "m.m.m", ".m.m."],
        b=[".mmm.", "mmmmm", "mmmmm", ".m.m.", "m.m.m"], ey=1, my=2, mc="k"),
    dict(  # deep space: a little green alien
        a=[".g.g.", "ggggg", "ggggg", ".ggg.", ".g.g."],
        b=["g...g", "ggggg", "ggggg", ".ggg.", "g...g"], ey=1, my=2, mc="k"),
]


def crit_face(rows, ey, my, mood, mc):
    """One critter picture: the body with its eyes and mouth drawn for a mood."""
    g = [list(r) for r in rows]
    for c in (1, 3):
        if mood != "blink":
            g[ey][c] = "k"
        if mood == "sad" and ey + 1 < 5 and g[ey + 1][c] != ".":
            g[ey + 1][c] = "b"                      # a tear
    if mood == "cheer":
        for c in (1, 2, 3):
            g[my][c] = mc                           # a wide grin
    elif mc != "k":
        g[my][2] = mc                               # only a beak shows when calm: eyes over a lone dot read as an X
    return art(["".join(r) for r in g])


@lru_cache(maxsize=None)
def critter_set(ti):
    """{calm: eight poses (sway, one blink), cheer: two poses, sad: one} for a world's critter."""
    c = CRITTERS[ti]
    a, b, ey, my, mc = c["a"], c["b"], c["ey"], c["my"], c["mc"]
    calm_a, calm_b = crit_face(a, ey, my, "calm", mc), crit_face(b, ey, my, "calm", mc)
    return dict(calm=[calm_a, calm_b, calm_a, calm_b, calm_a, calm_b, calm_a, crit_face(a, ey, my, "blink", mc)],
                cheer=[crit_face(a, ey, my, "cheer", mc), crit_face(b, ey, my, "cheer", mc)],
                sad=[crit_face(a, ey, my, "sad", mc)])


# ----------------------------------------------------------------------------------------------
# The eight worlds. Each: floor squares (3 looks, mostly plain), wall squares (3 looks), the solid's colours and
# surface (tex), the hole's colours, the frame round the board, the critter and the colours of the twinkles.

def dotted(tile_, pts):
    """A copy of a wall tile with a few pixels (x, y, colour letter) changed: the quiet variety in a brick wall."""
    t = tile_.copy()
    for x, y, c in pts:
        t[y, x] = GLYPH[c]
    return t


def wall_set(fill, seam, hi, dots_a, dots_b):
    """Three plain brick tiles plus two with a few specks, so a long wall never repeats one pattern."""
    base = bricks(fill, seam, hi)
    return base + [dotted(base[0], dots_a), dotted(base[1], dots_b)]


THEMES = [
    dict(  # 0 meadow: green lawn with flowers; the wall is a ploughed field of crop rows
        plain="g",
        floor=[tile(["ggrgg", "grygr", "ggrgg", "ggggg", "ggggg"]),
               tile(["ggggg", "gwggg", "ggggg", "gggbg", "ggggg"]),
               tile(["ggggg", "grwrg", "gggwg", "ggggg", "ggggg"]),
               tile(["ggggg", "ggggg", "gwwgg", "gggwg", "ggggg"]),
               tile(["ggggg", "gggyg", "ggyoy", "gggyg", "ggggg"])],
        wall=[tile(["nnnnn", "ooooo", "nnnnn", "ooooo", "nnnnn"]),
              tile(["nnnnn", "oogoo", "nnnnn", "ogooo", "nnnnn"]),
              tile(["nnnnn", "oyoyo", "nnnnn", "oyoyo", "nnnnn"]),
              tile(["nnnnn", "ooooo", "nnrnn", "ooooo", "nnnnn"])],
        block=dict(base=ORG, light=YEL, dark=MAR, pip=WHT, tex="plank"),
        pit=dict(base=BLU, glint=LBL),
        frame=(GRN, YEL, WHT, RED), twinkle=(YEL, WHT, RED, MAG),
        motif=([".r.", "ryr", ".r."], [".w.", "wyw", ".w."])),
    dict(  # 1 snowfield: snow with flakes and a sapling; snow-brick walls
        plain="l",
        floor=[tile(["lllll", "llwll", "lwwwl", "llwll", "lllll"]),
               tile(["lllll", "llbbl", "lllbl", "lllll", "lllll"]),
               tile(["lllll", "lllll", "lwwll", "wwwwl", "lllll"]),
               tile(["lllll", "lllll", "lllwl", "lllll", "wllll"]),
               tile(["lllll", "llgll", "lgggl", "llwll", "lllll"])],
        wall=wall_set("w", "l", "b", [(1, 0, "b"), (3, 3, "b")], [(2, 1, "l"), (0, 4, "b")]),
        block=dict(base=MAG, light=WHT, dark=MAR, pip=WHT, tex="ice"),
        pit=dict(base=BLU, glint=LBL),
        frame=(BLU, WHT, LBL, WHT), twinkle=(WHT, LBL, YEL, WHT),
        motif=(["w.w", ".w.", "w.w"], [".w.", "www", ".w."])),
    dict(  # 2 lava cave: cracked stone floor with crystals; ember-flecked walls
        plain="n",
        floor=[tile(["nnnnn", "nnknn", "nkknn", "nnnkn", "nnnnn"]),
               tile(["nnnnn", "nrrnn", "nnnnn", "nnnrr", "nnnnn"]),
               tile(["nnnnn", "nnnnn", "nnonn", "nnnnn", "nrnnn"]),
               tile(["nnnnn", "nnnnn", "nyynn", "nnynn", "nnnnn"]),
               tile(["nnnnn", "nnlnn", "nlbbn", "nnbnn", "nnnnn"])],
        wall=wall_set("k", "n", "r", [(2, 1, "r"), (1, 3, "o")], [(3, 0, "n"), (2, 4, "r")]),
        block=dict(base=LBL, light=WHT, dark=BLU, pip=BLK, tex="ice"),
        pit=dict(base=ORG, glint=YEL),
        frame=(BLK, ORG, RED, YEL), twinkle=(ORG, YEL, RED, ORG),
        motif=([".y.", "yoy", ".r."], ["y..", "oyo", ".r."])),
    dict(  # 3 toy workshop: plank floor with toys dropped on it; red toy-box walls (unchanged)
        plain=None,
        floor=[tile(["oyyyy", "oyyyy", "oyyyy", "oyyyy", "ooooo"]),
               tile(["yyyoy", "yyyoy", "yyyoy", "yyyoy", "ooooo"]),
               tile(["yyyyy", "yoyyy", "yyyyy", "yyyoy", "ooooo"]),
               tile(["oyyyy", "oybyy", "oyyyy", "oyyyy", "ooooo"]),
               tile(["yyyoy", "yyyoy", "yygoy", "yyyoy", "ooooo"])],
        wall=[tile(["rrrrr", "rwrwr", "rrrrr", "rwrwr", "rnnnn"]),
              tile(["rrrrr", "rwrwr", "rrrrr", "rwrwr", "nnnnr"]),
              tile(["rrrrr", "rwrwr", "rrrrr", "rwrrr", "rnnnn"])],
        block=dict(base=GRN, light=WHT, dark=MAR, pip=WHT, tex="plank"),
        pit=dict(base=BLU, glint=LBL),
        frame=(RED, WHT, YEL, BLU), twinkle=(YEL, GRN, LBL, MAG),
        motif=(["bbb", "bwb", "bbb"], ["ggg", "gyg", "ggg"])),
    dict(  # 4 desert: sand with a sprout, a bone and footprints; sandstone walls
        plain="o",
        floor=[tile(["ooooo", "oyooo", "ooooo", "oooyo", "ooooo"]),
               tile(["ooooo", "oyyoo", "ooooo", "ooooo", "ooonn"]),
               tile(["ooooo", "ooooo", "nooyo", "ooooo", "oyooo"]),
               tile(["ooooo", "oogoo", "ooggg", "oogoo", "ooooo"]),
               tile(["ooooo", "owwwo", "ooooo", "ooooo", "oonoo"])],
        wall=wall_set("y", "n", "o", [(2, 1, "o"), (3, 3, "o")], [(1, 0, "n"), (4, 4, "o")]),
        block=dict(base=BLU, light=LBL, dark=BLK, pip=WHT, tex="rock"),
        pit=dict(base=MAR, glint=RED),
        frame=(MAR, ORG, YEL, RED), twinkle=(YEL, ORG, WHT, RED),
        motif=([".y.", "yoy", ".y."], ["o.o", ".y.", "o.o"])),
    dict(  # 5 candy land: sprinkled icing floor, striped candy walls (unchanged)
        plain="w",
        floor=[tile(["wwwww", "wpwww", "wwwwy", "wwwww", "wgwww"]),
               tile(["wwwww", "wwbww", "wwwww", "pwwww", "wwwyw"]),
               tile(["wwwww", "wywww", "wwwpw", "wwwww", "wwgww"]),
               tile(["wwwww", "wrrww", "wwwww", "wwwbw", "wwwww"]),
               tile(["wwwww", "wwwww", "wgwww", "wwwwp", "wywww"])],
        wall=[tile(["rrwwr", "rwwrr", "wwrrw", "wrrww", "rrwwr"]),
              tile(["wrrww", "rrwwr", "rwwrr", "wwrrw", "wrrww"]),
              tile(["rwwrr", "wwrrw", "wrrww", "rrwwr", "rwwrr"])],
        block=dict(base=GRN, light=YEL, dark=MAR, pip=WHT, tex="stud"),
        pit=dict(base=MAR, glint=ORG),
        frame=(MAG, WHT, YEL, GRN), twinkle=(WHT, YEL, GRN, LBL),
        motif=(["rwr", "wrw", "rwr"], ["gwg", "wgw", "gwg"])),
    dict(  # 6 ocean floor: blue water with shells, weed and bubbles; reef walls
        plain="b",
        floor=[tile(["bbbbb", "blbbb", "bbbbb", "bbblb", "bbbbb"]),
               tile(["bbbbb", "bbbbb", "bllbb", "bbbbb", "bbbbl"]),
               tile(["bbbbb", "bwbbb", "bbbbb", "bbbwb", "bbbbb"]),
               tile(["bbbbb", "bbgbb", "bggbb", "bbgbg", "bbbgb"]),
               tile(["bbbbb", "bbbbb", "bbpbb", "bpwpb", "bbbbb"])],
        wall=wall_set("n", "k", "m", [(1, 1, "m"), (3, 3, "p")], [(2, 0, "g"), (0, 4, "m")]),
        block=dict(base=ORG, light=YEL, dark=MAR, pip=WHT, tex="stud"),
        pit=dict(base=BLK, glint=BLU),
        frame=(BLK, LBL, BLU, WHT), twinkle=(LBL, WHT, BLU, YEL),
        motif=([".l.", "l.l", ".l."], ["w.w", ".o.", ".o."])),
    dict(  # 7 deep space: stars and a tiny planet; star-flecked hull walls
        plain="k",
        floor=[tile(["kkkkk", "kkkkk", "kkwkk", "kkkkk", "kbkkk"]),
               tile(["kkkkk", "kykkk", "kkkkk", "kkkkl", "kkkkk"]),
               tile(["kkkkk", "kkkkk", "lkkkk", "kkkwk", "kkkkk"]),
               tile(["kkkkk", "kkwkk", "kwwwk", "kkwkk", "kkkkk"]),
               tile(["kkkkk", "kmmkk", "kmmmk", "kkkkk", "kkkkk"])],
        wall=wall_set("n", "k", "y", [(1, 1, "y"), (3, 3, "w")], [(2, 0, "l"), (4, 4, "y")]),
        block=dict(base=YEL, light=WHT, dark=ORG, pip=BLK, tex="stud"),
        pit=dict(base=BLU, glint=LBL),
        frame=(BLU, WHT, YEL, LBL), twinkle=(WHT, YEL, LBL, WHT),
        motif=([".y.", "yyy", ".y."], ["...", ".w.", "..."])),
]

# A solid's surface: pixels (x, y, which colour) added to the plain slab when it carries no pips.
TEX = {
    "plank": (((1, 2, "dark"), (2, 2, "dark"), (3, 1, "light")),
              ((2, 1, "dark"), (3, 1, "dark"), (1, 3, "light")),
              ((1, 1, "dark"), (2, 1, "dark"), (2, 3, "light"))),
    "ice": (((1, 1, "light"), (2, 2, "light"), (3, 3, "dark")),
            ((2, 1, "light"), (1, 2, "light"), (3, 2, "dark")),
            ((1, 3, "light"), (2, 2, "light"), (3, 1, "dark"))),
    "rock": (((2, 1, "dark"), (2, 2, "dark"), (3, 3, "dark")),
             ((1, 1, "dark"), (2, 2, "dark"), (2, 3, "dark")),
             ((3, 1, "dark"), (2, 2, "dark"), (1, 3, "dark"))),
    "stud": (((1, 1, "light"), (3, 3, "dark")),
             ((3, 1, "light"), (1, 3, "dark")),
             ((2, 2, "light"), (2, 2, "light"))),
}

# ----------------------------------------------------------------------------------------------
# Props drawn into a level's walls where the wall is big enough: L1 and L2 have a thick ring, L3-L8 have one-square
# strips, so their props are five rows tall (or five wide) and sit exactly on a strip. Still props are baked into the
# board's picture; the ones that move or change colour are ANIMS further down and are real sprites.

def swap_rows(rows, top):
    """A picture drawn as rows, with its first rows replaced (a flame that leans, a lamp that flashes)."""
    return art(list(top) + list(rows[len(top):]))


def where_colour(pic, old, new):
    return np.where(pic == old, new, pic).astype(np.int8)


COTTAGE = halo(art([
    "....rrr....",
    "...rrrrr...",
    "..rrrrrrr..",
    ".rrrrrrrrr.",
    "rrrrrrrrrrr",
    ".wwwwwwwww.",
    ".wllwwwnnw.",
    ".wllwwwnnw.",
    ".wwwwwwwww.",
]), BLK)
ROUND_TREE = halo(art([
    "..ggg..",
    ".ggrgg.",
    "ggggggg",
    "gggggrg",
    ".ggggg.",
    "...n...",
    "...n...",
]), BLK)
PINE = halo(art([
    "..g..",
    ".ggg.",
    "..g..",
    ".ggg.",
    "ggggg",
    "..n..",
]), BLU)
HAY = halo(art([".yyyyy.", "yoyyoyy", "yyyyyyo", "yoyyyyy", ".yyyyy."]), BLK)
SUNFLOWER = art(["..y..", ".yyy.", "ynnny", ".yyy.", "..g..", "g.g..", "gggg.", "..g.."])
SNOWMAN_ROWS = ["..kkk..", "..rrr..", ".wwwww.", ".wkwkw.", ".wwowww", "..rrr..", ".wwwww.", ".wwkww.", "wwwwwww",
                "wwwkwww", ".wwwww."]
SNOWMAN_BLINK = halo(art(SNOWMAN_ROWS[:3] + [".wwwww."] + SNOWMAN_ROWS[4:]), BLU)       # eyes shut
IGLOO = halo(art(["..lll..", ".lwwwl.", "lwwlwwl", "lwkkkwl", "lkkkkkl"]), BLK)
PRESENT = art(["..r..", ".r.r.", "bbwbb", "bbwbb", "bbwbb"])
ORE = art(["...l.....", "..lbl.l..", ".lbwbllb.", ".lbbblbbl", "kkkkkkkkk"])
CRYSTAL = art(["..l..", ".lbl.", "lbwbl", "lbbbl", ".kkk."])
SKULL = art([".www.", "wkwkw", ".www.", ".wkw."])
TORCH_ROWS = ["..y..", ".yoy.", ".ooo.", ".krk.", ".kkk.", "..k..", "..k..", "..k..", "..k.."]
STACK = art(["...rwr...", "..bwbwb..", ".yyyyyyy.", "gwggggwgg", "kkkkkkkkk"])
CRAYON = art(["..r..", ".rrr.", ".bbb.", ".bwb.", ".bbb.", ".bwb.", ".bbb.", ".kkk.", ".kkk."])
TEDDY = art(["oo.oo", "ooooo", "okoko", "oonoo", ".ooo."])
BALL = art([".bbb.", "bwbbb", "bbbbb", "bbbbn", ".bbb."])
TOTEM_ROWS = [".yyy.", "ykyky", "yyoyy", "ykkky", "ooooo", ".rrr.", "rkrkr", "rrorr", "rkkkr"]
PYRAMID = art(["....o....", "...ooo...", "..ooooo..", ".oookooo.", "ooookoooo"])
CACTUS_ROWS = ["..r..", "g.g.g", "ggggg", "..g..", "..g.."]
DESERT_SKULL = art(["w...w", "wwwww", "wkwkw", ".www.", ".w.w."])
PALM = art([".g.g.", "ggggg", ".ggg.", "..n..", "..n..", "..n..", "..n..", "..n.."])
CUPCAKE = art(["..kyk..", ".kmmmk.", "kmkmkmk", "koorook", ".kkkkk."])      # a face: eyes in the icing, a mouth in the case
GUMDROP = art([".ggg.", "gkgkg", "ggrgg", "ggggg", "wwwww"])
LOLLIPOP = art([".ggg.", "gywyg", "ywgwy", "gywyg", ".ggg.", "..k..", "..k..", "..k..", "..k.."])
WRECK = art(["....k......", "...kwwk....", "..kwwwwk...", "kookoookook", ".kkkkkkkkk."])   # two eyes in the hull
CHEST = art([".kkkkk.", "koooook", "kkkykkk", "koooook", ".kkkkk."])
CORAL = art(["m.m.m", "mmmmm", ".mmm.", "..m..", "..m.."])
STARFISH = art(["..o..", ".ooo.", "ooooo", ".o.o.", "o...o"])
SEAWEED_A = art(["..g..", ".g...", "..g..", "...g.", "..g..", ".g...", "..g..", "...g.", "..g.."])
LIGHT_ROWS = ["..y..", ".lyl.", ".www.", ".rrr.", ".www.", ".rrr.", ".www.", "rrrrr", "kkkkk"]
SATELLITE = art(["lbbb.k.bbbl", "bwbb.y.bbwb", "bbbbkykbbbb", "bwbb.y.bbwb", "lbbb.k.bbbl"])
UFO = art(["...lll...", "..lwwwl..", "ggggggggg", ".gyygyyg.", "..y...y.."])
ROCKET = art(["..r..", ".rrr.", ".www.", ".wlw.", ".wbw.", ".www.", ".rwr.", "rwwwr", "r.y.r", "..o.."])
PLANET = art([".ooo.", "ooyoo", "wwwww", "oyooo", ".ooo."])
ASTRO = art([".www.", "wkwkw", "wwrww", ".www.", "wlwlw", ".w.w."])

# Each entry is (picture, x, y) in board pixels (0..54). Only drawn where every pixel lands on a wall square.
PROPS = {
    0: [(COTTAGE, 22, 42), (PINE, 5, 44), (PINE, 44, 44), (HAY, 13, 46), (SUNFLOWER, 37, 46), (SUNFLOWER, 3, 18),
        (HAY, 45, 32)],
    1: [(PINE, 3, 43), (PINE, 10, 47), (PINE, 36, 44), (IGLOO, 44, 46), (PRESENT, 18, 48)],
    2: [(ORE, 6, 0), (ORE, 27, 0), (ORE, 44, 0), (ORE, 12, 50), (ORE, 34, 50),
        (CRYSTAL, 17, 0), (CRYSTAL, 37, 0), (CRYSTAL, 2, 50), (CRYSTAL, 24, 50), (CRYSTAL, 46, 50),
        (SKULL, 0, 24), (SKULL, 50, 24)],
    3: [(STACK, 6, 0), (STACK, 27, 0), (STACK, 43, 0), (STACK, 12, 50), (STACK, 35, 50),
        (CRAYON, 0, 12), (CRAYON, 0, 33), (CRAYON, 50, 12), (CRAYON, 50, 33),
        (TEDDY, 0, 3), (TEDDY, 50, 3), (BALL, 0, 23), (BALL, 50, 23)],
    4: [(PYRAMID, 8, 0), (PYRAMID, 40, 0), (PYRAMID, 22, 50), (DESERT_SKULL, 33, 0),
        (PALM, 25, 16), (PALM, 25, 30)],
    5: [(CUPCAKE, 3, 25), (CUPCAKE, 17, 25), (CUPCAKE, 31, 25), (CUPCAKE, 45, 25),
        (GUMDROP, 11, 25), (GUMDROP, 25, 25), (GUMDROP, 39, 25)],
    6: [(WRECK, 4, 25), (CHEST, 24, 25), (WRECK, 40, 25), (CORAL, 17, 25), (STARFISH, 33, 25)],
    7: [(ROCKET, 25, 5), (ROCKET, 25, 38), (PLANET, 17, 25), (PLANET, 35, 25)],
}

# ----------------------------------------------------------------------------------------------
# Things that live: named sprites over the walls that sway, blink, flicker, drift or change colour, and mean nothing.
# Two kinds. "stay": sits on a spot and cycles its poses (a torch, a tree that ripens). "x"/"y": drifts along a lane
# (a rectangle that must lie wholly on wall, checked when the level is built) and wraps; bob wobbles it sideways.
# Poses are tinted pictures; every = frames per pose.

def tinted(pic, colour):
    """A picture drawn with the chip colour c, set to one real colour."""
    return np.where(pic == 100, colour, pic).astype(np.int8)


BFLY = [art(["c.k.c", "cckcc", ".c.c."]), art(["..k..", ".ckc.", "..c.."])]
BAT = [art(["r...r", "rryrr", ".rrr."]), art([".rrr.", "rryrr", "r...r"])]
EMBER = [art(["y", "y"]), art(["o", "o"]), art(["r", "o"])]
FLAKE = [art([".c.", "ccc", ".c."]), art(["c.c", ".c.", "c.c"])]
BUBBLE = [art([".c.", "c.c", ".c."]), art(["...", ".c.", "..."])]
FISH = [art(["c.cc..", "ccccwc", "..cc.."]), art(["..cc..", "ccccwc", "c.cc.."])]
SCARAB = [art(["k.c.k", "ccccc", ".k.k."]), art([".kck.", "ccccc", "k...k"])]
COG = [art([".c.", "cwc", ".c."]), art(["c.c", ".w.", "c.c"])]
BONBON = halo(art(["ccc", "cwc", "ccc"]), BLK)
COMET = [art(["..l..", "bllww", "..l.."]), art(["l....", "bllww", "l...."])]
BALLOON = art([".c.", "ccc", "ccc", ".c.", ".k."])
SPRINKLE = art(["c", "c"])
GLEAM = [art([".w.", "www", ".w."]), np.full((3, 3), -1, dtype=np.int8)]
BLANK3 = GLEAM[1]
GLEAMS = [GLEAM[0]] + [BLANK3] * 4          # a glint now and then


def torch_poses():
    return [art(TORCH_ROWS), swap_rows(TORCH_ROWS, ["...y.", ".yoy.", ".ooo."]), swap_rows(TORCH_ROWS, [".y...", ".yoy.", ".ooo."])]


def lamp_poses():
    return [art(LIGHT_ROWS), swap_rows(LIGHT_ROWS, ["yyyyy", "yyyyy"])]


def at(poses, x, y, every=3, off=0, bob=0):
    """A prop that stays put."""
    return dict(poses=poses, kind="stay", a=x, b=x, c=y, speed=0, off=off, bob=bob, every=every)


def lane(poses, axis, a, b, c, speed, off=0, bob=1, every=2):
    """A drifter on a straight lane: from a to b along the axis, c fixed on the other. Negative speed goes back."""
    return dict(poses=poses, kind=axis, a=a, b=b, c=c, speed=speed, off=off, bob=bob, every=every)


def rev(poses):
    return [np.fliplr(p).copy() for p in poses]


ANIMS = {
    0: [at([ROUND_TREE, where_colour(ROUND_TREE, RED, YEL)], 1, 9, every=9),
        at([ROUND_TREE, where_colour(ROUND_TREE, RED, YEL)], 46, 22, every=9, off=1),
        at([ROUND_TREE, where_colour(ROUND_TREE, RED, YEL)], 1, 26, every=9, off=2),
        at([ROUND_TREE, where_colour(ROUND_TREE, RED, YEL)], 45, 8, every=9, off=3),
        lane([tinted(p, YEL) for p in BFLY], "x", 0, 49, 1, 1.5, every=2),
        lane([tinted(p, MAG) for p in BFLY], "y", 6, 34, 3, 1.0, off=5, bob=1),
        lane([tinted(p, ORG) for p in BFLY], "y", 6, 34, 48, -0.8, off=9, bob=1)],
    1: [at([halo(art(SNOWMAN_ROWS), BLU)] * 6 + [SNOWMAN_BLINK], 24, 40, every=3),
        lane([tinted(p, BLU) for p in FLAKE], "y", 1, 36, 1, 1.0, off=0, bob=1, every=4),
        lane([tinted(p, BLU) for p in FLAKE], "y", 1, 36, 1, 1.0, off=18, bob=1, every=4),
        lane([tinted(p, BLU) for p in FLAKE], "y", 1, 36, 51, 0.8, off=7, bob=1, every=4),
        lane([tinted(p, BLU) for p in FLAKE], "y", 1, 36, 51, 0.8, off=25, bob=1, every=4)],
    2: [at(torch_poses(), 0, 12, every=2), at(torch_poses(), 0, 33, every=2, off=1),
        at(torch_poses(), 50, 12, every=2, off=2), at(torch_poses(), 50, 33, every=2, off=3),
        at(GLEAMS, 9, 1, every=3), at(GLEAMS, 30, 1, every=3, off=1),
        at(GLEAMS, 47, 1, every=3, off=2), at(GLEAMS, 15, 51, every=3, off=3),
        at(GLEAMS, 37, 51, every=3, off=1),
        lane(BAT, "x", 0, 49, 1, 1.2, every=2), lane(rev(BAT), "x", 0, 49, 51, -1.0, off=20, every=2),
        lane(EMBER, "y", 3, 48, 2, -0.7, off=0, bob=2, every=2),
        lane(EMBER, "y", 3, 48, 52, -0.9, off=13, bob=2, every=2)],
    3: [at([tinted(p, YEL) for p in COG], 19, 1, every=2), at([tinted(p, LBL) for p in COG], 38, 1, every=2, off=1),
        at([tinted(p, YEL) for p in COG], 26, 51, every=2), at([tinted(p, LBL) for p in COG], 4, 51, every=2),
        at([tinted(p, YEL) for p in COG], 47, 51, every=2, off=1),
        at([tinted(BALLOON, c) for c in (MAG, RED, BLU)], 1, 29, every=7, bob=2),
        at([tinted(BALLOON, c) for c in (YEL, GRN, LBL)], 51, 29, every=7, off=1, bob=2)],
    4: [at([art(TOTEM_ROWS)] * 5 + [swap_rows(TOTEM_ROWS, [".yyy.", "yyyyy"])], 25, 5, every=4),
        at([art(TOTEM_ROWS)] * 5 + [swap_rows(TOTEM_ROWS, [".yyy.", "yyyyy"])], 25, 40, every=4, off=3),
        at([art(CACTUS_ROWS), swap_rows(CACTUS_ROWS, ["..y.."])], 19, 0, every=6),
        at([art(CACTUS_ROWS), swap_rows(CACTUS_ROWS, ["..y.."])], 26, 0, every=6, off=1),
        at([art(CACTUS_ROWS), swap_rows(CACTUS_ROWS, ["..y.."])], 4, 50, every=6, off=2),
        at([art(CACTUS_ROWS), swap_rows(CACTUS_ROWS, ["..y.."])], 12, 50, every=6, off=3),
        at([art(CACTUS_ROWS), swap_rows(CACTUS_ROWS, ["..y.."])], 36, 50, every=6, off=4),
        at([art(CACTUS_ROWS), swap_rows(CACTUS_ROWS, ["..y.."])], 46, 50, every=6, off=5),
        lane(SCARAB, "x", 0, 49, 51, 0.8, every=2)],
    5: [at([LOLLIPOP, np.fliplr(LOLLIPOP).copy()], 25, 8, every=4), at([LOLLIPOP, np.fliplr(LOLLIPOP).copy()], 0, 31, every=4, off=1),
        at([LOLLIPOP, np.fliplr(LOLLIPOP).copy()], 50, 31, every=4, off=1),
        at([LOLLIPOP, np.fliplr(LOLLIPOP).copy()], 0, 42, every=4), at([LOLLIPOP, np.fliplr(LOLLIPOP).copy()], 50, 42, every=4),
        lane([tinted(BONBON, c) for c in (BLU, YEL, GRN, LBL, MAG, ORG)], "x", 0, 50, 25, 2.0, every=1, bob=0),
        lane([tinted(SPRINKLE, c) for c in (YEL, GRN, BLU, MAG)], "y", 31, 52, 2, 1.3, every=3, bob=1),
        lane([tinted(SPRINKLE, c) for c in (MAG, BLU, YEL, GRN)], "y", 31, 52, 52, 1.1, off=9, every=3, bob=1),
        lane([tinted(SPRINKLE, c) for c in (GRN, YEL, MAG, BLU)], "y", 2, 22, 27, 1.2, off=4, every=3, bob=1)],
    6: [lane([tinted(p, ORG) for p in FISH], "x", 0, 48, 26, 1.0, every=3, bob=1),
        lane(rev([tinted(p, YEL) for p in FISH]), "x", 0, 48, 26, -1.3, off=22, every=3, bob=1),
        at(lamp_poses(), 25, 4, every=5),
        at([SEAWEED_A, np.fliplr(SEAWEED_A).copy()], 25, 14, every=5),
        at([SEAWEED_A, np.fliplr(SEAWEED_A).copy()], 0, 31, every=5, off=1),
        at([SEAWEED_A, np.fliplr(SEAWEED_A).copy()], 50, 31, every=5),
        lane([tinted(p, LBL) for p in BUBBLE], "y", 1, 26, 26, -0.7, off=0, bob=1, every=3),
        lane([tinted(p, WHT) for p in BUBBLE], "y", 1, 26, 26, -0.5, off=30, bob=1, every=3),
        lane([tinted(p, LBL) for p in BUBBLE], "y", 31, 50, 1, -0.6, off=4, bob=1, every=3),
        lane([tinted(p, WHT) for p in BUBBLE], "y", 31, 50, 51, -0.5, off=11, bob=1, every=3)],
    7: [at([SATELLITE, where_colour(SATELLITE, YEL, RED)], 4, 25, every=6), at([SATELLITE, where_colour(SATELLITE, YEL, RED)], 40, 25, every=6, off=1),
        at([UFO, where_colour(UFO, YEL, RED)], 23, 25, every=4),
        at([ASTRO], 25, 17, every=5, bob=1), at([ASTRO], 25, 30, every=5, off=2, bob=1),
        lane(COMET, "x", 0, 50, 26, 2.5, every=2, bob=0)],
}


def covered(wall, x, y, w, h):
    """True when every pixel of a w x h picture at x, y (board pixels) lies on a wall square."""
    for j in range(0, h):
        for i in range(0, w):
            px, py = x + i, y + j
            if not (0 <= px < N * CELL and 0 <= py < N * CELL and wall[py // CELL][px // CELL]):
                return False
    return True


@lru_cache(maxsize=None)
def ambient_for(ti):
    """The level's living sprites that fit: a lane or a spot is dropped unless it lies wholly on wall squares."""
    field = heights(LEVELS_SPEC[ti]["rows"])
    wall = [[field[y][x] >= WALL for x in range(N)] for y in range(N)]
    out = []
    for a in ANIMS.get(ti, ()):
        w = max(p.shape[1] for p in a["poses"])
        h = max(p.shape[0] for p in a["poses"])
        if a["kind"] == "stay":
            rect = (a["a"], a["c"], w, h + a["bob"])
        elif a["kind"] == "x":
            rect = (a["a"], a["c"], a["b"] - a["a"] + w, h + a["bob"])
        else:
            rect = (a["c"], a["a"], w + a["bob"], a["b"] - a["a"] + h)
        if covered(wall, *rect):
            out.append(a)
        else:
            AMB_DROPPED.append((ti, a["kind"], rect))
    return out


AMB_DROPPED = []


def amb_xy(a, t):
    """Where a living sprite is at time t, in board pixels."""
    length = a["b"] - a["a"]
    p = int((t * a["speed"] + a["off"]) % length) if length > 0 else 0
    wob = (0, 1, 1, 0)[(t // 2 + a["off"]) % 4] * a["bob"]
    if a["kind"] == "stay":
        return a["a"], a["c"] + wob
    if a["kind"] == "x":
        return a["a"] + p, a["c"] + wob
    return a["c"] + wob, a["a"] + p

# ----------------------------------------------------------------------------------------------
# The sun on the board's edge: a 15x4 half disc with a face. Drawn for the top edge (row 0 is the screen's edge);
# the other three edges are the same picture turned. Eyes are two pixels wide so the face reads at this size.

SUN_FACES = {
    "happy": ("ooyyyyyyyyyyyoo", ".oyykkyyykkyyo.", "..orykyyykyro..", "...yyykkkyyy..."),
    "blink": ("ooyyyyyyyyyyyoo", ".oyyooyyyooyyo.", "..orykyyykyro..", "...yyykkkyyy..."),
    "wince": ("ooyykkyyykkyyoo", ".oyykkyyykkyyo.", "..oryyyyyyyro..", "...yyyykyyyy..."),
    "cheer": ("ooyyyyyyyyyyyoo", ".oyykkyyykkyyo.", "..orykkkkkyro..", "...yyyrrryyy..."),
    "sad":   ("ooyyyoyyyoyyyoo", ".oyykkyyykkyyo.", "..oybyyyyybyo..", "...yyykkkyyy..."),
}
# the outline pixels that twinkle between orange and red (row, column)
SUN_GLOW = ((0, 0), (0, 1), (0, 13), (0, 14), (1, 1), (1, 13), (2, 2), (2, 12))
for _k, _v in SUN_FACES.items():
    assert len(_v) == 4 and all(len(r) == 15 for r in _v), _k


@lru_cache(maxsize=None)
def sun_picture(edge, face, ray):
    """The sun for one edge (0 top, 1 right, 2 bottom, 3 left), one face, one corona flicker."""
    top = art(SUN_FACES[face])
    for n, (j, i) in enumerate(SUN_GLOW):
        if top[j, i] >= 0:
            top[j, i] = RED if (n + ray) % 2 else ORG
    if edge == 0:
        return top
    if edge == 2:
        return np.flipud(top).copy()
    if edge == 3:
        return np.rot90(top, 1).copy()
    return np.rot90(top, -1).copy()


def sun_xy(edge, hidden):
    """Where the sun sits; hidden slides it that many pixels off the screen."""
    if edge == 0:
        return 25, -hidden
    if edge == 1:
        return 60 + hidden, 25
    if edge == 2:
        return 25, 60 + hidden
    return -hidden, 25


# ----------------------------------------------------------------------------------------------
# Tiles: every board square's look, cached so a swap is a pointer change.

def fill5(colour):
    return np.full((CELL, CELL), colour, dtype=np.int8)


@lru_cache(maxsize=None)
def block_tile(ti, top, bot, left, right, pips, var):
    """A solid's square. Lit on its exposed top and left, shaded on its exposed bottom and right, so a
    block reads as raised; joined squares of one solid blend into one slab. Only the anchor square
    carries the pips (the height); the others carry the world's surface (planks, ice facets, rock, studs)."""
    b = THEMES[ti]["block"]
    t = fill5(b["base"])
    if pips == 0:
        for x, y, which in TEX[b["tex"]][var % 3]:
            t[y, x] = b[which]
    if top:
        t[0, :] = b["light"]
    if left:
        t[:, 0] = b["light"]
    if bot:
        t[3, :] = b["dark"]
        t[4, :] = C_INK
    if right:
        t[:, 3] = b["dark"]
        t[:, 4] = C_INK
    if top and not left:
        t[0, 0] = b["light"]
    for dx, dy in DICE.get(pips, ()):
        t[dy, dx] = b["pip"]
    return t


SAGGED = {}


def sagged(ti, pic, k):
    """A block slumping on a lost run: sunk k rows, tinted red, and the top rows left empty (cached by picture)."""
    key = (id(pic), k)
    if key not in SAGGED:
        b = THEMES[ti]["block"]
        tint = {b["base"]: RED, b["light"]: ORG, b["dark"]: MAR, b["pip"]: WHT, C_INK: C_INK}
        out = np.full((CELL, CELL), -1, dtype=np.int8)
        for j in range(CELL - k):
            for i in range(CELL):
                out[j + k, i] = tint.get(int(pic[j, i]), RED)
        out[CELL - 1, :] = C_INK          # the slumped block rests on the ground
        SAGGED[key] = out
    return SAGGED[key]


@lru_cache(maxsize=None)
def pit_tile(ti, top, left, depth, mode, glint):
    """A hole's square. mode 0 plain, 1 shadow will fill it (all purple), 2 a refused shadow falls on it
    (chequered). glint is a position index for the little sparkle on the water/lava, or -1."""
    p = THEMES[ti]["pit"]
    t = fill5(SHADOW if mode == 1 else p["base"])
    if mode == 2:
        t[0::2, 0::2] = SHADOW
    if top:
        t[0, :] = C_INK
    if left:
        t[:, 0] = C_INK
    if mode == 0 and glint >= 0:
        gx, gy = ((4, 1), (2, 4), (4, 3), (3, 4))[glint % 4]
        t[gy, gx] = p["glint"]
    for dx, dy in DICE.get(depth, ()):
        t[dy, dx] = WHT
    return t


@lru_cache(maxsize=None)
def refused_floor_tile():
    """Plain floor under a refused shadow: only the chequer dots, so the floor shows between them."""
    t = np.full((CELL, CELL), -1, dtype=np.int8)
    t[0::2, 0::2] = SHADOW
    return t


@lru_cache(maxsize=None)
def slab_tile(ti, front_edge):
    """A toppled solid lying flat (used by the topple sweep): lit top and left edges, shaded bottom and right,
    streaks of light across the face so it reads as a slab skidding along."""
    b = THEMES[ti]["block"]
    t = fill5(b["base"])
    t[1, 1:4] = b["light"]
    t[3, 2:5] = b["dark"]
    t[0, :] = b["light"]
    t[:, 0] = b["light"]
    t[4, :] = b["dark"]
    t[:, 4] = b["dark"]
    return t


# ----------------------------------------------------------------------------------------------
# Level scenery: the frame round the board and the static ground (floor, walls, props).

def frame_pixels(ti):
    """64x64 backdrop: a coloured border with one calm row of beads, a corner stud at each corner, the world's emblems
    and an ink keyline round the board. The one-pixel row under the board is the fuse's track."""
    base, c1, c2, c3 = THEMES[ti]["frame"]
    f = np.full((64, 64), base, dtype=np.int8)
    for i in range(64):
        colour = c1 if i % 6 < 2 else c2 if 3 <= i % 6 < 5 else base
        for (x, y) in ((i, 1), (i, 62), (1, i), (62, i)):
            f[y, x] = colour
    for cx, cy in ((0, 0), (61, 0), (0, 61), (61, 61)):
        f[cy:cy + 3, cx:cx + 3] = c3
        f[cy + 1, cx + 1] = C_INK
    f[3, 3:60] = C_INK
    f[59, 3:60] = C_INK
    f[3:60, 3] = C_INK
    f[3:60, 59] = C_INK
    # the world's own little emblem every twelve pixels along each side, two kinds taking turns (flowers, flakes,
    # flames, toy blocks, ...). They sit in the three-pixel margin; the gem and the twinkles pass over them.
    motifs = [art(m) for m in THEMES[ti]["motif"]]
    for n, k in enumerate(range(6, 55, 12)):
        m = motifs[n % 2]
        for (x, y) in ((k, 0), (k, 61)):
            blit(f, x, y, m)
        for (x, y) in ((0, k), (61, k)):
            blit(f, x, y, m)
    return f


@lru_cache(maxsize=None)
def ground_for(ti):
    """55x55 floor + walls + props for one level (cached). Walls are ink-edged on the sides facing the play area."""
    th = THEMES[ti]
    field = heights(LEVELS_SPEC[ti]["rows"])
    g = np.zeros((N * CELL, N * CELL), dtype=np.int8)
    wall = [[field[y][x] >= WALL for x in range(N)] for y in range(N)]
    plain = None if th["plain"] is None else np.full((5, 5), GLYPH[th["plain"]], dtype=np.int8)
    for y in range(N):
        for x in range(N):
            v = hashed(x, y, ti)
            if wall[y][x]:
                t = th["wall"][v % 3].copy()
                open_ = lambda a, b: 0 <= a < N and 0 <= b < N and not wall[b][a]
                if open_(x, y - 1):
                    t[0, :] = C_INK
                if open_(x, y + 1):
                    t[4, :] = C_INK
                if open_(x - 1, y):
                    t[:, 0] = C_INK
                if open_(x + 1, y):
                    t[:, 4] = C_INK
            else:
                pick = v % 8          # three squares in eight are plain so the detailed ones read as detail, not noise
                t = plain if (plain is not None and pick < 3) else th["floor"][pick % len(th["floor"])]
            g[y * CELL:y * CELL + CELL, x * CELL:x * CELL + CELL] = t
    for picture, px, py in PROPS.get(ti, ()):
        # a prop is only drawn where every pixel of it lands on a wall square
        w, h = picture.shape[1], picture.shape[0]
        ok = all(wall[min(N - 1, (py + j) // CELL)][min(N - 1, (px + i) // CELL)]
                 for j in range(0, h, 2) for i in range(0, w, 2)
                 if 0 <= py + j < N * CELL and 0 <= px + i < N * CELL)
        if ok:
            blit(g, px, py, picture)
    return g


def wall_cells(ti):
    field = heights(LEVELS_SPEC[ti]["rows"])
    return [(x, y) for y in range(N) for x in range(N) if field[y][x] >= WALL]


def life_cells(ti):
    """Which wall squares carry a critter: a spread-out handful, the same every run."""
    cells = wall_cells(ti)
    want = 7
    picked = []
    for (x, y) in sorted(cells, key=lambda c: hashed(c[0], c[1], 7 + ti)):
        if all(abs(x - px) + abs(y - py) >= 3 for px, py in picked) and not prop_covers(ti, x, y):
            picked.append((x, y))
        if len(picked) == want:
            break
    return picked


def prop_covers(ti, x, y):
    """True when a prop was painted over this wall square (the critter would clash with it)."""
    spots = [(picture.shape[1], picture.shape[0], px, py) for picture, px, py in PROPS.get(ti, ())]
    spots += [(a["poses"][0].shape[1], a["poses"][0].shape[0] + a["bob"], a["a"], a["c"])
              for a in ambient_for(ti) if a["kind"] == "stay"]
    for w, h, px, py in spots:
        if px < (x + 1) * CELL and (x * CELL) < px + w and py < (y + 1) * CELL and (y * CELL) < py + h:
            return True
    return False


TWINKLES = ((10, 1), (18, 1), (42, 1), (50, 1), (1, 19), (62, 51), (1, 51), (62, 19))
RING = 4 * 61          # the gem's lap round the frame


def ring_xy(step):
    """Where the running gem's 3x3 sprite sits, `step` pixels along a lap round the frame's bead row."""
    p = step % RING
    if p < 61:
        cx, cy = 1 + p, 1
    elif p < 122:
        cx, cy = 62, 1 + (p - 61)
    elif p < 183:
        cx, cy = 62 - (p - 122), 62
    else:
        cx, cy = 1, 62 - (p - 183)
    return cx - 1, cy - 1


GEM = art([".w.", "www", ".w."])

# ----------------------------------------------------------------------------------------------
# Small effects

DUST_ART = [
    ["...c...", "..cwc..", "...c...", ".......", ".......", ".......", "......."],
    [".......", ".c.w.c.", "..www..", ".wwcww.", "..www..", ".c.w.c.", "......."],
    [".......", "c.w.w.c", ".wlllw.", "wlwcwlw", ".wlllw.", "c.w.w.c", "......."],
    ["c.....c", ".w...w.", "..l.l..", "...c...", "..l.l..", ".w...w.", "c.....c"],
]
for _f in DUST_ART:
    assert len(_f) == 7 and all(len(r) == 7 for r in _f)


@lru_cache(maxsize=None)
def dust_frames(ti):
    """The puff at the front of a sliding slab, four stages, its chips in the world's block colour."""
    base = THEMES[ti]["block"]["base"]
    out = []
    for f in DUST_ART:
        a = art(f)
        out.append(np.where(a == 100, base, a).astype(np.int8))
    return out


STARS = [
    art([".....", "..w..", ".www.", "..w..", "....."]),
    art(["..w..", "..w..", "wwwww", "..w..", "..w.."]),
    art(["w...w", ".w.w.", "..w..", ".w.w.", "w...w"]),
]
CHEER_COLOURS = (YEL, WHT, MAG, LBL, GRN, ORG)
CUE_RING = np.array([[BAD if max(abs(i - 2), abs(j - 2)) == 2 else -1 for i in range(5)] for j in range(5)],
                    dtype=np.int8)


@lru_cache(maxsize=None)
def haze(shift):
    """The red haze over a lost board: a thin chequer that swaps every few frames, and a red rim."""
    s = N * CELL
    a = np.array([[BAD if (i + 2 * j + shift) % 7 == 0 else -1 for i in range(s)] for j in range(s)], dtype=np.int8)
    a[0:2, :] = a[-2:, :] = a[:, 0:2] = a[:, -2:] = BAD
    return a


CONFETTI = 22
CONF = [np.full((3, 2), c, dtype=np.int8) for c in (YEL, WHT, MAG, LBL, GRN, ORG, RED, BLU)]
RAIN = 9
DROP = np.array([[LBL], [BLU], [BLU]], dtype=np.int8)


def storm_cloud():
    """The little rain cloud over a lost board: blue, lit on top, outlined, with two sad eyes and a frown."""
    w, h = 19, 8
    c = np.full((h, w), -1, dtype=np.int8)
    for j in range(h):
        for i in range(w):
            for cx, cy, r in ((4, 5, 3.2), (9, 3.5, 4.2), (14, 5, 3.6)):
                if (i - cx) ** 2 + (j - cy) ** 2 <= r * r:
                    c[j, i] = LBL if j < 3 else BLU
            if 3 <= i <= 15 and 4 <= j <= 7:
                c[j, i] = BLU
    c[7, :] = np.where(c[7, :] >= 0, PUR, -1)
    for i in (7, 11):
        c[4, i] = BLK
        c[5, i] = BLK
    c[5, 9] = BLK                  # the frown: ends low, middle high
    c[6, 8] = c[6, 10] = BLK
    return halo(c, BLK)


STORM = storm_cloud()
STORM_X = (64 - STORM.shape[1]) // 2


def outline_array(cells, colour):
    """A 55x55 see-through sheet with the outline of a group of squares drawn on it."""
    s = N * CELL
    a = np.full((s, s), -1, dtype=np.int8)
    cells = set(cells)
    for x, y in cells:
        px, py = x * CELL, y * CELL
        if (x, y - 1) not in cells:
            a[py, px:px + CELL] = colour
        if (x, y + 1) not in cells:
            a[py + CELL - 1, px:px + CELL] = colour
        if (x - 1, y) not in cells:
            a[py:py + CELL, px] = colour
        if (x + 1, y) not in cells:
            a[py:py + CELL, px + CELL - 1] = colour
    return a


# ═════════════════════════════════════════════════════════════════════════════════════════════
# PART 3 -- THE LEVEL SPRITES
# ═════════════════════════════════════════════════════════════════════════════════════════════

FREE = BlockingMode.NOT_BLOCKED
GHOST = InteractionMode.INTANGIBLE
BLANK5 = np.full((CELL, CELL), -1, dtype=np.int8)
SPAN = N * CELL


def make_sprite(pixels, name, x, y, layer, tags, visible=True):
    return Sprite(pixels=pixels, name=name, x=x, y=y, layer=layer, blocking=FREE, interaction=GHOST,
                  visible=visible, tags=tags)


def build_level(ti):
    field = heights(LEVELS_SPEC[ti]["rows"])
    sprites = [
        make_sprite(frame_pixels(ti), "frame", 0, 0, -3, ["scenery"]),
        # the click surface st01 had: every pixel of the board takes a click. Its picture is the ground.
        make_sprite(ground_for(ti).copy(), "board", INSET, INSET, -2, ["sys_click", "sys_every_pixel"]),
    ]
    for y in range(N):
        for x in range(N):
            if field[y][x] < WALL:
                sprites.append(make_sprite(BLANK5, f"cell-{x}-{y}", INSET + x * CELL, INSET + y * CELL, 0,
                                           ["cell"], visible=False))
    for k, (x, y) in enumerate(life_cells(ti)):
        sprites.append(make_sprite(critter_set(ti)["calm"][0], f"critter-{k}", INSET + x * CELL, INSET + y * CELL, 1,
                                   ["life", "critter"]))
    for k, (x, y) in enumerate(TWINKLES):
        sprites.append(make_sprite(np.full((1, 1), THEMES[ti]["twinkle"][k % 4], dtype=np.int8), f"twinkle-{k}",
                                   x, y, -1, ["life"]))
    sprites.append(make_sprite(GEM.copy(), "runner", *ring_xy(0), -1, ["life"]))
    for k, a in enumerate(ambient_for(ti)):
        x0, y0 = amb_xy(a, 0)
        sprites.append(make_sprite(a["poses"][0], f"amb-{k}", INSET + x0, INSET + y0, -1, ["life", "ambient"]))
    for d in range(4):
        sprites.append(make_sprite(sun_picture(d, "happy", 0), f"sun-{d}", *sun_xy(d, 0), 8, ["light"],
                                   visible=(d == LEVELS_SPEC[ti].get("sun0", 0))))
    sprites += [
        make_sprite(np.full((1, SPAN), -1, dtype=np.int8), "fuse", INSET, BAR_ROW, 6, ["counter"]),
        make_sprite(outline_array((), BAD), "cue", INSET, INSET, 5, ["cue"], visible=False),
        make_sprite(CUE_RING, "cue-ring", 0, 0, 5, ["cue"], visible=False),
        make_sprite(dust_frames(ti)[0], "dust", 0, 0, 4, ["effect"], visible=False),
        make_sprite(haze(0), "haze", INSET, INSET, 7, ["effect"], visible=False),
    ]
    for k in range(7):
        sprites.append(make_sprite(STARS[0], f"star-{k}", 0, 0, 9, ["effect"], visible=False))
    for k in range(CONFETTI):
        sprites.append(make_sprite(CONF[0], f"confetti-{k}", 0, 0, 9, ["effect"], visible=False))
    sprites.append(make_sprite(STORM, "storm", STORM_X, INSET + 1, 9, ["effect"], visible=False))
    for k in range(RAIN):
        sprites.append(make_sprite(DROP, f"rain-{k}", 0, 0, 9, ["effect"], visible=False))
    return Level(sprites=sprites, grid_size=(64, 64), name=f"world-{ti + 1}")


def build_levels() -> list[Level]:
    return [build_level(i) for i in range(len(LEVELS_SPEC))]


# ═════════════════════════════════════════════════════════════════════════════════════════════
# PART 4 -- THE GAME
# ═════════════════════════════════════════════════════════════════════════════════════════════

class St02(ARCBaseGame):

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
        self.lost = False
        self.beat = 0
        self.ti = 0
        self.sp = {}
        self.shown = {}
        self.cells = []
        self.lives = []
        self.shade_key = None
        self.shade = (set(), set(), set())
        self.amb = []
        self.amb_t = 0
        camera = Camera(width=64, height=64, background=C_INK, letter_box=C_INK)
        super().__init__(game_id="st02", levels=build_levels(), camera=camera, available_actions=[3, 4, 5, 6])

    def tick_index(self) -> int:
        return self.tick_total - self.tick

    # ---- level setup ------------------------------------------------------------------------

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
        self.lost = False
        self.beat = 0
        self.ti = self.level_index
        self.sp = {s.name: s for s in level.get_sprites()}
        self.shown = {}
        self.cells = [(x, y) for y in range(N) for x in range(N) if f"cell-{x}-{y}" in self.sp]
        self.lives = life_cells(self.ti)
        self.amb = ambient_for(self.ti)
        self.amb_t = 0
        self.shade_key = None
        self.paint()

    # ---- rules (st01's step, unchanged in what it decides) ---------------------------------

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
            self._begin("cheer", CHEER_FRAMES)     # the level-clear sparkle; the engine moves on when it ends
        else:
            self._settle()

    def _settle(self) -> None:
        """End of a move that did not win: an empty counter flashes the board, then the run is lost."""
        if self.moves_left <= 0:
            self._begin("die", DIE_FRAMES)
        else:
            self.complete_action()

    def step(self) -> None:
        self.beat += 1
        self.advance()
        self.paint()

    def advance(self) -> None:
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
                self.lost = True
                self.lose()
                self.complete_action()
            elif phase == "cheer":
                self.phase = None
                self.next_level()
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

    # ---- drawing: everything below only reads state and moves sprites ------------------------

    def put(self, name, pixels, x=None, y=None, visible=True):
        """Set a sprite's picture (only when it changed), position and visibility."""
        s = self.sp[name]
        if visible:
            if pixels is not None and self.shown.get(name) is not pixels:
                s.pixels = pixels
                self.shown[name] = pixels
            if x is not None:
                s.set_position(x, y)
        s.set_visible(visible)

    def shading(self):
        """Which squares a live shadow will fill (good) or would be refused over (bad); cached per board and light."""
        key = (self.field, self.sun)
        if self.shade_key != key:
            good, bad = set(), set()
            anchors = set(regions(self.field))
            for cell in anchors:
                solid = block_at(self.field, cell)
                cells, ok = cast(self.field, solid, SUNS[self.sun])
                if ok:
                    good.update(cells)
                else:
                    bad.update(c for c in cells if self.field[c[1]][c[0]] < 1)
            self.shade = (good, bad, anchors)
            self.shade_key = key
        return self.shade

    def sag_depth(self):
        """How far the blocks have slumped: nothing in play, sinking over the loss flash, fully slumped after it."""
        if self.lost:
            return 3
        if self.phase == "die":
            return min(3, self.tick_index() // 3)
        return 0

    def cell_picture(self, x, y, good, bad, anchors):
        """The picture a square should show now, or None when plain floor is all there is."""
        f = self.field
        h = f[y][x]
        if h >= 1:
            same = lambda a, b: 0 <= a < N and 0 <= b < N and f[b][a] == h
            pic = block_tile(self.ti, not same(x, y - 1), not same(x, y + 1), not same(x - 1, y),
                             not same(x + 1, y), h if (x, y) in anchors else 0, hashed(x, y, 3) % 3)
            sag = self.sag_depth()
            return sagged(self.ti, pic, sag) if sag else pic
        if h < 0:
            pit = lambda a, b: 0 <= a < N and 0 <= b < N and -3 <= f[b][a] < 0
            mode = 1 if (x, y) in good else 2 if (x, y) in bad else 0
            glint = (self.beat // 3 + hashed(x, y, 5)) % 4 if (hashed(x, y, 9) % 3) else -1
            return pit_tile(self.ti, not pit(x, y - 1), not pit(x - 1, y), -h, mode, glint)
        return refused_floor_tile() if (x, y) in bad else None

    def paint(self) -> None:
        good, bad, anchors = self.shading()
        sweep = self.topple_pictures() if self.phase == "topple" else {}
        for (x, y) in self.cells:
            name = f"cell-{x}-{y}"
            pic = sweep.get((x, y))
            if pic is None:
                pic = self.cell_picture(x, y, good, bad, anchors)
            self.put(name, pic, visible=pic is not None)
        self.paint_sun()
        self.paint_fuse()
        self.paint_cues(sweep)
        self.paint_life()
        self.paint_runner()
        self.paint_ambient()
        self.paint_cheer()
        self.paint_confetti()
        self.paint_haze()
        self.paint_storm()

    # -- the sun --
    def paint_sun(self):
        if self.lost or self.phase == "die":
            face = "sad"
        elif self.phase == "cheer":
            face = "cheer"
        elif self.phase in ("refuse", "poke"):
            face = "wince"
        else:
            face = "blink" if self.beat % 9 == 8 else "happy"
        ray = (self.beat // 2) % 2
        hidden = {self.sun: 0}
        if self.phase == "turn":
            idx = self.tick_index()
            hidden = {self.prev_sun: (1, 3, 3)[min(idx, 2)], self.sun: (3, 1, 0)[min(idx, 2)]}
        for d in range(4):
            if d in hidden:
                self.put(f"sun-{d}", sun_picture(d, face, ray), *sun_xy(d, hidden[d]))
            else:
                self.put(f"sun-{d}", None, visible=False)

    # -- the counter: a burning fuse under the board, one pixel shorter per move --
    def paint_fuse(self):
        left = -(-SPAN * max(0, self.moves_left) // self.budget) if self.budget else 0
        row = np.full((1, SPAN), -1, dtype=np.int8)
        row[0, :left] = WHT
        if left > 0 and not self.lost:
            row[0, left - 1] = (YEL, ORG, RED, ORG)[self.beat % 4]      # the burning tip
        key = (left, None if self.lost else self.beat % 4)
        s = self.sp["fuse"]
        if self.shown.get("fuse") != key:
            s.pixels = row
            self.shown["fuse"] = key

    # -- refusal outline / click ring --
    def paint_cues(self, sweep):
        idx = self.tick_index()
        if self.phase == "refuse" and (idx // 2) % 2 == 0:
            self.put("cue", outline_array(self.cue_cells, BAD))
        elif self.phase == "poke":
            self.put("cue", outline_array(self.cue_cells, BAD))
        else:
            self.put("cue", None, visible=False)
        if self.phase == "poke" and self.cue_point is not None:
            self.put("cue-ring", CUE_RING, self.cue_point[0] - 2, self.cue_point[1] - 2)
        else:
            self.put("cue-ring", None, visible=False)
        # dust at the front of a toppling solid
        if self.phase == "topple" and self.dust_at is not None:
            self.put("dust", dust_frames(self.ti)[min(3, self.tick_index() * 4 // TOPPLE_FRAMES)], *self.dust_at)
        else:
            self.put("dust", None, visible=False)

    # -- ambient life: wall critters (calm, cheer on a cleared level, sad on a lost run), border lights --
    def paint_life(self):
        crit = critter_set(self.ti)
        idx = self.tick_index()
        for k, (cx, cy) in enumerate(self.lives):
            lift = 0
            if self.lost or self.phase == "die":
                pic = crit["sad"][0]
            elif self.phase == "cheer":
                pic = crit["cheer"][(idx + k) % 2]
                lift = -((idx + k) % 2)          # a little hop
            else:
                pic = crit["calm"][(self.beat // 2 + k) % 8]
            self.put(f"critter-{k}", pic, INSET + cx * CELL, INSET + cy * CELL + lift)
        tw = THEMES[self.ti]["twinkle"]
        for k in range(len(TWINKLES)):
            s = self.sp[f"twinkle-{k}"]
            colour = tw[(self.beat // 2 + k) % len(tw)]
            key = ("tw", colour)
            if self.shown.get(f"twinkle-{k}") != key:
                s.pixels = np.full((1, 1), colour, dtype=np.int8)
                self.shown[f"twinkle-{k}"] = key

    # -- a bright gem that runs round the frame's bead row; it stops when the run is lost --
    def paint_runner(self):
        step = self.beat * (4 if self.phase == "cheer" else 2)
        if self.lost:
            step = self.shown.get("runner_at", step)
        self.shown["runner_at"] = step
        colour = THEMES[self.ti]["twinkle"][(self.beat // 3) % 4]
        key = ("gem", colour)
        s = self.sp["runner"]
        if self.shown.get("runner") != key:
            s.pixels = recolour(GEM, colour)
            self.shown["runner"] = key
        s.set_position(*ring_xy(step))

    # -- the quiet life over the walls: trees that ripen, torches, drifting butterflies, fish, snow, bubbles... --
    def paint_ambient(self):
        if not self.lost:
            self.amb_t = self.beat          # a lost run freezes the world where it stood
        t = self.amb_t
        for k, a in enumerate(self.amb):
            poses = a["poses"]
            x, y = amb_xy(a, t)
            self.put(f"amb-{k}", poses[(t // a["every"] + a["off"]) % len(poses)], INSET + x, INSET + y)

    # -- the level-clear shower: confetti falling over the whole screen, on top of the sparkles --
    def paint_confetti(self):
        idx = self.tick_index() if self.phase == "cheer" else -1
        for k in range(CONFETTI):
            if idx >= 0:
                h = hashed(k, self.ti, 21)
                x = 2 + h % 60
                y = -4 + idx * 11 + (h >> 5) % 16
                self.put(f"confetti-{k}", CONF[(k + idx) % len(CONF)], x, y, visible=y < 62)
            else:
                self.put(f"confetti-{k}", None, visible=False)

    # -- the loss: a sad rain cloud drifts over the board and weeps --
    def paint_storm(self):
        on = self.lost or (self.phase == "die" and self.tick_index() >= 2)
        if on:
            self.put("storm", STORM, STORM_X + (0, 1, 1, 0)[(self.beat // 2) % 4], INSET + 1)
        else:
            self.put("storm", None, visible=False)
        for k in range(RAIN):
            if on:
                top = INSET + 1 + STORM.shape[0]
                y = top + (self.beat * 3 + hashed(k, 5, 31) % 40) % 34
                x = STORM_X + 3 + (k * 13) % (STORM.shape[1] - 6)
                self.put(f"rain-{k}", DROP, x, y)
            else:
                self.put(f"rain-{k}", None, visible=False)

    # -- the level-clear sparkle --
    def paint_cheer(self):
        idx = self.tick_index() if self.phase == "cheer" else -1
        for k in range(7):
            if idx >= 0 and idx + 2 >= k // 2 + 1:
                h = hashed(k, self.ti, 11)
                x = INSET + 3 + h % (SPAN - 10)
                y = INSET + 3 + (h >> 4) % (SPAN - 10)
                shape = STARS[(idx + k) % 3]
                self.put(f"star-{k}", recolour(shape, CHEER_COLOURS[(idx + k) % 6]), x, y)
                self.shown[f"star-{k}"] = None      # recoloured each frame; force the next swap
            else:
                self.put(f"star-{k}", None, visible=False)

    # -- the loss: a red haze over the board and a sad sun --
    def paint_haze(self):
        if self.phase == "die":
            self.put("haze", haze((self.tick_index() // 3) % 3))
        elif self.lost:
            self.put("haze", haze(0))
        else:
            self.put("haze", None, visible=False)

    # -- the topple: the solid's squares turn to floor and the shadow's squares to slab, sweeping with the shadow --
    dust_at = None

    def topple_pictures(self):
        fx, fy = -SUNS[self.sun][0], -SUNS[self.sun][1]
        solid, landing = self.topple_from, self.topple_to
        if not landing:
            self.dust_at = None
            return {}

        def along(x, y, i, j):
            return (x * CELL + i) * fx + (y * CELL + j) * fy

        pix = [(x, y, i, j) for (x, y) in solid for j in range(CELL) for i in range(CELL)]
        origin = min(along(*p) for p in pix)
        far = max(along(x, y, i, j) for (x, y) in landing for j in range(CELL) for i in range(CELL))
        progress = (self.tick_index() + 1) / (TOPPLE_FRAMES + 1)
        front = origin + progress * (far - origin + 1)
        ground = ground_for(self.ti)
        slab = slab_tile(self.ti, 0)
        out = {}
        good, bad, anchors = self.shading()
        for (x, y) in landing:
            base = self.cell_picture(x, y, good, bad, anchors)
            t = base.copy() if base is not None else ground[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL].copy()
            for j in range(CELL):
                for i in range(CELL):
                    a = along(x, y, i, j)
                    if a <= front:
                        t[j, i] = C_INK if front - a < 1.5 else slab[j, i]
            out[(x, y)] = t
        for (x, y) in solid:
            base = self.cell_picture(x, y, good, bad, anchors)
            t = base.copy()
            for j in range(CELL):
                for i in range(CELL):
                    if along(x, y, i, j) <= front:
                        t[j, i] = ground[y * CELL + j, x * CELL + i]
            out[(x, y)] = t
        # dust rides the front line, centred across the solid
        lat = [(y * CELL + 2) if fx else (x * CELL + 2) for (x, y) in solid]
        mid = sum(lat) // len(lat)
        if fx:
            self.dust_at = (INSET + int(fx * front) - 3, INSET + mid - 3)
        else:
            self.dust_at = (INSET + mid - 3, INSET + int(fy * front) - 3)
        return out
