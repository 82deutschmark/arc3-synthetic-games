# Author: Claude Opus 5 (first cut and rules); Claude Sonnet 5.5 Low (head collision, enemies, sprite pass, re-cut levels)
# Date: 2026-10-30 (rules first cut 2026-09-07; marker rebuild 2026-09-12)
# PURPOSE: ng02 -- an ARC-AGI-3 environment. The world is a 128-cell strip, eight
#   viewports wide; the 64x64 frame is the engine camera locked to the walker, so the world
#   slides under a stationary token and every step visibly redraws the screen. The terrain is
#   drawn in exactly two colours: FIGURE (solid) and GROUND (passable). LEFT/RIGHT step one cell
#   and climb a one-cell rise automatically. ACTION1 and ACTION2 aim GRAVITY (up / down) and the
#   walker rolls over onto the other end of the open run it stands in. ACTION5 inverts the world:
#   the solid family and the hole family trade places. Two involutions on the same terrain --
#   invert the WORLD, or invert the PULL -- give four readings of one board. Loss is being
#   STRANDED (a reverse BFS over (x, y, polarity, gravity) says the goal is unreachable) or
#   touching one of the two creatures that live in the rock.
#
# CHANGELOG
#   2026-10-30 (Claude Sonnet 5.5 Low): Boss feedback on NG01 -- "the character goes through the
#   blue wall when they spin upside down; it is too big to fit the opening; too much solid unused
#   space; one of the least creative games; could use enemies".
#     * ROOT CAUSE of the pass-through. The walker is DRAWN two cells tall (body cell plus a head
#       cell on the side away from the pull) but its PHYSICS was one cell: sideways steps, falls
#       and pull flips only tested the body cell. The head cell was "simply not drawn" when it
#       overlapped rock, so a curtain that ended one cell above the floor let the token walk
#       straight under it with its head swallowed by the wall -- on the ceiling walk, the same
#       thing with the hanging teeth. It was not a draw-order bug: the collision and the picture
#       disagreed about how big the walker is. Fixed in the rules (new `fits`), not the drawing:
#       the walker now occupies two cells everywhere -- steps, climbs, falls, inversion -- and
#       a pull flip rolls it over onto its old head cell, so the picture and the physics are the
#       same two cells in every frame. Every curtain, plug and tooth was re-cut to match.
#     * Two creatures, both pure functions of (polarity, pull) so the strand search stays exact:
#       the DRIFTER rides against the pull (it clings to the end of its open run that the pull
#       is lifting you away from), the CRAWLER sinks with it. Touching one -- walking into it,
#       falling through it, or being flipped onto it -- is fatal; a red burst marks the cell.
#     * All terrain re-cut: no sealed decorative pockets (they read as passages), shorter
#       levels, a floor that rises and falls, lower galleries, ragged pillars and hanging teeth;
#       a seventh level (the vet gate's glow-up profile needs seven) and a shorter first level.
#     * Crawlers rest on a shelf above the floor lane (a crawler in an open column would block both
#       lanes and make levels 5 and 7 unwinnable); level 7 gained a drifter under a hanging block;
#       level 2 gained a second pair of cuts so random play cannot clear it. Regression test:
#       ng01_test.py (kills the old feet-only collision).
#     * Art: the world, the walker, the creatures, the goal ring and the status marks are named
#       engine sprites; the walker has a face and the creatures have eyes.
#   2026-09-12 (a): marker vocabulary rebuilt after a human playtest (red one-frame burst, the
#   inversion clamp drawn on the world, irregular seeded scenery).
#   2026-09-12 (b): the climb stopped being a key; ACTION1/2 aim the pull instead.
# SRP/DRY check: Pass -- self-contained environment. Rules are pure functions of (grid, state);
#   the strand search, the smoke-test solver and the game all call the same `step_state`.
"""ng02 -- flip the world, or flip which way it pulls.

ACTION3 / ACTION4 step one cell left / right.  A step onto terrain one cell higher (higher
meaning *against the current pull*) is taken automatically, provided the whole two-cell walker
fits there; a two-cell wall or a low ceiling refuses.  ACTION1 pulls gravity UP: the walker
rolls onto its head cell, rises to the first solid cell above and stands under it.  ACTION2
pulls it DOWN again.  Falling is discrete and immediate, inside the press.  ACTION5 inverts the
world.  It is refused when any part of the walker would end up inside rock, and a walker standing
where that is true wears a blue clamp -- the lock is a property of a place on the board.

The pull is drawn on the terrain, not in a HUD: every face you could stand on right now wears a
green hairline, so pressing ACTION1 sweeps every line in the frame from the tops of the blocks to
their undersides.  The walker's feet are green, and its head sits on the side away from the pull.

Any refused press fills the cell that blocked it with red for exactly one frame and shoves the
token into it.  Two creatures live in the rock: one floats against the pull, one sinks with it.
Touching either ends the run; the cell it was caught in flashes red and the walker goes dark.

7 levels, 15-30 actions each. No RNG, no timer, no score and no counter of any kind.
"""

from collections import deque

import numpy as np
from arcengine import ARCBaseGame, Camera, Level, Sprite

# ---------------------------------------------------------------------------
# Colours (ARC-3 palette indices)
# ---------------------------------------------------------------------------

C_WHITE, C_LGRAY, C_GRAY, C_DGRAY, C_VDGRAY, C_BLACK = 0, 1, 2, 3, 4, 5
C_MAGENTA, C_LMAGENTA, C_RED, C_BLUE, C_LBLUE = 6, 7, 8, 9, 10
C_YELLOW, C_ORANGE, C_MAROON, C_GREEN, C_PURPLE = 11, 12, 13, 14, 15

# Maroon is 0.0% of official pixels and greyscale is 60.3% of them, so the two world colours are
# maroon and light magenta: a model has effectively never seen a board like this one.
C_FIGURE = C_MAROON        # solid
C_GROUND = C_LMAGENTA      # passable
C_MUTABLE = C_PURPLE       # outline on every cell inversion will change
C_WALKER = C_ORANGE        # the walker, and nothing else in the game
C_GOAL = C_YELLOW          # goal ring, still reachable
C_DEAD = C_VDGRAY          # goal and walker once the run is over -- the only dark pixels
C_PULL = C_GREEN           # STATUS: a surface the pull holds you to; also the walker's feet
C_CLAMP = C_BLUE           # STATUS: a socket where inversion is off
C_REFUSE = C_RED           # EVENT, one frame: that press did nothing, or here is what killed you
C_DRIFTER = C_LBLUE        # the creature that floats against the pull
C_CRAWLER = C_MAGENTA      # the creature that sinks with the pull

# ---------------------------------------------------------------------------
# World geometry.  Cells are 4x4 px, so the 64x64 frame shows 16x16 cells out of a strip that is
# 128 cells wide -- eight frames.  Each level's map is embedded at X0 so the camera is unclamped
# for the whole play region and the terrain is always what moves.
# ---------------------------------------------------------------------------

CELL = 4
WORLD_W, WORLD_H = 128, 16
VIEW = 64 // CELL          # 16 cells across the frame
CEIL = 2                   # rows 0-1 are bedrock roof on every level
X0 = 24                    # world column of every map's column 0

VOID, MAT_A, MAT_B, FIXED = 0, 1, 2, 3
_CHARS = {".": VOID, "#": MAT_A, "o": MAT_B, "=": FIXED,
          "S": VOID, "G": VOID, "D": VOID, "C": VOID}

# Polarity 0: MAT_A is solid, MAT_B is a hole.  Polarity 1: the two swap.  FIXED is solid in both
# and is the one thing the player can rely on; VOID is open air in both.

# ---------------------------------------------------------------------------
# Painter.  A level is a short list of features cut into a 16-row map.  Maps are drawn by hand
# from these few verbs -- no random scatter -- so every solid mass on screen was put there for a
# reason: it is a wall, a lid, a platform, a tooth, a floor or a frame for a creature.
# Rows: 0-1 roof, 2-3 the ceiling lane (feet on row 2), 4-10 open air, 11-12 the floor lane (feet
# on row 12), 13-15 floor.  The floor used to start at row 11 and be five rows deep: a third of
# the frame was solid rock that nothing used.
# ---------------------------------------------------------------------------

FT = 13                    # first floor row; the floor lane is rows FT-2 and FT-1
FEET = FT - 1              # the walker's feet row when it stands on the floor
HEAD = FT - 2              # ...and its head row
CURTAIN_END = HEAD - 1     # last row of a curtain: leaves the two-cell floor lane clear


def _new(lw):
    """An empty map: two rows of roof, rock from row FT down, two columns of rock each end."""
    g = [["."] * lw for _ in range(WORLD_H)]
    for y in range(CEIL):
        g[y] = ["="] * lw
    _rect(g, 0, lw - 1, FT, WORLD_H - 1, "=")
    _rect(g, 0, 1, 0, WORLD_H - 1, "=")
    _rect(g, lw - 2, lw - 1, 0, WORLD_H - 1, "=")
    return g


def _rect(g, x0, x1, y0, y1, ch):
    """Overwrite an inclusive rectangle."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            g[y][x] = ch


def _stack(g, x0, bottoms, ch="="):
    """Columns hanging from the roof, one bottom row per column: stalactites and curtains."""
    for i, b in enumerate(bottoms):
        _rect(g, x0 + i, x0 + i, CEIL, b, ch)


def _stumps(g, x0, tops, ch="="):
    """Columns standing on the floor, one top row per column: teeth, pillars and walls."""
    for i, t in enumerate(tops):
        _rect(g, x0 + i, x0 + i, t, FEET, ch)


def _isle(g, x0, x1, y0, y1, ch):
    """A floating platform, with a one-cell lip knocked off its top corner so it is never a
    plain rectangle."""
    _rect(g, x0, x1, y0, y1, ch)
    g[y0][x0] = "."


def _dip(g, x0, x1, depth):
    """A pit in the floor `depth` rows deep."""
    _rect(g, x0, x1, FT, FT + depth - 1, ".")


def _slot(g, x0, x1, ch, lid=2):
    """One span of the plank bridge, as the original game built it, but with a LID of only
    `lid` rows (a plug in the ceiling walk) over the skin instead of rock all the way to the roof.

    `x0` and `x1` are FIXED STONES: rock from the roof down to the skin's level and from the floor
    down, so a stone is a two-row tunnel at the floor lane that nothing can ever change.  Between
    them is one mutable segment: two or three rows of skin over the tunnel and one or two under
    it.  Adjacent spans share a stone.  Walking a solid segment is safe in either pull; INVERTING
    inside one opens its skin top and bottom in the same press, the walker drops into a sealed
    shaft whose ends are both mutable, inversion is refused at both, and the stones block the
    shaft in both pulls -- which is why the only legal place to invert is a stone.  The skin
    wears the purple "this will move" border and the stones are the only cells without one.
    """
    for x in range(x0, x1 + 1):
        _rect(g, x, x, HEAD, FEET, ".")
        if x in (x0, x1):
            _rect(g, x, x, CEIL, HEAD - 1, "=")
            _rect(g, x, x, FT, WORLD_H - 1, "=")
        else:
            top = HEAD - 2 - (x * 7 + x0 * 3) % 2           # skin top: 2 or 3 rows deep
            bot = FT + (x * 5 + x1) % 2                       # skin bottom: 1 or 2 rows deep
            _rect(g, x, x, CEIL, CEIL + lid - 1, "=")        # the plug in the ceiling walk
            _rect(g, x, x, CEIL + lid, top - 1, ".")          # open air between plug and skin
            _rect(g, x, x, top, HEAD - 1, ch)
            _rect(g, x, x, FT, bot, ch)
            _rect(g, x, x, bot + 1, WORLD_H - 1, "=")


def _mark(g, start, goal, creatures=()):
    """Stamp S, G and any creature letters, and return the map as strings."""
    g[start[1]][start[0]] = "S"
    g[goal[1]][goal[0]] = "G"
    for ch, (x, y) in creatures:
        g[y][x] = ch
    return ["".join(r) for r in g]


def _embed(rows):
    """Put a map into the 128-cell world: solid rock everywhere the map does not say."""
    lw = len(rows[0])
    return ["=" * X0 + r + "=" * (WORLD_W - X0 - lw) for r in rows]


# Every level below is drawn left to right.  Vocabulary:
#   WALL    -- two or more cells of rock standing on the floor.  Too tall for the one-cell climb;
#              the ceiling walk passes over it.
#   CURTAIN -- rock hanging from the roof down to CURTAIN_END, leaving the two-cell floor lane
#              clear.  It stops the ceiling walk dead and the floor walk passes under it.  (It
#              used to end one row lower, a one-cell passage that a two-cell walker was drawn
#              squeezing through: that was the bug the Boss reported.)
#   Made of MAT instead of FIXED, either one is a gate that inversion opens.

def _l1():
    """pull -- the pull, and nothing else.  Walk east and the floor ends at a ragged pillar the
    one-cell climb cannot take; roll onto the roof, cross the pillar, and where the roof ends at
    a hanging curtain roll back down and walk out under it.  Everything load-bearing is FIXED,
    so inversion cannot strand anybody: the level is strand-proof by construction and checked."""
    g = _new(40)
    _stumps(g, 9, [9, 8])                              # the pillar, two columns, ragged
    _stack(g, 12, [7, CURTAIN_END, CURTAIN_END])       # the curtain, three columns, ragged
    _stumps(g, 16, [FEET, FEET - 1, FEET])             # a bump in the floor (climbable)
    _rect(g, 6, 6, FEET, FEET, "o")                    # the stud: invert is refused standing in it
    _isle(g, 19, 22, 5, 6, "#")                        # two platforms that invert repaints
    _isle(g, 26, 29, 6, 8, "o")
    _stack(g, 24, [4, 5])                              # a stalactite pair, far from the route
    _dip(g, 31, 32, 2)                                 # a small pit past the goal
    return _mark(g, (5, FEET), (20, FEET))


def _l2():
    """seam -- the pull is no longer free.  A floating storey with a lane inside it, two cuts
    through its roof and one through its floor: the pull only carries the walker to the next
    storey, and only where a cut is made.  Bottom lane, inside, out over the top, back in."""
    g = _new(44)
    _rect(g, 6, 36, 7, 10, "=")                        # the floating storey
    _rect(g, 7, 35, 8, 9, ".")                         # its lane
    _rect(g, 10, 10, 10, 10, ".")                      # cut: floor lane -> inside
    _rect(g, 15, 15, 7, 7, ".")                        # cut: inside -> roof lane
    _rect(g, 21, 21, 7, 7, ".")                        # cut: roof lane -> back inside
    _rect(g, 17, 18, 8, 9, "=")                        # the inside wall between the two cuts
    _stumps(g, 13, [HEAD, HEAD])                       # the floor lane is shut after col 12
    _rect(g, 5, 5, FEET, FEET, "o")                    # the stud
    _stack(g, 38, [4, 5])                              # teeth in the roof, past the storey
    _rect(g, 26, 26, 7, 7, ".")                        # cut: inside -> roof lane, second time
    _rect(g, 32, 32, 7, 7, ".")                        # cut: roof lane -> back inside
    _rect(g, 28, 29, 8, 9, "=")                        # the second inside wall
    _isle(g, 24, 27, 4, 5, "#")                        # a floating block hung in the roof run
    return _mark(g, (4, FEET), (34, 9))


def _l3():
    """slot -- inversion joins in, and this is the first level that can be lost.  One tooth to be
    crossed by roof, then a slot: a tunnel with mutable skin above and below it and one rock stone
    in the middle.  West of the stone the skin is solid as the world stands; east of it, the other
    family, so the far half is open air until the world is inverted -- and the stone is the only
    place that may be inverted on."""
    g = _new(46)
    _stumps(g, 6, [HEAD, HEAD - 1])                    # the tooth, ragged
    _slot(g, 10, 15, "#")
    _slot(g, 15, 20, "o")
    _isle(g, 24, 27, 6, 7, "#")
    _stack(g, 23, [4, 6, 5])
    _dip(g, 30, 32, 2)
    _stumps(g, 34, [FEET, HEAD])
    return _mark(g, (3, FEET), (26, FEET))


def _l4():
    """trade -- the world has to go back the way it was.  Three spans and two stones: the first is
    solid as the world stands, the second only once inverted, the third only once inverted BACK.
    A drifter keeps the shaft past the slots, so the roll to the roof goes one column further."""
    g = _new(54)
    _stumps(g, 5, [HEAD])
    _slot(g, 8, 12, "#")
    _slot(g, 12, 16, "o")
    _slot(g, 16, 20, "#")
    _stack(g, 28, [CURTAIN_END, CURTAIN_END])
    _stumps(g, 24, [HEAD, HEAD - 1])
    return _mark(g, (3, FEET), (36, FEET), (("D", (23, FEET)),))


def _l5():
    """loft -- the goal is on the roof, so the last press of the level is the pull.  A slot with a
    stone in it, then a tooth and a curtain past its east end."""
    g = _new(50)
    _rect(g, 5, 5, FEET, FEET, "o")
    _slot(g, 8, 12, "#")
    _slot(g, 12, 16, "o")
    _stumps(g, 19, [HEAD, HEAD])
    _stack(g, 22, [CURTAIN_END, CURTAIN_END])
    _isle(g, 25, 27, 7, 8, "=")                        # a shelf: the crawler rests on it
    return _mark(g, (3, FEET), (30, CEIL), (("C", (26, 5)),))


def _l6():
    """weave -- everything at once, and nothing new."""
    g = _new(56)
    _stumps(g, 7, [HEAD, HEAD])
    _slot(g, 10, 13, "#")
    _slot(g, 13, 17, "o")
    _slot(g, 17, 20, "#")
    _stack(g, 24, [CURTAIN_END, CURTAIN_END])
    _stumps(g, 28, [FEET, HEAD, HEAD])
    return _mark(g, (3, FEET), (40, CEIL))


def _l7():
    """gallery -- every creature at once."""
    g = _new(58)
    _stumps(g, 9, [HEAD, HEAD])
    _stack(g, 15, [CURTAIN_END, CURTAIN_END])
    _isle(g, 29, 31, 7, 8, "=")                        # a shelf: the crawler rests on it
    _stack(g, 40, [5, 6])
    _rect(g, 41, 43, 9, 10, "=")                       # a hanging block: the drifter lodges under it
    return _mark(g, (3, FEET), (52, FEET), (("C", (30, 5)), ("D", (42, 8))))


# (name, rows) for every level.  Built at import; the maps are pure data after this.
LEVELS = [
    {"name": "pull", "rows": _embed(_l1())},
    {"name": "seam", "rows": _embed(_l2())},
    {"name": "slot", "rows": _embed(_l3())},
    {"name": "trade", "rows": _embed(_l4())},
    {"name": "loft", "rows": _embed(_l5())},
    {"name": "weave", "rows": _embed(_l6())},
    {"name": "gallery", "rows": _embed(_l7())},
]

# ---------------------------------------------------------------------------
# Parsed level tables
# ---------------------------------------------------------------------------

def _parse(rows):
    """rows -> (grid of material codes, start cell, goal cell, creatures)."""
    grid = [[_CHARS[ch] for ch in row] for row in rows]
    start = goal = None
    creatures = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "S":
                start = (x, y)
            elif ch == "G":
                goal = (x, y)
            elif ch in "DC":
                creatures.append((ch, x, y))
    return grid, start, goal, tuple(creatures)


_TABLES = [_parse(ldef["rows"]) for ldef in LEVELS]

# ---------------------------------------------------------------------------
# World rules.  Pure functions of (grid, state) so the game, the smoke-test solver and the strand
# check all run on exactly one implementation.  State is (x, y, polarity, gravity); (x, y) is the
# FEET cell, and the head is the cell on the side away from the pull.
# ---------------------------------------------------------------------------

def solid(grid, x, y, pol):
    """Is cell (x, y) solid at this polarity?  Outside the strip is solid bedrock."""
    if y >= WORLD_H or y < 0 or x < 0 or x >= WORLD_W:
        return True
    c = grid[y][x]
    return c == FIXED or (c == MAT_A and pol == 0) or (c == MAT_B and pol == 1)


GRAV_DOWN, GRAV_UP = 1, -1


def fits(grid, x, y, pol, grav):
    """Can the walker stand with its feet at (x, y)?  It is two cells tall -- the feet cell and
    the head cell on the side away from the pull -- and BOTH must be clear.  Every move below
    goes through this one test; before 2026-10-30 only the feet were tested, which is how a token
    drawn two cells tall was allowed through a one-cell gap."""
    return not solid(grid, x, y, pol) and not solid(grid, x, y - grav, pol)


def settle(grid, x, y, pol, grav):
    """Discrete gravity: fall along the pull until the next cell that way is solid.  Feet only:
    the head trails the feet, so it only ever moves through cells the feet have just cleared."""
    while not solid(grid, x, y + grav, pol):
        y += grav
    return y


def step_target(grid, x, y, pol, grav, f):
    """Where a sideways press lands the walker, or None if a wall or a low ceiling refuses it.

    A clear two-cell column ahead is a plain step, then a fall.  Failing that, one cell higher
    (against the pull) is taken automatically if the walker fits there.  Anything else refuses.
    """
    if fits(grid, x + f, y, pol, grav):
        return (x + f, settle(grid, x + f, y, pol, grav))
    ny = y - grav
    if fits(grid, x + f, ny, pol, grav):
        return (x + f, settle(grid, x + f, ny, pol, grav))
    return None


def _body(x, y, grav):
    return ((x, y), (x, y - grav))


def _walk(grid, state, aid):
    """(new state, set of every cell the walker's body passed through) for one press."""
    x, y, pol, grav = state
    touched = set()
    if aid in (1, 2):
        want = GRAV_UP if aid == 1 else GRAV_DOWN
        if grav != want:
            # Roll over: the old head cell becomes the feet, so the two cells the body fills
            # are the same two cells before and after -- then fall to the far end of the run.
            ny = y - grav
            ey = settle(grid, x, ny, pol, want)
            for yy in range(ny, ey + want, want):
                touched.update(_body(x, yy, want))
            return (x, ey, pol, want), touched
    elif aid in (3, 4):
        f = -1 if aid == 3 else 1
        for ty in (y, y - grav):
            if fits(grid, x + f, ty, pol, grav):
                ey = settle(grid, x + f, ty, pol, grav)
                for yy in range(ty, ey + grav, grav):
                    touched.update(_body(x + f, yy, grav))
                return (x + f, ey, pol, grav), touched
    elif aid == 5:
        if fits(grid, x, y, 1 - pol, grav):
            ey = settle(grid, x, y, 1 - pol, grav)
            for yy in range(y, ey + grav, grav):
                touched.update(_body(x, yy, grav))
            return (x, ey, 1 - pol, grav), touched
    return state, touched


def apply_action(grid, state, aid):
    """(x, y, pol, gravity) + action id -> new state, ignoring creatures.  Refused moves return
    the state unchanged, so terrain alone is never fatal."""
    return _walk(grid, state, aid)[0]


def _clip(y):
    return max(0, min(WORLD_H - 1, y))


def refusal(grid, state, aid):
    """What stopped this press: (cell to flash, shove_x, shove_y).  Every refused press names a
    cell on the board, so the answer to "why didn't that work" is drawn where the obstacle is."""
    x, y, pol, grav = state
    if aid in (1, 2):
        # The pull already points that way: name the surface the walker is held against.
        return ((x, _clip(y + grav)), 0, grav)
    if aid in (3, 4):
        d = -1 if aid == 3 else 1
        # The cell that really stopped the two-cell walker: its head level first (a low ceiling
        # or the top of a wall), then the cell above that, then the feet level.
        for cy in (y - grav, y - 2 * grav, y):
            if solid(grid, x + d, cy, pol):
                return ((x + d, _clip(cy)), d, 0)
        return ((x + d, _clip(y)), d, 0)
    # ACTION5: a cell of the body would turn solid.
    if solid(grid, x, y, 1 - pol):
        return ((x, y), 0, grav)
    return ((x, _clip(y - grav)), 0, -grav)


# ---------------------------------------------------------------------------
# Creatures.  Both are one cell, both are fixed to a column, and where each one is at any moment
# is a pure function of (polarity, pull): the cell it was drawn in is somewhere in an open run of
# air, and it clings to one end of that run.  No creature moves on its own, so the state the
# strand search enumerates is still (x, y, polarity, gravity) and nothing else.
#   D  DRIFTER -- clings to the end of the run that the pull is lifting things away from.
#   C  CRAWLER -- clings to the end of the run that the pull is dropping things toward.
# ---------------------------------------------------------------------------

def creature_cell(grid, kind, x, y, pol, grav):
    """Where one creature is, given the polarity and the pull."""
    return (x, settle(grid, x, y, pol, -grav if kind == "D" else grav))


_CREATURE_CACHE = {}


def creature_cells(index, pol, grav):
    """All creature cells of a level at (pol, grav), as a frozenset."""
    key = (index, pol, grav)
    if key not in _CREATURE_CACHE:
        grid, _s, _g, creatures = _TABLES[index]
        _CREATURE_CACHE[key] = frozenset(
            creature_cell(grid, k, x, y, pol, grav) for k, x, y in creatures)
    return _CREATURE_CACHE[key]


def step_state(index, state, aid):
    """(new state, the cell that killed you or None).  A press kills when the walker's body, on
    any cell of its journey, overlaps a creature where it stood when the press began, or when it
    ends overlapping a creature where it stands after the press (the pull and the world move
    them).  Creatures never block: an unfatal press never touches one."""
    grid = _TABLES[index][0]
    new, touched = _walk(grid, state, aid)
    if new == state or not _TABLES[index][3]:
        return new, None
    hit = touched & creature_cells(index, state[2], state[3])
    if not hit:
        hit = set(_body(new[0], new[1], new[3])) & creature_cells(index, new[2], new[3])
    return new, (min(hit) if hit else None)


ACTION_IDS = (1, 2, 3, 4, 5)


def start_state(index):
    grid, (sx, sy), _g, _c = _TABLES[index]
    return (sx, settle(grid, sx, sy, 0, GRAV_DOWN), 0, GRAV_DOWN)


def _safe_states(index):
    """Every (x, y, pol, gravity) from which the goal is still reachable without touching a
    creature.  Built once per level as a reverse breadth-first search over the whole future, not
    a lookahead.  A state outside this set is stranded."""
    grid, _start, goal, _c = _TABLES[index]
    nodes = [(x, y, p, g)
             for x in range(WORLD_W) for y in range(WORLD_H)
             for p in (0, 1) for g in (GRAV_UP, GRAV_DOWN)
             if fits(grid, x, y, p, g)]
    back = {n: [] for n in nodes}
    for n in nodes:
        for aid in ACTION_IDS:
            m, dead = step_state(index, n, aid)
            if m != n and dead is None:
                back[m].append(n)
    safe = {n for n in nodes if (n[0], n[1]) == goal}
    queue = deque(safe)
    while queue:
        n = queue.popleft()
        for p in back.get(n, ()):
            if p not in safe:
                safe.add(p)
                queue.append(p)
    return safe


_SAFE_CACHE = {}


def safe_states(index):
    if index not in _SAFE_CACHE:
        _SAFE_CACHE[index] = _safe_states(index)
    return _SAFE_CACHE[index]


# ---------------------------------------------------------------------------
# Art.  Every thing on the screen is a named engine sprite on its own layer.  The terrain is four
# pre-baked strips per level (polarity x pull) of which one is visible; the engine camera scrolls
# over them.
# ---------------------------------------------------------------------------

_PIX_CACHE = {}


def _speck(x, y):
    """A deterministic 0..99 hash of a cell, for rock grain."""
    return ((x * 73856093) ^ (y * 19349663) ^ 0x5bd1e995) % 100


def world_pixels(index, pol, grav):
    """The whole 512x64-pixel strip, pre-drawn for one polarity and one pull direction."""
    key = (index, pol, grav)
    if key in _PIX_CACHE:
        return _PIX_CACHE[key]
    grid = _TABLES[index][0]
    img = np.full((WORLD_H * CELL, WORLD_W * CELL), C_GROUND, dtype=int)
    for y in range(WORLD_H):
        py = y * CELL
        for x in range(WORLD_W):
            if solid(grid, x, y, pol):
                px = x * CELL
                img[py:py + CELL, px:px + CELL] = C_FIGURE
    # Grain: deep rock (a cell of fixed rock with no open neighbour) gets a short hot-magenta
    # vein now and then, so a thick mass is a texture and not a flat slab.
    for y in range(1, WORLD_H - 1):
        for x in range(1, WORLD_W - 1):
            if grid[y][x] != FIXED:
                continue
            if all(solid(grid, x + dx, y + dy, pol) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                h = _speck(x, y)
                if h < 14:
                    img[y * CELL + 1, x * CELL + 1:x * CELL + 3] = C_MAGENTA
                elif h < 22:
                    img[y * CELL + 2:y * CELL + 4, x * CELL + 2] = C_MAGENTA
    # Every cell inversion WILL change wears a border on the outside of its region.
    for y in range(WORLD_H):
        py = y * CELL
        for x in range(WORLD_W):
            if grid[y][x] not in (MAT_A, MAT_B):
                continue
            px = x * CELL
            if y == 0 or grid[y - 1][x] not in (MAT_A, MAT_B):
                img[py, px:px + CELL] = C_MUTABLE
            if y == WORLD_H - 1 or grid[y + 1][x] not in (MAT_A, MAT_B):
                img[py + CELL - 1, px:px + CELL] = C_MUTABLE
            if x == 0 or grid[y][x - 1] not in (MAT_A, MAT_B):
                img[py:py + CELL, px] = C_MUTABLE
            if x == WORLD_W - 1 or grid[y][x + 1] not in (MAT_A, MAT_B):
                img[py:py + CELL, px + CELL - 1] = C_MUTABLE
    # The pull, drawn on the world: every solid cell whose ANTI-pull neighbour is open is a face
    # the walker could be held against right now, and gets a one-pixel green line in the last
    # pixel row of the open cell.
    for y in range(WORLD_H):
        py = y * CELL
        if not 0 <= y - grav < WORLD_H:
            continue
        for x in range(WORLD_W):
            if not solid(grid, x, y, pol) or solid(grid, x, y - grav, pol):
                continue
            px = x * CELL
            img[py - 1 if grav > 0 else py + CELL, px:px + CELL] = C_PULL
    _PIX_CACHE[key] = img
    return img


def ring_top(index):
    """Which of the goal cell's two rows the 8x8 ring hangs from: a floor goal takes the cell
    above it, a goal directly under rock takes the cell below."""
    grid, _start, (gx, gy), _c = _TABLES[index]
    above_free = not (solid(grid, gx, gy - 1, 0) or solid(grid, gx, gy - 1, 1))
    return gy - 1 if above_free else gy


def camera_x(wx):
    """The walker sits dead centre of the 16-cell window; the window clamps at the strip ends."""
    return max(0, min(WORLD_W - VIEW, wx - VIEW // 2))


def _px(rows, palette):
    """Sprite art from letter rows: '.' is transparent, other letters look up `palette`."""
    return np.array([[palette[c] if c != "." else -1 for c in r] for r in rows], dtype=np.int8)


# The walker, drawn for a downward pull and facing right: head above, feet below.  Pulled up the
# sprite is mirrored top to bottom, facing left it is mirrored left to right.  Eight pixels tall
# is exactly the two cells the physics gives it.
_WALKER = [
    ".oo.",
    "oooo",
    "ooKo",
    "oooo",
    ".oo.",
    "oooo",
    "oooo",
    "g..g",
]
_CREATURE_ART = {
    # drawn for a downward pull: the drifter's dome is up, tentacles down; the crawler's horns up
    "D": [".LL.", "LKKL", "LLLL", "L.L."],
    "C": ["M..M", "MMMM", "MKKM", ".MM."],
}
_RING_PX = np.array([[1 if (dx < 2 or dx >= 6 or dy < 2 or dy >= 6) else -1
                      for dx in range(8)] for dy in range(8)], dtype=np.int8)


def _clamp_art(grav):
    """The lock socket: a two-pixel frame round the whole two-cell token on three sides, open on
    the side away from the pull.  Returns (pixels, dx, dy) with dx, dy the offset of the array's
    corner from the feet cell's corner."""
    h = 8 + 2
    a = np.full((h, 8), -1, dtype=np.int8)
    if grav > 0:
        a[:, 0:2] = C_CLAMP
        a[:, 6:8] = C_CLAMP
        a[h - 2:, :] = C_CLAMP
        return a, -2, -4
    a[:, 0:2] = C_CLAMP
    a[:, 6:8] = C_CLAMP
    a[0:2, :] = C_CLAMP
    return a, -2, -2


class Ng02(ARCBaseGame):
    def __init__(self):
        self.grid = _TABLES[0][0]
        self.goal = _TABLES[0][2]
        self.wx = self.wy = 0
        self.pol = 0
        self.grav = GRAV_DOWN
        self.facing = 1
        self.flash = None
        self.pulse = 0
        self.stranded = False
        self.dead_at = None
        self.safe = frozenset()
        self.index = 0
        self.ring_row = 0
        self.sp = {}
        self.creatures = ()

        levels = [Level(sprites=[], grid_size=(64, 64), data=ldef, name=ldef["name"])
                  for ldef in LEVELS]

        super().__init__(
            "ng",
            levels,
            Camera(0, 0, 64, 64, C_GROUND, C_GROUND, []),
            False,
            len(levels),
            [1, 2, 3, 4, 5],     # 1/2 = pull up/down, 3/4 = step left/right, 5 = invert
        )

    # -- sprite construction ------------------------------------------------

    def _make_sprites(self, level, idx):
        for s in list(level.get_sprites()):
            level.remove_sprite(s)
        sp = {}

        def add(name, pixels, layer, tags, x=0, y=0, visible=True):
            s = Sprite(pixels, name=name, x=x, y=y, layer=layer, tags=tags, visible=visible,
                       collidable=False)
            level.add_sprite(s)
            sp[name] = s
            return s

        for p in (0, 1):
            for g, tag in ((GRAV_DOWN, "dn"), (GRAV_UP, "up")):
                add(f"rock_p{p}_{tag}", world_pixels(idx, p, g).astype(np.int8), 0,
                    ["terrain"], visible=False)
        for g, tag in ((GRAV_DOWN, "dn"), (GRAV_UP, "up")):
            px, dx, dy = _clamp_art(g)
            s = add(f"clamp_{tag}", px, 3, ["status"], visible=False)
            s.dx, s.dy = dx, dy
        add("goal_ring", np.where(_RING_PX >= 0, C_GOAL, -1).astype(np.int8), 2, ["goal"])
        add("goal_ring_dark", np.where(_RING_PX >= 0, C_DEAD, -1).astype(np.int8), 2, ["goal"],
            visible=False)
        pal = {"o": C_WALKER, "K": C_BLACK, "g": C_PULL}
        add("walker", _px(_WALKER, pal), 5, ["walker"])
        pal_dead = {"o": C_DEAD, "K": C_DEAD, "g": C_DEAD}
        add("walker_dark", _px(_WALKER, pal_dead), 5, ["walker"], visible=False)
        add("burst_cell", np.full((4, 4), C_REFUSE, dtype=np.int8), 6, ["event"], visible=False)
        for k in (1, 2):
            add(f"burst_halo_{k}", np.full((8 + 2 * k, 4 + 2 * k), C_REFUSE, dtype=np.int8), 4,
                ["event"], visible=False)
        self.creatures = []
        for i, (kind, x, y) in enumerate(_TABLES[idx][3]):
            col = C_DRIFTER if kind == "D" else C_CRAWLER
            nm = "drifter" if kind == "D" else "crawler"
            pal = {"L": col, "M": col, "K": C_BLACK}
            self.creatures.append((add(f"{nm}_{i}", _px(_CREATURE_ART[kind], pal), 4,
                                       ["creature", nm]), kind, x, y))
        self.sp = sp

    # -- level setup --------------------------------------------------------

    def on_set_level(self, level: Level) -> None:
        idx = self.level_index
        grid, start, goal, _c = _TABLES[idx]
        self.index = idx
        self.grid = grid
        self.goal = goal
        self.ring_row = ring_top(idx)
        self.wx, self.wy = start_state(idx)[:2]
        self.grav = GRAV_DOWN
        self.pol = 0
        self.facing = 1
        self.flash = None
        self.pulse = 0
        self.stranded = False
        self.dead_at = None
        self.safe = safe_states(idx)
        self._make_sprites(level, idx)
        self._sync()

    # -- drawing: move the named sprites to where the state says they are ----

    def _sync(self):
        sp = self.sp
        self.camera.x = camera_x(self.wx) * CELL
        tag = "dn" if self.grav > 0 else "up"
        for p in (0, 1):
            for t in ("dn", "up"):
                sp[f"rock_p{p}_{t}"].set_visible(p == self.pol and t == tag)
        gx = self.goal[0]
        over = self.stranded
        sp["goal_ring"].set_visible(not over).set_position(gx * CELL, self.ring_row * CELL)
        sp["goal_ring_dark"].set_visible(over).set_position(gx * CELL, self.ring_row * CELL)

        bx = self.wx * CELL
        top = (self.wy - 1) * CELL if self.grav > 0 else self.wy * CELL    # token's top edge
        ox = oy = 0
        for k in (1, 2):
            sp[f"burst_halo_{k}"].set_visible(False)
        sp["burst_cell"].set_visible(False)
        if self.flash and not self.stranded:
            (fx, fy), dx, dy = self.flash
            grow = 1 + self.pulse
            ox, oy = dx * grow, dy * grow
            sp["burst_cell"].set_visible(True).set_position(fx * CELL, fy * CELL)
            sp[f"burst_halo_{grow}"].set_visible(True).set_position(bx - grow, top - grow)
        if self.dead_at is not None:
            sp["burst_cell"].set_visible(True).set_position(self.dead_at[0] * CELL,
                                                            self.dead_at[1] * CELL)
        for w, name in ((False, "walker"), (True, "walker_dark")):
            s = sp[name]
            s.set_visible(self.stranded == w)
            s.set_mirror_lr(self.facing < 0).set_mirror_ud(self.grav < 0)
            s.set_position(bx + ox, top + oy)
        # The lock clamp: any cell of the body would turn solid if the world inverted.
        locked = (not self.stranded and
                  any(solid(self.grid, cx, cy, 1 - self.pol)
                      for cx, cy in _body(self.wx, self.wy, self.grav)))
        for t in ("dn", "up"):
            s = sp[f"clamp_{t}"]
            on = locked and t == tag
            s.set_visible(on)
            if on:
                s.set_position(bx + s.dx, self.wy * CELL + s.dy)
        for s, kind, x, y in self.creatures:
            cx, cy = creature_cell(self.grid, kind, x, y, self.pol, self.grav)
            s.set_position(cx * CELL, cy * CELL)
            s.set_mirror_ud(self.grav < 0)

    # -- engine entry point -------------------------------------------------

    def step(self) -> None:
        aid = self.action.id.value
        self.flash = None
        state = (self.wx, self.wy, self.pol, self.grav)
        if aid in (3, 4):
            self.facing = -1 if aid == 3 else 1     # decoration, and free even when refused

        if aid not in ACTION_IDS:
            self._sync()
            self.complete_action()
            return

        moved, killed_at = step_state(self.index, state, aid)
        if moved == state:
            # Nothing changed -- a wall, a low ceiling, an inversion that would bury the walker,
            # or the pull aimed the way it already points. Name the cell that stopped it.
            self.pulse ^= 1
            self.flash = refusal(self.grid, state, aid)
        self.wx, self.wy, self.pol, self.grav = moved

        if killed_at is not None:
            self.stranded = True
            self.dead_at = killed_at
            self._sync()
            self.lose()
            self.complete_action()
            return

        if (self.wx, self.wy) == self.goal:
            self.next_level()
            self.complete_action()
            return

        # Being stranded: the goal has genuinely become unreachable. The walker and the ring go
        # dark on the very frame it happens, and RESET is always there.
        if moved not in self.safe:
            self.stranded = True
            self._sync()
            self.lose()
            self.complete_action()
            return

        self._sync()
        self.complete_action()
