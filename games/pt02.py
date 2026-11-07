# Author: Claude Sonnet 5.5
# Date: 07-November-2026
# PURPOSE: pt02, a redraw of pt01 (Perfect Target, the turn-based ship game with eight levels and enemy fire on a fixed
#          script). The RULES ARE UNCHANGED: every level's sea, ships, scripts, hit points, hearts, win and loss are the
#          same functions copied from pt01 (Spec, trace_shot, advance), and the engine glue plays the same pictures at the
#          same moments. What is new is all picture: every ship is a named sprite with a face on its bow and a sail, every
#          level is its own place (a sunny cove, a meadow archipelago, a snowfield, a canyon strait, a volcano, a jungle,
#          a night harbour, a ruined temple) with its own shoreline, props and living things, the lanes and aim line are
#          sprites, the strip along the bottom is built from named sprites (hearts and one small ship per enemy afloat),
#          and winning a level or sinking now has its own drawn feedback.
# SRP/DRY check: Pass. Part one is the rules, pure and picture-free (copied unchanged from pt01). Part two is the colour
#          palette and the small drawing helpers. Part three is the ship, heart, effect and creature pictures (text rows).
#          Part four builds each level's backdrop, shoreline and land. Part five is the game class: it owns the state and the
#          sprites and only ever reads the rules.
#
# CHANGELOG
# 07-Nov-2026 (Claude Sonnet 5.5): pass four, polish. The loud purple pools in the water are gone (second water colours are now
#          soft green, sky or blue, mostly in a dotted edge) and the volcano and night seas no longer wash purple, so the ships
#          stand out at a glance. Unused import removed. Rules untouched.
# 07-Nov-2026 (Claude Sonnet 5.5): pass three, variety and life. A big landmark drawn over two land cells in every sea (beach
#          house with a chimney, windmill, igloo, rock beacon, volcano, totem, lighthouse with a sweeping beam, colossus), a
#          second water colour pooling in the deep, sliding cloud shadows, a new set of small props per level, a second
#          kind of weather per level, a second swimmer, a bear on an ice floe, buoys, kelp and resting gulls, glittering
#          ground, redrawn dolphin, whale and strip ships, a clean dark-red frame with drifting wreckage when a run is lost
#          and a confetti shower when a level is won. Rules untouched.
# 07-Nov-2026 (Claude Sonnet 5.5): pass two of the art. Soft light patches and drifting wave marks in the deep water, a
#          breathing surf, big per-level things lying in the sea (reefs, reeds, lilies, floes, a whirlpool, a moon's path,
#          sunken stones), weather per level, foam wakes under every ship, blinking faces, own sail colours, richer ground
#          and prop pictures, a lighter red-tinged loss look with gloating enemies, confetti cheer. Rules untouched.
# 07-Nov-2026 (Claude Sonnet 5.5): first version of pt02, the art-only rebuild of pt01 (rules byte-for-byte the same).
"""pt02 (game source).

Four arrow keys move your ship one sea cell, the fifth action fires a ball straight ahead. Enemy fire follows a fixed
script and every volley is drawn one action before it lands (red dashes show the lane; a gun that glows red fires on the
next action). Hit a ship on the stern to damage it; the bow or flank throws the ball back at you. Sink every enemy ship.
"""

import math
from math import gcd

import numpy as np
from arcengine import ARCBaseGame, BlockingMode, Camera, GameAction, InteractionMode, Level, Sprite

# ════════════════════════════════════════════════════════════════════════════════════════════════════
# PART ONE: THE RULES. Copied unchanged from pt01. Nothing in this part draws.
# ════════════════════════════════════════════════════════════════════════════════════════════════════

# ── geometry ──────────────────────────────────────────────────────────────────
CELL = 7                 # screen pixels per sea cell
GW, GH = 9, 8            # sea is 9 columns by 8 rows: 63 by 56 pixels
HUD_Y = GH * CELL        # the black strip below the sea starts here

N, E, S, W = 0, 1, 2, 3  # headings, clockwise
DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)
DIR_OF_ACTION = {1: N, 2: S, 3: W, 4: E}
FACING_CHAR = {"N": N, "E": E, "S": S, "W": W}

HEARTS = 3

# ── ship kinds: which guns each carries (relative to its heading: 0 bow, 1 starboard, 3 port) ──
KIND_GUNS = {
    "m": (),             # merchant: no guns
    "c": (0,),           # corvette: bow gun
    "f": (1, 3),         # frigate: broadside, both flanks
    "g": (0, 1, 3),      # galleon: bow and both flanks
}



# ── levels ────────────────────────────────────────────────────────────────────
# rows: '.' sea, '#' land, 'P' where you start, a..h an enemy ship (listed in `ships`).
# ships: letter -> (kind, heading, hit points, script). Script letters, one per action:
#   '.' rest   'F' fire the guns   'R' turn a quarter clockwise   'L' turn a quarter anticlockwise
LEVEL_DEFS = [
    dict(  # 1  a merchant docked in a cove
        rows=(".........",
              "....###..",
              ".....a##.",
              "....###..",
              ".........",
              ".........",
              ".P.......",
              "#........"),
        face="N", hearts=False,
        ships={"a": ("m", "E", 1, ".")},
    ),
    dict(  # 2  three merchantmen, two of them back to back
        rows=("....P....",
              ".........",
              "#........",
              "...a.....",
              "....b....",
              ".......##",
              "....c...#",
              "........."),
        face="S",
        ships={"a": ("m", "N", 3, "."), "b": ("m", "N", 3, "."), "c": ("m", "S", 3, ".")},
    ),
    dict(  # 3  four merchantmen among the islands
        rows=("........P",
              "..###....",
              "..##.....",
              "....#c...",
              "....#....",
              ".........",
              "....a..d.",
              "b........"),
        face="W",
        ships={"a": ("m", "S", 2, "."), "b": ("m", "W", 1, "."), "c": ("m", "W", 3, "."), "d": ("m", "N", 2, ".")},
    ),
    dict(  # 4  the strait: a corvette covers the only way through
        rows=("....#....",
              "....#.b..",
              "....#....",
              "..a.#....",
              ".P..#....",
              "....#....",
              "......c..",
              "....#...."),
        face="N",
        ships={"a": ("m", "N", 2, "."), "b": ("m", "W", 3, "."), "c": ("c", "W", 2, "...F")},
    ),
    dict(  # 5  two corvettes on different beats guard the way round the islands
        rows=(".....a...",
              "..b...d..",
              "....###..",
              ".....#...",
              "...##..c.",
              "...#.....",
              "...##...P",
              "........."),
        face="E",
        ships={"a": ("c", "N", 2, "....F."), "b": ("c", "E", 2, "..F..."), "c": ("m", "E", 2, "."), "d": ("m", "W", 2, ".")},
    ),
    dict(  # 6  ships that turn: a corvette and a merchant swing round, a frigate fires from both flanks
        rows=("...#a....",
              "..P#.....",
              ".........",
              "......#..",
              ".#######.",
              "...d.....",
              ".b.......",
              "..c......"),
        face="S",
        ships={"a": ("c", "N", 2, "..FR"), "b": ("f", "E", 2, "..F."), "c": ("m", "E", 3, "..R."), "d": ("m", "W", 3, ".")},
    ),
    dict(  # 7  everything at once: a column of turning merchantmen, a frigate, a corvette
        rows=(".........",
              ".c...#...",
              ".e...#...",
              ".d...##..",
              ".P...#...",
              "...##..b.",
              "...#.....",
              "....a...."),
        face="E",
        ships={"a": ("c", "S", 2, "..F."), "b": ("f", "N", 2, "..F."), "c": ("m", "W", 2, "..R."),
               "d": ("m", "S", 3, "."), "e": ("m", "E", 3, "..R.")},
    ),
    dict(  # 8  the same sea with a galleon added beside the frigate: bow gun and both flanks, three lamps
        rows=(".........",
              ".c...#...",
              ".e...#...",
              ".d...##..",
              ".P...#.f.",
              "...##..b.",
              "...#.....",
              "....a...."),
        face="E",
        ships={"a": ("c", "S", 2, "..F."),
               "b": ("f", "N", 2, "..F."),
               "c": ("m", "W", 2, "..R."),
               "d": ("m", "S", 3, "."),
               "e": ("m", "E", 3, "..R."),
               "f": ("g", "E", 3, "..F.....")},
    ),
]


class Spec:
    """One level's fixed facts, parsed once."""

    def __init__(self, d):
        rows = d["rows"]
        assert len(rows) == GH and all(len(r) == GW for r in rows), "level rows must be 9 by 8"
        self.land = set()
        self.start = None
        pos = {}
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == "#":
                    self.land.add((x, y))
                elif ch == "P":
                    self.start = (x, y)
                elif ch != ".":
                    pos[ch] = (x, y)
        assert self.start is not None, "no start"
        self.pface = FACING_CHAR[d["face"]]
        self.hud_hearts = d.get("hearts", True)
        order = sorted(pos)
        self.n = len(order)
        self.kind, self.cell, self.hp0, self.script, self.head0 = [], [], [], [], []
        for ch in order:
            kind, head, hp, script = d["ships"][ch]
            self.kind.append(kind)
            self.cell.append(pos[ch])
            self.hp0.append(hp)
            self.script.append(script)
            self.head0.append(FACING_CHAR[head])
        self.ship_at = {c: i for i, c in enumerate(self.cell)}
        self.guns = [KIND_GUNS[k] for k in self.kind]
        # the repeating timeline of every ship, over one common cycle
        cyc = 1
        for sc in self.script:
            net = (sc.count("R") - sc.count("L")) % 4
            orbit = 4 // gcd(4, net) if net else 1
            per = len(sc) * orbit
            cyc = cyc * per // gcd(cyc, per)
        self.cycle = cyc
        self.head, self.armed = [], []
        for i in range(self.n):
            sc = self.script[i]
            h = self.head0[i]
            heads, arms = [], []
            for t in range(cyc):
                tok = sc[t % len(sc)]
                heads.append(h)
                arms.append(tok == "F" and bool(self.guns[i]))
                if tok == "R":
                    h = (h + 1) % 4
                elif tok == "L":
                    h = (h - 1) % 4
            self.head.append(heads)
            self.armed.append(arms)
        self.sea = {(x, y) for x in range(GW) for y in range(GH)} - self.land

    def initial(self):
        return (self.start[0], self.start[1], self.pface, HEARTS, 0, tuple(self.hp0))


SPECS = [Spec(d) for d in LEVEL_DEFS]


# ── the rules: one pure function, called once per action ─────────────────────

def _lane(spec, i, d, px, py, hps):
    """Cells a volley from ship i travels along heading d, and whether it reaches you."""
    cx, cy = spec.cell[i]
    cells = []
    while True:
        cx += DX[d]
        cy += DY[d]
        if (cx, cy) not in spec.sea:
            return cells, False
        if cx == px and cy == py:
            cells.append((cx, cy))
            return cells, True
        j = spec.ship_at.get((cx, cy))
        if j is not None and hps[j] > 0:
            return cells, False
        cells.append((cx, cy))


def trace_shot(spec, px, py, pf, hps, phi):
    """Where a ball fired from (px, py) along heading pf ends: (cells travelled, result, ship hit or -1).
    result: 'hit' (the stern), 'bounce' (bow or flank), 'wall' (land or the edge)."""
    cx, cy = px, py
    cells = []
    while True:
        cx += DX[pf]
        cy += DY[pf]
        if (cx, cy) not in spec.sea:
            return cells, "wall", -1
        j = spec.ship_at.get((cx, cy))
        cells.append((cx, cy))
        if j is not None and hps[j] > 0:
            return cells, ("hit" if spec.head[j][phi] == pf else "bounce"), j


def advance(spec, st, a, ev=None):
    """Apply one action. Returns (new state, status): 0 afloat, 1 level won, 2 your ship sinks.
    If `ev` is a list it is filled with what happened, for the picture."""
    px, py, pf, hearts, phi, hp = st
    hps = list(hp)
    if a in DIR_OF_ACTION:
        d = DIR_OF_ACTION[a]
        nx, ny = px + DX[d], py + DY[d]
        occupied = False
        j = spec.ship_at.get((nx, ny))
        if j is not None and hps[j] > 0:
            occupied = True
        if (nx, ny) in spec.sea and not occupied:
            if ev is not None:
                ev.append(("move", px, py, nx, ny, d))
            px, py = nx, ny
        else:
            if ev is not None:
                ev.append(("bump", px, py, d))
        pf = d
    elif a == 5:
        cells, result, tgt = trace_shot(spec, px, py, pf, hps, phi)
        if result == "hit":
            hps[tgt] -= 1
        if ev is not None:
            ev.append(("shot", px, py, pf, cells, result, tgt))
            if result == "hit" and hps[tgt] == 0:
                ev.append(("sink", tgt))
        if result == "bounce":
            # the armoured bow or flank throws the ball straight back at you
            hearts -= 1
            if ev is not None:
                ev.append(("ricochet", px, py))
            if hearts <= 0:
                return (px, py, pf, hearts, phi, tuple(hps)), 2
        if not any(hps):
            return (px, py, pf, hearts, phi, tuple(hps)), 1
    dmg = 0
    for i in range(spec.n):
        if hps[i] <= 0:
            continue
        if spec.armed[i][phi]:
            h = spec.head[i][phi]
            for g in spec.guns[i]:
                d = (h + g) % 4
                cells, hit = _lane(spec, i, d, px, py, hps)
                if hit:
                    dmg += 1
                if ev is not None:
                    ev.append(("volley", i, d, cells, hit))
        if ev is not None:
            h0 = spec.head[i][phi]
            h1 = spec.head[i][(phi + 1) % spec.cycle]
            if h0 != h1:
                ev.append(("turn", i, h0, h1))
    hearts -= dmg
    nxt = (phi + 1) % spec.cycle
    st2 = (px, py, pf, hearts, nxt, tuple(hps))
    if hearts <= 0:
        return st2, 2
    return st2, 0




# ════════════════════════════════════════════════════════════════════════════════════════════════════
# PART TWO: PALETTE AND SMALL DRAWING HELPERS
# ════════════════════════════════════════════════════════════════════════════════════════════════════

# The sixteen palette indices by name. Indexes 1 to 4 are greys and are never used for art here.
WHITE, BLACK, MAGENTA, PINK, RED, BLUE, SKY, YELLOW, ORANGE, MAROON, GREEN, PURPLE = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
CLEAR = -1               # a transparent pixel in a sprite

# What each kind of ship is made of: its hull (also its colour in the strip below), the darker edge, the light stripe.
HULL = {"m": ORANGE, "c": MAROON, "f": PURPLE, "g": MAGENTA}
EDGE = {"m": MAROON, "c": BLACK, "f": BLACK, "g": PURPLE}
GLEAM = {"m": YELLOW, "c": ORANGE, "f": SKY, "g": YELLOW}
LAMP_SLOTS = {1: (3,), 2: (2, 4), 3: (1, 3, 5)}   # where the stern lamps sit on the stern board
MUZZLE_COLOUR = (BLACK, ORANGE, RED)               # at rest, charging, about to fire
EYE_COLOUR = (WHITE, YELLOW, RED)                  # a ship's eyes follow its guns: calm, charging, about to fire


def paint(rows, table):
    """Text rows to a pixel array. '.' is transparent; every other letter is looked up in `table`."""
    h, w = len(rows), max(len(r) for r in rows)
    a = np.full((h, w), CLEAR, dtype=np.int16)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                a[y, x] = table[ch]
    return a


def blank(h, w):
    return np.full((h, w), CLEAR, dtype=np.int16)


def hash2(x, y, salt=0):
    """A small repeatable scramble of two whole numbers (all the scatter in this file comes from it)."""
    n = (x * 73856093) ^ (y * 19349663) ^ (salt * 83492791)
    n = (n ^ (n >> 13)) * 1274126177
    return (n ^ (n >> 16)) & 0x7FFFFFFF


def disc(size, colour, core=None):
    """A small round burst; with `core` its middle is a second colour."""
    a = blank(size, size)
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            r = math.hypot(x - c, y - c)
            if r <= size / 2:
                a[y, x] = colour
                if core is not None and r <= size / 4 + 0.2:
                    a[y, x] = core
    return a


def ring_pixels(r, colour=SKY):
    """An expanding ripple where a ship went down."""
    size = 2 * r + 1
    a = blank(size, size)
    for y in range(size):
        for x in range(size):
            if abs(math.hypot(x - r, y - r) - r) < 0.6:
                a[y, x] = colour
    return a


# ════════════════════════════════════════════════════════════════════════════════════════════════════
# PART THREE: THE PICTURES THAT MOVE: ships, strip, effects, creatures
# ════════════════════════════════════════════════════════════════════════════════════════════════════

# ── ship pictures: seen from above, bow at the top, stern at the bottom, a face on the bow ─────────────
# o hull edge   h hull   l light stripe   e eye   m mouth   s sail (its colour is the ship's own)   M mast
# G gun (muzzle or barrel)   y gold   S stern board (lamps sit on it)
# Every kind is seven pixels square; the picture is turned a quarter for each heading. A foam wake (nine pixels square)
# rides under every hull so a ship always reads as floating, whichever way it points.
SHIP_ART = {
    "m": ("..ooo..",
          ".oeheo.",
          "ohhmhho",
          "ohsssho",
          "ohsMsho",
          "ohlhhlo",
          "oSSSSSo"),
    "c": ("...G...",
          ".oeheo.",
          ".ohmho.",
          ".ossso.",
          ".ohMho.",
          ".ohlho.",
          "..SSS.."),
    "f": ("...o...",
          ".oeheo.",
          "GhhmhhG",
          ".ossso.",
          "GhsMshG",
          ".ohlho.",
          ".SSSSS."),
    "g": ("...G...",
          ".oeheo.",
          "GhhmhhG",
          "yossosy",
          "GhsMshG",
          "yhhlhhy",
          ".SSSSS."),
}
PLAYER_ART = ("...M...",
              ".kekek.",
              "kkkmkkk",
              "kkwwwkk",
              "kykwkyk",
              "kkkkkkk",
              ".kkkkk.")
HAPPY_MOUTH = (2, 2), (2, 3), (2, 4)
SAILS = (WHITE, PINK, YELLOW, GREEN)       # each enemy ship flies its own sail colour (art only: it means nothing)

_SHIP_CACHE = {}


def sink_mask(a, stage):
    """Pixels fall away as a ship goes down: stage 0 whole, stage 4 gone."""
    if stage <= 0:
        return a
    out = a.copy()
    if stage >= 4:
        out[:, :] = CLEAR
        return out
    for y in range(out.shape[0]):
        for x in range(out.shape[1]):
            if out[y, x] >= 0 and (x * 3 + y * 5 + x * y) % 5 < stage:
                out[y, x] = CLEAR
    return out


def ship_pixels(kind, heading, hp, maxhp, charge=0, flash=False, sink=0, turning=False, bob=0, sail=WHITE, blink=False):
    """One enemy ship. Rotating, lamps, guns, eyes and the white bow tip all follow the old rules of pt01."""
    key = (kind, heading, hp, maxhp, charge, flash, sink, turning, bob, sail, blink)
    if key in _SHIP_CACHE:
        return _SHIP_CACHE[key].copy()
    eye = EYE_COLOUR[charge] if not sink else EDGE[kind]          # a sinking ship shuts its eyes
    if blink and not sink:
        eye = HULL[kind]                                          # a blink: both eyes close for one picture
    table = {"o": EDGE[kind], "h": HULL[kind], "l": GLEAM[kind], "e": eye, "m": BLACK, "s": sail, "M": EDGE[kind],
             "y": YELLOW, "S": BLACK, "G": MUZZLE_COLOUR[charge]}
    a = paint(SHIP_ART[kind], table)
    if charge == 2 and not sink:
        a[2, 3] = RED                                             # a gun about to fire: the mouth snarls red
    if turning:                       # about to turn a quarter: the bow tip shows white
        a[0, CELL // 2] = WHITE
    for i, sx in enumerate(LAMP_SLOTS[maxhp]):
        a[CELL - 1, sx] = YELLOW if i < hp else BLACK
    if flash:
        a[(a >= 0) & (a != YELLOW)] = WHITE
    a = np.rot90(a, -heading).copy()
    out = sink_mask(a, sink)
    _SHIP_CACHE[key] = out
    return out.copy()


def player_pixels(heading, flash=False, sink=0, muzzle=WHITE, mood="calm", bob=0, blink=False):
    """Your ship: a black hull, white sail, gold stripe and a face. mood is calm, happy (level won) or sad (going down)."""
    key = ("P", heading, flash, sink, muzzle, mood, bob, blink)
    if key in _SHIP_CACHE:
        return _SHIP_CACHE[key].copy()
    a = paint(PLAYER_ART, {"k": BLACK, "e": WHITE, "m": WHITE, "w": WHITE, "y": YELLOW, "M": muzzle})
    if blink and mood == "calm":
        a[1, 2] = a[1, 4] = BLACK
    if mood == "happy":
        for (y, x) in HAPPY_MOUTH:
            a[y, x] = WHITE
        a[1, 2] = a[1, 4] = YELLOW                        # eyes shining
        a[2, 1] = a[2, 5] = PINK                          # rosy cheeks
    elif mood == "sad":
        a[2, 2] = a[2, 4] = SKY                           # tears
        a[2, 3] = BLACK
        a[1, 2] = a[1, 4] = SKY
    if flash:
        a[(a >= 0) & (a != WHITE)] = RED
    a = np.rot90(a, -heading).copy()
    out = sink_mask(a, sink)
    _SHIP_CACHE[key] = out
    return out.copy()


def wake_pixels(heading, frame, bright=WHITE, soft=SKY):
    """Nine pixels square of foam round a hull: bright at the bow, soft along the stern, shimmering between two frames."""
    key = ("W", heading, frame, bright, soft)
    if key not in _SHIP_CACHE:
        a = blank(CELL + 2, CELL + 2)
        c = CELL // 2 + 1
        for y in range(CELL + 2):
            for x in range(CELL + 2):
                r = math.hypot(x - c, y - c)
                ahead = (x - c) * DX[heading] + (y - c) * DY[heading]
                if 3.9 <= r <= 4.6 and ahead >= -1 and (x + y + frame) % 2 == 0:
                    a[y, x] = bright if ahead > 1 else soft           # a bow wave and foam along the flanks
        for k in (4,):                                                # two stern trails
            for side in (-1, 1):
                x = c - DX[heading] * k + side * abs(DY[heading]) * (1 + frame % 2)
                y = c - DY[heading] * k + side * abs(DX[heading]) * (1 + frame % 2)
                if 0 <= x < CELL + 2 and 0 <= y < CELL + 2:
                    a[y, x] = soft
        _SHIP_CACHE[key] = a
    return _SHIP_CACHE[key].copy()


# ── the strip along the bottom: hearts, one small ship for every enemy still afloat ──────────────────
HEART_ART = (".r.r.",
             "rwrrr",
             "rrrrr",
             ".rrr.",
             "..r..")
FOE_ART = {                                   # a tiny sailing ship (seen from the side) for every enemy still afloat
    "m": ("..k..", ".kss.", ".ksss", "hhhhh", ".hhh."),                     # merchant: one sail
    "c": ("..k..", ".kss.", ".ksss", "hhhhk", ".hhh."),                     # corvette: one sail and a bow gun
    "f": ("..k..", ".kss.", ".ksss", "khhhk", ".hhh."),                     # frigate: a gun on each flank
    "g": ("..k.k", ".ksks", ".ksks", "khhhk", ".hhh."),                     # galleon: two masts and guns
}
FOE_SAIL = {"m": WHITE, "c": YELLOW, "f": SKY, "g": WHITE}


def heart_pixels(full):
    return paint(HEART_ART, {"r": RED if full else MAROON, "w": WHITE if full else MAROON})


def foe_pixels(kind):
    return paint(FOE_ART[kind], {"h": HULL[kind], "s": FOE_SAIL[kind], "k": ORANGE})


# ── balls and bursts ───────────────────────────────────────────────────────────────────────────────────
def ball(colour):
    """A cannonball: two pixels square with a bright corner."""
    return paint(("cc", "cd"), {"c": colour, "d": SKY if colour == WHITE else ORANGE})


BURST_ART = {          # what a hit looks like for one frame
    "burst": disc(5, ORANGE, YELLOW),
    "ping": paint(("..w..", "..w..", "wwyww", "..w..", "..w.."), {"w": WHITE, "y": YELLOW}),
    "puff": paint((".w.w.", "w.s.w", ".sss.", "w.s.w", ".w.w."), {"w": WHITE, "s": SKY}),
    "plank0": paint(("ooo", ".mm"), {"o": ORANGE, "m": MAROON}),            # bits of wreck float away when you go down
    "plank1": paint(("mo", "oo", "m."), {"o": ORANGE, "m": MAROON}),
    "plank2": paint(("omoo",), {"o": ORANGE, "m": MAROON}),
}
CONFETTI = (YELLOW, PINK, SKY, GREEN, ORANGE)    # the sparkles of a won level are every bright colour in turn


def star_pixels(size, colour):
    """The sparkle that bursts round a ship when a level is won: size 0 a dot up to 3 a four-point twinkle with outriders."""
    if size == 0:
        return paint(("y",), {"y": colour})
    if size == 1:
        return paint((".y.", "ywy", ".y."), {"y": colour, "w": WHITE})
    if size == 2:
        return paint(("..y..", ".yyy.", "yywyy", ".yyy.", "..y.."), {"y": colour, "w": WHITE})
    return paint(("y.....y", ".y.y.y.", "..ywy..", "yywwwyy", "..ywy..", ".y.y.y.", "y.....y"), {"y": colour, "w": WHITE})


BUBBLE_ART = paint((".w.", "w.w", ".w."), {"w": WHITE})


def fx_pixels(kind):
    if kind.startswith("ring"):
        return ring_pixels(int(kind[4:]))
    if kind.startswith("star"):                  # "star" + size digit + confetti colour digit
        return star_pixels(int(kind[4]), CONFETTI[int(kind[5])])
    if kind == "bubble":
        return BUBBLE_ART
    return BURST_ART[kind]


# ── living things that do nothing: birds, fish, whales, jellies ──────────────────────────────────────────
# Wings beat through four pictures. Every bird has a body, a beak or head and a wing colour of its own.
GULL_FRAMES = (("k.....k", "ww...ww", ".wwwww.", "..wyw.."), (".......", "wwk.kww", ".wwwww.", "..wyw.."),
               (".......", ".......", "wwwwwww", "..wyw.."), (".......", "wwk.kww", ".wwwww.", "..wyw.."))
HAWK_FRAMES = (("k.......k", ".kk...kk.", "..kkwkk..", "...kyk..."), (".........", "kkkk.kkkk", "..kkwkk..", "...kyk..."),
               (".........", ".........", "kkkkwkkkk", "...kyk..."), (".........", "kkkk.kkkk", "..kkwkk..", "...kyk..."))
BAT_FRAMES = (("k.k...k.k", "kkk.k.kkk", ".kkkkkkk.", "..k.r.k.."), ("........." , "kkkkrkkkk", ".kkkkkkk.", "..k...k.."),
              (".kk.....kk", "kkkk.k.kkk", ".kkkkkkk.", "..k.r.k.."), ("........." , "kkkkrkkkk", ".kkkkkkk.", "..k...k.."))
PARROT_FRAMES = (("..gg...", ".gyyg..", "gggggo.", ".r.r..."), ("..gg...", ".gyyg..", ".ggggo.", "..r.r.."),
                 ("g.gg...", ".gyyg..", "gggggo.", ".r.r..."), ("..gg...", ".gyyg..", ".ggggo.", "..r.r.."))
SWALLOW_FRAMES = (("k.....k", ".kk.kk.", "..kwk..", "...r..."), (".......", "kkk.kkk", "..kwk..", "...r..."),
                  (".......", ".......", "kkkkkkk", "...r..."), (".......", "kkk.kkk", "..kwk..", "...r..."))
BIRD_TABLES = {"gull": {"w": WHITE, "k": BLACK, "y": ORANGE}, "hawk": {"k": MAROON, "w": WHITE, "y": YELLOW},
               "bat": {"k": BLACK, "r": RED}, "parrot": {"g": GREEN, "y": YELLOW, "o": ORANGE, "r": RED},
               "swallow": {"k": BLUE, "w": WHITE, "r": ORANGE}}
BIRD_ART = {"gull": GULL_FRAMES, "hawk": HAWK_FRAMES, "bat": BAT_FRAMES, "parrot": PARROT_FRAMES, "swallow": SWALLOW_FRAMES}

DOLPHIN_FRAMES = (                      # one leap, tail to nose, six pictures: splash, climb, top, fall, splash, ripples
    ("............", "............", "............", "............", "............", "....w..w....", ".w.wwwwwww.."),
    ("..........pp", ".........pep", ".......pppp.", "......pspw..", ".mt..pwwp...", "..mtpwp.....", "w.w.wwww.w.."),
    ("............", "......ff....", ".....spppp..", ".mt.sppppepp", "..mtpwwwwwp.", "...pwwwwp...", "............"),
    ("mt..........", ".mtp........", "..ppsp......", "...pppspp...", "....pwwppp..", ".....pwwppe.", ".......w.pp."),
    ("............", "............", "............", "..mt........", ".wmtppp.....", "w.wwwwppe.w.", "..w.w.w.w..."),
    ("............", "............", "............", "............", "..w......w..", "...wwwwww...", "............"),
)
FISH_FRAMES = (("..s...", "tsswse", "tsswss", "..s..."), ("t.s...", "tsswse", "tsswss", "t.s..."))
SCHOOL_FRAMES = (("ss........", "sse...ss..", ".s....sse.", "..ss...s..", ".sse...ss.", "........se"),
                 ("s.........", "sse...s...", ".ss...ssse", "..ss...s..", ".ssse..s..", ".........s"))
DUCK_FRAMES = (("..ggg.", "..gebb", "wwwww.", ".wwww.", "s.s.s."), ("..ggg.", "..gebb", "wwwwwg", ".wwww.", ".s.s.s"))
WHALE_FRAMES = (                         # a whale's back with a spout that rises and falls and a tail that flicks
    ("......s......", ".....sws.....", "......s......", "...sbbbbb....", ".bbbbbbbbbbmm", "bbbebbbbbbbbm", "bwwwwwwwwwwb.", ".wwwwwwwww..."),
    (".....s.s.s...", "....s.sws.s..", "......s......", "...sbbbbb....", ".bbbbbbbbbbmm", "bbbebbbbbbbbm", "bwwwwwwwwwwb.", ".wwwwwwwww..."),
    (".............", "......s......", "......s......", "...sbbbbb..mm", ".bbbbbbbbbbm.", "bbbebbbbbbbb.", "bwwwwwwwwwwb.", ".wwwwwwwww..."),
    (".............", ".............", ".............", "...sbbbbb....", ".bbbbbbbbbbmm", "bbbebbbbbbbbm", "bwwwwwwwwwwb.", ".wwwwwwwww..."),
)
MANTA_FRAMES = (("b.........b", "bbb.....bbb", ".bbbbbbbbb.", "..bbewebb..", "....bbb....", ".....t....."),
                ("...........", "bbb.....bbb", "bbbbbbbbbbb", ".bbbewebbb.", "....bbb....", ".....t....."),
                ("...........", "...........", "bbbbbbbbbbb", "bbbbewebbbb", ".bb.bbb.bb.", ".....t....."))
CROC_FRAMES = (("..y.y..", ".ggggg.", "ggggggg", ".g.g.g."), ("..k.y..", ".ggggg.", "ggggggg", "g.g.g.g"))
SWAN_FRAMES = (("...w..", "..wwo.", "wwww..", "wwwww.", "s.s.s."), ("...w..", "..wwo.", ".www..", "wwwww.", ".s.s.s"))
BEAR_ART = (("k...k", "kwwwk", "kwkwk", "kwpwk", ".kkk."), ("k...k", "kwwwk", "kkkkk", "kwpwk", ".kkk."))
TURTLE_FRAMES = (("..gggg.", ".gGggGg", "gggggggp", ".gGggGg", "..gggg."), ("..gggg.", ".gggGgg", "gggggggp", ".gGgggg", "..gggg."))
JELLY_FRAMES = ((".www.", "wwwww", "wpwpw", ".w.w.", "w.w.w"), (".www.", "wwwww", "wpwpw", "..w..", ".w.w."), ("wwwww", "wwwww", "wpwpw", ".w.w.", "..w.."))
SEAL_FRAMES = ((".kkk..", "kkwkk.", "kkkkkkk", ".kkkkkk", "..w..k."), (".kkk..", "kkwkk.", "kkkkkkk", ".kkkkk.", ".w...k."))


# ════════════════════════════════════════════════════════════════════════════════════════════════════
# PART FOUR: THE EIGHT PLACES. Each level has a theme: its water, its shore, its props and its living things.
# Everything below is built once per level and handed to the game as named sprites.
# ════════════════════════════════════════════════════════════════════════════════════════════════════

SEA_H, SEA_W = GH * CELL, GW * CELL        # 56 by 63; column 63 is the frame post, rows 56 and below the strip

# One theme per level. deep/shallow/foam are the three bands of water and tide is a second water colour that pools in the
# deep (shade is the colour of the cloud shadows that slide over it); land describes the shore and the ground; big is the
# landmark drawn over two land cells (kind, top-left cell) and scatter the small props; bird, critter and critter2 are the
# living things; air and air2 are the two kinds of weather; trim is the rope along the top of the strip.
THEMES = [
    dict(name="cove", deep=BLUE, shallow=SKY, foam=WHITE, crest=SKY, glint=WHITE, weed=None, swell="scallop", tide=GREEN, shade=PURPLE,
         ground="sand", landmarks=(), big=("bungalow", (4, 1)),
         scatter=("palm", "palm", "crab", "driftwood", "palm", "shell", "sandcastle", "rowboat"), scatter_pct=70,
         bird="gull", critter="dolphin", critter2="school", trim=(YELLOW, ORANGE), air=None, air2="twinkle",
         features=(("reef", 2), ("starfish", 2), ("buoy", 2), ("gullraft", 1))),
    dict(name="meadow", deep=BLUE, shallow=SKY, foam=WHITE, crest=SKY, glint=WHITE, weed=GREEN, swell="dash", tide=SKY, shade=PURPLE,
         ground="grass", landmarks=(), big=("windmill_big", (8, 5)),
         scatter=("tree", "flower", "sheep", "fence", "haystack", "mushroom", "pond", "flower"), scatter_pct=80,
         bird="gull", critter="fish", critter2="duck", trim=(GREEN, YELLOW), air="butterfly", air2="pollen",
         features=(("reeds", 3), ("lilies", 2), ("kelp", 2))),
    dict(name="snow", deep=BLUE, shallow=WHITE, patch=SKY, foam=SKY, crest=BLUE, glint=WHITE, weed=None, swell="dash", tide=SKY, shade=BLUE,
         ground="snow", landmarks=(), big=("igloo_big", (2, 1)),
         scatter=("pine", "penguin", "snowman", "tent", "pine", "flake"), scatter_pct=80,
         bird="gull", critter="seal", critter2=None, trim=(WHITE, SKY), air="snow", air2="gust",
         features=(("bearfloe", 1), ("floe", 2), ("floe_small", 2), ("gullraft", 1))),
    dict(name="canyon", deep=BLUE, shallow=SKY, foam=WHITE, crest=SKY, glint=WHITE, weed=None, swell="long", tide=SKY, shade=PURPLE,
         ground="cliff", landmarks=(), big=("pillar_big", (4, 2)),
         scatter=("cactus", "boulder", "tumbleweed", "skull", "cactus", "boulder"), scatter_pct=65,
         bird="hawk", critter="whale", critter2="manta", trim=(ORANGE, MAROON), air="dust", air2="gust",
         features=(("whirl", 1), ("shoal_rock", 2), ("buoy", 2))),
    dict(name="volcano", deep=BLUE, shallow=PURPLE, patch=SKY, foam=ORANGE, crest=SKY, glint=YELLOW, weed=None, swell="scallop", tide=SKY, shade=PURPLE,
         ground="lava", landmarks=(), big=("volcano_big", (5, 2)),
         scatter=("embers", "deadtree", "obsidian", "lavapool", "embers"), scatter_pct=65,
         bird="swallow", critter="turtle", critter2="ray", trim=(ORANGE, YELLOW), air="embers", air2="ash",
         features=(("vent", 2), ("pumice", 3))),
    dict(name="jungle", deep=BLUE, shallow=SKY, foam=WHITE, crest=SKY, glint=WHITE, weed=GREEN, swell="dash", tide=SKY, shade=PURPLE,
         ground="jungle", landmarks=(), big=("totem_big", (3, 0)),
         scatter=("bigtree", "parrot", "fern", "frog", "bigtree", "mushroom"), scatter_pct=85,
         bird="parrot", critter="fish", critter2="croc", trim=(GREEN, PURPLE), air="leaf", air2="mist",
         features=(("lilies", 3), ("reeds", 2), ("kelp", 2))),
    dict(name="night", deep=BLUE, shallow=PURPLE, patch=SKY, foam=SKY, crest=PURPLE, glint=YELLOW, weed=None, swell="long", tide=SKY, shade=PURPLE,
         ground="night", landmarks=(), big=("lighthouse_big", (5, 1)),
         scatter=("lamp", "cottage", "cat", "barrel", "lamp"), scatter_pct=70,
         bird="bat", critter="jelly", critter2="swan", trim=(PURPLE, YELLOW), air="fireflies", air2="twinkle",
         features=(("moonpath", 1), ("lantern", 3))),
    dict(name="ruins", deep=SKY, shallow=GREEN, patch=BLUE, foam=WHITE, crest=BLUE, glint=WHITE, weed=YELLOW, swell="scallop", tide=BLUE, shade=BLUE,
         ground="ruin", landmarks=(), big=("colossus_big", (5, 1)),
         scatter=("column", "brazier", "urn", "fountain", "column", "arch", "brokencol"), scatter_pct=70,
         bird="swallow", critter="dolphin", critter2="school", trim=(YELLOW, GREEN), air="petal", air2="motes",
         features=(("sunken", 2), ("starfish", 2), ("kelp", 2), ("buoy", 1))),
]


def _erode(a):
    """A pixel stays True only if its four neighbours are True too (the screen edge counts as True)."""
    p = np.pad(a, 1, constant_values=True)
    return a & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]


def _dilate(a):
    p = np.pad(a, 1, constant_values=False)
    return a | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]


def land_mask(spec):
    """The land as pixels, each convex corner shaved by one pixel so shores look rounded."""
    mask = np.zeros((SEA_H, SEA_W), dtype=bool)
    for (cx, cy) in spec.land:
        mask[cy * CELL:(cy + 1) * CELL, cx * CELL:(cx + 1) * CELL] = True
    p = np.pad(mask, 1, constant_values=True)
    up, dn, lf, rt = ~p[:-2, 1:-1], ~p[2:, 1:-1], ~p[1:-1, :-2], ~p[1:-1, 2:]
    keep = mask & ~((up | dn) & (lf | rt))
    return keep


def depth_map(keep):
    """0 on the outline, 1 on the beach rim, up to 4 deep inland."""
    depth = np.full(keep.shape, -1, dtype=np.int16)
    rest = keep.copy()
    for d in range(4):
        edge = rest & ~_erode(rest)
        depth[edge] = d
        rest &= ~edge
    depth[rest] = 4
    return depth


# What each ground is made of: the shade of the lit and shaded beach rim, the fill and what is sprinkled over it.
def ground_pixel(ground, x, y, depth, lit, salt):
    """The colour of one land pixel. Depth 0 is the black outline, 1 the beach rim, deeper is the ground itself."""
    if depth == 0:
        return BLACK
    r = hash2(x, y, salt) % 100
    if ground == "sand":
        if depth == 1:
            return YELLOW if lit else ORANGE
        if (y + x // 5) % 6 == 2 and r < 70:
            return ORANGE                                     # wind ripples running across the dunes
        return MAROON if r == 98 else (WHITE if r == 99 else (ORANGE if r < 4 else YELLOW))
    if ground == "grass":
        if depth == 1:
            return YELLOW if lit else ORANGE
        if depth == 2:
            return GREEN
        if (x // 3 + y // 3) % 2 and r < 22:
            return YELLOW                                     # mown stripes, dithered
        return PINK if r == 97 else (WHITE if r > 97 else (YELLOW if r < 3 else GREEN))
    if ground == "snow":
        if depth == 1:
            return WHITE if lit else SKY
        if (x + 2 * y) % 11 < 2 and r < 55:
            return SKY                                        # wind-blown drifts
        return SKY if r < 7 else (YELLOW if r == 99 else WHITE)
    if ground == "cliff":
        if depth == 1:
            return ORANGE if lit else MAROON
        band = (y // 3 + x // 19) % 3
        base = (ORANGE, MAROON, YELLOW)[band]                 # strata of the rock
        if r < 5:
            return BLACK                                      # cracks
        return YELLOW if r > 96 else base
    if ground == "lava":
        if depth == 1:
            return MAROON if lit else BLACK
        return MAROON if r < 38 else (PURPLE if r > 96 else BLACK)
    if ground == "jungle":
        if depth == 1:
            return GREEN if lit else PURPLE                   # lit moss on the near rim, purple shade on the far one
        if depth == 2:
            return GREEN
        return BLACK if r < 6 else (PURPLE if r < 11 else (YELLOW if r > 97 else GREEN))
    if ground == "night":
        if depth == 1:
            return PURPLE if lit else BLACK
        if x % 3 == 1 and y % 3 == 1 and r < 70:
            return PURPLE                                     # wet cobbles catching the moon
        return BLUE if r == 99 else BLACK
    # ruin: sandstone blocks with mortar and moss
    if depth == 1:
        return YELLOW if lit else ORANGE
    if y % 4 == 3 or (x + (y // 4) * 2) % 5 == 4:
        return ORANGE                                         # mortar between the blocks
    return GREEN if r < 5 else (WHITE if r == 99 else YELLOW)


_LAND_CACHE = {}


def land_picture(spec, theme, idx):
    """One sprite for all the land of a level: outline, lit and shaded rim, textured ground."""
    key = (idx, tuple(sorted(spec.land)))
    if key not in _LAND_CACHE:
        keep = land_mask(spec)
        depth = depth_map(keep)
        out = blank(SEA_H, SEA_W)
        for y in range(SEA_H):
            for x in range(SEA_W):
                if keep[y, x]:
                    lit = (y > 0 and depth[y - 1, x] == 0) or (x > 0 and depth[y, x - 1] == 0)
                    out[y, x] = ground_pixel(theme["ground"], x, y, int(depth[y, x]), lit, idx)
        _LAND_CACHE[key] = (out, keep)
    out, keep = _LAND_CACHE[key]
    return out.copy(), keep


def distance_to_land(keep, reach=6):
    """For every sea pixel, how many steps (up to `reach`) to the nearest land; 0 on land, reach+1 beyond."""
    dist = np.full(keep.shape, reach + 1, dtype=np.int16)
    dist[keep] = 0
    cur = keep.copy()
    for d in range(1, reach + 1):
        nxt = _dilate(cur)
        dist[nxt & ~cur] = d
        cur = nxt
    return dist


def _smooth_noise(h, w, grain, salt):
    """Soft blobs of 0..1 over an h by w picture: random heights on a coarse grid, blended smoothly between."""
    gh, gw = h // grain + 2, w // grain + 2
    g = np.array([[hash2(i, j, salt) % 1000 / 1000.0 for i in range(gw)] for j in range(gh)])
    out = np.zeros((h, w))
    for y in range(h):
        fy, ty = divmod(y, grain)
        ty = ty / grain
        ty = ty * ty * (3 - 2 * ty)
        for x in range(w):
            fx, tx = divmod(x, grain)
            tx = tx / grain
            tx = tx * tx * (3 - 2 * tx)
            top = g[fy, fx] * (1 - tx) + g[fy, fx + 1] * tx
            bot = g[fy + 1, fx] * (1 - tx) + g[fy + 1, fx + 1] * tx
            out[y, x] = top * (1 - ty) + bot * ty
    return out


_SEA_CACHE = {}


def sea_picture(spec, theme, idx):
    """The water of a level: deep sea with soft lighter patches (checker-edged), a shallow band round every shore, foam
    along the beach, weed in the shallows."""
    key = (idx, tuple(sorted(spec.land)))
    if key in _SEA_CACHE:
        return _SEA_CACHE[key].copy()
    land_art, keep = land_picture(spec, theme, idx)
    dist = distance_to_land(keep)
    out = np.full((SEA_H, 64), theme["deep"], dtype=np.int16)
    out[:, 63] = BLACK
    cloud = _smooth_noise(SEA_H, SEA_W, 11, idx * 5 + 2)
    tide = _smooth_noise(SEA_H, SEA_W, 17, idx * 9 + 5)          # big slow pools of a second water colour
    for y in range(SEA_H):
        for x in range(SEA_W):
            d = dist[y, x]
            r = hash2(x, y, idx + 40) % 100
            if d == 0:
                out[y, x] = theme["shallow"]
            elif d <= 3:
                out[y, x] = theme["shallow"]
                if d == 1 and (x + y) % 2 == 0:
                    out[y, x] = theme["foam"]               # the dotted line of surf at the beach
                elif d == 2 and r < 14:
                    out[y, x] = theme["foam"]
                elif d == 3 and theme["weed"] is not None and r < 12:
                    out[y, x] = theme["weed"]
            elif d == 4 and (x + y) % 2 == 0:
                out[y, x] = theme["shallow"]                # the shallows fade out in a checker
            else:
                n = cloud[y, x]
                tn = tide[y, x]
                if tn > 0.86 or (tn > 0.74 and (x + y) % 2 == 0):
                    out[y, x] = theme["tide"]                                   # a pool of the level's second water colour
                elif n > 0.78:
                    out[y, x] = theme.get("patch", theme["shallow"])            # a lighter (or darker) patch of water
                elif n > 0.69 and (x + y) % 2 == 0:
                    out[y, x] = theme.get("patch", theme["shallow"])            # its soft edge
    _SEA_CACHE[key] = out
    return out.copy()


# ── things lying in the water: shoals, reeds, lily pads, ice floes, a whirlpool, a moon's path, sunken stones ──────
def blob_mask(w, h, seed):
    """An organic oval (True inside), its outline wobbling with the angle so no two are alike."""
    m = np.zeros((h, w), dtype=bool)
    for y in range(h):
        for x in range(w):
            nx, ny = (x + 0.5 - w / 2) / (w / 2), (y + 0.5 - h / 2) / (h / 2)
            ang = math.atan2(ny, nx)
            wob = 0.13 * math.sin(3 * ang + seed) + 0.08 * math.sin(5 * ang + 2 * seed)
            m[y, x] = nx * nx + ny * ny < 0.92 + wob
    return m


def shoal(w, h, seed, fill, rim, dots=True):
    """A patch of shallows seen through the water: a filled blob with a dotted rim of surf. No black outline, so it can
    never be mistaken for land."""
    m = blob_mask(w, h, seed)
    a = blank(h, w)
    edge = m & ~_erode(m)
    for y in range(h):
        for x in range(w):
            if m[y, x]:
                a[y, x] = rim if (edge[y, x] and (x + y) % 2 == 0 and dots) else fill
    return a


def stamp(a, rows, table, x0, y0):
    """Lay a small text picture over an array; '.' leaves what is there."""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != "." and 0 <= y0 + j < a.shape[0] and 0 <= x0 + i < a.shape[1]:
                a[y0 + j, x0 + i] = table[ch]


def _feature_frames(kind, seed, theme):
    """The pictures of one lying-in-the-water thing, and how it moves: (frames, motion)."""
    if kind == "reef":
        base = shoal(13, 9, seed, SKY, WHITE)
        out = []
        for f in range(2):
            a = base.copy()
            c1, c2 = (ORANGE, PINK) if f == 0 else (PINK, ORANGE)
            stamp(a, ("o.o.o", ".ooo.", "..o.."), {"o": c1}, 2, 2)
            stamp(a, ("p.p", ".p."), {"p": c2}, 8, 3)
            a[6, 3] = YELLOW if f == 0 else ORANGE
            out.append(a)
        return out, "still"
    if kind == "starfish":
        fs = []
        for f in range(2):
            fs.append(paint((".y.", "yyy", "y.y") if f == 0 else ("y.y", ".y.", "y.y"), {"y": ORANGE if seed % 2 else PINK}))
        return fs, "still"
    if kind == "reeds":
        out = []
        for f in range(3):
            a = blank(9, 9)
            for k, sx in enumerate((1, 4, 7)):
                top = 1 + (k * 2) % 3
                lean = (f - 1) if k % 2 == 0 else (1 - f)       # the reeds sway opposite ways
                for yy in range(top, 9):
                    xx = sx + (lean if yy < top + 3 else 0)
                    a[yy, xx] = GREEN
                a[top, sx + lean] = YELLOW
                a[top - 1 if top else 0, sx + lean] = MAROON
            out.append(a)
        return out, "still"
    if kind == "lilies":
        out = []
        for f in range(2):
            a = blank(8, 13)
            for (px, py, fc) in ((1, 3, PINK), (6, 1, WHITE), (7, 5, YELLOW)):
                stamp(a, (".ggg.", "ggGgg", ".ggg."), {"g": GREEN, "G": fc if f == 0 else WHITE if fc != WHITE else PINK}, px, py)
                a[py + 1, px + 1] = GREEN                         # the notch of the pad
            out.append(a)
        return out, "bob"
    if kind in ("floe", "floe_small"):
        w, h = (11, 7) if kind == "floe" else (7, 5)
        m = blob_mask(w, h, seed)
        a = blank(h, w)
        edge = m & ~_erode(m)
        for y in range(h):
            for x in range(w):
                if m[y, x]:
                    a[y, x] = BLUE if edge[y, x] and y >= h // 2 else (SKY if y >= h - 2 else WHITE)
        if kind == "floe":
            a[2, 3] = a[3, 4] = a[3, 5] = SKY                  # a crack
        return [a], "drift"
    if kind == "bearfloe":
        base = np.full((9, 13), CLEAR, dtype=np.int16)
        m = blob_mask(13, 9, seed)
        edge = m & ~_erode(m)
        for y in range(9):
            for x in range(13):
                if m[y, x]:
                    base[y, x] = BLUE if edge[y, x] and y >= 5 else (SKY if y >= 7 else WHITE)
        out = []
        for f in range(2):
            a = base.copy()
            stamp(a, BEAR_ART[f], {"k": BLACK, "w": WHITE, "p": PINK}, 4, 1)
            out.append(a)
        return out, "drift"
    if kind == "whirl":
        out = []
        for f in range(4):
            a = blank(11, 11)
            for y in range(11):
                for x in range(11):
                    r = math.hypot(x - 5, y - 5)
                    if 0.8 < r < 5.4:
                        ang = math.atan2(y - 5, x - 5)
                        v = (ang + r * 0.9 + f * math.pi / 2) % math.pi
                        if v < 0.8:
                            a[y, x] = SKY if r > 2.2 else WHITE
            a[5, 5] = BLUE
            out.append(a)
        return out, "still"
    if kind == "shoal_rock":
        a = shoal(11, 8, seed, SKY, WHITE)
        stamp(a, (".mm.", "mMmm", ".mm."), {"m": MAROON, "M": ORANGE}, 2, 2)
        stamp(a, ("mm", "mM"), {"m": MAROON, "M": ORANGE}, 7, 4)
        return [a], "still"
    if kind == "vent":
        out = []
        for f, col in enumerate((YELLOW, ORANGE, YELLOW)):
            a = shoal(9, 7, seed, PURPLE, ORANGE)
            stamp(a, (".ccc.", "ccwcc", ".ccc."), {"c": col, "w": WHITE if f != 1 else YELLOW}, 2, 2)
            out.append(a)
        return out, "still"
    if kind == "pumice":
        return [paint((".yy.", "yoyy", ".my."), {"y": YELLOW, "o": ORANGE, "m": MAROON}),
                paint((".yy.", "yyoy", ".ym."), {"y": YELLOW, "o": ORANGE, "m": MAROON})], "drift"
    if kind == "moonpath":
        out = []
        for f in range(4):
            a = blank(22, 11)
            for y in range(22):
                half = 1 + int(3.4 * abs(math.sin(y * 0.55 + f * 0.8)))
                for x in range(5 - half, 6 + half):
                    if 0 <= x < 11 and (y + f) % 2 == 0:
                        a[y, x] = YELLOW if abs(x - 5) < half - 1 else WHITE
            out.append(a)
        return out, "still"
    if kind == "lantern":
        return [paint((".y.", "yoy", ".m."), {"y": YELLOW, "o": ORANGE, "m": MAROON}),
                paint((".w.", "yyy", ".m."), {"y": YELLOW, "w": WHITE, "m": MAROON})], "bob"
    if kind == "sunken":
        base = shoal(13, 9, seed, SKY, WHITE)
        out = []
        for f in range(2):
            a = base.copy()
            stamp(a, ("yyyoyyy", "ooooooo", "yyyoyyy"), {"y": YELLOW, "o": ORANGE}, 3, 3)
            stamp(a, ("kyk", "kyk"), {"k": MAROON, "y": YELLOW}, 5, 1)
            a[6, 2 + f] = GREEN
            a[5, 3 + f] = GREEN
            out.append(a)
        return out, "still"
    if kind == "buoy":                                   # a channel buoy bobbing on its chain, its lamp blinking red and gold
        out = []
        for lamp in (YELLOW, RED, WHITE):
            out.append(paint(("..l..", ".rrr.", ".www.", ".rrr.", "..b.."), {"l": lamp, "r": RED, "w": WHITE, "b": BLUE}))
        return out, "bob"
    if kind == "kelp":                                   # a forest of weed seen through the water, swaying in three pictures
        out = []
        for f in range(3):
            a = blank(10, 9)
            for k, sx in enumerate((1, 3, 5, 7)):
                for yy in range(10):
                    lean = int(1.2 * math.sin(yy * 0.6 + f * 2.1 + k))
                    xx = sx + lean
                    if 0 <= xx < 9:
                        a[yy, xx] = GREEN if (yy + k) % 4 else YELLOW
            out.append(a)
        return out, "still"
    if kind == "gullraft":                               # three gulls resting on the water, bobbing
        out = []
        for f in range(2):
            a = blank(4, 9)
            stamp(a, ("ww..ww.w", "wwo.wwow"), {"w": WHITE, "o": ORANGE}, 0, 0)
            for x in range(9):
                if (x + f) % 2 == 0:
                    a[2, x] = SKY
            out.append(a)
        return out, "bob"
    raise KeyError(kind)


def place_features(spec, theme, idx, dist):
    """Choose where each lying-in-the-water thing goes: deep water only (clear of every shore), never overlapping."""
    placed = []
    rects = [(c[0] * CELL - 2, c[1] * CELL - 2, CELL + 4, CELL + 4) for c in list(spec.cell) + [spec.start]]   # keep clear of every ship
    for kind, count in theme["features"]:
        for k in range(count):
            frames, motion = _feature_frames(kind, idx * 13 + k, theme)
            h, w = frames[0].shape
            for attempt in range(80):
                hh = hash2(idx * 31 + k, attempt, hash2(len(kind), 5, 11))
                x = 2 + hh % max(1, SEA_W - w - 4)
                y = 2 + (hh >> 12) % max(1, SEA_H - h - 4)
                if dist[y:y + h, x:x + w].min() <= 5:
                    continue
                if any(not (x + w + 2 < rx or rx + rw + 2 < x or y + h + 2 < ry or ry + rh + 2 < y) for rx, ry, rw, rh in rects):
                    continue
                rects.append((x, y, w, h))
                placed.append((kind, x, y, frames, motion))
                break
    return placed


def swell_glyphs(style):
    """The little wave marks that drift over the deep water: three shapes, each four pictures long."""
    if style == "scallop":
        return ((".sss.", "s...s"), (".sss.", "s...s"), ("..s..", ".s.s."), (".sss.", "s...s"))
    if style == "long":
        return (("ssssss", "......"), (".ssss.", "......"), ("..ss..", "......"), (".ssss.", "......"))
    return (("ss.ss", "....."), (".ss.s", "....."), ("ss...", ".ss.."), (".ss.s", "....."))


def wave_frames(spec, theme, idx, count=4):
    """Overlays of wave marks laid out on a loose lattice that shuffle a pixel at a time, so the deep water breathes."""
    keep = land_mask(spec)
    dist = distance_to_land(keep)
    glyphs = swell_glyphs(theme["swell"])
    frames = []
    for f in range(count):
        a = blank(SEA_H, 64)
        for ry in range(0, SEA_H - 3, 8):
            for rx in range(-4, SEA_W, 12):
                h = hash2(rx, ry, idx * 7 + 3)
                if h % 100 > 58:
                    continue
                x = rx + (ry // 8 % 2) * 6 + h % 5
                y = ry + (h >> 6) % 4
                g = glyphs[(f + (h >> 9)) % len(glyphs)]
                col = theme["crest"] if (h >> 14) % 5 else WHITE
                for j, row in enumerate(g):
                    for i, ch in enumerate(row):
                        xx, yy = x + i, y + j
                        if ch == "s" and 0 <= xx < SEA_W and 0 <= yy < SEA_H and dist[yy, xx] > 4:
                            a[yy, xx] = col
        surf = (dist == 1) & ((np.add.outer(np.arange(SEA_H), np.arange(SEA_W)) + f) % 2 == 1)
        surf |= (dist == 2) & (f % 2 == 0) & (np.add.outer(np.arange(SEA_H), np.arange(SEA_W) * 3) % 5 == 0)
        a[:, :SEA_W][surf] = theme["foam"]                       # the surf breathes in and out along every beach
        for k in range(12):                                      # glints: a few single pixels that twinkle
            h = hash2(k, idx, 91)
            x, y = h % SEA_W, (h >> 8) % SEA_H
            if dist[y, x] > 4 and (f + k) % 4 == 0:
                a[y, x] = theme["glint"]
        frames.append(a)
    return frames


# ── props: every one is a small picture in text rows (seven pixels square at most), with its own animation frames ──
# Letters are looked up in each prop's own table; k is always the black outline so a prop reads as one object on any ground.
DECOR = {
    "palm": dict(table={"G": GREEN, "k": BLACK, "m": MAROON, "n": ORANGE, "y": YELLOW},
                 frames=((".GG.GG.", "GGGGGGG", ".GGnGG.", "G.GmG.G", "..nmn..", "...m...", "..kmk.."),
                         ("..GGG..", ".GGGGGG", "GGGnGG.", ".G.mG.G", "..nmn..", "...m...", "..kmk.."))),
    "hut": dict(table={"r": MAROON, "R": ORANGE, "w": WHITE, "y": YELLOW, "d": MAROON, "k": BLACK, "s": SKY},
                frames=((".kkRkk.", "kRRRRRk", "rrrrrrr", ".wwwww.", ".wyydw.", ".wyydw.", "kkkkkkk"),
                        (".kkRkk.", "kRRRRRk", "rrrrrrr", ".wwwww.", ".wyddw.", ".wyddw.", "kkkkkkk"),
                        (".kkRkk.", "kRRRRRk", "rrrrrrr", ".wwwww.", ".wyydw.", ".wyydw.", "kkkkkkk"))),
    "crab": dict(table={"o": ORANGE, "w": WHITE, "k": BLACK, "r": RED},
                 frames=(("r...r", "owkwo", "ooooo", ".o.o."), (".r.r.", "owkwo", "ooooo", "o...o"),
                         ("r...r", "owkwo", "ooooo", ".o.o."))),
    "shell": dict(table={"p": PINK, "w": WHITE, "o": ORANGE},
                  frames=((".ppp.", "pwpwp", ".ooo."), (".ppp.", "pppwp", ".ooo."))),
    "windmill": dict(table={"b": WHITE, "h": ORANGE, "w": YELLOW, "d": MAROON, "k": BLACK, "r": RED},
                     frames=(("..brb..", "..brb..", "bbbhbbb", "..brb..", ".kwwwk.", ".kwdwk.", "kkkkkkk"),
                             ("b.....b", ".b...b.", "..rhr..", ".b...b.", ".kwwwk.", ".kwdwk.", "kkkkkkk"),
                             ("..brb..", "..brb..", "bbbhbbb", "..brb..", ".kwwwk.", ".kwdwk.", "kkkkkkk"),
                             (".....b.", "b...b..", "..rhr..", "..b...b", ".kwwwk.", ".kwdwk.", "kkkkkkk"))),
    "tree": dict(table={"o": BLACK, "G": GREEN, "y": YELLOW, "m": MAROON, "w": WHITE, "r": RED},
                 frames=((".ooooo.", "oGGGrGo", "oGyGGGo", "oGGGyGo", ".ooooo.", "..omo..", "..omo.."),
                         (".ooooo.", "oGGGGGo", "oGyGrGo", "oGGGyGo", ".ooooo.", "..omo..", "..omo.."))),
    "flower": dict(table={"w": WHITE, "y": YELLOW, "s": SKY, "g": GREEN, "p": PINK, "o": ORANGE},
                   frames=((".p.w.", "pyw.w", ".p.wy", "..g.g", ".gg.g"), (".s.o.", "syo.o", ".s.oy", "..g.g", ".gg.g"),
                           (".y.p.", "ywp.p", ".y.pw", "..g.g", ".gg.g"))),
    "sheep": dict(table={"w": WHITE, "k": BLACK, "p": PINK},
                  frames=((".wwww.", "wwwwwkk", "wwwwwkp", ".wwww..", ".k..k.."), (".wwww.", "wwwwwkk", "wwwwwkp", ".wwww..", "..k.k.."))),
    "igloo": dict(table={"w": WHITE, "s": SKY, "d": BLACK, "k": BLACK},
                  frames=((".kkkkk.", "kwwswwk", "kwswwsk", "kwwddwk", "kkkddkk"),)),
    "pine": dict(table={"g": GREEN, "w": WHITE, "m": MAROON, "k": BLACK},
                 frames=(("...w...", "..kgk..", ".kgwgk.", "..kgk..", ".kgggk.", "kgwgwgk", "..kmk.."),
                         ("...w...", "..kgk..", ".kgggk.", "..kgk..", ".kgwgk.", "kgggwgk", "..kmk.."))),
    "penguin": dict(table={"k": BLACK, "w": WHITE, "o": ORANGE, "y": YELLOW},
                    frames=((".kkk.", "kwkwk", "kkoyk", "kwwwk", "kwwwk", ".ooo."), (".kkk.", "kwkwk", "kkoyk", "kwwwk", "kwwwk", "o.o.."),
                            (".kkk.", "kkkkk", "kkoyk", "kwwwk", "kwwwk", ".ooo."))),
    "flake": dict(table={"w": WHITE, "s": SKY, "b": BLUE},
                  frames=((".w.w.", "wsbsw", ".bwb.", "wsbsw", ".w.w."), ("..w..", ".wbw.", "wbsbw", ".wbw.", "..w.."))),
    "beacon": dict(table={"m": MAROON, "o": ORANGE, "y": YELLOW, "k": BLACK, "w": WHITE},
                   frames=(("..y..", ".yoy.", "..o..", "..k..", ".kmk.", ".kok.", "kkmkk"),
                           (".y.y.", "..w..", ".yoy.", "..k..", ".kmk.", ".kok.", "kkmkk"))),
    "cactus": dict(table={"g": GREEN, "k": BLACK, "p": PINK, "y": YELLOW},
                   frames=((".g.g.p.", ".g.g.g.", ".kgggk.", "..ggg..", "..ggg..", "..kgk.."),
                           (".g.g.y.", ".g.g.g.", ".kgggk.", "..ggg..", "..ggg..", "..kgk.."))),
    "boulder": dict(table={"m": MAROON, "o": ORANGE, "k": BLACK, "y": YELLOW},
                    frames=((".kkkk..", "koyomk.", "komomk.", "kmmmmmk", ".kkkkk."),)),
    "volcano": dict(table={"m": MAROON, "o": ORANGE, "y": YELLOW, "k": BLACK, "r": RED},
                    frames=((".yoyoy.", ".kyoyk.", ".kkokk.", "kkokokk", "kmkokmk", "kkmkmkk", "mkkkkkm"),
                            (".oyyyo.", ".kyoyk.", ".kkyrk.", "kkokyok", "kmkoomk", "kkmkmkk", "mkkkkkm"))),
    "embers": dict(table={"o": ORANGE, "y": YELLOW, "k": BLACK, "r": RED},
                   frames=((".o.o.", "oyroy", ".oyo.", "o.o.o"), (".y.o.", "oyyyo", ".oyo.", ".o.o."))),
    "deadtree": dict(table={"k": BLACK, "m": MAROON, "o": ORANGE},
                     frames=(("k.k.k.", ".kmk.k", "..mmk.", "k.mk..", ".kmk..", "..m..."),
                             ("k.k.k.", ".kmk.k", "..mmk.", "..mk.k", ".kmk..", "..m..."))),
    "tiki": dict(table={"m": MAROON, "o": ORANGE, "y": YELLOW, "k": BLACK, "w": WHITE, "r": RED},
                 frames=(("o.y.o", "kyoyk", "kmmmk", "mwkwm", "mmkmm", "mkrkm", ".mmm."),
                         ("y.o.y", "kyoyk", "kmmmk", "mwkwm", "mmkmm", "mkkkm", ".mmm."))),
    "bigtree": dict(table={"o": BLACK, "G": GREEN, "y": YELLOW, "m": MAROON, "p": PURPLE, "r": RED},
                    frames=((".ooooo.", "oGGGGGo", "oGyGpGo", "oGGGGGo", "oGpGGGo", ".ooooo.", "..mmm.."),
                            (".ooooo.", "oGGGGGo", "oGpGyGo", "oGGGGGo", "oGGGpGo", ".ooooo.", "..mmm.."))),
    "parrot": dict(table={"g": GREEN, "y": YELLOW, "o": ORANGE, "k": BLACK, "r": RED, "b": BLUE},
                   frames=((".rrr.", "rykyo", "rrrrr", "bgggb", ".o.o."), (".rrr.", "rkkyo", "rrrrr", "bgggb", "o.o.."))),
    "lighthouse": dict(table={"w": WHITE, "m": RED, "y": YELLOW, "k": BLACK, "o": ORANGE},
                       frames=(("..kyk..", ".kyoyk.", ".kwwwk.", ".kmmmk.", ".kwwwk.", ".kmmmk.", "kkwwwkk"),
                               ("y.kwk.y", ".kyyyk.", ".kwwwk.", ".kmmmk.", ".kwwwk.", ".kmmmk.", "kkwwwkk"))),
    "lamp": dict(table={"k": BLACK, "y": YELLOW, "o": ORANGE, "m": MAROON, "w": WHITE},
                 frames=((".kyk.", "kyyyk", ".kok.", "..m..", "..m..", ".kmk."), (".kok.", "kyoyk", ".kyk.", "..m..", "..m..", ".kmk."))),
    "cottage": dict(table={"k": BLACK, "y": YELLOW, "m": MAROON, "p": PURPLE, "w": WHITE, "b": BLUE, "o": ORANGE},
                    frames=((".kkkkk.", "kppbppk", "kmmmmmk", "kmyymyk", "kmyymmk", "kkkkkkk"),
                            (".kkkkk.", "kppbppk", "kmmmmmk", "kmywmwk", "kmywmmk", "kkkkkkk"))),
    "statue": dict(table={"y": YELLOW, "o": ORANGE, "g": GREEN, "k": BLACK, "w": WHITE, "r": RED},
                   frames=((".kyyyk.", "kyykyyk", "kyyyyyk", ".kyoyk.", ".koook.", "kkoookk", "kkkkkkk"),
                           (".kyyyk.", "kykyyyk", "kyyyyyk", ".kyoyk.", ".koook.", "kkoookk", "kkkkkkk"))),
    "column": dict(table={"y": YELLOW, "o": ORANGE, "k": BLACK, "g": GREEN},
                   frames=((".kkkkk.", "kyyyyyk", ".kyoyk.", ".kyoyk.", ".kyoyk.", ".kyoyk.", "kkkkkkk"),
                           (".kkkkk.", "kyyyyyk", ".kyoyk.", ".kyoyk.", ".kygyk.", ".kyoyk.", "kkkkkkk"))),
    "brazier": dict(table={"o": ORANGE, "y": YELLOW, "k": BLACK, "m": MAROON, "r": RED},
                    frames=((".r.y.", "ryoyr", ".koyk", "kkkkk", "..m.."), (".y.r.", "yrooy", ".kyok", "kkkkk", "..m.."))),
    "arch": dict(table={"y": YELLOW, "o": ORANGE, "k": BLACK},
                 frames=((".kkkkk.", "kyyyyyk", "kyk.kyk", "kyk.kyk", "kok.kok", "kkk.kkk"),)),
}
# ── more small props: each level has its own set of little things that stand about (art only, they mean nothing) ──
DECOR.update({
    "driftwood": dict(table={"k": BLACK, "m": MAROON, "o": ORANGE, "w": WHITE},
                      frames=(("kmmmok.", "komkmmk", ".kkkkk."), ("kmmmok.", "komkwmk", ".kkkkk."))),
    "rowboat": dict(table={"k": BLACK, "o": ORANGE, "w": WHITE, "y": YELLOW},
                    frames=(("kkkkkkk", "kowwwok", "koooook", ".kkkkk."), ("kkkkkkk", "kowywok", "koooook", ".kkkkk."))),
    "sandcastle": dict(table={"k": BLACK, "y": YELLOW, "o": ORANGE, "r": RED},
                       frames=(("..r..", ".kkk.", "kyoyk", "kyyyk", "ooooo"), ("..y..", ".kkk.", "kyoyk", "kyyyk", "ooooo"))),
    "haystack": dict(table={"k": BLACK, "y": YELLOW, "o": ORANGE},
                     frames=((".kkk.", "kyyyk", "kyoyk", "kkkkk"), (".kkk.", "kyyyk", "kyyok", "kkkkk"))),
    "mushroom": dict(table={"r": RED, "w": WHITE, "y": YELLOW},
                     frames=((".rr.", "rwrr", ".yy.", ".yy."), (".rr.", "rrwr", ".yy.", ".yy."))),
    "pond": dict(table={"k": BLACK, "s": SKY, "w": WHITE, "g": GREEN},
                 frames=((".kkkk.", "ksswsk", "kssgsk", ".kkkk."), (".kkkk.", "kswssk", "ksggsk", ".kkkk."))),
    "fence": dict(table={"o": ORANGE, "m": MAROON}, frames=(("o.o.o.o", "ooooooo", "m.m.m.m"),)),
    "snowman": dict(table={"w": WHITE, "k": BLACK, "o": ORANGE, "r": RED},
                    frames=(("..k..", ".kkk.", "kwkwk", ".kow.", ".rrr.", "kwwwk", ".kkk."),
                            ("..k..", ".kkk.", "kwwwk", ".kow.", ".rrr.", "kwwwk", ".kkk."))),
    "tent": dict(table={"r": RED, "w": WHITE, "k": BLACK, "y": YELLOW},
                 frames=((".y.k...", "..krk..", ".krrrk.", "krrwrrk", "kkkkkkk"), ("y..k...", "..krk..", ".krrrk.", "krrwrrk", "kkkkkkk"))),
    "skull": dict(table={"w": WHITE, "k": BLACK}, frames=((".www.", "wkwkw", ".www.", ".w.w."),)),
    "tumbleweed": dict(table={"m": MAROON, "o": ORANGE},
                       frames=((".mom.", "momom", "omomo", ".mom."), (".omo.", "mmomm", "ommom", ".omo."))),
    "obsidian": dict(table={"k": BLACK, "p": PURPLE, "w": WHITE},
                     frames=(("..k..", ".kpk.", "kkpkk", "kpkwk"), ("..k..", ".kpk.", "kkpkk", "kpkpk"))),
    "lavapool": dict(table={"o": ORANGE, "y": YELLOW, "r": RED, "k": BLACK},
                     frames=((".kkkk.", "koyyok", "kyoyrk", ".kkkk."), (".kkkk.", "kyoyok", "koyoyk", ".kkkk."),
                             (".kkkk.", "koyoyk", "kyyork", ".kkkk."))),
    "fern": dict(table={"g": GREEN, "G": YELLOW, "k": BLACK},
                 frames=(("g.gg.g", ".gGGg.", "..gg..", "..kk.."), (".g.g.g", "ggGGgg", "..gg..", "..kk.."))),
    "frog": dict(table={"g": GREEN, "y": YELLOW, "r": RED}, frames=(("ygggy", "ggrgg", "g.g.g"), ("ygggy", "ggggg", "g.g.g"))),
    "barrel": dict(table={"m": MAROON, "o": ORANGE, "y": YELLOW, "k": BLACK},
                   frames=((".kkk.", "kmomk", "kyyyk", "kmomk", ".kkk."),)),
    "cat": dict(table={"p": PURPLE, "y": YELLOW, "k": BLACK, "m": MAGENTA},
                frames=(("p...p", "ppppp", "pypyp", "ppmpp", ".ppp."), ("p...p", "ppppp", "ppppp", "ppmpp", ".ppp."),
                        ("p...p", "ppppp", "pypyp", "ppmpp", ".ppp."))),
    "fountain": dict(table={"s": SKY, "w": WHITE, "y": YELLOW, "k": BLACK},
                     frames=((".w.w.w.", "..w.w..", "kssssk.", "kyyyyyk", ".kkkkk."), ("..w.w..", ".w.w.w.", "kssssk.", "kyyyyyk", ".kkkkk."))),
    "urn": dict(table={"o": ORANGE, "y": YELLOW, "k": BLACK}, frames=((".kkk.", ".kyk.", "kyoyk", "kyoyk", ".kkk."),)),
    "brokencol": dict(table={"y": YELLOW, "o": ORANGE, "k": BLACK}, frames=(("kyk.k", "kyyyk", "kyoyk", "kkkkk"),)),
})

# ── the big landmarks: each is drawn over two land cells (7 by 14, or 14 by 7 or 14 by 14) and replaces the small one ──
DECOR.update({
    "bungalow": dict(table={"k": BLACK, "R": ORANGE, "r": MAROON, "y": YELLOW, "w": WHITE, "s": SKY, "d": MAROON, "m": RED, "o": ORANGE},
                     frames=(("...kkkkkkkkmmk", ".kkkkkkkkkkkk.", "kRRRyRRRRyRRRk", "kRrRRrRRrRRrRk", "krrrrrrrrrrrrk", "kwsswwdddwyywk", "kkkkkkkkkkkkkk"),
                             ("...kkkkkkkkmmk", ".kkkkkkkkkkkk.", "kRRRyRRRRyRRRk", "kRrRRrRRrRRrRk", "krrrrrrrrrrrrk", "kwsswwdddwoowk", "kkkkkkkkkkkkkk"))),
    "windmill_big": dict(table={"b": WHITE, "h": ORANGE, "r": RED, "k": BLACK, "w": WHITE, "d": MAROON, "y": YELLOW},
                         frames=(("...b...", "...b...", "...b...", "bbbhbbb", "...b...", "...b...", "...r...",
                                  "..kkk..", ".kwwwk.", ".kwdwk.", "kwwwwwk", "kwwyywk", "kwwydwk", "kkkkkkk"),
                                 ("b.....b", ".b...b.", "..b.b..", "...h...", "..b.b..", ".b...b.", "r.....r",
                                  "..kkk..", ".kwwwk.", ".kwdwk.", "kwwwwwk", "kwwyywk", "kwwydwk", "kkkkkkk"),
                                 ("...b...", "...b...", "...b...", "bbbhbbb", "...b...", "...b...", "...r...",
                                  "..kkk..", ".kwwwk.", ".kwdwk.", "kwwwwwk", "kwwyywk", "kwwydwk", "kkkkkkk"),
                                 ("..b...b", "..b..b.", "...bb..", "...h...", "..bb...", ".b..b..", "b...b..",
                                  "..kkk..", ".kwwwk.", ".kwdwk.", "kwwwwwk", "kwwyywk", "kwwydwk", "kkkkkkk"))),
    "igloo_big": dict(table={"w": WHITE, "s": SKY, "b": BLUE, "k": BLACK, "y": YELLOW, "r": RED},
                      frames=(("....kkkkkk....", "..kkwwwwwwkk..", ".kwwwsswwwwwk.", ".kwswwwwwwswwk", "kwwwwwswwwwwwk", "kswwwwwwwwwwsk", "kwwwskkkkkwwwk",
                               "kwwkbbbbbbkwwk", "kwwkbyyybbkwwk", "kwwkbbbbbbkwwk", "kswkbbkbbbkwsk", "kwwkbbkbbbkwwk", "kkwkkkkkkkkwkk", ".kkkkkkkkkkkk."),
                              ("....kkkkkk....", "..kkwwwwwwkk..", ".kwwwsswwwwwk.", ".kwswwwwwwswwk", "kwwwwwswwwwwwk", "kswwwwwwwwwwsk", "kwwwskkkkkwwwk",
                               "kwwkbbbbbbkwwk", "kwwkbyyybbkwwk", "kwwkbbbbbbkwwk", "kswkbbkbbbkwsk", "kwwkbbkbbbkwwk", "kkwkkkkkkkkwkk", ".kkkkkkkkkkkk."))),
    "pillar_big": dict(table={"y": YELLOW, "o": ORANGE, "w": WHITE, "k": BLACK, "m": MAROON},
                       frames=(("..y.y..", ".yoyoy.", "..oyo..", "kkkkkkk", ".kmmmk.", ".kmomk.", ".kmmmk.", "kmmommk", "kmmmmmk", "kmommmk", "kmmmomk", "kkmmmkk", "kmmmmmk", "kkkkkkk"),
                               (".y.y.y.", "..yoy..", ".yoyoy.", "kkkkkkk", ".kmmmk.", ".kmomk.", ".kmmmk.", "kmmommk", "kmmmmmk", "kmommmk", "kmmmomk", "kkmmmkk", "kmmmmmk", "kkkkkkk"))),
    "volcano_big": dict(table={"m": MAROON, "o": ORANGE, "y": YELLOW, "k": BLACK, "r": RED},
                        frames=(("..yyy..", ".kyoyk.", ".kkokk.", ".kmokk.", "kkmokmk", "kmmokmk", "kmoomkk", "kmmokmk", "kkmomkk", "kmmoomk", "kmkomkk", "kmmokmk", "kkmmmkk", "kkkkkkk"),
                                ("..oyo..", ".kyyyk.", ".kkokk.", ".kmkok.", "kkmokmk", "kmmkokk", "kmoomkk", "kmmokmk", "kkmomkk", "kmmoomk", "kmkomkk", "kmkoomk", "kkmmmkk", "kkkkkkk"))),
    "totem_big": dict(table={"m": MAROON, "o": ORANGE, "y": YELLOW, "k": BLACK, "w": WHITE, "r": RED, "g": GREEN},
                      frames=(("o.....o", "ky.y.yk", "kkyoykk", "kmmmmmk", "kwkmkwk", "kmmrmmk", "kkkkkkk", "kmmmmmk", "kwkmkwk", "kmkkkmk", "kmrrrmk", "kkkkkkk", "kgmmmgk", "kkkkkkk"),
                              ("y.....y", "ko.y.ok", "kkyoykk", "kmmmmmk", "kwkmkwk", "kmmrmmk", "kkkkkkk", "kmmmmmk", "kwkmkwk", "kmkkkmk", "kmrrrmk", "kkkkkkk", "kgmmmgk", "kkkkkkk"))),
    "lighthouse_big": dict(table={"w": WHITE, "m": RED, "y": YELLOW, "k": BLACK, "o": ORANGE, "b": BLUE},
                           frames=(("...o...", "..kkk..", ".kyyyk.", ".kywyk.", "kkkkkkk", ".kwwwk.", ".kmmmk.", "kkwwwkk", "kmmmmmk", "kwwwwwk", "kmmbmmk", "kwwbwwk", "kmmmmmk", "kkkkkkk"),
                                   ("...o...", "..kkk..", ".kwwwk.", ".kwyyk.", "kkkkkkk", ".kwwwk.", ".kmmmk.", "kkwwwkk", "kmmmmmk", "kwwwwwk", "kmmbmmk", "kwwbwwk", "kmmmmmk", "kkkkkkk"))),
    "colossus_big": dict(table={"y": YELLOW, "o": ORANGE, "g": GREEN, "k": BLACK, "r": RED, "w": WHITE},
                         frames=((".kkkkk.", "kyyyyyk", "kyryryk", "kyyoyyk", ".kkyykk", "kyyyyyk", "kyoooky", "kyyoyyk", ".kyyyyk", ".kkyykk", ".kyyyk.", ".kgoyk.", "kkyyykk", "kkkkkkk"),
                                 (".kkkkk.", "kyyyyyk", "kygygyk", "kyyoyyk", ".kkyykk", "kyyyyyk", "kyoooky", "kyyoyyk", ".kyyyyk", ".kkyykk", ".kyyyk.", ".kgoyk.", "kkyyykk", "kkkkkkk"))),
})
BIG_SIZE = {"bungalow": (2, 1), "windmill_big": (1, 2), "igloo_big": (2, 2), "pillar_big": (1, 2), "volcano_big": (1, 2),
            "totem_big": (1, 2), "lighthouse_big": (1, 2), "colossus_big": (1, 2)}     # (cells wide, cells high)

GROUND_SPARK = {"sand": WHITE, "grass": PINK, "snow": SKY, "cliff": WHITE, "lava": YELLOW, "jungle": YELLOW, "night": YELLOW, "ruin": WHITE}
_DECOR_CACHE = {}


def decor_frames(name):
    if name not in _DECOR_CACHE:
        d = DECOR[name]
        _DECOR_CACHE[name] = [paint(rows, d["table"]) for rows in d["frames"]]
    return _DECOR_CACHE[name]


def decor_plan(idx, spec, theme):
    """Which prop stands on which land cell: the landmarks on the best-connected cells, small props scattered by hash."""
    cells = sorted(spec.land)

    def friends(c):
        return sum((c[0] + a, c[1] + b) in spec.land for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))

    ranked = sorted(cells, key=lambda c: (-friends(c), hash2(c[0], c[1], idx)))
    plan, used = [], set()
    if theme.get("big"):
        kind, (bx, by) = theme["big"]
        bw, bh = BIG_SIZE[kind]
        plan.append((kind, (bx, by)))
        used |= {(bx + i, by + j) for i in range(bw) for j in range(bh)}
        assert used <= spec.land, "the big landmark must stand on land"
    for kind in theme["landmarks"]:
        if ranked:
            c = next((c for c in ranked if c not in used), None)
            if c is not None:
                used.add(c)
                plan.append((kind, c))
    for c in cells:
        if c in used:
            continue
        h = hash2(c[0], c[1], idx + 3)
        if h % 100 < theme["scatter_pct"]:
            plan.append((theme["scatter"][(h >> 8) % len(theme["scatter"])], c))
            used.add(c)
    return plan


# ── things that rise or drift on their own ─────────────────────────────────────────────────────────────
SMOKE_FRAMES = (("..w..", ".....", ".....", ".....", "....."),
                (".ww..", "..w..", ".....", ".....", "....."),
                (".....", ".ww..", "..ww.", ".....", "....."),
                (".....", ".....", "..ww.", "...w.", "....."))
BEAM_FRAMES = (("yyyy.", ".yyy.", "....."), (".....", ".yyy.", ".yyyy"))
LAVA_GLOW = {"y": YELLOW, "o": ORANGE}

# Specks of weather and wildlife that fall, rise or wander over a whole sea: (picture frames, colours, how they move, count)
AIR = {
    "butterfly": dict(frames=(("p.p", ".y."), (".p.", "pyp")), table={"p": PINK, "y": YELLOW}, move="wander", n=3),
    "snow": dict(frames=(("w",), ("w",)), table={"w": WHITE}, move="fall", n=10),
    "dust": dict(frames=(("o.",), (".o",)), table={"o": ORANGE}, move="drift", n=6),
    "embers": dict(frames=(("y",), ("o",)), table={"y": YELLOW, "o": ORANGE}, move="rise", n=7),
    "leaf": dict(frames=(("gg", ".g"), ("g.", "gg")), table={"g": GREEN}, move="fall", n=4),
    "fireflies": dict(frames=(("y",), ("w",), ("y.",)), table={"y": YELLOW, "w": WHITE}, move="wander", n=7),
    "petal": dict(frames=(("p.", ".p"), (".p", "p.")), table={"p": PINK}, move="fall", n=5),
    "twinkle": dict(frames=(("w",), (".",), (".",), ("y",), (".",), (".",)), table={"w": WHITE, "y": YELLOW}, move="still", n=10),
    "pollen": dict(frames=(("y.", ".y"), (".y", "y.")), table={"y": YELLOW}, move="drift", n=5),
    "gust": dict(frames=(("ww",), ("w.",), (".w",)), table={"w": WHITE}, move="streak", n=4),
    "ash": dict(frames=(("p",), ("k",)), table={"p": PURPLE, "k": MAROON}, move="fall", n=8),
    "mist": dict(frames=(("w.w", ".w."), (".w.", "w.w")), table={"w": WHITE}, move="drift", n=3),
    "motes": dict(frames=(("y",), ("o",), ("y.",)), table={"y": YELLOW, "o": ORANGE}, move="wander", n=6),
}


def air_position(spec_, k, t, idx):
    """Where speck k of a level's weather is at tick t: (x, y) or None for hidden (a firefly winks out)."""
    h = hash2(k, idx, 61)
    x0, y0 = h % 70, (h >> 7) % 56
    move = spec_["move"]
    if move == "still":                                   # a twinkle sits where it is; the picture itself blinks
        return (x0 % SEA_W, y0 % SEA_H)
    if move == "streak":                                  # a gust of wind-dashes sweeps across, quick and level
        return ((x0 + t * 2 + k * 17) % 84 - 10, y0 + k * 3 % 20)
    if move == "fall":
        return (x0 + (t // 6) % 5 - 2 + (t // 3) // 5, (y0 + t // 2 * (1 + k % 2) // 2) % 62 - 3)
    if move == "rise":
        return ((x0 + (t // 5) % 3 - 1) % 66, (y0 - t // 2 * (1 + k % 2) // 2) % 62 - 3)
    if move == "drift":
        return ((x0 + t // 2) % 76 - 6, y0 + (t // 8) % 3)
    wob = int(3 * math.sin(t * 0.35 + k * 1.7))
    return (x0 + wob + (t // 9) % 3, y0 + int(3 * math.cos(t * 0.27 + k)))


_BEAM_CACHE = []


def beam_frames():
    """A lighthouse beam turning through eight pictures: a dithered yellow wedge with a white core, 27 pixels square."""
    if not _BEAM_CACHE:
        for k in range(8):
            a = blank(27, 27)
            aim = k * math.pi / 4
            for y in range(27):
                for x in range(27):
                    r = math.hypot(x - 13, y - 13)
                    if 3 < r < 13.5 and (x + y) % 2 == 0:
                        off = abs((math.atan2(y - 13, x - 13) - aim + math.pi) % (2 * math.pi) - math.pi)
                        if off < 0.3:
                            a[y, x] = YELLOW
                        elif off < 0.45 and r > 6:
                            a[y, x] = WHITE
            _BEAM_CACHE.append(a)
    return _BEAM_CACHE


def critter_art(kind):
    """The frames and colour table of a sea creature."""
    if kind == "dolphin":
        return DOLPHIN_FRAMES, {"p": PURPLE, "w": WHITE, "e": BLACK, "s": SKY, "f": MAGENTA, "m": MAGENTA, "t": PURPLE}
    if kind == "school":
        return SCHOOL_FRAMES, {"s": ORANGE, "e": BLACK}
    if kind == "duck":
        return DUCK_FRAMES, {"g": GREEN, "e": BLACK, "b": ORANGE, "w": WHITE, "s": SKY}
    if kind == "manta":
        return MANTA_FRAMES, {"b": PURPLE, "w": WHITE, "e": BLACK, "t": ORANGE}
    if kind == "ray":
        return MANTA_FRAMES, {"b": ORANGE, "w": YELLOW, "e": BLACK, "t": RED}
    if kind == "croc":
        return CROC_FRAMES, {"g": GREEN, "y": YELLOW, "k": BLACK}
    if kind == "swan":
        return SWAN_FRAMES, {"w": WHITE, "o": ORANGE, "s": SKY}
    if kind == "fish":
        return FISH_FRAMES, {"s": ORANGE, "w": YELLOW, "e": BLACK, "t": RED}
    if kind == "whale":
        return WHALE_FRAMES, {"w": WHITE, "b": PURPLE, "e": BLACK, "s": SKY, "m": MAGENTA}
    if kind == "turtle":
        return TURTLE_FRAMES, {"g": GREEN, "G": YELLOW, "p": ORANGE}
    if kind == "seal":
        return SEAL_FRAMES, {"k": MAROON, "w": WHITE}
    return JELLY_FRAMES, {"w": PINK, "p": WHITE}


# ── the lines you read: where your next ball goes, and which lanes are armed ─────────────────────────────

def seg_pixels(cx, cy, d, ncells):
    """Pixels along a cell's centre line, from just outside cell (cx, cy) through ncells cells beyond it."""
    mx, my = cx * CELL + CELL // 2, cy * CELL + CELL // 2
    return [(mx + DX[d] * k, my + DY[d] * k) for k in range(CELL // 2 + 1, CELL // 2 + CELL * ncells + 1)]


def marks_picture(sc):
    """The armed lanes (red dashes) and the aim line (dots in your muzzle colour, with a black dot between them)."""
    lanes, aim = blank(SEA_H, SEA_W), blank(SEA_H, SEA_W)
    for _, pix in sc["lanes"]:
        for i, (x, y) in enumerate(pix):
            if i % 3 != 2 and 0 <= x < SEA_W and 0 <= y < SEA_H:
                lanes[y, x] = RED
    if sc["aim"] is not None:
        pix, colour = sc["aim"]
        for i, (x, y) in enumerate(pix):
            if 0 <= x < SEA_W and 0 <= y < SEA_H:
                aim[y, x] = colour if i % 2 == 0 else BLACK
    return lanes, aim


# ── the strip along the bottom ───────────────────────────────────────────────────────────────────────────
def strip_picture(theme):
    """A black strip under the sea with a two-colour rope along its top edge; the sprites for hearts sit on it."""
    a = np.full((8, 64), BLACK, dtype=np.int16)
    for x in range(64):
        a[0, x] = theme["trim"][(x // 2) % 2]
    return a


def tint_picture():
    """The look of a lost run: a dark red frame that closes in round the sea, solid at the edge and fading by checker and
    then by sparse dither; the water in the middle stays clean so the wreck reads."""
    a = blank(SEA_H, 64)
    for y in range(SEA_H):
        for x in range(SEA_W):
            edge = min(x, y, SEA_W - 1 - x, SEA_H - 1 - y)
            if edge < 2:
                a[y, x] = MAROON
            elif edge < 4 and (x + y) % 2 == 0:
                a[y, x] = MAROON
            elif edge < 6 and x % 2 == 0 and y % 2 == 0:
                a[y, x] = MAROON
    a[:, 63] = BLACK
    return a


# ════════════════════════════════════════════════════════════════════════════════════════════════════
# PART FIVE: THE GAME. It owns the state, builds the sprites and plays the pictures; the rules stay in part one.
# ════════════════════════════════════════════════════════════════════════════════════════════════════

FLY = 2            # frames a ball takes over a long line
SINK = 4           # frames an enemy ship takes to go down
DEATH_FRAMES = 9   # your own sinking: the ship goes down with a sad face under a red checker
CHEER_FRAMES = 6   # a won level: a ring of sparks round your ship before the next sea opens
# sparks over the sinking ship and round the winner, small to large and back
CHEER_SIZE = (0, 1, 2, 3, 2, 1)
LAYER = dict(sea=0, waves=1, life=2, lanes=3, aim=4, land=5, prop=6, smoke=7, wake=8, ship=9, player=10, ball=11, spark=12, tint=14, hud=20, heart=21)


def _clone(sc):
    return {"p": list(sc["p"]), "s": [list(x) for x in sc["s"]], "b": list(sc["b"]), "x": list(sc["x"]),
            "aim": sc["aim"], "lanes": sc["lanes"], "hearts": sc["hearts"], "foes": sc["foes"], "mz": sc["mz"],
            "mood": sc["mood"], "tint": sc["tint"]}


class Pt02(ARCBaseGame):
    def __init__(self) -> None:
        self.st = None
        self.frames = []
        self.fi = 0
        self.after = None
        self.tick = 0
        self.s_player = None
        self.s_ships = []
        self.s_fx = []
        self.anim = []
        levels = [Level(sprites=[], name=f"pt02-{i + 1}", data={"index": i}) for i in range(len(SPECS))]
        super().__init__(game_id="pt02", levels=levels, camera=Camera(0, 0, 64, 64, BLUE, BLACK),
                         win_score=len(levels), available_actions=[1, 2, 3, 4, 5])

    @property
    def spec(self):
        return SPECS[self.level_index]

    # ── entering a level: the one place that builds it, used for start, next level and RESET ──
    # (a sunk ship ends the run as GAME_OVER; RESET follows the engine's own rule, exactly as in pt01)

    def on_set_level(self, level: Level) -> None:
        self._enter(level)

    def _put(self, level, pixels, name, x, y, layer, tags=()):
        sp = Sprite(pixels, name=name, x=x, y=y, layer=LAYER[layer], blocking=BlockingMode.NOT_BLOCKED, tags=list(tags))
        level.add_sprite(sp)
        return sp

    def _enter(self, level) -> None:
        spec = self.spec
        idx = self.level_index
        theme = THEMES[idx]
        self.st = spec.initial()
        self.frames = []
        self.fi = 0
        self.after = None
        self.tick = 0
        self.s_fx = []
        self.anim = []
        level.remove_all_sprites()
        # the water, its crests, the shore and the props
        self._put(level, sea_picture(spec, theme, idx), "sea", 0, 0, "sea", ["backdrop"])
        self.waves = wave_frames(spec, theme, idx)
        self.s_waves = self._put(level, self.waves[0], "waves", 0, 0, "waves", ["ambient"])
        self.wave_i = 0
        land_art, _ = land_picture(spec, theme, idx)
        self._put(level, land_art, "land", 0, 0, "land", ["land"])
        self.s_lanes = self._put(level, blank(SEA_H, SEA_W), "lanes", 0, 0, "lanes", ["danger"])
        self.s_aim = self._put(level, blank(SEA_H, SEA_W), "aim", 0, 0, "aim", ["aim"])
        self._build_props(level, spec, theme, idx, land_art)
        self._build_life(level, spec, theme, idx)
        self._build_features(level, spec, theme, idx)
        self._build_air(level, theme, idx)
        self._build_shadows(level, theme, idx)
        # the ships and you: each rides on its own foam wake (a named sprite under the hull)
        self.s_wakes = [self._put(level, wake_pixels(spec.head0[i], 0), f"wake{i}", spec.cell[i][0] * CELL - 1,
                                  spec.cell[i][1] * CELL - 1, "wake", ["wake", "ambient"]) for i in range(spec.n)]
        self.s_pwake = self._put(level, wake_pixels(spec.pface, 0, WHITE, WHITE), "wake_player", spec.start[0] * CELL - 1,
                                 spec.start[1] * CELL - 1, "wake", ["wake", "ambient"])
        self.s_ships = []
        for i in range(spec.n):
            sp = self._put(level, ship_pixels(spec.kind[i], spec.head0[i], spec.hp0[i], spec.hp0[i]), f"ship{i}",
                           spec.cell[i][0] * CELL, spec.cell[i][1] * CELL, "ship", ["ship", "enemy", spec.kind[i]])
            self.s_ships.append(sp)
        self.s_player = self._put(level, player_pixels(spec.pface), "player", spec.start[0] * CELL, spec.start[1] * CELL,
                                  "player", ["ship", "player"])
        # the strip: rope, hearts and one small ship for every enemy afloat
        self._put(level, strip_picture(theme), "strip", 0, HUD_Y, "hud", ["hud"])
        self.s_hearts = [self._put(level, heart_pixels(True), f"heart{i}", 2 + i * 7, HUD_Y + 2, "heart", ["hud", "heart"])
                         for i in range(HEARTS)]
        self.s_foes = [self._put(level, foe_pixels("m"), f"foe{i}", 0, HUD_Y + 2, "heart", ["hud", "foe"]) for i in range(spec.n)]
        self.s_tint = self._put(level, tint_picture(), "tint", 0, 0, "tint", ["feedback"])
        self.s_tint.set_interaction(InteractionMode.REMOVED)
        self._show(self._settled(self.st))

    def _build_props(self, level, spec, theme, idx, land_art):
        """Props that stand on the land. Each is a named sprite that cycles through its own frames."""
        counts = {}
        for kind, (cx, cy) in decor_plan(idx, spec, theme):
            frames = decor_frames(kind)
            h, w = frames[0].shape
            n = counts[kind] = counts.get(kind, 0) + 1
            x = cx * CELL if w > CELL else cx * CELL + (CELL - w) // 2
            y = cy * CELL if h > CELL else cy * CELL + (CELL - h) // 2
            sp = self._put(level, frames[0], f"{kind}{n}", x, y, "prop", ["prop", kind, "landmark"] if kind in BIG_SIZE else ["prop", kind])
            phase = hash2(cx, cy, idx) % 4
            slow = 3 if kind in ("windmill", "windmill_big", "flower", "beacon", "lamp", "brazier", "embers", "fountain", "lavapool") else 5
            self.anim.append(dict(sp=sp, frames=frames, cur=0, fn=(lambda t, f=frames, p=phase, s=slow: (None, None, (t // s + p) % len(f)))))
            if kind in ("volcano_big", "bungalow"):    # smoke rises from the crater and from the chimney
                smoke = [paint(rows, {"w": WHITE if kind == "bungalow" else PINK}) for rows in SMOKE_FRAMES]
                sx_ = cx * CELL + (1 if kind == "volcano_big" else 10)
                sm = self._put(level, smoke[0], "smoke", sx_, max(0, cy * CELL - 5), "smoke", ["ambient", "smoke"])
                self.anim.append(dict(sp=sm, frames=smoke, cur=0, fn=(lambda t, f=smoke: (None, None, (t // 2) % len(f)))))
            if kind == "lighthouse_big":               # a slow beam sweeps round the night water
                beams = beam_frames()
                bm = self._put(level, beams[0], "beam", cx * CELL + 3 - 13, cy * CELL + 2 - 13, "life", ["ambient", "beam"])
                self.anim.append(dict(sp=bm, frames=beams, cur=0, fn=(lambda t, f=beams: (None, None, (t // 3) % len(f)))))
        # the ground glitters here and there: a few inland pixels flash a highlight in turn (sand glints, snow sparkles, ...)
        spark = GROUND_SPARK[theme["ground"]]
        spots = [(x, y) for y in range(SEA_H) for x in range(SEA_W)
                 if land_art[y, x] >= 0 and land_art[y, x] != BLACK and hash2(x, y, 33) % 100 < 5]
        flashes = [blank(SEA_H, SEA_W) for _ in range(3)]
        for q, (x, y) in enumerate(spots):
            flashes[q % 3][y, x] = spark
        sp = self._put(level, flashes[0], "glitter", 0, 0, "prop", ["ambient", "glitter"])
        self.anim.append(dict(sp=sp, frames=flashes, cur=0, fn=(lambda t, f=flashes: (None, None, (t // 3) % 3))))
        if theme["ground"] == "lava":                  # glowing cracks in the black rock that change colour
            veins = [blank(SEA_H, SEA_W), blank(SEA_H, SEA_W)]
            for y in range(SEA_H):
                for x in range(SEA_W):
                    if land_art[y, x] == MAROON and hash2(x, y, 5) % 100 < 14:
                        veins[0][y, x] = ORANGE
                        veins[1][y, x] = YELLOW
            sp = self._put(level, veins[0], "cracks", 0, 0, "prop", ["ambient", "lava"])
            self.anim.append(dict(sp=sp, frames=veins, cur=0, fn=(lambda t, f=veins: (None, None, (t // 3) % 2))))

    def _build_features(self, level, spec, theme, idx):
        """The big things lying in the water: shoals, reeds, lily pads, floes, a whirlpool, a moon's path. They do nothing."""
        dist = distance_to_land(land_mask(spec))
        for n, (kind, x, y, frames, motion) in enumerate(place_features(spec, theme, idx, dist)):
            sp = self._put(level, frames[0], f"{kind}{n}", x, y, "life", ["ambient", "water", kind])
            ph = hash2(n, idx, 17) % 12
            if motion == "drift":                     # a floe or a raft of pumice slides slowly and wraps round
                fn = (lambda t, x=x, y=y, f=frames, p=ph, w=frames[0].shape[1]: ((x + (t + p) // 6) % (SEA_W + w) - w, y, (t // 7 + p) % len(f)))
            elif motion == "bob":                     # lily pads and lanterns rise and fall a pixel
                fn = (lambda t, x=x, y=y, f=frames, p=ph: (x, y + ((t + p) // 5) % 2, (t // 6 + p) % len(f)))
            else:
                fn = (lambda t, f=frames, p=ph: (None, None, (t // 4 + p) % len(f)))
            self.anim.append(dict(sp=sp, frames=frames, cur=0, fn=fn))

    def _build_air(self, level, theme, idx):
        """Weather and little flyers over the whole sea: snow, embers, butterflies, fireflies, leaves, petals; a second
        kind of weather rides along (twinkles, pollen, wind dashes, ash, mist, motes)."""
        for which in ("air", "air2"):
            if theme[which] is None:
                continue
            a = AIR[theme[which]]
            frames = [paint(rows, a["table"]) for rows in a["frames"]]
            for k in range(a["n"]):
                kk = k + (20 if which == "air2" else 0)           # the second kind draws its own scatter
                sp = self._put(level, frames[0], f"{theme[which]}{k}", 0, 0, "smoke", ["ambient", "air"])
                fn = (lambda t, k=kk, a=a, f=frames: (lambda p: (p[0], p[1], (t // 3 + k) % len(f)) if 0 <= p[0] < SEA_W and 0 <= p[1] < SEA_H else (None, None, None))(air_position(a, k, t, idx)))
                self.anim.append(dict(sp=sp, frames=frames, cur=0, fn=fn))

    def _build_shadows(self, level, theme, idx):
        """Two cloud shadows slide slowly over the water (a checker of the level's shade colour, under every ship)."""
        for k in range(2):
            w, h = (24, 12) if k == 0 else (16, 9)
            m = blob_mask(w, h, idx * 3 + k)
            a = blank(h, w)
            for y in range(h):
                for x in range(w):
                    if m[y, x] and (x + y) % 2 == 0:
                        a[y, x] = theme["shade"]
            x0, y0 = hash2(k, idx, 71) % 60, 4 + (hash2(k, idx, 72) % 40)
            sp = self._put(level, a, f"shadow{k}", x0, y0, "waves", ["ambient", "shadow"])
            sp_speed = 5 + 3 * k
            self.anim.append(dict(sp=sp, frames=[a], cur=0, fn=(lambda t, x0=x0, y0=y0, v=sp_speed, w=w: ((x0 + t // v) % (SEA_W + w) - w, y0 + (t // 40) % 3, 0))))

    def _build_life(self, level, spec, theme, idx):
        """Birds across the sky and one creature in the sea: they do nothing, and they never touch the rules."""
        art = BIRD_ART[theme["bird"]]
        table = BIRD_TABLES[theme["bird"]]
        frames = [paint(rows, table) for rows in art]
        for k in range(2):
            y0 = 4 + 24 * k + hash2(k, idx, 8) % 9
            x0 = hash2(k, idx, 9) % 76
            sgn = 1 if k == 0 else -1
            sp = self._put(level, frames[0], f"bird{k}", x0, y0, "smoke", ["ambient", "bird"])
            self.anim.append(dict(sp=sp, frames=frames, cur=0,
                                  fn=(lambda t, x0=x0, y0=y0, s=sgn, f=frames: ((x0 + s * (t // 2)) % 78 - 8, y0 + (t // 6) % 2, (t // 2) % len(f)))))
        kind = theme["critter"]
        c_frames, c_table = critter_art(kind)
        cf = [paint(rows, c_table) for rows in c_frames]
        cells = sorted(spec.sea)
        cx, cy = cells[hash2(idx, 77, 3) % len(cells)]
        x0, y0 = cx * CELL, cy * CELL + 2
        sp = self._put(level, cf[0], "creature", x0, y0, "life", ["ambient", kind])
        if kind == "dolphin":
            fn = lambda t: (x0, y0, (t % 36) // 2) if t % 36 < 2 * len(cf) else (None, None, None)
        elif kind == "whale":
            fn = lambda t: (x0, y0, (t % 30) // 2) if t % 30 < 8 else (None, None, None)
        elif kind == "seal":
            fn = lambda t: (x0, y0, (t // 3) % 2) if t % 24 < 14 else (None, None, None)
        elif kind == "jelly":
            fn = lambda t: (x0, y0 - (t // 6) % 3, (t // 3) % len(cf))
        else:                                              # fish and turtles drift across and wrap round
            fn = lambda t: ((x0 + t // 3) % 78 - 8, y0, (t // 3) % len(cf))
        self.anim.append(dict(sp=sp, frames=cf, cur=0, fn=fn, shown=True))
        kind2 = theme.get("critter2")
        if kind2:                                          # a second swimmer glides the other way, in its own lane
            c2_frames, c2_table = critter_art(kind2)
            c2 = [paint(rows, c2_table) for rows in c2_frames]
            cx2, cy2 = cells[hash2(idx, 78, 4) % len(cells)]
            y2 = cy2 * CELL + 1
            sp2 = self._put(level, c2[0], "swimmer", 0, y2, "life", ["ambient", kind2])
            sw = 4 + hash2(idx, 5, 6) % 3
            self.anim.append(dict(sp=sp2, frames=c2, cur=0, shown=True,
                                  fn=(lambda t, y2=y2, sw=sw, f=c2: ((cx2 * CELL - t // sw) % 84 - 12, y2 + (t // 7) % 2, (t // 4) % len(f)))))

    # ── pictures ──────────────────────────────────────────────────────────────

    def _settled(self, st, marks=True):
        spec = self.spec
        px, py, pf, hearts, phi, hps = st
        nxt = (phi + 1) % spec.cycle
        ships = []
        for i in range(spec.n):
            charge = 2 if spec.armed[i][phi] else (1 if spec.armed[i][nxt] else 0)
            sc_ = spec.script[i]
            turning = sc_[phi % len(sc_)] in "RL"
            ships.append([spec.head[i][phi], hps[i], charge, 0, 0, hps[i] > 0, turning])
        aim, lanes, mz = None, [], WHITE
        if marks:
            cells, result, tgt = trace_shot(spec, px, py, pf, hps, phi)
            n = len(cells) - (1 if result in ("hit", "bounce") else 0)
            mz = PINK if result == "bounce" else WHITE
            aim = (seg_pixels(px, py, pf, n), mz)
            for i in range(spec.n):
                if hps[i] > 0 and spec.armed[i][phi]:
                    h = spec.head[i][phi]
                    for g in spec.guns[i]:
                        d = (h + g) % 4
                        cl, hit = _lane(spec, i, d, px, py, hps)
                        lanes.append((i, seg_pixels(spec.cell[i][0], spec.cell[i][1], d, len(cl) - (1 if hit else 0))))
        return {"p": [px * CELL, py * CELL, pf, 0, 0], "s": ships, "b": [], "x": [], "aim": aim, "lanes": lanes,
                "hearts": hearts if spec.hud_hearts else None,
                "foes": [spec.kind[i] for i in range(spec.n) if hps[i] > 0], "mz": mz, "mood": "calm", "tint": False}

    def _show(self, sc):
        spec = self.spec
        self.tick += 1
        t = self.tick
        bob = (t // 3) % 2
        p = sc["p"]
        self.s_player.set_position(p[0], p[1])
        self.s_player.pixels = player_pixels(p[2], flash=bool(p[3]), sink=p[4], muzzle=sc["mz"], mood=sc["mood"], bob=bob,
                                             blink=(t % 17 == 0))
        self.s_pwake.set_position(p[0] - 1, p[1] - 1)
        self.s_pwake.pixels = wake_pixels(p[2], (t // 2) % 2, WHITE, WHITE)
        for i, sp in enumerate(self.s_ships):
            h, hp, charge, flash, sink, visible, turning = sc["s"][i]
            if visible and sink < 4:
                sp.set_interaction(InteractionMode.TANGIBLE)
                sp.pixels = ship_pixels(spec.kind[i], h, hp, spec.hp0[i], charge, bool(flash), sink, turning, (bob + i) % 2,
                                        SAILS[i % len(SAILS)], blink=((t + 5 * i) % 19 == 0))
                wk = self.s_wakes[i]
                wk.set_interaction(InteractionMode.TANGIBLE)
                wk.pixels = wake_pixels(h, (t // 2 + i) % 2)
            else:
                sp.set_interaction(InteractionMode.REMOVED)
                self.s_wakes[i].set_interaction(InteractionMode.REMOVED)
        level = self.current_level
        for sp in self.s_fx:
            level.remove_sprite(sp)
        self.s_fx = []
        for k, (x, y, colour) in enumerate(sc["b"]):
            self.s_fx.append(self._put(level, ball(colour), f"ball{k}", x, y, "ball", ["shot"]))
        for k, (x, y, kind) in enumerate(sc["x"]):
            pix = fx_pixels(kind)
            off = pix.shape[0] // 2
            self.s_fx.append(self._put(level, pix, f"spark{k}", x - off, y - off, "spark", ["effect"]))
        # lanes, aim, tint
        lanes, aim = marks_picture(sc)
        self.s_lanes.pixels = lanes
        self.s_aim.pixels = aim
        self.s_tint.set_interaction(InteractionMode.TANGIBLE if sc["tint"] else InteractionMode.REMOVED)
        # the strip: hearts, then the enemies still afloat packed from the right
        for i, sp in enumerate(self.s_hearts):
            if sc["hearts"] is None:
                sp.set_interaction(InteractionMode.REMOVED)
            else:
                sp.set_interaction(InteractionMode.TANGIBLE)
                sp.pixels = heart_pixels(i < sc["hearts"])
        for k, sp in enumerate(self.s_foes):
            if k < len(sc["foes"]):
                sp.set_interaction(InteractionMode.TANGIBLE)
                sp.pixels = foe_pixels(sc["foes"][k])
                sp.set_position(63 - (k + 1) * 6, HUD_Y + 2)
            else:
                sp.set_interaction(InteractionMode.REMOVED)
        self._animate()

    def _animate(self):
        """The small lives that do nothing: waves, props, birds and the sea creature, all from the tick counter."""
        t = self.tick
        wi = (t // 3) % len(self.waves)
        if wi != self.wave_i:
            self.wave_i = wi
            self.s_waves.pixels = self.waves[wi]
        for rec in self.anim:
            x, y, i = rec["fn"](t)
            sp = rec["sp"]
            if i is None:
                if rec.get("shown", True):
                    sp.set_interaction(InteractionMode.REMOVED)
                    rec["shown"] = False
                continue
            if not rec.get("shown", True):
                sp.set_interaction(InteractionMode.TANGIBLE)
                rec["shown"] = True
            if i != rec["cur"]:
                sp.pixels = rec["frames"][i]
                rec["cur"] = i
            if x is not None:
                sp.set_position(x, y)

    # ── one action ────────────────────────────────────────────────────────────

    def step(self) -> None:
        if self.action.id == GameAction.RESET:      # the engine calls step() once for RESET too
            self.complete_action()
            return
        if self.action.id.value not in (1, 2, 3, 4, 5):
            self.complete_action()
            return
        if not self.frames:
            self._begin()
        sc = self.frames[self.fi]
        self.fi += 1
        if sc is None:                              # the death is over: the run ends; RESET restarts the level
            self.lose()
        else:
            self._show(sc)
        if self.fi >= len(self.frames):
            after = self.after
            self.frames = []
            self.fi = 0
            self.after = None
            if after == "win":
                self.next_level()
            self.complete_action()

    def _begin(self) -> None:
        """Decide the whole outcome once, then lay out the pictures that show it."""
        spec = self.spec
        st0 = self.st
        ev = []
        st1, status = advance(spec, st0, self.action.id.value, ev)
        frames = self._film(st0, st1, status, ev)
        self.st = st1
        self.frames = frames
        self.fi = 0
        self.after = "win" if status == 1 else None

    def _film(self, st0, st1, status, ev):
        spec = self.spec
        cur = self._settled(st0, marks=True)
        cur["aim"] = None
        cur["mz"] = WHITE
        frames = []
        sinks = {}

        def push():
            frames.append(_clone(cur))

        def centre(cell):
            return cell[0] * CELL + CELL // 2, cell[1] * CELL + CELL // 2

        def fly(a, b, colour, n):
            for k in range(1, n + 1):
                x = a[0] + (b[0] - a[0]) * k // n
                y = a[1] + (b[1] - a[1]) * k // n
                cur["b"] = [(x - 1, y - 1, colour)]
                push()
            cur["b"] = []

        for e in ev:
            kind = e[0]
            if kind == "move":
                _, ox, oy, nx, ny, d = e
                cur["p"][2] = d
                for k in (1, 2):
                    cur["p"][0] = ox * CELL + (nx - ox) * (CELL * k // 3)
                    cur["p"][1] = oy * CELL + (ny - oy) * (CELL * k // 3)
                    push()
                cur["p"][0], cur["p"][1] = nx * CELL, ny * CELL       # the move is finished before anything fires
            elif kind == "bump":
                _, ox, oy, d = e
                cur["p"][2] = d
                cur["p"][0], cur["p"][1] = ox * CELL + DX[d], oy * CELL + DY[d]
                push()
                cur["p"][0], cur["p"][1] = ox * CELL, oy * CELL
            elif kind == "shot":
                _, ox, oy, d, cells, result, tgt = e
                a = centre((ox, oy))
                a = (a[0] + DX[d] * 3, a[1] + DY[d] * 3)
                if result in ("hit", "bounce"):
                    tc = centre(cells[-1])
                    b = (tc[0] - DX[d] * 3, tc[1] - DY[d] * 3)
                else:
                    last = cells[-1] if cells else (ox, oy)
                    lc = centre(last)
                    b = (lc[0] + DX[d] * 3, lc[1] + DY[d] * 3)
                n = 1 if (len(cells) <= 2 or status == 2) else FLY
                fly(a, b, WHITE, n)
                if result == "hit":
                    cur["x"] = [(b[0], b[1], "burst")]
                    cur["s"][tgt][3] = 1
                    cur["s"][tgt][1] = st1[5][tgt]
                    push()
                    cur["x"] = []
                    cur["s"][tgt][3] = 0
                    if st1[5][tgt] == 0:
                        sinks[tgt] = len(frames)
                        cur["lanes"] = [ln for ln in cur["lanes"] if ln[0] != tgt]
                elif result == "bounce":
                    cur["x"] = [(b[0], b[1], "ping")]
                    push()
                    cur["x"] = []
                    fly(b, a, RED, n)
                else:
                    cur["x"] = [(b[0], b[1], "puff")]
                    push()
                    cur["x"] = []
            elif kind == "ricochet":
                cur["x"] = [(cur["p"][0] + CELL // 2, cur["p"][1] + CELL // 2, "burst")]
                cur["p"][3] = 1
                if cur["hearts"] is not None:
                    cur["hearts"] = max(0, cur["hearts"] - 1)
                push()
                cur["x"] = []
                cur["p"][3] = 0
        volleys = [e for e in ev if e[0] == "volley"]
        if volleys and not (status == 1):
            cur["lanes"] = []
            starts, ends = [], []
            for (_, i, d, cells, hit) in volleys:
                sc_ = centre(spec.cell[i])
                a = (sc_[0] + DX[d] * 3, sc_[1] + DY[d] * 3)
                if hit:
                    pc = (cur["p"][0] + CELL // 2, cur["p"][1] + CELL // 2)
                    b = (pc[0] - DX[d] * 3, pc[1] - DY[d] * 3)
                elif cells:
                    lc = centre(cells[-1])
                    b = (lc[0] + DX[d] * 3, lc[1] + DY[d] * 3)
                else:
                    b = a
                starts.append(a)
                ends.append(b)
            nf = 1 if status == 2 else FLY
            for k in range(1, nf + 1):
                cur["b"] = [(a[0] + (b[0] - a[0]) * k // nf - 1, a[1] + (b[1] - a[1]) * k // nf - 1, RED)
                            for a, b in zip(starts, ends)]
                push()
            cur["b"] = []
            marks = []
            damaged = 0
            for (_, i, d, cells, hit), b in zip(volleys, ends):
                marks.append((b[0], b[1], "burst" if hit else "puff"))
                damaged += 1 if hit else 0
            cur["x"] = marks
            if damaged:
                cur["p"][3] = 1
                if cur["hearts"] is not None:
                    cur["hearts"] = max(0, cur["hearts"] - damaged)
            push()
            cur["x"] = []
            cur["p"][3] = 0
        if status == 2:
            d = DEATH_FRAMES
            cur["b"] = []
            cur["x"] = []
            cur["mood"] = "sad"
            cur["tint"] = True
            for ship in cur["s"]:
                ship[2] = 2                                       # the enemy ships that are left gloat: red eyes, red mouths
            for k in range(d):
                cur["p"][4] = 1 + (k * 4) // d
                px_, py_ = cur["p"][0] + CELL // 2, cur["p"][1] + CELL // 2
                cur["x"] = [(px_, py_, f"ring{2 + (k * 5) // d}")]
                for q in range(3):                                # planks drift outward from the wreck
                    ang = q * 2.1 + 0.6
                    reach = 4 + k // 2 + 2 * q
                    cur["x"].append((px_ + int(round(reach * math.cos(ang))), py_ + int(round(reach * math.sin(ang))), f"plank{q}"))
                if k % 3 == 1:                                    # bubbles rise from the wreck
                    cur["x"].append((px_ + 2 * (k % 2) - 1, py_ - 3 - k // 3, "bubble"))
                push()
            frames.append(None)
        else:
            final = self._settled(st1, marks=(status == 0))
            frames.append(final)
        # ships that went down fade over the frames that follow their hit
        for tgt, start in sinks.items():
            while len(frames) < start + SINK:
                frames.insert(len(frames) - 1, _clone(frames[-2] if len(frames) > 1 else cur))
            for t in range(start, len(frames)):
                sc = frames[t]
                if sc is None:
                    continue
                sc["s"][tgt][4] = min(SINK, t - start + 1)
                if t < len(frames) - 1 and t - start + 1 < SINK + 1:
                    cx_, cy_ = centre(spec.cell[tgt])
                    sc["x"] = list(sc["x"]) + [(cx_, cy_, f"ring{1 + min(SINK, t - start + 1)}")]
        if status == 1:
            self._cheer(frames, centre, [centre(spec.cell[i]) for i in range(spec.n)])
        return frames

    def _cheer(self, frames, centre, wrecks):
        """A won level: your ship smiles and sparks burst round it and over every ship that went down."""
        base = frames[-1]
        pcx, pcy = base["p"][0] + CELL // 2, base["p"][1] + CELL // 2
        for k in range(CHEER_FRAMES):
            sc = _clone(base)
            sc["mood"] = "happy"
            sc["aim"] = None
            sc["lanes"] = []
            size = CHEER_SIZE[k]
            r = 6 + 2 * k
            pts = []
            for q in range(6):
                ang = (q / 6.0) * 2 * math.pi + k * 0.3
                pts.append((pcx + int(round(r * math.cos(ang))), pcy + int(round(r * math.sin(ang)))))
            for (wx, wy) in wrecks[:3]:
                pts.append((wx, wy))
            # every spark its own bright colour; the first picture of the cheer also throws a ring round your ship
            sc["x"] = [(min(max(x, 3), SEA_W - 4), min(max(y, 4), SEA_H - 5), f"star{size}{(q + k) % len(CONFETTI)}")
                       for q, (x, y) in enumerate(pts)]
            sc["x"].append((pcx, pcy, f"ring{3 + k}"))
            for q in range(9):                                # a shower of confetti falls over the whole sea
                fx_ = (q * 7 + 5 + 3 * (q % 3) * k) % (SEA_W - 6) + 3
                fy_ = (k * 11 + q * 13) % (SEA_H - 8) + 4
                sc["x"].append((fx_, fy_, f"star{q % 2}{(q + 2 * k) % len(CONFETTI)}"))
            frames.append(sc)
