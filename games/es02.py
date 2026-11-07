# ARC-AGI-3 candidate task es02 (Extreme Sneeze, redrawn).
# Author: Claude Sonnet 5.5
# Date: 07-November-2026
# Updated: 07-November-2026, Claude Sonnet 5.5: round A, a calmer and clearer picture (quiet floors, plain lawn, fewer twinkles and props); rules untouched.
# Updated: 07-November-2026, Claude Sonnet 5.5: round B (animation): hop-and-settle movement with a shadow, squash and dust wake, a bump when a step is blocked, a
#   sneeze recoil, a pop of sparks on every infection, heal, build and host switch, an angry stamp and a flinch, a bobbing visitor and host, a calmer neon level; rules untouched.
# Updated: 07-November-2026, Claude Sonnet 5.5: round C (final look): the win sweep now slides away to uncover the next level instead of cutting to it, calmer stall,
#   cabinet and vending-machine art, a gentler station mosaic and loss wash, a glint that slides over the wall columns, everyone bobs on their own beat; rules untouched.
# PURPOSE: es02 redraws es01 (Extreme Sneeze: spread an alien infection through a city, hopping between infected hosts).
#   THE RULES ARE UNCHANGED: every level's layout and solution, the level order, the inputs offered, the click geometry,
#   the win and loss outcomes, the spray / hop / hostile / doctor / barricade behaviour and the visible spore supply are
#   the same code as es01. Only the art is new: eight distinct looks (a plaza with trees and a street, a lantern-lit
#   market and a night market, two clinics, a station, a tunnel and a neon terminal), every thing on screen a named
#   engine Sprite with a face, small floor decals, gentle ambient life (swaying trees, a passing taxi, blinking lights,
#   twinkles, a spinning vent fan), drawn feedback for a spray, a hit, a refused move, a won level and a lost run.
# SRP/DRY check: Pass -- one game class; the rules (spray, turns, camera, click mapping) are copied unchanged from es01;
#   everything above the class only draws (pixel art, floors, walls, level backdrops) and holds no game rule.
#   Nothing is shared with es01 and es01 is untouched.
# CHANGELOG
# 07-Nov-2026 (Claude Sonnet 5.5): round B (animation, drawing only): three-step hops with a landing squash, a shadow and a dust wake behind the host
#   and the visitor; a blocked step bumps (nudge, star, recoil) instead of showing nothing; the sprayer recoils and every new infection, cure,
#   barricade and host switch pops; the hit visitor shakes, an angry guard stamps, a half-hit person flinches; idle bob for host and visitor in
#   action frames; the neon level lost its scan line and half its pulses; fewer petals on the lawn. No rule, level, input or outcome changed.
# 07-Nov-2026 (Claude Sonnet 5.5): first version of es02 -- es01's rules, a full redraw. Pass 1 of 4 (build).
# 07-Nov-2026 (Claude Sonnet 5.5): pass 2 of 4 (critique and redraw): calmer brick and tunnel floors, cobbled night market,
#   big-slab ward and station floors, a traffic barrel for the hazard pillar, new window and cabinet walls, a sharper doctor,
#   and expressions (blink, wince on loss, cheer on win).
# 07-Nov-2026 (Claude Sonnet 5.5): pass 3 of 4 (variety and life): the ward floor is now sky-blue and sunny-yellow slabs
#   with toys instead of white; the station is bevelled violet and maroon slabs with mosaic inlays, flecks and a tactile
#   strip; the neon terminal is a circuit board (chips, nodes, glowing traces with pulses running along them, a scan line);
#   every level has its own floor decals, wall shadows, board-edge dressing and its own inert life (butterflies and
#   sparrows, fireflies, steam and lanterns, soap bubbles, tied balloons, tumbling paper, drips, pulses); a real cheer
#   (hands up, wide mouth, bounce, sparkle burst) and a confetti shower on a won level; tears, orbiting dizzy stars and
#   a drooping ghost on a lost run. Rules, geometry, frame order of the rule code: unchanged.
# 07-Nov-2026 (Claude Sonnet 5.5): pass 4 of 4 (polish): the lost-run wash is a solid red frame closing in (no dither); the win
#   wipe uses pale flecks instead of pink. Rules unchanged.
# 07-Nov-2026 (Claude Sonnet 5.5): round A (calm and readable): quieter floors a step apart in one hue family (big slabs, no
#   seams-on-every-tile, rarer litter and flecks), a plain lawn and calmer trees and shopfronts in the plaza, sparser twinkles
#   and ambient life so the people, the host ring and the hazards pop. Rules unchanged.

from copy import deepcopy
from collections import deque
from math import sin, cos
from arcengine import ARCBaseGame, Camera, GameAction, Level, Sprite

CELL = 6
W, H = 10, 9
DIRS = {1:(0,-1), 2:(0,1), 3:(-1,0), 4:(1,0)}

# The 16 ARC colours by name. Indexes 1-4 are greys and are deliberately never used.
WHT, BLK, MAG, PNK, RED, BLU, LBL, YEL, ORG, MAR, GRN, PUR = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15

# One letter per colour, so sprites can be drawn as text rows. '.' is transparent. Upper-case letters are
# per-call parameters (a theme colour) handed to art().
LEG = dict(w=WHT, k=BLK, m=MAG, p=PNK, r=RED, b=BLU, l=LBL, y=YEL, o=ORG, d=MAR, g=GRN, v=PUR)


def _cross(width, row, gates):
    return [(x,row) for x in range(width) if x not in gates]


def _partitions(height, columns):
    return [(x,y) for x,gates in columns for y in range(height) if y not in gates]


# ---- level specifications: identical to es01 (layout, people, walls, vents, barricade spots, goals) ----
LEVELS_SPEC = [
 dict(size=(7,6), alien=(1,3), people=[(3,3),(5,3),(6,5)], doctors=[], walls=[], build=[], goal=2),
 dict(size=(20,10), alien=(1,4), people=[(3,4),(2,1),(8,4),(12,1),(17,2),(17,8)], doctors=[], walls=_partitions(10,[(6,{1,2,4})]), vents=[(6,4)], anchored=[(8,4),(17,8)], build=[]),
 dict(size=(18,12), alien=(1,4), people=[(3,4),(6,2),(9,4),(14,5),(16,9)], hostile=[(1,9)], doctors=[], walls=_partitions(12,[(7,{4}),(12,{2,3,7,8})]), vents=[(7,4)], anchored=[(9,4)], build=[]),
 dict(size=(19,13), alien=(1,5), people=[(3,5),(6,3),(9,3),(15,5),(17,10)], hostile=[(2,8),(9,10)], doctors=[(14,8)], walls=_partitions(13,[(7,{2,3,8,9}),(13,{4,5,9,10})]), build=[(7,3),(13,5),(13,9)]),
 dict(size=(20,14), alien=(2,6), people=[(4,6),(6,3),(10,4),(14,8),(15,3),(18,11)], hostile=[(3,8),(9,9),(16,8)], doctors=[(12,10)], walls=_partitions(14,[(7,{3,4,9,10}),(13,{8})])+_cross(20,7,{3,4,8,9,15,16}), vents=[(13,8)], anchored=[(14,8)], build=[(7,4),(7,9)]),
 dict(size=(21,15), alien=(2,7), people=[(4,7),(6,4),(10,3),(15,4),(19,12)], hostile=[(3,9),(10,11),(16,10)], doctors=[(14,12)], walls=_partitions(15,[(7,{3,4,10,11}),(13,{4,5,9,10}),(18,{2,3,11,12})]), build=[(7,4),(13,9),(18,11)]),
 dict(size=(22,15), alien=(3,7), people=[(4,7),(6,3),(10,3),(16,3),(20,12)], hostile=[(2,6),(3,9),(12,7),(3,14)], doctors=[(16,10)], walls=_partitions(15,[(7,{3,4,7,9,10}),(14,{4,5,10,11}),(19,{2,3,11,12})]), build=[(7,4),(14,10),(19,11)]),
 dict(size=(24,16), alien=(2,8), people=[(4,8),(6,3),(10,4),(16,3),(21,13)], hostile=[(3,10),(6,11),(10,12),(17,10)], doctors=[(15,12),(21,6)], walls=_partitions(16,[(7,{3,4,10,11}),(14,{4,5,10,11}),(20,{2,3,11,12})])+_cross(24,7,{2,3,9,10,16,17,22,23}), build=[(7,4),(14,10),(20,11)])
]

# ---- one look per level. scene picks the wall family; tile picks the floor; trim is the two-colour board edge; ink is
# the colour of the small "which way am I facing" pixel on a person (it must show against that floor); glint colours
# are the twinkles; A/B/W are the wall family's own colours. ----
SCENES = ('street','market','market','clinic','clinic','transit','transit','transit')
THEMES = [
 dict(tile='plaza',    life='plaza',   c1=BLU, c2=PUR, seam=LBL, trim=(YEL,WHT), ink=WHT, glint=(WHT,YEL,LBL), wall=dict(A=GRN,B=WHT,W=ORG)),
 dict(tile='brick',    life='market',  c1=YEL, c2=WHT, seam=ORG, trim=(RED,WHT), ink=BLK, glint=(WHT,RED,PNK), shade=ORG, edge=(MAR,ORG), wall=dict(A=RED,B=WHT,W=MAR)),
 dict(tile='night',    life='night',   c1=PUR, c2=MAR, seam=MAR, trim=(YEL,BLU), ink=WHT, glint=(YEL,PNK,WHT), shade=BLK, edge=(BLK,MAG), wall=dict(A=YEL,B=BLU,W=ORG)),
 dict(tile='clinic',   life='clinic',  c1=LBL, c2=WHT, seam=WHT, trim=(WHT,RED), ink=BLK, glint=(WHT,YEL,BLU), stripe=YEL, shade=BLU, edge=(BLU,WHT), wall=dict(A=RED,B=BLU,W=WHT)),
 dict(tile='checker',  life='ward',    c1=LBL, c2=BLU, seam=BLU, trim=(WHT,BLU), ink=BLK, glint=(WHT,RED,BLU), stripe=RED, shade=BLU, edge=(BLU,MAG), wall=dict(A=BLU,B=RED,W=WHT)),
 dict(tile='platform', life='station', c1=PUR, c2=MAR, seam=MAR, trim=(YEL,BLK), ink=WHT, glint=(WHT,LBL,YEL), shade=BLK, edge=(BLK,YEL), wall=dict(A=BLU,B=YEL,W=ORG)),
 dict(tile='tunnel',   life='tunnel',  c1=BLU, c2=LBL, seam=LBL, trim=(YEL,BLK), ink=WHT, glint=(WHT,YEL,LBL), shade=PUR, edge=(PUR,ORG), wall=dict(A=ORG,B=BLK,W=RED)),
 dict(tile='neon',     life='neon',    c1=BLK, c2=PUR, seam=PUR, trim=(MAG,LBL), ink=WHT, glint=(MAG,YEL,LBL), shade=PUR, edge=(BLU,MAG), wall=dict(A=MAG,B=LBL,W=PUR)),
]


# =====================================================================================================
# PART ONE: pixel-art helpers. Nothing in here knows a game rule.
# =====================================================================================================

def art(rows, **extra):
    """Text rows to a pixel grid. '.' is transparent; lower-case letters are palette colours (LEG), upper-case letters
    are colours the caller passes by keyword."""
    leg = dict(LEG, **extra)
    return [[-1 if c == '.' else leg[c] for c in row] for row in rows]


def blank(w, h, colour=-1):
    return [[colour] * w for _ in range(h)]


def rect(g, x0, y0, x1, y1, c):
    """Fill the box x0..x1, y0..y1 (inclusive), clipped to the grid."""
    for y in range(max(0, y0), min(len(g) - 1, y1) + 1):
        row = g[y]
        for x in range(max(0, x0), min(len(row) - 1, x1) + 1):
            row[x] = c


def put(g, x, y, sp):
    """Paint sprite pixels sp onto grid g at x,y (-1 is skipped, off-grid is clipped)."""
    for j, row in enumerate(sp):
        yy = y + j
        if 0 <= yy < len(g):
            for i, c in enumerate(row):
                xx = x + i
                if c != -1 and 0 <= xx < len(g[0]):
                    g[yy][xx] = c


def hsh(*a):
    """A small deterministic scramble, so decals and twinkles sit in the same place every run."""
    n = 2166136261
    for v in a:
        n = ((n ^ (v & 0xffffffff)) * 16777619) & 0xffffffff
    return n ^ (n >> 15)


def ease_out(t: float) -> float:
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    return 1 - (1 - t) * (1 - t)


def tween(a: int, b: int, step: int, span: int) -> int:
    if span <= 0:
        return b
    return int(round(a + (b - a) * ease_out(step / span)))


# =====================================================================================================
# PART TWO: the creatures. Every picture is six by six (one cell), with a face. The three small marks that
# carry information in es01 are kept in the same places: the facing mark (a pixel just outside the head),
# the green exposure blotches on the chin, and the lit corners of a doctor who has a job.
# =====================================================================================================

# Alien pixels vanish in this order as it is hit; all twenty-six body pixels are gone on the last hit (a loss).
ALIEN_ORDER = [(1,0),(4,0),(0,5),(5,5),(0,2),(5,2),(1,1),(4,1),
               (1,4),(4,4),(2,5),(3,5),(0,3),(5,3),(2,1),(3,1),
               (1,3),(4,3),(2,4),(3,4),(2,3),(3,3),(1,2),(4,2),(2,2),(3,2)]

# Where the two eyes sit on a four-wide head for each way of facing (None: the back of the head shows).
EYE_X = {(1,0): (2,4), (-1,0): (1,3), (0,1): (1,4), (0,-1): None}
# hair, jacket, trousers, skin for six townsfolk (no reds: red belongs to the angry ones, green to the sick)
FOLK = ((MAR,BLU,BLK,ORG), (BLK,PUR,BLU,PNK), (YEL,MAG,MAR,ORG), (ORG,LBL,PUR,PNK), (PUR,YEL,BLK,ORG), (BLK,WHT,MAR,PNK))


def facing_mark(px, heading, colour):
    """The single pixel just outside the head on the side the creature faces (same cells as es01)."""
    dx, dy = heading
    if dx > 0: px[2][5] = colour
    elif dx < 0: px[2][0] = colour
    elif dy < 0: px[0][3] = colour
    else: px[5][3] = colour
    return px


def exposure_blotches(px, exposure):
    """Green sick blotches on the chin: one for the first exposure, two for the second (es01's cells)."""
    if exposure >= 1: px[2][2] = GRN
    if exposure >= 2: px[2][3] = GRN
    return px


def head(px, heading, skin, hair, eye, cap=None):
    px[0] = [-1, hair, hair, hair, hair, -1]
    px[1] = [-1, skin, skin, skin, skin, -1]
    px[2] = [-1, skin, skin, skin, skin, -1]
    eyes = EYE_X[heading]
    if eyes is None:
        px[1] = [-1, hair, hair, hair, hair, -1]          # back of the head
    else:
        for x in eyes: px[1][x] = eye
    return px


def alien_art(heading, damage=0, flash=False, blink=False):
    """The visitor: a green blob with two antenna balls, big eyes that look where it faces, a magenta mouth."""
    px = art(['.m..m.', '.GwGG.', 'GEEEEG', 'GGmmGG', '.GllG.', 'G.GG.G'], G=RED if flash else GRN, E=WHT)
    if blink:
        px[2][1:5] = [BLK] * 4
    else:
        dx, dy = heading
        px[2][1:5] = [WHT, BLK, WHT, BLK] if dx > 0 else [BLK, WHT, BLK, WHT] if dx < 0 else [WHT, BLK, BLK, WHT]
    dx, dy = heading
    if dx > 0: px[2][5] = YEL
    elif dx < 0: px[2][0] = YEL
    elif dy < 0: px[1][3] = YEL
    else: px[4][3] = YEL
    for x, y in ALIEN_ORDER[:damage]:
        px[y][x] = -1
    return px


def ghost_art(rise=0):
    """The alien after the last hit: a violet ghost with crossed eyes and a limp tongue (drawn, no text)."""
    px = art(['.m..m.', '.vvvv.', 'vkwwkv', 'vvmmvv', '.vvvv.', 'v.vv.v'])
    px[2][1:5] = [WHT, BLK, BLK, WHT] if rise % 2 else [BLK, WHT, WHT, BLK]
    px[2][1] = px[2][4] = BLK
    px[2][2] = px[2][3] = WHT
    return px


def civilian_art(heading, variant, infected, controlled, exposure, cough, ink, mood=None):
    hair, jacket, trousers, skin = FOLK[variant % 6]
    if infected: skin = GRN
    px = blank(6, 6)
    head(px, heading, skin, hair, YEL if infected else BLK)
    px[3] = [jacket, jacket, jacket, jacket, jacket, jacket]
    if heading != (0, -1):
        px[3][2] = px[3][3] = LBL if variant % 2 else YEL     # buttons or a necklace, on the front only
    px[4] = [skin, jacket, jacket, jacket, jacket, skin]
    px[5] = [-1, trousers, -1, -1, trousers, -1]
    if infected:
        px[2][2], px[2][3] = BLK, MAG                          # a lopsided sick grin
        px[3][2] = px[3][3] = GRN
    else:
        exposure_blotches(px, exposure)
    if controlled:                                             # the passenger: magenta tendrils, a green crown
        px[0][0] = px[0][5] = px[5][0] = px[5][5] = MAG
        px[0][2] = px[0][3] = GRN
    if cough:                                                  # a sneeze is coming: eyes squeezed, mouth wide open
        for x in (EYE_X[heading] or ()): px[1][x] = BLK
        px[2][2] = px[2][3] = BLK
        px[0][0] = px[0][5] = GRN
    elif mood == 'cheer':                                      # a real cheer: starry eyes, a wide grin, both hands up
        for x in (EYE_X[heading] or ()): px[1][x] = WHT
        px[2][1:5] = [BLK, MAG, MAG, BLK]
        px[1][0] = px[1][5] = skin
        px[4][0] = px[4][5] = -1
    elif mood:
        mood_eyes(px, heading, mood, hair)
    return facing_mark(px, heading, YEL if controlled else ink)


def hostile_art(heading, windup, exposure, ink, mood=None):
    """An angry guard: red cap, red fists raised beside the head, a maroon jacket. Yellow sparks mean a hit is coming."""
    px = blank(6, 6)
    head(px, heading, ORG, RED, BLK)
    px[0] = [-1, RED, RED, RED, RED, -1]
    px[1][0] = px[1][5] = RED
    px[2] = [RED, ORG, WHT, WHT, ORG, RED]                     # fists and a snarl of teeth
    px[3] = [-1, MAR, RED, RED, MAR, -1]
    px[4] = [-1, MAR, MAR, MAR, MAR, -1]
    px[5] = [-1, BLK, -1, -1, BLK, -1]
    exposure_blotches(px, exposure)
    if windup:
        px[0][0] = px[0][5] = px[1][0] = px[1][5] = YEL
        px[0][1] = px[0][4] = YEL
    elif mood:
        mood_eyes(px, heading, mood, RED)
    return facing_mark(px, heading, RED if heading[1] else ink)


def doctor_art(heading, exposure, intent, ink, mood=None):
    """A doctor: white cap with a red band, blue mask, white coat with blue collar, sleeves and a red pen, light-blue
    scrub trousers. Lit corners mean the doctor is on a job."""
    px = blank(6, 6)
    head(px, heading, ORG, WHT, BLK)
    px[0] = [-1, WHT, RED, RED, WHT, -1]                       # the cap and its red band
    px[1][0] = px[1][5] = WHT
    px[2] = [-1, BLU, LBL, LBL, BLU, -1]                       # the mask, with a lighter centre
    px[3] = [BLU, WHT, BLU, BLU, WHT, BLU]                     # blue collar and sleeves against the white coat
    px[4] = [BLU, WHT, WHT, RED, WHT, BLU]                     # the red pen in the pocket
    px[5] = [-1, LBL, -1, -1, LBL, -1]                         # scrub trousers
    if heading == (0, -1):
        px[3] = [BLU, WHT, WHT, WHT, WHT, BLU]
        px[4] = [BLU, WHT, WHT, WHT, WHT, BLU]
    exposure_blotches(px, exposure)
    if intent:
        px[0][0] = px[0][5] = YEL
    mood_eyes(px, heading, mood, WHT)
    return facing_mark(px, heading, YEL)


def mood_eyes(px, heading, mood, hair):
    """Expressions shared by every person: a blink or a wince shuts the eyes; a cheer opens the mouth wide."""
    eyes = EYE_X[heading]
    if not mood or eyes is None:
        return px
    if mood in ('blink', 'wince'):
        for x in eyes: px[1][x] = hair if mood == 'blink' else BLK
        if mood == 'wince':
            px[2][2] = px[2][3] = BLK
            for x in eyes:                                      # tears run down from the shut eyes
                if x not in (2, 3): px[2][x] = LBL
    elif mood == 'cheer':
        px[2][2] = px[2][3] = MAG if px[2][2] != BLU else px[2][2]
    return px


def spore_pips(supply):
    """The visible spore supply: three capsules beside the host, magenta when full, dark when spent (es01: three pips)."""
    px = blank(2, 6)
    for j in range(3):
        lit = j < supply
        px[j * 2][0] = MAG if lit else MAR
        px[j * 2][1] = PNK if lit else MAR
        px[j * 2 + 1] = [BLK, BLK]
    return px


def host_ring(phase):
    """Yellow brackets around the host you control (a pulse between yellow and white)."""
    c = YEL if phase % 2 == 0 else WHT
    px = blank(8, 8)
    for a, b in ((0, 0), (7, 0), (0, 7), (7, 7)):
        px[b][a] = c
        px[b][a + (1 if a == 0 else -1)] = c
        px[b + (1 if b == 0 else -1)][a] = c
    return px


def medical_wall(strength):
    """A hazard barricade: black base, yellow-and-black edge, a fat red cross on white. Strength one is cracked."""
    px = art(['ywrrwy', 'wwrrww', 'rrrrrr', 'rrrrrr', 'wwrrww', 'kwrrwk'])
    if strength == 1:
        for x, y in ((3, 0), (2, 1), (3, 2), (2, 3), (3, 4)):    # a black crack runs down through the cross
            px[y][x] = BLK
        px[5][2] = BLK
    return px


def impact_burst(phase):
    """A ring of red with yellow sparks, eight by eight (es01 drew the same ring in plain red)."""
    px = blank(8, 8)
    for y in range(8):
        for x in range(8):
            if ((y in (0, 7) and 2 <= x <= 5) or (y in (1, 6) and x in (1, 6)) or (2 <= y <= 5 and x in (0, 7))):
                px[y][x] = RED if (x + y + phase) % 2 else ORG
    for x, y in ((1, 1), (6, 1), (1, 6), (6, 6)):
        px[y][x] = YEL
    px[3][3] = px[4][4] = YEL if phase % 2 else WHT
    return px


def refuse_marks():
    """Red corner brackets: that move was not allowed (es01 drew four red corner dots)."""
    px = blank(6, 6)
    for a, b in ((0, 0), (5, 0), (0, 5), (5, 5)):
        px[b][a] = RED
        px[b][a + (1 if a == 0 else -1)] = RED
        px[b + (1 if b == 0 else -1)][a] = RED
    return px


POP_KINDS = dict(infect=(GRN, YEL), heal=(LBL, WHT), build=(YEL, WHT), host=(MAG, WHT))


def pop_burst(kind):
    """A wide ring of sparks around one cell: the 'something just happened here' flash (an infection, a cure, a new
    barricade or a host switch). Ten by ten, so it clears the host's yellow brackets."""
    a, b = POP_KINDS[kind]
    return art(['....AA....', '.B......B.', '..........', '..........', 'A........A', 'A........A', '..........', '..........', '.B......B.', '....AA....'], A=a, B=b)


def dust_art(step, colour):
    """The little cloud kicked up behind a mover: a puff, then two wisps drifting apart, then two specks. Returns
    (pixels, dx, dy) relative to the cell the mover just left."""
    c = colour
    if step <= 1: return [[-1, c, c, -1], [c, c, c, c]], 1, 3
    if step == 2: return [[-1, c, -1, -1, c, -1], [c, -1, -1, -1, -1, c]], 0, 3
    return [[c, -1, -1, -1, -1, c]], 0, 2


def bonk_art(step):
    """The star where a blocked step hit something: a bright plus, then four sparks flying apart."""
    if step == 0: return [[-1, YEL, -1], [YEL, WHT, YEL], [-1, YEL, -1]]
    return [[WHT, -1, -1, -1, WHT], [-1, -1, -1, -1, -1], [-1, -1, -1, -1, -1], [-1, -1, -1, -1, -1], [WHT, -1, -1, -1, WHT]]


def squashed(face):
    """The landing squash: the sixth-high picture with its torso row squeezed out, so the head drops a pixel."""
    return [[-1] * len(face[0])] + [list(r) for r in face[:3]] + [list(r) for r in face[4:]]


def droplet(phase):
    """A sneeze cloud over one cell: a green puff with white shine and a magenta and a light-blue speck."""
    p = art(['..g...', '.gwg..', 'ggggg.', '.ggg..', '..g..l', '....l.'])
    if phase % 2:
        p = art(['...g..', '..gg..', '.gwgg.', 'ggggg.', '.lg.g.', '..m...'])
    return p


def barricade_marker(phase):
    """The corners where a doctor means to build next (same cells as es01), blinking between light blue and white."""
    px = blank(6, 6)
    c = LBL if phase % 2 else WHT
    for a, b in ((0, 0), (5, 0), (0, 5), (5, 5)):
        px[b][a] = c
    px[0][1] = px[1][0] = px[0][4] = px[1][5] = YEL
    px[5][1] = px[4][0] = px[5][4] = px[4][5] = YEL
    return px


def wipe_art(width, clock):
    """The win sweep: a green wave with white foam, pale leaf flecks and sparkles, pushed across the screen."""
    face = blank(width, 64)
    wave = (0, 1, 2, 1, 0, -1, -2, -1)
    for y in range(64):
        edge = min(width, width + wave[(y // 2 + width // 4) % 8])
        for x in range(edge):
            c = GRN
            if x >= edge - 1: c = WHT
            elif x >= edge - 2: c = LBL
            elif hsh(x // 3, y // 3) % 7 == 0: c = LBL if hsh(x, y) % 2 else WHT
            elif hsh(x, y, clock) % 41 == 0: c = YEL
            face[y][x] = c
    return face


def lose_tint(level):
    """The run-over look: a solid red frame closes in from the screen edges (a wider ring each beat, a dark rim on its
    inner side and a wavy edge), so the board in the middle stays readable and no pixel dither is used."""
    face = blank(64, 64)
    depth = (0, 5, 9, 13)[min(level, 3)]
    if depth == 0:
        return face
    for y in range(64):
        for x in range(64):
            d = min(x, y, 63 - x, 63 - y)
            ring = depth + (1 if (x + y) // 3 % 2 else 0)      # a gently scalloped inner edge
            if d < ring - 1: face[y][x] = RED if (d > 1 or level < 3) else ORG
            elif d < ring: face[y][x] = MAR
    return face


# =====================================================================================================
# PART THREE: walls, vents and floors.
# =====================================================================================================

# Market stalls (A, B are the awning's two colours, W is the wood). Four looks so a column of stalls is not a wall of copies.
MARKET = (
    ('AABBAA', 'AABBAA', 'BBAABB', 'rrWrrW', 'WWWWWW', 'kkkkkk'),      # awning over a fruit counter
    ('WWWWWW', 'WyyyyW', 'WyyyyW', 'WWddWW', 'WddddW', 'kkkkkk'),      # crates of oranges and bananas
    ('pypypy', 'pppppp', 'WWWWWW', 'WddWdW', 'WWWWWW', 'kkkkkk'),      # a flower box
    ('BBAABB', 'BBAABB', 'AABBAA', 'lylyly', 'WWWWWW', 'kkkkkk'),      # awning over hanging jars
)
# Clinic partitions (A, B accents; W is the wall white).
CLINIC = (
    ('AAAAAA', 'wlllbw', 'wllbbw', 'wlbbbw', 'wwwwww', 'kkkkkk'),      # a window: gradient glass, a sill
    ('kkkkkk', 'kbbllk', 'kwwwwk', 'kbbllk', 'kwwwwk', 'kkkkkk'),      # a medicine cabinet of bottles on two shelves
    ('kkkkkk', 'kwwwwk', 'kBBBBk', 'kBAABk', 'kBBBBk', 'kkkkkk'),      # a bed: pillow and blanket
    ('kkkkkk', 'AAWWBB', 'AAWWBB', 'AAWWBB', 'AAWWBB', 'kkkkkk'),      # a striped privacy curtain
)
# Station fittings (A, B, W are the level's colours).
TRANSIT = (
    None,                                                              # a hazard-striped pillar (drawn from a rule)
    ('AAAAAA', 'AyyAyy', 'AyyAyy', 'AAAAAA', 'kwkkwk', 'kkkkkk'),      # the side of a train car
    ('BBBBBB', 'BkkkkB', 'BklykB', 'BkkkkB', 'BBAABB', 'kkkkkk'),      # a ticket kiosk with a lit screen
    ('kkkkkk', 'kryryk', 'kwwwwk', 'kryryk', 'kAAAAk', 'kkkkkk'),      # a vending machine
)


def hazard_pillar(A, B):
    """A striped traffic barrel: a lit yellow lamp on top, bands of A and white, a black foot. B is unused so the
    pillar keeps the same call shape as the other fittings."""
    return art(['kyyyyk', 'kAAAAk', 'kwwwwk', 'kAAAAk', 'kwwwwk', 'kkkkkk'], A=A)


def wall_art(scene, variant, theme):
    w = theme['wall']
    if scene == 'market': return art(MARKET[variant], **w)
    if scene == 'clinic': return art(CLINIC[variant], **w)
    if variant == 0: return hazard_pillar(w['A'], w['B'])
    return art(TRANSIT[variant], **w)


def vent_art(phase):
    """A yellow vent with a fan that turns between two frames."""
    blades = (('BYYB', 'BBYY', 'YYBB', 'BYYB'), ('YYBB', 'BYYB', 'BBYY', 'YYBB'))[phase % 2]
    return art(['kkkkkk'] + ['k' + r + 'k' for r in blades] + ['kkkkkk'], B=MAR, Y=YEL)


def tile_plaza(tx, ty, t):
    px = blank(6, 6, t['c1'] if (tx + ty) % 2 == 0 else t['c2'])   # a plain two-tone checker, no seams: a quiet stage
    if hsh(tx, ty) % 19 == 0:                                   # a rare small gold inlay
        px[3][2] = px[3][3] = px[2][3] = YEL
    return px


def decal(px, x, y, rows, **extra):
    """Stamp a small drawn thing (a dropped fruit, a heart, a toy) onto a floor tile."""
    put(px, x, y, art(rows, **extra))


# Little floor litter, one list per place. Each is a flat picture on the floor: nothing here is an obstacle.
BRICK_LITTER = (('.g.', 'rrr', 'rrr'), ('.g.', 'doo', 'ooo'), ('ggg', 'gwg', 'ggg'), ('vvv', 'vwv', '.g.'),
                ('p.b', '.m.', 'b.p'), ('.dd', 'ddd', '.dd'))                    # apple, orange, cabbage, grapes, confetti, a dropped date
NIGHT_LITTER = (('.ll.', 'lyml', '.ll.'), ('m.m', '.m.', '...'), ('oo.', '.od', '...'), ('p.w', '.w.', 'w.p'))   # a lantern puddle, paws, a leaf, petals
CLINIC_LITTER = (('.r.r.', 'rwrrr', '.rrr.', '..r..'), ('wpppw', 'wpppw'), ('.y.', 'yyy', '.y.'), ('bbbb', 'kbkb', 'bbbb'))  # heart, plaster, sticker, drain
WARD_LITTER = (('bb..', 'bbrr', '..rr'), ('.m.', 'mmm', '.m.'), ('..b..', 'bbbbb', '.bbb.'), ('.r.', 'rwr', '.r.'))  # blocks, star, paper boat, ball
STATION_LITTER = (('yy', 'yo'), ('pp', 'pp'), ('www', 'mmm'), ('.ll.', 'llll', '.ll.'))      # coin, gum, a ticket, a puddle
TUNNEL_LITTER = (('.kk.', 'kmkk', '.kk.'), ('do', 'od'), ('ddd', 'dod', 'ddd'), ('.o.', 'ooo', '.o.'))    # oil, rust, a lamp base, a cable coil


def litter(px, tx, ty, kinds, seed, every=13):
    """Drop one bit of litter on roughly one tile in `every`, picked and placed by the tile's own hash."""
    n = hsh(tx, ty, seed)
    if n % (every * 2) == 0:                                    # half as often as asked: litter is a treat, not a texture
        rows = kinds[(n >> 5) % len(kinds)]
        decal(px, 1 + (n >> 9) % max(1, 5 - len(rows[0])), 1 + (n >> 12) % max(1, 5 - len(rows)), rows)


def tile_brick(tx, ty, t):
    """Running-bond paving, calm: big two-cell yellow bricks, one thin orange mortar line under each course and one joint
    per brick, now and then something dropped from a stall."""
    px = blank(6, 6, t['c1'])
    px[5] = [t['seam']] * 6
    if tx % 2 == ty % 2:
        for y in range(5): px[y][5] = t['seam']
    litter(px, tx, ty, BRICK_LITTER, 9)
    return px


def tile_night(tx, ty, t):
    """Wet cobbles, calm: big two-cell stones outlined in maroon on violet, a rare magenta lamp-glow, the odd puddle, paw
    prints and leaves."""
    px = blank(6, 6, t['c1'])
    px[5] = [t['seam']] * 6
    if tx % 2 == ty % 2:
        for y in range(5): px[y][5] = t['seam']
    if hsh(tx, ty) % 23 == 0: px[2][2] = px[2][3] = MAG
    litter(px, tx, ty, NIGHT_LITTER, 5, 10)
    return px


def tile_clinic(tx, ty, t):
    """Pale ward tiles: twelve-pixel slabs with white seams and a shine, a yellow dashed guide line, hearts and plasters."""
    px = blank(6, 6, t['c1'])
    for i in range(6):
        if ty % 2: px[5][i] = WHT
        if tx % 2: px[i][5] = WHT
    if ty % 5 == 2:                                             # a guide line along the corridor, dashed
        for r in (2, 3):
            px[r] = [t['stripe'] if (i + tx) % 4 < 3 else t['c1'] for i in range(6)]
    else:
        litter(px, tx, ty, CLINIC_LITTER, 4, 11)
    return px


def tile_checker(tx, ty, t):
    """The sunny ward: twelve-pixel slabs, mostly sky blue with the odd warm yellow one, deep-blue grout,
    a red dashed line across every few rows, and children's toys dropped about. No big white areas."""
    sky = hsh(tx // 2, ty // 2, 4) % 4 != 0             # most slabs are sky blue; a warm yellow one now and then
    px = blank(6, 6, t['c1'] if sky else YEL)
    for i in range(6):
        if tx % 2 == 1: px[i][5] = t['c2']
        if ty % 2 == 1: px[5][i] = t['c2']
    if ty % 7 == 3:
        px[2] = [t['stripe'] if i % 3 != 2 else (YEL if sky else LBL) for i in range(6)]
        px[3] = [MAR if i % 3 != 2 else px[3][i] for i in range(6)]
    else:
        litter(px, tx, ty, WARD_LITTER, 6, 12)
    return px


# A twelve-pixel mosaic inlay for the station floor, cut into four tile-sized quarters.
def _star():
    """A small diamond mosaic by distance from the centre: a yellow spark in an orange diamond (two flat colours, no rim)."""
    g = blank(12, 12)
    for y in range(12):
        for x in range(12):
            d = abs(x - 5.5) + abs(y - 5.5)
            g[y][x] = YEL if d <= 1.5 else ORG if d <= 4.5 else -1
    return g


SLAB_STAR = _star()


def tile_platform(tx, ty, t):
    """Station concrete, bevelled: two-cell slabs of violet and maroon, each with a light top and left edge and a dark
    bottom and right one, an occasional diamond mosaic, a rare drain grate, and the yellow edge strip."""
    big = 1 if hsh(tx // 2, ty // 2, 6) % 3 == 0 else 0     # mostly violet slabs, a maroon one in three
    base, lo = (t['c1'], MAR) if big == 0 else (t['c2'], BLK)
    px = blank(6, 6, base)
    if ty % 2 == 1: px[5] = [lo] * 6                            # one dark edge under and beside each slab, nothing more
    if tx % 2 == 1:
        for y in range(6): px[y][5] = lo
    n = hsh(tx, ty, 3)
    top = (ty // 2) * 2
    if hsh(tx // 2, ty // 2, 7) % 11 == 0 and top % 5 != 0 and (top + 1) % 5 != 0:   # a diamond mosaic in this slab
        qx, qy = (tx % 2) * 6, (ty % 2) * 6
        for y in range(6):
            for x in range(6):
                c = SLAB_STAR[qy + y][qx + x]
                if c != -1: px[y][x] = c
    if ty % 5 == 0:                                             # the yellow safety strip at the platform edge
        px[1] = [ORG] * 6
        px[2] = [YEL] * 6
        px[3] = [BLK, YEL, YEL, BLK, YEL, YEL]                  # raised bumps
        px[4] = [BLK] * 6
        px[5] = [MAR] * 6
    elif n % 41 == 5:                                           # a drain grate
        for y in (1, 2, 3):
            px[y][1:5] = [BLK, LBL, BLK, LBL] if y % 2 else [LBL, BLK, LBL, BLK]
    return px


def tile_tunnel(tx, ty, t):
    """Riveted steel plates: blue with a light top edge and a violet foot, rivets on each plate, a cable conduit now and
    then, oil, rust and cable coils on the floor."""
    px = blank(6, 6, t['c1'])
    if ty % 2 == 1: px[5] = [PUR] * 6                           # big plates two cells tall, a violet foot under each
    if tx % 2 == 0:
        for y in range(6): px[y][0] = PUR                       # and a violet seam on the left of each plate
        if ty % 2 == 0: px[1][1] = WHT                          # one rivet a plate
    if ty % 8 == 3:                                             # a cable conduit running along the tunnel
        px[2] = [ORG] * 6
        px[3] = [MAR] * 6
        px[2][(tx % 3) * 2] = YEL
    else:
        litter(px, tx, ty, TUNNEL_LITTER, 2, 14)
    return px


# The neon terminal's chip: a twelve-pixel microchip, cut into four tile quarters (pins all round, a lit die).
def _chip():
    g = blank(12, 12, BLK)
    rect(g, 1, 1, 10, 10, BLU)
    rect(g, 3, 3, 8, 8, PUR)
    rect(g, 4, 4, 7, 7, MAG)
    g[5][5] = g[6][6] = WHT
    for i in range(1, 11, 2):                                   # pins on all four sides
        g[0][i] = g[11][i] = g[i][0] = g[i][11] = YEL
    for x, y in ((1, 1), (10, 1), (1, 10), (10, 10)): g[y][x] = LBL
    return g


CHIP = _chip()


def tile_neon(tx, ty, t):
    """A circuit board: a black board with sparse blue grid lines, glowing magenta power traces every sixth row with round
    lit nodes, vertical vias between them, the odd microchip, and scattered LEDs."""
    px = blank(6, 6, t['c1'])
    for i in range(6):                                          # a twelve-pixel grid of blue lines, dotted in between
        if ty % 4 == 0: px[0][i] = t['c2']
        if tx % 6 == 0: px[i][0] = t['c2']
    top = (ty // 2) * 2
    if top % 6 == 4 and ((tx // 2) * 7 + ty // 6) % 5 == 0:     # a chip sits on two rows that carry no trace
        qx, qy = (tx % 2) * 6, (ty % 2) * 6
        for y in range(6):
            for x in range(6): px[y][x] = CHIP[qy + y][qx + x]
        return px
    if ty % 6 == 0:                                             # the trace: a lit core over a dark shadow
        px[2] = [MAG] * 6
        px[3] = [PUR] * 6
        if tx % 12 == 0:                                        # a round node on the trace
            px[1][1:5] = [BLK, LBL, LBL, BLK]
            px[2][1:5] = [LBL, YEL, YEL, LBL]
            px[3][1:5] = [LBL, YEL, YEL, LBL]
            px[4][1:5] = [BLK, LBL, LBL, BLK]
    elif ty % 6 == 1 and tx % 12 == 2:                           # a via dropping from the trace above
        for y in range(1, 6): px[y][2] = px[y][3] = PUR if y % 2 else MAG
    return px


TILES = dict(plaza=tile_plaza, brick=tile_brick, night=tile_night, clinic=tile_clinic, checker=tile_checker,
             platform=tile_platform, tunnel=tile_tunnel, neon=tile_neon)


def build_floor_grid(theme, w, h, walls=()):
    """Every cell's floor tile stamped into one ground sprite, then wall shadows (a one-pixel dark line under and beside
    each wall) and the board-edge dressing (a dark skirting line and a light one inside the frame)."""
    g = blank(w * CELL, h * CELL)
    tile = TILES[theme['tile']]
    for ty in range(h):
        for tx in range(w):
            put(g, tx * CELL, ty * CELL, tile(tx, ty, theme))
    shade = theme.get('shade')
    if shade is not None:
        for x, y in walls:
            if (x, y + 1) not in walls and y + 1 < h:
                rect(g, x * CELL, (y + 1) * CELL, x * CELL + 5, (y + 1) * CELL, shade)
            if (x + 1, y) not in walls and x + 1 < w:
                rect(g, (x + 1) * CELL, y * CELL, (x + 1) * CELL, y * CELL + 5, shade)
    edge = theme.get('edge')
    if edge is not None:
        dark, light = edge
        rect(g, 0, 0, w * CELL - 1, 0, dark); rect(g, 0, 1, w * CELL - 1, 1, light)
        rect(g, 0, h * CELL - 1, w * CELL - 1, h * CELL - 1, dark); rect(g, 0, h * CELL - 2, w * CELL - 1, h * CELL - 2, light)
        rect(g, 0, 0, 0, h * CELL - 1, dark); rect(g, 1, 2, 1, h * CELL - 3, light)
        rect(g, w * CELL - 1, 0, w * CELL - 1, h * CELL - 1, dark); rect(g, w * CELL - 2, 2, w * CELL - 2, h * CELL - 3, light)
    return g


# =====================================================================================================
# PART FOUR: the plaza of level one (a whole street around the board) and its drifting life.
# =====================================================================================================

TREE_A = ('..kkkkk..', '.kgggggk.', 'kggggggyk', 'kgggggggk', 'kgyggggyk', '.kgggggk.', '..kkkkk..', '...kdk...', '...kdk...', '..kdddk..')
TREE_B = ('..kkkkk..', '.kgggggk.', 'kgggggggk', 'kgggggyyk', 'kgggggggk', '.kgggggk.', '..kkkkk..', '...kdk...', '...kdk...', '..kdddk..')
BIRD = (('k.k', '.k.'), ('.k.', 'k.k'))
CAR = ('..yyyyy...', '.ylyylyy..', 'yyyyyyyyyy', 'yykkyykkyy', '.kwwkkwwk.')
CLOUD = ('..www...', '.wwwwww.', 'wwwwwwww')
BENCH = ('ooooooo', 'd.....d')
LAMP = ('.y.', 'yyy', '.k.', '.k.', '.k.', '.k.', '.k.', '.k.', 'kkk')


def plaza_backdrop(ox, oy, w, h):
    """Level one's world: a lawn with flowers on both sides, a row of shops across the top, a road along the bottom."""
    g = blank(64, 64, GRN)
    for y in range(64):
        for x in range(64):
            n = hsh(x, y)
            if n % 211 == 0: g[y][x] = YEL                      # a very few flowers on a plain lawn
            elif n % 331 == 1: g[y][x] = WHT
    rect(g, 0, 0, 63, oy - 2, LBL)                              # the sky behind the shops
    shops = ((0, 11, ORG, 5), (11, 22, PUR, 3), (22, 31, YEL, 6), (31, 43, MAG, 4), (43, 53, ORG, 2), (53, 63, PUR, 5))
    for x0, x1, body, top in shops:
        rect(g, x0, top, x1 - 1, oy - 2, body)
        rect(g, x0, top, x1 - 1, top, MAR)                      # the roof edge
        for wx in range(x0 + 2, x1 - 3, 5):                     # one row of lit windows
            for wy in range(top + 2, oy - 7, 6):
                rect(g, wx, wy, wx + 1, wy + 1, YEL if hsh(wx, wy) % 3 else LBL)
        for x in range(x0, x1):                                 # an awning over the door
            rect(g, x, oy - 5, x, oy - 4, RED if (x // 4) % 2 else WHT)
        rect(g, x0 + 4, oy - 3, x0 + 5, oy - 2, BLK)            # the door
    bottom = oy + h * CELL + 1
    rect(g, 0, bottom, 63, bottom + 1, WHT)                     # the kerb
    rect(g, 0, bottom + 2, 63, 63, BLK)                         # the road
    for x in range(0, 64, 8): rect(g, x, bottom + 7, x + 3, bottom + 7, YEL)
    for x in range(22, 34, 3): rect(g, x, bottom + 2, x + 1, bottom + 5, WHT)    # the zebra crossing
    return g


def plaza_ambient(clock, ox, oy, w, h):
    """The plaza's gentle life: swaying trees, clouds, birds and a taxi. Returns (pixels, x, y, name, layer)."""
    out = []
    sway = (clock // 4) % 2
    for i, (x, y) in enumerate(((0, oy + 1), (0, oy + 25), (54, oy + 1), (54, oy + 25))):
        rows = TREE_A if (sway + i) % 2 == 0 else TREE_B
        out.append((art(rows), x, y, f'tree_{i}', 3))
    for i, (cx, cy, sp) in enumerate(((10, 1, 3), (40, 5, 2))):
        out.append((art(CLOUD), (cx + clock // sp) % 80 - 12, cy, f'cloud_{i}', 2))
    out.append((art(BIRD[(clock // 2) % 2]), (clock * 2 + 20) % 90 - 10, 4 + (clock // 6) % 2, 'bird_0', 3))
    bottom = oy + h * CELL + 1
    out.append((art(CAR), (clock * 2) % 90 - 14, bottom + 2, 'taxi', 3))
    lamp = art(LAMP)
    for i, (x, bx) in enumerate(((0, 3), (61, 54))):
        out.append((lamp, x, oy + 13, f'lamp_{i}', 3))
        glow = blank(3, 1, YEL if (clock // 3 + i) % 2 else WHT)
        out.append((glow, x, oy + 12, f'lamp_glow_{i}', 3))
        out.append((art(BENCH), bx, oy + 20, f'bench_{i}', 3))
    for i in range(2):                                          # two petals drift down the side lawns
        t = clock * 2 + i * 23
        px = 2 + (i % 2) * 58 + int(3 * sin(t / 5.0))
        out.append(([[PNK if i % 2 else WHT]], px, oy + 2 + t % (h * CELL - 4), f'petal_{i}', 3))
    return out


# =====================================================================================================
# PART FOUR-B: the quiet life of each place, and the celebration and defeat showers. Every handler gets the hash `n` of one
# visible cell, the cell's pixel corner (wx, wy), the clock, the cell and whether a wall stands on it, and returns the
# things to draw there as (pixels, x, y, layer). All of it is inert: it is drawn under the people and never tells you
# anything about the rules. The cost is a handful of tiny sprites around the camera, not the whole board.
# =====================================================================================================

SPARROW = (art(['..dk.', 'ddddy', '.o.o.']), art(['.....', 'dddkd', '.o.oy']))
LANTERN = art(['.d.', 'rrr', 'ryr', '.r.'])
BUBBLE = art(['.b.', 'bwb', '.b.'])
PAPER = (art(['ww', '.y']), art(['w', 'w']))
STAR5 = art(['..y..', '.ywy.', 'ywwwy', '.ywy.', '..y..'])
PLUS5 = art(['..w..', '..w..', 'wwyww', '..w..', '..w..'])
DIZZY = art(['.y.', 'yyy', '.y.'])
PULSE = ([MAG, MAG, PNK, LBL, WHT, WHT], [PUR, PUR, MAG, PNK, PNK, WHT])
CONFETTI_COLOURS = (YEL, PNK, WHT, LBL, MAG, ORG, RED, BLU)
LED_COLOURS = (MAG, YEL, LBL, WHT)
# Tagged tuples in a frame's effects list that only steer the drawing (round B motion notes): hop (key, lift), land (key),
# nudge (key, dx, dy), dust (cell, step), bump (cell, dir, step), pop (cell, kind), flinch (cell), idle (allow a bob).
MOTION_TAGS = ('hop', 'land', 'nudge', 'dust', 'bump', 'pop', 'flinch', 'idle')


def puff(t):
    """A wisp of steam as it rises: a speck, then a bigger curl, then a fading speck."""
    if t < 2: return [[LBL]]
    if t < 5: return [[WHT, LBL], [LBL, WHT]]
    return [[LBL, -1], [-1, LBL]]


def life_market(n, wx, wy, clock, cx, cy, wall):
    out = []
    if wall: return out
    if n % 53 == 0:                                             # a butterfly wanders over the stones
        t = clock + (n >> 8) % 13
        col = (MAG, PUR, WHT, RED)[(n >> 4) % 4]
        wings = ['P.P', '.k.'] if (clock // 2) % 2 else ['PPP', '.k.']
        out.append((art(wings, P=col), wx + 3 + int(5 * sin(t / 3.0)), wy + 2 + int(3 * sin(t / 2.0 + 1)), 3))
    elif n % 71 == 5:                                           # a sparrow hops and pecks at crumbs
        out.append((SPARROW[(clock // 3 + n) % 2], wx + ((clock // 6 + n) % 3) * 2, wy + 2, 3))
    return out


def life_night(n, wx, wy, clock, cx, cy, wall):
    out = []
    if not wall and n % 31 == 0:                                # a firefly blinks as it drifts
        t = clock + (n >> 6) % 17
        on = (clock // 2 + n) % 4 < 3
        out.append(([[YEL if on else PNK]], wx + 3 + int(4 * sin(t / 4.0)), wy + 3 + int(3 * sin(t / 3.0)), 3))
    if wall and n % 4 == 0:                                     # steam curls off the stall
        t = (clock + n) % 8
        out.append((puff(t), wx + 2 + ((t // 2) % 2) * 2, wy + 1 - t, 5))
    if wall and n % 5 == 0 and cy > 0:                          # a paper lantern sways on its string above the stall
        out.append((LANTERN, wx + 1 + (n >> 5) % 3 + int(round(sin((clock + n) / 3.0))), wy - 5, 3))
    return out


def life_clinic(n, wx, wy, clock, cx, cy, wall):
    if wall or n % 37 != 0: return []
    t = (clock + (n >> 6)) % 12                                 # a soap bubble rises and wobbles
    return [(BUBBLE, wx + 2 + int(2 * sin(t / 2.0)), wy + 6 - t, 3)]


def life_ward(n, wx, wy, clock, cx, cy, wall):
    if wall or n % 41 != 2 or cy == 0: return []
    col = (RED, MAG, BLU, PUR, ORG)[(n >> 5) % 5]               # a tied balloon bobs on its string over a little weight
    sx = int(round(1.5 * sin((clock + n % 9) / 4.0)))
    return [(art(['CCC', 'CwC', '.C.'], C=col), wx + 2 + sx, wy - 1, 3), ([[MAR], [MAR], [MAR]], wx + 3, wy + 2, 3),
            ([[BLK, BLK]], wx + 2, wy + 5, 3)]


def life_station(n, wx, wy, clock, cx, cy, wall):
    if wall or n % 61 != 1: return []
    t = (clock + (n >> 6)) % 16                                 # a paper tumbles along the platform
    return [(PAPER[(t // 2) % 2], wx - 2 + t, wy + 3 + ((t // 2) % 2), 3)]


def life_tunnel(n, wx, wy, clock, cx, cy, wall):
    out = []
    if wall: return out
    if n % 43 == 4:                                              # a drip falls from the pipes and splashes
        t = (clock + (n >> 6)) % 10
        x = wx + 1 + (n >> 3) % 3
        out.append(([[LBL], [WHT]], x, wy + t, 3) if t < 5 else ([[LBL, -1, LBL], [-1, WHT, -1]], x - 1, wy + 4, 3))
    if cy % 8 == 3:
        if n % 4 == 0:                                          # steam leaks from the conduit
            t = (clock + n) % 8
            out.append((puff(t), wx + 1 + (n >> 5) % 4 + (t // 3) % 2, wy + 1 - t, 5))
        if (clock // 2 + n) % 3 == 0:                           # the caged lamp flickers white
            out.append(([[WHT]], wx + (cx % 3) * 2, wy + 2, 3))
    return out


def life_neon(n, wx, wy, clock, cx, cy, wall):
    if wall or n % 19 != 0: return []
    return [([[LED_COLOURS[(clock // 2 + n) % 4]]], wx + 3, wy + 3, 3)]           # an LED cycling colours


LIFE = dict(market=life_market, night=life_night, clinic=life_clinic, ward=life_ward, station=life_station,
            tunnel=life_tunnel, neon=life_neon)


def wall_extra(scene, variant, n, wx, wy, clock):
    """Life on the fittings: a station's lamp on the barrel and the row of lights on the vending machine, and on every
    third fitting of any place a single glint of light that slides across it and rests (so the columns are never dead)."""
    out = []
    if scene == 'transit' and variant == 0:
        out.append(([[YEL if (clock // 2 + n) % 2 else WHT] * 4], wx + 1, wy, 5))
    elif scene == 'transit' and variant == 3:
        out.append(([[(RED, YEL, LBL, PNK)[(clock // 2 + i) % 4] for i in range(4)]], wx + 1, wy + 1, 5))
    if n % 3 == 0 and not (scene == 'transit' and variant == 0):
        p = (clock // 2 + n) % 9
        if p < 4: out.append(([[LBL if scene == 'clinic' else WHT]], wx + 1 + p, wy + 4 - p, 5))
    return out


def clip_h(px, x, lo, hi):
    """Crop a one-row-wide-strip picture to the columns lo..hi-1 so a pulse never runs past the board."""
    keep = [i for i in range(len(px[0])) if lo <= x + i < hi]
    if not keep: return None, x
    return [[row[i] for i in keep] for row in px], x + keep[0]


def confetti(f):
    """The level-clear shower: forty-four flakes of coloured paper tumbling down the window; f counts the frames of the
    celebration. Returns (pixels, x, y) in window pixels."""
    out = []
    for i in range(44):
        n = hsh(i, 5)
        x = n % 60 + int(2 * sin((f + i) / 1.5))
        y = (n >> 8) % 30 - 18 + f * 9
        if y < -2 or y > 63: continue
        c = CONFETTI_COLOURS[(n >> 16) % 8]
        out.append(([[c, c, -1], [-1, c, c]] if (f + i) % 2 else [[c, c], [c, c]], x, y))
    return out


# =====================================================================================================
# PART FIVE: the game. The rules below are es01's, unchanged. Only the drawing methods are new.
# =====================================================================================================

class Es02(ARCBaseGame):
    def __init__(self):
        self._dynamic = []
        self._phase = 0
        self._clock = 0
        self._reveal = []
        self._revealing = False
        super().__init__(game_id='es02',
            levels=[Level(sprites=[], grid_size=(64,64), data={'index': i})
                    for i in range(len(LEVELS_SPEC))],
            camera=Camera(width=64, height=64, background=5, letter_box=5),
            available_actions=[1,2,3,4,5,6], win_score=len(LEVELS_SPEC))

    def on_set_level(self, level):
        spec = LEVELS_SPEC[self.level_index]
        self.alien = {'pos':spec['alien'], 'dir':(1,0), 'damage':0}
        self.people = [dict(pos=p, infected=False, exposure=0, doctor=False, anchored=p in spec.get('anchored',()), dir=(1,0))
                       for p in spec['people']]
        self.people += [dict(pos=p, infected=False, exposure=0, doctor=False, hostile=True, windup=False, dir=(-1,0))
                        for p in spec.get('hostile',[])]
        self.people += [dict(pos=p, infected=False, exposure=0, doctor=True, dir=(-1,0))
                        for p in spec['doctors']]
        self.control = None
        if self.level_index > 0:
            self.control = 0
            self.people[0]['infected'] = True
            self.people[0]['exposure'] = 3
        self.walls = set(spec['walls'])
        self.vents = set(spec.get('vents',[]))
        self.medical = {}
        self.tick = 0
        self.supply = 3
        self.cough_pending = None
        self.width, self.height = spec.get('size',(W,H))
        self.ox = max(1,(64-self.width*CELL)//2)
        self.oy = max(1,(64-self.height*CELL)//2)
        self.camera.x = self.camera.y = 0
        self._phase = 0
        self._frames = []
        self._events = []
        self._dynamic = []
        self._clock = 0
        self._result_won = False
        self._result_lost = False
        self._build_floor()
        self._draw(effects=[('reveal',self._reveal.pop(0))] if self._revealing and self._reveal else ())

    # ---------------- sprites ----------------
    def _sprite(self, pixels, x, y, name, layer=1, tags=()):
        s = Sprite(pixels=pixels, x=x, y=y, name=name, layer=layer, tags=list(tags))
        self.current_level.add_sprite(s)
        return s

    def _build_floor(self):
        """Everything that never changes during a level: backdrop, ground, board edge, walls, vents."""
        self.scene = SCENES[self.level_index]
        self.theme = THEMES[self.level_index]
        th = self.theme
        width, height = self.width * CELL, self.height * CELL
        if self.scene == 'street':
            self._sprite(plaza_backdrop(self.ox, self.oy, self.width, self.height), 0, 0, 'backdrop_street', 0, ('scenery',))
        self._sprite(build_floor_grid(th, self.width, self.height, self.walls), self.ox, self.oy, 'floor', 1, ('floor',))
        left, right = self.ox - 1, self.ox + width
        top, bottom = self.oy - 1, self.oy + height
        a, b = th['trim']
        edge_h = [a if (i // 3) % 2 == 0 else b for i in range(width + 2)]
        edge_v = [a if (i // 3) % 2 == 0 else b for i in range(height)]
        self._sprite([edge_h], left, top, 'frame_top', 3, ('frame',))
        self._sprite([edge_h], left, bottom, 'frame_bottom', 3, ('frame',))
        self._sprite([[c] for c in edge_v], left, self.oy, 'frame_left', 3, ('frame',))
        self._sprite([[c] for c in edge_v], right, self.oy, 'frame_right', 3, ('frame',))
        for x, y in ((left, top), (right, top), (left, bottom), (right, bottom)):
            self._sprite([[WHT]], x, y, f'corner_{x}_{y}', 4, ('frame',))
        # walls and vents never change, so they are made once; each wall picks one of four looks from its position
        self._wall_cells = {}
        cache = {}
        for x, y in sorted(self.walls):
            variant = (x * 3 + y * 5) % 4
            if variant not in cache: cache[variant] = wall_art(self.scene, variant, th)
            self._wall_cells[(x, y)] = variant
            self._sprite(cache[variant], self.ox + x * CELL, self.oy + y * CELL, f'wall_{x}_{y}', 4, ('wall',))

    def _clear_dynamic(self):
        for sprite in self._dynamic:
            self.current_level.remove_sprite(sprite)
        self._dynamic = []

    def _put(self, pixels, pos, name, layer=2, tags=()):
        x,y=pos
        self._dynamic.append(self._sprite(pixels, self.ox+round(x*CELL), self.oy+round(y*CELL), name, layer, tags))

    def _put_px(self, pixels, x, y, name, layer, tags=()):
        """A sprite at a world pixel position rather than a cell."""
        self._dynamic.append(self._sprite(pixels, x, y, name, layer, tags))

    def _ambient(self):
        """Gentle life that does nothing: twinkles on floors and walls, blinking lights, a spinning vent fan, the plaza's
        trees, clouds, birds and taxi, and each other place's own small creatures and weather (see LIFE). It is
        clock-driven and never touches the rules."""
        th = self.theme
        clock = self._clock
        for x, y in sorted(self.vents):
            self._put(vent_art(clock // 2), (x, y), f'vent_{x}_{y}', 4, ('vent',))
        if self.scene == 'street':
            for px, x, y, name, layer in plaza_ambient(clock, self.ox, self.oy, self.width, self.height):
                self._put_px(px, x, y, name, layer, ('ambient',))
        # visible cells only: twinkles stay in the window, and the cost does not grow with the level
        cx0 = max(0, (self.camera.x - self.ox) // CELL)
        cy0 = max(0, (self.camera.y - self.oy) // CELL)
        life = LIFE.get(th['life'])
        for cy in range(cy0, min(self.height, cy0 + 12)):
            for cx in range(cx0, min(self.width, cx0 + 12)):
                n = hsh(cx, cy, self.level_index)
                if (cx, cy) in self.vents: continue
                wx, wy = self.ox + cx * CELL, self.oy + cy * CELL
                variant = self._wall_cells.get((cx, cy))
                if life:                                                # this place's own small creatures and weather
                    for k, (px, x, y, layer) in enumerate(life(hsh(cx, cy, self.level_index, 77), wx, wy, clock, cx, cy, variant is not None)):
                        self._put_px(px, x, y, f'life_{cx}_{cy}_{k}', layer, ('ambient',))
                if variant is not None:
                    for k, (px, x, y, layer) in enumerate(wall_extra(self.scene, variant, n, wx, wy, clock)):
                        self._put_px(px, x, y, f'wall_light_{cx}_{cy}_{k}', layer, ('ambient',))
                    if variant == 1 and self.scene in ('clinic', 'transit') and n % 2 == 0:   # a status light on a cabinet or kiosk
                        lamp = (RED, YEL)[(clock // 3 + n) % 2]
                        self._put_px([[lamp]], wx + 4, wy + 1, f'light_{cx}_{cy}', 5, ('ambient',))
                        continue
                    if n % 11 != 0: continue                  # a rare sparkle on a stall or a fitting
                    layer = 5
                elif n % 37 != 0: continue                    # a rare glint on the floor
                else: layer = 2
                phase = (clock // 2 + n) % 5
                if phase > 2: continue
                px = wx + 1 + (n >> 5) % 4
                py = wy + 1 + (n >> 9) % 4
                colour = th['glint'][(n >> 3) % 3]
                shape = [[colour]] if phase != 1 else [[-1, colour, -1], [colour, WHT, colour], [-1, colour, -1]]
                if phase == 1: px, py = px - 1, py - 1
                self._put_px(shape, px, py, f'twinkle_{cx}_{cy}', layer, ('ambient',))
        if th['life'] == 'neon':
            span = self.width * CELL
            for cy in range(cy0, min(self.height, cy0 + 12)):
                if cy % 6: continue                               # data pulses race along the glowing traces, one each way
                for k, (start, direction) in enumerate(((clock * 3 + cy * 19, 1), (clock * 2 + cy * 31, -1))):
                    t = start % (span + 12) - 6
                    x = self.ox + (t if direction > 0 else span - 6 - t)
                    row = list(PULSE[0]) if direction > 0 else list(reversed(PULSE[1]))
                    px, x = clip_h([row, row], x, self.ox, self.ox + span)
                    if px: self._put_px(px, x, self.oy + cy * CELL + 2, f'pulse_{cy}_{k}', 3, ('ambient',))

    # ---------------- drawing a frame ----------------
    def _draw(self, positions=None, effects=(), beam=None):
        self._clear_dynamic()
        self._clock += 1
        clock = self._clock
        th = self.theme
        ink = th['ink']
        lose = next((e[1] for e in effects if isinstance(e[0], str) and e[0] == 'lose'), 0)
        hit = any(isinstance(e[0], str) and e[0] == 'impact' for e in effects)
        # round B motion notes ride in the effects list as tagged tuples (see MOTION_TAGS); none of them is a game rule
        def tagged(tag): return [e for e in effects if isinstance(e[0], str) and e[0] == tag]
        hops = {e[1]: e[2] for e in tagged('hop')}                # key -> pixels the piece is lifted off the ground
        nudges = {e[1]: (e[2], e[3]) for e in tagged('nudge')}    # key -> a pixel shove (a bump, a sneeze recoil)
        lands = {e[1] for e in tagged('land')}                    # keys that squash as they touch down
        flinches = {e[1] for e in tagged('flinch')}               # cells whose person winces at a spray that did not infect
        idle = bool(tagged('idle'))

        def shift(key, bob_on):
            """Pixel offset of a piece: the hop, a shove, and (in idle frames) a small breathing bob."""
            dx, dy = nudges.get(key, (0, 0))
            dy -= hops.get(key, 0)
            if idle and bob_on and key not in hops and key not in nudges: dy -= 1
            return dx, dy
        self._ambient()
        for (x,y),strength in sorted(self.medical.items()):
            self._put(medical_wall(strength),(x,y),f'medical_{x}_{y}',5,('barricade',))
        for doctor in self.people:
            b=doctor.get('build_target') if doctor.get('doctor') and not doctor['infected'] else None
            if b and b not in self.medical:
                self._put(barricade_marker(clock // 2),b,'next_barricade',3,('marker',))
        apos = positions.get('alien',self.alien['pos']) if positions else self.alien['pos']
        dead = self.alien['damage'] >= 26
        blink = (clock // 5) % 8 == 0
        face = alien_art(self.alien['dir'],self.alien['damage'],hit,blink)
        if 'alien' in lands: face = squashed(face)
        # the visitor's glow: four sparkles that trade places
        aura = blank(8, 8)
        for i, (ax, ay) in enumerate(((0,0),(7,0),(0,7),(7,7))):
            if (clock // 2 + i) % 2: aura[ay][ax] = LBL if i % 2 else PNK
        self._put_px(aura, self.ox+round(apos[0]*CELL)-1, self.oy+round(apos[1]*CELL)-1, 'alien_aura', 5, ('alien',))
        adx, ady = shift('alien', (clock // 2) % 2 == 1)           # the visitor bobs on the off beat to the host
        if hit: adx += 1 if clock % 2 else -1                      # and shudders when a guard lands a hit
        if hops.get('alien'): self._put_px(blank(4, 1, BLK), self.ox+round(apos[0]*CELL)+1, self.oy+round(apos[1]*CELL)+5, 'alien_shadow', 3, ('effect',))
        self._put_px(face, self.ox+round(apos[0]*CELL)+adx, self.oy+round(apos[1]*CELL)+ady, 'alien', 6, ('alien',))
        sx=self.ox+round(apos[0]*CELL)-self.camera.x
        sy=self.oy+round(apos[1]*CELL)-self.camera.y
        gx, gy = self.ox+round(apos[0]*CELL), self.oy+round(apos[1]*CELL)
        if sx<0 or sy<0 or sx+CELL>64 or sy+CELL>64:
            ex=max(1,min(57,sx)); ey=max(1,min(57,sy))
            gx, gy = self.camera.x+ex, self.camera.y+ey
            self._dynamic.append(self._sprite(face,gx+adx,gy+ady,'alien_edge',9,('alien',)))
            if hit:
                self._dynamic.append(self._sprite(impact_burst(clock),self.camera.x+ex-1,self.camera.y+ey-1,'alien_edge_hit',10,('effect',)))
        cheering = any(isinstance(e[0], str) and e[0] in ('wipe', 'cheer') for e in effects)
        for i,p in enumerate(self.people):
            pos=positions.get(i,p['pos']) if positions else p['pos']
            # expressions: everyone winces when the run is lost, the infected cheer when the level is won, and people
            # blink now and then, each on their own beat
            mood = 'wince' if lose else 'cheer' if (cheering and p['infected']) else 'blink' if (clock // 4 + i * 3) % 11 == 0 else None
            if mood != 'cheer' and p['pos'] in flinches: mood = 'wince'   # a person a spray only half-caught flinches
            if p.get('hostile') and not p['infected']:
                face=hostile_art(p['dir'],p['windup'],p['exposure'],ink,mood)
            elif p['doctor'] and not p['infected']:
                face=doctor_art(p['dir'],p['exposure'],bool(p.get('build_target') or p.get('heal_target') is not None),ink,mood)
            else:
                face=civilian_art(p['dir'],i,p['infected'],self.control==i,p['exposure'],bool(p.get('cough')),ink,mood)
            if i in lands: face = squashed(face)
            lift = 1 if (mood == 'cheer' and clock % 2) else 0       # the cheering hop up and down
            if p.get('windup') and idle: lift = 1 if clock % 2 else 0   # an angry guard stamps its feet while winding up
            pdx, pdy = shift(i, (clock // 2 + i) % 2 == 0)
            if hops.get(i): self._put_px(blank(4, 1, BLK), self.ox+round(pos[0]*CELL)+1, self.oy+round(pos[1]*CELL)+5, f'shadow_{i}', 3, ('effect',))
            self._put_px(face,self.ox+round(pos[0]*CELL)+pdx,self.oy+round(pos[1]*CELL)-lift+pdy,f'person_{i}',6,('person',))
            if mood == 'cheer':                                      # and throw a sparkle over their heads
                self._put_px(STAR5 if clock % 2 else PLUS5,self.ox+round(pos[0]*CELL)+1,self.oy+round(pos[1]*CELL)-6,f'cheer_spark_{i}',8,('effect',))
            if self.control==i:
                x,y=pos
                self._put_px(host_ring(clock // 2),self.ox+round(x*CELL)-1,self.oy+round(y*CELL)-1,f'host_ring_{i}',7,('marker',))
            if self.control==i and self.level_index>0:
                x,y=pos
                self._put_px(spore_pips(self.supply),self.ox+round(x*CELL)-2,self.oy+round(y*CELL),f'spores_{i}',8,('hud',))
        for i,pos in enumerate(effects):
            if isinstance(pos[0],str) and pos[0]=='impact':
                x,y=pos[1]
                self._put_px(impact_burst(clock+i),self.ox+round(x*CELL)-1,self.oy+round(y*CELL)-1,f'impact_{i}',10,('effect',))
            elif isinstance(pos[0],str) and pos[0]=='refuse':
                self._put(refuse_marks(),pos[1],f'refused_{i}',10,('effect',))
            elif isinstance(pos[0],str) and pos[0]=='wipe':
                self._dynamic.append(self._sprite(wipe_art(pos[1],clock),self.camera.x,self.camera.y,'level_wipe',30,('effect',)))
                self._shower(pos[2])
            elif isinstance(pos[0],str) and pos[0]=='reveal':
                face=[row[::-1] for row in wipe_art(pos[1],clock)]   # the same sweep, mirrored, leaving to the right
                self._dynamic.append(self._sprite(face,self.camera.x+64-pos[1],self.camera.y,'level_reveal',30,('effect',)))
            elif isinstance(pos[0],str) and pos[0]=='cheer':
                self._shower(pos[1])
            elif isinstance(pos[0],str) and pos[0]=='lose':
                pass                                        # handled below, once, after everything else is placed
            elif isinstance(pos[0],str) and pos[0] in MOTION_TAGS:
                if pos[0] == 'pop':                         # sparks around a cell: an infection, a cure, a barricade, a switch
                    x,y=pos[1]
                    self._put_px(pop_burst(pos[2]),self.ox+round(x*CELL)-2,self.oy+round(y*CELL)-2,f'pop_{i}',11,('effect',))
                elif pos[0] == 'dust':                      # the cloud behind a mover
                    x,y=pos[1]
                    px,dx,dy=dust_art(pos[2],th.get('dust',WHT))
                    self._put_px(px,self.ox+round(x*CELL)+dx,self.oy+round(y*CELL)+dy,f'dust_{i}',3,('effect',))
                elif pos[0] == 'bump':                      # the star where a blocked step hit
                    x,y=pos[1]; dx,dy=pos[2]
                    star=bonk_art(pos[3])
                    cx=self.ox+x*CELL+3+dx*4-len(star[0])//2
                    cy=self.oy+y*CELL+3+dy*4-len(star)//2
                    self._put_px(star,cx,cy,f'bonk_{i}',11,('effect',))
            else:
                self._put(droplet(clock + i),pos,f'droplet_{i}',10,('effect',))
        if beam:
            (x0,y0),(x1,y1)=beam[:2]
            colour=beam[2] if len(beam)>2 else 10
            x0,y0=self.ox+x0*CELL+3, self.oy+y0*CELL+3
            x1,y1=self.ox+x1*CELL+3, self.oy+y1*CELL+3
            steps=max(abs(x1-x0),abs(y1-y0))
            for n in range(2,steps,3):
                x=x0+(x1-x0)*n//steps; y=y0+(y1-y0)*n//steps
                core = WHT if (n // 3 + clock) % 2 else YEL
                self._dynamic.append(self._sprite([[colour,colour],[colour,core]],x,y,f'beam_{n}',10,('effect',)))
        if lose:
            self._dynamic.append(self._sprite(lose_tint(lose),self.camera.x,self.camera.y,'defeat_tint',18,('effect',)))
            if dead:
                self._dynamic.append(self._sprite(ghost_art(lose),gx,gy - lose,'alien_ghost',19,('effect',)))
                for k in range(3):                              # dizzy stars circle the ghost's head
                    a = lose * 1.3 + k * 2.0944
                    self._dynamic.append(self._sprite(DIZZY,gx + 2 + round(7 * cos(a)),gy - lose - 2 + round(2 * sin(a)),f'dizzy_{k}',20,('effect',)))

    def _shower(self, frame):
        """The level-clear confetti, drawn over everything in window pixels (so it falls through the whole picture)."""
        for k, (px, x, y) in enumerate(confetti(frame)):
            self._dynamic.append(self._sprite(px,self.camera.x + x,self.camera.y + y,f'confetti_{k}',31,('effect',)))

    # ---------------- rules (unchanged from es01) ----------------
    def _occupied(self, pos, except_alien=False):
        return ((not except_alien and self.alien['pos']==pos) or
                any(p['pos']==pos for p in self.people))

    def _blocked(self,pos,except_alien=False):
        x,y=pos
        return not (0<=x<self.width and 0<=y<self.height) or pos in self.walls or pos in self.vents or pos in self.medical or self._occupied(pos,except_alien)

    def _snapshot(self):
        return (deepcopy(self.people), deepcopy(self.medical), self.control, deepcopy(self.alien), self.supply)

    def _draw_snapshot(self, snapshot, effects=(), beam=None, positions=None):
        current=(self.people,self.medical,self.control,self.alien,self.supply)
        self.people,self.medical,self.control,self.alien,self.supply=deepcopy(snapshot)
        self._follow(positions)
        self._draw(positions=positions,effects=effects,beam=beam)
        self.people,self.medical,self.control,self.alien,self.supply=current

    def _follow(self, positions=None):
        actor = self.alien if self.control is None else self.people[self.control]
        key = 'alien' if self.control is None else self.control
        x,y = positions.get(key, actor['pos']) if positions else actor['pos']
        self.camera.x = max(0,min(max(0,self.ox+self.width*CELL+1-64),round(self.ox+x*CELL+3-32)))
        self.camera.y = max(0,min(max(0,self.oy+self.height*CELL+1-64),round(self.oy+y*CELL+3-32)))

    def _spray(self, origin, heading, strength, chain=True):
        queue=[(origin, heading, strength, chain)]
        effects=[]
        while queue:
            prior=self._snapshot()
            wave=[]
            newly=[]; glanced=[]                  # drawing notes only: who just caught it, who was only splashed
            (x,y),(dx,dy),power,can_chain=queue.pop(0)
            side=(-dy,dx)
            touched_walls=set()
            for sideways in (-1,0,1):
                vx,vy=dx+side[0]*sideways,dy+side[1]*sideways
                previous=(x,y)
                for n in range(1,4):
                    pos=(x+vx*n,y+vy*n)
                    if not (0<=pos[0]<self.width and 0<=pos[1]<self.height): break
                    if vx and vy:
                        corners=((previous[0]+vx,previous[1]),(previous[0],previous[1]+vy))
                        if all(c in self.walls or c in self.medical for c in corners): break
                    if pos in self.walls: break
                    if pos in self.medical:
                        if power==3 and pos not in touched_walls:
                            self.medical[pos]-=1
                            touched_walls.add(pos)
                            if self.medical[pos]<=0: del self.medical[pos]
                        wave.append(pos);effects.append(pos);break
                    wave.append(pos);effects.append(pos)
                    hit=next((i for i,p in enumerate(self.people) if p['pos']==pos),None)
                    if hit is not None:
                        p=self.people[hit]
                        if not p['infected']:
                            p['exposure']=min(3,p['exposure']+power)
                            if p['exposure']<3: glanced.append(pos)
                            if p['exposure']>=3:
                                newly.append(pos)
                                p['infected']=True
                                p['dir']=heading
                                self.supply=min(3,self.supply+1)
                                if self.control is None: self.control=hit
                                elif can_chain: queue.append((pos,heading,3,True))
                        break
                    previous=pos
            sneezer='alien' if self.alien['pos']==(x,y) else next((i for i,q in enumerate(self.people) if q['pos']==(x,y)),None)
            wave.extend(('flinch',c) for c in glanced)
            if sneezer is not None: wave.append(('nudge',sneezer,-dx,-dy))        # the sneezer's head snaps back
            self._events.append((prior,wave,None))
            if newly: self._events.append((self._snapshot(),[('pop',c,'infect') for c in newly],None))
        return effects

    def _alien_turn(self):
        if self.control is None: return []
        ax,ay=self.alien['pos']
        hx,hy=self.people[self.control]['pos']
        if self.tick % 2 and abs(ax-hx)+abs(ay-hy)<=3: return []
        tether=4
        available=[p for p in self.people if not p['infected']]
        if not available: return []
        available.sort(key=lambda p:(abs(p['pos'][0]-ax)+abs(p['pos'][1]-ay),p['pos'][1],p['pos'][0]))
        for target in available:
            if abs(ax-hx)+abs(ay-hy)>tether: break
            tx,ty=target['pos']
            if ax==tx or ay==ty:
                d=((tx>ax)-(tx<ax),(ty>ay)-(ty<ay))
                distance=abs(tx-ax)+abs(ty-ay)
                if distance<=3 and all((ax+d[0]*n,ay+d[1]*n) not in self.walls and (ax+d[0]*n,ay+d[1]*n) not in self.medical and not any(p['pos']==(ax+d[0]*n,ay+d[1]*n) for p in self.people) for n in range(1,distance)):
                    self.alien['dir']=d
                    return self._spray((ax,ay),d,1)
        targets={p['pos'] for p in available}
        if abs(ax-hx)+abs(ay-hy)>=tether:
            targets={(hx,hy)}
        blocked=self.walls | self.vents | set(self.medical) | {p['pos'] for p in self.people}
        start=(ax,ay)
        queue=deque([start]); first={start:None}; choice=None
        while queue and choice is None:
            cell=queue.popleft()
            if cell!=start and any((cell[0]+d[0],cell[1]+d[1]) in targets for d in DIRS.values()):
                choice=first[cell]; break
            for direction in DIRS.values():
                dest=(cell[0]+direction[0],cell[1]+direction[1])
                if (0<=dest[0]<self.width and 0<=dest[1]<self.height and
                        (abs(dest[0]-hx)+abs(dest[1]-hy)<=tether or abs(ax-hx)+abs(ay-hy)>=tether) and
                        dest not in blocked and dest not in first):
                    first[dest]=direction if cell==start else first[cell]
                    queue.append(dest)
        if choice:
            self.alien['pos']=(ax+choice[0],ay+choice[1])
            self.alien['dir']=choice
        return []

    def _infected_turn(self):
        if self.control is None or self.tick % 4: return
        pending=self.cough_pending
        if pending is not None:
            self.cough_pending=None
            p=self.people[pending]
            if p['infected'] and pending!=self.control:
                p['cough']=False
                self._spray(p['pos'],p['dir'],1,False)
            return
        cases=[(i,p) for i,p in enumerate(self.people) if p['infected'] and i!=self.control]
        targets=[p for p in self.people if not p['infected']]
        if not cases or not targets: return
        i,p=cases[(self.tick//4)%len(cases)]
        target=min(targets,key=lambda q:abs(q['pos'][0]-p['pos'][0])+abs(q['pos'][1]-p['pos'][1]))
        dx=target['pos'][0]-p['pos'][0];dy=target['pos'][1]-p['pos'][1]
        p['dir']=((1 if dx>0 else -1),0) if abs(dx)>=abs(dy) else (0,(1 if dy>0 else -1))
        p['cough']=True
        self.cough_pending=i
        self._events.append((self._snapshot(),[],None))

    def _hostile_turn(self):
        if self.level_index==0 or self.tick % 3: return
        ax,ay=self.alien['pos']
        for p in self.people:
            if not p.get('hostile') or p['infected']: continue
            x,y=p['pos']
            distance=abs(x-ax)+abs(y-ay)
            direction=((ax>x)-(ax<x),(ay>y)-(ay<y))
            line=(x==ax or y==ay) and 0<distance<=10
            if line:
                line=all((x+direction[0]*n,y+direction[1]*n) not in self.walls and
                         (x+direction[0]*n,y+direction[1]*n) not in self.medical and
                         not any(q is not p and q['pos']==(x+direction[0]*n,y+direction[1]*n) for q in self.people)
                         for n in range(1,distance))
            if line:
                if not p['windup']:
                    p['windup']=True
                    p['dir']=direction
                    self._events.append((self._snapshot(),[],(p['pos'],self.alien['pos'],8)))
                else:
                    before=self._snapshot()
                    self._events.extend([(before,[('impact',self.alien['pos'])],(p['pos'],self.alien['pos'],8))]*2)
                    p['windup']=False
                    self.alien['damage']+=1
                    self._events.append((self._snapshot(),[],None))
                    if self.alien['damage']>=26:
                        self._result_lost=True
                        return
                continue
            p['windup']=False
            directions=sorted(DIRS.values(),key=lambda d:abs(x+d[0]-ax)+abs(y+d[1]-ay))
            for dx,dy in directions:
                dest=(x+dx,y+dy)
                if not self._blocked(dest):
                    p['pos']=dest
                    p['dir']=(dx,dy)
                    break

    def _civilian_turn(self):
        if self.level_index==0: return
        for i,p in enumerate(self.people):
            if i==self.control or p.get('hostile') or p.get('doctor') or p.get('cough') or p.get('anchored'): continue
            if (self.tick+i*2)%8: continue
            axis=(1,0) if i%2 else (0,1)
            sign=p.get('walk_sign',1)
            x,y=p['pos']; dest=(x+axis[0]*sign,y+axis[1]*sign)
            if self._blocked(dest):
                sign=-sign
                dest=(x+axis[0]*sign,y+axis[1]*sign)
            p['walk_sign']=sign
            if not self._blocked(dest):
                p['pos']=dest
                p['dir']=(axis[0]*sign,axis[1]*sign)

    def _doctor_step_towards(self, doctor, goals):
        start=doctor['pos']; blocked=self.walls|self.vents|set(self.medical)|{self.alien['pos']}
        blocked|={p['pos'] for p in self.people if p is not doctor}
        queue=deque([start]); first={start:None}
        while queue:
            cell=queue.popleft()
            if any(abs(cell[0]-x)+abs(cell[1]-y)==1 for x,y in goals):
                return first[cell]
            for d in DIRS.values():
                nxt=(cell[0]+d[0],cell[1]+d[1])
                if (0<=nxt[0]<self.width and 0<=nxt[1]<self.height and
                        nxt not in blocked and nxt not in first):
                    first[nxt]=d if cell==start else first[cell]
                    queue.append(nxt)
        return None

    def _doctor_turn(self):
        if self.level_index==0 or self.tick%5: return
        spec=LEVELS_SPEC[self.level_index]
        for doctor in self.people:
            if not doctor.get('doctor') or doctor['infected']: continue
            x,y=doctor['pos']
            cases=[(i,p) for i,p in enumerate(self.people) if p['infected']]
            choices=[pos for pos in spec['build'] if pos not in self.walls and pos not in self.vents and
                     pos not in self.medical and not self._occupied(pos)]
            nearest=min(cases,key=lambda v:(abs(v[1]['pos'][0]-x)+abs(v[1]['pos'][1]-y),v[0])) if cases else None
            case_near=nearest and abs(nearest[1]['pos'][0]-x)+abs(nearest[1]['pos'][1]-y)<=3
            if nearest and (case_near or not choices):
                i,patient=nearest
                px,py=patient['pos']; dist=abs(px-x)+abs(py-y)
                doctor['build_target']=None
                if dist==1:
                    if doctor.get('heal_primed')!=i:
                        doctor['heal_primed']=i
                        doctor['heal_target']=i
                        self._events.append((self._snapshot(),[],(doctor['pos'],patient['pos'])))
                    else:
                        before=self._snapshot()
                        self._events.extend([(before,[],(doctor['pos'],patient['pos']))]*2)
                        patient['infected']=False;patient['exposure']=0;patient['cough']=False
                        if self.cough_pending==i:self.cough_pending=None
                        if self.control==i:self.control=None
                        doctor['heal_target']=None
                        doctor['heal_primed']=None
                        self._events.append((self._snapshot(),[('pop',patient['pos'],'heal')],None))
                    continue
                doctor['heal_target']=i
                doctor['heal_primed']=None
                direction=self._doctor_step_towards(doctor,{patient['pos']})
                if direction:
                    doctor['pos']=(x+direction[0],y+direction[1]);doctor['dir']=direction
                continue
            doctor['heal_target']=None
            doctor['heal_primed']=None
            if not choices:
                doctor['build_target']=None
                continue
            ax,ay=self.alien['pos']
            target=doctor.get('build_target')
            if target not in choices:
                target=min(choices,key=lambda q:(abs(q[0]-ax)+abs(q[1]-ay)+abs(q[0]-x)+abs(q[1]-y), abs(q[0]-x)+abs(q[1]-y)))
            doctor['build_target']=target
            dist=abs(target[0]-x)+abs(target[1]-y)
            if dist==1:
                self.medical[target]=2
                doctor['build_target']=None
                self._events.append((self._snapshot(),[('pop',target,'build')],(doctor['pos'],target)))
            else:
                direction=self._doctor_step_towards(doctor,{target})
                if direction:
                    doctor['pos']=(x+direction[0],y+direction[1]);doctor['dir']=direction

    def _switch_host(self, selected, origin):
        self.control = selected
        if self.cough_pending == selected:
            self.cough_pending = None
            self.people[selected]['cough'] = False
        self._events.append((self._snapshot(), [('pop', self.people[selected]['pos'], 'host')], (origin, self.people[selected]['pos'], 14)))

    def _host_beyond_grille(self, grille, direction):
        dx, dy = direction
        for distance in (1, 2):
            pos = (grille[0] + dx * distance, grille[1] + dy * distance)
            if not (0 <= pos[0] < self.width and 0 <= pos[1] < self.height):
                break
            if pos in self.walls or pos in self.medical or pos in self.vents:
                break
            person = next((i for i, p in enumerate(self.people) if p['pos'] == pos), None)
            if person is not None:
                return person if self.people[person]['infected'] else None
        return None

    def step(self):
        if self.action.id==GameAction.RESET:
            self.complete_action()
            return
        if self._revealing:                                  # the new level is uncovered as the green sweep slides away
            if self._reveal:
                self._draw(effects=[('reveal',self._reveal.pop(0))])
                return
            self._revealing=False
            self._draw()
            self.complete_action()
            return
        if self._phase:
            if self._frames:
                snapshot,effects,beam,positions=self._frames.pop(0)
                self._draw_snapshot(snapshot,effects,beam,positions)
                return
            self._phase=0
            # the resting picture; after a lost run it keeps the red wash and the ghost
            if self._result_won:
                self._draw(effects=[('wipe',64,9)])
                if not self.is_last_level():                  # the engine loads the next level after this frame; keep the
                    self._reveal=[40,20,6]                    # action open so the sweep can slide off and uncover it
                    self._revealing=True
                    self.next_level()
                    return
                self.next_level()                             # the last level: the sweep simply stays
            else:
                self._draw(effects=[('lose',3)] if self._result_lost else ())
            if self._result_lost:
                self.lose()
            self.complete_action()
            return
        action=self.action.id.value if hasattr(self.action.id,'value') else self.action.id
        if action not in (1,2,3,4,5,6):
            self.complete_action()
            return
        self.tick += 1
        self._events=[]
        start_alien=self.alien['pos']
        start_people=[p['pos'] for p in self.people]
        bump=None                                            # drawing note: a step that ran into something
        actor=self.alien if self.control is None else self.people[self.control]
        if action==6:
            available=[i for i,p in enumerate(self.people) if p['infected'] and
                       0<=self.ox+p['pos'][0]*CELL-self.camera.x<64 and
                       0<=self.oy+p['pos'][1]*CELL-self.camera.y<64]
            selected=None
            data=self.action.data or {}
            x=(data.get('x',-100)+self.camera.x-self.ox)//CELL
            y=(data.get('y',-100)+self.camera.y-self.oy)//CELL
            selected=next((i for i in available if self.people[i]['pos']==(x,y)),None)
            if selected is not None:
                if selected != self.control:
                    self._switch_host(selected, actor['pos'])
            else:
                self._events.append((self._snapshot(),[('refuse',actor['pos'])],None))
        elif action in DIRS:
            direction=DIRS[action]
            actor['dir']=direction
            x,y=actor['pos']
            pos=(x+direction[0],y+direction[1])
            if pos in self.vents and self.control is not None:
                selected = self._host_beyond_grille(pos, direction)
                if selected is not None:
                    self._switch_host(selected, actor['pos'])
                else:
                    self._events.append((self._snapshot(), [('refuse', pos)], None))
            elif not self._blocked(pos, actor is self.alien): actor['pos']=pos
            else: bump=('alien' if actor is self.alien else self.control, x, y, direction)
        else:
            if self.control is None or self.supply>0:
                if self.control is not None and self.level_index>0:self.supply-=1
                self._spray(actor['pos'],actor['dir'],1 if self.control is None else 3)
            else:
                self._events.append((self._snapshot(),[('refuse',actor['pos'])],None))
        motion_snapshot=self._snapshot()
        if self.level_index>0:
            self._alien_turn()
            self._infected_turn()
            self._hostile_turn()
            self._civilian_turn()
            self._doctor_turn()
        target=LEVELS_SPEC[self.level_index].get('goal',len(self.people))
        self._result_won=not self._result_lost and sum(p['infected'] for p in self.people)>=target
        motion=[]
        ends=[p['pos'] for p in self.people]
        if bump:                                             # a blocked step: shove into the obstacle, a star, then recoil
            key,bx,by,(ddx,ddy)=bump
            motion.append((motion_snapshot,[('nudge',key,2*ddx,2*ddy),('bump',(bx,by),(ddx,ddy),0)],None,None))
            motion.append((motion_snapshot,[('nudge',key,-ddx,-ddy),('bump',(bx,by),(ddx,ddy),1)],None,None))
        moved=[]
        if start_alien!=self.alien['pos'] or start_people!=ends:
            starts={'alien':start_alien}; finals={'alien':self.alien['pos']}
            for i in range(len(ends)): starts[i]=start_people[i]; finals[i]=ends[i]
            moved=[k for k in starts if starts[k]!=finals[k]]
            lead=[k for k in ('alien',self.control) if k in moved]       # the visitor and the host kick up dust
            for frame in (1,2,3):
                positions={k:(tween(starts[k][0]*CELL,finals[k][0]*CELL,frame,4)/CELL,
                              tween(starts[k][1]*CELL,finals[k][1]*CELL,frame,4)/CELL) for k in moved}
                notes=[('hop',k,(1,2,1)[frame-1] if k in lead else (0,1,0)[frame-1]) for k in moved]
                notes+=[('dust',starts[k],frame) for k in lead]
                motion.append((motion_snapshot,notes,None,positions))
        self._frames=motion+[(snap,list(effects)+[('idle',)],beam,None) for snap,effects,beam in self._events]
        self._frames+=[(self._snapshot(),[('land',k) for k in moved],None,None),(self._snapshot(),[],None,None)]
        if self._result_won:
            self._frames.extend((self._snapshot(),[('cheer', f)],None,None) for f in (1,3))
            self._frames.extend((self._snapshot(),[('wipe', width, f)],None,None)
                                for f, width in zip((4,7), (24,48)))
        if self._result_lost:                               # the run is over: the red wash creeps in, the ghost rises
            self._frames.extend((self._snapshot(),[('lose', k)],None,None) for k in (1,2,3))
        self._phase=1
        snapshot,effects,beam,positions=self._frames.pop(0)
        self._draw_snapshot(snapshot,effects,beam,positions)
