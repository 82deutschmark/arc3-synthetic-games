# Author: Claude Sonnet 5.5
# Date: 07-November-2026
# PURPOSE: WF03 redraws WF02 (a bank of linked water tanks: click a wheel to pour one or two blocks along its pipe,
#   flip the flow lever to reverse a circuit, match every tank to its white target marks, inside a move counter).
#   The RULES ARE UNCHANGED: every level's tanks, pipes, loads, levers, targets, click boxes and move counts are
#   copied from WF02.  Only the art is new: eight different places (meadow, crystal cave, harbour, desert, night
#   city, jungle, snowfield, volcano), each with its own backdrop, ground, drifting and blinking life and a small
#   creature with a face that hops when a delivery lands and droops when the run is lost.  Every part of the
#   machine is a named engine sprite with layers: tanks with glass walls, shaded outlined pipes, wheel buttons,
#   a lever with a face, a rail of delivery gems and a boxed move counter.
# SRP/DRY check: Pass.  Rules are the pure functions and level tables copied from WF02 (the one place a rule
#   lives); layout() is the same geometry; all art is pure pixel functions of small arguments (cached); the class
#   only wires state to sprites.  Nothing is shared with WF02 beyond that copied rule code.
#
# Updated: 07-November-2026, Claude Sonnet 5.5 (round A: calmer, more readable backdrops, floors, water and pipes)
# Updated: 07-November-2026, Claude Sonnet 5.5 (round B: animation; water drains and rises row by row, a drip falls into the
#   tank, the wheel spins, the lever glides, the creature crouches, leaps and flinches, an iris closes between levels,
#   a lost run crumples and clouds over; no rule changed, fifteen frames at most per action)
#
# Updated: 07-November-2026, Claude Sonnet 5.5 (round C: the whole scene now moves on every frame of an action, not once per
#   action; the creature squashes before a leap, stretches in it and flattens when the run is lost; a newly matched tank
#   lamp warms up before it glows; the splash is five drops that rise then fall; the cave floor is calmer)
#
# CHANGELOG
# 07-Nov-2026 Claude Sonnet 5.5 (round C, final look): idle life used to advance one step per action, so a pour showed a
#   frozen scene.  A beat counter now ticks on every drawn frame, so drifters, glints, blinks and the pipes' chasing
#   dashes move all through a pour.  Creature gets squash (crouch) and stretch (leap) by dropping or doubling a body row, and
#   a flat collapse on a lost run.  A lamp that has just matched shows a half-lit frame first.  The splash is five drops
#   over two frames.  Cave floor lines softened.  No rule, level, click box, counter or outcome changed.
# 07-Nov-2026 Claude Sonnet 5.5 (round B, animation): the Boss asked for motion and nothing busy.  A pour now plays as a
#   crouch and wheel spin, the water leaving its tank a row at a time while the pulse runs the pipe, a drip falling into the
#   other tank, the water rising there with a few thrown drops; the flow lever glides through two in-between stops;
#   the creature breathes, leaps on a delivery with a shadow, flinches on a refused press; the level-clear leap ends in
#   an iris that closes and opens on the next place; a lost run adds a startled hop, a flinch, the cloud rolling in and a
#   sag before the loss tint.  No rule, level, click box, counter or outcome changed.
# 07-Nov-2026 Claude Sonnet 5.5: first version of WF03, an art-only redraw of WF02.  The scene is rebuilt as
#   named sprites; no letters, digits or words are drawn anywhere.
# 07-Nov-2026 Claude Sonnet 5.5 (pass 2, critique and redraw): backdrops rebuilt around the gaps between tanks so
#   they can be seen; a different floor per place; an 11x11 creature with eyes that follow the click, blink, cheer
#   and sag; riveted, ribbed tanks on a bench; flanged shaded pipes with a comet pulse and chasing lit dashes; a
#   gauge that warms as it runs low; gem pips that twinkle; bigger win bursts.  No rule changed.
# 07-Nov-2026 Claude Sonnet 5.5 (round A, calm and readable): the Boss said nothing may be too busy.  Backdrops
#   cut back to a few big shapes with breathing room (no strata, ore, fields, fences, neon bars, cracks or
#   speckled floors); sky gradients are plain bands; each floor is one flat colour with a faint rule; the idle life
#   is a handful of drifting pieces per place and one per gap; water is a flat block with one drifting bead; pipes
#   keep only their end flanges; tanks lose the brim rivets.  Motion kept: sails, drifters, blinking glows, the
#   creature, pours and bursts.  No rule changed.
# 07-Nov-2026 Claude Sonnet 5.5 (pass 3, variety and life): the windmill moved clear of the gauge with sails that
#   turn on its own hub; a quiet two-tone soil; each place gets more distinct drawn props and its own inert life
#   (balloon, bees, bats, a far sailboat, a blimp, a lizard, a shooting star, lava bubbles); a small piece of life
#   in every gap between tanks so the dense levels are no longer just machine; a longer level-clear shower (seven
#   frames of rays plus falling confetti); a drawn rain cloud over the creature when the run is lost.  No rule changed.
import functools

import numpy as np
from arcengine import ARCBaseGame, Camera, GameAction, Level, Sprite

# ---------------------------------------------------------------- palette
FIELD = 15     # purple: the flat field behind everything
INK = 5        # black: tanks and every hard border
WATER = 9      # blue: the cargo
SHEEN = 10     # light blue: the surface of the top block, the second circuit's pipes
MARK = 0       # white: the target dashes, the travelling pulse
WHEEL = 11     # yellow: a button you can press
COPPER = 12    # orange: pipe
DONE = 14      # green: matched, delivered
IDLE = 13      # maroon: not yet
REFUSE = 8     # red: refused (the only thing red means here)

UNIT = 3       # rows per unit of water: two of water, one of gap


# ---------------------------------------------------------------- rules (pure; copied unchanged from WF02)
# A level is a dict: caps, start, valves=[(a, b, load, circuit)], orders=[levels, ...].
# State: v (units in each tank) and f (one reverse bit per circuit).

def circuits(spec):
    return 1 + max(valve[3] for valve in spec["valves"])


def lanes(spec, f, j):
    """(source, destination) of valve j under the lever settings f."""
    a, b, load, circuit = spec["valves"][j]
    return (b, a) if f[circuit] else (a, b)


def refusal(spec, v, f, j):
    """None when valve j can pour now, else the tank that stops it (empty source / full target)."""
    load = spec["valves"][j][2]
    src, dst = lanes(spec, f, j)
    if v[src] < load:
        return src
    if v[dst] + load > spec["caps"][dst]:
        return dst
    return None


def pour(spec, v, f, j):
    """New levels after pressing valve j (the caller has checked it is allowed)."""
    load = spec["valves"][j][2]
    src, dst = lanes(spec, f, j)
    w = list(v)
    w[src] -= load
    w[dst] += load
    return tuple(w)


# ---------------------------------------------------------------- levels (same tables as WF02)
LEVELS = [
    # 1: one pipe, two tanks; tip nearly all of a full tank across, one block per press
    dict(caps=(6, 6), start=(6, 0), valves=[(0, 1, 1, 0)], orders=[(1, 5)]),
    # 2: a chain with narrow middle tanks, two deliveries, forward only
    dict(caps=(6, 2, 2, 6), start=(6, 0, 0, 0),
         valves=[(0, 1, 1, 0), (1, 2, 1, 0), (2, 3, 1, 0)],
         orders=[(3, 1, 1, 1), (1, 1, 1, 3)]),
    # 3: water has to go the other way: the flow lever
    dict(caps=(3, 3, 5, 3), start=(1, 3, 2, 2),
         valves=[(0, 1, 1, 0), (1, 2, 1, 0), (2, 3, 1, 0)],
         orders=[(0, 2, 5, 1), (3, 1, 2, 2), (0, 2, 3, 3)]),
    # 4: a ring with two double pipes
    dict(caps=(6, 3, 6, 4), start=(0, 3, 3, 4),
         valves=[(0, 1, 1, 0), (1, 2, 1, 0), (2, 3, 2, 0), (3, 0, 2, 0)],
         orders=[(6, 0, 0, 4), (0, 3, 5, 2), (5, 1, 0, 4)]),
    # 5: the white pipes get their own lever
    dict(caps=(4, 5, 4, 5), start=(4, 2, 3, 3),
         valves=[(0, 1, 1, 0), (1, 2, 1, 1), (2, 3, 1, 0)],
         orders=[(2, 5, 0, 5), (4, 5, 2, 1), (0, 4, 3, 5)]),
    # 6: five tanks in a ring, two circuits, double pipes
    dict(caps=(5, 4, 6, 6, 5), start=(4, 3, 3, 1, 1),
         valves=[(0, 1, 2, 0), (1, 2, 1, 1), (2, 3, 2, 0), (3, 4, 1, 1), (4, 0, 1, 0)],
         orders=[(0, 2, 4, 6, 0), (5, 3, 1, 2, 1), (0, 1, 5, 6, 0)]),
    # 7: five tanks in a row, nearly full
    dict(caps=(6, 4, 3, 6, 6), start=(4, 3, 3, 4, 4),
         valves=[(0, 1, 2, 0), (1, 2, 1, 1), (2, 3, 1, 0), (3, 4, 2, 1)],
         orders=[(0, 4, 2, 6, 6), (6, 4, 3, 5, 0), (0, 3, 3, 6, 6)]),
    # 8: the whole bank, four deliveries
    dict(caps=(6, 5, 4, 3, 6), start=(4, 4, 2, 2, 4),
         valves=[(0, 1, 2, 0), (1, 2, 1, 0), (2, 3, 1, 1), (3, 4, 2, 1)],
         orders=[(2, 1, 4, 3, 6), (6, 4, 2, 2, 2), (0, 3, 4, 3, 6), (6, 5, 3, 2, 0)]),
]

# Moves allowed per level: twice the shortest winning line (WF02's own search), a lever flip and a press one move each.
BUDGETS = (10, 24, 36, 50, 60, 78, 106, 140)


# ---------------------------------------------------------------- layout (identical geometry to WF02)
def tank_geometry(n):
    """Interior width, gap between tanks, pipe thickness for n tanks in a row."""
    if n <= 2:
        return 9, 14, 3
    if n == 3:
        return 8, 9, 3
    if n == 4:
        return 7, 6, 3
    if n == 5:
        return 6, 4, 2
    return 5, 3, 2


def walk_of(points):
    """The pixels of an axis-aligned polyline, in order, end included."""
    walk = []
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        dx = (x2 > x1) - (x2 < x1)
        dy = (y2 > y1) - (y2 < y1)
        x, y = x1, y1
        while (x, y) != (x2, y2):
            walk.append((x, y))
            x += dx
            y += dy
    walk.append(points[-1])
    return walk


def layout(spec):
    n = len(spec["caps"])
    w, gap, pt = tank_geometry(n)
    outer = w + 2
    total = n * outer + (n - 1) * gap
    x0 = (64 - total) // 2
    ring = any(max(a, b) - min(a, b) > 1 for a, b, _, _ in spec["valves"])
    maxcap = max(spec["caps"])
    # centre the whole machine between the rail (row 9) and the lever strip (row 55)
    content = UNIT * maxcap + 16 + (11 if ring else 0)
    top_edge = 9 + (46 - content) // 2
    floor = top_edge + content - 4
    tanks = []
    for i, cap in enumerate(spec["caps"]):
        left = x0 + i * (outer + gap)
        tanks.append(dict(x=left, top=floor - UNIT * cap, w=w, cap=cap, ix=left + 1, cx=left + outer // 2))
    tallest = min(t["top"] for t in tanks)
    tier = {1: tallest - 8, 2: tallest - 19}

    def port(i, side):
        t = tanks[i]
        if side == "L":
            return t["ix"] + (pt - 1) // 2
        return t["ix"] + t["w"] - 1 - pt // 2

    lo, hi = (pt - 1) // 2, pt // 2
    valves = []
    for j, (a, b, load, circuit) in enumerate(spec["valves"]):
        p, q = min(a, b), max(a, b)
        if q == p + 1:
            xp, xq, ty = port(p, "R"), port(q, "L"), tier[1]
        else:
            xp, xq, ty = port(p, "L"), port(q, "R"), tier[2]
        walk = walk_of([(xp, tanks[p]["top"] - 1), (xp, ty), (xq, ty), (xq, tanks[q]["top"] - 1)])
        xs = [x for x, _ in walk]
        ys = [y for _, y in walk]
        bx, by = min(xs) - lo, min(ys) - lo
        pos = np.full((max(ys) + hi - by + 1, max(xs) + hi - bx + 1), -1, dtype=np.int16)
        for s, (x, y) in enumerate(walk):
            pos[y - lo - by:y + hi - by + 1, x - lo - bx:x + hi - bx + 1] = s
        valves.append(dict(a=a, b=b, p=p, q=q, load=load, circuit=circuit, walk=walk,
                           box=(bx, by), pos=pos, wheel=((xp + xq) // 2, ty)))
    levers = [(32, 59)] if circuits(spec) == 1 else [(17, 59), (47, 59)]
    return dict(n=n, w=w, pt=pt, floor=floor, tanks=tanks, valves=valves, levers=levers)




# ================================================================ ART ==========================================
# One letter per colour so pictures can be drawn as text rows.  '.' is not drawn.
KEY = {".": -1, "k": 5, "w": 0, "b": 9, "l": 10, "y": 11, "o": 12, "m": 13, "g": 14, "p": 15, "r": 8, "n": 7, "v": 6}


def pic(rows, swap=None):
    """Text rows to a pixel array.  `swap` renames letters (so one drawing serves several colourways)."""
    width = max(len(r) for r in rows)
    rows = [r.ljust(width, ".") for r in rows]          # a short row is padded with empty pixels
    swap = swap or {}
    return np.array([[KEY[swap.get(ch, ch)] for ch in r] for r in rows], dtype=np.int8)


def blank():
    return np.full((1, 1), -1, dtype=np.int8)


def rect(c, x, y, w, h, col):
    c[max(0, y):max(0, y + h), max(0, x):max(0, x + w)] = col


def stamp(c, x, y, art):
    """Lay a picture onto a canvas, clipped to it; undrawn pixels leave the canvas alone."""
    h, w = art.shape
    for r in range(h):
        for q in range(w):
            if art[r, q] >= 0 and 0 <= y + r < c.shape[0] and 0 <= x + q < c.shape[1]:
                c[y + r, x + q] = art[r, q]


def stamp_c(c, cx, y, art):
    """Stamp a picture centred on column cx."""
    stamp(c, cx - art.shape[1] // 2, y, art)


def disc(c, cx, cy, rad, col):
    for y in range(cy - rad, cy + rad + 1):
        for x in range(cx - rad, cx + rad + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad + rad and 0 <= x < c.shape[1] and 0 <= y < c.shape[0]:
                c[y, x] = col


def mound(c, cx, top, rx, base, col):
    """A rounded hill: a half-ellipse standing on row `base`."""
    h = base - top
    for y in range(top, base):
        t = (y - top + 0.5) / h
        half = int(round(rx * (1 - (1 - t) ** 2) ** 0.5))
        rect(c, cx - half, y, 2 * half + 1, 1, col)


def peak(c, cx, top, half, base, col, cap=None, capdepth=0, shade=None):
    """A pointed mountain; an optional snow cap on its upper rows and a shaded right flank."""
    h = base - top
    for y in range(top, base):
        t = (y - top + 1) / h
        wd = int(round(half * t))
        capped = cap is not None and y - top < capdepth
        rect(c, cx - wd, y, 2 * wd + 1, 1, cap if capped else col)
        if shade is not None and not capped:
            rect(c, cx + wd // 3, y, wd - wd // 3 + 1, 1, shade)          # the flank away from the light
    if cap is not None and capdepth > 1:                                    # a jagged snow line under the cap
        for x in range(cx - half, cx + half + 1, 2):
            if 0 <= x < 64 and 0 <= top + capdepth < 64 and c[top + capdepth, x] == col:
                c[top + capdepth, x] = cap


def hash2(x, y, m):
    """A cheap fixed scatter (the same every call), so textures do not flicker between redraws."""
    return (x * 37 + y * 91 + x * y * 13 + (x ^ y) * 7) % m


def dither(c, y, cur, nxt, level):
    """Blend row y from colour cur toward nxt: level 1 (a quarter), 2 (a checker) or 3 (three quarters)."""
    for x in range(64):
        on = {1: x % 2 == 0 and y % 2 == 0, 2: (x + y) % 2 == 0, 3: not (x % 2 and y % 2)}[level]
        c[y, x] = nxt if on else cur


def sky(c, gy, cols):
    """A banded sky from the top to row gy; one quiet checker row marks each seam (no busy gradient dither)."""
    n = len(cols)
    step = gy / n
    for y in range(gy):
        c[y, :] = cols[min(n - 1, int(y / step))]
    for i in range(n - 1):
        seam = int(round((i + 1) * step))
        if 0 < seam - 1 < gy:
            dither(c, seam - 1, cols[i], cols[i + 1], 2)


class Clip:
    """A canvas wrapper whose single-pixel writes off the edge are ignored (floors tile past the screen)."""

    def __init__(self, a):
        self.a = a
        self.shape = a.shape

    def __setitem__(self, k, v):
        y, x = k
        if isinstance(y, slice) or isinstance(x, slice):
            self.a[k] = v
        elif 0 <= y < 64 and 0 <= x < 64:
            self.a[y, x] = v


def ground(c, y, kind):
    """The shelf the machine stands on, from row y to the bottom.  Each place has its own colour, kept flat and
    calm: a lip, a quiet line every few rows and a few seams, never speckle."""
    c = Clip(c)
    base, lip, line, seam = {
        "grass": (13, 14, 15, None), "crypt": (13, 15, 15, None), "dock": (12, 11, 13, 13), "sand": (11, 12, 12, None),
        "street": (15, 9, 13, 13), "moss": (13, 14, 15, None), "ice": (10, 0, 9, 9), "basalt": (13, 8, 5, None),
    }[kind]
    rect(c, 0, y, 64, 64 - y, base)
    rect(c, 0, y, 64, 2, lip)
    if kind == "street":
        rect(c, 0, y + 1, 64, 1, 10)
    for k, yy in enumerate(range(y + 4, 64, 5)):                 # a faint rule across the floor
        if kind == "sand":
            for x0 in range((k * 11) % 20 - 8, 64, 22):
                rect(c, x0, yy, 7, 1, line)
        else:
            rect(c, 0, yy, 64, 1, line)
        if seam is not None:                                     # a few vertical seams, staggered
            for sx in range((k * 7) % 16, 64, 16):
                rect(c, sx, yy - 4, 1, 4, seam)


def band_floor(c, y, a, b):
    """Two thin lines at the head of the floor in the place's own colours."""
    rect(c, 0, y, 64, 1, a)
    rect(c, 0, y + 1, 64, 1, b)


# ---------------------------------------------------------------- small pictures
CLOUD = pic(["....ww......", "..wwwwww.ww.", ".wwwwwwwwwww", "wwwwwwwwwwww", ".llllllllll."])
CLOUD_LOW = pic(["..www.....", ".wwwwww.w.", "wwwwwwwwww", ".llllllll."])
CLOUD_BIG = pic([
    "......wwww.......", "....wwwwwwww.ww..", "..wwwwwwwwwwwwww.", ".wwwwwwwwwwwwwwww", "wwwwwwwwwwwwwwwww",
    ".lllllllllllllll."])
BARN = pic([
    "...kmmmmk...", "..kmmmmmmk..", ".kkkkkkkkkk.", ".krrrrrrrrk.", ".krwrrrrwrk.", ".krrwrrwrrk.",
    ".krrrwwrrrk.", ".krrwkkwrrk.", ".krwkkkkwrk.", ".kwwkkkkwwk.", ".kkkkkkkkkk."])
TREE = pic([
    "..kkkkk..", ".kgggggk.", "kgggrgggk", "kgggggrgk", "kgrgggggk", "kggggrggk", ".kgggggk.", "..kkmkk..",
    "...kmk...", "...kmk...", "...kmk..."])
BUSH = pic(["..kkk...", ".kgggk..", "kgggrgk.", "kggggggk", "kgrggggk", "kkkkkkkk"])
SUNFLOWER = pic([".kyk.", "kyoyk", ".kyk.", "..g..", ".gg..", "..g.."])
TULIP = pic(["r", "r", "g", "g"])
FENCE = pic(["y.y.y.y.y.y.y.y.", "yyyyyyyyyyyyyyyy", "m.m.m.m.m.m.m.m.", "mmmmmmmmmmmmmmmm", "m.m.m.m.m.m.m.m."])
WINDMILL = pic([
    "...kkkkk...", "..kmmmmmk..", ".kmmmmmmmk.", "kkkkkkkkkkk", ".kwwwwwwwk.", ".kwwkkkwwk.",
    ".kwwkkkwwk.", ".kwwwwwwwk.", "kwwwwwwwwwk", "kwwwwkwwwwk", "kwwwwwwwwwk", "kwwwkkkwwwk",
    "kwwkkkkkwwk", "kwwkkkkkwwk", "kkkkkkkkkkk"])
POND = pic(["..bbbbbbbb..", ".bbllbbbbbb.", "bbblbbwbbbbb", ".bbbbbbbbbb.", "..bbbbbbb..."])
HAYBALE = pic([".kkkkkk.", "kyyyyyyk", "kyoyyoyk", "kyyyyyyk", ".kkkkkk."])
STAL_DOWN = pic(["pmmmmmp", ".mmmmm.", ".mmmmm.", "..mmm..", "..mmm..", "...m...", "...m..."])
STAL_UP = pic(["...m...", "...m...", "..mmm..", "..mmm..", ".mmmmm.", ".mmmmm.", "mmmmmmm"])
CRYSTAL = pic(["..l..", ".lwl.", ".lll.", "lllbl", "lwllb", ".llb."])
CRYSTAL_G = pic(["..g..", ".gwg.", ".ggg.", "gggkg", "gwggk", ".ggk."])
CRYSTAL_Y = pic(["..y..", ".ywy.", ".yyy.", "yyyoy", "ywyyo", ".yyo."])
CRYSTAL_BIG = pic([
    "....l....", "...lwl...", "..lwlll..", "..lwlll..", ".llwllbl.", ".lllllbl.", "lllwllllb", "llllllllb", "bbbbbbbbb"])
SHROOM = pic([".rrr.", "rwrwr", ".www.", "..w..", "..w.."])
TORCH = pic(["..k..", ".kmk.", ".kmk.", "kkmkk", ".kmk."])
BAT_HANG = pic(["k...k", "kk.kk", ".kkk.", ".kwk."])
SAIL = pic([
    "..k......", "..kw.....", "..kwww...", "..kwwww..", "..kwwwwww", "..kwwwwww", "..kwwwwww", "..kwwwww.",
    "..kwwww..", "..kwww...", "..k......", "kkkkkkkkk", ".kmmmmmk.", "..kkkkk.."])
SAIL_R = pic([
    "..k......", "..kr.....", "..krrr...", "..krrrr..", "..krwrrrr", "..krrrrrr", "..krwrrrr", "..krrrrr.",
    "..krrrr..", "..krrr...", "..k......", "kkkkkkkkk", ".kyyyyyk.", "..kkkkk.."])
LIGHTHOUSE = pic([
    "..kkk...", ".krrrk..", ".kyyyk..", ".kkkkk..", "..kwwk..", "..krrk..", "..kwwk..", "..krrk..", ".kwwwwk.",
    ".krrrrk.", ".kwwwwk.", "kkkkkkkk"])
BUOY = pic([".r.", "rwr", "rwr", "bbb"])
CACTUS = pic([
    "..kgk....", "..kgk.kgk", "kgkgk.kgk", "kgkgk.kgk", "kgkgkkkgk", "kgggggggk", ".kkkgggk.", "...kgggk.", "...kgggk.",
    "...kgggk.", "...kgggk."])
CACTUS_B = pic(["..kgk..", "kgkgk.k", "kgkgkgk", "kgggggk", ".kkgggk", "...kgk.", "...kgk."])
MESA = pic([
    "..kkkkkkkk..", ".kmmmmmmmmk.", ".kmmmmmmmmk.", "kmmmmmmmmmmk", "kmrmmmmmmrmk", "kmmmmmmmmmmk"])
SKULL = pic([".www.", "wkwkw", ".www.", ".w.w."])
TUMBLE = [pic([".mm.", "m.mm", "mm.m", ".mm."]), pic(["m.mm", ".mm.", ".mm.", "mm.m"])]
TOWER_TOP = pic(["..k..", "..r..", "..k.."])
PALM = pic([
    "g.gggggg.g", ".ggggkggg.", "..gggkgg..", "...ggkg...", "....mk....", "....mk....", "....mk....", "....mk....",
    "....mk....", "....mk...."])
VINE = pic(["g", "g", "g", "g", "g", "g", "g", "g", "g", "g", "g", "g"])
LEAF = pic([".gggg.", "gggggg", "kggggk", ".kggk.", "..kk.."])
LEAF_BIG = pic([
    "...kkk...", "..kgggk..", ".kgggggk.", "kgggkgggk", "kggkgggkk", ".kgggggk.", "..kgggk..", "...kgk..."])
FLOWER = pic([".c.", "cyc", ".g."], {"c": "n"})
WATERFALL = [pic(["wlwlwl", "lwlwlw", "wlwlwl", "lwlwlw"] * 3), pic(["lwlwlw", "wlwlwl", "lwlwlw", "wlwlwl"] * 3)]
PINE = pic([
    "....w....", "...wgw...", "...ggg...", "..wgggw..", "..ggggg..", ".wgggggw.", ".ggggggg.", "wgggggggw",
    "ggggggggg", "...kmk...", "...kmk..."])
SNOWMAN = pic([
    "..kkk..", ".kwwwk.", ".kkwkk.", "..owo..", ".kwwwk.", "kwwkwwk", "kwwwwwk", "kwwkwwk", ".kwwwk."])
IGLOO = pic([
    "..kkkkk..", ".kwwwwwk.", "kwwwwwwwk", "kwwwwwwwk", "kwwkkkwwk", "kwkkkkkwk", "kkkkkkkkk"])
LAVA_POOL = pic(["..y..y..", ".yoyyoy.", "oooooooo"])
ROCK = pic(["..kk..", ".kmmk.", "kmmmmk", "kmkmmk", "kkkkkk"])
SMOKE = pic(["..mmm.", ".mmmmm", "mmmmmm", ".mmmm."])
SMOKE_BIG = pic([".mmmm..", "mmmmmm.", "mmmmmmm", "mmmmmmm", ".mmmmm."])
STAR_S = pic([".w.", "www", ".w."])
MOON = pic([".yyy.", "yyyyy", "yyy..", "yyyy.", ".yyy."])
MOON_BIG = pic([
    "..yyyy..", ".yyyyyy.", "yyyyoyyy", "yyyyyyyy", "yyoyyyyy", "yyyyyyoy", ".yyyyyy.", "..yyyy.."])
FLAKE = pic(["ww", "ww"])
EMBER = pic(["y", "o"])
DRIP = pic(["l", "b"])
SPLASH = pic(["w.w", ".w."])
WAVE = [pic(["l.l.l", ".l.l."]), pic([".l.l.", "l.l.l"])]
FOAM = [pic(["w.ww.w", ".ww.ww"]), pic([".ww.ww", "w.ww.w"])]
FLAME = [pic([".r.", "ryr", "yoy", "kmk"]), pic(["r..", "ryr", "yoy", "kmk"]), pic([".r.", ".yr", "yoy", "kmk"])]
PLANE_LIGHT = [pic(["r"]), blank()]
WINDMILL_S = pic([                       # a narrow mill, clear of the gauge (the sails are a separate turning sprite)
    "..kkkkk..", ".kmmmmmk.", ".kkkkkkk.", ".kwwwwwk.", ".kwwkwwk.", ".kwwwwwk.", "kwwwwwwwk", "kwwrrrwwk",
    "kwwwwwwwk", "kwwkkkwwk", "kwkkkkkwk", "kwkkkkkwk", "kkkkkkkkk"])
BALLOON = pic(["..kkk..", ".krrrk.", "krwrwrk", "kyyyyyk", "krwrwrk", ".kyyyk.", "..k.k..", ".kmmmk.", "..kkk.."])
BLIMP = pic(["...kkkkkkk...", "..kbbbbbbbk..", ".kbwbbbbbwbk.", ".kbbbbbbbbbk.", "..kkkkkkkkk..", "....kmmmk...."])
BAT_FLAP = [pic(["k...k", "kk.kk", ".krk.", "..k.."]), pic([".....", "k.k.k", ".krk.", ".kkk."])]
BEE = [pic(["yk", "ky"]), pic(["ky", "yk"])]
PUFF = [pic([".w", "ww"]), pic(["w.", ".w"])]
LAVA_BUBBLE = [pic(["o"]), pic([".o.", "oyo"]), pic(["o.o", ".y."]), blank()]
LIZARD = [pic(["..gg.", "ggggk", ".g.g."]), pic(["..gg.", "ggggk", "g..g."])]
BOAT_FAR = pic(["..w..", ".ww..", "wwwww", ".kkk."])
SHOOT = pic(["w...", ".w..", "..l."])
FIREFLY = [pic(["y"]), pic(["o"]), blank(), blank()]
BEAM = [pic(["yy", ".y"]), blank()]
WINDOW = [pic(["yy"]), pic(["kk"]), pic(["yy"]), pic(["oo"])]
SNOWPIX = pic(["w"])
CRYSTAL_GLOW = [pic(["l"]), pic(["w"]), pic(["y"]), blank()]
STEAM = [pic(["w", "l"]), pic(["l", "."])]


def blades(k, rad=6):
    """The four sails of the windmill at one of four angles (a spinning picture, ambient only)."""
    import math
    size = 2 * rad + 3
    mid = rad + 1
    c = np.full((size, size), -1, dtype=np.int8)
    ang = math.radians(k * 22.5)
    for arm in range(4):
        a = ang + arm * math.pi / 2
        for r in range(1, rad + 1):
            x, y = int(round(mid + r * math.cos(a))), int(round(mid + r * math.sin(a)))
            c[y, x] = 5 if r < 2 else 0
            if r >= rad - 2:
                px, py = int(round(x - math.sin(a))), int(round(y + math.cos(a)))
                if 0 <= px < size and 0 <= py < size:
                    c[py, px] = 11
    c[mid, mid] = 8
    return c


def butterfly(col, open_):
    return pic(["c.c", ".k."] if open_ else ["cc.", ".k."], {"c": col})


def gull(col, up):
    return pic(["c...c", ".c.c.", "..c.."] if up else ["cc.cc", "..c..", "....."], {"c": col})


def vulture(up):
    return pic(["k.....k", ".kk.kk.", "...k..."] if up else ["kk...kk", "..kkk..", "...k..."])


def parrot(flip):
    rows = [".rr.", "rkrr", "rrbb", ".bbb", "..y."]
    return pic([r[::-1] for r in rows] if flip else rows)


def sun(diagonal):
    c = np.full((13, 13), -1, dtype=np.int8)
    disc(c, 6, 6, 4, 12)
    disc(c, 6, 6, 3, 11)
    c[4, 4] = 0
    c[4, 5] = 0
    ray = [(6, 0), (6, 12), (0, 6), (12, 6)] if not diagonal else [(1, 1), (11, 1), (1, 11), (11, 11)]
    for x, y in ray:
        c[y, x] = 11
        c[min(max(y + (1 if y == 0 else -1 if y == 12 else 0), 0), 12), min(max(x + (1 if x == 0 else -1 if x == 12 else 0), 0), 12)] = 11
    return c


def twinkle_set(col):
    return [pic(["c"], {"c": col}), blank(), pic([".c.", "ccc", ".c."], {"c": col}), blank()]


def aurora(k):
    """A wide soft ribbon of coloured light that slowly changes hue (snow level, ambient only)."""
    cols = ((14, 10), (10, 14), (14, 9))[k]
    c = np.full((9, 30), -1, dtype=np.int8)
    for x in range(30):
        y0 = 3 + int(round(1.6 * np.sin(x / 4.0 + k)))
        c[y0:y0 + 3, x] = cols[0]
        c[y0 + 3, x] = cols[1]
        c[y0 - 1, x] = cols[1] if x % 2 else -1
    return c


# ---------------------------------------------------------------- the creature on the ground
# Each is a 9x9 body (outlined to 11x11): an ellipse with a lit upper-left and a shaded lower-right rim, extras
# stamped on (ears, horns, claws, beak, belly, feet), two 2x2 eyes with pupils that follow and a mouth that
# changes with the mood.  eye = (row, left col, right col), mouth = (row, col of its 3 pixels).
CREATURES = [
    dict(body=11, shade=12, light=0, belly=None, eye=(3, 1, 6), mouth=(6, 3), cheek=8,
         extras=["...yy....", "....y...."], beak=(5, "ooo"), feet=(12, (2, 3, 5, 6))),            # a duck
    dict(body=9, shade=5, light=10, belly=None, eye=(3, 1, 6), mouth=(6, 3), cheek=8,
         extras=["yb.....by", "bb.....bb"], beak=None, feet=(5, (2, 6))),                         # a cave bat
    dict(body=8, shade=13, light=11, belly=None, eye=(2, 1, 6), mouth=(5, 3), cheek=11,
         extras=["rr.....rr", "r.......r"], beak=None, feet=(8, (0, 2, 4, 6, 8))),                # a crab
    dict(body=14, shade=13, light=10, belly=11, eye=(2, 1, 6), mouth=(5, 3), cheek=11,
         extras=["..o.o.o..", "...o.o..."], beak=None, feet=(14, (1, 2, 6, 7))),                  # a lizard
    dict(body=12, shade=13, light=11, belly=11, eye=(2, 1, 6), mouth=(6, 3), cheek=8,
         extras=["w.......w", "ww.....ww"], beak=(5, "yyy"), feet=(11, (2, 3, 5, 6))),            # an owl
    dict(body=14, shade=13, light=10, belly=10, eye=(1, 1, 6), mouth=(5, 2), cheek=11,
         extras=[], beak=None, feet=(14, (0, 1, 7, 8))),                                           # a frog
    dict(body=9, shade=15, light=10, belly=0, eye=(2, 1, 6), mouth=(5, 3), cheek=8,
         extras=[], beak=(4, "ooo"), feet=(12, (1, 2, 6, 7))),                                     # a penguin
    dict(body=11, shade=12, light=0, belly=None, eye=(3, 1, 6), mouth=(6, 3), cheek=8,
         extras=["r.......r", "rr.....rr"], beak=None, feet=(8, (2, 3, 5, 6))),                   # a fire imp
]


def _ellipse():
    m = np.zeros((9, 9), dtype=bool)
    for y in range(1, 8):
        for x in range(9):
            if ((x - 4) / 4.5) ** 2 + ((y - 4) / 3.6) ** 2 <= 1.0:
                m[y, x] = True
    return m


ELLIPSE = _ellipse()


@functools.lru_cache(maxsize=None)
def creature_pixels(kind, mood, blink, look, tick):
    """mood: idle, cheer or sad.  look: -1 / 0 / 1 where the eyes point.  tick (0..1) makes a cheering body wiggle."""
    cr = CREATURES[kind]
    core = np.full((9, 9), -1, dtype=np.int8)
    core[ELLIPSE] = cr["body"]
    # shade on any body pixel with no body below it or to its right; light on the top-left rim
    below = np.zeros_like(ELLIPSE)
    below[:-1] = ELLIPSE[1:]
    right = np.zeros_like(ELLIPSE)
    right[:, :-1] = ELLIPSE[:, 1:]
    core[ELLIPSE & (~below | ~right)] = cr["shade"]
    left = np.zeros_like(ELLIPSE)
    left[:, 1:] = ELLIPSE[:, :-1]
    above = np.zeros_like(ELLIPSE)
    above[1:] = ELLIPSE[:-1]
    core[ELLIPSE & ~above & ~left] = cr["light"]
    core[2, 2:4] = np.where(core[2, 2:4] == cr["body"], cr["light"], core[2, 2:4])
    if cr["belly"] is not None:
        for y in range(4, 8):
            for x in range(2, 7):
                if ELLIPSE[y, x] and core[y, x] != cr["shade"]:
                    core[y, x] = cr["belly"]
    for r, row in enumerate(cr["extras"]):
        for x, ch in enumerate(row):
            if ch != ".":
                core[r, x] = KEY[ch]
    if cr["beak"]:
        row, txt = cr["beak"]
        for i, ch in enumerate(txt):
            core[row, 3 + i] = KEY[ch]
    frow, fcols = cr["feet"]
    for x in fcols:
        core[8, x] = frow
    # eyes: two 2x2 on a white of their own; the lid is the body colour
    r0, ca, cb = cr["eye"]
    for c0 in (ca, cb):
        if mood == "cheer":                                    # happy arcs
            core[r0, c0:c0 + 2] = INK
            core[r0 + 1, c0:c0 + 2] = cr["body"]
            if mood == "cheer":
                core[r0 + 2, c0] = cr["cheek"] if c0 == ca else core[r0 + 2, c0]
                core[r0 + 2, c0 + 1] = cr["cheek"] if c0 == cb else core[r0 + 2, c0 + 1]
        elif blink:
            core[r0, c0:c0 + 2] = cr["body"]
            core[r0 + 1, c0:c0 + 2] = INK
        elif mood == "sad":                                    # lids drooped, pupils down, a tear
            core[r0, c0:c0 + 2] = INK
            core[r0 + 1, c0:c0 + 2] = MARK
            core[r0 + 1, c0 + (0 if c0 == ca else 1)] = INK
            core[r0 + 2, c0 + (0 if c0 == ca else 1)] = 10
        else:
            core[r0, c0:c0 + 2] = MARK
            core[r0 + 1, c0:c0 + 2] = MARK
            if look == 0:
                core[r0 + 1, c0:c0 + 2] = INK
            else:
                core[r0 + 1, c0 + (1 if look > 0 else 0)] = INK
                core[r0, c0 + (1 if look > 0 else 0)] = INK
    # mouth
    mr, mc = cr["mouth"]
    if mood == "cheer":
        core[mr, mc:mc + 3] = INK
        core[mr + 1, mc + 1] = 8
    elif mood == "sad":
        core[mr + 1, mc] = INK
        core[mr + 1, mc + 2] = INK
        core[mr, mc + 1] = INK
    else:
        core[mr, mc] = INK
        core[mr, mc + 2] = INK
        core[mr + 1, mc + 1] = INK
    if mood == "cheer" and tick:                                # a wiggle: arms-up flourish on the extras row
        core[0, 0] = cr["body"] if core[0, 0] < 0 else core[0, 0]
    # a black outline all round (a creature with no outline reads as a smudge); it grows the picture to 11x11
    big = np.full((11, 11), -1, dtype=np.int8)
    solid = np.zeros(big.shape, dtype=bool)
    solid[1:-1, 1:-1] = core >= 0
    near = np.zeros_like(solid)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            near |= np.roll(np.roll(solid, dy, 0), dx, 1)
    big[near & ~solid] = INK
    big[1:-1, 1:-1][core >= 0] = core[core >= 0]
    return big


def squash(px, n):
    """The same picture n rows shorter, feet kept on the floor: the body compresses (crouch, flat collapse)."""
    h = px.shape[0]
    keep = [r for r in range(h) if r not in {4 + k for k in range(n)}]
    out = np.full_like(px, -1)
    out[h - len(keep):] = px[keep]
    return out


def stretch(px):
    """One body row doubled: the creature is taller in mid-leap (the caller lifts it one row to match)."""
    return np.insert(px, 5, px[5], axis=0)


# ---------------------------------------------------------------- the eight places
# Each scene paints the backdrop onto a 64x64 canvas.  gy is the row of the shelf the tanks stand on and gx the
# centre columns of the gaps between tanks (so a tall feature is drawn where the player can actually see it).
def tower(c, x, y, w, h, wall, lit, dark, seed):
    """A lit building: outlined, with a roof lip and a grid of windows (some on, some off)."""
    rect(c, x, y, w, h, wall)
    rect(c, x, y, w, 1, dark)
    rect(c, x, y, 1, h, dark)
    rect(c, x + w - 1, y, 1, h, dark)
    for wy in range(y + 2, y + h - 1, 3):
        for wx in range(x + 1, x + w - 1, 2):
            if hash2(wx, wy, 3) != seed % 3:
                c[wy, wx] = lit
                if wx + 1 < x + w - 1:
                    c[wy, wx + 1] = lit


def scene_meadow(c, gy, gx):
    sky(c, gy, [9, 10])
    mound(c, 50, gy - 26, 26, gy, 9)                                             # one far blue hill
    mound(c, 6, gy - 22, 22, gy, 9)
    mound(c, 30, gy - 14, 36, gy, 14)                                            # the green hills
    mound(c, 62, gy - 11, 18, gy, 14)
    stamp(c, gx[0] - 6, gy - 11, BARN)
    stamp(c, 4, gy - 13, WINDMILL_S)
    stamp(c, 53, gy - 11, TREE)
    stamp(c, 44, gy - 6, BUSH)
    for x, col in ((9, "r"), (22, "y"), (60, "r")):
        stamp(c, x, gy - 4, pic(["c", "g", "g"], {"c": col}))
    ground(c, gy, "grass")


def scene_cave(c, gy, gx):
    c[:, :] = 15
    rect(c, 0, 0, 64, 3, 13)                                                     # a ceiling of rock
    for x in (6, 24, 42, 57):
        stamp(c, x, 2, STAL_DOWN)
    for i, cx in enumerate(gx):                                                  # one crystal in each gap
        stamp_c(c, cx, gy - 6, (CRYSTAL, CRYSTAL_G, CRYSTAL_Y)[i % 3])
    stamp(c, 5, gy - 14, CRYSTAL_BIG)
    stamp(c, 54, gy - 13, CRYSTAL_BIG)
    stamp(c, 1, gy - 31, TORCH)
    ground(c, gy, "crypt")


def scene_harbour(c, gy, gx):
    sky(c, gy, [9, 10])
    rect(c, 0, gy - 19, 64, 19, 9)                                               # the sea, with a few short crests
    for k, y in enumerate(range(gy - 15, gy - 1, 6)):
        for x in range(2 + (k % 2) * 7, 64, 14):
            rect(c, x, y, 3, 1, 10)
    mound(c, 58, gy - 26, 14, gy - 19, 14)                                       # a rocky headland
    rect(c, 50, gy - 22, 14, 3, 13)
    stamp(c, 55, gy - 38, LIGHTHOUSE)
    for k, cx in enumerate(gx):                                                  # a boat in every other gap
        if k % 2 == 0:
            stamp_c(c, cx, gy - 36, SAIL if k % 4 == 0 else SAIL_R)
    stamp(c, 5, gy - 14, BUOY)
    ground(c, gy, "dock")


def scene_desert(c, gy, gx):
    sky(c, gy, [10, 11, 12])
    disc(c, 14, gy - 18, 6, 8)                                                    # a big low sun with a ring
    disc(c, 14, gy - 18, 5, 12)
    disc(c, 14, gy - 18, 3, 11)
    for mx, mh in ((26, 15), (50, 19)):                                          # two flat mesas
        stamp(c, mx - 6, gy - mh, pic(["..mmmmmmmm.."] + ["mmmmmmmmmmmm"] * (mh - 1)))
    mound(c, 32, gy - 8, 40, gy, 12)                                             # one long dune
    for k, cx in enumerate(gx):
        if k % 2 == 0:
            stamp_c(c, cx, gy - 12, CACTUS if k % 4 == 0 else CACTUS_B)
    stamp(c, 55, gy - 8, CACTUS_B)
    ground(c, gy, "sand")


def scene_city(c, gy, gx):
    sky(c, gy, [5, 15, 13])                                                      # night fading into a hot horizon
    for x, y in ((3, 3), (27, 2), (44, 5)):
        c[y, x] = 0
    disc(c, 58, 6, 4, 11)
    disc(c, 56, 5, 3, 5)
    for k, x in enumerate(range(-2, 64, 14)):                                    # a far skyline, dim and plain
        h = 20 + (k * 7) % 13
        tower(c, x, gy - h, 11, h, 15, 13, 5, k)
    for k, cx in enumerate(gx):                                                  # a plain maroon tower in every gap
        h = 26 + (k * 5) % 9
        rect(c, cx - 4, gy - h, 8, h, 13)
        rect(c, cx - 4, gy - h, 8, 1, 8)
        for wy in range(gy - h + 4, gy - 4, 7):                                  # a column of warm windows
            rect(c, cx - 1, wy, 2, 2, 12)
    ground(c, gy, "street")


def scene_jungle(c, gy, gx):
    sky(c, gy, [10, 10])
    mound(c, 14, gy - 28, 22, gy, 14)
    mound(c, 50, gy - 26, 22, gy, 14)
    rect(c, 0, 0, 64, 4, 14)                                                     # a scalloped canopy across the top
    for x in range(0, 64, 4):
        rect(c, x, 4, 3, 1, 14)
    for k, cx in enumerate(gx):                                                  # one hanging vine per gap
        rect(c, cx, 5, 1, 14 + (k * 5) % 8, 14)
        if k % 2:
            stamp_c(c, cx + 1, gy - 14, LEAF_BIG)
    stamp(c, 0, gy - 17, PALM)
    stamp(c, 54, gy - 15, PALM)
    for x, col in ((9, "r"), (46, "y")):
        stamp(c, x, gy - 4, pic([".c.", "cyc", ".g."], {"c": col}))
    ground(c, gy, "moss")


def scene_snow(c, gy, gx):
    sky(c, gy, [9, 15])                                                           # deep blue night into purple
    for x, y in ((4, 3), (38, 2), (60, 8)):
        c[y, x] = 0
    peak(c, 10, gy - 38, 22, gy, 15, 0, 11, shade=9)                               # two big purple peaks, white caps
    peak(c, 54, gy - 36, 20, gy, 15, 0, 10, shade=9)
    for k, cx in enumerate(gx):
        if k % 2 == 0:
            stamp_c(c, cx, gy - 7, PINE)
    stamp(c, 0, gy - 9, PINE)
    stamp(c, 3, gy - 7, IGLOO)
    stamp(c, 55, gy - 9, PINE)
    ground(c, gy, "ice")


def scene_volcano(c, gy, gx):
    sky(c, gy, [13, 8, 12])                                                       # ash into fire
    for x in (4, 26, 48):
        stamp(c, x, 0, SMOKE)
    peak(c, 32, gy - 36, 34, gy, 13, 12, 3, shade=5)                              # the cone with a glowing rim
    rect(c, 26, gy - 36, 12, 2, 8)
    mound(c, 8, gy - 12, 12, gy, 13)
    mound(c, 56, gy - 14, 12, gy, 13)
    stamp(c, 3, gy - 6, ROCK)
    stamp(c, 55, gy - 6, ROCK)
    stamp(c, 44, gy - 3, LAVA_POOL)
    rect(c, 0, gy - 2, 64, 2, 12)
    ground(c, gy, "basalt")


SCENES = [scene_meadow, scene_cave, scene_harbour, scene_desert, scene_city, scene_jungle, scene_snow, scene_volcano]
FRAMES = [9, 14, 11, 9, 10, 14, 14, 10]          # the colour of each tank's glass walls, by level
GIRDER = [(11, 12, 13), (10, 9, 13), (11, 12, 13), (10, 9, 13), (11, 12, 13), (10, 9, 13), (11, 12, 13), (11, 12, 13)]  # lit, body, shade
PIP_GEM = (14, 14, 14, 14, 14, 14, 14, 14)

# The tint a lost run puts over the backdrop: bright things go hot and dim, cool things go dark.
LOST_TINT = {0: 12, 10: 15, 9: 15, 11: 12, 12: 8, 14: 13, 8: 13, 7: 13, 6: 13, 15: 5, 13: 5, 5: 5}


def amb(frames, x, y, vx=0, span=1, bob=0, rate=4, vy=0, vspan=1, sway=(), rel=False):
    """Idle life: a few frames, a start, a sideways drift (px per sixteen frames) wrapping over `span` px, a bob, a
    vertical drift `vy` (negative rises) wrapping over `vspan` px, a sway pattern, and `rel` = y counts from the floor."""
    return dict(frames=frames, x=x, y=y, vx=vx, span=span, bob=bob, rate=rate, vy=vy, vspan=vspan, sway=sway, rel=rel)


SUN = [sun(False), sun(True)]
BLADES = [blades(k, 4) for k in range(4)]
AURORAS = [aurora(k) for k in range(3)]
SWAY = (0, 0, 1, 1, 0, 0, -1, -1)


# idle life per level: things that blink, sway and drift and do nothing at all
AMBIENT = [
    [amb(SUN, 49, 0, rate=6), amb([CLOUD_BIG], 2, 2, 3, 70), amb([CLOUD_LOW], 38, 9, 2, 66),
     amb([butterfly("o", True), butterfly("o", False)], 9, 30, 4, 20, bob=1, rate=2),
     amb(BLADES, 3, -17, rate=3, rel=True), amb([gull("k", True), gull("k", False)], 22, 6, 5, 60, bob=2, rate=3)],
    [amb(FLAME, 1, 6, rate=2), amb(twinkle_set("l"), 30, 20, rate=4),
     amb(BAT_FLAP, 4, 13, 7, 56, bob=2, rate=2), amb(CRYSTAL_GLOW, 8, 52, rate=3)],
    [amb([gull("w", True), gull("w", False)], 4, 6, 5, 56, bob=2, rate=3), amb([CLOUD_BIG], 14, 14, 2, 60),
     amb([BOAT_FAR], 3, -28, 2, 50, rate=6, rel=True), amb(BEAM, 52, 9, rate=3), amb(FOAM, 20, 28, rate=5)],
    [amb(SUN, 52, 0, rate=7), amb([vulture(True), vulture(False)], 18, 5, 3, 50, bob=1, rate=4),
     amb(TUMBLE, 4, 41, 7, 56, rate=3), amb(LIZARD, 1, 3, 6, 58, rate=3, rel=True)],
    [amb(twinkle_set("w"), 3, 2, rate=3), amb(twinkle_set("y"), 40, 3, rate=5), amb(PLANE_LIGHT, 25, 12, rate=4),
     amb([BLIMP], -14, 5, 3, 84, bob=1, rate=6), amb([SHOOT], 2, 2, 12, 60, vy=6, vspan=40, rate=9)],
    [amb([parrot(False), parrot(True)], 9, 20, 0, 1, bob=1, rate=5),
     amb([butterfly("n", True), butterfly("n", False)], 30, 18, 3, 24, bob=1, rate=2),
     amb(FIREFLY, 50, 22, 2, 10, bob=2, rate=3), amb(FIREFLY, 22, 32, 1, 12, bob=2, rate=4)],
    [amb([FLAKE], 6, 2, 0, 1, bob=3, rate=2), amb([FLAKE], 24, 5, 0, 1, bob=2, rate=3), amb([FLAKE], 44, 3, 0, 1, bob=3, rate=2),
     amb(AURORAS, 18, 1, rate=8), amb(twinkle_set("w"), 33, 10, rate=3)],
    [amb([EMBER], 8, 22, 0, 1, bob=3, rate=2), amb([EMBER], 52, 20, 0, 1, bob=3, rate=3), amb([SMOKE_BIG], 29, 3, 1, 8, bob=1, rate=7),
     amb(LAVA_BUBBLE, 16, -4, rate=3, rel=True), amb(LAVA_BUBBLE, 46, -4, rate=4, rel=True)],
]


def gap_life(k, cx, gy, i):
    """One small inert thing for the gap whose centre column is cx (a place's own flavour of ambient motion);
    the two candidates alternate gap by gap so no gap is crowded."""
    return _gap_pair(k, cx, gy, i)[i % 2:i % 2 + 1]


def _gap_pair(k, cx, gy, i):
    sw = SWAY[i % 4:] + SWAY[:i % 4]
    if k == 0:
        return [amb(BEE, cx - 2, gy - 24, 2, 5, bob=2, rate=2), amb(twinkle_set("y"), cx + 1, gy - 10 + i % 3, rate=4 + i % 3)]
    if k == 1:
        return [amb([DRIP], cx, 9 + 2 * (i % 3), vy=18, vspan=26, rate=1), amb(CRYSTAL_GLOW, cx - 1, gy - 10, rate=3 + i % 2)]
    if k == 2:
        return [amb([pic(["w"])], cx, gy - 6, vy=-8, vspan=14, sway=sw, rate=2), amb(WAVE, cx - 2, gy - 18, rate=3 + i % 2)]
    if k == 3:
        return [amb(twinkle_set("w"), cx, gy - 16 - i % 3, rate=3 + i % 3), amb([pic(["o"])], cx - 1, gy - 6, vy=-6, vspan=10, sway=sw, rate=3)]
    if k == 4:
        return [amb(WINDOW, cx - 1, gy - 22 - (i % 3) * 3, rate=3 + i % 3), amb(WINDOW, cx, gy - 11 - (i % 2) * 4, rate=2 + i % 4)]
    if k == 5:
        return [amb(FIREFLY, cx - 1, gy - 20, 1, 4, bob=2, rate=2 + i % 3), amb(FIREFLY, cx, gy - 8, 1, 3, bob=2, rate=3)]
    if k == 6:
        return [amb([SNOWPIX], cx - 1, 6 + 3 * (i % 3), vy=9, vspan=40, sway=sw, rate=3), amb(twinkle_set("w"), cx, gy - 14, rate=4)]
    return [amb([EMBER], cx, gy - 4, vy=-8, vspan=22, sway=sw, rate=2), amb(LAVA_BUBBLE, cx - 1, gy - 5, rate=2 + i % 3)]


BOB = (0, 1, 1, 2, 2, 1, 1, 0)


GLOOM = pic(["..kkkkkkkkk....", ".kpppppppppk...", "kpppwpppppppk..", "kppppppppppppk.", ".kmmmmmmmmmmmk."])
DROP_RAIN = pic(["b", "l"])
DRIP_FALL = pic(["bl", "bb", "bb"])                     # the drop that falls from a pipe into a tank
SHADOW = np.full((1, 7), INK, dtype=np.int8)           # under the creature while it is in the air
WIPE_EDGE = (0, 10, 24, 30)                            # how far the black frame has closed in, per wipe step


@functools.lru_cache(maxsize=None)
def wipe_pixels(step):
    """The iris between levels: a black frame closing in on a clear window (step 0 draws nothing)."""
    px = np.full((64, 64), -1, dtype=np.int8)
    e = WIPE_EDGE[step]
    if e:
        px[:, :] = INK
        px[e:64 - e, e:64 - e] = -1
        if e < 29:                                             # a thin orange rim on the inside edge
            px[e, e:64 - e] = COPPER
            px[63 - e, e:64 - e] = COPPER
            px[e:64 - e, e] = COPPER
            px[e:64 - e, 63 - e] = COPPER
    return px


# the creature's cues while a lost run plays out: a startled hop, a flinch, then the cloud rolling in and the sag
LOSS_FRAMES = [
    {"oops": True, "lift": 2},
    {"oops": True, "lift": -1},
    {"lost": True, "cloud": 0, "lift": -1},
    {"lost": True, "cloud": 1, "lift": -2},
    {"lost": True},                                  # the step paints the settled loss over this one
]

# ---------------------------------------------------------------- the machine
CIRCUIT_LOOK = (
    dict(pipe=COPPER, line=WHEEL, wheel=WHEEL, press=COPPER, lit=WHEEL, shade=13, hi=0),
    dict(pipe=SHEEN, line=MARK, wheel=MARK, press=SHEEN, lit=WATER, shade=9, hi=0),
)

# Glyphs inside the 7x7 body (row, col): water on the side it leaves, a black gate in the middle column.
GATE = tuple((r, 3) for r in range(7))
DROP_ONE = tuple((r, c) for r in range(1, 6) for c in range(3))
DROP_TWO = tuple((r, c) for r in (0, 1, 2, 4, 5, 6) for c in range(3))
RING = ((2, 2), (2, 3), (2, 4), (3, 2), (3, 4), (4, 2), (4, 3), (4, 4))  # spinning: round, no heading


@functools.lru_cache(maxsize=None)
def wheel_pixels(heads_right, load, circuit, state, lost):
    """9x9 wheel: black rim, body, water waiting on the side it leaves (None = spinning)."""
    look = CIRCUIT_LOOK[circuit]
    px = np.full((9, 9), INK, dtype=np.int8)
    for r, c in ((0, 0), (0, 8), (8, 0), (8, 8)):
        px[r, c] = -1
    body = {"idle": look["wheel"], "pressed": look["press"], "slam": look["press"], "refused": REFUSE,
            "hint": look["wheel"]}[state]
    if lost:
        body = IDLE
    px[1:8, 1:8] = body
    if state in ("idle", "hint") and not lost:
        px[7, 1:8] = look["press"]          # a shaded lower edge: a button that stands proud
        px[1, 2:7] = MARK if circuit == 0 else SHEEN   # and a lit upper edge
    for r, c in ((1, 1), (1, 7), (7, 1), (7, 7)):                   # four rivets on the rim
        px[r, c] = INK
    if state in ("hint", "slam"):
        px[0, 1:8] = MARK
        px[8, 1:8] = MARK
        px[1:8, 0] = MARK
        px[1:8, 8] = MARK
    if heads_right is None:
        for r, c in RING:
            px[1 + r, 1 + c] = INK
        return px
    for r, c in GATE:
        px[1 + r, 1 + c] = INK
    for r, c in (DROP_ONE if load == 1 else DROP_TWO):
        px[1 + r, 1 + (c if heads_right else 6 - c)] = WATER
    # a bright bead in each drop so the water looks wet (only where the drop is drawn)
    for r, c in ((2, 0), (3, 0)) if load == 1 else ((1, 0), (5, 0)):
        px[1 + r, 1 + (c if heads_right else 6 - c)] = SHEEN
    return px


# the knob's face: eyes always, a mouth by mood (smile, round when it spins, wide when happy, frown when lost)
KNOB_MOUTH = {"idle": ((3, 1), (3, 3), (4, 2)), "spin": ((3, 2), (4, 2)), "sad": ((3, 2), (4, 1), (4, 3)),
              "cheer": ((3, 1), (3, 2), (3, 3), (4, 2))}


KNOB_X = (1, 6, 11, 3, 8)        # left, middle, right, and the two stops in between while it slides
SLIDING = (1, 3, 4)


@functools.lru_cache(maxsize=None)
def lever_pixels(circuit, knob, hint, lost, blink, cheer):
    """17x7 switch: black track with a plate, a knob with a face at the left, middle or right (the flow lever)."""
    look = CIRCUIT_LOOK[circuit]
    px = np.full((7, 17), INK, dtype=np.int8)
    for r, c in ((0, 0), (0, 16), (6, 0), (6, 16)):
        px[r, c] = -1
    px[0, 1:16] = MARK if hint else IDLE                  # the plate's rim
    px[6, 1:16] = MARK if hint else IDLE
    for c in range(2, 15, 4):                              # studs along the rim
        px[0, c] = INK
        px[6, c] = INK
    px[3, 2:15] = look["pipe"]
    px[2:5, 2] = look["pipe"]                  # a plain stop at each end of the track
    px[2:5, 14] = look["pipe"]
    px[3, 3:14:2] = look["shade"]              # a notched rail
    x = KNOB_X[knob]
    body = IDLE if lost else look["wheel"]
    px[1:6, x:x + 5] = body
    px[1, x + 1:x + 4] = IDLE if lost else (MARK if circuit == 0 else SHEEN)   # lit top
    px[5, x:x + 5] = look["press"] if not lost else INK     # shaded underside
    mood = "sad" if lost else ("cheer" if cheer else ("spin" if knob in SLIDING else "idle"))
    if blink and not lost:
        px[3, x + 1] = INK
        px[3, x + 3] = INK
    else:
        px[2, x + 1] = INK
        px[2, x + 3] = INK
    for r, c in KNOB_MOUTH[mood]:
        px[1 + r, x + c] = INK
    return px


MAR_LOST = 13


@functools.lru_cache(maxsize=None)
def tank_pixels(w, cap, matched, refused, glass, lost):
    """Glass tank, 2 px wider and 2 px taller than its footprint for a black outline.  Black inside so the
    water and the white marks read.  A refusing tank gets a red rim: along the floor when it has nothing to
    give, along the brim when it has no room.  Rivets on the shell, a lamp at the foot."""
    rows = UNIT * cap + 4
    px = np.full((rows + 2, w + 4), INK, dtype=np.int8)
    for r, c in ((0, 0), (0, w + 3), (rows + 1, 0), (rows + 1, w + 3)):
        px[r, c] = -1
    inner = px[1:rows + 1, 1:w + 3]
    inner[:, :] = INK
    wall = MAR_LOST if lost else glass
    inner[:, 0] = wall
    inner[:, w + 1] = wall
    inner[0, :] = wall                                                   # the brim
    if not lost:
        inner[2:4, 0] = MARK                                             # a glint on the glass
        inner[1, 1] = wall
    lamp = IDLE if (lost or not matched or matched == "warm") else DONE
    inner[rows - 2:rows, 1:w + 1] = lamp
    if matched == "warm" and not lost:
        inner[rows - 2:rows, 1:w + 1] = IDLE
        inner[rows - 2:rows, 2:w] = DONE                                 # lamp half lit: the glow has not yet filled the lens
    elif matched and not lost:
        inner[rows - 2, 1:3] = WHEEL                                     # the shine on a lit lamp
        inner[rows - 2, w - 1:w + 1] = WHEEL
        inner[rows - 1, 2:w] = SHEEN
    elif not lost and not matched:
        inner[rows - 1, 2:w] = INK                                       # an unlit lamp: dark slit
    if refused:
        inner[:, 0] = REFUSE
        inner[:, w + 1] = REFUSE
        if refused == "full":
            inner[0, :] = REFUSE
        else:
            inner[rows - 5:rows - 3, :] = REFUSE
    return px


@functools.lru_cache(maxsize=None)
def water_pixels(w, cap, count, flash, phase, lost, cut=0):
    """The stack of units: two rows of blue, one row of gap; bubbles that drift sideways on each unit, a moving
    glint on the top row.  `phase` is already coarse (changes every few frames).  `cut` hides that many water rows
    from the top of the stack, so a pour can drain or fill a tank one row at a time instead of jumping."""
    rows = UNIT * cap
    px = np.full((rows, w), -1, dtype=np.int8)
    deep, light = (15, 13) if lost else (WATER, SHEEN)
    drawn = [(k, r) for k in range(count - 1, -1, -1) for r in (0, 1)][cut:]      # (unit, 0 = top row / 1 = bottom row)
    for n, (k, r) in enumerate(drawn):
        row = rows - 1 - UNIT * k - 1 + r
        colour = MARK if k >= count - flash else deep
        px[row, :] = colour
        if colour != deep:
            continue
        if n == 0:                                                       # the surface: light, with a glint walking along it
            px[row, :] = light
            px[row, phase % w] = deep
            px[row, (phase + w // 2) % w] = MARK if not lost else light
        elif r == 0:
            px[row, (3 * k + phase) % w] = light                         # one bright bead per unit, drifting
    return px


@functools.lru_cache(maxsize=None)
def marks_pixels(w, colour):
    px = np.full((1, w), -1, dtype=np.int8)
    for c in range(w):
        if c % 3 != 2:
            px[0, c] = colour
    return px


def pipe_pixels(valve, circuit, window, lit, lost, pt):
    """A pipe on a black outline: a lit upper edge, a shaded lower edge, bands (flanges) near each end and every
    few pixels, its centre stripe if it carries two, and the pulse (window of walk indices) as a bright comet with
    a wet tail.  `lit` is None or a phase 0..3: the whole pipe glows and bright dashes run along it.  The array is
    one pixel larger on every side than the pipe's box."""
    look = CIRCUIT_LOOK[circuit]
    pos = valve["pos"]
    mask = pos >= 0
    h, w = pos.shape
    big = np.zeros((h + 2, w + 2), dtype=bool)
    big[1:-1, 1:-1] = mask
    near = np.zeros_like(big)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            near |= np.roll(np.roll(big, dy, 0), dx, 1)
    px = np.full(big.shape, -1, dtype=np.int8)
    px[near & ~big] = INK
    body = IDLE if lost else (look["lit"] if lit is not None else look["pipe"])
    px[big] = body
    above = np.roll(big, 1, 0)
    left = np.roll(big, 1, 1)
    below = np.roll(big, -1, 0)
    right = np.roll(big, -1, 1)
    if not lost and pt == 3:
        px[big & (~above | ~left)] = look["pipe"] if lit is not None else look["hi"]
    if pt == 3 or lost:
        px[big & (~below | ~right)] = INK if lost else (look["pipe"] if lit is not None else look["shade"])
    else:
        px[big & ~below] = look["pipe"] if lit is not None else look["shade"]       # a slim pipe: shade its underside only
    bx, by = valve["box"]
    walk = valve["walk"]
    n = len(walk)
    if valve["load"] == 2:
        for x, y in walk:
            px[y - by + 1, x - bx + 1] = look["pipe"] if (lit is not None or lost) else look["line"]
    ring = INK if lost else (look["shade"] if lit is None else look["pipe"])
    lo_, hi_ = (pt - 1) // 2, pt // 2
    for s in range(n):
        if s in (1, n - 2):                                   # a flange band across the pipe
            x, y = walk[s]
            nx, ny = walk[min(s + 1, n - 1)]
            if nx != x:
                px[y - by + 1 - lo_:y - by + 2 + hi_, x - bx + 1] = ring
            else:
                px[y - by + 1, x - bx + 1 - lo_:x - bx + 2 + hi_] = ring
    inner = px[1:-1, 1:-1]
    if lit is not None and not lost:
        for s in range(n):
            if (s + lit) % 5 == 0:
                inner[pos == s] = MARK
    if window is not None and not lost:
        lo, hi = window
        inner[(pos >= lo - 1) & (pos < hi + 1) & (pos >= 0)] = SHEEN if circuit == 0 else WATER
        inner[(pos >= lo) & (pos < hi)] = MARK
    return px


GAUGE_ROWS = 61   # rows 2..62 at columns 0..2: empty on every level (the machine starts at column 4)


@functools.lru_cache(maxsize=None)
def gauge_pixels(left, bucket):
    """The move counter in its black case: cells stacked three across from the bottom of a 3x61 column; the top
    cell goes first.  A cold scale of maroon ticks shows in the empty part; the lit cells turn orange, then red, as
    the column runs low.  The case is one column wider and a row taller at each end."""
    px = np.full((GAUGE_ROWS + 2, 4), INK, dtype=np.int8)
    for r in range(1, GAUGE_ROWS + 1, 2):
        px[r, 0:3] = 13 if r % 6 == 1 else INK
    light, body, shade = ((WHEEL, WHEEL, COPPER), (COPPER, COPPER, REFUSE), (REFUSE, REFUSE, 13))[bucket]
    for k in range(left):
        row, col = GAUGE_ROWS - k // 3, k % 3
        px[row, col] = body
        if col == 2:
            px[row, col] = shade
    top = GAUGE_ROWS - (left - 1) // 3 if left else None
    if top is not None:
        px[top, 0:3] = light                                    # the bright meniscus on the top cell
    px[1:GAUGE_ROWS + 1:6, 3] = 13                              # studs on the case edge
    return px


@functools.lru_cache(maxsize=None)
def pip_pixels(state, t):
    px = np.full((5, 5), -1, dtype=np.int8)
    px[:, :] = {"done": DONE, "now": WHEEL, "later": IDLE}[state]
    for r, c in ((0, 0), (0, 4), (4, 0), (4, 4)):
        px[r, c] = -1
    if state == "now":
        px[1:4, 1:4] = INK if t == 0 else COPPER
        px[2, 2] = WHEEL if t == 0 else INK
    if state == "done":
        px[1, 1] = MARK                      # a gem's glint
        px[2, 2:4] = SHEEN
        px[3, 3] = MARK if t else SHEEN      # a twinkle that comes and goes
        px[0, 2] = SHEEN
    if state == "later":
        px[2, 2] = INK
        px[1, 1] = MAR_LOST
    return px


@functools.lru_cache(maxsize=None)
def rail_pixels(width):
    px = np.full((9, width), INK, dtype=np.int8)
    for r, c in ((0, 0), (0, width - 1), (8, 0), (8, width - 1)):
        px[r, c] = -1
    px[0, 1:width - 1] = IDLE
    px[8, 1:width - 1] = IDLE
    for c in range(3, width - 3, 6):                       # studs along the rim
        px[0, c] = WHEEL
        px[8, c] = WHEEL
    px[3:6, 0] = COPPER                                    # end caps
    px[3:6, width - 1] = COPPER
    return px


@functools.lru_cache(maxsize=None)
def girder_pixels(width, look, lost=False):
    """The bench the tanks stand on: a lit edge, two rows of body, a shaded row, a black foot, bolts."""
    lit, body, shade = (13, 13, 5) if lost else look
    px = np.full((5, width), body, dtype=np.int8)
    px[0, :] = lit
    px[3, :] = shade
    px[4, :] = INK
    for c in range(2, width - 1, 12):
        px[1, c] = INK
        px[2, c] = shade
    return px


SPARK_COLS = (0, 11, 8, 14, 9, 12, 10)
SPARKS = 26                       # 14 rays from the middle plus 12 pieces of falling confetti


@functools.lru_cache(maxsize=None)
def star_pixels(kind, col):
    if kind == 0:
        return pic([".c.", "ccc", ".c."], {"c": {0: "w", 11: "y", 8: "r", 14: "g", 9: "b", 12: "o", 10: "l"}[col]})
    if kind == 1:
        return pic(["..c..", ".ccc.", "ccwcc", ".ccc.", "..c.."], {"c": {0: "w", 11: "y", 8: "r", 14: "g", 9: "b", 12: "o", 10: "l"}[col]})
    if kind == 2:
        return pic(["c.c", ".c.", "c.c"], {"c": {0: "w", 11: "y", 8: "r", 14: "g", 9: "b", 12: "o", 10: "l"}[col]})
    return pic(["cc", "cc"], {"c": {0: "w", 11: "y", 8: "r", 14: "g", 9: "b", 12: "o", 10: "l"}[col]})


def _burst_dirs():
    import math
    return [(math.cos(i * 2 * math.pi / 14), math.sin(i * 2 * math.pi / 14)) for i in range(14)]


BURST = _burst_dirs()


# ---------------------------------------------------------------- the game
class Wf03(ARCBaseGame):
    def __init__(self, seed=0):
        levels = [Level(sprites=[], grid_size=(64, 64), name=f"bank_{k}", data={}) for k in range(len(LEVELS))]
        super().__init__(
            game_id="wf03", levels=levels,
            camera=Camera(width=64, height=64, background=FIELD, letter_box=FIELD),
            available_actions=[5, 6], seed=seed,
        )

    # ---- level setup
    def on_set_level(self, level):
        level.remove_all_sprites()
        self.spec = LEVELS[self.level_index]
        self.geo = layout(self.spec)
        self.v = tuple(self.spec["start"])
        self.f = [0] * circuits(self.spec)
        self.order = 0
        self.queue = []
        self.finish = False
        self.left = BUDGETS[self.level_index]   # set on level entry, so RESET refills it
        self.tick = getattr(self, "tick", 0)
        self.beat = getattr(self, "beat", 0)      # ticks on every drawn frame, so idle life moves inside an action
        self.was = {}                              # which tanks were matched at the previous frame (for the lamp warm-up)
        self.gaze = 0
        self.sprites = {}
        self.pipe_art = {}
        geo = self.geo
        k = self.level_index
        gy = geo["floor"] + 4

        def add(name, px, x, y, layer, tags):
            s = Sprite(px, name=name, x=x, y=y, layer=layer, tags=tags)
            level.add_sprite(s)
            self.sprites[name] = s
            return s

        # the free columns between neighbouring tanks: where the backdrop can actually be seen
        gx = [(a["x"] + a["w"] + 2 + b["x"]) // 2 for a, b in zip(geo["tanks"], geo["tanks"][1:])]
        canvas = np.full((64, 64), FIELD, dtype=np.int8)
        SCENES[k](canvas, gy, gx)
        self.back_art = canvas
        self.back_lost = np.vectorize(lambda p: LOST_TINT.get(int(p), int(p)), otypes=[np.int8])(canvas)
        add("backdrop", canvas, 0, 0, 0, ["scenery"])
        self.glass = FRAMES[k]
        self.ambient = []
        lives = list(AMBIENT[k])
        for i, cx in enumerate(gx):                  # a little life in every gap between tanks
            lives += gap_life(k, cx, gy, i)
        for n, spec in enumerate(lives):
            spec = dict(spec, y=spec["y"] + (gy if spec["rel"] else 0))
            sp = add(f"drift_{n}", spec["frames"][0], spec["x"], spec["y"], 1, ["scenery", "idle_life"])
            self.ambient.append((sp, spec))
        first, last = geo["tanks"][0], geo["tanks"][-1]
        bench = last["x"] + last["w"] + 2 - first["x"] + 6
        self.bench_w = bench
        add("bench", girder_pixels(bench, GIRDER[k]), first["x"] - 3, gy - 3, 1, ["scenery"])
        for i, t in enumerate(geo["tanks"]):
            add(f"tank_{i}", tank_pixels(t["w"], t["cap"], False, False, self.glass, False), t["x"] - 1, t["top"] - 1,
                2, ["tank"])
            add(f"water_{i}", blank(), t["ix"], t["top"] + 1, 3, ["water"])
            add(f"mark_{i}", blank(), t["ix"], t["top"], 4, ["target"])
        for j, vv in enumerate(geo["valves"]):
            bx, by = vv["box"]
            add(f"pipe_{j}", blank(), bx - 1, by - 1, 5, ["pipe"])
            add(f"wheel_{j}", blank(), vv["wheel"][0] - 4, vv["wheel"][1] - 4, 6, ["wheel"])
        for c, (lx, ly) in enumerate(geo["levers"]):
            add(f"lever_{c}", blank(), lx - 8, ly - 3, 6, ["lever"])
        total = len(self.spec["orders"])
        px0 = 32 - (total * 8 - 3) // 2
        add("rail", rail_pixels(total * 8 - 3 + 6), px0 - 3, 0, 6, ["hud"])
        for q in range(total):
            add(f"pip_{q}", blank(), px0 + 8 * q, 2, 7, ["hud"])
        add("gauge", blank(), 0, 1, 7, ["hud"])
        self.mascot_x = 46 if len(geo["levers"]) == 1 else 26
        add("creature", blank(), self.mascot_x, 51, 5, ["creature"])
        for q in range(SPARKS):
            add(f"spark_{q}", blank(), 0, 0, 9, ["sparkle"])
        add("shadow", blank(), 0, 0, 4, ["creature"])
        add("drip", blank(), 0, 0, 8, ["motion"])
        add("wipe", blank(), 0, 0, 10, ["transition"])
        add("gloom", blank(), 0, 0, 8, ["lost_look"])           # the rain cloud of a lost run
        for q in range(3):
            add(f"rain_{q}", blank(), 0, 0, 8, ["lost_look"])
        self.paint({"wipe": 1} if getattr(self, "entering", False) else {})
        self.entering = False

    # ---- drawing
    def heads_right(self, j, f=None):
        f = self.f if f is None else f
        src, dst = lanes(self.spec, f, j)
        return dst > src

    def pipe_art_for(self, j, window, lit, lost):
        key = (j, window, lit, lost)
        art = self.pipe_art.get(key)
        if art is None:
            vv = self.geo["valves"][j]
            art = pipe_pixels(vv, vv["circuit"], window, lit, lost, self.geo["pt"])
            self.pipe_art[key] = art
        return art

    def paint(self, fx):
        spec, geo, sp = self.spec, self.geo, self.sprites
        lost = fx.get("lost", False)
        v = fx.get("v", self.v)
        order = fx.get("order", self.order)
        goals = spec["orders"]
        target = goals[order] if order < len(goals) else None
        flash = fx.get("flash", {})
        red = fx.get("red", {})
        self.beat += 1
        coarse = (self.beat // 3) % 20
        for i, t in enumerate(geo["tanks"]):
            matched = target is not None and v[i] == target[i]
            warm = matched and self.was.get(i) is False          # just matched: a half-lit lamp for one frame, then full glow
            self.was[i] = bool(matched)
            sp[f"tank_{i}"].pixels = tank_pixels(t["w"], t["cap"], "warm" if warm else matched, red.get(i), self.glass, lost)
            count, cut = fx.get("wet", {}).get(i, (v[i], 0))          # a tank mid-pour shows its own count minus a few rows
            sp[f"water_{i}"].pixels = water_pixels(t["w"], t["cap"], count, flash.get(i, 0), coarse, lost, cut)
            marks = fx.get("marks", "show")
            if target is None or marks == "hide":
                sp[f"mark_{i}"].pixels = blank()
            else:
                y = geo["floor"] - UNIT * target[i] + 1
                colour = MARK if marks == "flash" else (DONE if matched else MARK)
                sp[f"mark_{i}"].pixels = marks_pixels(t["w"], colour)
                sp[f"mark_{i}"].set_position(t["ix"], y)
        flips = fx.get("flips", self.f)
        spin = fx.get("spin", ())
        pulse = fx.get("pulse", {})
        states = fx.get("wheel", {})
        nudge = fx.get("nudge", {})
        for j, vv in enumerate(geo["valves"]):
            lit = (self.beat % 4) if j in fx.get("lit", ()) else None
            sp[f"pipe_{j}"].pixels = self.pipe_art_for(j, pulse.get(j), lit, lost)
            state = states.get(j, "idle")
            heads = None if (vv["circuit"] in spin or j in fx.get("whirl", ())) else self.heads_right(j, flips)
            sp[f"wheel_{j}"].pixels = wheel_pixels(heads, vv["load"], vv["circuit"], state, lost)
            wx, wy = vv["wheel"]
            sp[f"wheel_{j}"].set_position(wx - 4 + nudge.get(j, 0), wy - 4 + (1 if state == "pressed" else 0))
        knobs = fx.get("knob", {})
        hints = fx.get("lever_hint", ())
        blink = self.beat % 11 in (0, 1)
        for c, (lx, ly) in enumerate(geo["levers"]):
            knob = knobs.get(c, 2 if flips[c] else 0)
            sp[f"lever_{c}"].pixels = lever_pixels(c, knob, c in hints, lost, blink, bool(fx.get("cheer")))
        pips = fx.get("pips")
        beat = (self.beat // 2) % 2
        for k in range(len(goals)):
            state = "done" if k < order else ("now" if k == order else "later")
            if pips is not None:
                state = pips[k]
            sp[f"pip_{k}"].pixels = pip_pixels(state, beat)
        budget = BUDGETS[self.level_index]
        bucket = 0 if self.left * 3 > budget else (1 if self.left * 6 > budget else 2)
        sp["gauge"].pixels = gauge_pixels(self.left, bucket)
        sp["backdrop"].pixels = self.back_lost if lost else self.back_art
        sp["bench"].pixels = girder_pixels(self.bench_w, GIRDER[self.level_index], lost)
        self.paint_life(fx, lost)
        self.paint_motion(fx)

    def paint_motion(self, fx):
        """The drip that falls into a tank, the wipe that closes between levels."""
        sp = self.sprites
        drip = fx.get("drip")
        if drip is None:
            sp["drip"].pixels = blank()
        else:
            sp["drip"].pixels = DRIP_FALL
            sp["drip"].set_position(drip[0], drip[1])
        sp["wipe"].pixels = wipe_pixels(fx.get("wipe", 0))

    def paint_life(self, fx, lost):
        """Idle drift, the creature and the sparkles: all of it decoration, none of it reads the rules."""
        t = self.beat
        sp = self.sprites
        for s, spec in self.ambient:
            if lost:
                s.pixels = blank()
                continue
            n = (t // spec["rate"])
            s.pixels = spec["frames"][n % len(spec["frames"])]
            x = spec["x"] + ((t * spec["vx"]) // 16 % spec["span"] if spec["vx"] else 0)
            if spec["sway"]:
                x += spec["sway"][n % len(spec["sway"])]
            y = spec["y"] + (BOB[n % 8] * spec["bob"] // 2 if spec["bob"] else 0)
            if spec["vy"]:
                y = spec["y"] + (t * spec["vy"] // 16) % spec["vspan"]
            s.set_position(x, y)
        mood = "sad" if lost else ("cheer" if fx.get("cheer") else ("sad" if fx.get("oops") else "idle"))
        blink = mood == "idle" and t % 13 in (0, 1)
        body = creature_pixels(self.level_index, mood, blink, self.gaze, t % 2)
        lift = fx.get("lift")
        if lift is None:                                      # no cue from the move: lost sags, otherwise a slow breath
            lift = -2 if lost else (1 if (t // 6) % 2 else 0)
        bend = 0                                              # squash before a leap, stretch in it, flat when lost
        if lost:
            bend = 3 if fx.get("cloud", 2) >= 1 else 2
            lift = 0
            body = squash(body, bend)
        elif lift < 0:
            body = squash(body, 1)
            lift = 0                                          # feet stay planted while the body compresses
        elif lift >= 4:
            body = stretch(body)
            bend = -1
        sp["creature"].pixels = body
        shake = (1 if t % 2 else -1) if fx.get("oops") and not lost else 0       # a refused press makes it flinch sideways
        sp["creature"].set_position(self.mascot_x + shake, 51 - lift + (bend if bend < 0 else 0))
        sp["shadow"].pixels = SHADOW if lift >= 2 else blank()               # a little shadow while it is in the air
        sp["shadow"].set_position(self.mascot_x + 2, 62)
        gloom = sp["gloom"]
        if lost:                                                     # a dark rain cloud with falling drops over the creature
            cloud = fx.get("cloud", 2)                               # the cloud rolls in over three frames
            gloom.pixels = GLOOM
            gloom.set_position(self.mascot_x - 2, 34 + 3 * cloud)
            for q in range(3):
                if cloud < 1:
                    sp[f"rain_{q}"].pixels = blank()
                    continue
                sp[f"rain_{q}"].pixels = DROP_RAIN
                sp[f"rain_{q}"].set_position(self.mascot_x + 1 + 4 * q, 46 + (q * 2) % 5)
        else:
            gloom.pixels = blank()
            for q in range(3):
                sp[f"rain_{q}"].pixels = blank()
        phase = fx.get("spark")
        big = fx.get("burst", "small") == "big"
        ox, oy = (32, 30) if big else (self.mascot_x + 5, 54)
        splash = fx.get("splash")
        for q in range(SPARKS):
            s = sp[f"spark_{q}"]
            if splash is not None and phase is None and q < 5:                  # five drops thrown up, then falling back
                late = fx.get("fall", 0)
                s.pixels = pic(["l"]) if (q % 2 == 1) else star_pixels(3, 0)
                s.set_position(splash[0] + ((-5, -3, 0, 3, 5) if late else (-4, -2, 0, 2, 4))[q],
                               splash[1] - ((1, 3, 4, 3, 1) if not late else (0, 1, 1, 1, 0))[q])
                continue
            if phase is None or lost or (not big and q >= 8):
                s.pixels = blank()
                continue
            col = SPARK_COLS[(q + phase) % 7]
            if big and q >= 14:                                     # confetti shower: falls from the top, drifting sideways
                s.pixels = star_pixels(3 if q % 2 else 2, col)
                s.set_position(min(61, max(1, (q * 23 + 7) % 60 + 2 + (1 if phase % 2 else -1))),
                               min(61, -3 + phase * 11 + (q % 5) * 4))
                continue
            art = star_pixels((1 if q % 2 == 0 else 0) if big and q % 4 != 3 else 3, col)
            reach = (4 + phase * 6 + (q % 3) * 3) if big else (4 + phase * 4 + (q % 2) * 2)
            dx, dy = BURST[q]
            s.pixels = art
            s.set_position(min(61, max(1, int(ox + dx * reach))), min(61, max(1, int(oy + dy * reach * 0.8))))

    # ---- turns
    def step(self):
        if self.action.id == GameAction.RESET:
            self.complete_action()
            return
        self.tick += 1
        if not self.queue:
            self.left -= 1          # every accepted press or click counts, misses included
            self.take(self.action)
            if self.left <= 0 and not self.finish:        # the last move is spent: the creature crumples before the loss shows
                self.queue = self.queue + LOSS_FRAMES
        if self.queue:
            self.paint(self.queue.pop(0))
        if not self.queue:
            if self.finish:         # a delivery on the last move still wins
                self.finish = False
                self.entering = not self.is_last_level()          # the iris opens on the next place
                self.next_level()
            elif self.left <= 0:
                self.paint({"lost": True})
                self.lose()
            self.complete_action()

    def take(self, action):
        if action.id == GameAction.ACTION5:
            self.queue = self.flip(0)
        elif action.id == GameAction.ACTION6:
            data = action.data or {}
            x, y = int(data.get("x", -1)), int(data.get("y", -1))
            self.gaze = (x > self.mascot_x + 5) - (x < self.mascot_x + 5)       # the creature looks where you pressed
            self.queue = self.click(x, y)
        else:
            self.queue = [{}]

    def click(self, x, y):
        geo = self.geo
        for c, (lx, ly) in enumerate(geo["levers"]):
            if abs(x - lx) <= 8 and abs(y - ly) <= 3:
                return self.flip(c)
        for j, vv in enumerate(geo["valves"]):
            wx, wy = vv["wheel"]
            if abs(x - wx) <= 4 and abs(y - wy) <= 4:
                return self.press(j)
        for i, t in enumerate(geo["tanks"]):
            if t["x"] <= x <= t["x"] + t["w"] + 1 and t["top"] <= y <= geo["floor"] + 3:
                wheels = {j: "hint" for j, vv in enumerate(geo["valves"]) if i in (vv["a"], vv["b"])}
                return [{"wheel": wheels}, {}, {"wheel": wheels}, {}]
        wheels = {j: "hint" for j in range(len(geo["valves"]))}
        levers = tuple(range(len(geo["levers"])))
        return [{"wheel": wheels, "lever_hint": levers}, {}, {"wheel": wheels, "lever_hint": levers}, {}]

    def flip(self, c):
        before = list(self.f)
        self.f[c] ^= 1
        slide = (3, 1, 4, 2) if self.f[c] else (4, 1, 3, 0)          # the knob glides across through two in-between stops
        popped = {j: "pressed" for j, vv in enumerate(self.geo["valves"]) if vv["circuit"] == c}
        queue = [{"flips": before, "knob": {c: slide[i]}, "spin": (c,)} for i in range(3)]
        queue.append({"flips": self.f, "knob": {c: slide[3]}, "wheel": popped})
        queue.append({})
        return queue

    def press(self, j):
        spec, geo = self.spec, self.geo
        vv = geo["valves"][j]
        blocked = refusal(spec, self.v, self.f, j)
        if blocked is not None:
            src = lanes(spec, self.f, j)[0]
            ok = {"wheel": {j: "refused"}, "red": {blocked: "empty" if blocked == src else "full"}, "oops": True}
            return [dict(ok, nudge={j: 1}), dict(ok, nudge={j: -1}), dict(ok, nudge={j: 1}), {}]
        src, dst = lanes(spec, self.f, j)
        load = vv["load"]
        before = self.v
        shown = self.order
        self.v = pour(spec, self.v, self.f, j)
        walk = vv["walk"]
        n = len(walk)
        length = 5 * load
        reach = n + length
        last = self.v == spec["orders"][self.order] and self.order + 1 == len(spec["orders"])
        # a pour is: press (the creature crouches), the water leaves its tank while a pulse runs the pipe, a drip falls
        # into the other tank, the water rises there and splashes.  The delivery that clears the level gets a shorter
        # run so its celebration keeps six of the fifteen frames.
        frames_travel = max(4, min(4 if last else 7, -(-reach // 6)))
        speed = -(-reach // frames_travel)
        leaving = tuple(b - (load if i == src else 0) for i, b in enumerate(before))
        rows = 2 * load                                          # water rows that move: two per block
        base = {"order": shown}

        def drain(cut):
            return {"wet": {src: (before[src], cut)}}

        queue = [dict(base, v=leaving, wheel={j: "slam"}, lit={j}, lift=-1, **drain(0))]
        for t in range(1, frames_travel + 1):
            head = speed * t
            lo, hi = max(0, head - length), min(n, head)
            if src != vv["p"]:
                lo, hi = n - hi, n - lo
            fx = dict(base, v=leaving, pulse={j: (lo, hi)}, lit={j}, **drain(min(rows, -(-rows * t * 2 // frames_travel))))
            if t <= 2:
                fx["wheel"] = {j: "pressed"}                     # the wheel turns for two frames
                fx["whirl"] = (j,)
            queue.append(fx)
        tank = geo["tanks"][dst]
        end = walk[-1] if src == vv["p"] else walk[0]
        surface = lambda c: tank["top"] + UNIT * (tank["cap"] - c) + 2
        near = max(tank["top"] + 1, surface(before[dst]) - 3)
        fill = lambda cut: {"wet": {dst: (self.v[dst], cut)}}
        queue.append(dict(base, v=leaving, drip=(end[0], tank["top"] + 1 + (near - tank["top"] - 1) // 2), **fill(rows)))
        queue.append(dict(base, v=leaving, drip=(end[0], near), **fill(rows - rows // 2)))
        queue.append(dict(base, flash={dst: load}, splash=(end[0], surface(self.v[dst])), **fill(0)))
        goals = spec["orders"]
        if self.v != goals[self.order]:
            queue.append(dict(base, splash=(end[0], surface(self.v[dst])), fall=1))
            return queue
        self.order += 1
        done = ["done"] * self.order + ["later"] * (len(goals) - self.order)
        if self.order == len(goals):
            self.finish = True
            everything = {i: 99 for i in range(len(self.v))}
            hops = (3, 5, 6, 4, 2, 0)                            # the creature's leap, up and back down
            for k in range(6):
                queue.append(dict(base, marks="flash" if k % 2 == 0 else "show", flash=everything if k < 4 else {}, pips=done,
                                  cheer=True, spark=k, burst="big", lift=hops[k], wipe=(0, 0, 0, 0, 1, 2)[k]))
        else:
            queue.append(dict(base, marks="flash", pips=done, cheer=True, spark=0, lift=3))
            queue.append({"marks": "hide", "cheer": True, "spark": 1, "lift": 4})
            queue.append({"marks": "flash", "cheer": True, "lift": 2})
            queue.append({})
        return queue
