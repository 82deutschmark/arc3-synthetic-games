# ARC-AGI-3 candidate task xa03.
#
# Author: Claude Sonnet 5.5 Medium
# Date: 07-November-2026
# PURPOSE: Round two of the crawler (xa02 became xa03). Same rooms, keys, gates, patrols and routes; the
#          picture is rebuilt at a bigger scale (6-pixel cells, a 10-cell window) with readable creatures,
#          six themed moats, patrol trails, and a hop / bump / lift / puff / iris animation set. The game is
#          a little harder: the window is smaller, the last three worlds gain a patrol that walks the middle of
#          a room, and a lantern carried by the bodies burns down one drop per action; when it is out the run ends.
# SRP/DRY check: Pass. Rules (World, SPECS, movement, doors, gates, patrols, curses, send-back) are xa02's;
#          the painter, the event record that drives it, and the lantern are the new parts.
#
# CHANGELOG
# 07-Nov-2026 Claude Sonnet 5.5 Medium: xa03. CELL 4 -> 6, VIEW 16 -> 10. New kit, themed moats, trails.
#   LANTERN: every action burns one drop (BUDGETS per world); at zero the run ends (GAME_OVER). Three extra
#   room patrols (worlds 4-6, data only, each a vertical lane across a room's middle). Animation: hop, dust,
#   bump and wince, pickup pop, rune burst, portcullis lift, lock swing, puff on send-back, burst on a felled
#   patrol, iris on clear and on loss. Frames still cost no actions: one logical move is one perform_action.
#   FIX: the painted map was cached by (size, start, exit), so two worlds of one size with the same start and
#   exit (worlds 3 and 4) shared one map; it is now cached per world.
# 31-Oct-2026 Claude Sonnet 5.5 Max: xa02. Art pass over xa01 (meadow, brick, moat, faces, slides).

from __future__ import annotations

import numpy as np

from arcengine import (
    ARCBaseGame,
    BlockingMode,
    Camera,
    GameAction,
    InteractionMode,
    Level,
    RenderableUserDisplay,
    Sprite,
)


# ---- tiny art helpers ---------------------------------------------------------------------------------
def pixel_art(rows: tuple, colours: dict) -> list[list[int]]:
    return [[-1 if ch == "." else colours[ch] for ch in row] for row in rows]


def blank(w: int, h: int) -> list[list[int]]:
    return [[-1] * w for _ in range(h)]


def brick(face: int, mortar: int, row: int = 0) -> list[list[int]]:
    """Six pixels of wall: two courses, mortar between, the join staggered from row to row."""
    a = ("ffmfff", "ffmfff", "mmmmmm", "ffffmf", "ffffmf", "mmmmmm")
    b = ("fffmff", "fffmff", "mmmmmm", "fmffff", "fmffff", "mmmmmm")
    return pixel_art(a if row % 2 == 0 else b, {"f": face, "m": mortar})


# Shape glyphs, drawn black on the key's colour. The same three families show on the held gem (4x3), on locks
# and on the exit (4x4), so a player can match what they carry to what blocks them.
GLYPH4 = {0: (".XX.", "X..X", "X..X", ".XX."), 1: ("XXXX", "X..X", "X..X", "XXXX"),
          2: ("X...", "XX..", "XXX.", "XXXX")}
GLYPH3 = {0: (".XX.", "X..X", ".XX."), 1: ("XXXX", "X..X", "XXXX"),
          2: ("X...", "XX..", "XXXX")}


def glyph_cells(table: dict, shape: int):
    return [(x, y) for y, row in enumerate(table[shape]) for x, ch in enumerate(row) if ch == "X"]


# ---- creatures (bottom-aligned on their cell; the stamp helper centres them) ----------------------------
def crab(colour: int, step: int) -> list[list[int]]:
    """Hostile patrol: horned magenta crab, white eyes with a black pupil, black mouth, feet that step."""
    legs = "c.cc.c" if step % 2 == 0 else ".c..c."
    return pixel_art(("c....c", ".cccc.", "cwbcwb", ".cbbc.", legs), {"c": colour, "w": 0, "b": 5})


def guard(colour: int, heading: tuple, step: int) -> list[list[int]]:
    """Warden: light-blue helmeted guard. The dark visor slot sits on the side it faces (both eyes in it);
    seen from behind the visor is gone. Legs step."""
    dx, dy = heading
    px = pixel_art((".cccc.", "cvvvvc", ".cccc.", "cccccc", "cc..cc", ".c..c.", ".c..c."),
                   {"c": colour, "v": 5})
    if dy < 0:
        px[1] = [colour] * 6
    elif dx < 0:
        px[1][1] = px[1][2] = 0
    elif dx > 0:
        px[1][3] = px[1][4] = 0
    else:
        px[1][2] = px[1][3] = 0
    if step % 2:
        px[5], px[6] = px[6], px[5]
    return px


# ---- the two bodies --------------------------------------------------------------------------------------
def hero(skin: int, face: int, awake: bool, key_hue: int, key_shape: int, gear, curses: bool, over: bool,
         flame: int, flick: int, wince: bool, step: int) -> list[list[int]]:
    """An 8 x 8 figure: a round head with eyes that look where it last went and a mouth, a neck row, a chest
    gem in the key's colour with the key's shape on it, boots, a raised blade, a cap for the anchor, a ball
    and chain for a curse, sweat drops for a heavy load and a lantern in the right hand whose flame is the
    oil left. Bottom-aligned; its head stands two pixels above its cell."""
    g = blank(8, 8)

    def put(x: int, y: int, c: int) -> None:
        if 0 <= x < 8 and 0 <= y < 8:
            g[y][x] = c

    for y in range(3):                                  # head: narrow top, wide eyes row, narrow chin
        for x in (range(1, 7) if y == 1 else range(2, 6)):
            put(x, y, skin)
    if face == 0:                                       # seen from behind: dark hair, no face
        for x in range(1, 7):
            put(x, 1, 5)
            if 2 <= x <= 5:
                put(x, 0, 5)
    else:
        eyes = {1: (2, 5), 2: (1, 3), 3: (4, 6)}[face]
        eye = 5 if awake else 4
        if wince:                                       # eyes squeezed shut: one pixel each, a row lower
            put(eyes[0], 1, skin)
            put(eyes[1], 1, skin)
            put(eyes[0], 2 if eyes[0] >= 2 else 1, eye)
            put(eyes[1], 2, eye)
        else:
            put(eyes[0], 1, eye)
            put(eyes[1], 1, eye)
            if awake:
                for mx in {1: (3, 4), 2: (2,), 3: (5,)}[face]:
                    put(mx, 2, 5)
    if 2 in gear:                                       # anchor: a grey cap
        put(3, 0, 2)
        put(4, 0, 2)
    for y in (3, 4):                                    # neck/shoulders and arms
        for x in range(1, 7) if y == 3 else (1, 6):
            put(x, y, skin)
    for y in range(3):                                  # chest gem with the key's shape
        for x in range(4):
            put(2 + x, 4 + y, key_hue)
    for x, y in glyph_cells(GLYPH3, key_shape):
        put(2 + x, 4 + y, 5)
    foot = 13 if 0 in gear else skin
    lx, rx = (2, 5) if step % 2 == 0 else (3, 4)
    put(lx, 7, foot)
    put(rx, 7, foot)
    if 1 in gear:                                       # raised blade, hilt at the hand
        for y in range(2, 6):
            put(0, y, 1)
        put(0, 6, 13)
        put(1, 6, 13)
    if curses:                                          # ball and chain
        put(0, 7, 5)
        put(1, 7, 5)
        put(1, 6, 5)
    if over:                                            # sweat drops
        put(1, 0, 10)
        put(6, 0, 10)
    # Lantern, right hand: a cage of two grey pixels and a flame as tall as the oil.
    put(7, 5, 2 if flame else 4)
    put(7, 6, 2 if flame else 4)
    for k in range(flame):
        put(7 if not (k == flame - 1 and flick % 2 and flame > 1) else 6, 4 - k, 11 if k < flame - 1 else 12)
    return g


# ---- things on the floor -------------------------------------------------------------------------------------
def boot(leather: int) -> list[list[int]]:
    return pixel_art(("bb....", "bb....", "bb....", "bbbb..", "bbbbb.", "bbbbbb"), {"b": leather})


def sword(blade: int, hilt: int) -> list[list[int]]:
    return pixel_art(("....bb", "...bbb", "..bbb.", ".bbb..", "hbb...", "hh...."), {"b": blade, "h": hilt})


def anchor_shape(colour: int) -> list[list[int]]:
    return pixel_art(("..cc..", "..cc..", ".cccc.", "..cc..", "c.cc.c", ".cccc."), {"c": colour})


def boulder(face: int, light: int) -> list[list[int]]:
    return pixel_art((".ffff.", "fllfff", "flffff", "ffffff", "ffffff", ".ffff."), {"l": light, "f": face})


def orb(colour: int) -> list[list[int]]:
    """Colour tile: a round gem with a white highlight."""
    return pixel_art((".cccc.", "cwwccc", "cwcccc", "cccccc", "cccccc", ".cccc."), {"c": colour, "w": 0})


def domino(shape: int) -> list[list[int]]:
    """Shape tile: a white stone carrying the shape's black glyph."""
    px = pixel_art((".wwww.", "wwwwww", "wwwwww", "wwwwww", "wwwwww", ".wwww."), {"w": 0})
    for x, y in glyph_cells(GLYPH4, shape):
        px[1 + y][1 + x] = 5
    return px


def brazier(colour: int, lit: bool, flick: int, burst: int = 0) -> list[list[int]]:
    """Standing bowl of a rune in its gate's colour. Unlit: a dark ember. Lit: a white flame that flickers;
    `burst` (1..3) is the frame of the flare right after it is lit."""
    px = pixel_art(("......", "......", "rrrrrr", ".rrrr.", "..rr..", ".rrrr."), {"r": colour})
    if not lit:
        px[1][2] = px[1][3] = 4
        return px
    if burst:
        for x in range(1, 5):
            px[1][x] = 0
        px[0][1 + burst % 3] = 11
        px[0][3] = 0
    else:
        px[1][1:5] = [-1, 0, 0, -1]
        px[0][2 + flick % 2] = 0
    return px


def flower(colour: int, open_: bool) -> list[list[int]]:
    """Decoy: opens and closes. Petals wear the same colours the live things wear."""
    if open_:
        return pixel_art(("..hh..", ".hyyh.", ".hyyh.", "..hh..", "..s...", "..s..."),
                         {"h": colour, "y": 11 if colour != 11 else 0, "s": 5})
    return pixel_art(("......", "..hh..", "..hh..", "..hh..", "..s...", "..s..."), {"h": colour, "s": 5})


def wall_torch(flick: int) -> list[list[int]]:
    rows = ("..t...", ".fff..", ".fff..", "..b...", ".bbb..", "......") if flick % 2 == 0 else \
           ("...t..", ".fff..", ".fff..", "..b...", ".bbb..", "......")
    return pixel_art(rows, {"f": 12, "t": 11, "b": 2})


def tower(roof: int) -> list[list[int]]:
    """Corner tower outside a room: coloured roof, lit slit window, black stone."""
    return pixel_art(("..rr..", ".rrrr.", "rrrrrr", "555555", "55ww55", "555555"), {"r": roof, "w": 11, "5": 5})


def tree(leaf: int) -> list[list[int]]:
    """A great tree filling an unused room corner: black-outlined crown on a trunk."""
    return pixel_art(("..55..", ".5445.", "554455", ".5555.", "..tt..", "..tt.."), {"5": 5, "4": 4, "t": 13})


# ---- moat dressing (outside the rooms, never on a live cell) ----------------------------------------------
def pine(leaf: int, trunk: int, sway: int) -> list[list[int]]:
    rows = ("..gg..", ".gggg.", "gggggg", ".gggg.", "..tt..", "..tt..") if sway % 2 == 0 else \
           ("...gg.", ".gggg.", "gggggg", ".gggg.", "..tt..", "..tt..")
    return pixel_art(rows, {"g": leaf, "t": trunk})


def lily(pad: int, bloom: int, sway: int) -> list[list[int]]:
    rows = ("......", ".pppp.", "ppbppp", ".pppp.", "......", "......") if sway % 2 == 0 else \
           ("......", "......", ".pppp.", "ppbppp", ".pppp.", "......")
    return pixel_art(rows, {"p": pad, "b": bloom})


def rock(face: int, light: int, sway: int) -> list[list[int]]:
    return pixel_art(("......", ".fff..", "fllfff", "ffffff", ".ffff.", "......"), {"f": face, "l": light})


def floe(white: int, sway: int) -> list[list[int]]:
    return pixel_art(("......", ".wwww.", "wwwwww", ".wwww.", "......", "......") if sway % 2 == 0 else
                     ("......", "......", ".wwww.", "wwwwww", ".wwww.", "......"), {"w": white})


def cloud(white: int, sway: int) -> list[list[int]]:
    return pixel_art(("..ww..", ".wwww.", "wwwwww", "wwwwww", ".wwww.", "......") if sway % 2 == 0 else
                     ("......", "..ww..", ".wwww.", "wwwwww", "wwwwww", ".wwww."), {"w": white})


# Flat marks on the meadow (never an obstacle: you can walk over every one of them).
def daisy() -> list[list[int]]:
    return pixel_art((".w.", "wyw", ".w."), {"w": 0, "y": 11})


def tuft() -> list[list[int]]:
    return pixel_art(("b.b", ".b.", ".b."), {"b": 5})


def pebbles() -> list[list[int]]:
    return pixel_art(("gg.", "gg.", "..d"), {"g": 2, "d": 3})


def puddle() -> list[list[int]]:
    return pixel_art((".bb.", "bbbb"), {"b": 10})


def petals() -> list[list[int]]:
    return pixel_art(("p.p", ".p."), {"p": 7})


FLAT = {"daisy": daisy, "tuft": tuft, "pebbles": pebbles, "puddle": puddle, "petals": petals}


# A theme per world: base colour, glint colour, glint pixel kind, decoration (a sprite maker and how rare),
# and the roof colour of the corner towers. Nothing here is a live colour in a live shape.
THEMES = [
    dict(base=9, glint=10, deco=(("pine", 7), ("lily", 7)), floor=("daisy", "tuft"), roof=12),       # lake and pines
    dict(base=9, glint=10, deco=(("lily", 5), ("rock", 9)), floor=("tuft", "petals"), roof=15),       # blossom pond
    dict(base=5, glint=0, deco=(("rock", 9),), floor=("pebbles", "tuft"), roof=9),                     # night, with stars
    dict(base=13, glint=12, deco=(("rock", 7),), floor=("pebbles", "tuft"), roof=12),                  # lava
    dict(base=10, glint=0, deco=(("floe", 6),), floor=("puddle", "tuft"), roof=9),                    # ice sea
    dict(base=10, glint=0, deco=(("cloud", 6),), floor=("daisy", "puddle"), roof=11),                  # sky islands
]


def deco_sprite(kind: str, theme: dict, sway: int) -> list[list[int]]:
    if kind == "pine":
        return pine(14, 13, sway)
    if kind == "lily":
        return lily(14, 7, sway)
    if kind == "rock":
        return rock(4 if theme["base"] != 5 else 3, 2, sway)
    if kind == "floe":
        return floe(0, sway)
    return cloud(0, sway)


def stamp(frame, x: int, y: int, sprite) -> None:
    """Paint a sprite (list of rows, -1 clear) at pixel x, y; clips at the frame edge."""
    h, w = len(frame), len(frame[0])
    for r, row in enumerate(sprite):
        for c, v in enumerate(row):
            if v >= 0 and 0 <= y + r < h and 0 <= x + c < w:
                frame[y + r][x + c] = v


# Colours. The floor is green meadow, so no rule may read green any more: gate rune 5 is purple.
VOID, FLOOR, WALL = 5, 14, 5
BRICK = 13
BODY, IDLE = 0, 3
FOE_BODY = 6
KEY_HUE = (7, 9, 8)
HOSTILE, WARDEN = 0, 1
WARD_BODY = 10
BOOTS, BLADE, ANCHOR = 0, 1, 2
GEAR_HUE = (13, 1, 2)
WEIGHT = (1, 1, 2)
CURSED_WEIGHT, CARRY = 3, 3
CURSE_HUE = 3
RUBBLE, RUBBLE_LIGHT = 4, 2
GATE_RUNES = {4: 11, 5: 15, 6: 12}
PLAIN_RUNE = 13
GLOW = 0
PROP_HUE = (7, 9, 8, 11, 15, 12, 6)
CORNERS = ((-1, -1, 0, 0), (1, -1, 4, 0), (-1, 1, 0, 4), (1, 1, 4, 4))

# Geometry. Six pixels a cell, a ten-cell window (60 pixels) centred in the 64-pixel frame.
CELL = 6
VIEW = 10
SCREEN = VIEW * CELL
OFF = (64 - SCREEN) // 2
SETTLED = 4                  # animation frames 1..3, then 4 = settled and clean
TWEEN = (2, 3, 5, 6)         # pixels of a one-cell slide shown on frames 1..4 (6 = settled)
HOP = (1, 2, 1, 0)           # pixels a mover rises on frames 1..4
FACE_UP, FACE_DOWN, FACE_LEFT, FACE_RIGHT = 0, 1, 2, 3

CIRCLE, SQUARE, TRI = 0, 1, 2
PINK, CYAN, GOLD = 0, 1, 2

# The lantern: drops of oil per world, one burned by every action (arrows and the fifth key). Measured from
# the verifier's recorded routes (258, 481, 787, 624, 1049, 1000 actions for a solver that knows the map)
# times 3.5, 3.0, 2.8, 2.6, 2.4, 2.4: widest in world one. One list, easy to retune after a person has played.
BUDGETS = [910, 1450, 2210, 1630, 2520, 2400]
IRIS_FRAMES = 5
OPEN_FRAMES = 3
DYING_FRAMES = 5

def rune_hue(gnum: int) -> int:
    return GATE_RUNES.get(gnum, PLAIN_RUNE)


def _hash(x: int, y: int, salt: int) -> int:
    n = (x * 73856093) ^ (y * 19349663) ^ (salt * 83492791)
    n = (n ^ (n >> 13)) & 0xFFFFFFFF
    n = (n * 1274126177) & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFFFFFFFF


SPECS = [
    dict(cols=3, rows=2, roomW=12, roomH=12, gap=3,
         links=[((0,0),(1,0)), ((0,0),(0,1)), ((0,1),(1,1)), ((1,1),(2,1)), ((1,0),(2,0))],
         start=(0,0,3,3), startKey=(CIRCLE, PINK),
         tiles=[(1,1,6,6,"c",CYAN), (0,1,3,9,"s",SQUARE), (2,1,8,6,"c",GOLD)],
         doors=[((1,0),(2,0),CIRCLE,CYAN)],
         gates=[],
         exit=(2,0,8,6,SQUARE,GOLD),
         marks=[(0,0,8,8,0), (1,1,3,3,1), (2,1,3,8,2), (0,1,8,3,3)],
         gear=[(0,1,8,8,BOOTS,0)],
         rubble=[(1,1,5,6), (1,1,5,7), (1,1,6,7)],
         props=[(0,0,6,6,"#ff2d95"), (1,0,4,8,"#00e5ff"), (2,1,6,4,"#b14bff"), (0,1,9,8,"#9dff3c")],
         foes=[(1,1,2,6,1,0,8,HOSTILE)]),
    dict(cols=3, rows=3, roomW=12, roomH=12, gap=3,
         links=[((0,0),(1,0)), ((1,0),(2,0)), ((0,0),(0,1)), ((0,1),(0,2)), ((0,2),(1,2)), ((1,2),(2,2)), ((2,0),(2,1))],
         start=(0,0,3,3), startKey=(CIRCLE, PINK),
         tiles=[(0,2,3,3,"s",TRI), (2,2,8,8,"c",GOLD), (1,2,6,6,"s",SQUARE), (0,1,6,6,"c",CYAN)],
         doors=[((2,0),(2,1),TRI,GOLD)],
         gates=[((0,0),(0,1),(4, 5))],
         exit=(2,1,6,8,SQUARE,CYAN),
         marks=[(1,0,3,3,4), (2,0,8,8,5), (0,0,8,8,0), (0,1,3,3,1), (0,2,8,3,2), (1,2,3,8,6), (2,2,3,3,7)],
         gear=[(0,1,8,8,BOOTS,0), (2,0,4,4,ANCHOR,0), (1,2,3,3,BOOTS,1)],
         rubble=[(0,2,5,5), (0,2,6,5), (1,2,7,7)],
         props=[(0,0,5,9,"#ffd400"), (0,1,6,7,"#ff2d95"), (1,2,4,4,"#00e5ff"), (2,2,8,9,"#b14bff"), (1,0,8,3,"#ff6a00")],
         foes=[(0,1,6,2,0,1,8,HOSTILE), (1,2,2,6,1,0,8,HOSTILE), (1,2,4,4,0,1,6,WARDEN)]),
    dict(cols=4, rows=3, roomW=12, roomH=12, gap=3,
         links=[((0,0),(1,0)), ((1,0),(2,0)), ((1,0),(1,1)), ((0,0),(0,1)), ((0,1),(0,2)), ((0,2),(1,2)), ((1,2),(2,2)), ((2,0),(3,0)), ((3,0),(3,1)), ((3,1),(3,2))],
         start=(0,0,3,3), startKey=(CIRCLE, PINK),
         tiles=[(0,2,3,3,"s",SQUARE), (1,1,6,6,"c",CYAN), (3,0,6,9,"c",PINK), (1,2,8,3,"s",CIRCLE), (2,2,6,6,"c",GOLD), (0,1,3,8,"s",TRI)],
         doors=[((2,0),(3,0),SQUARE,CYAN), ((3,1),(3,2),TRI,GOLD)],
         gates=[((0,0),(0,1),(4, 5, 6))],
         exit=(3,2,8,6,CIRCLE,PINK),
         marks=[(1,0,3,3,4), (2,0,8,8,5), (1,1,3,8,6), (0,0,8,8,0), (0,1,8,3,1), (0,2,8,8,2), (1,2,3,3,7), (2,2,8,3,8), (3,0,3,3,9), (3,1,8,8,10)],
         gear=[(0,1,3,3,BOOTS,0), (1,1,8,8,BLADE,0), (2,2,3,9,ANCHOR,0), (1,2,5,3,BLADE,1), (3,0,8,3,ANCHOR,1)],
         rubble=[(1,2,5,5), (1,2,6,5), (0,2,8,9), (2,2,4,4)],
         props=[(0,0,5,9,"#ffd400"), (1,0,3,4,"#ff6a00"), (0,2,7,8,"#ff2d95"), (2,2,7,7,"#9dff3c"), (3,0,7,8,"#00e5ff"), (1,1,3,9,"#b14bff")],
         foes=[(1,0,2,6,1,0,8,HOSTILE), (0,1,6,2,0,1,8,HOSTILE), (2,2,2,6,1,0,8,HOSTILE), (1,0,4,4,0,1,6,WARDEN), (2,2,4,4,0,1,6,WARDEN)]),
    dict(cols=4, rows=3, roomW=12, roomH=12, gap=3,
         links=[((0,0),(1,0)), ((1,0),(2,0)), ((1,0),(1,1)), ((0,0),(0,1)), ((0,1),(0,2)), ((0,2),(1,2)), ((1,2),(2,2)), ((2,1),(2,2)), ((2,0),(3,0)), ((3,0),(3,1)), ((3,1),(3,2))],
         start=(0,0,3,3), startKey=(CIRCLE, PINK),
         second=(0,2,3,8), secondKey=(CIRCLE, PINK),
         tiles=[(1,1,6,6,"s",SQUARE), (2,1,6,6,"c",CYAN), (0,1,3,3,"s",TRI), (2,2,8,8,"c",GOLD)],
         doors=[((2,0),(3,0),SQUARE,CYAN)],
         gates=[((0,0),(0,1),(4, 5))],
         exit=(3,2,8,6,TRI,GOLD),
         marks=[(1,0,3,3,4), (2,0,8,8,5), (0,0,8,8,0), (0,1,8,3,1), (0,2,3,3,2), (1,1,3,8,6), (1,2,6,6,7), (2,1,3,3,8), (2,2,3,8,9), (3,0,6,6,10), (3,1,3,3,11)],
         gear=[(0,1,6,3,BOOTS,0), (1,2,8,4,BLADE,0), (2,2,4,9,ANCHOR,0), (0,2,8,5,BOOTS,1), (3,1,8,3,BLADE,1)],
         rubble=[(1,1,5,5), (1,1,6,5), (2,2,7,4), (0,2,8,8)],
         props=[(0,0,5,9,"#ffd400"), (1,0,4,8,"#ff6a00"), (2,1,7,7,"#ff2d95"), (1,2,8,3,"#00e5ff"), (3,1,6,6,"#b14bff"), (0,1,4,9,"#9dff3c")],
         foes=[(1,0,2,9,1,0,8,HOSTILE), (2,1,2,2,0,1,8,HOSTILE), (1,2,2,6,1,0,8,HOSTILE), (0,1,6,2,0,1,8,HOSTILE), (1,2,4,4,0,1,6,WARDEN), (2,0,5,1,0,1,8,HOSTILE)]),
    dict(cols=4, rows=4, roomW=12, roomH=12, gap=3,
         links=[((0,0),(1,0)), ((1,0),(2,0)), ((1,0),(1,1)), ((0,0),(0,1)), ((0,1),(0,2)), ((0,2),(0,3)), ((0,3),(1,3)), ((1,3),(2,3)), ((2,2),(2,3)), ((2,1),(2,2)), ((2,0),(3,0)), ((3,0),(3,1)), ((3,1),(3,2)), ((3,2),(3,3))],
         start=(0,0,3,3), startKey=(CIRCLE, PINK),
         second=(0,3,3,8), secondKey=(CIRCLE, PINK),
         tiles=[(1,1,6,6,"s",TRI), (2,1,6,6,"c",GOLD), (0,2,3,3,"s",SQUARE), (1,3,6,6,"c",CYAN), (2,2,8,8,"c",PINK), (0,1,8,8,"s",CIRCLE)],
         doors=[((2,0),(3,0),TRI,GOLD), ((3,1),(3,2),SQUARE,CYAN)],
         gates=[((0,0),(0,1),(4, 5, 6))],
         exit=(3,3,8,6,CIRCLE,PINK),
         marks=[(1,0,3,3,4), (2,0,8,8,5), (1,1,3,8,6), (0,0,8,8,0), (0,1,3,3,1), (0,2,8,8,2), (0,3,8,3,7), (1,3,3,3,8), (2,1,3,8,9), (2,2,3,3,10), (2,3,8,8,11), (3,0,6,6,12), (3,1,3,3,13)],
         gear=[(0,1,4,4,BOOTS,0), (1,1,7,7,BLADE,0), (2,2,6,6,ANCHOR,0), (1,3,3,9,BLADE,0), (0,2,8,3,ANCHOR,1), (2,3,8,5,BOOTS,1)],
         rubble=[(0,2,5,6), (0,2,6,6), (2,2,4,8), (1,3,8,4), (2,1,6,9)],
         props=[(0,0,8,9,"#ffd400"), (1,0,4,4,"#ff6a00"), (2,1,7,4,"#ff2d95"), (0,3,6,6,"#00e5ff"), (2,3,4,9,"#b14bff"), (3,0,5,5,"#9dff3c")],
         foes=[(1,0,2,9,1,0,8,HOSTILE), (2,1,2,2,0,1,8,HOSTILE), (0,2,6,2,0,1,8,HOSTILE), (2,3,2,6,1,0,8,HOSTILE), (0,1,6,2,0,1,8,HOSTILE), (2,3,4,4,0,1,6,WARDEN), (1,0,4,7,0,1,4,WARDEN), (2,0,5,1,0,1,8,HOSTILE)]),
    dict(cols=5, rows=4, roomW=12, roomH=12, gap=3,
         links=[((0,0),(1,0)), ((1,0),(2,0)), ((1,0),(1,1)), ((0,0),(0,1)), ((0,1),(0,2)), ((0,2),(0,3)), ((0,3),(1,3)), ((1,3),(2,3)), ((2,2),(2,3)), ((2,1),(2,2)), ((2,0),(3,0)), ((3,0),(4,0)), ((3,0),(3,1)), ((3,1),(3,2)), ((3,2),(3,3)), ((4,0),(4,1)), ((4,1),(4,2)), ((4,2),(4,3))],
         start=(0,0,3,3), startKey=(CIRCLE, PINK),
         second=(0,3,3,8), secondKey=(CIRCLE, PINK),
         tiles=[(1,1,6,6,"s",SQUARE), (2,2,6,6,"c",CYAN), (0,2,3,3,"c",GOLD), (1,3,6,6,"s",TRI), (2,1,8,8,"c",PINK), (0,1,8,3,"s",CIRCLE)],
         doors=[((2,0),(3,0),SQUARE,CYAN), ((3,0),(4,0),TRI,GOLD)],
         gates=[((0,0),(0,1),(4, 5, 6))],
         exit=(4,2,8,6,CIRCLE,PINK),
         marks=[(1,0,3,3,4), (2,0,8,8,5), (1,1,3,8,6), (0,0,8,8,0), (0,1,3,3,1), (0,2,8,8,2), (0,3,8,3,7), (1,3,3,3,8), (2,1,3,3,9), (2,2,8,3,10), (2,3,3,8,11), (3,0,3,3,12), (3,1,8,8,13), (4,0,6,6,14), (4,1,3,3,15)],
         gear=[(0,1,4,9,BOOTS,0), (1,1,8,4,BLADE,0), (2,2,4,4,ANCHOR,0), (1,3,8,8,BLADE,0), (3,1,5,5,ANCHOR,0), (0,2,8,5,BOOTS,1), (2,3,5,3,BLADE,1), (4,1,8,8,ANCHOR,1)],
         rubble=[(0,2,5,7), (0,2,6,7), (1,3,4,5), (2,1,7,8), (3,2,6,6), (2,2,9,3)],
         props=[(0,0,8,9,"#ffd400"), (1,0,4,4,"#ff6a00"), (2,1,5,3,"#ff2d95"), (0,3,6,6,"#00e5ff"), (2,3,8,4,"#b14bff"), (4,1,6,6,"#9dff3c"), (3,0,8,8,"#ff4f6d")],
         foes=[(1,0,2,9,1,0,8,HOSTILE), (2,1,2,2,0,1,8,HOSTILE), (0,2,6,2,0,1,8,HOSTILE), (2,3,2,6,1,0,8,HOSTILE), (3,1,2,9,1,0,8,HOSTILE), (0,1,6,2,0,1,8,HOSTILE), (2,3,4,4,0,1,6,WARDEN), (1,0,4,7,0,1,4,WARDEN), (3,1,4,7,0,1,4,WARDEN), (3,0,5,1,0,1,8,HOSTILE)]),
]


class World:

    def __init__(self, spec: dict) -> None:
        P, Q = spec["roomW"] + spec["gap"], spec["roomH"] + spec["gap"]
        self.rx = lambda c: 1 + c * P
        self.ry = lambda r: 1 + r * Q
        self.w = 2 + (spec["cols"] - 1) * P + spec["roomW"]
        self.h = 2 + (spec["rows"] - 1) * Q + spec["roomH"]

        rects = []
        for r in range(spec["rows"]):
            for c in range(spec["cols"]):
                rects.append((self.rx(c), self.ry(r), spec["roomW"], spec["roomH"]))
        for (c1, r1), (c2, r2) in spec["links"]:
            if r1 == r2:
                rects.append((self.rx(c1) + spec["roomW"],
                              self.ry(r1) + spec["roomH"] // 2 - 1, spec["gap"], 2))
            else:
                rects.append((self.rx(c1) + spec["roomW"] // 2 - 1,
                              self.ry(r1) + spec["roomH"], 2, spec["gap"]))

        self.grid = [["#"] * self.w for _ in range(self.h)]
        for x, y, w, h in rects:
            for j in range(y, y + h):
                for i in range(x, x + w):
                    if 0 <= j < self.h and 0 <= i < self.w:
                        self.grid[j][i] = "."

        at = lambda c, r, x, y: (self.rx(c) + x, self.ry(r) + y)

        def hall_mid(a, b):
            (c1, r1), (c2, r2) = a, b
            if r1 == r2:
                return (self.rx(c1) + spec["roomW"] + spec["gap"] // 2,
                        self.ry(r1) + spec["roomH"] // 2 - 1, True)
            return (self.rx(c1) + spec["roomW"] // 2 - 1,
                    self.ry(r1) + spec["roomH"] + spec["gap"] // 2, False)

        self.start = at(*spec["start"][:2], *spec["start"][2:])
        self.start_key = list(spec["startKey"])
        self.second = at(*spec["second"][:2], *spec["second"][2:]) if "second" in spec else None
        self.second_key = list(spec.get("secondKey", spec["startKey"]))

        self.tiles = {}
        for c, r, x, y, fam, val in spec["tiles"]:
            self.tiles[at(c, r, x, y)] = (fam, val)

        self.doors = {}
        for a, b, s, col in spec["doors"]:
            mx, my, horiz = hall_mid(a, b)
            cells = [(mx, my), (mx, my + 1)] if horiz else [(mx, my), (mx + 1, my)]
            for cc in cells:
                self.doors[cc] = (s, col)
        self.gates = {}
        for a, b, need in spec["gates"]:
            mx, my, horiz = hall_mid(a, b)
            cells = [(mx, my), (mx, my + 1)] if horiz else [(mx, my), (mx + 1, my)]
            for cc in cells:
                self.gates[cc] = tuple(need)

        self.marks = {}
        for c, r, x, y, g in spec["marks"]:
            self.marks[at(c, r, x, y)] = g

        ex = spec["exit"]
        self.exit = at(ex[0], ex[1], ex[2], ex[3])
        self.exit_key = (ex[4], ex[5])

        for cc in list(self.doors) + list(self.gates) + [self.exit]:
            self.grid[cc[1]][cc[0]] = "."

        self.foes = []
        for c, r, x, y, dx, dy, ln, kind in spec["foes"]:
            ox, oy = at(c, r, x, y)
            self.foes.append(dict(ox=ox, oy=oy, dx=dx, dy=dy, ln=ln, kind=kind))

        self.gear = [dict(pos=at(c, r, x, y), kind=k, cursed=bool(cu))
                     for c, r, x, y, k, cu in spec.get("gear", [])]
        self.rubble = {at(c, r, x, y) for c, r, x, y in spec.get("rubble", [])}
        self.props = [dict(pos=at(c, r, x, y), hue=PROP_HUE[i % len(PROP_HUE)])
                      for i, (c, r, x, y, _hex) in enumerate(spec.get("props", []))]

        used = ({self.start, self.exit} | set(self.tiles) | set(self.marks)
                | set(self.rubble) | {gp["pos"] for gp in self.gear}
                | {q["pos"] for q in self.props}
                | {(f["ox"] + f["dx"] * k, f["oy"] + f["dy"] * k)
                   for f in self.foes for k in range(f["ln"] + 1)})
        if self.second:
            used.add(self.second)
        self.nooks = []
        for r in range(spec["rows"]):
            for c in range(spec["cols"]):
                x0, y0 = self.rx(c), self.ry(r)
                x1, y1 = x0 + spec["roomW"] - 1, y0 + spec["roomH"] - 1
                for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1),
                                       (x0, y1, 1, -1), (x1, y1, -1, -1)):
                    cell = (cx, cy)
                    if not any((cx + a, cy + b) in used
                               for a in (-1, 0, 1) for b in (-1, 0, 1)):
                        self.nooks.append(cell)
        for x, y in self.nooks:
            self.grid[y][x] = "#"

    def solid(self, x: int, y: int) -> bool:
        return not (0 <= x < self.w and 0 <= y < self.h) or self.grid[y][x] == "#"


WORLDS = [World(s) for s in SPECS]


def build_levels() -> list[Level]:
    levels = []
    for wd in WORLDS:
        sprites = [Sprite(pixels=[[VOID] * CELL] * CELL, name="body0",
                          blocking=BlockingMode.NOT_BLOCKED,
                          interaction=InteractionMode.INTANGIBLE, layer=1)
                   .set_position(wd.start[0] * CELL, wd.start[1] * CELL)]
        if wd.second:
            sprites.append(Sprite(pixels=[[VOID] * CELL] * CELL, name="body1",
                                  blocking=BlockingMode.NOT_BLOCKED,
                                  interaction=InteractionMode.INTANGIBLE, layer=1)
                           .set_position(wd.second[0] * CELL, wd.second[1] * CELL))
        levels.append(Level(sprites=sprites))
    return levels



# ---- the static art map ---------------------------------------------------------------------------
# The world is bigger than the camera and is painted from the model, so everything that never changes
# (meadow, brick, moat base, great trees, boulders, patrol trails) is painted once per world into one
# pixel map and cropped each frame at a pixel offset, which is what lets the slide between cells be smooth.
# Doors, gates, runes, creatures and anything that moves, sways or lights are drawn over it every frame.
_ART: dict = {}


def _sig(wd) -> tuple:
    return (wd.w, wd.h, tuple(sorted(wd.marks)), tuple(sorted(wd.tiles)))


# A world is found by what is in it, not by identity: Undo deep-copies the whole game, World included.
# (Size, start and exit are not enough: worlds three and four share all of them and differ in their halls.)
_WORLD_NO = {_sig(w): i for i, w in enumerate(WORLDS)}


def _art_key(wd) -> int:
    return _WORLD_NO[_sig(wd)]


def _put(img, x: int, y: int, sprite) -> None:
    """Stamp a list-of-rows sprite into a numpy map; -1 is clear."""
    for r, row in enumerate(sprite):
        for c, v in enumerate(row):
            if v >= 0:
                img[y + r, x + c] = v


def art_for(wd) -> dict:
    key = _art_key(wd)
    art = _ART.get(key)
    if art is None:
        art = _ART[key] = _build_art(wd)
    return art


def lane_cells(wd) -> dict:
    """Every cell a patrol walks, with the step number along its lane (for the footprints)."""
    out: dict = {}
    for f in wd.foes:
        for t in range(f["ln"] + 1):
            out.setdefault((f["ox"] + f["dx"] * t, f["oy"] + f["dy"] * t), t)
    return out


def _build_art(wd) -> dict:
    theme = THEMES[_art_key(wd) % len(THEMES)]
    img = np.full((wd.h * CELL, wd.w * CELL), VOID, dtype=np.uint8)
    solid = wd.solid
    salt = wd.w * 31 + wd.h
    nooks = set(wd.nooks)
    lanes = lane_cells(wd)

    def wall(x: int, y: int) -> bool:
        """Solid for the purposes of drawing brick: a tree in an unused room corner is floor to the wall."""
        return solid(x, y) and (x, y) not in nooks
    busy = (set(wd.tiles) | set(wd.marks) | set(wd.doors) | set(wd.gates) | {wd.exit, wd.start}
            | {gp["pos"] for gp in wd.gear} | wd.rubble | {q["pos"] for q in wd.props} | set(lanes))
    if wd.second:
        busy.add(wd.second)
    torches, glints, decor = {}, {}, {}
    for wy in range(wd.h):
        for wx in range(wd.w):
            X, Y = wx * CELL, wy * CELL
            if solid(wx, wy):
                if (wx, wy) in nooks:
                    # An unused room corner holds a great tree.
                    img[Y:Y + CELL, X:X + CELL] = FLOOR
                    _put(img, X, Y, tree(FLOOR))
                    continue
                near = any(not wall(wx + a, wy + b) for a in (-1, 0, 1) for b in (-1, 0, 1))
                if not near:
                    # Dead space between rooms is a moat: a flat base, a few things, a few glints.
                    img[Y:Y + CELL, X:X + CELL] = theme["base"]
                    for n, (kind, mod) in enumerate(theme["deco"]):
                        if _hash(wx, wy, salt + 7 * n + 3) % mod == 0:
                            decor[(wx, wy)] = kind
                            break
                    else:
                        k = _hash(wx, wy, salt)
                        if k % 3 == 0:
                            glints[(wx, wy)] = ((k >> 3) % CELL, (k >> 6) % CELL)
                    continue
                _put(img, X, Y, brick(BRICK, WALL, wy))
                # Convex corners step down onto the floor.
                for dx, dy, px, py in CORNERS:
                    if not wall(wx + dx, wy) and not wall(wx, wy + dy):
                        img[Y + py:Y + py + 2, X + px:X + px + 2] = FLOOR
                # Room corners outside: a small castle tower.
                for dx, dy in ((-1, 1), (1, 1)):          # only the two top corners of a room
                    if not wall(wx + dx, wy + dy) and wall(wx + dx, wy) and wall(wx, wy + dy):
                        _put(img, X, Y, tower(theme["roof"]))
                        break
                else:
                    if not wall(wx, wy + 1) and _hash(wx, wy, salt + 1) % 6 == 0:
                        torches[(wx, wy)] = True
                continue
            img[Y:Y + CELL, X:X + CELL] = FLOOR
            for dx, dy, px, py in CORNERS:
                if wall(wx + dx, wy) and wall(wx, wy + dy):
                    img[Y + py:Y + py + 2, X + px:X + px + 2] = WALL
            if (wx, wy) in wd.rubble:
                _put(img, X, Y, boulder(RUBBLE, RUBBLE_LIGHT))
            elif (wx, wy) in lanes:
                # Where a patrol walks the ground is worn: a pair of footprints a step.
                t = lanes[(wx, wy)] % 2
                img[Y + 2 + t, X + 1 + 3 * t] = BRICK
                img[Y + 3 + t, X + 2 + 3 * t] = BRICK
            elif (wx, wy) not in busy and _hash(wx, wy, salt + 11) % 9 == 0:
                # A flat mark on the meadow; where it sits inside the cell varies.
                k = _hash(wx, wy, salt + 13)
                kind = theme["floor"][k % len(theme["floor"])]
                _put(img, X + 1 + (k >> 3) % 2, Y + 1 + (k >> 5) % 2, FLAT[kind]())
    return dict(img=img, torches=torches, glints=glints, decor=decor, theme=theme)


def _gate_slab(wd, cell, table) -> tuple:
    """Which half of its two-cell slab this cell is, which way the slab lies across the hall, and the
    partner cell. Returns (index 0/1, vertical, partner) where vertical means the two cells are stacked."""
    x, y = cell
    if (x, y + 1) in table:
        return 0, True, (x, y + 1)
    if (x, y - 1) in table:
        return 1, True, (x, y - 1)
    if (x + 1, y) in table:
        return 0, False, (x + 1, y)
    return 1, False, (x - 1, y)


def portcullis(needs, lit, half: int, vertical: bool) -> list[list[int]]:
    """One half (6x6) of the gate across a hall: black bars with grey rails, a stud per rune it waits on. An
    unlit stud is dark with a dot of its rune's colour; a lit one is the rune's full colour."""
    big = [[VOID] * 6 for _ in range(12)]                   # across x along, then turned if needed
    for r in range(12):
        big[r][0] = 4
        big[r][5] = 4
    n = min(3, len(needs))
    starts = {1: (5,), 2: (2, 8), 3: (1, 5, 9)}[n]
    for need, s in zip(needs, starts):
        hue = rune_hue(need)
        for dy in range(2):
            for dx in range(2):
                big[s + dy][2 + dx] = hue if need in lit else 4
        if need not in lit:
            big[s][2] = hue
    rows = big[half * 6:half * 6 + 6]
    if vertical:
        return rows
    return [[rows[c][r] for c in range(6)] for r in range(6)]


def _door(hue: int, shape: int, edges) -> list[list[int]]:
    """A lock: the key's colour, a black frame where it meets brick, the shape's black glyph."""
    px = [[hue] * 6 for _ in range(6)]
    top, bottom, left, right = edges
    for k in range(6):
        if top:
            px[0][k] = VOID
        if bottom:
            px[5][k] = VOID
        if left:
            px[k][0] = VOID
        if right:
            px[k][5] = VOID
    for x, y in glyph_cells(GLYPH4, shape):
        px[1 + y][1 + x] = VOID
    return px


def _exit(hue: int, shape: int) -> list[list[int]]:
    """The doorway out: a frame in the key's colour round a dark opening, the shape's glyph inside."""
    px = [[hue] * 6] + [[hue] + [VOID] * 4 + [hue] for _ in range(4)] + [[hue] * 6]
    for x, y in glyph_cells(GLYPH4, shape):
        px[1 + y][1 + x] = hue
    return px


def _clip_stamp(buf, x: int, y: int, sprite, box) -> None:
    """Paint a sprite but only inside the pixel box (x0, y0, x1, y1), so a lifting gate rises into its frame."""
    bx0, by0, bx1, by1 = box
    for r, row in enumerate(sprite):
        for c, v in enumerate(row):
            px, py = x + c, y + r
            if v >= 0 and bx0 <= px < bx1 and by0 <= py < by1 and 0 <= px < SCREEN and 0 <= py < SCREEN:
                buf[py, px] = v


def _ring(buf, cx: int, cy: int, r: int, colours) -> None:
    """Eight points of a ring of radius r (a pop, a pulse, a puff)."""
    pts = ((r, 0), (-r, 0), (0, r), (0, -r), (r - r // 3, r - r // 3), (-r + r // 3, r - r // 3),
           (r - r // 3, -r + r // 3), (-r + r // 3, -r + r // 3))
    for k, (dx, dy) in enumerate(pts):
        x, y = cx + dx, cy + dy
        if 0 <= x < SCREEN and 0 <= y < SCREEN:
            buf[y, x] = colours[k % len(colours)]


def _iris(buf, cx: int, cy: int, r: int) -> None:
    """Everything farther than r from (cx, cy) goes black."""
    ys, xs = np.ogrid[:SCREEN, :SCREEN]
    buf[(xs - cx) ** 2 + (ys - cy) ** 2 > r * r] = VOID


def _dim(buf, frac: float) -> None:
    """The lantern is running low: the edges of the world dither away, then go dark."""
    if frac > 0.25:
        return
    t = 2 if frac > 0.10 else 4
    ys, xs = np.mgrid[:SCREEN, :SCREEN]
    edge = np.minimum(np.minimum(xs, SCREEN - 1 - xs), np.minimum(ys, SCREEN - 1 - ys))
    buf[(edge < t) & ((xs + ys) % 2 == 0)] = VOID
    if frac <= 0.10:
        buf[edge < 1] = VOID


def _shape_pips(shape: int):
    return glyph_cells(GLYPH4, shape)


class Window(RenderableUserDisplay):

    def __init__(self, game: "Xa03") -> None:
        super().__init__()
        self._g = game

    def _lerp(self, cur, prev) -> tuple:
        """World pixel of something that was at cell prev and is now at cell cur, mid-slide."""
        g = self._g
        if prev is None or g.phase >= SETTLED:
            return cur[0] * CELL, cur[1] * CELL
        k = TWEEN[g.phase - 1]
        return (prev[0] * CELL + (cur[0] - prev[0]) * k, prev[1] * CELL + (cur[1] - prev[1]) * k)

    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        g = self._g
        wd = g.world
        ev = g.ev
        ph = g.phase
        anim = ph < SETTLED
        art = art_for(wd)
        theme = art["theme"]
        img = art["img"]
        pre = g.prev
        amb = g.beat + ph // 2                                   # scenery sways a little each frame

        buf = np.full((SCREEN, SCREEN), VOID, dtype=np.uint8)
        cx, cy = self._lerp((g.cam_x, g.cam_y), pre["cam"] if pre else None)
        x0, y0 = max(0, cx), max(0, cy)
        x1, y1 = min(img.shape[1], cx + SCREEN), min(img.shape[0], cy + SCREEN)
        if x1 > x0 and y1 > y0:
            buf[y0 - cy:y1 - cy, x0 - cx:x1 - cx] = img[y0:y1, x0:x1]

        gx0, gy0 = cx // CELL, cy // CELL
        cells = [(x, y) for y in range(gy0, gy0 + VIEW + 1) for x in range(gx0, gx0 + VIEW + 1)
                 if 0 <= x < wd.w and 0 <= y < wd.h]

        def at(cell) -> tuple:
            return cell[0] * CELL - cx, cell[1] * CELL - cy

        def blit(sprite, cell) -> None:
            sx, sy = at(cell)
            stamp(buf, sx, sy, sprite)

        def put_c(sprite, sx: int, sy: int) -> None:
            """Centre a sprite on a cell's width and stand it on the cell's bottom edge."""
            stamp(buf, sx + (CELL - len(sprite[0])) // 2, sy + CELL - len(sprite), sprite)

        # Scenery that sways or glints: torches in the brick, moat dressing, glints on the base.
        for cell in cells:
            if cell in art["torches"]:
                blit(wall_torch(amb + cell[0]), cell)
            elif cell in art["decor"]:
                blit(deco_sprite(art["decor"][cell], theme, amb + cell[0] + cell[1]), cell)
            elif cell in art["glints"]:
                if (amb + cell[0] + cell[1]) % 4 < 2:
                    px, py = art["glints"][cell]
                    sx, sy = at(cell)
                    if 0 <= sx + px < SCREEN and 0 <= sy + py < SCREEN:
                        buf[sy + py, sx + px] = theme["glint"]

        lit_now = ev.get("lit")
        opened_gates = set(ev.get("gates", ())) if anim else set()
        for cell in cells:
            tile = wd.tiles.get(cell)
            if tile:
                fam, val = tile
                blit(orb(KEY_HUE[val]) if fam == "c" else domino(val), cell)

            gnum = wd.marks.get(cell)
            if gnum is not None:
                burst = ph if (anim and lit_now == cell) else 0
                blit(brazier(rune_hue(gnum), gnum in g.lit, amb + cell[0], burst), cell)

            door = wd.doors.get(cell)
            if door:
                x, y = cell
                edges = (wd.solid(x, y - 1), wd.solid(x, y + 1), wd.solid(x - 1, y), wd.solid(x + 1, y))
                sprite = _door(KEY_HUE[door[1]], door[0], edges)
                if cell not in g.opened:
                    blit(sprite, cell)
                elif anim and ev.get("door") == cell:
                    width = max(0, CELL - 2 * ph)                 # the lock swings away on its hinge
                    blit([row[:width] + [-1] * (CELL - width) for row in sprite], cell)

            gate = wd.gates.get(cell)
            if gate:
                lifting = cell in opened_gates
                if not g.gate_open(gate) or lifting:
                    half, vertical, partner = _gate_slab(wd, cell, wd.gates)
                    sprite = portcullis(gate, g.lit, half, vertical)
                    sx, sy = at(cell)
                    if lifting:
                        # The slab rises into its own frame, then it is gone.
                        px_, py_ = at(partner)
                        box = (min(sx, px_), min(sy, py_), max(sx, px_) + CELL, max(sy, py_) + CELL)
                        _clip_stamp(buf, sx, sy - 2 * ph, sprite, box)
                    else:
                        stamp(buf, sx, sy, sprite)

            if cell == wd.exit:
                blit(_exit(KEY_HUE[wd.exit_key[1]], wd.exit_key[0]), cell)

        for i, q in enumerate(wd.props):
            bright = (amb % 2 == 0) if i == 0 else ((amb + i) % 4 < 2)
            blit(flower(q["hue"], bright), q["pos"])

        for gp in wd.gear:
            if id(gp) in g.taken:
                continue
            hue = GEAR_HUE[gp["kind"]]
            blit(self._gear_sprite(gp["kind"], hue), gp["pos"])

        # Creatures and bodies, back to front, so a head can overlap the cell above.
        actors = []
        prevfoes = pre["foes"] if pre else None
        for n, f in enumerate(g.foes):
            if id(f) in g.dead:
                continue
            prev = prevfoes[n] if prevfoes else None
            wx, wy = self._lerp((f["x"], f["y"]), prev)
            actors.append((wy, 0, n, wx, wy))
        prevb = pre["bodies"] if pre else None
        back = ev.get("back")
        for i, b in enumerate(g.bodies):
            wx, wy = self._lerp((b["x"], b["y"]), prevb[i] if prevb else None)
            if i == g.active:
                wy_hop = -HOP[ph - 1] if (anim and pre and ev.get("land")) else 0
                bump = ev.get("bump")
                if anim and bump:
                    k = (2, 3, 1)[ph - 1]
                    wx, wy = wx + bump[0] * k, wy + bump[1] * k
                wy += wy_hop
            actors.append((wy, 1, i, wx, wy))
        for _, kind, n, wx, wy in sorted(actors):
            sx, sy = wx - cx, wy - cy
            if kind == 0:
                f = g.foes[n]
                sgn = -1 if f["back"] else 1
                step = g.beat + (1 if ph >= 3 else 0)
                if f["kind"] == WARDEN:
                    put_c(guard(WARD_BODY, (f["dx"] * sgn, f["dy"] * sgn), step), sx, sy)
                else:
                    put_c(crab(FOE_BODY, step), sx, sy)
            else:
                if back and anim and ph < 3 and n == g.active:
                    continue                                  # gone in a puff, back a moment later
                b = g.bodies[n]
                awake = n == g.active
                frac = g.oil / g.budget
                flame = 3 if frac > 0.5 else 2 if frac > 0.25 else 1 if frac > 0.10 else 0
                wince = bool(anim and ev.get("bump") and awake)
                put_c(hero(BODY if awake else IDLE, g.face[n], awake, KEY_HUE[b["key"][1]], b["key"][0],
                           b["gear"], bool(b["curses"]), g._overloaded(b), flame, g.beat + ph // 2,
                           wince, g.beat + ph // 2), sx, sy)

        if anim:
            self._effects(buf, g, ev, ph, cx, cy, put_c)

        # Lantern low: the edges close in. Iris: the level is won, entered or lost.
        _dim(buf, g.oil / g.budget)
        me = g.bodies[g.active]
        mx, my = self._lerp((me["x"], me["y"]), pre["bodies"][g.active] if pre else None)
        hx, hy = mx - cx + CELL // 2, my - cy + CELL // 2
        if g.flash:
            _iris(buf, hx, hy, g.flash * 7)
        elif g.clear_pending:
            _iris(buf, hx, hy, 4)                             # closed on the winner
        elif g.opening:
            _iris(buf, hx, hy, (OPEN_FRAMES + 1 - g.opening) * 14)
        elif g.lost:
            _iris(buf, hx, hy, 4)
        elif g.dying:
            _iris(buf, hx, hy, g.dying * 8)

        ox = oy = 0
        if (anim and ev.get("back")) or g.dying:
            ox, oy = (1, 0) if (ph + g.dying) % 2 else (-1, 1)
        frame[:] = VOID
        frame[OFF + oy:OFF + oy + SCREEN, OFF + ox:OFF + ox + SCREEN] = buf
        return frame

    @staticmethod
    def _gear_sprite(kind: int, hue: int):
        return boot(hue) if kind == BOOTS else sword(hue, GEAR_HUE[BOOTS]) if kind == BLADE else anchor_shape(hue)

    def _effects(self, buf, g, ev, ph: int, cx: int, cy: int, put_c) -> None:
        """Short-lived things, drawn only on the animation frames of the action that caused them."""
        me = g.bodies[g.active]
        pre = g.prev
        mx, my = self._lerp((me["x"], me["y"]), pre["bodies"][g.active] if pre else None)
        hx, hy = mx - cx + CELL // 2, my - cy + CELL // 2          # the body's middle on screen
        feet = (hx, my - cy + CELL)

        if ev.get("land") and ph in (2, 3):                        # dust where it lands
            d = ph + 1
            for dx in (-d, d):
                for dy in (0, -1 if ph == 3 else 0):
                    x, y = feet[0] + dx, feet[1] - 1 + dy
                    if 0 <= x < SCREEN and 0 <= y < SCREEN:
                        buf[y, x] = 1
        pick = ev.get("pick")
        if pick:                                                   # the thing pops up into the hand
            kind, _cell = pick
            sprite = self._gear_sprite(kind, GEAR_HUE[kind])
            stamp(buf, hx - CELL // 2, my - cy - 3 - 3 * ph, sprite)
            _ring(buf, hx, my - cy - 2 * ph, 2 + ph, (11, 0))
        if "tile" in ev:                                           # a ring of the tile's colour runs onto the gem
            _ring(buf, hx, hy, 1 + 2 * ph, (ev["tile"],))
        if ev.get("swap"):
            _ring(buf, hx, hy, 2 + 2 * ph, (0, 11))
        for cell in ev.get("felled", ()):                          # a felled patrol bursts
            fx, fy = cell[0] * CELL - cx + CELL // 2, cell[1] * CELL - cy + CELL // 2
            _ring(buf, fx, fy, 1 + 2 * ph, (0, FOE_BODY, 11))
        back = ev.get("back")
        if back:                                                   # a puff where it was, another where it lands
            (ax, ay), (bx, by) = back
            _ring(buf, ax * CELL - cx + CELL // 2, ay * CELL - cy + CELL // 2, 1 + 2 * ph, (0, 1))
            if ph >= 2:
                _ring(buf, bx * CELL - cx + CELL // 2, by * CELL - cy + CELL // 2, 2 * (ph - 1), (0, 1))


class Xa03(ARCBaseGame):

    FLASH_FRAMES = IRIS_FRAMES

    def __init__(self) -> None:
        self.world = WORLDS[0]
        self.cam_x = self.cam_y = 0
        self.bodies = []
        self.active = 0
        self.opened = set()
        self.lit = set()
        self.foes = []
        self.flash = 0
        self.hit = 0
        self.beat = 0
        self.prev = None          # art only: where things stood before the move, while they slide
        self.phase = SETTLED      # art only: animation frame 1..3, SETTLED = at rest
        self.ev = {}              # art only: what the action did (bump, pickup, lit rune ...), for the painter
        self.face = [FACE_DOWN]
        self.oil = self.budget = BUDGETS[0]
        self.dying = 0            # frames of the run ending left to play
        self.lost = False
        self.opening = 0          # frames of the iris opening on a new world
        self.clear_pending = False
        camera = Camera(width=64, height=64, background=VOID, letter_box=VOID,
                        interfaces=[Window(self)])
        super().__init__(game_id="xa03", levels=build_levels(), camera=camera,
                         available_actions=[1, 2, 3, 4, 5])
        self._enter(0)

    def _enter(self, index: int) -> None:
        wd = self.world = WORLDS[index]
        self.bodies = [dict(x=wd.start[0], y=wd.start[1], key=list(wd.start_key),
                            gear=[], curses=[])]
        if wd.second:
            self.bodies.append(dict(x=wd.second[0], y=wd.second[1],
                                    key=list(wd.second_key), gear=[], curses=[]))
        self.taken = set()
        self.dead = set()
        self.active = 0
        self.opened = set()
        self.lit = set()
        self.lit_order = []
        self.foes = [dict(x=f["ox"], y=f["oy"], ox=f["ox"], oy=f["oy"],
                          dx=f["dx"], dy=f["dy"], ln=f["ln"], t=0, back=False,
                          kind=f["kind"])
                     for i, f in enumerate(wd.foes)]
        self.flash = 0
        self.hit = 0
        self.prev = None
        self.phase = SETTLED
        self.ev = {}
        self.dying = 0
        self.lost = False
        self.budget = BUDGETS[index]
        self.oil = self.budget
        self.opening = OPEN_FRAMES if self.clear_pending else 0
        self.clear_pending = False
        self.face = [FACE_DOWN] * len(self.bodies)
        self._follow(snap=True)
        self._sync()

    def on_set_level(self, level: Level) -> None:
        self._enter(self.level_index)

    def level_reset(self) -> None:
        super().level_reset()
        self._enter(self.level_index)

    def full_reset(self) -> None:
        super().full_reset()
        self._enter(self.level_index)

    def _sync(self) -> None:
        for i, b in enumerate(self.bodies):
            found = self.current_level.get_sprites_by_name(f"body{i}")
            if found:
                found[0].set_position(b["x"] * CELL, b["y"] * CELL)

    def _follow(self, snap: bool = False) -> None:
        me = self.bodies[self.active]
        self.cam_x = max(0, min(max(0, self.world.w - VIEW), me["x"] - VIEW // 2))
        self.cam_y = max(0, min(max(0, self.world.h - VIEW), me["y"] - VIEW // 2))
        self.camera.x = self.cam_x * CELL
        self.camera.y = self.cam_y * CELL

    def gate_open(self, need) -> bool:
        return all(n in self.lit for n in need)

    @staticmethod
    def _has(body, kind: int) -> bool:
        return kind in body["gear"]

    @staticmethod
    def _burden(body) -> int:
        return (sum(WEIGHT[k] for k in body["gear"])
                + len(body["curses"]) * CURSED_WEIGHT)

    def _overloaded(self, body) -> bool:
        return self._burden(body) > CARRY

    def passable(self, x: int, y: int, who: int) -> bool:
        wd = self.world
        if wd.solid(x, y):
            return False
        if (x, y) in wd.rubble and not self._has(self.bodies[who], BOOTS):
            return False
        door = wd.doors.get((x, y))
        if door and (x, y) not in self.opened:
            return tuple(self.bodies[who]["key"]) == door
        gate = wd.gates.get((x, y))
        if gate and not self.gate_open(gate):
            return False
        return True

    def _resolve_foes(self) -> None:
        for w in self.foes:
            if w["kind"] != WARDEN or id(w) in self.dead:
                continue
            for f in self.foes:
                if f is w or f["kind"] != HOSTILE or id(f) in self.dead:
                    continue
                if f["x"] == w["x"] and f["y"] == w["y"]:
                    self.dead.add(id(f))

    def _step_foes(self) -> None:
        for f in self.foes:
            if id(f) in self.dead:
                continue
            f["t"] += -1 if f["back"] else 1
            if f["t"] >= f["ln"]:
                f["t"] = f["ln"]
                f["back"] = True
            elif f["t"] <= 0:
                f["t"] = 0
                f["back"] = False
            nx, ny = f["ox"] + f["dx"] * f["t"], f["oy"] + f["dy"] * f["t"]
            if self.world.solid(nx, ny):
                f["back"] = not f["back"]
            else:
                f["x"], f["y"] = nx, ny

    def _caught(self) -> bool:
        me = self.bodies[self.active]
        for f in self.foes:
            if id(f) in self.dead or (f["x"], f["y"]) != (me["x"], me["y"]):
                continue
            if self._has(me, BLADE):
                self.dead.add(id(f))
                me["gear"] = [k for k in me["gear"] if k != BLADE]
                self.hit = 1
                return False
            return f["kind"] == HOSTILE
        return False

    def _send_back(self) -> None:
        me = self.bodies[self.active]
        wd = self.world
        came_from = (me["x"], me["y"])
        if self.lit_order:
            me["x"], me["y"] = self.lit_order[-1]
        elif self.active == 0 or not wd.second:
            me["x"], me["y"] = wd.start
        else:
            me["x"], me["y"] = wd.second
        if not self._has(me, ANCHOR):
            me["key"] = list(wd.start_key if self.active == 0 else wd.second_key)
        self.hit = 1
        self.ev["back"] = (came_from, (me["x"], me["y"]))
        self._follow(snap=True)

    # ---- art only: the animation frames ------------------------------------------------------------
    def _snap(self) -> dict:
        return dict(bodies=[(b["x"], b["y"]) for b in self.bodies],
                    foes=[(f["x"], f["y"]) for f in self.foes],
                    cam=(self.cam_x, self.cam_y),
                    dead=set(self.dead),
                    gates={c for c, n in self.world.gates.items() if self.gate_open(n)})

    def _arm(self, pre: dict) -> None:
        """Start the animation from the snapshot to where things are now. A slide runs when every mover
        went one cell at most (a send-back, a body swap across the map snaps instead); other events (a bump,
        a pickup, a lit rune, a lifted gate ...) animate in place. Never touches game state."""
        ev = self.ev
        ok, moved = not ev.get("back"), False
        pairs = list(zip(pre["bodies"], [(b["x"], b["y"]) for b in self.bodies]))
        pairs += list(zip(pre["foes"], [(f["x"], f["y"]) for f in self.foes]))
        pairs.append((pre["cam"], (self.cam_x, self.cam_y)))
        for (ax, ay), (bx, by) in pairs:
            if abs(bx - ax) > 1 or abs(by - ay) > 1 or abs(bx - ax) + abs(by - ay) > 2:
                ok = False
            moved = moved or (ax, ay) != (bx, by)
        opened = {c for c, n in self.world.gates.items() if self.gate_open(n)} - pre["gates"]
        if opened:
            ev["gates"] = sorted(opened)
        newly_dead = self.dead - pre["dead"]
        if newly_dead:
            ev["felled"] = [(f["x"], f["y"]) for f in self.foes if id(f) in newly_dead]
        if moved and ok:
            ev["land"] = True
        events = any(k in ev for k in ("bump", "pick", "tile", "lit", "gates", "door", "felled", "back", "swap"))
        if (ok and moved) or events:
            self.prev, self.phase = (pre if ok and moved else None), 1
        else:
            self.prev, self.phase = None, SETTLED

    def _finish(self, pre: dict) -> None:
        self._arm(pre)
        if self.oil <= 0 and not self.flash:
            self.dying = DYING_FRAMES                      # the lantern is out: the run is ending
        if self.phase >= SETTLED and not self.dying:
            self.complete_action()

    def step(self) -> None:
        if self.flash:
            self.flash -= 1
            self.phase = min(SETTLED, self.phase + 1)
            if self.flash == 0:
                self.clear_pending = True
                self.next_level()
                if not self._next_level:                    # the last world: the game is won
                    self.complete_action()
            return
        if self.opening:                                    # the iris opens on the next world
            self.opening -= 1
            if self.opening == 0:
                self.complete_action()
            return
        if self.phase < SETTLED:
            self.phase += 1
            if self.phase >= SETTLED and not self.dying:
                self.complete_action()
            return
        if self.dying:                                      # the lantern is out: the world closes in
            self.dying -= 1
            if self.dying == 0:
                self.lost = True
                self.lose()
                self.complete_action()
            return

        pre = self._snap()
        self.hit = 0
        self.beat += 1
        ev = self.ev = {}
        wd = self.world
        aid = self.action.id
        me = self.bodies[self.active]
        heading = {GameAction.ACTION1: FACE_UP, GameAction.ACTION2: FACE_DOWN,
                   GameAction.ACTION3: FACE_LEFT, GameAction.ACTION4: FACE_RIGHT}.get(aid)
        if heading is not None:
            self.face[self.active] = heading
        if aid in (GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3,
                   GameAction.ACTION4, GameAction.ACTION5):
            self.oil -= 1                                   # every action burns a drop of the lantern

        if aid == GameAction.ACTION5:
            if len(self.bodies) > 1:
                self.active = (self.active + 1) % len(self.bodies)
                ev["swap"] = True
            self._step_foes()
            self._resolve_foes()
            if self._caught():
                self._send_back()
            self._follow()
            self._sync()
            self._finish(pre)
            return

        delta = {GameAction.ACTION1: (0, -1), GameAction.ACTION2: (0, 1),
                 GameAction.ACTION3: (-1, 0), GameAction.ACTION4: (1, 0)}.get(aid)
        if delta is None:
            self._finish(pre)
            return
        nx, ny = me["x"] + delta[0], me["y"] + delta[1]

        other = next((i for i, b in enumerate(self.bodies)
                      if i != self.active and (b["x"], b["y"]) == (nx, ny)), None)
        if other is not None:
            self.active = other
            ev["swap"] = True
        elif any(f["kind"] == WARDEN and id(f) not in self.dead
                 and (f["x"], f["y"]) == (nx, ny) for f in self.foes) \
                and not self._has(me, BLADE):
            ev["bump"] = delta
        elif self.passable(nx, ny, self.active):
            door = wd.doors.get((nx, ny))
            if door and (nx, ny) not in self.opened:
                self.opened.add((nx, ny))
                ev["door"] = (nx, ny)
            me["x"], me["y"] = nx, ny
            tile = wd.tiles.get((nx, ny))
            if tile:
                fam, val = tile
                me["key"][1 if fam == "c" else 0] = val
                ev["tile"] = KEY_HUE[val] if fam == "c" else 0
            for gp in wd.gear:
                if gp["pos"] == (nx, ny) and id(gp) not in self.taken:
                    self.taken.add(id(gp))
                    ev["pick"] = (gp["kind"], gp["pos"])
                    if gp["cursed"]:
                        me["curses"].append(gp["kind"])
                    elif gp["kind"] not in me["gear"]:
                        me["gear"].append(gp["kind"])
            gnum = wd.marks.get((nx, ny))
            if gnum is not None and gnum not in self.lit:
                self.lit.add(gnum)
                self.lit_order.append((nx, ny))
                ev["lit"] = (nx, ny)
            if (nx, ny) == wd.exit and tuple(me["key"]) == wd.exit_key:
                self.flash = self.FLASH_FRAMES
                self._follow()
                self._sync()
                self._arm(pre)
                return
        else:
            ev["bump"] = delta

        if self._caught():
            self._send_back()
        else:
            self._step_foes()
            self._resolve_foes()
            if self._caught():
                self._send_back()
            elif self._overloaded(me):
                self._step_foes()
                self._resolve_foes()
                if self._caught():
                    self._send_back()
        self._follow()
        self._sync()
        self._finish(pre)
