# Author: Claude Sonnet 5.5 (the art pass); Claude Opus 5.5 High and Mark Barney (dz01, the game and its rules)
# Date: 07-November-2026
# CHANGELOG: 07-Nov-2026 (Claude Sonnet 5.5) -- pass 3, variety and life. Sand drawn in strata bands (a second colour ramp
#   per level, so no level is one flat field); level four's white moon dust is now blue and pink; a horizon of two hill
#   layers shaped per level in the sky strip; big buried set pieces (ribs, mushroom, arch, rocket, skull, crystals, a
#   sunken boat) behind the pockets; six little inert creatures per level crawling, swimming or flitting in the hollows;
#   the world's idle clock now also jumps between moves, so every resting picture differs; a five-picture run-over
#   (burst, squashed hero circled by stars, a ghost rising); a win with a themed shower (coins, leaves, stars, embers,
#   flakes, petals, gems) and three fireworks. Rules untouched.
# CHANGELOG: 07-Nov-2026 (Claude Sonnet 5.5) -- pass 2, the critique pass. New colour ramps per level for sand, earth and
#   rock (eight different looks, no grey); a wall pattern per level's pockets plus drifting little lives in them (bubbles,
#   embers, fireflies, dust, sparkles); a redrawn hero (lamp helmet, overalls, boots, crossed-eye dead face) and three
#   creatures with their own silhouettes whose eyes follow the hero; five sand pictures per style; a run-over look that
#   recolours the whole world darker and redder (no dotted veil) with a sad rain cloud over the hero; a denser win with a
#   ring of sparks, a hop and a scalloped curtain. Rules untouched.
# CHANGELOG: 07-Nov-2026 (Claude Sonnet 5.5) -- first version. dz01 redrawn at Mark Barney's call as named sprites in
#   the sprite-book way: a backdrop per level, a ground and an item pool that follow the camera, the hero and every effect
#   as single moving sprites, a drawn side panel, drawn win and run-over feedback. The rules, levels, budgets and inputs
#   are dz01's, copied unchanged.
# PURPOSE: dz02 -- the art pass on dz01: dig down a shaft of sand, packed earth and rock to the checkered finish at the
#   bottom. THE RULES ARE UNCHANGED: every level's layout, hearts, click budget, the inputs (arrows, space, click), the
#   fights, the falling, the lit star and the energy cells behave exactly as in dz01. Only what is on screen changed:
#   eight themed levels (sky, pocket colours, scenery, panel), a drawn hero and creatures with faces, and gentle
#   idle motion (drifting clouds, swaying palms, twinkling stars, blinking eyes) that does nothing and means nothing.
#   Plugs into arcengine 0.9.3 as an ARCBaseGame with actions 1-6 (6 is a click with x, y).
# SRP/DRY check: Pass -- the rules are pure functions on a small DigState (act, settle, can_go_on) shared with the
#   searches; the pictures are data at the top of the art section; Scene.show is the only code that touches sprites and
#   it only reads (state, fx). Nothing here duplicates a helper elsewhere in the repo (games must be one file).
"""Dz02 -- dig down to the checkered floor (dz01 with new art).

Click a cell next to the hero to dig it: sand goes in one click, packed earth in two, rock in three; bedrock
never. Each click comes out of the bar at the side. The hero falls into whatever he opens, and loose sand,
hearts, stars and red-eyed creatures fall into pockets opened under them. Walk into a creature to fight it:
you punch out a stripe, it punches out a heart, until its last stripe goes. Space lights a star you carry.
"""

import math

import numpy as np
from arcengine import ARCBaseGame, BlockingMode, Camera, GameAction, Level, Sprite

# ---------------------------------------------------------------------------
# Palette (ARC-3 indices). No greys anywhere: the early-console look Mark Barney asked for.
# ---------------------------------------------------------------------------
C_WHITE, C_BLACK = 0, 5
C_RED, C_BLUE, C_LBLUE = 8, 9, 10
C_YELLOW, C_ORANGE, C_MAROON, C_GREEN, C_PURPLE = 11, 12, 13, 14, 15

# ---------------------------------------------------------------------------
# Geometry: a shaft eight cells wide, cells seven pixels square, nine rows on screen; the panel on the right
# holds the hearts, the star slot and the bar (budget as its draining background, the hero's depth as a dot,
# the checkered finish at its foot).
# ---------------------------------------------------------------------------
W = 8
CELL = 7
VIEW = 9
PANEL_X = W * CELL          # 56
HERO_ROW_ON_SCREEN = 3      # the view keeps the hero on the fourth row while it can
ENERGY_FILL = 8             # clicks an energy cell puts back in the bar (never past full)
STAR_LEN = 8                # a lit star lasts eight moves: one spark of the ring per move
MAX_HEARTS = 3

# ---------------------------------------------------------------------------
# Cells. Creatures are CRE + stripes (1 crab, 2 mole, 3 worm), plus DROP for a red-eyed dropper.
# ---------------------------------------------------------------------------
AIR, SAND, EARTH, EARTH1, ROCK, ROCK1, ROCK2, BED, HEART, STAR, ENERGY = range(11)
CRE, DROP = 16, 4
ITEMS = (HEART, STAR, ENERGY)
PASS = (AIR, HEART, STAR, ENERGY)                 # what the hero can step or fall into
CLIMB = (SAND, EARTH, EARTH1)            # what the hero can climb one cell against
DIG_NEXT = {SAND: AIR, EARTH: EARTH1, EARTH1: AIR, ROCK: ROCK1, ROCK1: ROCK2, ROCK2: AIR}
CHARS = {".": AIR, "s": SAND, "e": EARTH, "r": ROCK, "#": BED, "h": HEART, "*": STAR, "+": ENERGY,
         "c": CRE + 1, "m": CRE + 2, "w": CRE + 3, "C": CRE + 1 + DROP, "M": CRE + 2 + DROP, "W": CRE + 3 + DROP}
NEIGH = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}


def is_cre(v):
    return v >= CRE


def cre_stripes(v):
    return (v - CRE) & 3


def falls(v):
    """Loose things fall into air under them: sand, hearts, stars, energy cells and droppers. Earth, rock, bedrock and
    ordinary creatures (they cling to their pocket) never do."""
    return v == SAND or v == HEART or v == STAR or v == ENERGY or (v >= CRE and (v - CRE) & DROP)


# ---------------------------------------------------------------------------
# The rules: pure functions on a DigState, shared by the game, the generator and the checks
# ---------------------------------------------------------------------------

class DigState:
    """Everything that decides the future of a level: the ground (one byte a cell, row-major, W wide), the
    hero's cell, hearts, clicks left (never more than full), a carried star, a lit star's moves left, and whether the hero is perched
    (he climbed one cell and holds on until he moves)."""
    __slots__ = ("g", "h", "r", "c", "hearts", "clicks", "full", "star", "lit", "perched")

    def copy(self):
        s = DigState.__new__(DigState)
        s.g = bytearray(self.g)
        s.h, s.r, s.c = self.h, self.r, self.c
        s.hearts, s.clicks, s.full = self.hearts, self.clicks, self.full
        s.star, s.lit, s.perched = self.star, self.lit, self.perched
        return s

    def key(self):
        return (bytes(self.g), self.r, self.c, self.hearts, self.clicks, self.star, self.lit, self.perched)

    def at(self, r, c):
        if c < 0 or c >= W or r < 0:
            return BED                     # the shaft walls and the sky above the surface are not ground
        if r >= self.h:
            return BED                     # the finish floor
        return self.g[r * W + c]


def parse_level(spec):
    """A level spec (rows of characters, hero cell, hearts, click budget) -> a settled DigState."""
    s = DigState.__new__(DigState)
    rows = spec["rows"]
    s.h = len(rows)
    s.g = bytearray(CHARS[ch] for row in rows for ch in row)
    s.r, s.c = spec["hero"]
    s.hearts = spec["hearts"]
    s.clicks = s.full = spec["budget"]
    s.star, s.lit, s.perched = 0, 0, False
    s.g[s.r * W + s.c] = AIR
    settle(s)
    return s


def cam_top(r, h):
    """Top row on screen: the view follows the hero down the shaft and stops with the finish on the bottom row."""
    return max(0, min(r - HERO_ROW_ON_SCREEN, h + 1 - VIEW))


def cell_xy(r, c, hero_r, h):
    """Screen point of a cell's centre, the click that digs it (used by the generator's lines)."""
    return c * CELL + CELL // 2, (r - cam_top(hero_r, h)) * CELL + CELL // 2


def _pickup(s):
    """The hero has just entered his cell: a heart, a star or an energy cell there is his."""
    i = s.r * W + s.c
    v = s.g[i]
    if v == HEART:
        s.hearts = min(MAX_HEARTS, s.hearts + 1)
        s.g[i] = AIR
        return "heart"
    if v == STAR:
        s.star = 1
        s.g[i] = AIR
        return "star"
    if v == ENERGY:
        s.clicks = min(s.full, s.clicks + ENERGY_FILL)
        s.g[i] = AIR
        return "energy"
    return None


def settle(s, rec=None):
    """Gravity, one cell a tick, until nothing moves. Each tick scans bottom-up so a column falls together as a
    block. The hero falls unless perched; things fall onto him and rest there (he holds them up). rec(s, fx), when
    given, records a frame per tick. Returns the pickups made while falling."""
    got = []
    g = s.g
    for _ in range(2 * s.h + 4):
        moved = False
        for row in range(s.h - 2, -1, -1):
            base = row * W
            for col in range(W):
                if s.r == row and s.c == col:
                    if not s.perched and g[base + W + col] in PASS:
                        s.r += 1
                        moved = True
                        p = _pickup(s)
                        if p:
                            got.append(p)
                    continue
                v = g[base + col]
                if v and falls(v) and g[base + W + col] == AIR and not (s.r == row + 1 and s.c == col):
                    g[base + W + col] = v
                    g[base + col] = AIR
                    moved = True
        if not moved:
            break
        if rec:
            rec(s, {"fall": True})
    return got


class Result:
    """What act() did: the outcome ('win', 'die' or None), whether anything happened, the clicks spent, the
    hearts lost in fights, whether a rock cell was dug (the generator's keep rules read those two), and whether a
    dropper landed on the hero and was fought."""
    __slots__ = ("outcome", "acted", "spent", "hurt", "rock", "lit_used", "why", "dropped_on")

    def __init__(self):
        self.outcome, self.acted, self.spent, self.hurt, self.rock, self.lit_used, self.why = None, False, 0, 0, False, False, None
        self.dropped_on = False                 # a dropper landed on the hero this move and was fought


def act(s, a, cell=None, rec=None, check=True):
    """Play one action on a copy of s. a is 1-4 (up, down, left, right), 5 (space) or 6 (dig `cell`, a (row,
    col)). rec(state, fx) records animation frames; the game passes one, the search does not. With check, a
    level that can no longer be finished (no clicks left and the finish out of reach on foot) is a death.
    Returns (new state, Result)."""
    s = s.copy()
    res = Result()
    snap = rec or (lambda st, fx: None)

    if a == 5:
        if s.star and not s.lit:
            s.star, s.lit = 0, STAR_LEN
            res.acted = True
            snap(s, {"light": 2})
            snap(s, {"light": 1})
        else:
            snap(s, {"slot_flash": True})       # an answer, no cost: the empty slot flashes
        return s, res

    lit_now = s.lit > 0
    if a in NEIGH:
        dr, dc = NEIGH[a]
        tr, tc = s.r + dr, s.c + dc
        v = s.at(tr, tc)
        if is_cre(v):
            _fight(s, tr, tc, v, res, snap)
        elif a == 1:
            side = (s.at(s.r, s.c - 1) in CLIMB) or (s.at(s.r, s.c + 1) in CLIMB)
            if not s.perched and v in PASS and side:
                s.r = tr
                s.perched = True
                res.acted = True
                p = _pickup(s)
                snap(s, {"pick": p} if p else {})
            else:
                _nudge(s, dr, dc, snap)
        elif v in PASS and tr < s.h:
            s.r, s.c = tr, tc
            s.perched = False
            res.acted = True
            p = _pickup(s)
            snap(s, {"step": (dr, dc)} if not p else {"pick": p})
        else:
            _nudge(s, dr, dc, snap)
    elif a == 6:
        _dig(s, cell, res, snap)

    if res.outcome == "die":
        return s, res
    if res.acted:
        held = {i for i, v in enumerate(s.g) if v >= CRE and (v - CRE) & DROP}
        for p in settle(s, rec):
            snap(s, {"pick": p})
        # a dropper that came down this move and landed on the hero's head drops in on him: the fight starts at
        # once, the same punch trade as walking into it (a lit hero flattens it); then the sand behind it settles
        top = (s.r - 1) * W + s.c
        if s.r >= 1 and s.g[top] >= CRE and (s.g[top] - CRE) & DROP and top not in held:
            _fight(s, s.r - 1, s.c, s.g[top], res, snap)
            if res.outcome == "die":
                return s, res
            res.dropped_on = True
            for p in settle(s, rec):
                snap(s, {"pick": p})
        if lit_now and s.lit > 0:
            s.lit -= 1                          # one spark of the ring goes out per move
            res.lit_used = True
            snap(s, {})
    if s.r >= s.h - 1:
        res.outcome = "win"
    elif check and res.acted and not can_go_on(s):
        res.outcome = "die"
        res.why = "budget"
    return s, res


def _nudge(s, dr, dc, snap):
    """Solid ground (or the shaft wall): the hero leans into it and back, nothing spent."""
    snap(s, {"lean": (dr, dc)})
    snap(s, {})


def _fight(s, tr, tc, v, res, snap):
    """Walk into a creature: the hero punches a stripe out, it punches a heart out, until its last stripe goes;
    a creature whose last stripe falls never lands its hit. A lit hero flattens it at no cost. The hero keeps
    his cell; the pocket opens and whatever was above it falls in (settled by act)."""
    n = cre_stripes(v)
    res.acted = True
    i = tr * W + tc
    if s.lit:
        snap(s, {"punch": (tr, tc), "stripes_out": n, "flat": True})
        s.g[i] = AIR
        return
    for k in range(1, n + 1):
        # the hero's punch: a spark where they meet and stripe k goes out; then a beat to see it
        snap(s, {"punch": (tr, tc), "stripes_out": k, "spark": (tr, tc)})
        snap(s, {"show": (tr, tc), "stripes_out": k})
        if k < n:
            s.hearts -= 1
            res.hurt += 1
            if s.hearts <= 0:
                # the last heart is gone: the creature that took it turns red and the hero breaks
                for b in range(1, 6):
                    snap(s, {"hit_back": (tr, tc), "stripes_out": k, "red": (tr, tc), "poof": b})
                res.outcome = "die"
                res.why = "fight"
                return
            # its punch back: it lunges, the hero flashes red and a heart goes dark; then a beat
            snap(s, {"hit_back": (tr, tc), "stripes_out": k, "spark": (tr, tc), "hurt": True})
            snap(s, {"show": (tr, tc), "stripes_out": k})
    snap(s, {"crumple": (tr, tc), "stripes_out": n})
    s.g[i] = AIR


def _dig(s, cell, res, snap):
    """Dig a neighbouring cell. Sand clears; earth and rock crack toward clearing. A lit hero digs sand for
    free, and the sand above it puffs away with it instead of pouring in. Anything else is a cursor nudge."""
    if cell is None:
        snap(s, {"mark": None})
        return
    tr, tc = cell
    v = s.at(tr, tc) if (0 <= tc < W and 0 <= tr < s.h) else BED
    near = abs(tr - s.r) + abs(tc - s.c) == 1
    if not near or v not in DIG_NEXT:
        snap(s, {"mark": cell})
        snap(s, {})
        return
    free = s.lit > 0 and v == SAND
    if not free and s.clicks <= 0:
        snap(s, {"mark": cell, "bar_flash": True})
        snap(s, {})
        return
    res.acted = True
    if not free:
        s.clicks -= 1
        res.spent = 1
    if v in (ROCK, ROCK1, ROCK2):
        res.rock = True
    snap(s, {"cursor": cell})
    nv = DIG_NEXT[v]
    s.g[tr * W + tc] = nv
    puffs = [cell]
    if free:
        rr = tr - 1
        while rr >= 0 and s.g[rr * W + tc] == SAND:
            s.g[rr * W + tc] = AIR
            puffs.append((rr, tc))
            rr -= 1
    if nv == AIR:
        snap(s, {"puff": puffs})
    else:
        snap(s, {"crack": cell})


def can_go_on(s):
    """Can the level still be finished? While clicks are left (or a lit star can dig sand), yes, as far as this
    test goes: the run ends only when the budget is out and the finish is out of reach. With no
    clicks, search the moves on foot (and a lit hero's free sand digs) for the finish; a long search says yes. An energy
    cell reached on foot puts clicks back, and from there the level can go on."""
    if s.clicks > 0:
        return True
    seen = {s.key()}
    todo = [s]
    while todo:
        cur = todo.pop()
        moves = [(a, None) for a in (1, 2, 3, 4)]
        if cur.lit:
            moves += [(6, (cur.r + dr, cur.c + dc)) for dr, dc in NEIGH.values()]
        for a, cell in moves:
            nxt, res = act(cur, a, cell, check=False)
            if not res.acted or res.outcome == "die":
                continue
            if res.outcome == "win" or nxt.clicks > 0:
                return True
            k = nxt.key()
            if k not in seen:
                seen.add(k)
                if len(seen) > 4000:
                    return True
                todo.append(nxt)
    return False



# ---------------------------------------------------------------------------
# Levels (written by a level generator between the markers; do not hand-edit)
# ---------------------------------------------------------------------------
# BEGIN LEVELS
LEVELS = [
    {"name": "dz02-1", "hero": [0, 5], "hearts": 3, "budget": 30,
     "rows": ["........",
              "ssssssss",
              "ssssscss",
              "ssssssss",
              "ssssssss",
              "ssssssss",
              "ssssssss",
              "ssssssss",
              "sssccsss",
              "ssssss+s",
              "ssssssss",
              "csssssss",
              "ssssssss",
              "ssssssss"]},
    {"name": "dz02-2", "hero": [0, 5], "hearts": 1, "budget": 18,
     "rows": ["........",
              "ssssssss",
              "ssssssss",
              "meeeemee",
              "ssssscss",
              "ssssssss",
              "ssssssss",
              "eemeeeee",
              "sssshsss",
              "sssss+ss",
              "sssscsss",
              "eememeee",
              "sshsssss",
              "ssssssss",
              "ssssssss"]},
    {"name": "dz02-3", "hero": [0, 3], "hearts": 1, "budget": 22,
     "rows": ["........",
              "ssssssss",
              "ssssssss",
              "#rwrrr#r",
              "ssssss.s",
              "s###hsss",
              "sseeeess",
              "sssssscs",
              "##shssss",
              "##sseees",
              "sssshsss",
              "ssssscss",
              "ssss+sss",
              "eeeemmee",
              "ssssshss",
              "ssssssss",
              "ssssssss"]},
    {"name": "dz02-4", "hero": [0, 2], "hearts": 2, "budget": 23,
     "rows": ["........",
              "ssssssss",
              "ssssssss",
              "ssseeess",
              "sssM*sss",
              "ssssssss",
              "###sssss",
              "ssssssss",
              "eeeeeemm",
              "ssssssss",
              "sssss+sM",
              "ssssssch",
              "ssss###r",
              "ssssssss",
              "ssssssss",
              "seeessss",
              "ssssssss",
              "ssssssss"]},
    {"name": "dz02-5", "hero": [0, 5], "hearts": 2, "budget": 30,
     "rows": ["........",
              "ssssssss",
              "ssssssss",
              "rrrrwr#r",
              "sssss*ss",
              "sssss##s",
              "rrrrr##s",
              "sssCssss",
              "ssssssss",
              "eeeeeeem",
              "sss##css",
              "scssss+s",
              "ssssrrrr",
              "sssss.ss",
              "hsCsssss",
              "csssss+s",
              "seeeeees",
              "ss.ssshs",
              "ssssssss",
              "ssssssss"]},
    {"name": "dz02-6", "hero": [0, 3], "hearts": 2, "budget": 32,
     "rows": ["........",
              "ssssssss",
              "ssssssss",
              "ssrrrsss",
              "ss##*sss",
              "ssssssss",
              "ssssssss",
              "srrrssss",
              "ssshssss",
              "sMssssss",
              "sssc+sss",
              "eememeee",
              "Msssssss",
              "sscsssss",
              "r####rrw",
              "s+###sws",
              "ssssssss",
              "meee##ee",
              "swssssss",
              "shssssss",
              "ssssssss",
              "ssssssss"]},
    {"name": "dz02-7", "hero": [0, 3], "hearts": 2, "budget": 40,
     "rows": ["........",
              "ssssssss",
              "*sssssss",
              "rw#rrr#r",
              "rrw###rr",
              "ssssssss",
              "ssss##ss",
              "sshr##rr",
              "s+sswsss",
              "MsCsssss",
              "ssssssss",
              "r#rrrwrr",
              "rwr##r#r",
              "css##sss",
              "ssssssss",
              "rrrrrrss",
              "ssssssss",
              "+sshcsss",
              "ssssssss",
              "meeemeee",
              "ssssssss",
              "ssssssss"]},
    {"name": "dz02-8", "hero": [0, 2], "hearts": 1, "budget": 35,
     "rows": ["........",
              "ssssssss",
              "ss*sssss",
              "ssssssss",
              "rrw#rrr#",
              "rrwrrr#r",
              "r#wrr###",
              "#rwrr#rr",
              "##wrr#r#",
              "rrw#r#r#",
              "#rw#rrr#",
              "........",
              "...+....",
              "eeee....",
              "........",
              "....c...",
              ".eeeee..",
              "....c...",
              "...eeee.",
              ".....c..",
              ".eeeee..",
              "........",
              "ssssssss",
              "ssssssss"]},
]
# END LEVELS


# ---------------------------------------------------------------------------
# Pictures: the sprite book. Every picture is drawn here by hand, one character a pixel, then
# recoloured per level by a theme. "." is see-through. No letters ever reach the screen.
# ---------------------------------------------------------------------------
C_MAG, C_PINK = 6, 7
_COL = {"Y": C_YELLOW, "O": C_ORANGE, "M": C_MAROON, "K": C_BLACK, "R": C_RED, "W": C_WHITE, "B": C_BLUE,
        "L": C_LBLUE, "G": C_GREEN, "P": C_PURPLE, "A": C_MAG, "N": C_PINK}


def _art(rows, extra=None):
    """Character rows -> a numpy picture (-1 = see-through)."""
    cmap = dict(_COL)
    if extra:
        cmap.update(extra)
    return np.array([[cmap.get(ch, -1) for ch in row] for row in rows], dtype=np.int8)


def _recolour2(rows, colour):
    """Rows of 'X' and '.' -> a picture in one colour."""
    return _art(rows, {"X": colour})


def _hash(a, b=0, c=0):
    """A small stable scramble: the same place always gets the same texture."""
    n = (a * 73856093) ^ (b * 19349663) ^ (c * 83492791)
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return n ^ (n >> 16)


# --- the ground -------------------------------------------------------------------------------------------------
# S = speck colour, set per level. Three sand patterns so a wall of sand never tiles in a line.
# Four ways to draw sand (a theme picks one): ripples, grass tufts, gravel, glitter. S = the theme's speck colour.
SAND_STYLES = {
    "dune": (["YYYYYYY", "YOOYYYY", "YYYOOYY", "YYYYYYY", "YYYYYWY", "YSYYYYY", "YYYYYYY"],
             ["YYYYYYY", "YYYYYSY", "YYWYYYY", "YYYYYYY", "YOOYYYY", "YYYOOYY", "YYYYYYY"],
             ["YYYYYYY", "YYYYYYY", "YSYYYOO", "YYYYOYY", "YYYYYYY", "YYWYYYY", "YYYYYSY"],
             ["YYYYYYY", "YOOOYYY", "YYYYYYW", "YYYYYYY", "YYSYOOO", "YYYYYYY", "YYYYYYY"],
             ["YYYYYYY", "YYYYYYY", "YWYYYYY", "YYYYSYY", "OOOYYYY", "YYYYYYO", "YYYYYYY"]),
    "tuft": (["YYYYYYY", "YYYYYYY", "YSYSYYY", "YYSYYYY", "YYYYYOY", "YYYYYYY", "YYWYYYY"],
             ["YYYYYYY", "YYYYSYS", "YYYYYSY", "YYYYYYY", "YOYYYYY", "YYYWYYY", "YYYYYYY"],
             ["YYYYYYY", "YWYYYYY", "YYYYYYY", "YYYYSYS", "YYYYYSY", "YYOYYYY", "YYYYYYY"],
             ["YYYYYYY", "YYYYYYY", "YSYSYWY", "YYSYYYY", "YYYYYYY", "YYYYSYS", "YYYYYSY"],
             ["YYYYYYY", "YYYSYSY", "YYYYSYY", "YYYYYYY", "YOYYYYY", "YYYYYWY", "YYYYYYY"]),
    "gravel": (["YYYYYYY", "YSSYYYY", "YYYYYYY", "YYYYSSY", "YYYYYYY", "YOOYYYY", "YYYYYYY"],
               ["YYYYYYY", "YYYYYSS", "YYYYYYY", "YSSYYYY", "YYYYYYY", "YYYYOOY", "YYYYYYY"],
               ["YYYYYYY", "YYSSYYY", "YYYYYYY", "YYYYYOO", "YSSYYYY", "YYYYYYY", "YYYWYYY"],
               ["YYYYYYY", "YYYYYYY", "YOOYSSY", "YYYYYYY", "YYYYYYY", "YSSYYOO", "YYYYYYY"],
               ["YYYYYYY", "YSYYYYY", "YSSYYYY", "YYYYYYY", "YYYYSOO", "YYYYYYY", "YYWYYYY"]),
    "glitter": (["YYYYYYY", "YYYWYYY", "YYWSWYY", "YYYWYYY", "YYYYYYY", "YYYYYOY", "YOYYYYY"],
                ["YYYYYYY", "YYYYYYY", "YYWYYYY", "YWSWYYY", "YYWYYYY", "YYYYYYY", "YYYYOYY"],
                ["YYYYYYY", "YYYYWYY", "YYYWSWY", "YYYYWYY", "YYYYYYY", "YOYYYYY", "YYYYYYY"],
                ["YYYYYYY", "YYYYYYY", "YOYYYYY", "YYYWYYY", "YYWSWYY", "YYYWYYY", "YYYYYOY"],
                ["YYYYYYY", "YWYYYYY", "WSWYYYY", "YWYYYYY", "YYYYYYY", "YYYYYWY", "YYYYWSW"]),
}
EARTH_ROWS = (
    ["OOOOOOO", "OMMOOOO", "OMMOOPO", "OOOOOOO", "OOOOMMO", "OPOOMMO", "OOOOOOO"],
    ["OOOOOOO", "OOPOOOO", "GOOOMMM", "OGOOOOO", "OOOOOPO", "MMMOOOO", "OOOOOOO"],
)
# bevelled brick: H high light, R face, M shadow, K joint
ROCK_ROWS = (
    ["KKKKKKK", "KHHHHRK", "KHRRRMK", "KHRRMMK", "KRRMMMK", "KRMMMMK", "KKKKKKK"],
    ["KKKKKKK", "KHHRRRK", "KHRKRMK", "KRRRRMK", "KRMRMMK", "KRMMMMK", "KKKKKKK"],
)
BED_ROWS = ["BBBBBBB", "BKKKKKK", "BKPKKPK", "BKKKKKK", "BKKPKKK", "BKKKKPK", "BKKKKKK"]
CRACK_A = ["...K...", "..K....", "...K...", "....K..", "...K...", "..K....", "...K..."]
CRACK_B = [".......", "K......", ".K...K.", "..K.K..", "...K...", "....K..", "......."]


def _overlay(base, rows, colour):
    """Paint the 'K' pixels of rows onto base in colour."""
    out = base.copy()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "K":
                out[y, x] = colour
    return out


def _light(base, open_above, open_below, hi, mid, lo, dk):
    """Sun-lit crest where the ground meets open air above, a shaded lip where it hangs over a pocket. The four colours
    are the kind's own ramp (light, base, dark, darkest), so every theme lights its own ground in its own colours."""
    out = base.copy()
    if open_above:
        out[0, :] = np.where(out[0, :] == mid, hi, np.where(out[0, :] == lo, mid, out[0, :]))
    if open_below:
        out[6, :] = np.where(out[6, :] == mid, lo, np.where(out[6, :] == lo, dk, out[6, :]))
    return out


# --- levels' looks: sky, the dug pocket's colours and wall pattern, a colour ramp per kind of ground, the panel frame,
# scenery, and the little lives drifting in the pockets. ---------------------------------------------------------------
# sand_c / earth_c = (base, dark, light, darkest); rock_c = (face, shadow, highlight). sand < earth < rock in weight,
# in every theme, so the three kinds of ground are told apart by texture and darkness whatever the colours are.
# props: (kind, x, y, motion). y is the picture's top in the 7-pixel strip of sky above the ground.
THEMES = [
    dict(name="dunes", sand="dune", sky=C_LBLUE, sky2=C_WHITE, hill=C_ORANGE, pa=C_PURPLE, pb=C_MAROON, wall="strata",
         sand_c=(C_YELLOW, C_ORANGE, C_WHITE, C_MAROON), spk=C_ORANGE,
         earth_c=(C_ORANGE, C_MAROON, C_YELLOW, C_RED), peb=C_MAROON, eg=C_GREEN, ecrack=C_BLACK,
         rock_c=(C_RED, C_MAROON, C_ORANGE), crack=C_YELLOW, rim=C_BLUE, frame=C_ORANGE,
         deco=("bone", "shell", "gem"), glint=C_YELLOW, shade=C_LBLUE, mote="firefly", mmove="twinkle",
         props=[("sun", 47, 0, "twirl"), ("cloud", 6, 0, "drift"), ("cactus", 20, 1, "still"), ("cactus", 36, 2, "still")]),
    dict(name="oasis", sand="tuft", sky=C_LBLUE, sky2=C_WHITE, hill=C_YELLOW, pa=C_BLUE, pb=C_PURPLE, wall="waves",
         sand_c=(C_YELLOW, C_ORANGE, C_WHITE, C_MAROON), spk=C_GREEN,
         earth_c=(C_GREEN, C_BLUE, C_YELLOW, C_BLUE), peb=C_YELLOW, eg=C_WHITE, ecrack=C_BLACK,
         rock_c=(C_BLUE, C_PURPLE, C_LBLUE), crack=C_YELLOW, rim=C_GREEN, frame=C_GREEN,
         deco=("fish", "bubble", "root"), glint=C_WHITE, shade=C_LBLUE, mote="bubble", mmove="rise",
         props=[("palm", 3, 0, "sway"), ("palm", 19, 0, "sway2"), ("cloud", 30, 1, "drift"), ("sun", 50, 0, "twirl")]),
    dict(name="ruins", sand="gravel", sky=C_ORANGE, sky2=C_YELLOW, hill=C_MAROON, pa=C_MAROON, pb=C_BLACK, wall="bricks",
         sand_c=(C_ORANGE, C_MAROON, C_YELLOW, C_RED), spk=C_WHITE,
         earth_c=(C_PURPLE, C_MAROON, C_MAG, C_BLACK), peb=C_YELLOW, eg=C_ORANGE, ecrack=C_YELLOW,
         rock_c=(C_YELLOW, C_ORANGE, C_WHITE), crack=C_BLACK, rim=C_LBLUE, frame=C_YELLOW,
         deco=("coin", "pot", "bone"), glint=C_YELLOW, shade=C_YELLOW, mote="dust", mmove="drift",
         props=[("sun", 38, 1, "twirl"), ("pillar", 7, 0, "still"), ("broken", 15, 2, "still"), ("bird", 24, 1, "fly")]),
    dict(name="moon", sand="glitter", sky=C_BLUE, sky2=C_PURPLE, hill=C_BLACK, pa=C_BLACK, pb=C_PURPLE, wall="craters",
         sand_c=(C_WHITE, C_LBLUE, C_YELLOW, C_BLUE), spk=C_BLUE,
         earth_c=(C_BLUE, C_PURPLE, C_LBLUE, C_BLACK), peb=C_LBLUE, eg=C_LBLUE, ecrack=C_WHITE,
         rock_c=(C_PURPLE, C_BLACK, C_LBLUE), crack=C_YELLOW, rim=C_PURPLE, frame=C_LBLUE,
         deco=("gem", "crystal", "bone"), glint=C_LBLUE, shade=C_BLUE, mote="sparkle", mmove="twinkle",
         props=[("moon", 46, 1, "still"), ("star", 6, 1, "blink0"), ("star", 18, 3, "blink1"), ("star", 34, 0, "blink2"),
                ("cactus", 24, 1, "still")]),
    dict(name="ember", sand="gravel", sky=C_MAG, sky2=C_ORANGE, hill=C_MAROON, pa=C_BLACK, pb=C_MAROON, wall="cracks",
         sand_c=(C_RED, C_MAROON, C_ORANGE, C_BLACK), spk=C_YELLOW,
         earth_c=(C_MAROON, C_BLACK, C_RED, C_BLACK), peb=C_ORANGE, eg=C_YELLOW, ecrack=C_BLACK,
         rock_c=(C_ORANGE, C_RED, C_YELLOW), crack=C_BLACK, rim=C_ORANGE, frame=C_RED,
         deco=("ember", "bone", "coin"), glint=C_ORANGE, shade=C_MAG, mote="ember", mmove="rise",
         props=[("sun", 24, 0, "twirl"), ("pyramid", 3, 1, "still"), ("pyramid", 42, 2, "still"), ("bird", 12, 0, "fly")]),
    dict(name="grove", sand="tuft", sky=C_GREEN, sky2=C_LBLUE, hill=C_GREEN, pa=C_BLACK, pb=C_GREEN, wall="roots",
         sand_c=(C_GREEN, C_BLUE, C_YELLOW, C_BLUE), spk=C_YELLOW,
         earth_c=(C_MAROON, C_BLACK, C_ORANGE, C_BLACK), peb=C_ORANGE, eg=C_GREEN, ecrack=C_ORANGE,
         rock_c=(C_PURPLE, C_MAROON, C_MAG), crack=C_YELLOW, rim=C_GREEN, frame=C_YELLOW,
         deco=("root", "gem", "shell"), glint=C_WHITE, shade=C_GREEN, mote="firefly", mmove="drift",
         props=[("palm", 8, 0, "sway"), ("flower", 22, 4, "bloom"), ("flower", 31, 5, "bloom2"), ("sun", 48, 0, "twirl"),
                ("moth", 40, 2, "fly")]),
    dict(name="dusk", sand="glitter", sky=C_PURPLE, sky2=C_MAG, hill=C_BLACK, pa=C_MAROON, pb=C_PURPLE, wall="dots",
         sand_c=(C_PURPLE, C_BLUE, C_MAG, C_BLUE), spk=C_PINK,
         earth_c=(C_BLUE, C_BLACK, C_LBLUE, C_BLACK), peb=C_LBLUE, eg=C_LBLUE, ecrack=C_BLACK,
         rock_c=(C_ORANGE, C_MAROON, C_YELLOW), crack=C_WHITE, rim=C_MAG, frame=C_MAG,
         deco=("gem", "crystal", "fish"), glint=C_PINK, shade=C_PURPLE, mote="sparkle", mmove="twinkle",
         props=[("moon", 8, 1, "still"), ("star", 24, 1, "blink1"), ("star", 40, 3, "blink0"), ("pillar", 50, 0, "still"),
                ("bird", 30, 2, "fly")]),
    dict(name="crystal", sand="glitter", sky=C_BLACK, sky2=C_BLUE, hill=C_BLUE, pa=C_BLACK, pb=C_BLUE, wall="facets",
         sand_c=(C_LBLUE, C_BLUE, C_WHITE, C_PURPLE), spk=C_WHITE,
         earth_c=(C_BLUE, C_PURPLE, C_LBLUE, C_BLACK), peb=C_LBLUE, eg=C_WHITE, ecrack=C_WHITE,
         rock_c=(C_MAG, C_PURPLE, C_PINK), crack=C_WHITE, rim=C_LBLUE, frame=C_LBLUE,
         deco=("crystal", "gem", "crystal"), glint=C_WHITE, shade=C_BLACK, mote="shine", mmove="twinkle",
         props=[("star", 5, 1, "blink0"), ("star", 15, 4, "blink2"), ("star", 27, 0, "blink1"), ("star", 44, 3, "blink0"),
                ("moon", 52, 0, "still"), ("comet", 34, 2, "fly")]),
]

# Pass 3 per-level extras, merged into THEMES: bands = sand colour ramps (base, dark, light, darkest) that alternate every
# three rows, horizon = the shape of the far hills in the sky strip, setp = big buried pictures behind the pockets,
# critter = the little inert creature that moves about in the hollows (and how), shower = what rains on a won level.
_EXTRA = [
    dict(bands=[(C_YELLOW, C_ORANGE, C_WHITE, C_MAROON), (C_ORANGE, C_RED, C_YELLOW, C_MAROON)], horizon="dunes",
         setp=("ribs", "ribs"), critter=("lizard", "walk"), shower="coin"),
    dict(bands=[(C_YELLOW, C_ORANGE, C_WHITE, C_MAROON), (C_ORANGE, C_RED, C_YELLOW, C_MAROON)], horizon="oasis",
         setp=("boat", "boat"), critter=("fish", "swim"), shower="leaf"),
    dict(bands=[(C_ORANGE, C_MAROON, C_YELLOW, C_RED), (C_RED, C_MAROON, C_ORANGE, C_BLACK)], horizon="ruins",
         setp=("arch", "arch"), critter=("bat", "flit"), shower="star"),
    dict(sand_c=(C_LBLUE, C_BLUE, C_WHITE, C_PURPLE), spk=C_WHITE,
         bands=[(C_LBLUE, C_BLUE, C_WHITE, C_PURPLE), (C_PINK, C_MAG, C_WHITE, C_PURPLE)], horizon="moon",
         setp=("rocket", "rocket"), critter=("alien", "hover"), shower="flake"),
    dict(bands=[(C_RED, C_MAROON, C_ORANGE, C_BLACK), (C_MAG, C_PURPLE, C_PINK, C_BLACK)], horizon="ember",
         setp=("skull", "skull"), critter=("spark", "rise"), shower="ember"),
    dict(bands=[(C_GREEN, C_BLUE, C_YELLOW, C_BLUE), (C_YELLOW, C_GREEN, C_WHITE, C_ORANGE)], horizon="grove",
         setp=("mushroom", "mushroom"), critter=("butterfly", "flit"), shower="petal"),
    dict(bands=[(C_PURPLE, C_BLUE, C_MAG, C_BLUE), (C_MAG, C_PURPLE, C_PINK, C_BLUE)], horizon="dusk",
         setp=("crystals", "crystals"), critter=("jelly", "hover"), shower="gem"),
    dict(bands=[(C_LBLUE, C_BLUE, C_WHITE, C_PURPLE), (C_GREEN, C_BLUE, C_LBLUE, C_BLACK)], horizon="crystal",
         setp=("crystals", "crystals"), critter=("shard", "flit"), shower="gem"),
]
for _th, _ex in zip(THEMES, _EXTRA):
    _th.update(_ex)
    _th.setdefault("bands", [_th["sand_c"]])
THEMES[3]["sand_c"] = (C_LBLUE, C_BLUE, C_WHITE, C_PURPLE)

# Big buried pictures (set pieces) and the little creatures; one character a pixel like every other picture here.
SETPIECES = {
    "ribs": ["..W.......W..", ".W.W.....W.W.", ".W..W...W..W.", "W...W...W...W", "W..W.....W..W", ".WW.......WW."],
    "boat": ["....W....", "....WW...", "...WWWW..", "OOOOOOOOO", ".OMOMOMO.", "..OOOOO.."],
    "arch": ["YYYYYYYYYY", "YOOOOOOOOY", "YO......OY", "YO......OY", "YO......OY", "YM......MY"],
    "rocket": ["...R...", "..WWW..", "..WLW..", "..WWW..", ".RWWWR.", ".R.R.R."],
    "skull": [".WWWWW.", "WWKWKWW", "WWWWWWW", ".WKKKW.", ".W.W.W."],
    "mushroom": ["..RRRR..", ".RWRRWR.", "RRRRRRRR", "..YYYY..", "..YYYY..", "..YYYY.."],
    "crystals": ["..L..L...", ".LWL.LL..", ".LLLLWL.L", "LLLLLLLLL", "LLLLLLLLL"],
}
CRITTERS = {
    "lizard": (["....GG.", "GGGGGGW", ".G..G.."], ["....GG.", "GGGGGGW", "G..G..."]),
    "fish": ([".OOO..O", "OOWOOOO", ".OOO..O"], [".OOO.O.", "OOWOOOO", ".OOO.O."]),
    "bat": (["P...P", "PPWPP", ".PPP."], [".P.P.", "PPWPP", "P...P"]),
    "alien": ([".GGG.", "GWGWG", "GGGGG", "G.G.G"], [".GGG.", "GWGWG", "GGGGG", ".G.G."]),
    "spark": ([".O.", "OYO", ".R."], ["O.O", ".Y.", "R.R"]),
    "butterfly": (["OO.OO", "OYYYO", "OO.OO"], [".O.O.", "OYYYO", ".O.O."]),
    "jelly": ([".NNN.", "NNWNN", ".N.N.", "N.N.N"], [".NNN.", "NNWNN", "N.N.N", ".N.N."]),
    "shard": (["..L..", ".LWL.", "..L.."], [".L.L.", "..W..", ".L.L."]),
}
SHOWERS = {
    "coin": ["YY", "YO"], "leaf": [".G", "GG"], "star": [".Y.", "YWY", ".Y."], "ember": ["O", "R"],
    "flake": [".W.", "WLW", ".W."], "petal": ["NN", ".A"], "gem": [".L.", "LWL", ".L."],
}


def burst_art(r, colour):
    """A firework ring of radius r (1-4): eight spokes and a bright core, in a 9x9 picture."""
    pic = np.full((9, 9), -1, dtype=np.int8)
    pic[4, 4] = C_WHITE
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        pic[4 + dy * r, 4 + dx * r] = colour if r < 4 else C_WHITE
        if r > 1 and (dx and dy):
            pic[4 + dy * (r - 1), 4 + dx * (r - 1)] = C_YELLOW
    return pic


GHOST = ["WWWWW", "WWWWW", "WKWKW", "WWWWW", "WWWWW", "W.W.W"]
# The run-over pictures after the two bursts: the helmet and shoulders sunk low, stars circling above him.
POOF_C = [_art(["W.....W", ".......", "...W...", "...K...", "..KYK..", ".KYYYK.", "KGGGGGK"]),
          _art([".......", "W.....W", "..W.W..", "...K...", "..KYK..", ".KYYYK.", "KGGGGGK"]),
          _art(["...Y...", ".W...W.", "..Y.Y..", "...K...", "..KYK..", ".KYYYK.", "KBBYBBK"])]


def tile_art(th, v, var, open_above, open_below, band=0):
    """One 7x7 ground tile in a theme's colour ramp. v is SAND, EARTH(1), ROCK(1, 2) or BED."""
    if v == SAND:
        sb, sd, sl, sx = th["bands"][band % len(th["bands"])]
        base = _art(SAND_STYLES[th["sand"]][var % 5], {"Y": sb, "O": sd, "W": sl, "S": th["spk"]})
        return _light(base, open_above, open_below, sl, sb, sd, sx)
    if v in (EARTH, EARTH1):
        eb, ed, el, ex = th["earth_c"]
        base = _art(EARTH_ROWS[var % 2], {"O": eb, "M": ed, "P": th["peb"], "G": th["eg"]})
        base = _light(base, open_above, open_below, el, eb, ed, ex)
        return _overlay(base, CRACK_A, th["ecrack"]) if v == EARTH1 else base
    if v in (ROCK, ROCK1, ROCK2):
        rf, rs, rh = th["rock_c"]
        base = _art(ROCK_ROWS[var % 2], {"R": rf, "M": rs, "H": rh})
        if v >= ROCK1:
            base = _overlay(base, CRACK_A, th["crack"])
        if v == ROCK2:
            base = _overlay(base, CRACK_B, th["crack"])
        return base
    return _art(BED_ROWS, {"B": th["rim"], "P": th["glint"]})


# --- things in the ground: hearts, stars, energy cells (two frames each so they twinkle) ----------------------------
HEART_A = [".......", ".KK.KK.", "KRWRRRK", "KRRRRRK", ".KRRRK.", "..KRK..", "...K..."]
HEART_B = [".......", ".KK.KK.", "KRRRRRK", "KRWRRRK", ".KRRRK.", "..KRK..", "...K..."]
STAR_A = ["...K...", "..KYK..", "KKYYYKK", ".KYWYK.", "..KYYK.", ".KYKYK.", ".K...K."]
STAR_B = ["...K...", "..KYK..", "KKYYYKK", ".KYYYK.", "..KWYK.", ".KYKYK.", ".K...K."]
ENERGY_A = ["..KKK..", ".KLLLK.", ".KBYBK.", ".KBYYK.", ".KBYBK.", ".KBBBK.", "..KKK.."]
ENERGY_B = ["..KKK..", ".KLWLK.", ".KBYBK.", ".KYYBK.", ".KBYBK.", ".KBBBK.", "..KKK.."]
ITEM_ROWS = {HEART: (HEART_A, HEART_B), STAR: (STAR_A, STAR_B), ENERGY: (ENERGY_A, ENERGY_B)}

# Creatures: three kinds, told apart by silhouette first and colour second. E eye (white), Q pupil (placed by
# _eyes so the eyes follow the hero), X body, S shade, N nose, T mouth, 1-3 the stripes (white while they last, black once
# punched out: the hit points, kept exactly as dz01 drew them), K outline.
# Crab (one stripe): claws up, splayed legs.  Mole (two): round ears, big pink nose, digging claws.  Worm (three):
# antennae, wavy sides, a body that narrows. Second frame of each: eyes shut for a blink.
CRE_ROWS = {
    1: (["XX...XX", "XKXXXKX", "KEQXQEK", "KSTTTSK", "KXXXXXK", "X11111X", "KK.K.KK"],
        ["XX...XX", "XKXXXKX", "KKKXKKK", "KSTTTSK", "KXXXXXK", "X11111X", "KK.K.KK"]),
    2: (["KX...XK", "KXXXXXK", "KEQXQEK", "KXNNNXK", "X11111X", "KSSSSSK", "X22222X"],
        ["KX...XK", "KXXXXXK", "KKKXKKK", "KXNNNXK", "X11111X", "KSSSSSK", "X22222X"]),
    3: (["XK...KX", "KEQXQEK", "X11111X", ".KTTTK.", "X22222X", ".KXXXK.", "X33333X"],
        ["XK...KX", "KKKXKKK", "X11111X", ".KTTTK.", "X22222X", ".KXXXK.", "X33333X"]),
}
CRE_BODY = {1: (C_ORANGE, C_RED), 2: (C_BLUE, C_LBLUE), 3: (C_YELLOW, C_ORANGE)}
PUPIL_COLS = {-1: (1, 4), 0: (2, 4), 1: (2, 5)}      # which two eye pixels hold the pupils: looking left, ahead, right


def _eyes(rows, look):
    """Move the pupils of a creature's template to where `look` (-1 left, 0 ahead, 1 right) points them: an eye is two
    pixels wide, so the black dot sits in the left, inner or right pixel of each."""
    rows = list(rows)
    for y, row in enumerate(rows):
        if "Q" in row:
            cells = list(row)
            for x in (1, 2, 4, 5):
                if cells[x] in "EQ":
                    cells[x] = "E"
            for x in PUPIL_COLS[look]:
                cells[x] = "Q"
            rows[y] = "".join(cells)
    return rows


def creature_art(v, out=0, red=False, blink=False, flat=False, look=0):
    """The picture of creature v with `out` stripes punched out (red body: the one that took the last heart)."""
    n = cre_stripes(v)
    drop = bool((v - CRE) & DROP)
    body, shade = CRE_BODY[n]
    cmap = {"X": C_RED if red else body, "S": C_MAROON if red else shade, "E": C_WHITE, "Q": C_RED if drop else C_BLACK,
            "T": C_BLACK, "N": C_PINK}
    for k in range(1, 4):
        cmap[str(k)] = C_BLACK if k <= out else C_WHITE
    rows = CRE_ROWS[n][1 if blink else 0]
    art = _art(rows if blink else _eyes(rows, look), cmap)
    if flat:
        art[:4] = -1                         # a flattened creature keeps only its lower rows
    return art


# --- the hero: a green digger in a yellow lamp helmet, blue overalls and orange boots -----------------------------
# Each mood is the three rows that change: eyes (two rows) and mouth. The helmet (r0-r1), body and boots stay.
HERO_TOP = [".KYWYK.", "KOYYYOK"]
HERO_FACE = {"open": ["KGWGWGK", "KGKGKGK", "KGGRGGK"], "blink": ["KGGGGGK", "KGKGKGK", "KGGRGGK"],
             "hurt": ["KGKGKGK", "KGGGGGK", "KGKKKGK"], "glad": ["KGWGWGK", "KGKGKGK", "KGRRRGK"],
             "dead": ["KGRGRGK", "KLGKGLK", "KGKKKGK"]}
HERO_BODY = ["KBBYBBK", ".KOKOK."]


def hero_art(mood="open", glow=False, side=0, cheer=False, punch=0):
    """The hero. mood picks the face; glow lights the outline yellow; side (-1/+1) puts a gloved hand on that wall;
    cheer throws both arms up; punch (-1/+1) throws a glove toward that side. Dead: a pale face, crossed eyes, tears,
    the lamp out."""
    rows = [list(r) for r in HERO_TOP + HERO_FACE[mood] + HERO_BODY]
    if side:
        rows[2][0 if side < 0 else 6], rows[3][0 if side < 0 else 6] = "W", "W"
    if punch:
        rows[5][0 if punch < 0 else 6] = "W"
    if cheer:
        rows[1][0], rows[1][6], rows[2][0], rows[2][6] = "W", "W", "W", "W"
    rows = ["".join(r) for r in rows]
    cmap = {"K": C_YELLOW if glow else (C_RED if mood == "hurt" else C_BLACK)}
    if mood == "dead":
        cmap.update({"G": C_WHITE, "Y": C_ORANGE, "W": C_BLACK, "O": C_MAROON, "B": C_PURPLE, "L": C_LBLUE})
    return _art(rows, cmap)


# A sad rain cloud that hangs over the run-over hero (two frames: the drops fall past the hero's shoulders)
SADCLOUD = (["...LLL...", ".LLLLLLL.", "LLLLLLLLL", ".BBBBBBB.", ".........", "L.......L", ".........", "L.......L"],
            ["...LLL...", ".LLLLLLL.", "LLLLLLLLL", ".BBBBBBB.", ".........", ".........", "L.......L", ".........",])

# The little lives that drift in the pockets (a theme picks one): three small pictures, two frames each
MOTES = {
    "firefly": ([".Y.", "YWY", ".Y."], ["...", ".Y.", "..."]),
    "bubble": ([".W.", "W.W", ".W."], [".W.", "WLW", ".W."]),
    "dust": (["YY.", ".YY"], [".YY", "YY."]),
    "sparkle": ([".W.", "WLW", ".W."], ["...", ".W.", "..."]),
    "ember": ([".Y", "OR"], ["O.", "RO"]),
    "shine": ([".W.", "WLW", ".W."], ["L.L", ".W.", "L.L"]),
}

POOF_A = _art([".R...R.", "..R.R..", "...R...", "..R.R..", ".R...R.", "R.....R", "..R.R.."])
POOF_B = _art([".W...W.", "..W.W..", "...W...", "..W.W..", ".W...W.", "W.....W", "..W.W.."])
PUFF_A = _art(["W.....W", "..W.W..", ".W...W.", "...W...", ".W...W.", "..W.W..", "W.....W"])
PUFF_B = _art([".......", "..W.W..", ".W.O.W.", "..O.O..", ".W.O.W.", "..W.W..", "......."])
CURSOR = _art(["WW...WW", "W.....W", ".......", ".......", ".......", "W.....W", "WW...WW"])
IMPACT = _art(["..W..", ".WYW.", "WYWYW", ".WYW.", "..W.."])
MARK = _art(["W.W", ".W.", "W.W"])
SPARK_DOT = _art(["Y"])
SPARK_BIG = _art([".W.", "WYW", ".W."])
CARRY = _art([".Y.", "YWY", ".Y."])
STARCHIP = ["..Y..", ".YWY.", "YYYYY", ".YYY.", ".Y.Y."]
HEARTCHIP = ["RW.RR", "RRRRR", ".RRR.", "..R.."]
GLINT_A = _art([".W.", "WYW", ".W."])
GLINT_B = _art(["...", ".Y.", "..."])
# Confetti for a won level: blocks, pluses and streamers in seven colours (21 pictures, cycled over 32 sprites)
_CONF_COLOURS = (C_RED, C_YELLOW, C_BLUE, C_GREEN, C_ORANGE, C_PURPLE, C_LBLUE)
CONFETTI = ([_recolour2(["XXX", "XXX"], c) for c in _CONF_COLOURS] + [_recolour2([".X.", "XXX", ".X."], c) for c in _CONF_COLOURS]
            + [_recolour2(["XX", "X.", "X.", "XX"], c) for c in _CONF_COLOURS])

# Where the eight sparks of a lit star sit around the hero's cell, in the order they go out
SPARKS = [(-1, -1), (3, -2), (7, -1), (8, 3), (7, 7), (3, 8), (-1, 7), (-2, 3)]

# --- scenery in the strip of sky above the ground (each picture has two frames where it moves) ------------------------
SCENERY = {
    "sun": (["...O...", "..YYY..", ".YYWYY.", "OYYYYYO", ".YYYYY.", "..YYY..", "...O..."],
            ["O..O..O", ".YYYYY.", ".YYWYY.", "..YYY..", ".YYYYY.", ".YYYYY.", "O..O..O"]),
    "cloud": (["..WWW......", ".WWWWWW.WW.", "WWWWWWWWWWW", ".SSSSSSSSS."],) * 2,
    "cactus": (["..Y..", "..G..", "G.G..", "GGG.G", "..GGG", "..G.."],) * 2,
    "palm": ([".GGGGG.", "GG.G.GG", "G..O..G", "...O...", "...O...", "...O...", "..OOO.."],
             ["..GGG..", ".GGGGG.", "G..O..G", "...O...", "...O...", "...O...", "..OOO.."]),
    "pillar": (["YYY", "OYO", "OYO", "OYO", "OYO", "OYO", "YYY"],) * 2,
    "broken": (["Y.Y", "OYO", "OYO", "OYO", "YYY"],) * 2,
    "moon": ([".WW..", "WW...", "WW...", "WW...", ".WW.."],) * 2,
    "star": (["Y"], ["W"]),
    "pyramid": (["....Y....", "...YYO...", "..YYYOO..", ".YYYYYOO.", "YYYYYYYOO", "OOOOOOOOO"],) * 2,
    "bird": (["W.W", ".W."], ["...", "WWW"]),
    "moth": (["W.W", ".Y."], ["...", "WYW"]),
    "flower": (["Y", "G"], ["W", "G"]),
    "comet": (["W..", "YW.", ".YW"], ["W..", "YW.", ".YW"]),
}


def scenery_art(kind, frame, th):
    return _art(SCENERY[kind][frame % 2], {"S": th["shade"]})


# --- the shaft backdrop: the dark inside of the ground, the sky strip on top, small finds buried in it ---------------
DECO = {
    "bone": ["W...W", ".WWW.", "W...W"],
    "shell": [".YO.", "YOYO", "OYOY", ".OY."],
    "gem": [".G.", "GWG", ".G."],
    "fish": ["..WW...", "WWWWWWW", "WWKWWWW", "..WW..W"],
    "bubble": [".W.", "W.W", ".W."],
    "root": ["G..", "GG.", ".G.", ".GG", "..G"],
    "coin": [".Y.", "YOY", ".Y."],
    "pot": [".OOO.", "OMMMO", "OMMMO", ".OOO."],
    "crystal": ["..L..", ".LWL.", ".LLL.", "LLLLL", "LLLLL"],
    "ember": ["..O..", ".ORO.", "ORRRO", ".ORO."],
}


def _wall_on(kind, x, y, seed):
    """Is pixel (x, y) of a pocket's wall drawn in the theme's second colour? One rule per wall pattern, so each
    level's hollows look like their own place: strata, ripples, old bricks, craters, cracks, roots, facets or stars."""
    n = _hash(x, y, seed)
    if kind == "strata":                    # wavy layers of rock
        return (y + int(1.8 * math.sin(x / 5.0 + y // 7))) % 7 == 3 and n % 5 != 0
    if kind == "waves":                     # the slow ripple of a flooded cave
        return (y + int(2 * math.sin(x / 3.0 + y // 7))) % 6 == 0 and n % 6 != 0
    if kind == "bricks":                    # a tomb wall: rows of bricks, every other row shifted
        return y % 4 == 3 or (x + (4 if (y // 4) % 2 else 0)) % 9 == 0
    if kind == "craters":                   # a ring round a hash-chosen centre in each 14-pixel block
        bx, by = x // 14, y // 14
        hh = _hash(bx, by, seed)
        r2 = (x - (bx * 14 + 3 + hh % 8)) ** 2 + (y - (by * 14 + 3 + (hh >> 4) % 8)) ** 2
        return (4 <= r2 <= 9 and (hh >> 9) % 3 == 0) or n % 41 == 0
    if kind == "cracks":                    # hot seams
        return ((x + 2 * y) % 17 == 0 and n % 3 != 0) or ((x - 3 * y) % 23 == 0 and n % 3 == 0)
    if kind == "roots":                     # hanging roots
        return (x + int(2.5 * math.sin(y / 4.0 + x // 9))) % 8 == 0 and n % 4 != 0
    if kind == "facets":                    # crystal planes
        return ((x + y) % 11 == 0 or (x - y) % 13 == 0) and n % 5 != 0
    return n % 19 == 0                      # dots: a scatter of small stars


def _horizon(kind, x, seed):
    """Height (1-4 pixels, from the bottom of the sky strip) of the far skyline at column x, one shape per level."""
    n = _hash(x // 3, seed, 4)
    if kind == "dunes":
        return 2 + (1 if math.sin(x / 6.0 + seed) > 0 else 0)
    if kind == "oasis":
        return 2 + (n % 5 == 0)
    if kind == "ruins":
        return 1 + _hash(x // 5, seed, 8) % 4
    if kind == "moon":
        return 2 + n % 3 // 2 + (1 if x % 13 < 3 else 0)
    if kind == "ember":
        return max(1, 4 - abs(x % 22 - 11) // 2)
    if kind == "grove":
        return 2 + n % 3
    if kind == "dusk":
        return 4 if (x // 2) % 7 == 3 else 2
    return max(1, 4 - abs(x % 8 - 4))       # crystal: a row of spikes


def backdrop_art(th, h, seed):
    """The whole shaft's backdrop, one picture 56 wide and one row (7 pixels) per level row plus the finish row."""
    hp = (h + 1) * CELL
    pic = np.full((hp, W * CELL), th["pa"], dtype=np.int8)
    for y in range(hp):                     # the theme's wall pattern, so a pocket reads as a place, not a flat hole
        for x in range(W * CELL):
            if _wall_on(th["wall"], x, y, seed):
                pic[y, x] = th["pb"]
    for rr in range(1, h):                  # small buried finds, shown only where a pocket opens
        n = _hash(rr, 5, seed)
        kind = th["deco"][n % len(th["deco"])]
        art = _art(DECO[kind])
        x = (n >> 5) % (W * CELL - art.shape[1] - 2) + 1
        y = rr * CELL + (n >> 11) % (CELL - art.shape[0] + 1)
        sub = pic[y:y + art.shape[0], x:x + art.shape[1]]
        pic[y:y + art.shape[0], x:x + art.shape[1]] = np.where(art >= 0, art, sub)
    for rr in range(2, h - 1, 4):           # big buried set pieces: one every few rows, never at the finish
        n = _hash(rr, 17, seed)
        art = _art(SETPIECES[th["setp"][n % 2]])
        x = n % (W * CELL - art.shape[1] - 4) + 2
        y = rr * CELL + (n >> 8) % 3
        sub = pic[y:y + art.shape[0], x:x + art.shape[1]]
        pic[y:y + art.shape[0], x:x + art.shape[1]] = np.where(art >= 0, art, sub)
    for x in range(W * CELL):               # the sky strip: sky, a lighter band, two layers of hills shaped per level
        pic[0:CELL, x] = th["sky"]
        for y in (2, 3, 4):
            if (x + y) % 2 == 0 and y >= 3 - (x % 3 == 0):
                pic[y, x] = th["sky2"]
        far = _horizon(th["horizon"], x, seed)
        near = 1 + (1 if math.sin(x / 3.1 + seed) > 0.3 else 0)
        pic[CELL - far:CELL, x] = th["pb"] if th["pb"] != th["sky"] else th["sky2"]
        pic[CELL - near:CELL, x] = th["hill"]
    return pic


def finish_tile(col, flash):
    """The checkered floor: two-pixel squares, continuous across the row (flash swaps the colours)."""
    pic = np.zeros((CELL, CELL), dtype=np.int8)
    for y in range(CELL):
        for x in range(CELL):
            on = ((col * CELL + x) // 2 + y // 2) % 2 == 0
            pic[y, x] = (C_WHITE if flash else C_YELLOW) if on else (C_GREEN if flash else C_BLACK)
    pic[0, :] = np.where(pic[0, :] == C_BLACK, C_MAROON, pic[0, :])
    return pic


def curtain_art(th, k):
    """The wipe that closes a won level: the theme's sky colours coming down in stripes, k quarters of the way, with a
    scalloped white hem."""
    pic = np.full((VIEW * CELL, PANEL_X), -1, dtype=np.int8)
    rows = 16 * k
    full = rows >= VIEW * CELL
    for x in range(PANEL_X):
        hem = VIEW * CELL - 1 if full else rows - 1 - 3 * ((x // 4) % 2)      # alternate 4-pixel scallops, 3 pixels apart
        pic[:hem + 1, x] = th["sky"] if (x // 4) % 2 == 0 else th["sky2"]
        if not full:
            pic[hem, x] = C_WHITE
    return pic


def dim_art():
    """The 'run over' frame: a thick maroon border closing in on the shaft (the shaft itself is recoloured, not covered)."""
    pic = np.full((VIEW * CELL, PANEL_X), -1, dtype=np.int8)
    pic[:4, :] = C_MAROON
    pic[-4:, :] = C_MAROON
    pic[:, :3] = C_MAROON
    pic[:, -3:] = C_MAROON
    pic[4, 3:-3] = C_RED
    pic[-5, 3:-3] = C_RED
    return pic


def panel_art(th):
    """The side panel's backing: black with a frame in the level's colour and rivets."""
    pic = np.full((64, 8), C_BLACK, dtype=np.int8)
    pic[:, 0] = th["frame"]
    pic[0, :] = th["frame"]
    for y in range(4, 64, 8):
        pic[y, 7] = th["frame"]
    return pic


def bar_art(left, flash, span):
    """The click bar: a maroon (or flashing red) tube that drains from the top, yellow charge with a bright crest."""
    pic = np.full((span, 4), C_RED if flash else C_MAROON, dtype=np.int8)
    if left:
        pic[span - left:, :] = C_YELLOW
        pic[span - left, :] = C_WHITE
        pic[span - left + 1:, 0] = C_ORANGE
    for y in range(2, span, 5):             # tube joints: dark on the empty part, orange on the charge
        pic[y, 3] = C_BLACK if y < span - left else C_ORANGE
    return pic


def _chip(rows, colour):
    return _art(rows, {"R": colour, "Y": colour})


# ---------------------------------------------------------------------------
# The scene: every thing on screen is a named sprite. Cells of the shaft are two pools (ground, items) the size of
# the screen, whose pictures follow the camera's rows; the hero, the poof, the cursor, the sparks and so on are
# single sprites that move whole. show() is the only function that touches them, and it only reads (state, fx).
# ---------------------------------------------------------------------------
L_SHAFT, L_SCENE, L_GROUND, L_ITEM, L_VEIL, L_HERO, L_FX, L_CURTAIN, L_CONFETTI, L_PANEL, L_HUD = range(11)
BAR_Y0, BAR_Y1 = 19, 56
BAR_SPAN = BAR_Y1 - BAR_Y0 + 1
SOLID = (SAND, EARTH, EARTH1, ROCK, ROCK1, ROCK2, BED)
NAME_OF = {SAND: "sand", EARTH: "earth", EARTH1: "earth", ROCK: "rock", ROCK1: "rock", ROCK2: "rock", BED: "bedrock"}
CRE_NAMES = {1: "crab", 2: "mole", 3: "worm"}


def _open(st, row, col):
    """Is this cell open air (what the lit crest of the ground above, or the shaded lip below, is judged on)?"""
    if row < 0:
        return True
    if col < 0 or col >= W or row >= st.h:
        return False
    v = st.g[row * W + col]
    return v in PASS or v >= CRE


class Scene:
    def __init__(self, level, theme_index, h):
        self.level, self.h = level, h
        self.th = THEMES[theme_index % len(THEMES)]
        self.seed = theme_index + 3
        self.shown = {}                    # id(sprite) -> the key last drawn on it, so a sprite is redrawn only on change
        self.pic_cache = {}
        th = self.th
        self.dim = False
        self.backdrop_pic = backdrop_art(th, h, self.seed)
        self.backdrop = self._add(self.backdrop_pic, "shaft", 0, 0, L_SHAFT, ["backdrop"])
        self.props = []
        for k, (kind, x, y, motion) in enumerate(th["props"]):
            sp = self._add(scenery_art(kind, 0, th), kind, x, y, L_SCENE, ["scenery", motion])
            self.props.append((sp, kind, x, y, motion, k))
        self.motes = []                    # the pocket's little lives: they live under the ground, so show only in hollows
        for i in range(12):
            n = _hash(i, 9, self.seed)
            wy = CELL * (1 + n % max(1, h - 1)) + (n >> 9) % 5
            self.motes.append((self._add(self._mote(0), th["mote"], 0, 0, L_SCENE, ["mote"]), (n >> 4) % (PANEL_X - 4) + 1, wy))
        ck, self.cmove = th["critter"]      # the little inert creatures: they live under the ground like the motes
        self.critter_kind = ck
        self.critters = []
        for i in range(6):
            n = _hash(i, 21, self.seed)
            wy = CELL * (2 + n % max(1, h - 2)) + (n >> 9) % 4
            self.critters.append((self._add(self._critter(0), ck, 0, 0, L_SCENE, ["critter"]), (n >> 4) % PANEL_X, wy))
        self.tiles = [[self._add(tile_art(th, SAND, 0, False, False), "ground", c * CELL, vr * CELL, L_GROUND, ["ground"])
                       for c in range(W)] for vr in range(VIEW)]
        self.items = [[self._add(HEART_A_ART, "item", c * CELL, vr * CELL, L_ITEM, ["item"], False)
                       for c in range(W)] for vr in range(VIEW)]
        self.hero = self._add(hero_art(), "hero", 0, 0, L_HERO, ["hero"])
        self.cloud = self._add(_art(SADCLOUD[0]), "sad-cloud", 0, 0, L_FX, ["fx"], False)
        self.poof = self._add(POOF_A, "poof", 0, 0, L_FX, ["fx"], False)
        self.carry = self._add(CARRY, "carried-star", 0, 0, L_FX, ["fx"], False)
        self.sparks = [self._add(SPARK_DOT, "spark", 0, 0, L_FX, ["fx"], False) for _ in range(8)]
        self.cursor = self._add(CURSOR, "cursor", 0, 0, L_FX, ["fx"], False)
        self.impact = self._add(IMPACT, "impact", 0, 0, L_FX, ["fx"], False)
        self.mark = self._add(MARK, "mark", 0, 0, L_FX, ["fx"], False)
        self.point = self._add(MARK, "point", 0, 0, L_FX, ["fx"], False)
        self.puffs = [self._add(PUFF_A, "puff", 0, 0, L_FX, ["fx"], False) for _ in range(VIEW + 1)]
        self.veil = self._add(dim_art(), "run-over-veil", 0, 0, L_VEIL, ["fx"], False)
        self.curtain = self._add(curtain_art(th, 1), "curtain", 0, 0, L_CURTAIN, ["fx"], False)
        # a themed shower (coins, leaves, flakes...) falls among the confetti, and three fireworks open over the shaft
        rain = _art(SHOWERS[th["shower"]])
        self.confetti = [self._add(rain if i % 2 else CONFETTI[i % len(CONFETTI)], "confetti", 0, 0, L_CONFETTI, ["fx"], False)
                         for i in range(32)]
        self.fireworks = [self._add(burst_art(1, C_YELLOW), "firework", 0, 0, L_CONFETTI, ["fx"], False) for _ in range(3)]
        self.ghost = self._add(_art(GHOST), "ghost", 0, 0, L_FX, ["fx"], False)
        # the panel
        self._add(panel_art(th), "panel", PANEL_X, 0, L_PANEL, ["hud"])
        self.hearts = [self._add(_chip(HEARTCHIP, C_RED), "heart-slot", 58, 2 + 4 * k, L_HUD, ["hud"]) for k in range(MAX_HEARTS)]
        self.slot = self._add(_chip(STARCHIP, C_MAROON), "star-slot", 58, 14, L_HUD, ["hud"])
        self.bar = self._add(bar_art(0, False, BAR_SPAN), "click-bar", 58, BAR_Y0, L_HUD, ["hud"])
        self.dot = self._add(_art([".YYYY.", "GWGGWG", ".GGGG."]), "depth-dot", 57, BAR_Y0, L_HUD + 1, ["hud"])
        self._add(_art(["YKYKYKY", "KYKYKYK", "YKYKYKY", "KYKYKYK", "YKYKYKY", "KYKYKYK"]), "finish-mark", 57, 58, L_HUD, ["hud"])
        self._add(np.full((1, PANEL_X), th["frame"], dtype=np.int8), "ground-edge", 0, 63, L_HUD, ["hud"])

    def _mote(self, frame):
        """A mote's picture in this theme's colours (the L of a sparkle is the theme's glint colour)."""
        return _art(MOTES[self.th["mote"]][frame], {"L": self.th["glint"]})

    def _critter(self, frame):
        return _art(CRITTERS[self.critter_kind][frame])

    def _add(self, pic, name, x, y, layer, tags, visible=True):
        sp = Sprite(np.array(pic, dtype=np.int8), name=name, x=x, y=y, layer=layer,
                    blocking=BlockingMode.NOT_BLOCKED, tags=list(tags))
        if not visible:
            sp.set_visible(False)
        self.level.add_sprite(sp)
        self.shown[(id(sp), "v")] = visible
        return sp

    # -- small helpers: draw a sprite only when what it shows changed -----------------------------------------------
    def _look(self, sp, key, make, dim=False):
        """Draw `make()` on sp when `key` changed. With dim, a run that is over shows the picture through DIM_LUT: the
        whole world sinks to a darker, redder version of itself (the hero and panel are not dimmed)."""
        dim = dim and self.dim
        if self.shown.get(id(sp)) != ("pic", key, dim):
            pic = make()
            sp.pixels = DIM_LUT[pic] if dim else pic
            self.shown[id(sp)] = ("pic", key, dim)

    def _name(self, sp, name):
        if self.shown.get((id(sp), "n")) != name:
            sp.set_name(name)
            self.shown[(id(sp), "n")] = name

    def _vis(self, sp, on):
        if self.shown.get((id(sp), "v")) != on:
            sp.set_visible(bool(on))
            self.shown[(id(sp), "v")] = on

    def _cached(self, key, make):
        if key not in self.pic_cache:
            self.pic_cache[key] = make()
        return self.pic_cache[key]

    # -- one frame ----------------------------------------------------------------------------------------------------
    def show(self, st, fx, broken, tick, budget):
        th, h = self.th, st.h
        top = cam_top(st.r, h)
        win = bool(fx.get("finish") or fx.get("sink") or fx.get("fade"))
        flash = fx.get("finish", 0) % 2 == 1
        poof = fx.get("poof", 0)
        self.dim = bool(broken or poof >= 3)
        self._look(self.backdrop, 0, lambda: self.backdrop_pic, True)
        self.backdrop.set_position(0, -top * CELL)
        self._scenery(top, tick)
        for vr in range(VIEW):
            row = top + vr
            for col in range(W):
                self._cell(st, fx, row, col, vr, tick, flash)
        self._hero(st, fx, top, tick, broken, win, poof)
        self._effects(st, fx, top, tick, win)
        self._panel(st, fx, budget)
        self._vis(self.veil, broken or poof >= 3)
        k = fx.get("fade", 0)
        self._vis(self.curtain, bool(k))
        if k:
            self._look(self.curtain, k, lambda: self._cached(("curtain", k), lambda: curtain_art(th, k)))

    def _scenery(self, top, tick):
        th, sky = self.th, top == 0
        for sp, kind, x, y, motion, k in self.props:
            self._vis(sp, sky)
            if not sky:
                continue
            frame, px, py = 0, x, y
            if motion == "twirl":
                frame = (tick // 4) % 2
            elif motion.startswith("sway"):
                frame = (tick // 5 + (motion == "sway2")) % 2
            elif motion == "drift":
                px = (x + tick // 3) % (PANEL_X + 11) - 11
            elif motion == "fly":
                frame = (tick // 2) % 2
                px = (x + tick) % (PANEL_X + 6) - 6
                py = y + (tick // 4) % 2
            elif motion.startswith("blink"):
                frame = (tick // 3 + int(motion[-1])) % 2
            elif motion.startswith("bloom"):
                frame = (tick // 6 + (motion == "bloom2")) % 2
            self._look(sp, (kind, frame), lambda: self._cached(("sc", kind, frame, th["name"]), lambda: scenery_art(kind, frame, th)), True)
            sp.set_position(px, py)
        mv = th["mmove"]
        for i, (sp, gx, wy) in enumerate(self.motes):
            x, y = gx, wy - top * CELL
            if mv == "rise":                # bubbles and embers climb, then start again low
                y -= (tick // 2 + 5 * i) % 12
            elif mv == "drift":             # dust and fireflies wander in small loops
                x += int(2.5 * math.sin(tick / 7 + i))
                y += int(1.5 * math.cos(tick / 9 + i))
            on = 0 <= y < VIEW * CELL - 3 and (mv != "twinkle" or (tick // 2 + i) % 4 != 0)
            self._vis(sp, on)
            if on:
                frame = (tick // 2 + i) % 2
                self._look(sp, frame, lambda: self._cached(("m", th["name"], frame), lambda: self._mote(frame)), True)
                sp.set_position(x, y)
        mv = self.cmove
        for i, (sp, gx, wy) in enumerate(self.critters):
            x, y = gx, wy - top * CELL
            if mv in ("walk", "swim"):      # crawl or swim along, wrapping round the shaft; fish also bob
                x = (gx + (1 if i % 2 else -1) * tick // 2) % (PANEL_X + 10) - 5
                if mv == "swim":
                    y += int(2 * math.sin(tick / 4 + i))
            elif mv == "flit":              # loops about a spot
                x += int(5 * math.sin(tick / 6 + i))
                y += int(3 * math.cos(tick / 5 + i))
            elif mv == "hover":             # bobs and sways
                x += int(2 * math.sin(tick / 11 + i))
                y += int(2 * math.sin(tick / 5 + i))
            else:                           # rise: climbs and starts again low
                x += int(2 * math.sin(tick / 4 + i))
                y -= (tick // 2 + 7 * i) % 18
            on = 0 <= y < VIEW * CELL - 4 and -4 < x < PANEL_X
            self._vis(sp, on)
            if on:
                frame = (tick // 2 + i) % 2
                self._look(sp, frame, lambda: self._cached(("k", th["name"], frame), lambda: self._critter(frame)), True)
                sp.set_position(x, y)

    def _cell(self, st, fx, row, col, vr, tick, flash):
        tile, item = self.tiles[vr][col], self.items[vr][col]
        h, th = st.h, self.th
        if row == h:
            self._vis(tile, True)
            self._look(tile, ("fin", col, flash), lambda: finish_tile(col, flash), True)
            self._vis(item, False)
            return
        if row > h:
            self._vis(tile, False)
            self._vis(item, False)
            return
        v = st.g[row * W + col]
        if v in SOLID:
            oa, ob = _open(st, row - 1, col), _open(st, row + 1, col)
            var = (row * 3 + col * 2 + row // 2) % 5
            self._vis(tile, True)
            band = (row // 3) % len(th["bands"])
            self._look(tile, (v, var, oa, ob, band), lambda: self._cached(("t", th["name"], v, var, oa, ob, band),
                                                                      lambda: tile_art(th, v, var, oa, ob, band)), True)
            self._name(tile, NAME_OF[v])
            self._vis(item, False)
            return
        self._vis(tile, False)
        if v in ITEMS:
            frame = (tick // 3 + row + col) % 2
            self._vis(item, True)
            self._look(item, (v, frame), lambda: self._cached(("i", v, frame), lambda: _art(ITEM_ROWS[v][frame])), True)
            item.set_position(col * CELL, vr * CELL)
            self._name(item, ("heart", "star", "energy-cell")[ITEMS.index(v)])
        elif is_cre(v):
            out, red, dx, dy, flat = 0, False, 0, 0, False
            here = (row, col)
            for key in ("punch", "hit_back", "crumple", "show"):
                if fx.get(key) == here:
                    out = fx.get("stripes_out", 0)
            if fx.get("red") == here:
                red = True
            if fx.get("hit_back") == here:
                dy, dx = _toward(st, row, col)       # the creature lunges at the hero
            if fx.get("crumple") == here or (fx.get("flat") and fx.get("punch") == here):
                flat = True
            blink = (tick // 2 + 5 * row + 3 * col) % 9 == 0
            look = (st.c > col) - (st.c < col)         # the eyes follow the hero
            self._vis(item, True)
            self._look(item, (v, out, red, flat, blink, look),
                       lambda: self._cached(("c", v, out, red, flat, blink, look),
                                            lambda: creature_art(v, out, red, blink, flat, look)), True)
            item.set_position(col * CELL + dx, vr * CELL + dy)
            self._name(item, CRE_NAMES[cre_stripes(v)])
        else:
            self._vis(item, False)

    def _hero(self, st, fx, top, tick, broken, win, poof):
        hx, hy = st.c * CELL, (st.r - top) * CELL
        if fx.get("lean"):
            dr, dc = fx["lean"]
            hx, hy = hx + dc, hy + dr
        sign = 0
        if fx.get("punch") and not poof:
            pr, pc = fx["punch"]
            hx, hy = hx + 2 * (pc - st.c), hy + 2 * (pr - st.r)
            sign = (pc > st.c) - (pc < st.c)
        if fx.get("sink"):
            hy += fx["sink"]
        elif win:
            hy -= (tick // 2) % 2                      # a little hop of joy
        self._vis(self.hero, not poof)
        self._vis(self.poof, bool(poof))
        if poof:
            self._look(self.poof, poof, lambda: (POOF_A, POOF_B)[poof - 1] if poof < 3 else POOF_C[poof - 3])
            self.poof.set_position(hx, hy)
        else:
            if broken:
                mood = "dead"
            elif fx.get("hurt"):
                mood = "hurt"
            elif win:
                mood = "glad"
            else:
                mood = "blink" if (tick // 2) % 11 == 0 else "open"
            side = 0
            if st.perched:
                side = -1 if st.at(st.r + 1, st.c - 1) in CLIMB else 1
            glow = st.lit > 0
            key = (mood, glow, side, win, sign)
            self._look(self.hero, key, lambda: self._cached(("h",) + key, lambda: hero_art(mood, glow, side, win, sign)))
            self.hero.set_position(hx, hy)
        ghost = poof >= 4                              # a little ghost slips out of the heap and rises
        self._vis(self.ghost, ghost)
        if ghost:
            self.ghost.set_position(hx + 1, hy - 3 * (poof - 3) - 2)
        # run over: a sad rain cloud hangs over his head when there is room above him
        rain = broken and not poof and hy >= 4
        self._vis(self.cloud, rain)
        if rain:
            fr = (tick // 3) % 2
            self._look(self.cloud, fr, lambda: _art(SADCLOUD[fr]))
            self.cloud.set_position(hx - 1, hy - 4)
        # a carried star: a small twinkle over his head
        carrying = st.star and not st.lit and not poof and not broken
        self._vis(self.carry, carrying)
        if carrying:
            self._look(self.carry, (tick // 2) % 2, lambda: CARRY if (tick // 2) % 2 == 0 else _recolour(CARRY, C_WHITE))
            self.carry.set_position(hx + 2, hy - 2)
        # a lit star: a ring of sparks that goes out one per move
        light = fx.get("light", 0)
        for k, sp in enumerate(self.sparks):
            on = (st.lit > k or win) and not poof and not broken
            self._vis(sp, on)
            if on:
                sx, sy = SPARKS[(k + (tick // 2 if win else 0)) % 8]
                if light:
                    sx, sy = sx + (sx > 3) * light - (sx < 3) * light, sy + (sy > 3) * light - (sy < 3) * light
                big = bool(light) or win or (tick + k) % 3 == 0
                self._look(sp, (big, light), lambda: SPARK_BIG if big else _recolour(SPARK_DOT, C_YELLOW))
                sp.set_position(hx + sx - (1 if big else 0), hy + sy - (1 if big else 0))

    def _effects(self, st, fx, top, tick, win):
        poof = fx.get("poof", 0)
        cur = fx.get("cursor")
        self._vis(self.cursor, bool(cur))
        if cur:
            self.cursor.set_position(cur[1] * CELL, (cur[0] - top) * CELL)
        pf = fx.get("puff", ())
        for i, sp in enumerate(self.puffs):
            on = i < len(pf)
            self._vis(sp, on)
            if on:
                self._look(sp, (tick // 2) % 2, lambda: PUFF_A if (tick // 2) % 2 == 0 else PUFF_B)
                sp.set_position(pf[i][1] * CELL, (pf[i][0] - top) * CELL)
        mk = fx.get("mark")
        on = bool(mk) and 0 <= mk[1] < W and top <= mk[0] < top + VIEW
        self._vis(self.mark, on)
        if on:
            self.mark.set_position(mk[1] * CELL + 2, (mk[0] - top) * CELL + 2)
        pt = fx.get("point")
        self._vis(self.point, bool(pt))
        if pt:
            self.point.set_position(pt[0] - 1, pt[1] - 1)
        sp_ = fx.get("spark")
        self._vis(self.impact, bool(sp_) and not poof)
        if sp_ and not poof:
            pr, pc = sp_
            self.impact.set_position((st.c + pc) * CELL // 2 + 1, (st.r + pr - 2 * top) * CELL // 2 + 1)
        # the win: confetti raining down the shaft over the flashing floor and the closing curtain
        stage = 0
        if fx.get("finish"):
            stage = fx["finish"]
        elif fx.get("sink"):
            stage = 4 + fx["sink"] // 2
        elif fx.get("fade"):
            stage = 7 + fx["fade"]
        for k, sp in enumerate(self.fireworks):
            r = (stage + 2 * k) % 7
            on = win and 1 <= r <= 4
            self._vis(sp, on)
            if on:
                col = (self.th["glint"], C_YELLOW, self.th["frame"])[k]
                self._look(sp, (r, col), lambda: self._cached(("fw", r, col), lambda: burst_art(r, col)))
                sp.set_position(2 + 20 * k + 5 * (k % 2), 1 + 6 * (k % 2))
        for i, sp in enumerate(self.confetti):
            self._vis(sp, win)
            if win:
                wob = int(2 * math.sin(stage * 1.3 + i))
                sp.set_position(max(0, min(PANEL_X - 3, (i * 37 + 11 + stage * 3) % (PANEL_X - 3) + 1 + wob)),
                                (stage * 10 + i * 9) % 70 - 6)

    def _panel(self, st, fx, budget):
        for k, sp in enumerate(self.hearts):
            full = k < st.hearts
            self._look(sp, full, lambda: _chip(HEARTCHIP if full else [r.replace("W", "R") for r in HEARTCHIP], C_RED if full else C_MAROON))
        slot = "flash" if fx.get("slot_flash") else ("lit" if st.lit else ("carry" if st.star else "empty"))
        colour = {"flash": C_WHITE, "lit": C_WHITE, "carry": C_YELLOW, "empty": C_PURPLE}[slot]
        self._look(self.slot, slot, lambda: _chip(STARCHIP if slot != "empty" else [r.replace("W", "Y") for r in STARCHIP], colour))
        left = 0 if not budget else int(round(BAR_SPAN * min(budget, max(0, st.clicks)) / budget))
        bad = bool(fx.get("bar_flash"))
        self._look(self.bar, (left, bad), lambda: bar_art(left, bad, BAR_SPAN))
        # the hero's dot moves down the bar as he descends
        dot = BAR_Y0 + int(round((BAR_SPAN - 2) * min(st.r, st.h - 1) / max(1, st.h - 1)))
        self.dot.set_position(57, dot)


# What a run that is over does to the world's colours: everything sinks one step toward red and dark (index 16 keeps
# the see-through -1, which numpy reads as the last element).
DIM_LUT = np.array([C_YELLOW, 1, 2, 3, 4, C_BLACK, C_PURPLE, C_MAG, C_MAROON, C_PURPLE, C_BLUE, C_ORANGE, C_RED, C_BLACK,
                    C_BLUE, C_MAROON, -1], dtype=np.int8)


def _recolour(pic, colour):
    """A picture with every drawn pixel set to one colour."""
    return np.where(pic >= 0, colour, pic).astype(np.int8)


def _toward(st, r, c):
    """(dy, dx) of a two-pixel lunge from a creature at (r, c) toward the hero."""
    return (2 * (st.r > r) - 2 * (st.r < r), 2 * (st.c > c) - 2 * (st.c < c))


HEART_A_ART = _art(HEART_A)


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------

class Dz02(ARCBaseGame):
    def __init__(self):
        self.st = None
        self.budget = 0
        self.v = None                  # the frame being shown: (DigState, fx) or None for the resting picture
        self._script = []
        self._end = None
        self._busy = False
        self.broken = False            # the run is over: the veil is down and the hero is slumped
        self.tick = 0                  # advances once per frame shown; drives the gentle idle motion
        self.scene = None
        levels = [Level(sprites=[], grid_size=(64, 64), data=ldef, name=ldef["name"]) for ldef in LEVELS]
        super().__init__(game_id="dz02", levels=levels,
                         camera=Camera(0, 0, 64, 64, C_BLACK, C_BLACK),
                         win_score=len(levels), available_actions=[1, 2, 3, 4, 5, 6])

    def on_set_level(self, level: Level) -> None:
        ldef = LEVELS[self.level_index]
        self.st = parse_level(ldef)
        self.budget = ldef["budget"]
        self.v = None
        self._script = []
        self._end = None
        self._busy = False
        self.broken = False
        self.scene = Scene(level, self.level_index, self.st.h)
        self._show()

    def view_state(self):
        return self.v[0] if self.v is not None else self.st

    def view_fx(self):
        return self.v[1] if self.v is not None else {}

    def _show(self):
        """Put the frame being shown (or the resting picture) onto the sprites."""
        self.tick += 1
        self.scene.show(self.view_state(), self.view_fx(), self.broken, self.tick, self.budget)

    # -- building the animation (the rules decide once, in act; the frames replay what it recorded) ---------

    def _begin(self):
        aid = self.action.id
        self.tick += 7                  # the idle clock moves between moves too, so each resting picture is its own
        a = {GameAction.ACTION1: 1, GameAction.ACTION2: 2, GameAction.ACTION3: 3, GameAction.ACTION4: 4,
             GameAction.ACTION5: 5, GameAction.ACTION6: 6}.get(aid)
        cell = None
        if a == 6:
            data = self.action.data or {}
            x, y = int(data.get("x", 0)), int(data.get("y", 0))
            if 0 <= x < PANEL_X and 0 <= y < VIEW * CELL:
                cell = (cam_top(self.st.r, self.st.h) + y // CELL, x // CELL)
        frames = []
        if a == 6 and cell is None:
            # a click off the shaft (on the panel or the bottom edge): the cursor mark flashes where it landed,
            # nothing else happens
            self._script = [(self.st.copy(), {"point": (x, y)}), (self.st.copy(), {})]
            self._end = None
            return
        new, res = act(self.st, a, cell, rec=lambda s, fx: frames.append((s.copy(), dict(fx))))
        if res.outcome == "win":
            for k in range(1, 5):
                frames.append((new.copy(), {"finish": k}))
            for k in range(1, 4):
                frames.append((new.copy(), {"finish": 4, "sink": 2 * k}))
            for k in range(1, 5):
                frames.append((new.copy(), {"sink": 7, "fade": k}))
            self._end = "next"
        elif res.outcome == "die":
            if res.why == "budget":
                # the bar is empty and the finish is out of reach: it flashes and the hero breaks
                for k in range(1, 6):
                    frames.append((new.copy(), {"bar_flash": k % 2 == 1, "poof": k}))
            self._end = "die"
        else:
            self._end = None
            if frames and frames[-1][1]:
                # the step loop swallows the last frame (it settles on the resting picture), so every effect
                # recorded, the last puff included, gets shown before the rest
                frames.append((new.copy(), {}))
        self.st = new
        self._script = frames

    # -- engine entry point ---------------------------------------------------------------------------------

    def step(self) -> None:
        if self.action.id == GameAction.RESET:
            self._script = []
            self._end = None
            self._busy = False
            self.v = None
            self.broken = False
            self._show()
            self.complete_action()
            return

        if not self._busy:
            self._busy = True
            self._begin()
            if not self._script and self._end is None:
                self._busy = False
                self.v = None
                self._show()
                self.complete_action()
                return

        if self._script:
            self.v = self._script.pop(0)
            self._show()
            if self._script or self._end is not None:
                return
            # settled: the last recorded frame is the resting picture
            self._busy = False
            self.v = None
            self._show()
            self.complete_action()
            return

        # the frame after the last scripted one: apply what the animation was showing
        end, self._end = self._end, None
        self._busy = False
        self.v = None
        if end == "next":
            self.next_level()                   # builds the next level's scene and shows its opening picture
        elif end == "die":
            self.broken = True
            self.lose()
            self._show()
        else:
            self._show()
        self.complete_action()
