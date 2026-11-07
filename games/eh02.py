# Author: Claude Sonnet 5.5
# Date: 07-November-2026
# PURPOSE: eh02 "Echo", the redrawn eh01. The RULES ARE UNCHANGED: same eight corridors, same pits, keys and ring, same two
#   marks per cell (one on thin ground), same step bar sized at twice the shortest win, same Space-to-look retreat, same
#   dead-end-free walk, the same win and the same run-over. Core below is eh01's rule object copied as it was. What changed is
#   the picture: every thing on screen is now a NAMED engine Sprite (name, tags, layer) instead of pixels painted on the
#   finished frame. Each level is its own cavern (cellar, crystal cave, night, lava, ice, temple, sea ruin, vault) with a
#   hand-drawn backdrop, wall props and a few gentle drifting things that do nothing. Floor tiles, flames for the marks, key
#   slots, the portal, the walker (with eyes, a mouth, a blink and a sad face) are all small pictures. A level win bursts
#   into sparkles; a lost run reddens the cave, the floor crumbles and the walker sags with a frown.
#   Pass 3 (variety and life): big multi-cell set pieces fill the rock of every cave, drawn with a small pen (door, cauldron,
#   arched windows; crystals; haunted tree, lamps, mushrooms; demon face, lava fall, volcano; snowman, firs, igloo; sun disc,
#   totems, altar; coral reef, kelp, chest; armour, shield, pillar, gold), each a two-frame named sprite placed where it fits.
#   Pass 4: new tree, reef, cluster and volcano pictures; big pieces avoid the start corner.
#   Plain black key niches with solid keys, a level-clear confetti shower, the top band and set pieces redden in a lost run.
#   Nothing on the play surface is text. Dark ground is still purple (now with a cave-specific surface in its lower half), lit ground is still green, pink
#   is still only a pit rim or a shut ring, and a cell the walker cannot reach is still drawn as rubble inside a dark ring.
# SRP/DRY check: Pass -- rules live in Core (no art); the art helpers (art, put, tiles, themes) never read a rule except
#   through the Core the game hands them; one paint() turns (Core, per-frame vis) into sprites. eh01 is untouched.
# CHANGELOG
# 07-Nov-2026 (Claude Sonnet 5.5): first sprite version of eh01 (pass 1 of the art redraw). Rules identical.
# 07-Nov-2026 (Claude Sonnet 5.5): pass 2, critique and redraw: crystal spires replace the scratchy ruling, bigger outlined
#   props (torch, crystal, owl with a blink, imp, snowman, idol, kelp, banner), a per-cave floor surface, a taller walker with
#   feet, a grin on a win and a frown and dust on a loss, falling stones and props in a lost run, gold-rimmed key sockets, a
#   masonry band with an emblem at each end, bigger drifters, a moon and molten seams. Rules identical.
# 07-Nov-2026 (Claude Sonnet 5.5): pass 3, per-level set pieces and living detail, cleaner key slots, wider crystal spires,
#   moss/cracks/inlay/shell scatter on the backdrops, rats, drips, jellyfish and scarabs, confetti on a win, tinted band on a
#   loss. Rules identical.
"""Echo -- the lantern is how you see.

ACTION1-4 walk up/down/left/right. ACTION5 (Space) steps back the way you just came and lights
the cell you left. No text: the slots along the top are the keys, the portal at the right of them is
the way out, and the white bar under them is the steps left. RESET restarts the level.
"""

import copy
import math
from collections import deque

import numpy as np
from arcengine import ARCBaseGame, Camera, Level, Sprite

# ---------------------------------------------------------------------------
# Palette (ARC-3 indices)
# ---------------------------------------------------------------------------

C_WHITE, C_LGRAY, C_GRAY, C_DGRAY, C_VDGRAY, C_BLACK = 0, 1, 2, 3, 4, 5
C_MAGENTA, C_LMAGENTA, C_RED, C_BLUE, C_LBLUE = 6, 7, 8, 9, 10
C_YELLOW, C_ORANGE, C_MAROON, C_GREEN, C_PURPLE = 11, 12, 13, 14, 15

C_ROCK = C_MAROON      # the stone the corridor is cut through (each level now picks its own, see THEMES)
C_DARK = C_PURPLE      # a cell whose contents are unknown
C_NOISE = C_BLACK      # the stipple over it
C_LIT = C_GREEN        # ground you have lit
C_MARK = C_ORANGE      # a remaining retreat
C_SCAR = C_ORANGE      # a spent cell (filled, crossed)
C_KEY = C_YELLOW
C_SHUT = C_MAGENTA     # the ring while a key is still out
C_OPEN = C_LBLUE       # the ring once every key is in
C_PIT = C_BLACK
C_RIM = C_MAGENTA      # pink: sends you back
C_YOU = C_BLUE
C_NO = C_RED
C_FLARE = C_WHITE

# ---------------------------------------------------------------------------
# Geometry: 7 x 6 cells of 9 px under a 10 px top band (the key slots and the ring).
# ---------------------------------------------------------------------------

GW, GH = 7, 6
CELL = 9
HUD_H = 10
OFFX = (64 - GW * CELL) // 2
OFFY = 64 - GH * CELL
LOOKS = 2

DIRS = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}
ACTION_DIR = {1: "U", 2: "D", 3: "L", 4: "R"}
LOOK = 5
ACTIONS = [1, 2, 3, 4, 5]

# Steps per level, one per walk or look (bumps included; RESET free). Twice the shortest winning line, found by
# breadth-first search over Core's own rules. Shortest lines: 7, 16, 24, 24, 24, 27, 36, 32.
BUDGETS = [14, 32, 48, 48, 48, 54, 72, 64]

WALL, FLOOR, START, TRAP, KEY, EXIT, THIN = "#", ".", "S", "T", "K", "E", "o"


def neighbours(cell):
    return [(cell[0] + dx, cell[1] + dy) for dx, dy in DIRS.values()]


def origin(cell):
    return OFFX + cell[0] * CELL, OFFY + cell[1] * CELL


# ---------------------------------------------------------------------------
# Levels. Walls are visible from the first frame; contents are not. 'o' is thin ground (one
# mark), 'K' a key, 'T' a pit, 'E' the ring, 'S' where you start (and where a pit sends you).
# ---------------------------------------------------------------------------

LEVELS = [
    {"name": "l1", "free": True,
     "map": ("#######",
             "#S..###",
             "###.###",
             "###.E##",
             "#######",
             "#######")},
    {"name": "l2",
     "map": ("#K#.#.#",
             "#.#.#.#",
             "S.....E",
             "#.#K#K#",
             "#######",
             "#######")},
    {"name": "l3",
     "map": ("##K#K##",
             "##.#.##",
             "#S.....",
             "##.#.#E",
             "##K#K##",
             "#######")},
    {"name": "l4",
     "map": ("##K#K#K",
             "##.#.#.",
             "#S.....",
             "##.#.#E",
             "##K#T##",
             "#######")},
    {"name": "l5",
     "map": ("#K#K#.#",
             "#.#.#T#",
             "S.....E",
             "#.#.#.#",
             "#K#K#.#",
             "#######")},
    {"name": "l6",
     "map": ("##K#K##",
             "#S....#",
             "#.#E#.#",
             "#K###K#",
             "#.o.o.#",
             "##K#T##")},
    {"name": "l7",
     "map": ("S..K...",
             "######.",
             "K.K.K..",
             ".######",
             "......E",
             "#K#T#K#")},
    {"name": "l8",
     "map": ("#K#.#K#",
             "#.#.#.#",
             "S.o.o.E",
             "#.#K#.#",
             "#K#.#K#",
             "#T#K#.#")},
]


# ---------------------------------------------------------------------------
# Rules, as one small object: the game drives this and the drawing only reads it.
# (Copied unchanged from eh01.)
# ---------------------------------------------------------------------------

def parse(rows):
    cells, content, keys, exits, thin = set(), {}, set(), set(), set()
    start = None
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == WALL:
                continue
            cells.add((c, r))
            content[(c, r)] = FLOOR if ch in (START, THIN) else ch
            if ch == START:
                start = (c, r)
            elif ch == EXIT:
                exits.add((c, r))
            elif ch == KEY:
                keys.add((c, r))
            elif ch == THIN:
                thin.add((c, r))
    return frozenset(cells), start, frozenset(exits), frozenset(keys), content, frozenset(thin)


def component(src, passable):
    seen = {src}
    q = deque([src])
    while q:
        p = q.popleft()
        for n in neighbours(p):
            if n in passable and n not in seen:
                seen.add(n)
                q.append(n)
    return seen


class Core:
    """All of the rules and none of the pictures."""

    def __init__(self, ldef):
        rows = ldef["map"]
        self.free = bool(ldef.get("free"))
        (self.cells, self.start, self.exits, self.keys, self.content, self.thin) = parse(rows)
        self.pos = self.start
        self.trail = None
        self.revealed = {self.start}
        self.looks = {}
        for c in self.cells:
            self.looks[c] = 99 if (self.free or c == self.start) else (1 if c in self.thin else LOOKS)
        self.taken = set()

    # -- state helpers ------------------------------------------------------

    def copy(self):
        n = copy.copy(self)
        n.revealed = set(self.revealed)
        n.looks = dict(self.looks)
        n.taken = set(self.taken)
        return n

    def key(self):
        return (self.pos, self.trail, frozenset(self.revealed),
                tuple(sorted(self.looks.items())), frozenset(self.taken))

    def passable(self):
        return {c for c in self.cells
                if self.looks[c] > 0 and not (c in self.revealed and self.content[c] == TRAP)}

    def ring_open(self):
        return self.keys <= self.taken

    def won(self):
        return self.pos in self.exits and self.pos in self.revealed and self.ring_open()

    # -- the two verbs ------------------------------------------------------

    def walk(self, d):
        dx, dy = DIRS[d]
        nxt = (self.pos[0] + dx, self.pos[1] + dy)
        if nxt not in self.passable():
            return [("block", nxt, d)]
        here = self.pos
        if here not in self.revealed and self.content[here] == TRAP:
            self.revealed.add(here)                 # the floor gives way
            self.pos = self.start
            self.trail = None
            return [("fall", here)]
        self.trail = here
        self.pos = nxt
        return [("move", here, nxt)]

    def look(self):
        back = self.trail
        if back is None or self.pos in self.revealed:
            return [("empty",)]                     # nothing here to light
        d = next((k for k, (dx, dy) in DIRS.items()
                  if (self.pos[0] + dx, self.pos[1] + dy) == back), None)
        if self.looks[back] <= 0:
            return [("scar", back, d)]
        x = self.pos
        cost = 1
        took = False
        self.revealed.add(x)
        if self.content[x] == KEY and x not in self.taken:
            self.taken.add(x)
            took = True
        before = self.looks[back]
        home = self.free or back == self.start      # the entrance never wears out
        if not home:
            self.looks[back] = max(0, before - cost)
        self.pos = back
        self.trail = None
        return [("look", x, back, 0 if home else cost, took, before)]

    def act(self, aid):
        if aid in ACTION_DIR:
            return self.walk(ACTION_DIR[aid])
        if aid == LOOK:
            return self.look()
        return []


# ---------------------------------------------------------------------------
# Pictures, part one: the tiny pixel-art toolkit.
# A picture is a tuple of equal-length text rows. '.' is see-through; every other letter is a palette colour.
# ---------------------------------------------------------------------------

LEGEND = {"W": 0, "K": 5, "M": 6, "P": 7, "R": 8, "B": 9, "L": 10,
          "Y": 11, "O": 12, "N": 13, "G": 14, "V": 15}


def art(rows, legend=None):
    """Text rows -> int8 pixel array, -1 where see-through. Ragged rows are a bug, so they raise."""
    assert len({len(r) for r in rows}) == 1, "ragged picture: %r" % (rows[0],)
    lg = legend or LEGEND
    return np.array([[lg.get(ch, -1) for ch in row] for row in rows], dtype=np.int8)


def remap(pix, table):
    """A copy of a picture with some colours swapped for others (used for tints and damage)."""
    out = pix.copy()
    for old, new in table.items():
        out[pix == old] = new
    return out


def flip(pix):
    return pix[:, ::-1].copy()


def blank(h, w, colour=-1):
    return np.full((h, w), colour, dtype=np.int8)


# ---------------------------------------------------------------------------
# Pictures, part two: the things that are the same in every cave.
# ---------------------------------------------------------------------------

KEY_PIC = art((".OOO....",
               "OYWYOOOO",
               "OYYYOYOY",
               ".OOO...."))
KEY_EMPTY = remap(KEY_PIC, {11: C_BLUE, 0: C_LBLUE, 12: C_BLUE})       # the silhouette waiting in a slot

# A key socket: a gold-rimmed little niche, pale-blue lip along the top, deep blue inside. An empty one shows the
# black outline of a key; a full one shows the real gold key with a gleam on it.
SLOT_PIC = art(("OYOOOOOOYO",
                "OKKKKKKKKO",
                "OKKKKKKKKO",
                "OKKKKKKKKO",
                "OKKKKKKKKO",
                "OKKKKKKKKO",
                "OYOOOOOOYO"))
# The portal. Shut: a magenta ring around black with an eyelid shut across it. Open: a pale-blue ring around a bright
# glow with an eye looking out. Rows 0 and 8 stay see-through so the same picture sits in the band and in a cell.
GATE_SHUT = art(("....P....",
                 ".MMPPPMM.",
                 "MPPMMMPPM",
                 "MPMKKKMPM",
                 "MPKMMMKPM",
                 "MPMKKKMPM",
                 "MPPMMMPPM",
                 ".MMPPPMM.",
                 "....P...."))
GATE_OPEN = art(("....W....",
                 ".LLWWWLL.",
                 "LWWLLLWWL",
                 "LWLWWWLWL",
                 "LWWWBWWWL",
                 "LWLWWWLWL",
                 "LWWLLLWWL",
                 ".LLWWWLL.",
                 "....W...."))

# Where a key was: an empty stone seat. (A lit cell that held a key only ever shows this.)
SEAT_PIC = art((".........",
                ".........",
                "...NNN...",
                "..NKKKN..",
                "..NKKKN..",
                "...NNN...",
                ".........",
                ".........",
                "........."))

# A pit that has been looked at: black hole, pink rim with teeth. (Pink means it sends you back.)
PIT_PIC = art(("....M....",
               "...MPM...",
               "..MPKPM..",
               ".MPKKKPM.",
               "MPKKKKKPM",
               ".MPKKKPM.",
               "..MPKPM..",
               "...MPM...",
               "....M...."))

# Marks: little flames in the two top corners of a cell (left one is the first mark, right one the second).
FLAME = art((".Y.",
             "OYO",
             "OOO"))
FLAME_HOT = art((".Y.",
                 "ROR",
                 "RRR"))
SPARK_BIG = art((".W.",
                "WYW",
                ".W."))
SPARK_SMALL = art(("Y",))
GLINT = art(("..W..",
             "..W..",
             "WWYWW",
             "..W..",
             "..W.."))

# A puff of dust, two sizes.
PUFF = [art((".WW.", "WYYW", "WYYW", ".WW.")), art(("W..W", ".YY.", ".YY.", "W..W"))]
# Falling stone chunks that come loose from the roof when the run is lost.
CHUNK = [art((".YO", "OOR", "NRN")), art(("OO.", "ORR", "NNK"))]

CONFETTI = [art(("YY", "YO")), art(("MM", "MP")), art(("LL", "LB")), art(("GG", "GY")), art(("OO", "OR")),
            art(("WW", "WL")), art(("PP", "PM"))]

FLARE_A = blank(CELL, CELL, C_WHITE)
FLARE_A[4, 2:7] = C_YELLOW
FLARE_A[2:7, 4] = C_YELLOW
FLARE_B = blank(CELL, CELL, C_WHITE)


def ring_edge(colour):
    """A two-pixel outline of one cell (the old 'edge' flash)."""
    a = blank(CELL, CELL)
    for t in (0, 1):
        a[t, t:CELL - t] = colour
        a[CELL - 1 - t, t:CELL - t] = colour
        a[t:CELL - t, t] = colour
        a[t:CELL - t, CELL - 1 - t] = colour
    return a


EDGE_WHITE = ring_edge(C_WHITE)
EDGE_RED = ring_edge(C_RED)
BUMP_BIG = blank(CELL, CELL, C_RED)
BUMP_BIG[3:6, 3:6] = C_WHITE
BUMP_SMALL = blank(CELL, CELL)
BUMP_SMALL[2:CELL - 2, 2:CELL - 2] = C_RED
BUMP_SMALL[CELL // 2, CELL // 2] = C_YELLOW
BUMP_SMALL[CELL // 2 - 1:CELL // 2 + 2, CELL // 2] = C_YELLOW


# ---------------------------------------------------------------------------
# The walker: a round blue creature with eyes and a mouth. Built from a template so the pupils can look the way it
# is going, the eyes can blink, and the face can go sad. Three sizes (the pit swallows it small).
# ---------------------------------------------------------------------------

_WALKER_CACHE = {}


def walker_pic(scale, body, look="R", blink=False, sad=False, stride=0, happy=False):
    """The walker: a seven-wide, eight-tall round creature with a lit crown, big eyes whose pupils look where it is
    heading, a mouth (small, grin, or frown with a tear) and two little feet that swap as it strides."""
    key = (scale, body, look, blink, sad, stride, happy)
    if key in _WALKER_CACHE:
        return _WALKER_CACHE[key]
    hi = C_LBLUE if body == C_YOU else C_YELLOW
    lg = {"K": C_BLACK, "B": body, "L": hi, "W": C_WHITE, "T": C_LBLUE, "Y": C_YELLOW}
    if scale == 2:
        pupils = "KWKBWKK" if look == "R" else "KKWBKWK"
        if blink:
            eyes = ["KBBBBBK", "KKKBKKK"]
        elif sad:
            eyes = ["KWWBWWK", "KWKBWKK"]            # sad eyes stare down and forward
        else:
            eyes = ["KWWBWWK", pupils]
        if happy:
            mouth = ["KKBBBKK", "KBKKKBK"]            # a wide grin
        elif sad:
            mouth = ["KBKKKBK", "KKBTBKK"]            # a frown with a tear
        else:
            mouth = ["KBBBBBK", "KBBKBBK"]
        feet = (".KK.KK.", "KK...KK")[stride]
        rows = [".KKKKK.", "KLLBBBK"] + eyes + mouth + [".KBBBK.", feet]
    elif scale == 1:
        rows = [".KKK.", "KLBBK", "KBBBK" if blink else "KWKWK", "KBBBK", ".K.K."]
    else:
        rows = ["KKK", "KBK", "KKK"]
    pix = art(rows, lg)
    _WALKER_CACHE[key] = pix
    return pix


# ---------------------------------------------------------------------------
# Pictures, part three: eight caves. Each theme names its rock colour, the dark outline round its corridor, the flower
# colour on lit ground, a backdrop recipe, a wall prop and its drifting extras.
# ---------------------------------------------------------------------------

def _bricks(base, mortar, hi, bw, bh, band=None):
    """Offset courses of blocks: a lit top edge, a dark mortar line. `band` carves a pattern into every third course."""
    a = blank(64, 64, base)
    for y in range(64):
        row, ry = divmod(y, bh)
        off = (row % 2) * (bw // 2)
        for x in range(64):
            rx = (x + off) % bw
            if ry == bh - 1 or rx == bw - 1:
                a[y, x] = mortar
            elif ry == 0:
                a[y, x] = hi
            elif band is not None and row % 3 == 1 and ry == bh // 2 and (rx // 2) % 2 == 0:
                a[y, x] = band
    return a


def _facets(base, line, crack, step_a=12, step_b=20):
    """Slanted ruling that reads as cut ice (kept only for the ice cave)."""
    a = blank(64, 64, base)
    for y in range(64):
        for x in range(64):
            if (x + y) % step_a == 0 or (x + y) % step_a == 1 and (x // 3) % 2:
                a[y, x] = line
            if (x - y) % step_b == 0:
                a[y, x] = crack
    return a


def _spires(base):
    """Crystal cave: big cut prisms growing from the roof and the floor. Each has a pale lit left face, a white ridge,
    a shaded right face (blue checked with black) and a black outline, and a white glint at the tip."""
    a = blank(64, 64, base)
    ups = [(0, 12, 22), (13, 8, 12), (26, 14, 26), (44, 9, 15), (53, 11, 23)]      # from the roof: x, width, length
    downs = [(1, 15, 22), (17, 14, 26), (33, 11, 15), (46, 17, 24)]                  # from the floor: wide at the base
    for grow_down, spires in ((True, ups), (False, downs)):
        for x, w, ln in spires:
            cx = x + w // 2
            for k in range(ln):
                hw = max(0, int(round((w / 2.0) * (1 - k / float(ln)))))
                y = k if grow_down else 63 - k
                for dx in range(-hw, hw + 1):
                    xx = cx + dx
                    if not 0 <= xx < 64:
                        continue
                    if abs(dx) == hw:
                        c = C_BLACK
                    elif dx < 0:
                        c = C_LBLUE
                    elif dx == 0:
                        c = C_WHITE
                    else:
                        c = C_BLACK if (xx + y) % 2 == 0 else C_BLUE
                    a[y, xx] = c
            ty = ln - 1 if grow_down else 64 - ln
            if 0 <= cx < 64:
                a[ty if grow_down else ty, cx] = C_WHITE
    for gx, gy in ((9, 31), (24, 33), (41, 30), (58, 34), (33, 36), (15, 29)):
        a[gy, gx] = C_WHITE
        a[gy - 1, gx] = a[gy + 1, gx] = a[gy, gx - 1] = a[gy, gx + 1] = C_LBLUE
    return a


def _strata(base, line, glow):
    a = blank(64, 64, base)
    for y in range(64):
        if y % 6 == 3:
            for x in range(64):
                if (x + (y // 6) * 5) % 11 < 5:
                    a[y, x] = line
        if y % 12 == 9:
            for x in range(64):
                if (x * 7 + y) % 17 == 0:
                    a[y, x] = glow
    return a


def _waves(base, wave, foam):
    a = blank(64, 64, base)
    for x in range(64):
        for k in range(0, 64, 8):
            y = k + int(round(1.6 * math.sin(x / 3.2 + k)))
            if 0 <= y < 64:
                a[y, x] = wave
                if x % 7 == 2 and y > 0:
                    a[y - 1, x] = foam
    return a


def _lattice(base, line, dot):
    a = blank(64, 64, base)
    for y in range(64):
        for x in range(64):
            if (x + y) % 12 == 0 or (x - y) % 12 == 0:
                a[y, x] = line
            if (x % 12 == 6) and (y % 12 == 0 or y % 12 == 6):
                a[y, x] = dot
    return a


def _moon(a):
    """A fat yellow crescent with a white rim and a few stars, hung in the upper right of the night cave."""
    for y in range(-8, 9):
        for x in range(-8, 9):
            d = x * x + y * y
            bite = (x - 4) ** 2 + (y + 2) ** 2
            if d <= 64 and bite > 52:
                a[26 + y, 49 + x] = C_WHITE if d > 50 else C_YELLOW
    for x, y in ((10, 20), (22, 24), (36, 18), (58, 52), (6, 46), (30, 56)):
        a[y, x] = C_WHITE
        a[y, x + 1] = C_BLUE
    return a


def _glow(a):
    """Lava cave: molten seams (orange over yellow) welling between a few of the courses."""
    for y in (14, 33, 52):
        for x in range(64):
            if (x // 5) % 2 == 0:
                a[y, x] = C_ORANGE
                a[y + 1, x] = C_YELLOW if x % 3 == 0 else C_ORANGE
    return a


def _scatter(a, seed, n, pic):
    """Stamp a small picture at n spread-out spots (deterministic, no random state): moss, cracks, inlay, shells."""
    h, w = pic.shape
    for i in range(n):
        x = (seed * 37 + i * 29 + i * i * 3) % (64 - w)
        y = (seed * 53 + i * 41 + i * i * 5) % (64 - h)
        sub = a[y:y + h, x:x + w]
        sub[pic >= 0] = pic[pic >= 0]
    return a


MOSS = art(("..G.", "GGLG", "LGGG"))
CRACK = art(("K..", "KK.", ".KK", "..K"))
INLAY = art((".Y.", "YOY", ".Y."))
SHELL = art((".P.", "PWP"))
FROST = art(("L.L", ".L.", "L.L"))
RUBBLE = art(("NN.", "KNK"))
SEED = art((".G.", "GYG"))

BACKDROPS = {
    "cellar": lambda: _scatter(_scatter(_bricks(C_MAROON, C_BLACK, C_RED, 8, 4), 3, 9, MOSS), 7, 7, CRACK),
    "crystal": lambda: _scatter(_spires(C_BLUE), 4, 6, GLINT[1:4, 1:4]),
    "night": lambda: _moon(_strata(C_BLACK, C_MAROON, C_BLUE)),
    "lava": lambda: _scatter(_glow(_bricks(C_RED, C_MAROON, C_ORANGE, 10, 5)), 5, 8, RUBBLE),
    "ice": lambda: _scatter(_facets(C_WHITE, C_LBLUE, C_BLUE, 14, 22), 6, 9, FROST),
    "temple": lambda: _scatter(_bricks(C_MAROON, C_BLACK, C_RED, 12, 6, band=C_BLACK), 2, 12, INLAY),
    "sea": lambda: _scatter(_scatter(_waves(C_LBLUE, C_BLUE, C_WHITE), 8, 6, SHELL), 9, 5, SEED),
    "vault": lambda: _lattice(C_BLUE, C_YELLOW, C_LBLUE),
}

# -- wall props: 9x9, two frames each (a flicker, a blink or a sway) --------------------------------------------

PROPS = {
    # a wall torch: iron bracket, a big two-tone flame that leans one way then the other
    "torch": [art(("....Y....", "...YOY...", "..YOWOY..", "..OOYOO..", "...ORO...",
                   "..KKKKK..", "...KNK...", "...KNK...", "..KKKKK..")),
              art((".....Y...", "...YOOY..", "..YOWOY..", "..OOYOO..", "...ORO...",
                   "..KKKKK..", "...KNK...", "...KNK...", "..KKKKK.."))],
    # a cluster of three cut crystals, outlined, with a glint that hops from one tip to the next
    "crystal": [art(("....K....", "...KWK...", "..KLLLK.K", "..KLLBKWK", ".KWLLBKLK",
                     ".KLLBBKLK", "KKLBBBKBK", "KBBBBBKKK", ".KKKKKK..")),
                art(("....K....", "...KLK...", "..KLWLK.K", "..KLLBKLK", ".KLLLBKLK",
                     ".KLLBBKWK", "KKLBBBKBK", "KBBBBBKKK", ".KKKKKK.."))],
    # an owl on a perch: ear tufts, ringed eyes that look left, then right, then shut; beak, breast feathers
    "owl": [art(("N.......N", "NN.....NN", "NNNNNNNNN", "NYYYNYYYN", "NYKWNYKWN",
                 "NNNNONNNN", "NNRNRNRNN", ".NNNNNNN.", "KKOKKKOKK")),
            art(("N.......N", "NN.....NN", "NNNNNNNNN", "NYYYNYYYN", "NYWKNYWKN",
                 "NNNNONNNN", "NNRNRNRNN", ".NNNNNNN.", "KKOKKKOKK")),
            art(("N.......N", "NN.....NN", "NNNNNNNNN", "NNNNNNNNN", "NKKKNKKKN",
                 "NNNNONNNN", "NNRNRNRNN", ".NNNNNNN.", "KKOKKKOKK"))],
    # a fire imp: horns, white-hot eyes, a jagged grin, flames licking from its head
    "fire": [art((".Y.Y.Y.Y.", "KYOYOYOYK", "KOOOOOOOK", "KOWKOWKOK", "KOOOOOOOK",
                  "KOKYKYKOK", "KOOKKKOOK", ".KROOOROK", "..K...K..")),
             art(("..Y.Y.Y..", "KYOYOYOYK", "KOOOOOOOK", "KOKWOKWOK", "KOOOOOOOK",
                  "KOKYKYKOK", "KOOKKKOOK", ".KROOOROK", "..K...K.."))],
    # a snowman: top hat, red scarf, carrot nose, coal buttons; the second frame blinks
    "snowman": [art(("..KKKKK..", "..KWKWK..", "..KWOWK..", ".KRRRRRK.", ".KWWKWWK.",
                     ".KWWWWWK.", ".KWWKWWK.", "..KWWWK..", "...KKK...")),
                art(("..KKKKK..", "..KWWWK..", "..KWOWK..", ".KRRRRRK.", ".KWWKWWK.",
                     ".KWWWWWK.", ".KWWKWWK.", "..KWWWK..", "...KKK..."))],
    # a temple idol: gold crown, carved red brow, yellow eyes that go dark and come back
    "idol": [art(("Y.Y.Y.Y.Y", "KKKKKKKKK", "KRRRRRRRK", "KRYKRKYRK", "KRRRKRRRK",
                  "KRKKKKKRK", "KRKRKRKRK", "KRRRRRRRK", ".KKKKKKK.")),
             art(("Y.Y.Y.Y.Y", "KKKKKKKKK", "KRRRRRRRK", "KRKYRYKRK", "KRRRKRRRK",
                  "KRKKKKKRK", "KRKRKRKRK", "KRRRRRRRK", ".KKKKKKK."))],
    # sea kelp: three fat strands with a darker rib, swaying
    "kelp": [art((".GG...GG.", ".GLG.GG..", "..GGGGG.G", "..GLGGLGG", ".GG.GGGGL",
                  ".GL.GG.GG", "..GGGG.G.", "..GLGG.GG", "...GG..G.")),
             art(("..GG..GG.", ".GGL.GLG.", ".GGGG.GG.", "..GGLGGGG", "..GGGGGL.",
                  "...GG.GG.", "..GGLG.GG", "..GGGG.G.", "...GG..GG"))],
    # a hanging banner: gold rod, a magenta field, a gold cross, a swallow-tailed hem that flutters
    "banner": [art(("YYYYYYYYY", ".MMMMMMM.", ".MMMYMMM.", ".MMYYYMM.", ".MMMYMMM.",
                    ".MMMYMMM.", "..MMMMM..", "..MMYMM..", "...M.M...")),
               art(("YYYYYYYYY", ".MMMMMMM.", ".MMMYMMM.", ".MMYYYMM.", ".MMMYMMM.",
                    ".MMMYMMM.", "..MMMMM..", "..MMYMM..", "....M.M.."))],
}

# -- drifting extras: behind the floor, so they only show through the rock --------------------------------------

PROP_CYCLE = {"owl": (0, 0, 1, 1, 0, 0, 1, 1, 2, 0)}
SPIDER = [art(("..W..", "..W..", "..W..", "..W..", "..W..", "..W..", "K.K.K", ".KKK.", "KWKWK", ".K.K.")),
          art(("..W..", "..W..", "..W..", "..W..", "K.K.K", ".KKK.", "KWKWK", ".K.K.", ".....", ".....")),
          art(("..W..", "..W..", "..W..", "K.K.K", ".KKK.", "KWKWK", ".K.K.", ".....", ".....", "....."))]
# a bat: ear points, red eyes, wings up then down
BAT = [art(("VV.....VV", "VVV.V.VVV", ".VVVVVVV.", "..VRVRV..", "...V.V...")),
       art((".........", "VVVVVVVVV", ".VVVVVVV.", "..VRVRV..", "...V.V..."))]
# a fish: gold body with a white eye and a belly, red tail that flaps
FISH = [art(("..OOOO..R", ".OOOWKOOR", "OOOOOOOOR", ".OYYOOOOR", "..OOOO..R")),
        art(("..OOOO...", ".OOOWKOOR", "OOOOOOOOR", ".OYYOOOOR", "..OOOO..."))]
EMBER = [art(("YO", "OR")), art(("OR", "RR"))]
BUBBLE = [art((".WW.", "W..W", "W..W", ".WW.")), art(("....", ".WW.", ".WW.", "...."))]
SNOW = [art((".B.", "BWB", ".B.")), art(("...", ".W.", "..."))]
STAR = [art(("W",)), art((".W.", "WWW", ".W.")), art(("W",))]
GLITTER = [art(("W",)), art((".Y.", "YWY", ".Y.")), art(("Y",))]
MOTE = [art(("YO", "OY")), art(("OY", "YO"))]

# -- set pieces: big drawn objects that fill whole stretches of rock (2x2, 1x2 or 2x1 cells), two frames each ---------------
# Built with a tiny pen (shapes, not painted specks) and outlined in black. Every piece is a named sprite that only
# swaps picture; none of them does anything, and none is ever placed on a floor cell.

class Pen:
    """A little canvas: fill shapes, then edge() wraps the whole drawing in a black outline."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.a = blank(h, w)

    def fill(self, fn, c):
        for y in range(self.h):
            for x in range(self.w):
                if fn(x, y):
                    self.a[y, x] = c
        return self

    def rect(self, x0, y0, x1, y1, c):
        self.a[max(y0, 0):y1 + 1, max(x0, 0):x1 + 1] = c
        return self

    def ell(self, cx, cy, rx, ry, c):
        return self.fill(lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0, c)

    def dots(self, pts, c):
        for x, y in pts:
            if 0 <= x < self.w and 0 <= y < self.h:
                self.a[y, x] = c
        return self

    def line(self, x0, y0, x1, y1, c, thick=1):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            x = int(round(x0 + (x1 - x0) * i / float(n)))
            y = int(round(y0 + (y1 - y0) * i / float(n)))
            self.rect(x, y, x + thick - 1, y + thick - 1, c)
        return self

    def edge(self, c=C_BLACK):
        src = self.a.copy()
        for y in range(self.h):
            for x in range(self.w):
                if src[y, x] >= 0:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.w and 0 <= ny < self.h and src[ny, nx] >= 0:
                        self.a[y, x] = c
                        break
        return self

    def done(self):
        return self.a


def _prism(p, cx, top, bot, hw, lc=C_LBLUE, dc=C_BLUE):
    """A cut crystal: pointed top, flat base, pale left face, white ridge, shaded right face."""
    for y in range(top, bot + 1):
        half = min(hw, (y - top + 1) // 2)
        for x in range(cx - half, cx + half + 1):
            p.a[y, x] = lc if x < cx else (C_WHITE if x == cx else dc)
    return p


def _arch(x, y, m, w, top):
    """Inside test for a round-topped doorway of width w whose half-circle roof starts at row `top`."""
    r = (w - 1) / 2.0 - m
    cx = (w - 1) / 2.0
    if y < m or not m <= x <= w - 1 - m:
        return False
    return y >= top or ((x - cx) / r) ** 2 + ((y - top) / r) ** 2 <= 1.0


def pc_door(f):
    p = Pen(18, 18).fill(lambda x, y: _arch(x, y, 1, 18, 8), C_BLACK)
    p.fill(lambda x, y: _arch(x, y, 2, 18, 8), C_ORANGE)
    p.dots([(x, y) for x in (5, 8, 11, 14) for y in range(3, 17)], C_MAROON)
    p.rect(2, 10, 15, 10, C_BLACK).rect(2, 15, 15, 15, C_BLACK)
    p.dots([(3, 10), (14, 10), (3, 15), (14, 15)], C_YELLOW)
    p.rect(12, 12, 13, 13, C_YELLOW).dots([(12, 12)], C_BLACK).dots([(4, 5), (4, 6), (3, 8)], C_WHITE)
    p.rect(3, 16, 14, 16, C_YELLOW if f else C_ORANGE)               # a flicker of light under the door
    return p.edge().done()


def pc_cauldron(f):
    p = Pen(18, 9)
    p.dots([(x, 7) for x in (3, 5, 7, 9, 11, 13)], C_YELLOW).dots([(x, 6) for x in (4, 8, 12)], C_ORANGE)
    p.rect(3, 8, 14, 8, C_YELLOW if f else C_ORANGE)
    p.ell(8.5, 4.5, 7.3, 3.3, C_BLACK).ell(8.5, 2.6, 6.3, 1.4, C_GREEN).rect(3, 3, 14, 3, C_BLACK)
    p.dots([(5, 4), (4, 5), (12, 5)], C_BLUE).dots([(6, 2), (11, 2 + f)], C_YELLOW)
    p.dots([(7 + 3 * f, 0), (11 - 4 * f, 1)], C_WHITE)
    return p.edge().done()


def pc_window(f):
    p = Pen(9, 18).fill(lambda x, y: _arch(x, y, 0, 9, 5), C_BLACK)
    p.fill(lambda x, y: _arch(x, y, 1, 9, 5), C_BLUE)
    p.rect(4, 1, 4, 14, C_BLACK).rect(1, 9, 7, 9, C_BLACK).rect(0, 15, 8, 16, C_ORANGE).rect(0, 17, 8, 17, C_BLACK)
    p.dots([(2, 4), (6, 6) if f else (6, 3), (2, 12)], C_WHITE).dots([(6, 12), (6, 13), (7, 12)], C_YELLOW)
    return p.done()


def pc_crystals(f):
    p = Pen(18, 18)
    _prism(p, 9, 1, 16, 3)
    _prism(p, 4, 6, 16, 2, C_WHITE, C_LBLUE)
    _prism(p, 14, 8, 16, 2)
    p.dots([(8, 3 + 5 * f), (3, 8)] if f else [(9, 2), (14, 10)], C_WHITE)
    p.rect(1, 17, 16, 17, C_LBLUE)
    return p.edge().done()


def pc_spire(f):
    p = Pen(9, 18)
    _prism(p, 4, 1, 16, 3, C_LBLUE, C_BLUE)
    p.dots([(4, 3 + 6 * f)], C_YELLOW).dots([(2, 12)], C_WHITE)
    p.rect(0, 17, 8, 17, C_LBLUE)
    return p.edge().done()


def pc_cluster(f):
    # three big cut gems of different heights on a lit rock bed, a gold glint travelling between frames
    p = Pen(18, 9)
    p.rect(0, 7, 17, 8, C_BLUE).rect(0, 7, 17, 7, C_LBLUE)
    for cx, top, hw, lc in ((3, 3, 2, C_LBLUE), (8, 0, 3, C_WHITE), (14, 2, 3, C_LBLUE)):
        _prism(p, cx, top, 7, hw, lc, C_BLUE)
    p.dots([(8, 2 + f * 3), (14, 4 - f), (3, 5)], C_YELLOW).dots([(7, 5)], C_WHITE)
    return p.edge().done()


def pc_tree(f):
    # a night tree: green leafy crown with lit tufts and red fruit, orange trunk with roots and a hollow with eyes
    p = Pen(18, 18)
    p.rect(7, 9, 11, 17, C_ORANGE).rect(10, 9, 11, 17, C_RED).rect(4, 16, 14, 17, C_ORANGE)
    p.dots([(7, y) for y in range(10, 16, 3)], C_YELLOW)
    p.ell(9, 5.5, 8.0, 5.2, C_GREEN).ell(5, 8, 3.2, 2.2, C_GREEN).ell(13, 8, 3.2, 2.2, C_GREEN)
    p.ell(6, 3.5, 3.0, 1.8, C_YELLOW).dots([(5, 3), (6, 3)], C_WHITE)
    p.fill(lambda x, y: y >= 6 and p.a[y, x] == C_GREEN and (x + 2 * y) % 5 == 0, C_BLACK)
    p.dots([(3, 6), (14, 5), (9, 8 + f), (11, 3)], C_RED)
    p.rect(8, 11, 10, 14, C_BLACK)
    p.dots([(8, 12), (10, 12)] if f else [(8, 11), (10, 11)], C_WHITE)
    return p.edge().done()


def pc_lamp(f):
    p = Pen(9, 18)
    p.rect(4, 6, 4, 17, C_MAROON).rect(2, 16, 6, 17, C_MAROON).rect(4, 1, 6, 1, C_MAROON)
    sw = 1 if f else 0
    p.rect(3 + sw, 2, 7 + sw, 7, C_BLACK).rect(4 + sw, 3, 6 + sw, 6, C_YELLOW)
    p.dots([(5 + sw, 4), (5 + sw, 5)], C_WHITE if f else C_ORANGE).dots([(3 + sw, 8), (7 + sw, 8)], C_YELLOW)
    return p.done()


def pc_mushrooms(f):
    p = Pen(18, 9)
    for cx, cy, rx, col in ((4, 4, 3.5, C_RED), (11, 3, 4.5, C_MAGENTA), (15, 5, 2.5, C_ORANGE)):
        p.rect(int(cx) - 1, int(cy) + 1, int(cx), 8, C_WHITE)
        p.ell(cx, cy, rx, 2.6, col)
        p.dots([(int(cx) - 1, int(cy) - 1), (int(cx) + 1, int(cy))], C_WHITE)
    p.dots([(7, 1), (2 + 8 * f, 0)], C_YELLOW)
    return p.edge().done()


def pc_demon(f):
    p = Pen(18, 18)
    p.line(3, 2, 5, 5, C_YELLOW, 2).line(14, 2, 12, 5, C_YELLOW, 2)
    p.ell(8.5, 9.5, 7.5, 7.0, C_ORANGE).fill(lambda x, y: y >= 14 and (x - 8.5) ** 2 + (y - 9.5) ** 2 <= 49, C_RED)
    p.rect(3, 8, 6, 10, C_WHITE).rect(11, 8, 14, 10, C_WHITE)
    if f:
        p.rect(3, 9, 6, 9, C_BLACK).rect(11, 9, 14, 9, C_BLACK)
    else:
        p.rect(5, 8, 6, 10, C_BLACK).rect(11, 8, 12, 10, C_BLACK)
    p.rect(3, 6, 6, 6, C_RED).rect(11, 6, 14, 6, C_RED).rect(5, 12, 12, 15, C_BLACK)
    p.dots([(x, 12) for x in (5, 7, 9, 11)], C_YELLOW).dots([(8, 11), (9, 11)], C_RED)
    p.dots([(7 + 3 * f, 1), (9, 0), (10 - 3 * f, 1)], C_YELLOW)
    return p.edge().done()


def pc_lavafall(f):
    p = Pen(9, 18)
    p.rect(0, 0, 8, 2, C_MAROON).rect(0, 0, 8, 0, C_RED)
    p.rect(1, 3, 7, 15, C_ORANGE).rect(1, 3, 1, 15, C_RED).rect(7, 3, 7, 15, C_RED)
    p.dots([(x, y) for x in range(2, 7) for y in range(3, 16) if (y + 2 * f + (x // 2) * 3) % 7 < 2], C_YELLOW)
    p.rect(0, 16, 8, 17, C_RED).rect(1, 16, 7, 16, C_YELLOW if f else C_ORANGE)
    return p.edge().done()


def pc_volcano(f):
    # a stout cone with a lava lip, glowing streaks, a plume of sparks and a smoke puff that swaps sides
    p = Pen(18, 9)
    p.fill(lambda x, y: y >= 2 and abs(x - 8.5) <= 3.5 + (y - 2) * 1.0, C_MAROON)
    p.fill(lambda x, y: y >= 2 and 0 < x - 8.5 <= 3.5 + (y - 2) * 1.0 and (x + y) % 3 == 0, C_RED)
    p.rect(5, 1, 12, 2, C_ORANGE).rect(6, 1, 11, 1, C_YELLOW)
    p.line(8, 3, 6, 8, C_ORANGE).line(10, 3, 12, 8, C_ORANGE).line(9, 3, 9, 6, C_YELLOW)
    p.dots([(7 + 2 * f, 0), (11 - 3 * f, 0), (9, 0)], C_YELLOW)
    return p.edge().done()


def pc_snowman(f):
    p = Pen(18, 18)
    p.line(4, 12, 1, 9, C_MAROON).line(14, 12, 17, 9, C_MAROON).dots([(2, 8), (16, 8)], C_MAROON)
    p.ell(9, 13.5, 5.5, 4.2, C_WHITE).ell(9, 6.5, 4.0, 3.5, C_WHITE)
    p.fill(lambda x, y: x >= 11 and y >= 11 and (x - 9) ** 2 / 30.0 + (y - 13.5) ** 2 / 17.6 <= 1.0, C_LBLUE)
    p.rect(6, 0, 12, 2, C_BLACK).rect(5, 3, 13, 3, C_BLACK).rect(6, 2, 12, 2, C_RED)
    p.rect(5, 10, 13, 10, C_RED).rect(11, 11, 12, 13, C_RED)
    p.rect(9, 6, 12, 6, C_ORANGE).dots([(7, 5), (10, 5)] if not f else [(7, 6), (10, 6)], C_BLACK)
    p.dots([(9, 12), (9, 14), (9, 16)], C_BLACK).dots([(7, 8), (8, 8), (9, 8), (10, 8)] if False else [], C_BLACK)
    return p.edge().done()


def pc_fir(f):
    p = Pen(9, 18)
    for top, bot, hw in ((1, 6, 3), (5, 11, 4), (9, 15, 4)):
        p.fill(lambda x, y, t=top, b=bot, h=hw: t <= y <= b and abs(x - 4) <= (y - t) * h // (b - t) + (1 if y > t else 0), C_GREEN)
    p.dots([(x, y) for y in range(1, 15) for x in range(9) if p.a[y, x] == C_GREEN and (x + y) % 4 == 0], C_WHITE)
    p.rect(4, 15, 4, 17, C_MAROON).rect(3, 16, 5, 17, C_MAROON).dots([(4, 0)], C_YELLOW if f else C_WHITE)
    return p.edge().done()


def pc_igloo(f):
    p = Pen(18, 9)
    p.fill(lambda x, y: ((x - 8.5) / 8.0) ** 2 + ((y - 8.5) / 8.0) ** 2 <= 1.0, C_WHITE)
    p.fill(lambda x, y: p.a[y, x] == C_WHITE and y < 8 and (y % 3 == 2 or (x + 3 * (y // 3)) % 6 == 0), C_LBLUE)
    p.rect(7, 5, 10, 8, C_BLACK).rect(8, 4, 9, 4, C_BLACK).rect(8, 6, 9, 8, C_YELLOW if f else C_ORANGE)
    return p.edge().done()


def pc_totem(f):
    p = Pen(9, 18)
    p.a[0:9] = PROPS["idol"][f]
    p.a[9:18] = remap(PROPS["idol"][1 - f], {C_RED: C_BLUE, C_YELLOW: C_ORANGE})
    return p.done()


def pc_sun(f):
    p = Pen(18, 18)
    for k in range(12):
        ang = (k * 30 + f * 15) * math.pi / 180.0
        for r in (7.2, 8.0):
            p.dots([(int(round(8.5 + r * math.cos(ang))), int(round(8.5 + r * math.sin(ang))))], C_YELLOW if k % 2 == f else C_ORANGE)
    p.ell(8.5, 8.5, 6.0, 6.0, C_ORANGE).ell(8.5, 8.5, 5.0, 5.0, C_YELLOW)
    p.rect(5, 6, 7, 7, C_BLACK).rect(10, 6, 12, 7, C_BLACK)
    if f:
        p.rect(5, 7, 7, 7, C_YELLOW)
    p.dots([(6, 6), (11, 6)], C_WHITE).dots([(5, 10), (12, 10)], C_RED).rect(7, 11, 10, 11, C_BLACK).dots([(6, 10), (11, 10)], C_BLACK)
    return p.edge().done()


def pc_altar(f):
    p = Pen(18, 9)
    p.rect(1, 5, 16, 8, C_MAROON).rect(1, 5, 16, 5, C_RED).dots([(x, 7) for x in range(3, 15, 2)], C_YELLOW)
    for bx in (3, 12):
        p.rect(bx, 3, bx + 3, 4, C_BLACK)
        p.dots([(bx + 1, 2), (bx + 2, 2 - f * 0), (bx + 1 + f, 1)], C_ORANGE).dots([(bx + 1 + f, 2)], C_YELLOW).dots([(bx + 2 - f, 0)], C_YELLOW)
    return p.edge().done()


def pc_coral(f):
    p = Pen(18, 18)
    s = 1 if f else -1
    p.rect(8, 11, 10, 17, C_MAGENTA).rect(5, 16, 13, 17, C_MAGENTA)
    for tx, ty, ax, col in ((3 + s, 3, 8, C_MAGENTA), (9 + s, 1, 9, C_LMAGENTA), (15 + s, 4, 10, C_MAGENTA), (1, 10, 8, C_ORANGE), (16, 9, 10, C_ORANGE)):
        p.line(ax, 13, tx, ty, col, 2)
        p.ell(tx, ty, 1.6, 1.6, C_YELLOW)
    return p.edge().done()


def pc_kelp(f):
    p = Pen(9, 18)
    for cx, ph in ((2, 0), (6, 2)):
        for y in range(0, 18):
            x = cx + int(round(1.0 * math.sin((y + f * 3 + ph) / 3.0)))
            p.rect(x - 1, y, x + 1, y, C_GREEN)
    return p.edge().done()


def pc_chest(f):
    p = Pen(18, 9)
    p.rect(2, 4, 15, 8, C_MAROON).rect(2, 4, 15, 4, C_ORANGE).rect(2, 6, 15, 6, C_ORANGE).rect(8, 4, 9, 8, C_YELLOW)
    p.ell(8.5, 4, 6.5, 2.0, C_YELLOW).dots([(5, 3), (11, 3), (8, 2)], C_ORANGE).dots([(6, 3), (13 - 6 * f, 2)], C_RED)
    p.rect(2, 0, 15, 1, C_MAROON).rect(2, 0, 15, 0, C_ORANGE)
    p.dots([(4 + 9 * f, 1), (5 + 9 * f, 1), (4 + 9 * f, 0)], C_WHITE)
    return p.edge().done()


def pc_armor(f):
    p = Pen(9, 18)
    p.rect(3, 0, 5, 1, C_MAGENTA).dots([(6, 1), (6, 2)], C_MAGENTA)
    p.ell(4, 5, 3.3, 3.6, C_LBLUE).rect(2, 5, 6, 5, C_BLACK).dots([(3, 5), (5, 5)] if not f else [(3, 5)], C_YELLOW)
    p.rect(1, 9, 7, 14, C_LBLUE).rect(5, 9, 7, 14, C_BLUE).rect(2, 9, 2, 12, C_WHITE).rect(1, 13, 7, 13, C_YELLOW)
    p.rect(2, 15, 3, 17, C_BLUE).rect(5, 15, 6, 17, C_BLUE).dots([(4, 10), (4, 11)], C_RED)
    return p.edge().done()


def pc_treasure(f):
    p = Pen(18, 9)
    p.ell(8.5, 9, 8.3, 6.8, C_YELLOW)
    p.dots([(x, y) for x in range(18) for y in range(9) if p.a[y, x] == C_YELLOW and (x * 3 + y * 5) % 7 == 0], C_ORANGE)
    p.rect(4, 4, 5, 5, C_RED).rect(11, 3, 12, 4, C_LBLUE).rect(8, 2, 9, 3, C_GREEN).dots([(5 + 6 * f, 3), (12 - 6 * f, 5)], C_WHITE)
    return p.edge().done()


def pc_shield(f):
    p = Pen(18, 18)
    p.line(1, 1, 16, 16, C_LBLUE, 2).line(16, 1, 1, 16, C_LBLUE, 2).dots([(0, 0), (17, 0)], C_YELLOW)
    p.ell(8.5, 8.5, 7.5, 7.5, C_ORANGE).ell(8.5, 8.5, 6.4, 6.4, C_BLUE)
    p.fill(lambda x, y: (x - 8.5) ** 2 + (y - 8.5) ** 2 <= 40 and ((x < 8.5) == (y < 8.5)), C_YELLOW)
    p.ell(8.5, 8.5, 2.6, 2.6, C_RED).dots([(8, 7), (9, 7)], C_WHITE)
    p.dots([(3, 3), (13, 14)] if f else [(13, 3), (3, 14)], C_WHITE)
    return p.edge().done()


def pc_reef(f):
    # brain-coral domes with ridges and an orange anemone that sways: round, not forked
    p = Pen(18, 9)
    p.ell(4.5, 8, 4.6, 5.2, C_ORANGE).ell(13, 8, 4.4, 4.2, C_MAGENTA)
    p.fill(lambda x, y: x < 9 and p.a[y, x] == C_ORANGE and (x + y) % 3 == 0, C_RED)
    p.fill(lambda x, y: x > 9 and p.a[y, x] == C_MAGENTA and (x - y) % 3 == 0, C_LMAGENTA)
    p.dots([(3, 5), (4, 4)], C_YELLOW).dots([(12, 6), (13, 6)], C_WHITE)
    for tx in (8, 9, 10):
        p.rect(tx, 2 + (1 if (tx + f) % 2 else 0), tx, 8, C_GREEN)
    p.dots([(8, 1 + f), (10, 2 - f)], C_YELLOW)
    p.rect(0, 8, 17, 8, C_ORANGE)
    return p.edge().done()


def pc_pillar(f):
    p = Pen(9, 18)
    p.rect(1, 1, 7, 3, C_YELLOW).rect(1, 1, 7, 1, C_WHITE).rect(2, 4, 6, 14, C_BLUE).rect(2, 4, 3, 14, C_LBLUE)
    p.dots([(5, y) for y in range(5, 14, 2)], C_BLACK).rect(1, 15, 7, 17, C_YELLOW)
    p.rect(4, 8, 4, 9, C_RED if f else C_ORANGE).dots([(3, 8)], C_WHITE)
    return p.edge().done()


# name -> (builder, footprint in cells: wide, tall)
PIECES = {
    "door": (pc_door, 2, 2), "cauldron": (pc_cauldron, 2, 1), "window": (pc_window, 1, 2),
    "crystals": (pc_crystals, 2, 2), "spire": (pc_spire, 1, 2), "cluster": (pc_cluster, 2, 1),
    "tree": (pc_tree, 2, 2), "lamp": (pc_lamp, 1, 2), "mushrooms": (pc_mushrooms, 2, 1),
    "demon": (pc_demon, 2, 2), "lavafall": (pc_lavafall, 1, 2), "volcano": (pc_volcano, 2, 1),
    "snowman": (pc_snowman, 2, 2), "fir": (pc_fir, 1, 2), "igloo": (pc_igloo, 2, 1),
    "totem": (pc_totem, 1, 2), "sun": (pc_sun, 2, 2), "altar": (pc_altar, 2, 1),
    "coral": (pc_coral, 2, 2), "kelp": (pc_kelp, 1, 2), "chest": (pc_chest, 2, 1),
    "armor": (pc_armor, 1, 2), "reef": (pc_reef, 2, 1), "pillar": (pc_pillar, 1, 2), "shield": (pc_shield, 2, 2), "treasure": (pc_treasure, 2, 1),
}
_PIECE_FRAMES = {}


def piece_frames(name):
    """Both frames of a set piece, built once."""
    if name not in _PIECE_FRAMES:
        _PIECE_FRAMES[name] = [PIECES[name][0](f) for f in (0, 1)]
    return _PIECE_FRAMES[name]


# The red-and-dim look of a lost run, applied to the backdrop, the set pieces and the top band alike.
DEAD_MAP = {C_BLUE: C_MAROON, C_LBLUE: C_RED, C_WHITE: C_ORANGE, C_BLACK: C_MAROON, C_YELLOW: C_RED,
            C_RED: C_MAROON, C_MAROON: C_BLACK, C_ORANGE: C_RED, C_GREEN: C_MAROON, C_MAGENTA: C_MAROON,
            C_LMAGENTA: C_RED, C_PURPLE: C_MAROON}
_DEAD_CACHE = {}


def _dead(pic):
    k = id(pic)
    if k not in _DEAD_CACHE:
        _DEAD_CACHE[k] = (pic, remap(pic, DEAD_MAP))      # keep `pic` alive so its id is never reused
    return _DEAD_CACHE[k][1]


# small life that wanders: a rat, a jellyfish, a scarab, a falling drip
RAT = [art((".....K.", "KK.KKKK", "KNNNNRK", ".K.K.K.")), art((".....K.", "K..KKKK", "KNNNNRK", "..K.K.K."[:7]))]
JELLY = [art((".MMMM.", "MPPPPM", "MMMMMM", "M.M.M.", ".M.M.M")), art((".MMMM.", "MPPPPM", "MMMMMM", ".M.M.M", "M.M.M."))]
SCARAB = [art((".RR.", "RYYR", "ROOR", "K..K")), art((".RR.", "RYYR", "ROOR", ".KK."))]
DROP = [art(("L", "B")), art(("B", "L"))]

# theme: rock colour, outline round the corridor, ring on rubble, flower, backdrop, prop(+how many), drifters
THEMES = [
    dict(rock=C_MAROON, edge=C_BLACK, rubble=C_BLACK, flower=C_YELLOW, back="cellar", prop="torch", props=4,
         pieces=("door", "cauldron", "window", "window"),
         roam=[("bob", SPIDER, 2), ("rise", MOTE, 4), ("row", RAT, 1), ("fall", DROP, 3)]),
    dict(rock=C_BLUE, edge=C_BLACK, rubble=C_BLACK, flower=C_WHITE, back="crystal", prop="crystal", props=3,
         pieces=("crystals", "spire", "cluster", "spire"),
         roam=[("twinkle", GLITTER, 8), ("rise", MOTE, 3)]),
    dict(rock=C_BLACK, edge=C_BLUE, rubble=C_BLUE, flower=C_YELLOW, back="night", prop="owl", props=2,
         pieces=("tree", "lamp", "mushrooms", "lamp"),
         roam=[("row", BAT, 2), ("twinkle", STAR, 8), ("rise", MOTE, 3)]),
    dict(rock=C_RED, edge=C_BLACK, rubble=C_BLACK, flower=C_YELLOW, back="lava", prop="fire", props=2,
         pieces=("demon", "lavafall", "volcano", "lavafall"),
         roam=[("rise", EMBER, 8), ("row", EMBER, 2)]),
    dict(rock=C_WHITE, edge=C_BLACK, rubble=C_BLACK, flower=C_BLUE, back="ice", prop="snowman", props=2,
         pieces=("snowman", "igloo", "fir", "fir", "igloo"),
         roam=[("fall", SNOW, 10), ("twinkle", GLITTER, 3)]),
    dict(rock=C_MAROON, edge=C_BLACK, rubble=C_BLACK, flower=C_ORANGE, back="temple", prop="idol", props=2,
         pieces=("sun", "altar", "totem", "altar", "totem"),
         roam=[("twinkle", GLITTER, 4), ("rise", MOTE, 3), ("row", SCARAB, 2)]),
    dict(rock=C_LBLUE, edge=C_BLACK, rubble=C_BLUE, flower=C_WHITE, back="sea", prop="kelp", props=2,
         pieces=("coral", "chest", "reef", "reef", "kelp", "reef"),
         roam=[("row", FISH, 3), ("rise", BUBBLE, 6), ("rise", JELLY, 2)]),
    dict(rock=C_BLUE, edge=C_BLACK, rubble=C_BLACK, flower=C_YELLOW, back="vault", prop="banner", props=3,
         pieces=("shield", "armor", "treasure", "pillar", "armor", "pillar"),
         roam=[("twinkle", GLITTER, 8), ("rise", MOTE, 3)]),
]


# ---------------------------------------------------------------------------
# Pictures, part four: floor tiles. Built once per (look, theme, which sides touch rock) and cached.
# ---------------------------------------------------------------------------

_TILE_CACHE = {}


def _flower(t, x, y, colour):
    t[y, x + 1] = colour
    t[y + 1, x] = colour
    t[y + 1, x + 2] = colour
    t[y + 2, x + 1] = colour
    t[y + 1, x + 1] = C_YELLOW if colour != C_YELLOW else C_ORANGE


def _outline(t, mask, edge):
    """Dark line on every side of a tile that borders rock (mask = up, down, left, right neighbour is floor)."""
    up, down, left, right = mask
    if not up:
        t[0, :] = edge
    if not down:
        t[CELL - 1, :] = edge
    if not left:
        t[:, 0] = edge
    if not right:
        t[:, CELL - 1] = edge


# Surface details for dark ground, per cave. Each is (row, col, colour) pixels inside the lower half of the 9x9 tile.
# Lower half only: the retreat flames sit in rows 1-3 and must read on clean ground.
def _surface(ti, variant):
    v = variant % 3
    sx = (0, 1, 2)[v]
    if ti == 0:       # cellar flagstones: a mortar seam with a staggered joint
        return [(5, c, C_BLACK) for c in range(1, 8)] + [(r, 3 + sx, C_BLACK) for r in (6, 7)] + [(6, 7, C_LBLUE)]
    if ti == 1:       # crystal cave: frosted facets, a bright cross glint
        return [(5, 2 + sx, C_LBLUE), (6, 1 + sx, C_LBLUE), (6, 2 + sx, C_WHITE), (6, 3 + sx, C_LBLUE), (7, 2 + sx, C_LBLUE),
                (5, 7, C_BLUE), (6, 6, C_BLUE), (7, 5, C_BLUE)]
    if ti == 2:       # night cave: damp ground with blue starlit puddles
        return [(5, 1 + sx, C_BLUE), (5, 2 + sx, C_BLUE), (6, 4 + sx, C_BLUE), (6, 5 + sx, C_BLUE), (7, 2, C_BLACK), (7, 7, C_BLACK)]
    if ti == 3:       # lava cave: hot red cracks with an orange core
        return [(5, 1 + sx, C_RED), (6, 2 + sx, C_RED), (7, 3 + sx, C_RED), (6, 4 + sx, C_ORANGE), (7, 5 + sx, C_RED), (5, 6, C_RED)]
    if ti == 4:       # ice cave: slick diagonal sheen
        return [(5, 6, C_LBLUE), (6, 5, C_LBLUE), (7, 4, C_LBLUE), (6, 2 + sx, C_WHITE), (7, 1 + sx, C_LBLUE)]
    if ti == 5:       # temple: carved studs set in the slab
        return [(5, 2, C_BLACK), (5, 3, C_BLACK), (5, 5, C_BLACK), (5, 6, C_BLACK), (7, 2 + sx, C_BLACK), (7, 3 + sx, C_BLACK)]
    if ti == 6:       # sea ruin: wet ripples, two swells deep
        return [(5, 1, C_BLUE), (5, 2, C_BLUE), (5, 5 + sx % 2, C_BLUE), (6, 3, C_BLUE), (6, 4, C_BLUE), (7, 1 + sx, C_BLUE),
                (7, 2 + sx, C_BLUE)]
    return [(5, 2, C_BLUE), (5, 4, C_BLUE), (5, 6, C_BLUE), (6, 3, C_LBLUE), (6, 5, C_LBLUE), (7, 2, C_BLUE), (7, 4, C_BLUE),
            (7, 6, C_BLUE)]    # vault: a checker of tiny studs


# The sparkle on lit ground, per cave: two or three pixels inside the lower half.
def _lit_detail(ti):
    if ti == 0:
        return [(7, 2, C_BLACK), (7, 3, C_BLACK), (6, 6, C_BLACK)]            # moss crumbs
    if ti == 1:
        return [(6, 6, C_WHITE), (7, 2, C_LBLUE)]
    if ti == 2:
        return [(7, 2, C_BLUE), (6, 6, C_BLUE), (7, 7, C_BLUE)]
    if ti == 3:
        return [(7, 3, C_ORANGE), (6, 7, C_ORANGE), (7, 4, C_YELLOW)]
    if ti == 4:
        return [(7, 3, C_LBLUE), (6, 6, C_LBLUE), (7, 4, C_WHITE)]
    if ti == 5:
        return [(7, 2, C_BLACK), (7, 6, C_BLACK), (6, 4, C_YELLOW)]
    if ti == 6:
        return [(7, 3, C_LBLUE), (7, 4, C_LBLUE), (6, 6, C_BLUE)]
    return [(7, 3, C_YELLOW), (6, 6, C_LBLUE), (7, 7, C_YELLOW)]


def tile(kind, ti, mask, variant):
    """kind: lit | lit_plain | dark | scar | cut | pitfloor ; ti: theme index."""
    key = (kind, ti, mask, variant)
    if key in _TILE_CACHE:
        return _TILE_CACHE[key]
    th = THEMES[ti]
    if kind in ("lit", "lit_plain"):
        t = blank(CELL, CELL, C_LIT)
        t[1, 1:4] = C_WHITE                      # a bright lip along the top-left of the slab
        t[2, 1] = C_WHITE
        for r, c, col in _lit_detail(ti):
            t[r, c] = col
        if kind == "lit":
            fx, fy = ((5, 4), (1, 5), (5, 5))[variant % 3]
            _flower(t, fx, fy, th["flower"])
        _outline(t, mask, th["edge"])
    elif kind == "dark":
        t = blank(CELL, CELL, C_DARK)
        t[1, 1:3] = C_LBLUE if variant % 4 == 0 else C_DARK    # now and then a faint glimmer on the slab edge
        for r, c, col in _surface(ti, variant):
            t[r, c] = col
        _outline(t, mask, th["edge"])
    elif kind == "scar":
        t = blank(CELL, CELL, C_SCAR)
        for i in range(CELL):
            t[i, i] = C_MAROON
            t[i, CELL - 1 - i] = C_MAROON
        t[0, :] = C_BLACK
        t[CELL - 1, :] = C_BLACK
        t[:, 0] = C_BLACK
        t[:, CELL - 1] = C_BLACK
    elif kind == "cut":
        t = blank(CELL, CELL, th["rock"])
        t[1, 1:CELL - 1] = th["rubble"]
        t[CELL - 2, 1:CELL - 1] = th["rubble"]
        t[1:CELL - 1, 1] = th["rubble"]
        t[1:CELL - 1, CELL - 2] = th["rubble"]
        t[3, 3:5] = C_MAROON if th["rock"] != C_MAROON else C_BLACK     # a few fallen stones
        t[5, 5:7] = C_BLACK if th["rock"] != C_BLACK else C_MAROON
        t[4, 3] = t[6, 4] = C_ORANGE if th["rock"] != C_ORANGE else C_RED
    else:                                          # pitfloor: bare rock where the floor gave way
        t = blank(CELL, CELL, th["rock"])
        t[2, 2:4] = th["rubble"]
        t[6, 5:8] = th["rubble"]
        _outline(t, mask, th["edge"])
    _TILE_CACHE[key] = t
    return t


def marks_pic(n, hot):
    """The row of flames above a cell's corner: n of them (0-2); `hot` of them burning red."""
    key = ("marks", n, hot)
    if key in _TILE_CACHE:
        return _TILE_CACHE[key]
    a = blank(3, CELL)
    if n >= 1:
        a[:, 1:4] = FLAME_HOT if hot >= n else FLAME
    if n >= 2:
        a[:, CELL - 4:CELL - 1] = FLAME_HOT if hot >= 1 else FLAME
    _TILE_CACHE[key] = a
    return a


# Emblems for the two ends of the top band, one per cave (5x5): flame, gem, moon, ember, flake, sun, shell, star.
EMBLEMS = [art(("..Y..", ".YOY.", "YOWOY", ".ORO.", "..K..")),
           art(("..W..", ".LWL.", "LLBLL", ".LBL.", "..L..")),
           art((".YYY.", "YY...", "Y....", "YY...", ".YYY.")),
           art(("..Y..", ".YOY.", "YOROY", ".ORO.", "..R..")),
           art(("W.W.W", ".WLW.", "WLBLW", ".WLW.", "W.W.W")),
           art(("Y.Y.Y", ".YYY.", "YYOYY", ".YYY.", "Y.Y.Y")),
           art((".OOO.", "OYYYO", "OYOYO", "OYYYO", ".OOO.")),
           art(("..Y..", "..Y..", "YYWYY", ".YYY.", "Y...Y"))]

_BANDS = {}


def band_pic(ti, x0, x1):
    """The top band: a black plate under the slots and the step bar, theme-coloured masonry with a gold edge and an
    emblem at each end, so even a level with no keys has a finished-looking strip."""
    key = (ti, x0, x1)
    if key in _BANDS:
        return _BANDS[key]
    th = THEMES[ti]
    x0, x1 = max(0, x0), min(64, x1)
    a = blank(HUD_H, 64, th["rock"])
    for y in range(HUD_H):                                   # small brick courses in the rock colour
        for x in range(64):
            off = 3 if (y // 3) % 2 else 0
            if y % 3 == 2 or (x + off) % 6 == 5:
                a[y, x] = th["edge"] if th["edge"] != th["rock"] else C_BLACK
    a[HUD_H - 1, :] = C_ORANGE                               # gold trim along the bottom
    a[0, :] = C_BLACK
    a[0:HUD_H - 1, x0:x1] = C_BLACK                          # the plate behind the slots, the gate and the bar
    a[HUD_H - 1, x0:x1] = C_YELLOW
    a[0:HUD_H - 1, x0] = a[0:HUD_H - 1, x1 - 1] = C_ORANGE
    gem = EMBLEMS[ti]
    for gx in ((x0 - 5) // 2 - 2, (x1 + 64) // 2 - 3):       # one centred in each end piece (if the piece is wide enough)
        if gx >= 0 and gx + 5 <= 64 and (gx + 5 <= x0 - 1 or gx >= x1 + 1):
            a[2:7, gx:gx + 5] = np.where(gem >= 0, gem, C_BLACK)
    _BANDS[key] = a
    return a


_BAR_CACHE = {}


def bar_pic(full, left, tick):
    """The steps-left bar: two thin white lines between gold end caps. The top line drains first from its right end,
    then the bottom one, as before. A spark sits where it is burning down."""
    key = (full, left, tick)
    if key in _BAR_CACHE:
        return _BAR_CACHE[key]
    half = (full + 1) // 2
    a = blank(2, half + 2)
    a[:, 0] = C_ORANGE
    a[:, half + 1] = C_ORANGE
    top = max(0, left - half)
    bottom = min(left, half)
    a[0, 1:1 + top] = C_WHITE
    a[1, 1:1 + bottom] = C_WHITE
    if 0 < left < full:
        row, col = (0, 1 + top) if left > half else (1, 1 + bottom)
        if col <= half:
            a[row, col] = C_YELLOW if tick % 2 else C_ORANGE
    _BAR_CACHE[key] = a
    return a


# ---------------------------------------------------------------------------
# The game. paint(vis) turns (rules state, the frame's overrides) into sprites; nothing else draws.
# ---------------------------------------------------------------------------

L_BACK, L_PIECE, L_ROAM, L_FLOOR, L_OBJ, L_MARK, L_FX, L_WALK, L_BAND, L_HUD, L_TOP = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12


class Eh02(ARCBaseGame):
    def __init__(self):
        self.core = Core(LEVELS[0])
        self.vis = {}
        self.anim = None
        self.budget = self.steps = BUDGETS[0]
        self.clock = 0
        self.face = "R"
        self.spr = {}
        self.cur = {}
        self.lv = None

        levels = [Level(sprites=[], grid_size=(64, 64), data=ldef, name=ldef["name"])
                  for ldef in LEVELS]
        super().__init__(
            game_id="eh02",
            levels=levels,
            camera=Camera(x=0, y=0, width=64, height=64, background=C_BLACK, letter_box=C_BLACK,
                          interfaces=[]),
            debug=False,
            win_score=len(levels),
            available_actions=list(ACTIONS),
        )

    # -- sprite plumbing ------------------------------------------------------

    def put(self, name, pix, x, y, layer, tags=()):
        """Create the named sprite once, then only touch it when its picture or place changed."""
        x, y = int(x), int(y)
        s = self.spr.get(name)
        if s is None:
            s = Sprite(pixels=pix, name=name, x=x, y=y, layer=layer, collidable=False, tags=list(tags))
            self.lv.add_sprite(s)
            self.spr[name] = s
            self.cur[name] = (pix, x, y, True)
            return s
        old = self.cur[name]
        if old[0] is pix and old[1] == x and old[2] == y and old[3]:
            return s
        if old[0] is not pix:
            s.pixels = pix
        if old[1] != x or old[2] != y:
            s.set_position(x, y)
        if not old[3]:
            s.set_visible(True)
        self.cur[name] = (pix, x, y, True)
        return s

    def hide(self, name):
        s = self.spr.get(name)
        if s is not None and self.cur[name][3]:
            s.set_visible(False)
            o = self.cur[name]
            self.cur[name] = (o[0], o[1], o[2], False)

    # -- level set-up: the cave itself ---------------------------------------

    def on_set_level(self, level: Level) -> None:
        self.core = Core(LEVELS[self.level_index])
        self.vis = {}
        self.anim = None
        self.budget = self.steps = BUDGETS[self.level_index]   # a full bar on every entry and RESET
        self.face = "R"
        self.lv = level
        self.spr = {}
        self.cur = {}
        ti = self.level_index
        self.theme = THEMES[ti]
        rows = LEVELS[ti]["map"]
        # wall cells in a stable scattered order: props, hanging things and sparkles go on these
        walls = [(c, r) for r in range(GH) for c in range(GW) if rows[r][c] == WALL]
        walls.sort(key=lambda p: (p[0] * 7 + p[1] * 13 + ti * 5) % 11 * 100 + p[0] * 10 + p[1])
        # set pieces take whole stretches of rock first (biggest first, each where it fits), small props fill the rest
        taken = set()
        self.placed = []
        for k, name in enumerate(self.theme["pieces"]):
            _, cw, ch = PIECES[name]
            spots = [(c, r) for r in range(GH - ch + 1) for c in range(GW - cw + 1)
                     if all(rows[r + j][c + i] == WALL and (c + i, r + j) not in taken
                            for i in range(cw) for j in range(ch))]
            if not spots:
                continue
            # keep big pieces off the walker's start corner so the first frame reads at a glance
            sx, sy = self.core.start
            c, r = min(spots, key=lambda s: (abs(s[0] + (cw - 1) / 2.0 - sx) < cw / 2.0 + 1.5 and abs(s[1] + (ch - 1) / 2.0 - sy) < ch / 2.0 + 1.5,
                                             (s[0] * 7 + s[1] * 11 + k * 5 + ti * 3) % 13, s))
            for i in range(cw):
                for j in range(ch):
                    taken.add((c + i, r + j))
            x, y = origin((c, r))
            pic = piece_frames(name)[0]
            self.placed.append((name, x + (cw * CELL - pic.shape[1]) // 2, y + (ch * CELL - pic.shape[0]) // 2))
        self.walls = walls
        self.free_walls = [w for w in walls if w not in taken] or walls
        # the wall row with the most rock: bats and fish patrol along it
        self.lane = max(range(GH), key=lambda r: (sum(1 for c in range(GW) if rows[r][c] == WALL), -r))
        if ti not in _BACKS:
            _BACKS[ti] = BACKDROPS[self.theme["back"]]()
        self.paint({})

    # -- layout of the top band ---------------------------------------------

    def slot_xy(self, i):
        n = len(self.core.keys)
        x0 = self._hud_x0(n)
        return x0 + i * 9, 2

    def ring_xy(self):
        n = len(self.core.keys)
        x0 = self._hud_x0(n)
        return x0 + n * 9 + (3 if n <= 5 else 1), 1

    @staticmethod
    def _hud_x0(n):
        total = n * 9 + (13 if n <= 5 else 11)   # slots, then the ring
        return (64 - total) // 2 + 1

    # -- paint: one frame of the world ---------------------------------------

    def paint(self, v):
        core = self.core
        ti = self.level_index
        dying = v.get("dying", 0)
        reach = component(core.pos, core.passable())
        hide_cells = v.get("hide", ())
        # the cave behind everything goes red when the run is lost
        if dying >= 1:
            dead = _DEAD_BACKS.get(ti)
            if dead is None:
                dead = _DEAD_BACKS[ti] = remap(_BACKS[ti], DEAD_MAP)
            self.put("backdrop", dead, 0, 0, L_BACK, ["backdrop"])
        else:
            self.put("backdrop", _BACKS[ti], 0, 0, L_BACK, ["backdrop"])
        self._paint_ambient(dying)
        for cell in sorted(core.cells):
            self._paint_cell(cell, v, reach, dying, hide_cells, ti)
        self._paint_hud(v)
        self._paint_walker(v, dying)
        self._paint_fx(v)

    def _mask(self, cell):
        c, r = cell
        cs = self.core.cells
        return ((c, r - 1) in cs, (c, r + 1) in cs, (c - 1, r) in cs, (c + 1, r) in cs)

    def _paint_cell(self, cell, v, reach, dying, hide_cells, ti):
        core = self.core
        px, py = origin(cell)
        tag = "%d_%d" % cell
        lit = cell in core.revealed and cell not in hide_cells
        what = core.content[cell]
        n = v.get("pips", {}).get(cell, core.looks[cell])
        mask = self._mask(cell)
        variant = cell[0] * 3 + cell[1] * 5
        floor_name, obj_name, mark_name = "floor_" + tag, "obj_" + tag, "marks_" + tag

        def show(kind, var=variant):
            self.put(floor_name, tile(kind, ti, mask, var), px, py, L_FLOOR, ["floor", kind])

        if lit and what == TRAP:
            show("pitfloor")
            self.put(obj_name, PIT_PIC, px, py, L_OBJ, ["pit"])
            self.hide(mark_name)
            return
        if n <= 0 and not core.free:
            show("scar")
            self.hide(obj_name)
            self.hide(mark_name)
            return
        if cell not in reach or dying >= 3:
            show("cut")
            self.hide(obj_name)
            self.hide(mark_name)
            return
        if lit:
            show("lit" if what not in (KEY, EXIT) else "lit_plain")
        else:
            show("dark")
        if not core.free and cell != core.start:
            hot = v.get("hot", {}).get(cell, 0)
            self.put(mark_name, marks_pic(max(0, min(2, n)), hot), px, py + 1, L_MARK, ["marks"])
        else:
            self.hide(mark_name)
        if lit and what == KEY:
            self.put(obj_name, SEAT_PIC, px, py, L_OBJ, ["seat"])
        elif lit and what == EXIT:
            shown_open = core.ring_open() if v.get("ring") is None else v["ring"]
            self.put(obj_name, GATE_OPEN if shown_open else GATE_SHUT, px, py, L_OBJ, ["gate"])
        else:
            self.hide(obj_name)

    # -- the top band ----------------------------------------------------------

    def _paint_hud(self, v):
        core = self.core
        n = len(core.keys)
        taken = len(core.taken) if v.get("taken") is None else v["taken"]
        x0 = self._hud_x0(n) - 2
        band = band_pic(self.level_index, x0, x0 + n * 9 + (13 if n <= 5 else 11) + 3)
        self.put("band", _dead(band) if v.get("dying") else band, 0, 0, L_BAND, ["hud"])
        for i in range(n):
            x, y = self.slot_xy(i)
            self.put("slot_%d" % i, SLOT_PIC, x - 1, y - 1, L_HUD, ["hud", "slot"])
            self.put("slot_key_%d" % i, KEY_PIC if i < taken else KEY_EMPTY, x, y + 1, L_HUD + 1, ["hud", "key"])
        ex, ey = self.ring_xy()
        opened = core.ring_open() if v.get("taken") is None else (v["taken"] >= n)
        self.put("hud_gate", GATE_OPEN if opened else GATE_SHUT, ex, ey - 1, L_HUD, ["hud", "gate"])
        half = (self.budget + 1) // 2
        self.put("step_bar", bar_pic(self.budget, max(0, self.steps), self.clock), (64 - half) // 2 - 1,
                 HUD_H - 2, L_HUD, ["hud", "steps"])
        g = v.get("glint")
        if g is not None:
            sx, sy = self.slot_xy(g)
            self.put("glint", GLINT, sx + 1, sy - 1, L_TOP, ["fx"])
        else:
            self.hide("glint")

    # -- the walker ---------------------------------------------------------------

    def _paint_walker(self, v, dying):
        scale = v.get("wscale", 2)
        if scale <= 0:
            self.hide("walker")
            return
        wp = v.get("wp") or origin(v.get("wcell") or self.core.pos)
        col = v.get("wcolor")
        blink = (self.clock % 29) in (13, 14) and not v
        stride = (wp[0] + wp[1]) // 3 % 2
        face = v.get("face", self.face)
        pix = walker_pic(scale, col if col is not None else C_YOU, face, blink, bool(v.get("sad")), stride,
                         bool(v.get("happy")))
        ox, oy = (CELL - pix.shape[1]) // 2, (CELL - pix.shape[0]) // 2
        self.put("walker", pix, wp[0] + ox, wp[1] + oy - v.get("bounce", 0), L_WALK, ["player"])
        if v.get("puff"):                                    # a dust cloud as the walker gives up
            k = v["puff"]
            for i, (dx, dy) in enumerate(((-4, 3), (4, 3), (0, -3))):
                self.put("puff_%d" % i, PUFF[k % 2], wp[0] + 2 + dx + (dx // 4) * k, wp[1] + 2 + dy - k, L_TOP,
                         ["fx"])
        else:
            for i in range(3):
                self.hide("puff_%d" % i)

    # -- flashes: flare, edge, bump, the key in flight, win sparkles ---------------------------

    def _paint_fx(self, v):
        if v.get("flare"):
            bx, by = origin(v["flare"])
            self.put("flare", FLARE_A if self.clock % 2 else FLARE_B, bx, by, L_FX, ["fx"])
        else:
            self.hide("flare")
        if v.get("edge"):
            bx, by = origin(v["edge"][0])
            self.put("edge", EDGE_RED if v["edge"][1] == C_RED else EDGE_WHITE, bx, by, L_FX, ["fx"])
        else:
            self.hide("edge")
        if v.get("redcell"):
            cell, big = v["redcell"]
            bx, by = origin(cell)
            self.put("bump", BUMP_BIG if big else BUMP_SMALL, bx, by, L_FX, ["fx"])
        else:
            self.hide("bump")
        if v.get("key"):
            kx, ky = v["key"]
            self.put("flying_key", KEY_PIC, kx, ky, L_TOP, ["fx", "key"])
        else:
            self.hide("flying_key")
        k = v.get("spark")
        for i in range(6):
            name = "spark_%d" % i
            if k is None:
                self.hide(name)
                continue
            cx, cy = origin(v["sparkcell"])
            ang = i * math.pi / 3 + 0.4 * k
            rad = 3 + 2 * k
            self.put(name, SPARK_BIG if (i + k) % 2 == 0 else SPARK_SMALL,
                     cx + 4 + int(round(rad * math.cos(ang))) - (1 if (i + k) % 2 == 0 else 0),
                     cy + 4 + int(round(rad * math.sin(ang))) - (1 if (i + k) % 2 == 0 else 0), L_TOP, ["fx"])
        k = v.get("conf")
        for i in range(16):
            name = "conf_%d" % i
            if k is None:
                self.hide(name)
                continue
            cx = (i * 23 + 5) % 60 + int(round(2 * math.sin(k + i)))
            cy = HUD_H + k * 8 + (i * 13) % 17 - 6
            self.put(name, CONFETTI[i % len(CONFETTI)], cx, cy, L_TOP, ["fx"])
        d = v.get("dying", 0)
        for i in range(5):
            name = "chunk_%d" % i
            if d >= 2:
                self.put(name, CHUNK[i % 2], 6 + i * 12, HUD_H + ((d - 2) * 7 + i * 9) % 50, L_TOP, ["fx"])
            else:
                self.hide(name)
        if v.get("vignette"):
            self.put("vignette", _VIGNETTE, 0, 0, L_TOP + 1, ["fx"])
        else:
            self.hide("vignette")

    # -- ambient life: sway, flicker, drift. All of it is drawn behind the floor and does nothing. --------------

    def _paint_ambient(self, dying):
        th = self.theme
        walls = self.walls
        t = self.clock
        if not walls:
            return
        for k, (name, x, y) in enumerate(self.placed):
            pic = piece_frames(name)[((t // 6) + k) % 2]
            if dying:                                    # a lost run: the set piece sags, tinted red
                pic = _dead(pic)
                y += dying // 2
            self.put("piece_%d" % k, pic, x, y, L_PIECE, ["piece", name])
        fw = self.free_walls
        for i in range(min(th["props"], len(fw))):
            c, r = fw[(i * 3) % len(fw)]
            frames = PROPS[th["prop"]]
            cyc = PROP_CYCLE.get(th["prop"], (0, 1))
            f = frames[cyc[((t // 4) + i) % len(cyc)]]
            if dying:
                x, y = origin((c, r))
                f = frames[0]
                self.put("prop_%d" % i, f, x + ((i % 3) - 1) * (dying // 3), y + dying * (2 + i % 3), L_ROAM,
                         ["prop", th["prop"]])
                continue
            x, y = origin((c, r))
            self.put("prop_%d" % i, f, x, y, L_ROAM, ["prop", th["prop"]])
        for j, (mode, frames, count) in enumerate(th["roam"]):
            for i in range(count):
                self._roamer("roam_%d_%d" % (j, i), mode, frames, i, count, t, j)

    def _roamer(self, name, mode, frames, i, count, t, j):
        walls = self.walls
        cw, ch = walls[(i * 5 + j * 2) % len(walls)]
        bx, by = origin((cw, ch))
        w = frames[0].shape[1]
        phase = i * 17 + j * 5
        if mode == "bob":                                   # hangs on a thread and bobs
            f = frames[(0, 1, 2, 1)[((t // 5) + i) % 4]]
            self.put(name, f, bx + 2, by, L_ROAM, ["drift"])
        elif mode == "row":                                 # patrols along the rockiest row
            sp = 1 + (i % 2)
            span = 64 + 2 * w
            x = (t * sp + phase * 9) % span - w
            right = (i % 2 == 0)
            if not right:
                x = 64 - w - x
            y = OFFY + self.lane * CELL + 1 + int(round(1.5 * math.sin((t + phase) / 5.0)))
            pic = frames[((t // 2) + i) % len(frames)]
            if not right:
                pic = flip(pic)
            self.put(name, pic, x, y + (i * 4) % 5, L_ROAM, ["drift"])
        elif mode in ("rise", "fall"):
            x = bx + 1 + (i * 3) % 6 + int(round(1.3 * math.sin((t + phase) / 6.0)))
            k = (t * (1 if i % 2 else 2) + phase * 7) % 54
            y = (OFFY + 52 - k) if mode == "rise" else (OFFY - 2 + k)
            self.put(name, frames[((t // 3) + i) % len(frames)], x, y, L_ROAM, ["drift"])
        else:                                               # twinkle: fixed spots that glint now and then
            f = frames[((t // 3) + i * 2) % len(frames)]
            self.put(name, f, bx + (i * 5) % 7, by + (i * 3) % 7, L_ROAM, ["drift"])

    # -- presentation: decide once (the core already moved), then show -------

    def _build(self, aid, ev):
        core = self.core
        frames = []
        e = ev[0]
        kind = e[0]
        if kind == "move":
            a, b = e[1], e[2]
            ax, ay = origin(a)
            dx, dy = b[0] - a[0], b[1] - a[1]
            if dx:
                self.face = "R" if dx > 0 else "L"
            for k in (1, 2, 3):
                frames.append({"wp": (ax + dx * 3 * k, ay + dy * 3 * k), "wcell": a})
            if core.won():
                for k in range(6):                       # sparkle ring round the walker plus a shower of confetti
                    frames.append({"wcell": b, "spark": k, "sparkcell": b, "bounce": (0, 2, 3, 3, 1, 0)[k],
                                   "happy": True, "conf": k})
                frames[-1]["win"] = True
        elif kind == "fall":
            cell = e[1]
            frames.append({"wcell": cell, "wscale": 2, "wcolor": C_RED, "sad": True})
            frames.append({"wcell": cell, "wscale": 1})
            frames.append({"wcell": cell, "wscale": 0.5})
            frames.append({"wcell": cell, "wscale": 0})
            frames.append({"edge": (core.start, C_WHITE)})
            frames.append({})
        elif kind == "block":
            cell = e[1]
            inside = cell[0] in range(GW) and cell[1] in range(GH)
            for big in (True, False):
                if inside:
                    frames.append({"redcell": (cell, big)})
                else:
                    frames.append({"edge": (core.pos, C_RED)})
            frames.append({})
        elif kind == "empty":
            frames.append({"edge": (core.pos, C_WHITE)})
            frames.append({"edge": (core.pos, C_WHITE)})
            frames.append({})
        elif kind == "scar":
            frames.append({"flare": e[1]})
            frames.append({"edge": (e[1], C_WHITE)})
            frames.append({})
        elif kind == "look":
            _, x, back, cost, took, pips_before = e
            xx, xy = origin(x)
            bx, by = origin(back)
            dx, dy = back[0] - x[0], back[1] - x[1]
            hide = {x}
            n_after = core.looks[back]
            pips_old = {back: pips_before}
            hud_old = len(core.taken) - (1 if took else 0)
            for k in (1, 2, 3):
                frames.append({"wp": (xx + dx * 3 * k, xy + dy * 3 * k), "wcell": x,
                               "hide": hide, "pips": pips_old, "taken": hud_old,
                               "ring": (hud_old >= len(core.keys))})
            frames[-1]["wp"] = None
            frames[-1].pop("wcell")
            frames.append({"hide": hide, "flare": x, "pips": pips_old, "taken": hud_old,
                           "ring": (hud_old >= len(core.keys))})
            hot = {back: min(cost, pips_before)} if cost else {}
            f5 = {"pips": pips_old, "hot": hot, "taken": hud_old, "edge": (x, C_WHITE),
                  "ring": (hud_old >= len(core.keys))}
            if took:
                f5["key"] = (xx, xy + 2)
            frames.append(f5)
            if took:
                sx, sy = self.slot_xy(hud_old)
                frames.append({"taken": hud_old, "pips": {back: n_after},
                               "key": ((xx * 2 + sx) // 3, (xy + 2) * 2 // 3 + sy // 3),
                               "ring": (hud_old >= len(core.keys))})
                frames.append({"taken": hud_old, "pips": {back: n_after},
                               "key": ((xx + sx * 2) // 3, (xy + 2) // 3 + sy * 2 // 3),
                               "ring": (hud_old >= len(core.keys))})
                frames.append({"glint": hud_old})
                frames.append({})
            else:
                frames.append({"pips": {back: n_after}})
                frames.append({})
        return frames

    def _death(self):
        """The run is over: the cave reddens, the floor crumbles, the walker sags with a frown and shrinks away."""
        fr = []
        for t in range(8):
            fr.append({"dying": t + 1, "vignette": True, "sad": True, "puff": (t - 3) if t >= 4 else 0,
                       "wcolor": C_RED if t < 4 else None,
                       "wscale": 2 if t < 3 else (1 if t < 5 else (0.5 if t < 7 else 0))})
        fr[-1]["lose"] = True
        return fr

    # -- engine entry point -------------------------------------------------

    def step(self) -> None:
        self.clock += 1
        aid = self.action.id.value
        if aid == 0:
            self.vis = {}
            self.anim = None
            self.paint({})
            self.complete_action()
            return
        if self.anim is None:
            ev = self.core.act(aid)
            frames = self._build(aid, ev) if ev else [{}]
            if aid in ACTIONS:                      # only the offered actions spend a step
                self.steps -= 1
                if self.steps <= 0 and not any(f.get("win") for f in frames):
                    frames += self._death()
            self.anim = frames
        frame = self.anim.pop(0)
        self.vis = frame
        done = not self.anim
        self.paint(frame)
        if frame.get("win"):
            self.next_level()
        if frame.get("lose"):
            self.lose()
            done = True
        if done:
            self.anim = None
            self.complete_action()


# The red vignette is a one-pixel frame round the whole screen plus a thicker corner.
_BACKS = {}          # one backdrop per level, drawn the first time it is needed
_DEAD_BACKS = {}     # the same cave tinted red for a lost run
_VIGNETTE = blank(64, 64)
_VIGNETTE[HUD_H, :] = C_RED
_VIGNETTE[63, :] = C_RED
_VIGNETTE[HUD_H:, 0] = C_RED
_VIGNETTE[HUD_H:, 63] = C_RED
