# ARC-AGI-3 candidate task bs02 (Bell Stealth, redrawn).
# Author: Claude Sonnet 5.5
# Date: 07-November-2026
# PURPOSE: The art redraw of bs01. The rules, the eight levels, the inputs, the guards, the loads, the bells, the plates,
#   the exit and the move counters are exactly bs01's (the rule functions below are copied unchanged). Only the picture is
#   new: every thing on screen is a named engine sprite (ground tiles, rocks, big floor pictures, props, pads, bells, the
#   door, the guards, you, the danger squares, the flying loads, the frame, the move bar), each level has its own world
#   (meadow, dusk dunes, snowfield, jungle, crystal cave, volcano, harbour, castle) with a gentle life of its own, and a
#   win or a loss is drawn (a cheer and a burst of stars; a wince, a dark world and laughing guards).
# SRP/DRY check: Pass. Rules are pure functions near the top (untouched from bs01); art tables and tile builders come next;
#   the engine glue at the bottom only shows what the rules decided. bs01 stays as it is; nothing is shared with it.
#
# CHANGELOG
# 07-Nov-2026 (Claude Sonnet 5.5): pass three, variety and life. Six living props per world (three new each, taller and
#   moving: sunflowers, igloos, frogs, lighthouses, armour, a small volcano...), flat ground decals, a wanderer that paces a
#   free lane and a flyer that crosses each world, a bell on a beam and a stone plinth for the pads, expressive guard eyes
#   (looking down, glancing, frowning on the move), a fuller fallen heap, rain on the dark world after a loss and a
#   star shower across the whole board on a win. No rule changed.
# 07-Nov-2026 (Claude Sonnet 5.5): pass two. Bigger creatures (nine pixels tall, with faces that look, blink, wince and
#   cheer), three drawings of every ground texture, two drawings of every wall, a big floor picture per world, three
#   taller props per world, a frame pattern per world, a darkening world on a loss and a bigger win burst. No rule changed.
# 07-Nov-2026 (Claude Sonnet 5.5): first version, a pure redraw of bs01: no rule, level, counter or input changed.

from collections import deque
import math

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

# ---------------------------------------------------------------------------------------------
# Geometry: eight by eight cells of seven pixels, inside a four pixel brick border.
# ---------------------------------------------------------------------------------------------
COLS = 8
ROWS = 8
CELL = 7
MARGIN = 4

MOVES = {GameAction.ACTION1: (0, -1), GameAction.ACTION2: (0, 1),
         GameAction.ACTION3: (-1, 0), GameAction.ACTION4: (1, 0)}
# Guards read their way down the distance map in this order: up, right, down, left.
NEIGHBOURS = ((0, -1), (1, 0), (0, 1), (-1, 0))

# ---------------------------------------------------------------------------------------------
# Levels. `ground` is the terrain: '#' rock, '.' low, '-' middle, '=' high (three terraces).
# `things` sits on the ground: G guard, P you, X exit, b bell, 1-4 plate that wants that load,
# w x y z a bell that is also a plate wanting 1 to 4. `loads` is each guard's load, in reading order.
# ---------------------------------------------------------------------------------------------
# <<<LEVELS (each entry is one level)
LEVELS = [
    {"ground": ["--------",
                "--------",
                "------=-",
                "--------",
                "--------",
                "--------",
                "--------",
                "--------"],
     "things": ["........",
                "........",
                ".G....w.",
                "........",
                "....P...",
                "........",
                "......X.",
                "........"],
     "loads": [1]},
    {"ground": ["--------",
                "----=---",
                "--------",
                "--=-----",
                "--------",
                "--------",
                "--------",
                "--------"],
     "things": ["........",
                "....b...",
                ".......X",
                "..w.....",
                "...G....",
                ".P......",
                "........",
                "........"],
     "loads": [1]},
    {"ground": ["--------",
                "--------",
                "--------",
                "--------",
                "--------",
                "--.....-",
                "--.....=",
                "----=---"],
     "things": ["...X....",
                "........",
                ".P......",
                "......G.",
                "........",
                "..G.....",
                "......2b",
                "....b..."],
     "loads": [1, 1]},
    {"ground": ["--.....-",
                "--.....=",
                "--.....-",
                "--------",
                "--------",
                "----=---",
                "--------",
                "----=---"],
     "things": ["........",
                ".....22b",
                "P..G..G.",
                "........",
                "....G...",
                "....b...",
                "...X....",
                "....b..."],
     "loads": [3, 1, 2]},
    {"ground": ["---#----",
                "=..#----",
                "---#=---",
                "---#----",
                "---#----",
                "---#----",
                "--------",
                "---#----"],
     "things": ["........",
                "b22...P.",
                "....b...",
                "........",
                "........",
                "........",
                ".G...G..",
                "....G..X"],
     "loads": [2, 1, 2]},
    {"ground": ["=---#=#-",
                "----#.#-",
                "----#.#-",
                "----#.#-",
                "----#.#-",
                "--------",
                "--------",
                "--------"],
     "things": ["b.X..b..",
                ".....3..",
                ".....2..",
                "........",
                "........",
                ".......G",
                "P.......",
                "...GG..."],
     "loads": [2, 2, 2]},
    {"ground": ["--------",
                "-------=",
                "-----=--",
                "#-######",
                "-----.--",
                "-----.--",
                "-----.--",
                "-----=--"],
     "things": ["......X.",
                ".......b",
                ".....b..",
                "........",
                ".....G..",
                ".....2G.",
                ".....3..",
                ".P...bG."],
     "loads": [3, 2, 2]},
    {"ground": ["=---#=#-",
                "----#.#-",
                "----#.#-",
                "--=-#.#-",
                "--------",
                "#######-",
                "--------",
                "--------"],
     "things": ["b....b..",
                ".....3..",
                ".....2..",
                ".Gb.....",
                "X.......",
                "........",
                "G.......",
                "..G...P."],
     "loads": [3, 1, 2]},
]
# LEVELS>>>

# Moves allowed per level, drawn as the bar in the bottom border; every arrow press spends one, RESET
# refills it. Sized at twice the shortest winning line, found by a full breadth-first search over
# (you, guards, loads, bell) with resolve() below on 07-Nov-2026: shortest lines 8, 21, 23, 27, 33,
# 38, 45, 50.
MOVE_BUDGET = (16, 42, 46, 54, 66, 76, 90, 100)

HEIGHT_OF = {"#": None, ".": 0, "-": 1, "=": 2}
PLATE_GLYPHS = "1234"
BELL_PLATE_GLYPHS = "wxyz"


# ---------------------------------------------------------------------------------------------
# Rules. Pure functions of plain values; the game class only shows what they decide.
# ---------------------------------------------------------------------------------------------
_MODELS: dict = {}


def build_model(spec: dict) -> dict:
    ground, things, loads = spec["ground"], spec["things"], spec["loads"]
    if len(ground) != ROWS or len(things) != ROWS:
        raise ValueError("a level is eight rows")
    floor, height, bells, plates, posts = set(), {}, [], [], []
    start = exit_cell = None
    for y in range(ROWS):
        if len(ground[y]) != COLS or len(things[y]) != COLS:
            raise ValueError(f"row {y} is not eight cells wide")
        for x in range(COLS):
            cell = (x, y)
            h = HEIGHT_OF[ground[y][x]]
            ch = things[y][x]
            if h is None:
                if ch != ".":
                    raise ValueError(f"{ch!r} sits inside rock at {cell}")
                continue
            floor.add(cell)
            height[cell] = h
            if ch == "b":
                bells.append(cell)
            elif ch in PLATE_GLYPHS:
                plates.append((cell, PLATE_GLYPHS.index(ch) + 1))
            elif ch in BELL_PLATE_GLYPHS:
                bells.append(cell)
                plates.append((cell, BELL_PLATE_GLYPHS.index(ch) + 1))
            elif ch == "G":
                posts.append(cell)
            elif ch == "P":
                start = cell
            elif ch == "X":
                exit_cell = cell
            elif ch != ".":
                raise ValueError(f"unknown thing {ch!r}")
    if start is None or exit_cell is None:
        raise ValueError("a level needs a start and an exit")
    if len(posts) != len(loads):
        raise ValueError("one load per guard")
    dist = []
    for b in bells:
        d = {b: 0}
        q = deque([b])
        while q:
            cur = q.popleft()
            for dx, dy in NEIGHBOURS:
                nb = (cur[0] + dx, cur[1] + dy)
                if nb in floor and nb not in d:
                    d[nb] = d[cur] + 1
                    q.append(nb)
        dist.append(d)
    return {"ground": tuple(ground), "things": tuple(things), "floor": frozenset(floor),
            "height": height, "bells": tuple(bells), "plates": tuple(plates),
            "posts": tuple(posts), "loads": tuple(loads), "start": start, "exit": exit_cell,
            "dist": tuple(dist)}


def model(index: int) -> dict:
    if index not in _MODELS:
        _MODELS[index] = build_model(LEVELS[index])
    return _MODELS[index]


def grid_distance(a, b) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def guard_step(m: dict, cell: tuple, target: int) -> tuple:
    d = m["dist"][target]
    here = d.get(cell)
    if here is None or here == 0:
        return cell
    for dx, dy in NEIGHBOURS:
        nb = (cell[0] + dx, cell[1] + dy)
        if d.get(nb, 1 << 30) == here - 1:
            return nb
    return cell


def advance(m: dict, guards: tuple, target: int) -> tuple:
    """Every guard takes one step toward the bell; a guard whose next cell is taken waits."""
    want = [guard_step(m, g, target) for g in guards]
    cur = list(guards)
    occupied = set(cur)
    moving = True
    while moving:
        moving = False
        for i, dest in enumerate(want):
            if cur[i] == dest or dest in occupied:
                continue
            occupied.discard(cur[i])
            occupied.add(dest)
            cur[i] = dest
            moving = True
    return tuple(cur)


def settle(m: dict, guards: tuple, loads: tuple, flows: list | None = None) -> tuple:
    """Loads run downhill between neighbouring guards: one unit moves when the giver's
    load plus ground height is at least two above the taker's."""
    h = m["height"]
    out = list(loads)
    for i, gi in enumerate(guards):
        for j, gj in enumerate(guards):
            if i == j or grid_distance(gi, gj) != 1 or out[i] < 1:
                continue
            if (out[i] + h[gi]) - (out[j] + h[gj]) >= 2:
                out[i] -= 1
                out[j] += 1
                if flows is not None:
                    flows.append((i, j))
    return tuple(out)


def held(m: dict, guards: tuple, loads: tuple) -> tuple:
    return tuple(any(g == cell and loads[i] >= need for i, g in enumerate(guards))
                 for cell, need in m["plates"])


def resolve(m: dict, player: tuple, guards: tuple, loads: tuple, target, move: tuple,
            flows: list | None = None):
    """One turn. Returns (player, guards, loads, target, caught, won)."""
    nxt = (player[0] + move[0], player[1] + move[1])
    if nxt not in m["floor"]:
        nxt = player
    if nxt in m["bells"]:
        target = m["bells"].index(nxt)
    if target is not None:
        guards = advance(m, guards, target)
    loads = settle(m, guards, loads, flows)
    caught = any(grid_distance(g, nxt) <= 1 for g in guards)
    won = (not caught) and nxt == m["exit"] and all(held(m, guards, loads))
    return nxt, guards, loads, target, caught, won


def start_state(m: dict) -> tuple:
    return (m["start"], m["posts"], m["loads"], None)


# ---------------------------------------------------------------------------------------------
# Art. Early home-console look: flat saturated fields, black hard edges, no grey. Every picture below is text:
# one letter per pixel, '.' is see-through. Red belongs to the guards alone: red means this sends you back.
# ---------------------------------------------------------------------------------------------
WHITE, BLACK, MAGENTA, PINK = 0, 5, 6, 7
RED, BLUE, LBLUE, YELLOW, ORANGE, MAROON, GREEN, PURPLE = 8, 9, 10, 11, 12, 13, 14, 15

# The one legend every picture uses. Capital letters are slots a builder fills with a theme colour (see px).
LEGEND = {"w": WHITE, "k": BLACK, "c": MAGENTA, "p": PINK, "r": RED, "b": BLUE, "l": LBLUE, "y": YELLOW,
          "o": ORANGE, "m": MAROON, "g": GREEN, "u": PURPLE}


def px(rows, **slots) -> np.ndarray:
    """Text rows to a pixel block. Slots (A=..., F=...) give a picture its theme colours. Rows must all be as wide as
    the first, so a mistyped picture fails loudly here instead of drawing a ragged sprite."""
    table = dict(LEGEND)
    table.update(slots)
    width = len(rows[0])
    assert all(len(row) == width for row in rows), rows
    return np.array([[-1 if ch == "." else table[ch] for ch in row] for row in rows], dtype=np.int8)


def mirrored(rows):
    return [row[::-1] for row in rows]


def two_sided(half):
    """A picture drawn as its left half becomes the whole thing: the right half is the mirror image."""
    return tuple(row + row[::-1] for row in half)


def framed(frames):
    """Frames of one animated prop must be the same size (the engine keeps one sprite per prop): pad to the biggest."""
    h = max(len(f) for f in frames)
    w = max(len(f[0]) for f in frames)
    out = []
    for f in frames:
        rows = [row.ljust(w, ".") for row in f]
        out.append(tuple(["." * w] * (h - len(rows)) + rows))     # shorter frames sit on the ground line
    return out


# ---------------------------------------------------------------------------------------------
# Ground textures: 'a' and 'b' are the two accent colours of a tier. 'b' twinkles; on the low tier 'a' drifts like water.
# Every texture has three hand-drawn variants (and each also flips), so no two neighbouring squares are the same
# picture. Marks are two or three pixels long, never lone specks, and leave a calm margin round the middle of the square
# so a guard or you never stands in a thicket.
# ---------------------------------------------------------------------------------------------
PATTERNS = {
    "ripple": (
        (".......", ".aaa...", "a...a.b", ".......", "...aaa.", "..a...a", ".b....."),
        ("b......", "..aaa..", ".a...a.", ".......", ".aa....", "...a.aa", "......b"),
        (".......", "aa.aa..", "..a..a.", ".b.....", "....aaa", ".a...a.", ".....b."),
    ),
    "tufts": (
        (".......", ".a.a...", "..a....", ".......", ".......", ".....b.", "......."),
        (".......", ".......", "....a.a", ".....a.", ".b.....", ".......", "......."),
        (".......", "..a.a..", "...a...", ".......", "......b", ".......", "......."),
    ),
    "leaves": (
        (".......", ".aa....", "..aa...", ".......", ".......", ".....b.", "......."),
        (".......", ".......", "....aa.", ".....aa", ".b.....", ".......", "......."),
        (".......", "...aa..", "..aa...", ".......", "......b", ".......", "......."),
    ),
    "specks": (
        (".......", ".aa....", ".......", ".......", ".......", "....b..", "......."),
        (".......", ".......", "....aa.", ".......", "..b....", ".......", "......."),
        (".......", ".......", ".......", "..aa...", ".......", ".....b.", "......."),
    ),
    "flecks": (
        (".......", "....b..", "...bab.", "....b..", ".......", ".......", "......."),
        (".......", ".......", ".......", ".b.....", "bab....", ".b.....", "......."),
        (".......", "..b....", ".......", ".......", ".......", "....b..", "...bab."),
    ),
    "facets": (
        (".......", "..a....", ".a.....", ".......", ".......", "....b..", "......."),
        (".......", ".......", "....a..", "...a...", ".b.....", ".......", "......."),
        ("a......", ".a.....", "..a....", ".......", ".......", ".....b.", "......."),
    ),
    "cracks": (
        (".......", ".a.....", "..a....", "...aa..", ".......", ".......", "......b"),
        (".......", ".......", "....a..", "...a...", "..aa...", ".b.....", "......."),
        (".......", "a......", ".aa....", "...a...", ".......", ".....b.", "......."),
    ),
    "planks": (
        (".......", "aaaaaaa", ".b...b.", ".......", "aaaaaaa", ".b...b.", "......."),
        ("aaaaaaa", "b...b..", ".......", "aaaaaaa", "..b...b", ".......", "......."),
        (".......", ".......", "aaaaaaa", ".b...b.", ".......", "aaaaaaa", "b...b.."),
    ),
    "slabs": (
        (".......", "..a....", "..a.b..", "aaaaaaa", "....a..", ".b..a..", "......."),
        (".......", "....a..", ".b..a..", "aaaaaaa", "..a....", "..a..b.", "......."),
        ("aaaaaaa", "...a...", ".b.a...", ".......", "aaaaaaa", "....a.b", "....a.."),
    ),
    "dunes": (
        (".......", ".aaa...", "....a..", ".......", ".......", ".......", "......b"),
        (".......", ".......", "..aaa..", ".a.....", ".......", ".......", "b......"),
        (".......", ".......", ".......", "...aaa.", ".a.....", ".b.....", "......."),
    ),
}

# ---------------------------------------------------------------------------------------------
# Themes, one per level. A tier is (fill, lit lip, cliff face, accent a, accent b, texture). Low is always the darkest
# colour of the three, high the lightest, and every raised edge draws its cliff, so height reads the same in every world.
# `pad` is the unlit pad colour, `door` the arch stone, `rim` the picture frame (stitch, band colour, second colour),
# `scarf` your scarf, `zone` the danger-square dither.
# ---------------------------------------------------------------------------------------------
THEMES = (
    dict(name="meadow", rim=("fence", ORANGE, YELLOW), pad=LBLUE, door=ORANGE, scarf=MAGENTA, zone=MAGENTA,
         tiers=((BLUE, LBLUE, PURPLE, LBLUE, WHITE, "ripple"),
                (GREEN, YELLOW, MAROON, YELLOW, WHITE, "tufts"),
                (YELLOW, WHITE, ORANGE, ORANGE, WHITE, "specks"))),
    dict(name="dusk", rim=("studs", PURPLE, MAGENTA), pad=LBLUE, door=MAROON, scarf=MAGENTA, zone=MAGENTA,
         tiers=((PURPLE, BLUE, BLACK, MAGENTA, BLUE, "ripple"),
                (ORANGE, YELLOW, MAROON, YELLOW, MAROON, "dunes"),
                (YELLOW, WHITE, ORANGE, ORANGE, WHITE, "specks"))),
    dict(name="snow", rim=("ice", LBLUE, WHITE), pad=MAGENTA, door=BLUE, scarf=MAGENTA, zone=MAGENTA,
         tiers=((BLUE, LBLUE, PURPLE, LBLUE, WHITE, "ripple"),
                (LBLUE, WHITE, BLUE, WHITE, BLUE, "flecks"),
                (WHITE, WHITE, LBLUE, LBLUE, BLUE, "flecks"))),
    dict(name="jungle", rim=("vine", GREEN, YELLOW), pad=LBLUE, door=ORANGE, scarf=MAGENTA, zone=PINK,
         tiers=((PURPLE, MAGENTA, BLACK, GREEN, MAGENTA, "ripple"),
                (GREEN, YELLOW, MAROON, YELLOW, ORANGE, "leaves"),
                (YELLOW, WHITE, ORANGE, ORANGE, MAROON, "slabs"))),
    dict(name="crystal", rim=("ice", BLUE, MAGENTA), pad=MAGENTA, door=PURPLE, scarf=ORANGE, zone=MAGENTA,
         tiers=((PURPLE, BLUE, BLACK, BLUE, MAGENTA, "facets"),
                (BLUE, LBLUE, PURPLE, LBLUE, WHITE, "facets"),
                (LBLUE, WHITE, BLUE, WHITE, MAGENTA, "facets"))),
    dict(name="volcano", rim=("flame", MAROON, ORANGE), pad=LBLUE, door=MAROON, scarf=MAGENTA, zone=MAGENTA,
         tiers=((MAROON, ORANGE, BLACK, ORANGE, YELLOW, "cracks"),
                (ORANGE, YELLOW, MAROON, MAROON, YELLOW, "cracks"),
                (YELLOW, WHITE, ORANGE, ORANGE, WHITE, "specks"))),
    dict(name="harbour", rim=("rope", YELLOW, ORANGE), pad=LBLUE, door=BLUE, scarf=MAGENTA, zone=MAGENTA,
         tiers=((BLUE, LBLUE, PURPLE, LBLUE, WHITE, "ripple"),
                (ORANGE, YELLOW, MAROON, MAROON, YELLOW, "planks"),
                (YELLOW, WHITE, ORANGE, ORANGE, WHITE, "planks"))),
    dict(name="castle", rim=("brick", BLUE, YELLOW), pad=LBLUE, door=ORANGE, scarf=YELLOW, zone=YELLOW,
         tiers=((BLUE, LBLUE, BLACK, LBLUE, WHITE, "ripple"),
                (PURPLE, LBLUE, BLUE, LBLUE, BLUE, "slabs"),
                (LBLUE, WHITE, PURPLE, WHITE, BLUE, "slabs"))),
)

# ---------------------------------------------------------------------------------------------
# Rock (the walls): two drawn blocks per world, used in a checker so a wall never repeats square to square.
# Only the crystal, volcano, harbour and castle levels have walls.
# ---------------------------------------------------------------------------------------------
ROCKS = {
    4: (("kkkkkkk", "kuuuwuk", "kuuwcuk", "kuwccuk", "kwcccuk", "kcccuuk", "kkkkkkk"),
        ("kkkkkkk", "kcuuuuk", "kccwuuk", "kcccwuk", "kuccuwk", "kuuuuuk", "kkkkkkk")),   # crystal facets catching the light
    5: (("kkkkkkk", "kmkokmk", "kmkmkmk", "kmkykok", "kokmkmk", "kmkmkmk", "kkkkkkk"),
        ("kkkkkkk", "kmkmkok", "kokmkmk", "kmkmkmk", "kmkokyk", "kmkmkok", "kkkkkkk")),   # basalt columns with glowing seams
    6: (("kkkkkkk", "kyoooyk", "kommmok", "komymok", "kommmok", "kyoooyk", "kkkkkkk"),
        ("kkkkkkk", "kyyyyyk", "kmmmmmk", "kooyook", "kmmmmmk", "koooook", "kkkkkkk")),   # crates, braced and slatted
    7: (("kkkkkkk", "kllkllk", "kbbkbbk", "kkkkkkk", "klllllk", "kbbbbbk", "kkkkkkk"),
        ("kkkkkkk", "klllllk", "kbbbbbk", "kkkkkkk", "kllkllk", "kbbkbbk", "kkkkkkk")),   # castle stone, lit from the top left
}

# ---------------------------------------------------------------------------------------------
# Props: living things that stand on empty ground and do nothing. Three kinds per world. Each is a list of frames (all the
# same size; slots A and B cycle colours), `drifts` is a one-pixel wander. They are bottom-centred in their square and
# may reach over the square above, so a tree is taller than a square. Never red: red belongs to the guards.
# ---------------------------------------------------------------------------------------------
def make_props(name, frames, drifts=False, **cycle):
    """Frames of rows, or one picture with a colour cycle (A=(...), B=(...)) -> the sprite's frame list."""
    if cycle:
        if isinstance(frames[0], str):                   # one picture whose colours cycle
            frames = [frames]
        pics = framed(frames)
        n = max(len(v) for v in cycle.values())
        return (name, [px(pics[i % len(pics)], **{k: v[i % len(v)] for k, v in cycle.items()}) for i in range(n)], drifts)
    return (name, [px(f) for f in framed(frames)], drifts)


def swapped(rows, a, b):
    """The same picture with two letters traded (a lit window, a flicker)."""
    return tuple(row.translate(str.maketrans(a + b, b + a)) for row in rows)


FLOWER = ("..AAA..", ".AAyAA.", ".AyyyA.", ".AAyAA.", "...g...", ".g.g.g.", "..ggg..", "...g...")
BUSH = ("..ggg..", ".ggBgg.", "ggggggg", "gBggggB", "ggggBgg", ".mmmmm.")
BUTTERFLY = (("cc...cc", "cccyccc", ".cckcc.", "..k.k.."), (".......", "..c.c..", "..cyc..", "...k..."))
CACTUS = ("...A...", "..ggg..", "g.ggg.g", "g.ggg.g", "ggggggg", "..ggg..", "..ggg..", ".mmmmm.")
TUMBLE = (("..mmm..", ".m.o.m.", "mo.m.om", ".m.o.m.", "..mmm.."), ("..mmm..", ".mo.om.", "m.mmm.m", ".mo.om.", "..mmm.."))
SUNROCK = ("..mmm..", ".moAom.", "mooooom", "moooAom", ".mmmmmm")
PINE = (("...w...", "..www..", "..ggg..", ".wgggw.", ".ggggg.", "wwgggww", "ggggggg", "...m...", "..mmm.."),
        ("...w...", "..wgw..", "..ggg..", ".wgggw.", ".ggggg.", "wgwgwgw", "ggggggg", "...m...", "..mmm.."))
PENGUIN = ((".kkkkk.", ".kwkwk.", ".kkokk.", "kkwwwkk", "kkwwwkk", "kkwwwkk", ".kkkkk.", ".oo.oo."),
           (".kkkkk.", ".kkkkk.", ".kkokk.", "kkwwwkk", "kkwwwkk", "kkwwwkk", ".kkkkk.", "oo...oo"))
SNOWMAN = ("..kkk..", ".kkkkk.", ".wwwww.", ".wkwkw.", "..wow..", ".AAAAA.", ".wwkww.", "wwwwwww", ".wwwww.")
PALM = ("kk.kkk.kk", "kgkkgkkgk", ".kgggggk.", "..kgogk..", "...kmk...", "...kmk...", "...kmk...", "..kkmkk..")
PARROT = (("..bbb..", ".bwkbbo", ".bbbbo.", "ybbbbb.", "yyybb..", ".y.y...", ".o.o..."),
          ("..bbb..", ".bwkbbo", ".bbbbo.", "bbbbbb.", "yybbb..", ".y.y...", ".o.o..."))
ORCHID = ("..AAA..", ".AAwAA.", "AAAyAAA", ".AAAAA.", "..AgA..", ".g.g.g.", "..ggg..", "...g...")
SHARD = ("...A...", "..AwA..", "A.AwA.A", "AwAAAwA", "AAAAAAA", "AAAAAAA", ".uuuuu.", ".kkkkk.")
GLOWCAP = ("..AAA..", ".AwAwA.", "AAAAAAA", "..www..", "..www..", ".gwwwg.", "gg.g.gg")
BRAZIER = (("...y...", "..yoy..", ".yowoy.", ".oyyyo.", "mmmmmmm", ".mkkkm.", ".mmmmm.", "..m.m.."),
           ("..y....", "..yoy..", ".yoooy.", ".owyyo.", "mmmmmmm", ".mkkkm.", ".mmmmm.", "..m.m.."))
OBSIDIAN = (("...k...", "..kmk..", "..kmk..", ".kmmmk.", ".kmwmk.", "kmmmmmk", "kkkkkkk"),
            ("...k...", "..kmk..", "..kmk..", ".kmmmk.", ".kmymk.", "kmmmmmk", "kkkkkkk"))
BUBBLE = (("...o...", "..oyo..", ".ooooo.", "mmmmmmm"), (".ooooo.", "oyyyyyo", "ooooooo", "mmmmmmm"),
          ("o.y.y.o", "...y...", ".......", "mmmmmmm"))
BARREL = (".kkkkk.", "kooyook", "kmmmmmk", "kooyook", "kooyook", "kmmmmmk", "kooyook", ".kkkkk.")
GULL = (("w.....w", "ww...ww", ".wwwww.", "..wwy.."), (".......", "wwwwwww", "..wkw..", "...y..."))
CRAB = (("o.....o", "oo...oo", ".ooooo.", ".owowo.", "m.m.m.m"), ("oo...oo", "o.....o", ".ooooo.", ".owowo.", ".m.m.m."))
TORCH = (("...y...", "..yoy..", ".yowoy.", "..ooo..", "..mkm..", "..mkm..", "..mkm..", ".mmkmm.", "mmmmmmm"),
         ("..y....", "..yoy..", ".yoooy.", "..owo..", "..mkm..", "..mkm..", "..mkm..", ".mmkmm.", "mmmmmmm"))
def swaying(head, stem):
    """Two frames of a plant in a breeze: the head slides a pixel right and the top of the stem bends under it."""
    assert all(len(r) == len(head[0]) for r in head + stem)
    a = tuple(r + "." for r in head) + tuple(r + "." for r in stem)
    b = tuple("." + r for r in head) + ("." + stem[0],) + tuple(r + "." for r in stem[1:])
    return a, b


# --- pass three: three more living things per world, taller and with a motion of their own -------------------------
SUNFLOWER = swaying((".yyyyy.", "yymmmyy", "ymmkmmy", "yymmmyy", ".yyyyy."),
                    ("...g...", "..gg...", "...g.g.", "...gg..", "...g..."))
TOADSTOOL = ("..ccc..", ".cwcpc.", "ccwccwc", ".wwwww.", "..www..", "..www..", ".gg.gg.")
PINWHEEL = ("AA.BB", "AAwBB", ".kwk.", "DDwCC", "DD.CC", "..m..", "..m..", "..m..", "..m..")
PYRAMID = ("...y...", "..yyo..", ".yyyoo.", "yyykooo", "yyykooo", "mmmmmmm")
LIZARD = (("....ggg", "ggggkgg", ".g..g..", "g.....g"), ("g...ggg", "ggggkgg", "..g..g.", ".g....."))
SKULL = ("w.....w", ".w...w.", "..www..", ".wkwkw.", "..www..", "..wkw..")
IGLOO = ("...bbb...", ".bbwwwbb.", "bwwwlwwwb", "bwlwwwlwb", "bwwwwwwwb", "bbbkkkbbb", "..bkkkb..")
ICESPIKES = ("...A...", "..AwA..", "A.AwA.A", "AAAwAAA", "AAAAAAA", ".bbbbb.")
SLED = ("....y...", "..kkkkk.", "kmoyyomk", "kkkkkkkk")
BIRDFLOWER = swaying(("c.o.b", "ccoob", ".cyo."), ("..y..", "..g..", ".gg..", "..g.g", "..gg."))
FROG = ((".bw.wb.", "bbbbbbb", "blyyylb", ".bbbbb.", "bb...bb"), (".bk.kb.", "bbbbbbb", "blyyylb", ".bbbbb.", ".b...b."))
TIKI = ("kkkkkkk", "kmmmmmk", "kmwmwmk", "kmmommk", "kmkkkmk", "kmmmmmk", "kkkkkkk", "..mkm..", "..mkm..")
CLUSTER = (".....A...", "..A.AwA..", ".AwAAwAA.", "AAwAAAAwA", "AAAAAAAAA", "uuuuuuuuu")
GLOWFLOWER = ("..A.A..", ".AAyAA.", "AAyyyAA", ".AAyAA.", "..lgl..", "...g...")
DRIP_BASE = ("..uuu..", "..ubu..", ".ubbbu.", "ubbbbbu")
DRIP = tuple(tuple(("...l..." if r == k else ".......") for r in range(3)) + DRIP_BASE for k in range(3))
DIAMOND = ("..kkkkk..", ".kAwwAAk.", "kAwAAAAAk", ".kAAAAAk.", "..kAAAk..", "...kAk...", "....k....")
LANTERN = ("...k...", "..kkk..", ".kyyyk.", ".kyoyk.", ".kyyyk.", "..kkk..", "...m...", "...m...")
VOLCANO = tuple(sm + ("...y...", "..yoy..", ".mmomm.", "mmmommm", "mmmmmmm") for sm in
                (("...w...", ".......", "......."), ("..w.w..", "...w...", "......."), ("...w...", "..w.w..", "...w...")))
BONES = ("w.w.w.w", ".wwwww.", "w.w.w.w", ".wwwww.", "..w.w..")
FIRELILY = ("..A.A..", ".AAyAA.", "A.AyA.A", "..yyy..", "...g...", "..gg...")
ANCHOR = ("..kkk..", "..k.k..", ".kkkkk.", "...k...", "k..k..k", "kk.k.kk", ".kkkkk.")
LIGHTHOUSE = ("..AAA..", ".kAAAk.", "..kkk..", ".bbbbb.", ".wwwww.", ".bbbbb.", ".wwwww.", "bbbbbbb")
SHELL = ("..ccc..", ".cpwpc.", "cpwpwpc", "cwpcpwc", ".c.c.c.")
BANNER = ("kkkkkkk", "kAAAAAk", "kAwwwAk", "kAwAwAk", "kAwwwAk", "kAAAAAk", ".kAAAk.", "..kAk..", "...k...")
ARMOUR = ("...y...", "..yyy..", ".kkkkk.", "kwwwwwk", "kkkkkkk", "kwwwwwk", "kbwwwbk", "kwwbwwk", ".kwwwk.", ".kk.kk.")
CHEST = tuple((g,) + ("kkkkkkk", "kmmmmmk", "kyyyyyk", "kmmkmmk", "kmmkmmk", "kkkkkkk") for g in ("...w...", "w......", "......w"))
CANDELABRA = ("y..y..y", "o..o..o", "k.kkk.k", "kkkkkkk", "..kmk..", "..kmk..", "..kmk..", ".kkkkk.")
CRYSTALBALL = ("..AAA..", ".AwAAA.", "AwAAAAA", ".AAAAA.", "..kkk..", ".kmmmk.", "kkkkkkk")

# Per theme, six kinds: (name, frames, drifts)
PROPS = (
    (make_props("flower", FLOWER, A=(ORANGE, WHITE, MAGENTA)), make_props("bush", BUSH, B=(MAGENTA, YELLOW)),
     make_props("butterfly", BUTTERFLY, True), make_props("sunflower", SUNFLOWER),
     make_props("toadstool", (TOADSTOOL, swapped(TOADSTOOL, "p", "y"))),
     make_props("pinwheel", PINWHEEL, A=(MAGENTA, BLUE, YELLOW, GREEN), B=(BLUE, YELLOW, GREEN, MAGENTA),
                C=(YELLOW, GREEN, MAGENTA, BLUE), D=(GREEN, MAGENTA, BLUE, YELLOW))),
    (make_props("cactus", CACTUS, A=(PINK, YELLOW, MAGENTA, YELLOW)), make_props("tumbleweed", TUMBLE, True),
     make_props("sunrock", SUNROCK, A=(YELLOW, WHITE)), make_props("pyramid", (PYRAMID,) * 3 + (swapped(PYRAMID, "k", "m"),)),
     make_props("lizard", LIZARD), make_props("skull", (SKULL,) * 3 + (swapped(SKULL, "k", "m"),))),
    (make_props("pine", PINE), make_props("penguin", PENGUIN),
     make_props("snowman", SNOWMAN, A=(MAGENTA, ORANGE, MAGENTA, YELLOW)), make_props("igloo", (IGLOO,) * 3 + (swapped(IGLOO, "k", "m"),)),
     make_props("icespikes", ICESPIKES, A=(BLUE, PURPLE, BLUE, MAGENTA)), make_props("sled", (SLED,) * 3 + (swapped(SLED, "y", "c"),))),
    (make_props("palm", (PALM, tuple(mirrored(PALM)))), make_props("parrot", PARROT),
     make_props("orchid", ORCHID, A=(MAGENTA, YELLOW, ORANGE, PINK)), make_props("birdflower", BIRDFLOWER),
     make_props("frog", FROG), make_props("tiki", (TIKI,) * 3 + (swapped(TIKI, "w", "y"),))),
    (make_props("cluster", CLUSTER, A=(MAGENTA, PINK, WHITE, LBLUE)), make_props("glowcap", GLOWCAP, A=(LBLUE, MAGENTA, WHITE)),
     make_props("diamond", DIAMOND, A=(LBLUE, MAGENTA, YELLOW, GREEN)), make_props("glowflower", GLOWFLOWER, A=(LBLUE, WHITE, MAGENTA)),
     make_props("stalagmite", DRIP), make_props("lantern", (LANTERN, swapped(LANTERN, "y", "o")))),
    (make_props("brazier", BRAZIER), make_props("obsidian", OBSIDIAN), make_props("bubble", BUBBLE),
     make_props("volcano", VOLCANO), make_props("bones", (BONES,) * 3 + (swapped(BONES, "w", "y"),)),
     make_props("firelily", FIRELILY, A=(MAGENTA, PINK))),
    (make_props("barrel", (BARREL,) * 3 + (swapped(BARREL, "y", "o"),)), make_props("gull", GULL, True),
     make_props("crab", CRAB), make_props("anchor", (ANCHOR,) * 3 + (swapped(ANCHOR, "k", "b"),)),
     make_props("lighthouse", LIGHTHOUSE, A=(YELLOW, WHITE, ORANGE, WHITE)),
     make_props("shell", (SHELL, swapped(SHELL, "p", "y")))),
    (make_props("torch", TORCH), make_props("banner", BANNER, A=(LBLUE, BLUE, YELLOW, BLUE)),
     make_props("armour", (ARMOUR,) * 3 + (swapped(ARMOUR, "o", "y"),)), make_props("chest", CHEST),
     make_props("candelabra", (CANDELABRA, swapped(CANDELABRA, "y", "o"))),
     make_props("crystalball", CRYSTALBALL, A=(LBLUE, YELLOW, GREEN, WHITE))),
)
DRIFT = ((0, 0), (1, 0), (1, 1), (0, 1))


def _hyp(dx, dy):
    return math.hypot(dx, dy)


def emblem_tile(ti: int, phase: int) -> np.ndarray:
    """The big flat picture on the floor (two squares by two): a daisy, a compass star, a snowflake, a giant blossom,
    a gem mosaic, a carved sun, a starfish, a rug. Drawn from shapes, in two frames that twinkle. Never a pad."""
    def build():
        n = 14
        a = np.full((n, n), -1, dtype=np.int8)
        c = (n - 1) / 2
        for y in range(n):
            for x in range(n):
                dx, dy = x - c, y - c
                r = _hyp(dx, dy)
                ang = math.atan2(dy, dx)
                d = abs(dx) + abs(dy)
                v = -1
                if ti == 0:                                   # daisy
                    petal = 3 + 3.6 * abs(math.cos(4 * ang)) ** 0.8
                    if r < 2.7:
                        v = YELLOW if (x + y + phase) % 5 else ORANGE
                    elif r < 3.4:
                        v = ORANGE
                    elif r <= petal:
                        v = WHITE if r < petal - 0.9 else PINK
                elif ti == 1:                                  # compass star baked into the sand
                    edge = abs(dx) ** 0.6 + abs(dy) ** 0.6
                    lim = 6.6 ** 0.6
                    if edge <= lim:
                        v = MAROON if edge > lim - 0.75 else YELLOW
                        if d < 3.4:
                            v = WHITE if (x + y + phase) % 2 == 0 else ORANGE
                elif ti == 2:                                  # snowflake
                    arm = min(abs(dx), abs(dy), abs(abs(dx) - abs(dy)) * 0.8)
                    if r < 6.8 and arm < 0.62:
                        v = BLUE
                    elif r < 6.8 and 3 < r < 5 and min(abs(abs(dx) - 2.5), abs(abs(dy) - 2.5)) < 0.55 and (abs(dx) < 3.5) == (abs(dy) < 3.5):
                        v = BLUE
                    if r < 1.9:
                        v = WHITE if phase == 0 else MAGENTA
                elif ti == 3:                                  # giant blossom
                    petal = 3 + 3.6 * abs(math.cos(3 * ang)) ** 0.8
                    if r < 2.4:
                        v = MAGENTA if phase == 0 else PINK
                    elif r < 3.2:
                        v = YELLOW
                    elif r <= petal:
                        v = ORANGE if r < petal - 1.2 else YELLOW
                elif ti == 4:                                  # gem mosaic: nested diamonds
                    if d <= 7.2:
                        v = (WHITE, MAGENTA, LBLUE, PURPLE)[min(3, int(d // 2))]
                        if d < 2 and phase:
                            v = YELLOW
                        if 6.2 < d <= 7.2:
                            v = BLACK
                elif ti == 5:                                  # a sun carved in the rock: rays and a glowing heart
                    ray = 3.1 + 3.5 * abs(math.cos(6 * ang)) ** 1.3
                    if r <= ray:
                        v = MAROON if r > ray - 0.85 else YELLOW
                        if r < 2.6:
                            v = WHITE if phase else ORANGE
                elif ti == 6:                                  # a starfish: five arms, dotted
                    arm = 0.5 + 0.5 * math.cos(5 * (ang + math.pi / 2))
                    reach = 1.8 + 4.9 * arm ** 1.6
                    if r <= reach:
                        v = BLACK if r > reach - 0.9 else MAGENTA
                        if v == MAGENTA and arm > 0.85 and int(r) in (3, 5):
                            v = PINK if (int(r) + phase) % 2 else YELLOW
                        if r < 1.6:
                            v = YELLOW
                else:                                          # rug: border, field and a gold lozenge
                    if d <= 7.4:
                        v = BLACK if d > 6.4 else YELLOW if d > 4.8 else (LBLUE if (x + y + phase) % 2 else WHITE)
                        if d <= 2.6:
                            v = YELLOW if phase else ORANGE
                if v >= 0:
                    a[y, x] = v
        return a
    return cached(("emblem", ti, phase), build)


def _emblem_spots(index, m):
    """Up to two flat two-by-two patches of empty, level, edge-free floor that the picture may lie on."""
    taken = set(m["bells"]) | {c for c, _ in m["plates"]} | set(m["posts"]) | {m["start"], m["exit"]}
    found = []
    for y in range(ROWS - 1):
        for x in range(COLS - 1):
            cells = [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]
            if any(c not in m["floor"] or c in taken for c in cells):
                continue
            if len({m["height"][c] for c in cells}) != 1 or any(any(_lower_sides(m, c)) for c in cells):
                continue
            found.append(((x * 7 + y * 3 + index * 5) % 11, x, y))
    found.sort()
    spots = []
    for _, x, y in found:
        if all(abs(x - sx) > 2 or abs(y - sy) > 2 for sx, sy in spots) and len(spots) < 2:
            spots.append((x, y))
    return spots


# ---------------------------------------------------------------------------------------------
# Pass three: the quiet life. Flat decals on the ground (never on a pad, a bell, a guard's post, you, the door or a big
# floor picture), one small creature that wanders to and fro along a free run of squares, and one flyer that crosses
# the world above the ground and below everything that matters. None of it means anything and none of it is red.
# ---------------------------------------------------------------------------------------------
DECALS = (
    (("..w....", ".wyw.w.", "..w.wyw", "...g.w.", ".g...g."),                      # meadow: daisies, pebbles, a puddle
     (".......", "..lw...", "..ll.ww", "...l.ll", "......."),
     (".bbbb..", "bllllb.", "bllllbb", ".bbbbb.")),
    (("..m....", ".mm.m..", "..m.mm.", "....m..", "...mm.."),                      # dusk: footprints, bones, pebbles
     ("w..w...", ".www...", "w..ww..", ".....w."),
     (".....k.", ".mm....", "mmk..m.", ".m..mm.")),
    (("b.b....", "...b.b.", ".b.b...", "...bb.b"),                                  # snow: paw prints, ice, twigs
     ("bbbbb..", "bwlwb..", "blllb..", "bbbbb.."),
     ("m..m...", ".mmm...", "m.m.m..")),
    (("..c.c..", ".cwcwc.", "..y.y..", ".......", "g.....g"),                       # jungle: toadstools, petals, roots
     ("c..p...", "...c.p.", ".p...c.", "..c...."),
     ("m.....m", ".mm.mm.", "..mmm..", ".m...m.")),
    (("l...w..", "..c..l.", "w....c.", ".l.w..."),                                  # crystal: shards, glow, cracks
     (".lll...", "lwwwl..", "lwwwl..", ".lll..."),
     ("u.....u", ".u...u.", "..uuu..", ".u...u.")),
    (("y..o..y", ".o...o.", "..y.y..", "o.....o"),                                  # volcano: embers, ash, lava crack
     (".kk....", "kmmk...", ".kmmk..", "..kk..."),
     ("y......", ".yo....", "..oy...", "...oy..", ".....y.")),
    (("p.w..c.", ".w...p.", "..c.w..", "p....w."),                                  # harbour: shells, net, puddle
     ("b.b.b..", ".b.b.b.", "b.b.b..", ".b.b.b."),
     (".bbbb..", "bllllb.", "bllllbb", ".bbbbb.")),
    (("..lll..", ".l...l.", "l..l..l", ".l...l.", "..lll.."),                      # castle: a ring of light, straw, a rug scrap
     ("y.o.y..", ".y.o.y.", "o.y.o..", ".o.y.o."),
     ("yyyyyyy", "ycycycy", "yyyyyyy")),
)

# Creatures that wander: (two frames facing right). They are drawn a little smaller than a square and bob as they walk.
CRITTERS = (
    ((".w.w...", "kykyk..", "yykkyk.", ".k..k.."), (".w.w...", "kykyk..", "ykykyk.", "..k.k..")),      # meadow: a bee on foot
    (("....m..", "..mmmm.", "mmmmmko", ".m.m.m."), ("....m..", "..mmmm.", "mmmmmko", "m.m.m..")),     # dusk: a beetle
    (("..w.w..", ".wwwww.", "wwwwwkw", ".w..w.."), ("..w.w..", ".wwwww.", "wwwwwkw", "w....w.")),     # snow: a hare
    (("..bbb..", ".bbbbb.", "gggggkb", ".g..g.."), ("..bbb..", ".bbbbb.", "gggggkb", "g....g.")),    # jungle: a snail-backed lizard
    (("..l.l..", ".lwwwl.", "lwwwwwk", ".l...l."), ("..l.l..", ".lwwwl.", "lwwwwwk", "l.....l")),     # crystal: a glow bug
    (("..o.o..", ".ooyoo.", "oyyyyok", ".o.o.o."), ("..o.o..", ".ooyoo.", "oyyyyok", "o.o.o.o")),     # volcano: a fire beetle
    (("..o.o..", ".ooooo.", "ooooooo", ".o.o.o."), ("..o.o..", ".ooooo.", "ooooooo", "o.o.o.o")),     # harbour: a crab
    (("..y.y..", ".yyyyy.", "yyyyykc", ".y...y."), ("..y.y..", ".yyyyy.", "yyyyykc", "y.....y")),     # castle: a yellow mouse
)
# Flyers cross the world slowly: (two frames, step per two painted frames).
FLYERS = (
    ((".b...b.", "bwb.bwb", ".bbkbb.", "..bkb.."), ("..b.b..", "..bbb..", ".bbkbb.", "..bkb..")),  # dragonfly
    (("k.....k", "kk...kk", ".kkkkk.", "..kmk.."), (".......", "kkkkkkk", ".kkmkk.", "..kmk..")),     # bat at dusk
    (("w.....w", "ww...ww", ".wwkww.", "...y..."), (".......", "wwwwwww", "..wkw..", "...y...")),     # snow bird
    (("g.....g", "gg...gg", ".gcgcg.", "..ccc.."), (".......", "ggggggg", "..gcg..", "...c...")),     # leaf-wing
    (("l.....l", "lw...wl", ".lwcwl.", "..lwl.."), (".......", "lwwwwwl", "..lcl..", "...l...")),     # pixie
    (("o.....o", "oo...oo", ".oyyyo.", "..omo.."), (".......", "ooooooo", "..oyo..", "...o...")),     # fire bat
    (("w.....w", "ww...ww", ".wwwww.", "..wwy.."), (".......", "wwwwwww", "..wkw..", "...y...")),     # gull
    (("c.....c", "cc...cc", ".cyyyc.", "..kyk.."), (".......", "ccccccc", "..cyc..", "...k...")),     # moth
)
FLYER_PICTURES = tuple([px(f) for f in pair] for pair in FLYERS)
CRITTER_PICTURES = tuple(([px(f) for f in pair], [px(f)[:, ::-1].copy() for f in pair]) for pair in CRITTERS)
DECAL_PICTURES = tuple(tuple(px(d) for d in per) for per in DECALS)


_SCENES: dict = {}


def _scene(index: int) -> dict:
    """Where everything decorative goes, decided once per level: big floor pictures, a handful of living things, flat
    decals and the wanderer's lane. Only empty, free squares are ever used, so the picture never hides a thing that plays."""
    if index in _SCENES:
        return _SCENES[index]
    m = model(index)
    ti = index % len(THEMES)
    taken = set(m["bells"]) | {c for c, _ in m["plates"]} | set(m["posts"]) | {m["start"], m["exit"]}
    emblems = _emblem_spots(index, m)
    for sx, sy in emblems:
        taken |= {(sx, sy), (sx + 1, sy), (sx, sy + 1), (sx + 1, sy + 1)}
    free = {(x, y) for y in range(ROWS) for x in range(COLS) if (x, y) in m["floor"] and (x, y) not in taken}
    # the wanderer's lane: the longest horizontal run of free squares on one level of ground
    lane, best = [], 1
    for y in range(ROWS):
        run = []
        for x in range(COLS + 1):
            c = (x, y)
            if c in free and (not run or m["height"][c] == m["height"][run[-1]]):
                run.append(c)
                continue
            if len(run) > best or (len(run) == best and len(run) > 1 and (y + index) % 2):
                lane, best = run, len(run)
            run = [c] if c in free else []
    free -= set(lane)
    props, decals = [], []
    for (x, y) in sorted(free, key=lambda c: (c[1], c[0])):
        h = (x * 5 + y * 3 + index * 7 + x * y) % 4
        if h == 0 and len(props) < 10:
            kind = (len(props) * 5 + index) % 6
            shape = PROPS[ti][kind][1][0].shape
            props.append((kind, (x, y), (CELL - shape[1]) // 2, CELL - shape[0]))
        elif h == 2 and len(decals) < 8:
            decals.append(((len(decals) + index * 2) % 3, (x, y)))
    _SCENES[index] = {"emblems": emblems, "props": props, "decals": decals, "lane": lane}
    return _SCENES[index]


# ---------------------------------------------------------------------------------------------
# Motes: a few tiny things that drift across each world and mean nothing (petals, glints, snow, fireflies, sparkles,
# embers, spray, dust). They pass under the creatures and the pads, wrap round the board, and go out when a run is lost.
# (frames, step x, step y): a step is one pixel every two painted frames.
# ---------------------------------------------------------------------------------------------
MOTES = (
    ((("pw.", "wp.", "..."), (".pw", ".wp", "...")), 1, 1),                  # meadow: petals
    ((("yw.", "wy.", "..."), (".y.", "yoy", ".y.")), 1, 0),                  # dusk: glints on the wind
    (((".w.", "www", ".w."), ("w.w", ".w.", "w.w")), 0, 1),                  # snow: flakes
    ((("yy.", "yy.", "..."), ("...", ".y.", "...")), 1, -1),                 # jungle: fireflies
    (((".w.", "wcw", ".w."), ("...", ".w.", "...")), 0, -1),                 # crystal: sparkles
    (((".o.", ".y.", "..."), ("...", ".o.", ".y.")), 0, -1),                 # volcano: embers
    (((".w.", "w.w", ".w."), ("...", ".w.", "...")), 1, -1),                 # harbour: spray
    (((".y.", "ywy", ".y."), ("y.y", ".w.", "y.y")), -1, 0),                 # castle: dust in the light
)
MOTE_SPRITES = 5
MOTE_PICTURES = tuple([px(f) for f in frames] for frames, _, _ in MOTES)

# ---------------------------------------------------------------------------------------------
# Things on the ground: pad (pressure plate), bell, bell that is also a pad, and the door. (Pictures unchanged from the
# first redraw; the pass-two work went into the creatures, the world and the frame.)
# ---------------------------------------------------------------------------------------------
# A load or a need is a die face: pips on a three by three lattice, six at most (unchanged from bs01).
LATTICE = {0: (), 1: ((3, 3),), 2: ((2, 2), (4, 4)), 3: ((3, 2), (2, 4), (4, 4)),
           4: ((2, 2), (4, 2), (2, 4), (4, 4)), 5: ((2, 2), (4, 2), (3, 3), (2, 4), (4, 4)),
           6: ((2, 1), (4, 1), (2, 3), (4, 3), (2, 5), (4, 5))}
# A guard's load as pips on its belly: two rows, three columns, filled from the bottom middle outwards.
BELLY = {0: (), 1: ((3, 7),), 2: ((2, 7), (4, 7)), 3: ((1, 7), (3, 7), (5, 7)),
         4: ((2, 6), (4, 6), (2, 7), (4, 7)), 5: ((1, 6), (3, 6), (5, 6), (2, 7), (4, 7)),
         6: ((1, 6), (3, 6), (5, 6), (1, 7), (3, 7), (5, 7))}

# A pad is a square stone plinth with a stud in each corner, a lit top edge and a shaded lower edge. A bell stands
# from a wooden beam on a chain: a flared bronze bell with a gleam, a clapper that swings below its lip.
PAD = ("ykkkkky", "kFFFFFk", "kFFFFFk", "kFFFFFk", "kFFFFSk", "kFSSSSk", "ykkkkky")
BELL = ("ymmmmmy", "...k...", "..kkk..", ".kywok.", ".kyook.", "kywoook", "kyyoomk", "kkkkkkk", ".......")
BELLPAD = ("ykkkkky", "kFFkFFk", "kFkykFk", "kkywokk", "kFkkkSk", "kFFkSSk", "ykkkkky")
DOOR_SHUT = ("..kkk..", ".kmmmk.", "..kkk..", ".kDDDk.", "kDmmmDk", "kDkkkDk", "kDmymDk", "kDmmmDk", "kkkkkkk")
DOOR_LIVE = ("y.kkk.y", ".kyyyk.", "..kkk..", ".kDDDk.", "kDyyyDk", "kDyyyDk", "kDyyyDk", "kDyyyDk", "kkkkkkk")
GLOW_SPOTS = (((2, 4), (4, 6)), ((3, 5), (2, 7)), ((4, 4), (2, 6)), ((3, 6), (4, 7)))
STAR_COLOURS = {"y": YELLOW, "w": WHITE, "c": MAGENTA, "l": LBLUE, "o": ORANGE, "g": GREEN}
STAR3 = (".A.", "AwA", ".A.")
STAR5 = ("..A..", ".AAA.", "AAwAA", ".AAA.", "..A..")

# ---------------------------------------------------------------------------------------------
# Creatures, both nine pixels tall: seven rows stand in their square and two rise above it (horns, hood). The guard is a
# red knight with a horned helm, glaring eyes that look where it is about to walk, and a belly that shows its load as pips.
# You are a round-headed ninja: black hood, a scarf-coloured headband, a yellow face with eyes that follow your way,
# blink, wince when you are caught and squeeze shut with a grin when you win.
# ---------------------------------------------------------------------------------------------
GUARD = ("k.....k", "ky...yk", "kkoookk", "krrrrrk", "krrrrrk", "krrrrrk", "krrrrrk", "krrrrmk", ".kk.kk.")
GUARD_FEET = (".kk.kk.", "kk...kk")
PLAYER = ("..kkk..", ".kkkkk.", "kCCCCCk", "kyyyyyk", "kyyyyyk", "koyyyok", ".kCCCk.", "kkkkkkk", ".kk.kk.")
PLAYER_FEET = (".kk.kk.", "kk...kk")
HEAP = ("kk...kk", "ww...ww", ".w...w.", ".w...w.", ".kkkkk.", "kyyyyyk", "kyyyyyk", "kCCCCCk", "kkkkkkk")
PUFF = (".......", ".......", "..www..", ".wlllw.", "wllllw.", "wlllllw", ".wlllw.", "..www..", ".......")


def guard_tile(load: int, face: int, grin: int, blink: bool, walk: int) -> np.ndarray:
    """grin is 0 (none) or 1/2 (the two frames of a laugh)."""
    def build():
        a = px(GUARD)
        a[8] = px((GUARD_FEET[walk],))[0]
        if face == 1:                      # facing away: the back of its helm, a seam down the middle
            a[3:6, 3] = MAROON
        elif blink and not grin:           # eyes squeezed shut
            a[4, (1, 2, 4, 5)] = BLACK
        else:
            # Two round eyes, two pixels each. A guard on the move looks where it goes (a pupil on that side); one that is
            # waiting looks down at you (the lower row of both eyes), so nobody is ever cross-eyed. A guard on the move
            # also frowns: the inner top pixel of each eye turns black, brows slanting down toward the nose.
            look = {2: 1, 4: -1}.get(face, 0)
            for cols in ((1, 2), (4, 5)):
                a[3:5, cols] = WHITE
                if look:
                    a[3:5, cols[1] if look > 0 else cols[0]] = BLACK
                else:
                    a[4, cols] = BLACK
            if face:
                a[3, 2] = a[3, 4] = BLACK
        if face != 1:
            a[5, 3] = MAROON               # a small mouth
        if grin:                           # caught you: brows down, teeth out, the belly pips hidden
            a[3, 1:3] = BLACK
            a[3, 4:6] = BLACK
            a[5, 1:6] = [BLACK, WHITE, BLACK, WHITE, BLACK] if grin == 1 else [WHITE, BLACK, WHITE, BLACK, WHITE]
        else:
            for x, y in BELLY[min(load, 6)]:
                a[y, x] = WHITE
        return a
    return cached(("guard", load, face, grin, blink, walk), build)


def player_tile(pose: str, look: tuple, walk: int, tick: int, scarf: int, blink: bool = False) -> np.ndarray:
    def build():
        if pose == "fall":                 # flat on its back, dizzy, crying
            a = px(HEAP, C=scarf)
            a[5, (2, 4)] = BLACK
            a[6, 3] = BLACK
            a[6 if tick % 2 == 0 else 7, 1] = LBLUE
            a[6 if tick % 2 == 0 else 7, 5] = LBLUE
            return a
        if pose == "puff":
            a = px(PUFF)
            a[1, 3] = a[7, 3] = YELLOW if tick % 2 == 0 else WHITE
            return a
        a = px(PLAYER, C=scarf)
        a[8] = px((PLAYER_FEET[walk],))[0]
        dx, dy = look
        if dy < 0 and pose == "idle":      # walking away: the back of the hood, a knot in the band
            a[3:6, 1:6] = BLACK
            a[4, 3] = scarf
        else:
            eyes = (1, 3) if dx < 0 else (3, 5) if dx > 0 else (2, 4)
            if pose == "cheer":            # eyes shut in a grin, mouth wide
                a[4, eyes[0]] = a[4, eyes[1]] = ORANGE
                a[3, eyes[0]] = a[3, eyes[1]] = BLACK
                a[5, 2:5] = MAROON
            elif pose == "hit":            # eyes squeezed, mouth gaping
                a[3:5, eyes[0]] = BLACK
                a[3:5, eyes[1]] = BLACK
                a[5, 2:5] = MAROON
            else:
                a[4, eyes[0]] = a[4, eyes[1]] = ORANGE if blink else BLACK
                a[5, 3] = BLACK
        a[6 if tick % 2 == 0 else 7, 6] = scarf          # the scarf tail flutters
        if pose == "hit":                  # you turn red: this sent you back
            flash = WHITE if tick % 2 else RED
            a[a == BLACK] = flash
        elif pose == "half":               # stepping into the door
            a[6:] = -1
        elif pose == "gone":
            a[:] = -1
        return a
    return cached(("player", pose, look, walk, tick % 2, scarf, blink), build)


# ---------------------------------------------------------------------------------------------
# Tile builders. Every one is cached, because a tile is a pure function of a few small values.
# ---------------------------------------------------------------------------------------------
_TILES: dict = {}


def cached(key, build):
    if key not in _TILES:
        _TILES[key] = build()
    return _TILES[key]


# When a run is over the world goes dark: every colour steps to a deeper one. (Guards and you keep theirs and stand out.)
DIM = {WHITE: LBLUE, LBLUE: BLUE, BLUE: PURPLE, YELLOW: ORANGE, ORANGE: MAROON, GREEN: PURPLE, PURPLE: BLACK,
       MAROON: BLACK, MAGENTA: MAROON, PINK: MAGENTA, RED: MAROON}
_DIMMED: dict = {}


def dim_of(a: np.ndarray) -> np.ndarray:
    """The dimmed twin of a cached picture, itself cached (the original is kept so its id stays unique)."""
    hit = _DIMMED.get(id(a))
    if hit is None:
        out = a.copy()
        for src, dst in DIM.items():
            out[a == src] = dst
        hit = _DIMMED[id(a)] = (a, out)
    return hit[1]


def ground_tile(ti: int, tier: int, lower: tuple, variant: int, phase: int) -> np.ndarray:
    def build():
        fill, hi, cliff, ca, cb, pattern = THEMES[ti]["tiers"][tier]
        rows = PATTERNS[pattern][variant % 3]
        if variant >= 3:
            rows = mirrored(rows[::-1])
        a = np.full((CELL, CELL), fill, dtype=np.int8)
        drift = phase // 2 if tier == 0 else 0           # the low ground shimmers sideways, the rest stands still
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == "a":
                    a[y, (x + drift) % CELL] = ca
                elif ch == "b" and (phase + variant + x + y) % 4 != 0:
                    a[y, x] = cb
        up, right, down, left = lower
        # a raised edge: a sunlit lip on the up and left sides, a cliff face on the down and right sides, black outside
        if up:
            a[1, 1:6] = hi
            a[0, :] = BLACK
        if left:
            a[1:6, 1] = hi
            a[:, 0] = BLACK
        if down:
            a[5, 1:6] = cliff
            a[6, :] = BLACK
        if right:
            a[1:6, 5] = cliff
            a[:, 6] = BLACK
        return a
    return cached(("ground", ti, tier, lower, variant, phase), build)


def rock_tile(ti: int, flip: int) -> np.ndarray:
    return cached(("rock", ti, flip), lambda: px(ROCKS.get(ti, ROCKS[7])[flip]))


def zone_tile(ti: int, parity: int) -> np.ndarray:
    """The danger dither: a checker over the inside of a square, coloured per world."""
    def build():
        a = np.full((CELL, CELL), -1, dtype=np.int8)
        for y in range(1, CELL - 1):
            for x in range(1, CELL - 1):
                if (x + y + parity) % 2 == 0:
                    a[y, x] = THEMES[ti]["zone"]
        return a
    return cached(("zone", ti, parity), build)


def pad_colours(ti: int, lit: bool) -> tuple:
    if lit:
        return WHITE, YELLOW
    fill = THEMES[ti]["pad"]
    return fill, (PURPLE if fill == BLUE else BLUE)


def pad_tile(ti: int, need: int, lit: bool, phase: int) -> np.ndarray:
    def build():
        fill, shade = pad_colours(ti, lit)
        a = px(PAD, F=fill, S=shade)
        for x, y in LATTICE[min(need, 6)]:
            a[y, x] = ORANGE if lit else BLACK
        if not lit:
            a[1, 1] = WHITE            # the lit corner of the stone
        else:                           # a held pad glints at its four corner studs
            a[0, 0] = a[6, 6] = WHITE if phase % 2 == 0 else YELLOW
            a[0, 6] = a[6, 0] = YELLOW if phase % 2 == 0 else WHITE
        return a
    return cached(("pad", ti, need, lit, phase % 2 if lit else 0), build)


def bell_tile(active: bool, phase: int) -> np.ndarray:
    """The bell in its frame. At rest the clapper sways; rung, the bronze flashes and sparks leap round the crown."""
    def build():
        a = px(BELL)
        if not active:
            a[8, (3, 2, 3, 4)[phase]] = ORANGE
            a[3, 3] = WHITE if phase % 2 == 0 else YELLOW
            return a
        a[8, 2 if phase % 2 == 0 else 4] = ORANGE
        body = a[3:7, 1:6]
        body[body == ORANGE] = YELLOW                    # rung: the bronze goes bright
        body[body == YELLOW] = WHITE if phase % 2 == 0 else YELLOW
        a[3, 3] = WHITE
        a[3, 0] = a[3, 6] = WHITE if phase % 2 == 0 else YELLOW      # sound leaps off both shoulders
        a[2, 1] = a[2, 5] = YELLOW if phase % 2 == 0 else WHITE
        return a
    return cached(("bell", active, phase if not active else phase % 2), build)


def bellpad_tile(ti: int, active: bool, lit: bool, phase: int) -> np.ndarray:
    def build():
        fill, shade = pad_colours(ti, lit)
        if active:
            a = px(BELLPAD, F=fill, S=shade, o=YELLOW, y=WHITE)
        else:
            a = px(BELLPAD, F=fill, S=shade)
        if lit:
            a[0, 0] = a[6, 6] = WHITE if phase % 2 == 0 else YELLOW
            a[0, 6] = a[6, 0] = YELLOW if phase % 2 == 0 else WHITE
        return a
    return cached(("bellpad", ti, active, lit, phase % 2 if (lit or active) else 0), build)


def door_tile(ti: int, live: bool, phase: int) -> np.ndarray:
    def build():
        if not live:
            return px(DOOR_SHUT, D=THEMES[ti]["door"])
        a = px(DOOR_LIVE, D=THEMES[ti]["door"])
        for x, y in GLOW_SPOTS[phase]:
            a[y, x] = WHITE
        a[0, 0] = a[0, 6] = WHITE if phase % 2 else YELLOW        # the lamp throws sparks
        a[1, 2:5] = WHITE if phase % 2 == 0 else YELLOW
        return a
    return cached(("door", ti, live, phase if live else 0), build)


def star_tile(kind: str) -> np.ndarray:
    """A sparkle: kind is 's' + size (3 or 5) + colour letter."""
    if kind[0] == "r":                                  # a raindrop (the sad weather after a loss)
        return cached(("drop",), lambda: px(("l", "l", "b")))
    big, colour = kind[1] == "5", STAR_COLOURS[kind[2]]
    centre = WHITE if colour != WHITE else YELLOW
    return cached(("star", kind), lambda: px(STAR5 if big else STAR3, A=colour, w=centre))


def flight_tile() -> np.ndarray:
    """A load in flight: a white pip in a black coin, so it is read as the same thing as a pip in a belly."""
    return cached(("flight",), lambda: px((".kkkk.", "kwwyk.", "kwwwk.", ".kkkk.")))


def rim_colour(kind: str, along: int, row: int, band: int, alt: int) -> int:
    """One pixel of the picture frame's two-pixel band. `along` runs round the frame, `row` is 0 outside, 1 inside."""
    if kind == "brick":                                  # bricks with black joints
        return BLACK if (along + 2 * row) % 4 == 0 else (alt if (along + row) % 8 == 5 else band)
    if kind == "fence":                                  # planks with posts
        return BLACK if along % 4 == 3 else (alt if along % 4 < 2 else band)
    if kind == "studs":                                  # a plate with bright rivets
        return alt if (along % 5 == 2 and row == 0) else band
    if kind == "ice":                                    # a ledge with icicles hanging inside
        return alt if (row == 1 and along % 3 == 0) or (row == 0 and along % 6 == 1) else band
    if kind == "vine":                                   # a vine with leaves
        return alt if (row == 1 and along % 6 in (1, 2)) or (row == 0 and along % 6 == 4) else band
    if kind == "flame":                                  # a licking fire
        return alt if (along + row * 2) % 4 < 2 else band
    return alt if ((along + row) // 2) % 2 else band     # rope: a twist


def border_tile(ti: int, state: str, phase: int) -> np.ndarray:
    """The four pixel frame: black outline, a two pixel band, a gem in each corner. White when the door is live, red on a loss."""
    def build():
        n = 64
        a = np.full((n, n), -1, dtype=np.int8)
        kind, band, alt = THEMES[ti]["rim"]
        if state == "live":
            band, alt = (WHITE, YELLOW) if phase % 2 == 0 else (YELLOW, WHITE)
        elif state == "death":
            band, alt = RED, MAROON
        for y in range(n):
            for x in range(n):
                d = min(x, y, n - 1 - x, n - 1 - y)
                if d >= MARGIN:
                    continue
                if d in (0, MARGIN - 1):
                    a[y, x] = BLACK
                    continue
                along = y if min(x, n - 1 - x) < min(y, n - 1 - y) else x
                a[y, x] = rim_colour(kind, along, d - 1, band, alt)
        for cx, cy in ((1, 1), (n - 3, 1), (1, n - 3), (n - 3, n - 3)):
            a[cy:cy + 2, cx:cx + 2] = YELLOW if state != "death" else MAROON
            a[cy, cx] = WHITE if state != "death" else RED
        return a
    return cached(("border", ti, state, phase % 2 if state == "live" else 0), build)


def fuse_tile(full: int, left: int, phase: int) -> np.ndarray:
    """The move counter, drawn exactly as in bs01: one pixel per move, two rows, a black track as long as the budget.
    A small spark burns at the spent end (it is never yellow, so it is never counted)."""
    def build():
        a = np.full((2, (full + 1) // 2), BLACK, dtype=np.int8)
        for k in range(min(left, full)):
            a[1 if k % 2 == 0 else 0, k // 2] = YELLOW
        if 0 < left < full:
            a[1 if left % 2 == 0 else 0, left // 2] = ORANGE if phase % 2 == 0 else WHITE
        return a
    return cached(("fuse", full, left, phase % 2 if 0 < left < full else 0), build)


# ---------------------------------------------------------------------------------------------
# Engine glue: sprites and the turn. The rules above decide the whole outcome of an action once; the frames below only
# show it.
# ---------------------------------------------------------------------------------------------
LAYER_GROUND, LAYER_EMBLEM, LAYER_PROP, LAYER_ZONE, LAYER_THING = -6, -5, -4, -3, -2
LAYER_BORDER, LAYER_EXIT, LAYER_GUARD, LAYER_PLAYER, LAYER_FX, LAYER_FUSE = -1, 0, 1, 3, 4, 9
FLIGHTS = 6
SPARKS = 28
RISE = 2                      # the creatures are nine pixels tall and stand two pixels above their square
SPARK_COLOURS = "ywclog"


def _pixel(cell):
    return MARGIN + cell[0] * CELL, MARGIN + cell[1] * CELL


def _lower_sides(m, cell):
    h = m["height"][cell]
    return tuple((cell[0] + dx, cell[1] + dy) in m["floor"] and m["height"][(cell[0] + dx, cell[1] + dy)] < h
                 for dx, dy in NEIGHBOURS)


def _things(m):
    kinds = {b: "bell" for b in m["bells"]}
    for cell, _ in m["plates"]:
        kinds[cell] = "bellpad" if cell in kinds else "pad"
    return kinds


def _thing_tile(ti, m, cell, kind, held_now, active, phase):
    if kind == "bell":
        return bell_tile(active, phase)
    need = dict(m["plates"])[cell]
    if kind == "pad":
        return pad_tile(ti, need, held_now, phase)
    return bellpad_tile(ti, active, held_now, phase)


def _variant(index, x, y):
    """Which of the six drawings of a ground texture this square uses."""
    return (x * 3 + y * 5 + index * 2 + (x * y) % 3) % 6


def _sprite(pixels, name, x, y, layer, tags=(), visible=True):
    return Sprite(pixels=pixels, name=name, blocking=BlockingMode.NOT_BLOCKED,
                  interaction=InteractionMode.INTANGIBLE, layer=layer, tags=list(tags),
                  visible=visible).set_position(x, y)


def build_levels() -> list:
    levels = []
    for index in range(len(LEVELS)):
        m = model(index)
        ti = index % len(THEMES)
        sprites = []
        for y in range(ROWS):
            for x in range(COLS):
                cell = (x, y)
                px_, py_ = _pixel(cell)
                if cell in m["floor"]:
                    h = m["height"][cell]
                    sprites.append(_sprite(ground_tile(ti, h, _lower_sides(m, cell), _variant(index, x, y), 0),
                                           f"ground_{x}_{y}", px_, py_, LAYER_GROUND, ("ground",)))
                    sprites.append(_sprite(zone_tile(ti, (x + y) % 2), f"zone_{x}_{y}", px_, py_, LAYER_ZONE,
                                           ("danger",), visible=False))
                else:
                    sprites.append(_sprite(rock_tile(ti, (x + y) % 2), f"rock_{x}_{y}", px_, py_, LAYER_GROUND,
                                           ("rock",)))
        deco = _scene(index)
        for i, (sx, sy) in enumerate(deco["emblems"]):
            px_, py_ = _pixel((sx, sy))
            sprites.append(_sprite(emblem_tile(ti, 0), f"emblem_{i}", px_, py_, LAYER_EMBLEM, ("emblem",)))
        for i, (variant, cell) in enumerate(deco["decals"]):
            h, w = DECAL_PICTURES[ti][variant].shape
            px_, py_ = _pixel(cell)
            sprites.append(_sprite(DECAL_PICTURES[ti][variant], f"decal_{i}", px_ + (CELL - w) // 2, py_ + (CELL - h) // 2,
                                   LAYER_EMBLEM, ("decal",)))
        for i, (kind, cell, ox, oy) in enumerate(deco["props"]):
            frames = PROPS[ti][kind][1]
            px_, py_ = _pixel(cell)
            sprites.append(_sprite(frames[0], f"prop_{i}", px_ + ox, py_ + oy, LAYER_PROP, ("prop", PROPS[ti][kind][0])))
        if deco["lane"]:
            bx, by = _pixel(deco["lane"][0])
            sprites.append(_sprite(CRITTER_PICTURES[ti][0][0], "critter", bx, by + 3, LAYER_PROP, ("critter",)))
        sprites.append(_sprite(FLYER_PICTURES[ti][0], "flyer", MARGIN, MARGIN + 8, LAYER_PROP, ("flyer",)))
        for cell, kind in _things(m).items():
            px_, py_ = _pixel(cell)
            sprites.append(_sprite(_thing_tile(ti, m, cell, kind, False, False, 0), f"thing_{cell[0]}_{cell[1]}",
                                   px_, py_ - (RISE if kind == "bell" else 0), LAYER_THING, (kind,)))
        px_, py_ = _pixel(m["exit"])
        sprites.append(_sprite(door_tile(ti, False, 0), "exit", px_, py_ - RISE, LAYER_EXIT, ("exit",)))
        for i, cell in enumerate(m["posts"]):
            px_, py_ = _pixel(cell)
            sprites.append(_sprite(guard_tile(m["loads"][i], 0, 0, False, 0), f"guard_{i}", px_, py_ - RISE,
                                   LAYER_GUARD, ("guard",)))
        px_, py_ = _pixel(m["start"])
        sprites.append(_sprite(player_tile("idle", (0, 1), 0, 0, THEMES[ti]["scarf"]), "player", px_, py_ - RISE,
                               LAYER_PLAYER, ("player",)))
        for i in range(MOTE_SPRITES):
            sprites.append(_sprite(MOTE_PICTURES[ti][0], f"mote_{i}", MARGIN, MARGIN, LAYER_ZONE, ("mote",)))
        for i in range(FLIGHTS):
            sprites.append(_sprite(flight_tile(), f"flight_{i}", 0, 0, LAYER_FX, ("fx", "load"), visible=False))
        for i in range(SPARKS):
            sprites.append(_sprite(star_tile("s3y"), f"spark_{i}", 0, 0, LAYER_FX, ("fx", "spark"), visible=False))
        sprites.append(_sprite(border_tile(ti, "normal", 0), "border", 0, 0, LAYER_BORDER, ("border",)))
        full = MOVE_BUDGET[index]
        sprites.append(_sprite(fuse_tile(full, full, 0), "fuse", MARGIN, 61, LAYER_FUSE, ("counter",)))
        levels.append(Level(sprites=sprites, grid_size=(64, 64)))
    return levels


def _faces(m, guards, target):
    out = []
    for g in guards:
        face = 0
        if target is not None:
            nxt = guard_step(m, g, target)
            if nxt != g:
                face = {(0, -1): 1, (1, 0): 2, (0, 1): 3, (-1, 0): 4}[(nxt[0] - g[0], nxt[1] - g[1])]
        out.append(face)
    return out


def _danger(m, guards, target):
    """Squares where a move would be caught: where the guards will stand after their next step and the
    four beside each, plus any bell that would send them to a place that catches you on that bell."""
    ahead = advance(m, guards, target) if target is not None else guards
    cells = set(ahead)
    for g in ahead:
        for dx, dy in NEIGHBOURS:
            c = (g[0] + dx, g[1] + dy)
            if c in m["floor"]:
                cells.add(c)
    for i, b in enumerate(m["bells"]):
        if any(grid_distance(g, b) <= 1 for g in advance(m, guards, i)):
            cells.add(b)
    return sorted(cells)


def _lerp(a, b, num, den):
    return (a[0] + round((b[0] - a[0]) * num / den), a[1] + round((b[1] - a[1]) * num / den))


class Bs02(ARCBaseGame):

    HIT_FRAMES = 5
    FALL_FRAMES = 4
    PUFF_FRAMES = 2

    def __init__(self) -> None:
        self.pos = (0, 0)
        self.guards = ()
        self.loads = ()
        self.target = None
        self.moves_left = 0
        self.script = []
        self.view = None
        self.look = (0, 1)        # which way you face; only the picture reads it
        self.beat = 0             # counts painted frames; the world's gentle life reads it
        self._refs = {}
        self._shown = {}
        self._zone_on = set()
        self._deco = {"emblems": [], "props": [], "decals": [], "lane": []}
        self._rocks = []
        camera = Camera(width=64, height=64, background=BLACK, letter_box=BLACK)
        super().__init__(game_id="bs02", levels=build_levels(), camera=camera,
                         available_actions=[1, 2, 3, 4])

    # -- the level ---------------------------------------------------------------------------
    def on_set_level(self, level: Level) -> None:
        m = model(self.level_index)
        self.pos, self.guards, self.loads, self.target = start_state(m)
        self.moves_left = MOVE_BUDGET[self.level_index]   # full again on entry and on RESET
        self.script = []
        self.look = (0, 1)
        self._refs = {s.name: s for s in level.get_sprites()}
        for s in self._refs.values():     # a level is cloned on entry and the clone shows everything: hide the helpers again
            if s.name.startswith(("zone_", "flight_", "spark_")):
                s.set_visible(False)
        self._shown = {}
        self._zone_on = set()
        self._deco = _scene(self.level_index)
        ti = self.level_index % len(THEMES)
        self._rocks = [(self._refs[f"rock_{x}_{y}"], rock_tile(ti, (x + y) % 2))
                       for y in range(ROWS) for x in range(COLS) if (x, y) not in m["floor"]]
        self._paint(self._settled())

    def _settled(self, state=None) -> dict:
        m = model(self.level_index)
        pos, guards, loads, target = state or (self.pos, self.guards, self.loads, self.target)
        flags = held(m, guards, loads)
        live = bool(flags) and all(flags)
        return {"p": _pixel(pos), "pose": "idle", "look": self.look, "walk": 0, "tick": 0,
                "g": [_pixel(c) for c in guards], "loads": list(loads), "face": _faces(m, guards, target),
                "grin": [False] * len(guards), "lit": list(flags), "live": live, "bell": target,
                "ring": "live" if live else "normal", "flights": [],
                "zone": _danger(m, guards, target), "shade": False, "fx": []}

    def _put(self, sprite, pixels, dim=False) -> None:
        """Swap a sprite's picture only when it really changed. `dim` shows the world's dark twin of the picture."""
        if dim:
            pixels = dim_of(pixels)
        if self._shown.get(sprite.name) is not pixels:
            sprite.pixels = pixels
            self._shown[sprite.name] = pixels

    def _paint(self, view: dict) -> None:
        self.view = view
        self.beat += 1
        phase = (self.beat // 2) % 4
        index = self.level_index
        ti = index % len(THEMES)
        m = model(index)
        refs = self._refs
        dim = view["shade"]
        # the ground: the low terrace shimmers, every tile twinkles a little
        for cell in m["floor"]:
            lower = _lower_sides(m, cell)
            self._put(refs[f"ground_{cell[0]}_{cell[1]}"],
                      ground_tile(ti, m["height"][cell], lower, _variant(index, *cell), phase), dim)
        for sprite, pixels in self._rocks:
            self._put(sprite, pixels, dim)
        deco = self._deco
        for i in range(len(deco["emblems"])):
            self._put(refs[f"emblem_{i}"], emblem_tile(ti, phase % 2), dim)
        for i, (variant, cell) in enumerate(deco["decals"]):
            self._put(refs[f"decal_{i}"], DECAL_PICTURES[ti][variant], dim)
        for i, (kind, cell, ox, oy) in enumerate(deco["props"]):
            name, frames, drifts = PROPS[ti][kind]
            s = refs[f"prop_{i}"]
            self._put(s, frames[(phase + i) % len(frames)], dim)
            bx, by = _pixel(cell)
            dx, dy = DRIFT[(phase + i) % 4] if drifts else (0, 0)
            s.set_position(bx + ox + dx, by + oy + dy)
        # the wanderer paces its lane, a pixel a frame, and turns at each end; the flyer crosses the world on a lazy wave
        if deco["lane"]:
            s = refs["critter"]
            right, left = CRITTER_PICTURES[ti]
            span = (len(deco["lane"]) - 1) * CELL + 1
            t = (self.beat + index * 5) % (2 * span)
            going = t < span
            self._put(s, (right if going else left)[(self.beat // 2) % 2], dim)
            bx, by = _pixel(deco["lane"][0])
            s.set_position(bx + (t if going else 2 * span - t), by + 3 + (self.beat // 2) % 2)
            s.set_visible(not dim)
        s = refs["flyer"]
        self._put(s, FLYER_PICTURES[ti][(self.beat // 2) % 2], dim)
        s.set_position(MARGIN + (index * 13 + self.beat) % 50, MARGIN + 8 + (index * 11) % 30 + round(3 * math.sin(self.beat / 5 + index)))
        s.set_visible(not dim)
        # the motes drift across the board, one pixel every two painted frames, and go out when the run is lost
        pictures, vx, vy = MOTE_PICTURES[ti], MOTES[ti][1], MOTES[ti][2]
        for i in range(MOTE_SPRITES):
            s = refs[f"mote_{i}"]
            self._put(s, pictures[(phase + i) % len(pictures)])
            s.set_position(MARGIN + (i * 23 + index * 11 + vx * (self.beat // 2)) % 56,
                           MARGIN + (i * 37 + index * 5 + vy * (self.beat // 2)) % 56)
            s.set_visible(not dim)
        # the danger squares
        want = set(view["zone"])
        for cell in self._zone_on - want:
            refs[f"zone_{cell[0]}_{cell[1]}"].set_visible(False)
        for cell in want - self._zone_on:
            refs[f"zone_{cell[0]}_{cell[1]}"].set_visible(True)
        self._zone_on = want
        # things on the ground
        plate_at = {cell: i for i, (cell, _) in enumerate(m["plates"])}
        active = m["bells"][view["bell"]] if view["bell"] is not None else None
        for cell, kind in _things(m).items():
            held_now = view["lit"][plate_at[cell]] if cell in plate_at else False
            self._put(refs[f"thing_{cell[0]}_{cell[1]}"],
                      _thing_tile(ti, m, cell, kind, held_now, cell == active, phase), dim)
        self._put(refs["exit"], door_tile(ti, view["live"], phase), dim)
        # guards: they laugh when they have caught you
        for i, (gx, gy) in enumerate(view["g"]):
            s = refs[f"guard_{i}"]
            grin = (1 + view["tick"] % 2) if view["grin"][i] else 0
            self._put(s, guard_tile(min(view["loads"][i], 6), view["face"][i], grin,
                                    phase == 3 and not view["walk"] and not grin, view["walk"]))
            s.set_position(gx, gy - RISE)
        # you
        s = refs["player"]
        pose = view["pose"]
        tick = view["tick"] if pose in ("hit", "fall", "puff") else phase
        self._put(s, player_tile(pose, view["look"], view["walk"], tick, THEMES[ti]["scarf"],
                                 phase == 3 and pose == "idle" and not view["walk"]))
        s.set_position(view["p"][0], view["p"][1] - RISE - (1 if pose == "cheer" else 0))
        # the loads in flight, the sparks
        for i in range(FLIGHTS):
            s = refs[f"flight_{i}"]
            if i < len(view["flights"]):
                s.set_position(view["flights"][i][0] - 1, view["flights"][i][1] - 1)
                s.set_visible(True)
            else:
                s.set_visible(False)
        for i in range(SPARKS):
            s = refs[f"spark_{i}"]
            if i < len(view["fx"]):
                kind, fx, fy = view["fx"][i]
                self._put(s, star_tile(kind))
                off = 2 if kind[1] == "5" else 1
                s.set_position(fx - off, fy - off)
                s.set_visible(True)
            else:
                s.set_visible(False)
        # the frame and the move counter
        self._put(refs["border"], border_tile(ti, view["ring"], phase))
        full = MOVE_BUDGET[index]
        self._put(refs["fuse"], fuse_tile(full, self.moves_left, phase))

    # -- one action --------------------------------------------------------------------------
    def step(self) -> None:
        if self.action.id == GameAction.RESET:
            self.complete_action()
            return
        if not self.script and not self._begin():
            self.complete_action()
            return
        view = self.script.pop(0)
        end = view.get("end")
        if end == "lose":
            self.lose()
        elif end == "next":
            self.next_level()
        else:
            self._paint(view)
            if self.script:
                return
        self.complete_action()

    def _begin(self) -> bool:
        move = MOVES.get(self.action.id)
        if move is None:
            return False
        m = model(self.level_index)
        old = (self.pos, self.guards, self.loads, self.target)
        flows: list = []
        pos, guards, loads, target, caught, won = resolve(m, *old, move, flows)
        new = (pos, guards, loads, target)
        self.moves_left -= 1
        spent = (not caught) and (not won) and self.moves_left <= 0   # a winning last move still wins
        self.pos, self.guards, self.loads, self.target = new
        self.look = move
        self.script = self._frames(m, old, new, move, flows, caught or spent, won)
        return True

    def _frames(self, m, old, new, move, flows, dies, won) -> list:
        op, og, ol, ot = old
        np_, ng, nl, nt = new
        bumped = np_ == op
        moved = any(a != b for a, b in zip(og, ng))
        steps = 3 if (not bumped or moved) else 2
        before = self._settled(old)
        after = self._settled(new)
        frames = []
        for k in range(1, steps + 1):
            v = dict(before)
            v["p"] = _lerp(_pixel(op), _pixel(np_), k, steps)
            if bumped and k < steps:
                v["p"] = (v["p"][0] + move[0], v["p"][1] + move[1])
            v["g"] = [_lerp(_pixel(a), _pixel(b), k, steps) for a, b in zip(og, ng)]
            v["face"] = [self._heading(m, a, b, f) for a, b, f in zip(og, ng, before["face"])]
            v["walk"] = k % 2
            v["flights"] = []
            frames.append(v)
        # a load in flight: the giver shows what it keeps, the taker what it had
        if flows and not dies:
            shown = [min(a, b) for a, b in zip(ol, nl)]
            for k in (1, 2, 3):
                v = dict(after)
                v["loads"] = shown
                v["lit"] = list(before["lit"])
                v["live"] = before["live"]
                v["ring"] = before["ring"]
                v["flights"] = [_lerp((_pixel(ng[i])[0] + 2, _pixel(ng[i])[1] + 3),
                                      (_pixel(ng[j])[0] + 2, _pixel(ng[j])[1] + 3), k, 4) for i, j in flows]
                frames.append(v)
            frames.append(dict(after))
        else:
            last = dict(after)
            frames[-1] = last
        if dies:
            grin = [grid_distance(g, np_) <= 1 for g in ng]
            centre = (after["p"][0] + 3, after["p"][1] + 2)
            plan = (("hit", self.HIT_FRAMES), ("fall", self.FALL_FRAMES), ("puff", self.PUFF_FRAMES))
            tick = 0
            for pose, count in plan:
                for _ in range(count):
                    v = dict(after)
                    v["pose"] = pose
                    v["tick"] = tick
                    v["grin"] = grin
                    v["ring"] = "death"
                    v["lit"] = [False] * len(after["lit"])
                    v["live"] = False
                    v["zone"] = []
                    v["shade"] = pose != "hit"          # the world goes dark once you are down
                    if pose == "hit":          # shake
                        v["p"] = (after["p"][0] + (1 if tick % 2 else -1), after["p"][1])
                    elif pose == "fall":       # dizzy stars circle the heap
                        ang = tick * math.pi / 2
                        v["fx"] = [("s3y", centre[0] + round(5 * math.cos(ang + a)),
                                    centre[1] - 2 + round(2 * math.sin(ang + a))) for a in (0, math.pi)]
                    else:                      # the poof, and stars flung out
                        v["fx"] = [("s3w" if n % 2 else "s3y", centre[0] + dx, centre[1] + dy)
                                   for n, (dx, dy) in enumerate(((-6, -3), (6, -3), (-5, 3), (5, 3)))]
                    if pose != "hit":          # it rains on the dark world
                        v["fx"] = v["fx"] + [("rl", MARGIN + (i * 13 + 5) % 56, MARGIN + (i * 17 + tick * 6) % 50) for i in range(10)]
                    tick += 1
                    frames.append(v)
            frames.append({"end": "lose"})
        elif won:
            door = (_pixel(m["exit"])[0] + 3, _pixel(m["exit"])[1] + 3)
            for pose, count in (("cheer", 1), ("half", 2), ("gone", 4)):
                for n in range(count):
                    v = dict(after)
                    v["pose"] = pose
                    v["ring"] = "live"
                    v["live"] = True
                    v["zone"] = []
                    v["tick"] = n
                    if pose == "half":         # the first sparks leap from the door
                        v["fx"] = [("s3" + SPARK_COLOURS[(n * 2 + a) % 6], door[0] + dx, door[1] + dy)
                                   for a, (dx, dy) in enumerate(((-5, -2), (5, -2), (-3, 5), (3, 5)))]
                    if pose == "gone":         # a burst: a ring of big stars and an inner ring of small ones
                        r = 3 * (n + 1)
                        v["fx"] = [("s5" + SPARK_COLOURS[(a + n) % 6],
                                    door[0] + round(r * math.cos(a * math.pi / 4)),
                                    door[1] + round(r * math.sin(a * math.pi / 4))) for a in range(8)]
                        v["fx"] += [("s3" + SPARK_COLOURS[(a + n + 3) % 6],
                                     door[0] + round(r * 0.6 * math.cos((a + 0.5) * math.pi / 2)),
                                     door[1] + round(r * 0.6 * math.sin((a + 0.5) * math.pi / 2))) for a in range(4)]
                        # and a shower of small stars falls across the whole world
                        v["fx"] += [("s3" + SPARK_COLOURS[(a + n) % 6], MARGIN + (a * 19 + n * 7) % 56,
                                     MARGIN + (a * 11 + n * 12) % 52) for a in range(10)]
                    frames.append(v)
            frames.append({"end": "next"})
        return frames

    @staticmethod
    def _heading(m, a, b, face):
        if a == b:
            return face
        return {(0, -1): 1, (1, 0): 2, (0, 1): 3, (-1, 0): 4}[(b[0] - a[0], b[1] - a[1])]
