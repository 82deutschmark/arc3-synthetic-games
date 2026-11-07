# Author: Claude Sonnet 5.5
# Date: 07-November-2026
# PURPOSE: se02 redraws se01 (Shrine Exploration: a hooded pilgrim crosses a scrolling world, lights four shrines to
#          melt the coloured seal gates, dodges thorn bramble and horned patrols, and reaches the sanctum before the
#          move counter drains). THE RULES ARE UNCHANGED: the map, the six levels' seals, patrols and move budgets, the
#          four move inputs, what a thorn, a patrol or an empty counter does, and the draining-bar counter are se01's,
#          copied line for line. Only the art is new: every level is its own season and place (meadow, autumn, snow,
#          night, dune, twilight swamp) with its own ground, forest, trees, ponds, props, shrine houses and drifting
#          life; the pilgrim and the patrols are drawn as named creature sprite sheets with faces and a walk cycle; the
#          braziers, seal gates, portal and flags are live sprites; a lit shrine throws sparks and a melting seal
#          crumbles into sparkles; reaching the sanctum bursts into stars; a lost run turns the world red and dim and
#          leaves the pilgrim collapsed with spiral eyes. No letter, digit or word is drawn anywhere.
# SRP/DRY check: Pass. Parts: (1) palette and sprite helpers, (2) the six themes, (3) sprite sheets, (4) se01's
#          rules and map, unchanged, (5) the pre-drawn world pictures, one per theme, (6) the camera window that draws
#          live sprites over the world cut-out, (7) the game class, whose rule code is se01's. Nothing here is shared
#          with another game; the art never feeds a rule.
# CHANGELOG
# 07-Nov-2026 (Claude Sonnet 5.5): se02, art pass 4 (polish and check): every level opening, a walk, a win, a loss and the
#   first frame after RESET were rendered and read; a dead variable removed (pyflakes clean); rules checked against se01 by
#   random play, including from each later level. No rule or picture change needed.
# 07-Nov-2026 (Claude Sonnet 5.5): se02, art pass 3 (variety and life): every season gets its own forest-floor and path
#   texture, tree colour variants (night pines no longer one blue mass, the dunes thinned), shaded bigger props built
#   from sprites (nine by ten, drawn under seals and thorns so they never hide a gate), swaying flora and a small
#   critter per season (bunny, fox, penguin, bat, lizard, axolotl), pond pets and rocks, a second drifting-life kind per
#   season, flickering house windows and chimney smoke, a confetti shower on a cleared level and a drawn run-over
#   (rain cloud, drooping trees, dark vignette). Rules untouched.
# 07-Nov-2026 (Claude Sonnet 5.5): se02, art pass 2 (critique and redraw): live swaying trees with new shapes (maple, dead,
#   willow, mushroom, palm, saguaro), bigger irregular ponds, per-theme house pictures with arched doorways, themed floor
#   decals, tidier pebbles, two prop kinds per theme, blinking/wincing/cheering pilgrim, a gloating catching patrol and
#   waking thorns. Rules untouched.
# 07-Nov-2026 (Claude Sonnet 5.5): se02, art pass 1 of se01. Six themed worlds, creature sprite sheets, themed shrine
#   houses, live braziers, seals, portal, flags, ambient life, win and loss looks. Rules identical to se01.

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

# ===================================================================================================================
# PART ONE: palette and sprite helpers
# ===================================================================================================================
# Palette names used by the art. Colours 1-4 are greys and are never used.
WHT, BLK, MAG, PNK, RED, BLU, LBL, YEL, ORG, MAR, GRN, PUR = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
LEGEND = dict(k=BLK, w=WHT, m=MAR, o=ORG, y=YEL, g=GRN, b=BLU, l=LBL, p=PNK, c=MAG, r=RED, u=PUR)


def art(rows, legend=None) -> np.ndarray:
    """Draw a sprite from text rows: '.' is see-through, a letter is a palette colour (extras via `legend`)."""
    table = dict(LEGEND, **(legend or {}))
    width = len(rows[0])
    out = np.full((len(rows), width), -1, dtype=np.int16)
    for y, row in enumerate(rows):
        assert len(row) == width, f"ragged sprite row {y}: {row!r}"
        for x, ch in enumerate(row):
            if ch != ".":
                out[y, x] = table[ch]
    return out


def blit(dst: np.ndarray, x: int, y: int, spr: np.ndarray) -> None:
    """Put a sprite on a picture at (x, y), clipped, skipping its see-through pixels."""
    h, w = spr.shape
    H, W = dst.shape
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    sub = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    mask = sub >= 0
    dst[y0:y1, x0:x1][mask] = sub[mask]


def flip(spr: np.ndarray) -> np.ndarray:
    return spr[:, ::-1].copy()


def dot(frame: np.ndarray, x: int, y: int, colour: int) -> None:
    """One clipped pixel."""
    if 0 <= y < frame.shape[0] and 0 <= x < frame.shape[1]:
        frame[y, x] = colour


def disc(w: int, h: int, fill: int, line: int = BLK, hi=None, lo=None) -> np.ndarray:
    """A round body, w by h: a one-pixel outline, a flat fill, a lit patch up-left and a shade crescent down-right
    (flat colours only, so it keeps the early-console look). The building block of the props and creatures."""
    s = np.full((h, w), -1, dtype=np.int16)
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = (w - 1) / 2, (h - 1) / 2
    s[((xx - cx) / (w / 2)) ** 2 + ((yy - cy) / (h / 2)) ** 2 <= 1.0] = line
    inner = ((xx - cx) / max(0.5, (w - 2) / 2)) ** 2 + ((yy - cy) / max(0.5, (h - 2) / 2)) ** 2 <= 1.0
    s[inner] = fill
    lean = (xx - cx) * 0.7 + (yy - cy) * 1.1
    if hi is not None:
        s[inner & (lean < -h * 0.42)] = hi
    if lo is not None:
        s[inner & (lean > h * 0.42)] = lo
    return s


def put(s: np.ndarray, colour: int, *points) -> None:
    """Set the listed (x, y) pixels of a sprite, ignoring any that fall outside it."""
    for x, y in points:
        if 0 <= y < s.shape[0] and 0 <= x < s.shape[1]:
            s[y, x] = colour


def centre(rows, width: int):
    """Pad hand-drawn rows with see-through pixels so the picture sits in the middle of `width`."""
    return tuple(r.center(width, ".") for r in rows)


def _hash(x: int, y: int, salt: int) -> int:
    n = (x * 73856093) ^ (y * 19349663) ^ (salt * 83492791)
    n = (n ^ (n >> 13)) & 0xFFFFFFFF
    n = (n * 1274126177) & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFFFFFFFF


# ===================================================================================================================
# PART TWO: the six themes. One per level; each is a season or a place with its own ground, forest, trees, pond, props,
# house and mood.
# ===================================================================================================================
# path/path_lo/path_hi/speck : the walkable ground, its cast shadow, its lit lip, its pebbles
# base/base_lo/base_hi/rim   : the forest floor, its dark flecks, its lit lip and the outline where forest meets path
# t0, t1                     : letter -> colour tables of the theme's two tree shapes (see SHAPES for the letters)
# pond                       : water, deep, hi (the ripple), shore, plant, bloom
# slab/joint, wall, roof     : the shrine floor, its brick wall (face, shade, light) and its roof (tile, shade, ridge)
# glow                       : the accent of banners, sparks, the dais and the sanctum
# life, props, decor, house  : the drifting ambient creature, the two prop kinds, the floor decals, the house style
THEMES = [
    dict(name="meadow", path=YEL, path_lo=ORG, path_hi=WHT, speck=ORG, base=GRN, base_lo=BLK, base_hi=YEL, rim=BLK,
         t0=dict(k=BLK, a=GRN, h=YEL, d=BLK, e=PNK, f=WHT, t=MAR, u=BLK),
         t1=dict(k=BLK, a=GRN, h=LBL, d=BLK, e=WHT, f=YEL, t=MAR, u=BLK), trees=("oak", "pine"),
         pond=dict(water=BLU, deep=PUR, hi=LBL, shore=YEL, plant=GRN, bloom=PNK),
         slab=WHT, joint=YEL, wall=(ORG, MAR, WHT), roof=(RED, MAR, PNK), glow=PNK, life="butterfly",
         props=("flower", "hive"), decor=("flower", "clover", "tuft"), house=0),
    dict(name="autumn", path=ORG, path_lo=MAR, path_hi=YEL, speck=RED, base=MAR, base_lo=BLK, base_hi=ORG, rim=BLK,
         t0=dict(k=BLK, a=ORG, h=YEL, d=RED, e=RED, f=YEL, t=BLK, u=BLK),
         t1=dict(k=BLK, a=GRN, h=YEL, d=BLK, e=ORG, f=YEL, t=BLK, u=MAR), trees=("maple", "pine"),
         pond=dict(water=BLU, deep=PUR, hi=LBL, shore=ORG, plant=GRN, bloom=YEL),
         slab=YEL, joint=ORG, wall=(YEL, ORG, WHT), roof=(ORG, RED, YEL), glow=YEL, life="leaf",
         props=("pumpkin", "toadstool"), decor=("leaves", "acorn", "toadstool"), house=1),
    dict(name="snow", path=WHT, path_lo=LBL, path_hi=LBL, speck=BLU, base=LBL, base_lo=BLU, base_hi=WHT, rim=BLU,
         t0=dict(k=BLK, a=GRN, h=WHT, d=BLK, e=WHT, f=LBL, t=MAR, u=BLK),
         t1=dict(k=BLK, a=MAR, h=WHT, d=BLK, e=YEL, f=WHT, t=MAR, u=BLK, y=YEL), trees=("pine", "dead"),
         pond=dict(water=LBL, deep=BLU, hi=WHT, shore=WHT, plant=LBL, bloom=WHT),
         slab=LBL, joint=BLU, wall=(MAR, BLK, LBL), roof=(WHT, LBL, BLU), glow=LBL, life="snow",
         props=("snowman", "igloo"), decor=("drift", "frostflower", "icicle"), house=2),
    dict(name="night", path=MAR, path_lo=BLK, path_hi=RED, speck=ORG, base=BLK, base_lo=BLU, base_hi=PUR, rim=BLU,
         t0=dict(k=BLK, a=BLU, h=LBL, d=PUR, e=YEL, f=WHT, t=MAR, u=BLK),
         t1=dict(k=PUR, a=MAR, h=PNK, d=BLK, e=YEL, f=WHT, t=PUR, u=BLK, y=YEL), trees=("pine", "dead"),
         pond=dict(water=BLU, deep=BLK, hi=WHT, shore=PUR, plant=PUR, bloom=LBL),
         slab=PUR, joint=BLU, wall=(PUR, BLK, MAG), roof=(BLU, BLK, LBL), glow=LBL, life="firefly",
         props=("crystal", "owl"), decor=("crystalbit", "glowcap", "star"), house=3),
    dict(name="dune", path=YEL, path_lo=ORG, path_hi=WHT, speck=ORG, base=ORG, base_lo=RED, base_hi=YEL, rim=MAR,
         t0=dict(k=BLK, a=GRN, h=YEL, d=BLK, e=MAR, f=ORG, t=MAR, u=BLK),
         t1=dict(k=BLK, a=GRN, h=YEL, d=BLK, e=PNK, f=WHT, t=GRN, u=BLK), trees=("palm", "cactus"),
         pond=dict(water=BLU, deep=PUR, hi=LBL, shore=GRN, plant=GRN, bloom=PNK),
         slab=WHT, joint=ORG, wall=(WHT, ORG, LBL), roof=(MAR, BLK, RED), glow=ORG, life="spark",
         props=("barrel", "cairn"), decor=("pebbles", "sprout", "ripple"), house=4),
    dict(name="swamp", path=GRN, path_lo=BLK, path_hi=YEL, speck=BLK, base=PUR, base_lo=BLK, base_hi=MAG, rim=BLK,
         t0=dict(k=BLK, a=GRN, h=YEL, d=BLK, e=LBL, f=PNK, t=MAR, u=BLK),
         t1=dict(k=BLK, a=MAG, h=PNK, d=BLK, e=WHT, f=YEL, t=WHT, u=LBL), trees=("willow", "mush"),
         pond=dict(water=GRN, deep=BLK, hi=YEL, shore=BLK, plant=GRN, bloom=PNK),
         slab=LBL, joint=BLU, wall=(LBL, BLU, WHT), roof=(MAG, PUR, YEL), glow=MAG, life="wisp",
         props=("ghost", "frog"), decor=("reed", "bubble", "glowcap"), house=5),
]

# The pass-three additions, one block per theme so the table above stays readable.
# alt      : two colour variants of the trees, each (changes to the first shape's table, changes to the second's)
# thin     : hide every n-th tree (0 keeps them all); decor_rate: one forest cell in n carries a decal
# tex, ptex: the forest-floor and path texture families; acc: the accent colour of the floor texture
# life2    : a second kind of drifting life; confetti: the shower colours of a cleared level
# flora    : the two swaying plants, critter: the little animal of the season, pet: what swims or sits in the ponds
# smoke    : the two colours of a chimney's smoke
EXTRA = dict(
    meadow=dict(alt=((dict(a=GRN, h=WHT, e=RED, f=YEL), dict(a=BLU, h=LBL, e=WHT)),
                     (dict(h=YEL, e=ORG, f=WHT), dict(a=GRN, h=WHT, e=PNK))),
                thin=0, decor_rate=3, tex="grass", ptex="grass", acc=YEL, life2="bee", confetti=(PNK, WHT, YEL, LBL, RED),
                flora=("poppies", "bush"), critter="bunny", pet="duck", smoke=(WHT, LBL)),
    autumn=dict(alt=((dict(a=RED, h=ORG, d=MAR, e=YEL, f=ORG), dict(a=ORG, h=YEL, d=MAR, e=RED)),
                     (dict(a=YEL, h=WHT, d=ORG, e=ORG, f=RED), dict(a=GRN, h=YEL, e=ORG))),
                thin=0, decor_rate=3, tex="leaf", ptex="leaf", acc=RED, life2="gust", confetti=(RED, ORG, YEL, WHT, MAR),
                flora=("leafpile", "stump"), critter="fox", pet="koi", smoke=(WHT, LBL)),
    snow=dict(alt=((dict(a=BLU, h=WHT, e=WHT), dict(t=PUR, y=RED)),
                   (dict(a=GRN, h=LBL, e=RED, f=YEL), dict(t=MAR, y=YEL, u=BLK))),
              thin=0, decor_rate=3, tex="snow", ptex="snow", acc=BLU, life2="glint", confetti=(WHT, LBL, BLU, YEL, WHT),
              flora=("snowbush", "icecrystal"), critter="penguin", pet="glint", smoke=(BLU, LBL)),
    night=dict(alt=((dict(a=PUR, h=LBL, e=WHT), dict(t=MAR, y=RED)),
                    (dict(a=GRN, h=LBL, d=BLU, e=YEL, f=WHT), dict(t=BLU, u=BLK, y=WHT))),
               thin=0, decor_rate=4, tex="star", ptex="night", acc=LBL, life2="twinkle", confetti=(YEL, LBL, WHT, MAG, PUR),
               flora=("glowshroom", "starflower"), critter="bat", pet="stars", smoke=(LBL, WHT)),
    dune=dict(alt=((dict(a=GRN, h=WHT, e=PNK, f=YEL), dict(a=GRN, h=LBL, e=YEL)),
                   (dict(h=LBL, e=RED, f=ORG), dict(a=GRN, h=PNK, e=WHT))),
              thin=3, decor_rate=5, tex="wind", ptex="dune", acc=YEL, life2="dust", confetti=(ORG, YEL, WHT, RED, PNK),
              flora=("grasstuft", "rock"), critter="lizard", pet="dragonfly", smoke=(WHT, LBL)),
    swamp=dict(alt=((dict(a=YEL, h=WHT, d=GRN), dict(a=BLU, h=LBL, e=WHT)),
                    (dict(a=LBL, h=WHT, d=GRN, e=PNK), dict(a=GRN, h=YEL, e=WHT, f=YEL))),
               thin=0, decor_rate=3, tex="murk", ptex="swamp", acc=MAG, life2="bubble", confetti=(MAG, YEL, LBL, GRN, WHT),
               flora=("cattail", "bubblepot"), critter="axolotl", pet="frog", smoke=(LBL, WHT)),
)
for _theme in THEMES:
    _theme.update(EXTRA[_theme["name"]])

# colour pairs used by the shaded sprites: a darker and a lighter cousin of each hue
DARKER = {WHT: LBL, LBL: BLU, BLU: PUR, PNK: MAG, MAG: PUR, RED: MAR, ORG: RED, YEL: ORG, GRN: BLK, PUR: BLK}
LIGHTER = {BLU: LBL, PUR: MAG, MAG: PNK, RED: PNK, ORG: YEL, YEL: WHT, GRN: YEL, PNK: WHT, LBL: WHT}

# ===================================================================================================================
# PART THREE: sprite sheets
# ===================================================================================================================
# ---- trees: ten wide, twelve tall, trunk on the bottom three rows --------------------------------------------------
# Letters: k outline, a main, h light, d dark (laid on as a dither so the shade is soft), e and f little accents
# (blossom, fruit, autumn patches, snow), t trunk, u trunk shade, y glowing eyes on the dead trees.
TREE_H = 12
SHAPES = dict(
    oak=("...kkkk...", ".kkahhakk.", "kahhhaeaak", "kahhaaaaak", "kaaeaaahak", "kaaaaaaadk", "kadaaaddak", ".kddaddkk.",
         "..kkddkk..", "...kttk...", "...ktuk...", "..kttuuk.."),
    oak2=(".kkk..kkk.", "kahhkkhhak", "kahaaaaaak", "kaeaaaaaak", "kaaaaahaak", "kadaaaeadk", "kkddaaddkk", ".kkkddkkk.",
          "...kttk...", "...kttk...", "...ktuk...", "..kttuuk.."),
    maple=("..k.kk.k..", ".kakahkak.", "kahaehhaak", ".kahhaefak", "kaeaaafaak", "kaaahaaadk", ".kadaedadk", "..kddaddk.",
           "...kkddk..", "...kttk...", "...ktuk...", "..kttuuk.."),
    pine=("....kk....", "...kahk...", "..kahhak..", "...kaadk..", "..kahhadk.", ".kahhaaadk", "..kkaaddkk", ".kahhaaadk",
          "kahaaaaadk", "kkkkkddkkk", "...kttk...", "...ktuk..."),
    pine2=("....kk....", "...khak...", "..kahhek..", "...kaadk..", "..kahhadk.", ".kehhaaadk", "..kkaaddkk", ".kahhaeadk",
           "kahaaaaadk", "kkkkkddkkk", "...kttk...", "...kttk..."),
    dead=("k....k..k.", "tk..ktk.tk", ".tk.tt.tk.", "..kttttk..", "k.kttttk.k", "tkkttyttkk", ".tkttttkt.", "..kttdtk..",
          "..kttdtk..", "...kttk...", "...ktuk...", "..kttuuk.."),
    mush=("..kkkkkk..", ".kaahaeak.", "kaeaahaaak", "kahaaaaaek", "kaaaaeaahk", "kddddddddk", ".kkkktkkk.", "...ktuk...",
          "...ktuk...", "...ktuk...", "..kttuuk..", ".kkttuukk."),
    palm=("a..a..a..a", ".aahaahaa.", "aahhaahhaa", ".kaaeeaak.", "..akttka..", "....kttk..", "...ktuk...", "...kttk...",
          "....ktuk..", "...kttuk..", "...kttuk..", "..kttuuk.."),
    cactus=("....kk....", "...kahk...", "...kahk.kk", "kk.kahkkak", "kakkahkkak", "kakkaaakak", "kaakadakak", ".kkkadkkk.",
            "...kadk...", "...kadk...", "...kaadk..", "..kkkkkk.."),
    willow=("..kkkkkk..", ".kahhaahk.", "kahaaaahak", "kaaaaeaaak", "kakaakaakk", "kdkkakdkdk", "kd.kd.kd.k", "k..kd.kd..",
            "...kttk...", "...ktuk...", "...ktuk...", "..kttuuk.."),
)
SHAPES.update(
    maple2=("....kk....", "..kkahkk..", ".kahhaeak.", "kaahaaafak", "kaeaahaaak", ".kaaaaaadk", "kaadaeaadk", ".kkddaddk.",
            "...kkddk..", "...kttk...", "...ktuk...", "..kttuuk.."),
    dead2=("..k.....k.", ".tk..k.tk.", "..tk.tktk.", "...ttkttk.", ".k.kttttk.", "kttkttytk.", ".tkktttk..", "..ktttk...",
           "..kttdk...", "...kttk...", "...ktuk...", "..kttuuk.."),
    willow2=("..kkkkkk..", ".kahaaahk.", "kaaaaaahak", "kahaeaaaak", "kakaakaakk", "kd.kakd.dk", "kd.kd.kd.k", "k..k..kd..",
             "...kttk...", "...ktuk...", "...ktuk...", "..kttuuk.."),
    mush2=("...kkkk...", ".kaahhaak.", "kaeaaaeaak", "kahaaaaahk", "kddddddddk", "..kktuukk.", "...ktuk...", "...ktuk...",
           "...ktuk...", "..kttuuk..", ".kkttuukk.", "kkkttuukkk"),
    palm2=("..a.aa.a..", ".aahaahaa.", "ahhaaaahha", ".kaeeeaak.", "..ak.tka..", "....kttk..", "....ktuk..", "....kttk..",
           "...ktuk...", "...kttk...", "..kttuuk..", ".kkttuukk."),
    cactus2=("..........", "..........", "..........", "....kk....", "...kekk...", "..kahhak..", ".kahaaahk.", ".kaaaaaak.",
             ".kadaaadk.", ".kaaddaak.", ".kddaaddk.", "..kkkkkk.."),
)
ALT = dict(oak="oak2", pine="pine2", maple="maple2", dead="dead2", willow="willow2", mush="mush2", palm="palm2",
           cactus="cactus2")                 # variants 2 and 3 of a tree use the alternate shape if one exists
TREE_W = 12                                         # sprite canvas: the ten-wide tree with a pixel of room to sway


def tree_art(theme: dict, which: int, variant: int, sway: int = 0, cv: int = 0) -> np.ndarray:
    """One tree of the theme: which=0 the first shape, 1 the second; variant bit 0 mirrors it, bit 1 takes the
    alternate shape; `cv` (0, 1, 2) picks the theme's colour variant, so a wood is never one flat mass of a colour.
    `sway` (-1, 0, 1) slides the crown and bends its tip; the trunk stays planted."""
    shape = theme["trees"][which]
    if variant >= 2 and shape in ALT:
        shape = ALT[shape]
    rows = SHAPES[shape]
    rows = tuple("." * 10 for _ in range(TREE_H - len(rows))) + tuple(rows)
    soft = tuple("".join("a" if ch == "d" and (x + y) % 2 == 0 else ch for x, ch in enumerate(r))
                 for y, r in enumerate(rows))                          # the dark is laid on as a dither
    table = dict(theme["t0" if which == 0 else "t1"])
    if cv:
        table.update(theme["alt"][cv - 1][which])
    spr = art(soft, table)
    if variant % 2:
        spr = flip(spr)
    out = np.full((TREE_H, TREE_W), -1, dtype=np.int16)
    crown = TREE_H - 3
    for y in range(TREE_H):
        shift = sway if y < crown else 0
        if y < 3 and shift:
            shift += sway                                               # the tip bends furthest
        for x in range(10):
            if spr[y, x] >= 0 and 0 <= x + 1 + shift < TREE_W:
                out[y, x + 1 + shift] = spr[y, x]
    return out


# ---- the pond: an irregular water hole with a lit shore, rocks, deep water, reeds, a lily pad, a drifting ripple and
# a pet of its season -----------------------------------------------------------------------------------------------
POND_ROWS = (("...ssssss...", ".ssWWwWWWss.", "sWWWWWWWWWWs", "sWWWWWWWDDWs", "sWDDWWWWDDWs", ".sWDDDDDWWs.", "..sssssss..."),
             ("..ssssss....", ".sWWWWWWss..", "sWWwWWWWWWss", "sWWWWWDDWWWs", ".sDDDWWDDWs.", "..sWWWWWWs..", "...sssssss.."),
             ("..sssss.....", ".sWWWWWss...", "sWWwWWWWWss.", "sWWWWDDWWWWs", ".sWWDDDDWWs.", "..sWWWWWWs..", "...ssssss..."))
POND_ROCKS = (((0, 2), (11, 4)), ((0, 2), (11, 3)), ((0, 2), (11, 3)))      # shore pixels that are a stone each


def pond_pet(spr: np.ndarray, theme: dict, phase: int) -> None:
    """The pond's pet of the season, drawn into the pond picture: it paddles, circles, glints or blinks and means nothing."""
    pet = theme["pet"]
    if pet == "duck":                                        # a white duck paddling to and fro
        x = 3 + (0, 1, 2, 1)[phase % 4]
        put(spr, WHT, (x, 3), (x + 1, 3), (x + 2, 3), (x + 2, 2), (x + 1, 4))
        put(spr, ORG, (x + 3, 2))
        put(spr, BLK, (x + 2, 2) if phase % 4 == 3 else (x + 1, 3))      # an eye that blinks into its feathers
    elif pet == "koi":                                        # an orange koi swimming a slow circle
        x, y = ((7, 3), (8, 4), (7, 5), (6, 4))[phase % 4]
        put(spr, ORG, (x, y), (x - 1, y))
        put(spr, WHT, (x + 1, y))
        put(spr, RED, (x - 2, y + (phase % 2)))
    elif pet == "glint":                                      # sunlight skipping over the ice
        put(spr, WHT, *(((3, 2), (8, 3)), ((4, 4), (7, 2)), ((8, 4), (5, 3)), ((6, 4), (3, 3)))[phase % 4])
    elif pet == "stars":                                      # the night sky twinkling in the water
        put(spr, (WHT, YEL, LBL, WHT)[phase % 4], (5, 2), (8, 4))
        put(spr, (LBL, WHT, WHT, YEL)[phase % 4], (3, 4), (7, 3))
    elif pet == "dragonfly":                                  # a dragonfly hovering with whirring wings
        x, y = ((6, 2), (7, 3), (6, 3), (5, 2))[phase % 4]
        put(spr, GRN, (x, y), (x + 1, y))
        put(spr, WHT, (x, y - 1), (x + 1, y - 1)) if phase % 2 else put(spr, LBL, (x - 1, y), (x + 2, y))
    else:                                                     # frog: two golden eyes breaking the surface
        put(spr, BLK, (5, 3), (7, 3))
        put(spr, YEL if phase % 4 != 2 else GRN, (5, 4), (7, 4))


def pond_art(phase: int, theme: dict, shape: int = 0) -> np.ndarray:
    """Twelve wide, nine tall. Ripples slide, the lily pad bobs, the reeds lean, the pet moves; ice (snow) shows cracks;
    the lower lip throws a one-pixel shadow so the water sits in the ground, and two shore stones break the outline."""
    p = theme["pond"]
    spr = art(POND_ROWS[shape], dict(s=p["shore"], W=p["water"], D=p["deep"], w=p["hi"]))
    spr = np.vstack([spr, np.full((2, 12), -1, dtype=np.int16)])
    for x in range(12):                                              # the shadow under the lower shore
        for y in range(6, -1, -1):
            if spr[y, x] >= 0:
                spr[y + 1, x] = theme["rim"]
                break
    for rx, ry in POND_ROCKS[shape]:                                 # shore stones
        put(spr, LBL, (rx, ry))
        put(spr, WHT, (rx, ry - 1))
        put(spr, BLK, (rx, ry + 1))
    frozen = theme["name"] == "snow"
    if frozen:                                                       # a frozen pond: pale ice with a crack
        for x, y in ((3, 3), (4, 3), (5, 4), (6, 4), (6, 5), (7, 5)):
            spr[y, x] = p["hi"]
        for x, y in ((2, 2), (3, 2)):
            spr[y, x] = WHT
    else:
        ripple = 3 + (phase * 2) % 6                                 # a pair of pale pixels sliding along row two
        for dx in (0, 1):
            if spr[2, ripple + dx] == p["water"]:
                spr[2, ripple + dx] = p["hi"]
        for x, y in ((2, 4), (3, 4), (3, 5)):                        # the lily pad, bobbing a pixel
            spr[y - phase % 2, x] = p["plant"]
        spr[3 - phase % 2, 2] = p["bloom"]
        if theme["name"] == "night":                                 # a moon reflection that wobbles
            spr[3, 8 + phase % 2] = WHT
    pond_pet(spr, theme, phase)
    lean = (0, 1, 0, -1)[phase % 4]                                  # two cattails at the right shore
    for i, (bx, h) in enumerate(((10, 3), (11, 2))):
        for r in range(h):
            x = bx + (lean if r == h - 1 else 0)
            if 0 <= x < 12:
                spr[5 - r - (1 if i else 0), x] = theme["pond"]["plant"] if r < h - 1 else MAR
    return spr


# ---- the pilgrim: hooded, blue-robed, a black face opening with two glowing yellow eyes, an orange scarf ----------
PILGRIM_ROWS = {
    (0, 1): ("..kkk..", ".kbbbk.", "kbllbbk", "kbkkkbk", "kbykybk", "kbkkkbk", "koooook", "kblbbbk"),
    (0, -1): ("..kkk..", ".kbbbk.", "kbllbbk", "kbbbbbk", "kbbbbbk", "kbbbbbk", "koooook", "kblbbbk"),
    (-1, 0): ("..kkk..", ".kbbbk.", "kllbbbk", "kkkbbbk", "kykbbbk", "kkkbbbk", "ooooook", "kblbbbk"),
    (1, 0): ("..kkk..", ".kbbbk.", "kbbllbk", "kbbbkkk", "kbbbkyk", "kbbbkkk", "koooooo", "kbbblbk"),
}
PILGRIM_LEGS = ((".kk.kk.", "..k.k.."), ("..kkk..", ".k...k."))     # two walking poses, two rows each


def pilgrim(face: tuple, leg: int, mood: str = "calm") -> np.ndarray:
    """Seven wide, ten tall: the hooded pilgrim in the direction he faces, mid-stride on one of two poses. `mood`:
    calm; blink (eyes shut); wince (eyes squeezed, a sweat drop, in a catch); cheer (arms up, nine wide)."""
    rows = list(PILGRIM_ROWS[face] + PILGRIM_LEGS[leg % 2])
    if mood == "blink":
        rows = [r.replace("y", "k") for r in rows]
    spr = art(rows)
    if mood == "wince":
        spr = art([r.replace("y", "k") for r in rows])
        spr[3, 2], spr[3, 4] = YEL, YEL                              # eyes flung wide up under the hood
        spr[5, 3] = ORG                                              # and a small round shout
        spr[1, 6] = LBL                                              # a sweat drop on the hood
    if mood == "cheer":
        out = np.full((10, 9), -1, dtype=np.int16)
        out[:, 1:8] = spr
        for x in (0, 8):                                              # both arms thrown up, fists gold
            out[0, x] = YEL
            out[1, x] = ORG
            out[2:5, x] = BLU
        return out
    return spr


# the collapsed pilgrim of a lost run: flat on his back, swirl eyes, scarf trailing, a tear
FALLEN = art((".kkkkk....", "kbllbbk...", "kkykbbkkkk", "kykkbbbbbk", "kkkkooookk", ".kbbbbbbk.", "..kk..kk.."))
FALLEN_TEAR = art((".l.", "lwl"))                                    # a tear that wobbles beside the hood


# ---- the patrol: a horned magenta imp whose eyes look where it is heading --------------------------------------
def imp(heading: tuple, leg: int, mood: str = "calm") -> np.ndarray:
    """Seven wide, eight tall. Each eye is half white, half black; the black half looks where it heads. `mood`: calm,
    glee (toothy grin, nine wide with both fists in the air: the one that caught the pilgrim) or shy (the others,
    eyes cast down after a catch)."""
    top, bottom = {(0, 1): ("ww", "kk"), (0, -1): ("kk", "ww"),
                   (-1, 0): ("kw", "kw"), (1, 0): ("wk", "wk")}[heading]
    if mood == "shy":
        top, bottom = "ww", "kk"
    mouth = "kwkwkck" if mood == "glee" else ("kckkkck" if mood == "calm" else "kcckcck")
    rows = ("w.....w", "kc...ck", "kccccck", "k" + top + "c" + top + "k", "k" + bottom + "c" + bottom + "k", mouth,
            "kcpppck", (".k...k.", "k.k.k.k")[leg % 2])
    spr = art(rows)
    if mood == "glee":
        out = np.full((8, 9), -1, dtype=np.int16)
        out[:, 1:8] = spr
        for y in (0, 1, 2):
            out[y, 0] = out[y, 8] = MAG
        out[0, 0] = out[0, 8] = WHT
        return out
    return spr


# ---- the bramble: a thorny tangle with a sleepy face that opens its eyes when the pilgrim comes near ---------------
THORN_ROWS = ("w.c..c.w", ".cckkcc.", "wkcccckw", "ckcEEckc", "wkcEEckw", ".kcmmckc", "..kkkk..", "...kk...")


def thorn_art(pose: int, beat: int) -> np.ndarray:
    """Eight by eight. pose 0 asleep (eye slits), 1 awake (white eyes), 2 furious (red eyes, bared teeth). The tips of
    the thorns shimmer between two poses on the beat."""
    spr = art(THORN_ROWS, dict(E=BLK))
    eyes = ((3, 3), (3, 4), (4, 3), (4, 4))
    if pose == 0:
        for x, y in ((3, 4), (4, 4)):
            spr[y, x] = BLK
        for x, y in ((3, 3), (4, 3)):
            spr[y, x] = MAG
    elif pose == 1:
        spr[3, 3] = WHT
        spr[3, 4] = WHT
        spr[4, 3] = BLK
        spr[4, 4] = BLK
    else:
        for x, y in eyes:
            spr[y, x] = RED
        spr[5, 3] = WHT
        spr[5, 4] = WHT
    if beat % 2:
        spr[0, 0], spr[0, 7] = -1, -1
        spr[1, 0], spr[1, 7] = WHT, WHT
    return spr


# ---- the brazier: a gold-rimmed bowl on a stem, identical at every shrine until the flame is lit -----------------
# ---- props: the scene dressing drawn at each level's prop cells, two kinds per theme, two poses each --------------------
# Each is built from round shaded bodies (disc) and a few hand-placed pixels on a nine-wide, ten-tall canvas whose bottom
# row is the ground. `hue` is the prop's own colour (it changes from prop to prop so no two look alike); `pose` (0 or 1)
# is the idle animation: a sway, a blink, a bob or a glint. They are drawn UNDER seals, thorns and creatures.
PROP_W, PROP_H = 9, 10


def _p_flower(s, hue, pose):
    """A bed of three flowers whose heads trade colours and whose stems lean with the breeze."""
    alt = YEL if hue == WHT else WHT
    for i, (cx, top) in enumerate(((2, 3), (6, 2), (4, 5))):
        lean = pose if i != 1 else -pose
        for y in range(top + 1, 9):
            put(s, GRN, (cx + (lean if y <= top + 2 else 0), y))
        hx = cx + lean
        put(s, hue if (i + pose) % 2 == 0 else alt, (hx, top - 1), (hx - 1, top), (hx + 1, top), (hx, top + 1))
        put(s, YEL if (i + pose) % 2 == 0 else ORG, (hx, top))
        put(s, GRN, (cx - 1, top + 3), (cx + 1, top + 4))
    s[9, 1:8] = MAR
    s[8, 0:2] = GRN
    s[8, 7:9] = GRN


def _p_hive(s, hue, pose):
    """A straw skep with honey bands and a dark doorway; a bee loops round it."""
    s[2:10, :] = disc(9, 8, YEL, BLK, WHT, ORG)
    for y in (4, 6):
        s[y][s[y] == YEL] = ORG
    put(s, BLK, (3, 8), (4, 8), (5, 8), (3, 9), (4, 9), (5, 9), (4, 7))
    put(s, BLK, (4, 1))
    bx, by = (7, 1) if pose else (1, 2)
    put(s, BLK, (bx, by))
    put(s, YEL, (bx + 1, by))
    put(s, WHT, (bx, by - 1))
    put(s, LBL, (bx + 1, by - 1))


def _p_pumpkin(s, hue, pose):
    """A carved pumpkin whose candle flickers: the eyes shine gold on one pose and go dark on the other."""
    s[3:10, :] = disc(9, 7, ORG, BLK, YEL, RED)
    for x in (3, 5):
        for y in range(4, 9):
            if s[y, x] == ORG:
                s[y, x] = RED
    put(s, GRN, (4, 2), (4, 1), (5, 2), (5, 1) if pose else (3, 1))
    put(s, YEL if pose else BLK, (2, 5), (3, 5), (5, 5), (6, 5))
    put(s, BLK, (2, 7), (3, 8), (4, 7), (5, 8), (6, 7))
    put(s, YEL if pose else BLK, (4, 6))


def _p_toadstool(s, hue, pose):
    """A fat toadstool: a spotted cap in the prop's hue on a white stem, spots that change colour."""
    cap = disc(9, 9, hue, BLK, LIGHTER.get(hue, WHT), DARKER.get(hue, BLK))[0:5]
    s[1:6, :] = cap
    spot = (RED if hue == WHT else WHT) if pose == 0 else YEL
    put(s, spot, (2, 2), (5, 1), (6, 3), (4, 3), (3, 2) if pose else (1, 3))
    s[6:9, 3:6] = WHT
    s[6:9, 2] = BLK
    s[6:9, 6] = BLK
    put(s, BLK, (3, 9), (4, 9), (5, 9))
    put(s, GRN, (1, 9), (2, 9), (6, 9), (7, 9), (0, 8) if pose else (1, 8))


def _p_snowman(s, hue, pose):
    """A two-ball snowman in a top hat, with a coal-eyed face, a carrot nose and a scarf of the prop's hue; one stick arm
    waves up and down."""
    scarf = hue if hue != WHT else RED
    body = disc(9, 5, WHT, BLK, WHT, LBL)
    s[5:10, :] = body
    head = disc(5, 5, WHT, BLK, WHT, LBL)
    s[2:7, 2:7] = np.where(head >= 0, head, s[2:7, 2:7])
    s[0, 3:6] = BLK
    s[1, 2:7] = BLK
    put(s, scarf, (3, 1), (4, 1), (5, 1))                                   # the hat band
    put(s, BLK, (3, 3), (5, 3))
    put(s, ORG, (4, 4), (5, 4))
    for x in range(2, 7):
        put(s, scarf, (x, 6))
    put(s, scarf, (6, 7), (6, 8))
    put(s, BLK, (4, 7), (4, 8))
    put(s, MAR, (0, 6 - pose), (1, 7 - pose), (8, 7 + pose), (7, 7 + pose))   # the stick arms


def _p_igloo(s, hue, pose):
    """A snow-block igloo with a dark arched door and a pennant that flaps."""
    s[4:10, :] = disc(9, 10, WHT, BLK, WHT, LBL)[0:6]
    for x in range(2, 7, 2):
        put(s, LBL, (x, 6))
    for x in range(1, 8, 2):
        put(s, LBL, (x, 7))
    put(s, BLK, (3, 8), (4, 8), (5, 8), (3, 9), (4, 9), (5, 9), (4, 7))
    for y in range(1, 4):
        put(s, BLK, (4, y))
    put(s, hue if hue != WHT else RED, (5, 1), (6, 1 - pose + 0), (5, 2))


def _p_crystal(s, hue, pose):
    """A fat faceted gem standing in the ground: a lit left face, the hue in the middle, a dark right face, a white
    highlight stripe and a glint that travels over it."""
    dark, light = DARKER.get(hue, BLU), LIGHTER.get(hue, WHT)
    for y, w in enumerate((1, 3, 5, 7, 7, 7, 7, 5, 3, 1)):
        for x in range(4 - w // 2, 5 + w // 2):
            edge = x in (4 - w // 2, 4 + w // 2) or y in (0, 9)
            put(s, BLK if edge else (light if x < 3 else (hue if x < 5 else dark)), (x, y))
    put(s, WHT, (2, 3), (2, 4), (2, 5))
    put(s, WHT, *(((3, 2), (4, 2)) if pose else ((5, 6), (5, 7))))
    put(s, hue, (0, 9), (8, 9))


def _p_owl(s, hue, pose):
    """A round brown owl on a branch: big white eyes that blink, a gold beak and a feathered belly."""
    s[1:9, 1:8] = disc(7, 8, MAR, BLK, ORG, PUR)
    put(s, BLK, (1, 0), (2, 1), (7, 0), (6, 1))
    for ex in (1, 5):
        s[2:5, ex:ex + 3] = BLK if pose else WHT
        if not pose:
            put(s, BLK, (ex, 2), (ex + 2, 2), (ex, 4), (ex + 2, 4))
        put(s, BLK if not pose else hue, (ex + 1, 3))
    put(s, ORG, (4, 4), (4, 5))
    put(s, YEL, (3, 6), (5, 6), (4, 7), (4, 8))
    s[9, 0:9] = MAR
    put(s, ORG, (3, 9), (5, 9))


def _p_barrel(s, hue, pose):
    """A fat clay jar with a band in the prop's hue and a sprout that sways from its mouth."""
    s[3:10, :] = disc(9, 7, RED, BLK, ORG, MAR)
    for x in range(1, 8):
        if s[6, x] >= 0 and s[6, x] != BLK:
            s[6, x] = hue if hue != RED else YEL
    put(s, BLK, (3, 2), (4, 2), (5, 2))
    put(s, GRN, (4, 1), (3 - pose, 0), (5 - pose, 0), (3, 1) if pose else (5, 1))


def _p_cairn(s, hue, pose):
    """Three stacked stones with a small gem on top that twinkles."""
    s[6:10, :] = disc(9, 4, WHT, BLK, WHT, LBL)
    s[3:7, 1:8] = np.where(disc(7, 4, LBL, BLK, WHT, BLU) >= 0, disc(7, 4, LBL, BLK, WHT, BLU), s[3:7, 1:8])
    top = disc(5, 3, WHT, BLK, WHT, LBL)
    s[1:4, 2:7] = np.where(top >= 0, top, s[1:4, 2:7])
    put(s, YEL, (4, 0))
    if pose:
        put(s, WHT, (3, 0), (5, 0))
    put(s, hue if hue != WHT else ORG, (4, 8), (3, 4))


def _p_ghost(s, hue, pose):
    """A friendly ghost with rosy cheeks, bobbing in the air; its hem ripples."""
    y0 = 1 + pose
    s[y0:y0 + 8, 1:8] = disc(7, 8, WHT, BLK, WHT, LBL)
    for x in range(1, 8):
        if (x + pose) % 2:
            s[y0 + 7, x] = -1
    put(s, BLK, (3, y0 + 3), (3, y0 + 4), (5, y0 + 3), (5, y0 + 4), (4, y0 + 5))
    put(s, hue if hue != WHT else PNK, (2, y0 + 5), (6, y0 + 5))
    put(s, WHT, (0, y0 + 4), (8, y0 + 4 - pose))


def _p_frog(s, hue, pose):
    """A plump frog: two bulging eyes that blink, a wide smile, a pale puffing throat and a spot in the prop's hue."""
    s[4:9, :] = disc(9, 5, YEL, BLK, WHT, ORG)
    for ex in (0, 6):
        s[2:5, ex:ex + 3] = disc(3, 3, WHT if not pose else YEL, BLK)
        put(s, BLK if not pose else YEL, (ex + 1, 3))
    put(s, BLK, *((x, 6) for x in range(2, 7)))
    put(s, WHT if pose else LBL, (3, 7), (4, 7), (5, 7))
    put(s, hue if hue not in (YEL, GRN) else MAR, (2, 5), (6, 5), (4, 5))
    put(s, BLK, (0, 8), (0, 9), (1, 9), (8, 8), (8, 9), (7, 9))
    put(s, YEL, (1, 8), (7, 8))


PROP_BUILD = dict(flower=_p_flower, hive=_p_hive, pumpkin=_p_pumpkin, toadstool=_p_toadstool, snowman=_p_snowman,
                  igloo=_p_igloo, crystal=_p_crystal, owl=_p_owl, barrel=_p_barrel, cairn=_p_cairn, ghost=_p_ghost,
                  frog=_p_frog)


def prop_art(kind: str, hue: int, pose: int, theme: dict) -> np.ndarray:
    s = np.full((PROP_H, PROP_W), -1, dtype=np.int16)
    PROP_BUILD[kind](s, hue, pose)
    return s


# ---- ground decals: forest-floor dressing, four by four, scattered by hash (art only) -------------------------------
DECALS = dict(
    flower=("..h.", ".hyh", "..g.", ".gg."), clover=("g.g.", ".gg.", "g.g.", "..g."), tuft=("..h.", ".h.h", "....", "h..."),
    leaves=("..r.", ".oyo", "ro.o", "..y."), acorn=(".kk.", "kmmk", ".mm.", "..k."),
    toadstool=("krrk", "kwrw", ".kk.", ".kw."), drift=("..w.", ".www", "wwwl", "...."), frostflower=(".l.l", "..w.", ".l.l", "...."),
    icicle=("w.w.", "lwl.", ".l..", "...."), crystalbit=("..l.", ".lwl", ".lll", "...."), glowcap=("..y.", ".yyy", "..w.", "..w."),
    star=("..w.", ".wyw", "..w.", "...."), pebbles=(".kk.", "kwwk", ".kk.", "..k."), sprout=("..g.", "g.g.", ".gg.", "..k."),
    ripple=("....", ".ww.", "w..w", "...."), reed=(".m..", ".g.m", ".g.g", ".g.g"), bubble=("..w.", ".w.w", "..w.", "...."),
)
DECAL_HUE = (PNK, WHT, YEL, MAG, RED, LBL)


def decal_art(kind: str, theme: dict, k: int) -> np.ndarray:
    """One decal in the theme's colours; `k` (a hash) picks its flower hue."""
    hue = DECAL_HUE[k % len(DECAL_HUE)]
    return art(DECALS[kind], dict(h=hue, r=RED, o=ORG, y=YEL, w=WHT, l=LBL, g=GRN, m=MAR, k=theme["rim"] if kind in
               ("pebbles", "sprout", "acorn", "toadstool") else BLK))


# ---- forest-floor and path textures: four-by-four patterns, picked by hash, that give every season its own ground ------
# Letters: k the theme's dark fleck, h its lit fleck, a its accent (forest floor); on the path k is the cast shadow, h the
# worn light, s the pebble, and g/r/y/w/o the plain colours.
FLOOR_TEX = dict(
    grass=(("....", ".k.k", ".kk.", "...."), ("k...", "kk.a", "....", "..k."), ("....", "a...", "..k.", ".kk.")),
    leaf=(("....", ".ak.", "..ka", "...."), ("a...", ".k..", "..ah", "...."), ("....", "hk..", ".a.k", "....")),
    snow=(("....", ".h..", "hhh.", "...."), ("..h.", ".hhh", "....", "k..."), ("....", "...k", ".hh.", "hhhh")),
    star=(("....", "..a.", "....", "k..."), ("a...", "....", "..k.", "...a"), (".k..", "....", "....", ".a.h")),
    wind=(("....", "hhh.", "..hk", "...."), (".hh.", "k..k", "....", "hh.."), ("....", "kk..", ".hhh", "....")),
    murk=(("....", ".k..", "kk.h", "...."), ("h...", "....", ".kk.", "k..a"), ("....", "..a.", "..k.", ".kk.")),
)
PATH_TEX = dict(
    grass=(("....", "....", "g.g.", ".g.."), ("....", "..g.", "..g.", ".gg."), ("....", ".h..", "....", "...k")),
    leaf=(("....", ".r..", "..y.", "...."), ("....", "..r.", ".ry.", "...."), ("....", "k...", ".h..", "....")),
    snow=(("....", "..s.", "....", ".s.."), ("....", ".h..", "hh..", "...."), ("....", "...s", "....", "s...")),
    night=(("....", "kkk.", "..k.", "...."), ("....", ".k..", "kkk.", "...."), ("....", "..s.", "....", "....")),
    dune=(("....", ".hh.", "....", "...."), ("....", "....", "k.k.", "...."), (".h..", "h.h.", "....", "....")),
    swamp=(("....", ".k.k", "....", "k..."), ("..y.", "....", "....", ".k.."), ("....", "kk..", "....", "..y.")),
)


def tex_art(table: dict, family: str, theme: dict, i: int, ground: str) -> np.ndarray:
    pal = dict(k=theme["base_lo"], h=theme["base_hi"], a=theme["acc"]) if ground == "floor" else \
        dict(k=theme["path_lo"], h=theme["path_hi"], s=theme["speck"], g=GRN, r=RED, y=YEL)
    return art(table[family][i % 3], pal)


# ---- flora: plants that sway, pulse or glint where no tree grows (the forest's edge); never on the path ---------------
# rows: a hand-drawn core (padded to nine wide); sway: how many top rows lean with the breeze; glint: where a spark
# shows on each of four beats; letters h and j are the plant's two hues, which trade places every other beat
FLORA = dict(
    poppies=dict(rows=(".hhh.jjj.", "hhyhjjyjj", ".hhh.jjj.", "..g...g..", "..g.g.g..", ".gg.g.gg.", "..ggggg..", ".mmmmmmm."),
                 sway=4, glint=None, hues=(PNK, RED, WHT, ORG)),
    bush=dict(rows=("..kkkkk..", ".kgygggk.", "kgygegggk", "kgggggegk", "kggegggek", ".kgggggk.", "..kkkkk.."), sway=0,
              glint=None, hues=(RED, PNK, WHT, ORG)),
    leafpile=dict(rows=(".r.o...", ".royoy.", "royroyo", "oyroyro", ".kkkkk."), sway=2, glint=None, hues=(ORG,)),
    stump=dict(rows=(".kkkkk.", "kmooomk", "kmoyomk", "kmooomk", ".kmmmk.", "..kkk.."), sway=0,
               glint=(((2, 1),), ((4, 3),), ((3, 2),), ((5, 2),)), gc=WHT, hues=(ORG,)),
    snowbush=dict(rows=("..kkk..", ".kwwwk.", "kwwlwwk", "kwlwwwk", ".kwwwk.", "..kkk.."), sway=0,
                  glint=(((2, 2),), ((4, 1),), ((5, 3),), ((3, 4),)), gc=BLU, hues=(WHT,)),
    icecrystal=dict(rows=("...w...", "..lwl..", ".llwll.", ".blllb.", "bblllbb", "kkbbbkk"), sway=0,
                    glint=(((3, 1),), ((4, 3),), ((2, 4),), ((4, 4),)), gc=WHT, hues=(LBL,)),
    glowshroom=dict(rows=("..kkk..", ".khhhk.", "khjhjhk", ".kkukk.", "...u...", "..uuu.."), sway=0, glint=None,
                    hues=(LBL, YEL, MAG, WHT)),
    starflower=dict(rows=("...h...", "..hjh..", ".hjyjh.", "..hjh..", "...g...", "..g.g.."), sway=0, glint=None,
                    hues=(YEL, LBL, PNK, WHT)),
    grasstuft=dict(rows=("h..h..h", ".g.g.g.", ".g.g.g.", "..ggg..", "..kgk..", "...k..."), sway=3, glint=None,
                   hues=(YEL, WHT, RED)),
    rock=dict(rows=("..kkk..", ".kwwlk.", "kwwlllk", "kwlllmk", "kllmmmk", ".kkkkk."), sway=0,
              glint=(((2, 1),), ((3, 2),), ((2, 2),), ((4, 1),)), gc=YEL, hues=(WHT,)),
    cattail=dict(rows=("..m.m..", "..m.m.m", ".gg.gg.", ".g..g.g", ".g.gg.g", "gg.g.gg"), sway=3, glint=None,
                 hues=(MAR,)),
    bubblepot=dict(rows=("...h...", "h...j..", ".kkkkk.", "kgggggk", "kgyggyk", ".kkkkk."), sway=0,
                   glint=(((3, 1),), ((2, 0),), ((4, 0),), ((5, 1),)), gc=LBL, hues=(LBL, WHT, YEL)),
)


def flora_art(kind: str, hue: int, phase: int) -> np.ndarray:
    """One plant on one of its four beats: its top rows lean, its two hues swap on odd beats, a glint sparks."""
    spec = FLORA[kind]
    alt = YEL if hue in (WHT, ORG, RED, PNK, LBL) else WHT
    h, j = (hue, alt) if phase % 2 == 0 else (alt, hue)
    core = art(centre(spec["rows"], 9), dict(h=h, j=j, e=hue))
    out = np.full(core.shape, -1, dtype=np.int16)
    dx = (0, 1, 0, -1)[phase % 4]
    for y in range(core.shape[0]):
        shift = dx if y < spec["sway"] else 0
        for x in range(9):
            if core[y, x] >= 0 and 0 <= x + shift < 9:
                out[y, x + shift] = core[y, x]
    if spec["glint"]:
        put(out, spec["gc"], *((x + 1, y) for x, y in spec["glint"][phase % 4]))
    return out


# ---- critters: one small animal of the season, sitting in the forest, hopping, blinking and twitching -----------------
# each is (pose A, pose B, blink); every row is as wide as its first
CRITTERS = dict(
    bunny=((".kp.pk.", ".kw.wk.", ".kwwwk.", "kwkwkwk", "kwwpwwk", ".kwwwk.", "..kkk.."),
           ("kp...pk", "kw...wk", ".kwwwk.", "kwkwkwk", "kwwpwwk", ".kwwwk.", "..kkk.."),
           (".kp.pk.", ".kw.wk.", ".kwwwk.", "kwwwwwk", "kwwpwwk", ".kwwwk.", "..kkk..")),
    fox=(("k.....k", "kok.kok", "koooook", "kokokok", "kwwkwwk", ".kwwwk.", "..kkk.."),
         (".......", "k.....k", "koo.ook", "kokokok", "kwwkwwk", ".kwwwk.", "..kkk.."),
         ("k.....k", "kok.kok", "koooook", "koooook", "kwwkwwk", ".kwwwk.", "..kkk..")),
    penguin=(("..kkk..", ".kkkkk.", "kkwkwkk", "kkkokkk", "krrrrrk", "kwwwwwk", ".oo.oo."),
             ("..kkk..", ".kkkkk.", "kkwkwkk", "kkkokkk", "kkrrrkk", "kkwwwkk", ".oo.oo."),
             ("..kkk..", ".kkkkk.", "kkkkkkk", "kkkokkk", "krrrrrk", "kwwwwwk", ".oo.oo.")),
    bat=(("u.....u", "uu...uu", "ucu.ucu", ".ucccu.", ".cycyc.", "..ccc.."),
         (".......", ".......", "uu.c.uu", "ucccccu", ".cycyc.", "..ccc.."),
         ("u.....u", "uu...uu", "ucu.ucu", ".ucccu.", ".ccccc.", "..ccc..")),
    axolotl=(("rr...rr", "rrkpkrr", ".kpppk.", "kpkkkpk", ".kpppk.", "..k.k.."),
             (".rr.rr.", "rrkpkrr", ".kpppk.", "kpkkkpk", ".kpppk.", ".k...k."),
             ("rr...rr", "rrppprr", ".kpppk.", "kpkkkpk", ".kpppk.", "..k.k..")),
)


def _lizard(pose: int) -> np.ndarray:
    """A green gecko, ten wide and six tall: a round body, a head with gold eyes, four legs and a tail that flicks up
    and down; pose 2 shuts its eyes."""
    s = np.full((6, 10), -1, dtype=np.int16)
    s[1:5, 2:8] = disc(6, 4, GRN, BLK, YEL, None)
    s[1:4, 0:4] = np.where(disc(4, 3, GRN, BLK, YEL, None) >= 0, disc(4, 3, GRN, BLK, YEL, None), s[1:4, 0:4])
    put(s, BLK if pose == 2 else YEL, (1, 2))
    put(s, BLK, (3, 0), (6, 0), (3, 5), (6, 5), (0, 4))
    tail = ((8, 2), (9, 1)) if pose == 1 else ((8, 3), (9, 4))
    put(s, GRN, (8, 3 if pose != 1 else 2), *tail)
    put(s, BLK, (8, 4 if pose != 1 else 1), (9, 3 if pose != 1 else 2))
    return s


def critter_art(kind: str, pose: int) -> np.ndarray:
    """pose 0 and 1 are the two resting poses, 2 is the blink."""
    return _lizard(pose) if kind == "lizard" else art(CRITTERS[kind][pose])


# ---- the houses ---------------------------------------------------------------------------------------------------
# A shrine is a walled courtyard five cells square: a roof on the back wall (top four pixel rows), side walls, a front
# wall with the doorway, and a flagstone floor. It is drawn as one twenty-by-twenty picture per theme, built from a
# roof, a side wall and a front wall pattern. Letters: R roof, S roof shade, H ridge, F wall face, M wall dark, L wall
# light, Y lit window, W window glint, k outline; `P` is left see-through for the floor/doorway.
ROOFS_ART = (
    (".kkkkkkkkkkkkkkkkkk.", "kHHHHHHHHHHHHHHHHHHk", "kRRRRRRRRRRRRRRRRRRk", "kSRRSRRSRRSRRSRRSRRk"),     # tiles
    (".kkkkkkkkkkkkkkkkkk.", "kHHRHHRHHRHHRHHRHHRk", "kRSRRSRRSRRSRRSRRSRk", "kSSSSSSSSSSSSSSSSSSk"),     # thatch
    (".kkkkkkkkkkkkkkkkkk.", "kHHHHHHHHHHHHHHHHHHk", "kRRRRRRRRRRRRRRRRRRk", "kRSRRSRSRRSRRSRSRRSk"),     # snow
    ("kk..kkkkkkkkkkkk..kk", "kHRRHHHHHHHHHHHHRRHk", "kRRSRRSRRSRRSRRSRRSk", "kSSSSSSSSSSSSSSSSSSk"),     # pagoda
    ("kkk.kkk.kkk.kkk.kkk.", "kHHHHHHHHHHHHHHHHHHk", "kRRkRRRRkRRRRkRRRRRk", "kSSSSSSSSSSSSSSSSSSk"),     # adobe
    (".kkkkkkkkkkkkkkkkkk.", "kRRRwwRRRRRRRRwwRRRk", "kRRRwwRRRRRRRRwwRRRk", "kSSSSSSSSSSSSSSSSSSk"),     # toadstool cap
)
SANCTUM_ROOFS = (
    (".kk..kkkkkkkkkk..kk.", "kHHkkHHHHHHHHHHkkHHk", "kRRHHRRRRRRRRRRHHRRk", "kSSSSSSSSSSSSSSSSSSk"),      # twin towers
    (".....kkkkkkkkkk.....", "...kkHHHHHHHHHHkk...", ".kkHRRRRRRRRRRRRHkk.", "kSSSSSSSSSSSSSSSSSSk"),      # a low dome
    ("..k.k.k.kkkk.k.k.k..", ".kHkHkHkHHHHkHkHkHk.", "kHHHHHHHHHHHHHHHHHHk", "kRRSRRSRRSRRSRRSRRSk"),      # crowned
)
EAVES = ("SSSSSSSSSSSS", "SSSSSSSSSSSS", "w.w..w.ww.w.", "SSSSSSSSSSSS", "MMMMMMMMMMMM", "SS.S..SS.S.S")   # row 4 over floor
SIDES = (
    ("kLFM", "kLFM", "kLFM", "kkkM", "kYWM", "kYYM", "kYYM", "kLLM", "kLFM", "kLFM", "kLFM", "kLFM"),         # arched window
    ("kLFM", "kLFM", "kLkM", "kkYM", "kYWM", "kYYM", "kkYM", "kLkM", "kLFM", "kLFM", "kLFM", "kLFM"),         # round window
    ("kLFM", "kLFM", "kkLM", "kFYM", "kFYM", "kFYM", "kkLM", "kLFM", "kLFM", "kLFM", "kLFM", "kLFM"),         # slit
)
SIDE_OF_HOUSE = (0, 1, 2, 1, 0, 2)
FRONTS = (("FFFL", "FMFF"), ("FLFF", "MFFF"), ("LFFF", "FFMF"))                    # brick patterns for the front wall


def house_sprite(theme: dict, sanctum: bool) -> np.ndarray:
    """The whole 20x20 picture of a shrine (or the sanctum) for a theme, doorway closed; the caller opens the door."""
    h = theme["house"] % 6
    if sanctum:
        face, dark, light = WHT, LBL, YEL
        roof = (YEL, ORG, WHT)                              # the sanctum keeps the theme's roof shape, in gold
    else:
        face, dark, light = theme["wall"]
        roof = theme["roof"]
    legend = dict(R=roof[0], S=roof[1], H=roof[2], F=face, M=dark, L=light, Y=YEL, W=WHT)
    spr = np.full((20, 20), -1, dtype=np.int16)
    spr[0:4] = art(SANCTUM_ROOFS[h % 3] if sanctum else ROOFS_ART[h], legend)
    side = art(SIDES[SIDE_OF_HOUSE[h]], legend)
    spr[4:16, 0:4] = side
    spr[4:16, 16:20] = flip(side)
    p1, p2 = FRONTS[SIDE_OF_HOUSE[h]]
    front = ("M" + "L" * 18 + "M", "k" + (p1 * 5)[:18] + "k", "k" + (p2 * 5)[:18] + "k", "k" * 20)
    spr[16:20] = art(front, legend)
    return spr


def floor_art(theme: dict, sanctum: bool) -> np.ndarray:
    """The 12x12 flagstone floor of a courtyard: slabs in a brick bond with a pale joint, and a round dais in the theme's
    glow colour under the brazier (the sanctum's is a gold sunburst under the portal)."""
    slab, joint, glow = theme["slab"], theme["joint"], theme["glow"]
    if sanctum:
        slab, joint, glow = WHT, LBL, YEL
    f = np.full((12, 12), slab, dtype=np.int16)
    for y in range(12):
        if y % 4 == 3:
            f[y, :] = joint
        else:
            f[y, (1 if (y // 4) % 2 == 0 else 5)::6] = joint
    yy, xx = np.mgrid[0:12, 0:12]
    d = (xx - 5.5) ** 2 + (yy - 5.5) ** 2
    f[d <= 18.5] = BLK                                    # a dark ring round the dais, so it reads as a raised round step
    f[d <= 12.5] = glow
    f[d <= 6.5] = slab if not sanctum else WHT
    if sanctum:
        for k in range(12):                               # the sunburst: four gold spokes under the portal
            f[5 + (k % 2), k] = YEL
            f[k, 5 + (k % 2)] = YEL
    return f


def door_arch(side: str, wall: int) -> np.ndarray:
    """A gold-lintelled arch over a doorway cell, four by four, for a door on the south wall (the lintel on the side
    that touches the courtyard); turned for the other three walls. The corners fill with the wall's colour, the middle
    stays open, so the doorway reads as an arch over the path."""
    south = art(("FyyF", "F..F", "....", "...."), dict(F=wall, y=YEL))
    return {"S": south, "N": south[::-1], "E": south.T, "W": south.T[:, ::-1]}[side].copy()


# ---- the brazier: a gold-rimmed bowl on a stem, identical at every shrine until the flame is lit -----------------
FLAME = (("...o..", "..oy..", ".oyyo.", ".oywo.", "oyywyo", ".oyyo."),
         ("..o...", "..yo..", ".oyyo.", ".owyo.", "oywyyo", ".oyyo."))
BOWL = (".kook.", "..kk..", ".kkkk.")                # rows 7-9 of the brazier sprite (row 6 is the rim, drawn apart)
BOWL_COLD = "kymmyk"                                 # a gold rim round dark coals: the same at every shrine until lit
BOWL_LIT = "kyooyk"


def brazier(size: int, beat: int) -> np.ndarray:
    """Six wide, ten tall: `size` of the six flame rows lit (0 = cold coals) above the bowl."""
    flame = FLAME[beat % 2]
    rows = ["......" if r < 6 - size else flame[r] for r in range(6)]
    rows += [BOWL_COLD if size == 0 else BOWL_LIT] + list(BOWL)
    return art(rows)


# ---- the seal slab: the identity colour of the gate, with a studded face and black planks -------------------------
SEAL_HUE = (RED, BLU, PUR, WHT)
SEAL_LIGHT = (PNK, LBL, MAG, LBL)


def seal_tile(colour: int, top: bool, bottom: bool, left: bool) -> np.ndarray:
    """A barred slab in the seal's colour. Black only where it meets something that is not the same gate, so a block
    of cells joins into one gate; the black planks are the bars and the light stud and dark rivet are its face."""
    t = np.full((4, 4), SEAL_HUE[colour], dtype=np.int16)
    t[:, 3] = BLK
    t[1, 1] = SEAL_LIGHT[colour]
    t[2, 2] = BLK
    if top:
        t[0, :] = BLK
    if bottom:
        t[3, :] = BLK
    if left:
        t[:, 0] = BLK
    return t


FLAG = (art(("kcc..", "kcccc", "kcc..", "k....", "k....", "k....")), art(("kc...", "kccc.", "kcccc", "k....", "k....",
                                                                              "k....")))


def flag_art(colour: int, beat: int) -> np.ndarray:
    spr = FLAG[beat % 2].copy()
    spr[spr == MAG] = colour
    return spr


# ---- the sanctum portal: a swirling gold-and-sky disc on the win cell ------------------------------------------------
def portal_art(beat: int) -> np.ndarray:
    """Eight by eight: a gold ring, a sky-blue heart, and four white sparks that turn round it one step a beat."""
    rows = ("..kkkk..", ".kyyyyk.", "kyllllyk", "kylbblyk", "kylbblyk", "kyllllyk", ".kyyyyk.", "..kkkk..")
    spr = art(rows)
    ring = ((1, 2), (2, 1), (3, 1), (4, 1), (5, 2), (6, 3), (6, 4), (5, 5), (4, 6), (3, 6), (2, 6), (1, 5))
    # twelve ring positions; four sparks, three apart, turn round them
    for i in range(4):
        x, y = ring[(3 * i + beat) % 12]
        if (x, y) not in ((3, 1),):
            spr[y, x] = WHT
    return spr


# ---- sparkles: three little stars that grow and fade, used for lit shrines, melting seals and the win ---------------
STAR = (art(("w",)), art((".w.", "wyw", ".w.")), art(("y.y.y", ".ywy.", "ywwwy", ".ywy.", "y.y.y")))


def sparkle(frame: np.ndarray, cx: int, cy: int, stage: int, colour: int = YEL) -> None:
    """A star centred on (cx, cy); stage 0 a pixel, 1 a plus, 2 a burst; the rim takes `colour`."""
    spr = STAR[min(2, max(0, stage))].copy()
    spr[(spr == YEL)] = colour
    blit(frame, cx - spr.shape[1] // 2, cy - spr.shape[0] // 2, spr)


def burst(frame: np.ndarray, cx: int, cy: int, radius: int, colour: int) -> None:
    """A little star: eight rays, grown one pixel at a time (the catch flash)."""
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        for r in range(max(1, radius - 1), radius + 1):
            dot(frame, cx + dx * r, cy + dy * r, colour if r == radius else WHT)


# ---- ambient life: a few things that drift and do nothing ------------------------------------------------------------
def life_pixels(kind: str, i: int, t: int, seed: int) -> list:
    """The pixels (dx, dy, colour) of one ambient creature of kind `kind`, i-th of the set, at time t (in frames)."""
    n = _hash(i, seed, 41)
    if kind == "butterfly":
        wing = (PNK, YEL, LBL, WHT)[n % 4]
        flap = (t // 2 + n) % 2
        return [(0, 0, BLK), (-1, -flap, wing), (1, -flap, wing)]
    if kind == "leaf":
        return [(0, 0, (ORG, RED, YEL)[n % 3]), (1, 0, (RED, ORG, MAR)[n % 3])]
    if kind == "snow":
        return [(0, 0, WHT)] + ([(1, 0, WHT), (0, 1, WHT)] if n % 3 == 0 else [])
    if kind == "firefly":
        return [(0, 0, YEL if (t // 3 + n) % 3 else WHT)] + ([(0, 1, ORG)] if (t // 3 + n) % 3 == 0 else [])
    if kind == "spark":
        return [(0, 0, WHT if (t + n) % 4 else YEL)]
    if kind == "bee":                                                    # a bee: black and gold, wings a blur
        return [(0, 0, BLK), (1, 0, YEL), (0, -1, WHT if (t + n) % 2 else LBL)]
    if kind == "gust":                                                   # three leaves caught in a whirl
        return [(0, 0, YEL if (t + n) % 3 else ORG), (1, 1, ORG), (-1, 1, RED)]
    if kind == "glint":                                                  # frost sparkle: a plus that blinks in place
        return [(0, 0, WHT)] + ([(1, 0, LBL), (-1, 0, LBL), (0, 1, LBL), (0, -1, LBL)] if (t // 3 + n) % 4 == 0 else [])
    if kind == "twinkle":                                                # a star that cycles colour
        return [(0, 0, (WHT, YEL, LBL)[(t // 2 + n) % 3])] + ([(1, 0, WHT), (-1, 0, WHT)] if (t // 3 + n) % 5 == 0 else [])
    if kind == "dust":                                                   # a puff of sand skimming along
        return [(0, 0, YEL), (1, 0, ORG if (t + n) % 2 else WHT), (-1, 0, ORG)]
    if kind == "bubble":                                                 # a marsh bubble that swells and pops
        return [(0, 0, LBL)] + ([(1, 0, WHT), (0, 1, WHT), (1, 1, LBL)] if (t // 3 + n) % 3 == 1 else [])
    return [(0, 0, LBL), (1, 0, WHT if (t + n) % 3 else MAG)]            # wisp: a bubble of light


def life_position(kind: str, i: int, t: int, seed: int) -> tuple:
    """Where the i-th ambient creature is, in screen-patch pixels (before the caller wraps them to the window) at
    time t: a start spot from a hash, then a slow drift."""
    n = _hash(i, seed, 43)
    x0, y0 = n % 64, (n >> 8) % 60
    if kind == "butterfly":
        dx, dy = int(5 * np.sin((t + n % 17) / 5.0)), int(3 * np.cos((t + n % 13) / 4.0)) - t // 12
    elif kind == "leaf":
        dx, dy = int(4 * np.sin((t + n % 17) / 4.0)), t // 3
    elif kind == "snow":
        dx, dy = int(2 * np.sin((t + n % 17) / 6.0)) + t // 9, t // 3
    elif kind == "firefly":
        dx, dy = int(6 * np.sin((t + n % 17) / 7.0)), int(4 * np.cos((t + n % 11) / 5.0))
    elif kind == "spark":
        dx, dy = t // 5, int(3 * np.sin((t + n % 17) / 5.0))
    elif kind == "bee":
        dx, dy = int(7 * np.sin((t + n % 17) / 3.0)), int(4 * np.cos((t + n % 11) / 2.0))
    elif kind == "gust":
        dx, dy = int(7 * np.cos(t / 4.0 + n % 7)), int(4 * np.sin(t / 4.0 + n % 7))
    elif kind in ("glint", "twinkle"):
        dx, dy = 0, 0
    elif kind == "dust":
        dx, dy = t // 2, int(2 * np.sin((t + n % 17) / 4.0))
    elif kind == "bubble":
        dx, dy = int(np.sin((t + n % 17) / 4.0)), -((t + n % 9) // 3)
    else:
        dx, dy = int(2 * np.sin((t + n % 17) / 5.0)), -(t // 4)
    return x0 + dx, y0 + dy


# ===================================================================================================================
# PART FOUR: the rules and the map, se01's own, unchanged (only the colours a drawing uses were re-chosen)
# ===================================================================================================================
VOID = 5
FOE_BODY = 6                         # the colour of a catch: the flash border and the burst
PROP_HUE = (6, 7, 10, 0, 12, 15)

CELL = 4
VIEW = 16
SCREEN = VIEW * CELL
VIEW_ROWS = VIEW - 1                 # world cell rows on screen; the bottom cell row is the counter strip
PLAY_H = VIEW_ROWS * CELL            # pixel rows of world picture (the rest is the fixed counter strip)

# Moves per level. Sized at twice the shortest winning line, found by a full breadth-first search over
# (cell, lit shrines, patrol phase) with this file's own passable/_step_foes rules, where a thorn or a catch is a
# loss: shortest lines 210, 211, 261, 327, 370, 426.
BUDGETS = (420, 422, 522, 654, 740, 852)
# The counter strip: a coarse bar where each block is COUNTER_UNIT moves, and a fine row under it that loses one
# pixel per move and refills when a block falls, so every move visibly shrinks something.
COUNTER_UNIT = 16
COUNTER_TRACK, COUNTER_BAR, COUNTER_TICK = MAR, YEL, WHT

STONE_CH, THORN_CH = "#", "x"
CORNERS = ((-1, -1, 0, 0), (1, -1, 3, 0), (-1, 1, 0, 3), (1, 1, 3, 3))

WORLD = dict(
    w=65, h=65, start=(27, 27),
    shrines=[(9, 9), (56, 9), (9, 56), (56, 56)],
    sanctum=(32, 32), sanctum_door=(32, 30),
    rows=[
        '#################################################################',
        '#################################################################',
        '#########....####################################################',
        '#########..........###########################....###############',
        '#########..........###########################............#######',
        '#####.........##...###########################..x.....x......####',
        '#####.........################################....##.........####',
        '#####..#####..######################################..#####..####',
        '#####..#...#..################################...###..#...#..####',
        '#####..#...#..###############....######..#####........#......####',
        '#####..#...#..###############.........................#...#..####',
        '#####..##.##..###############....................###..#####..####',
        '#####.........##########....#..x.######..###########.........####',
        '##............##########..x......###################.....x.....##',
        '##.....##..#############.........#######################.....x.##',
        '##.....##..#############....###..########################......##',
        '#########..##############...###..##########################....##',
        '########....#############.x.##....##########################.x.##',
        '########....#############...##....##########################...##',
        '##########..####################..###############################',
        '##########..####################..###############################',
        '##########..####################..###############################',
        '##########..####################..###############################',
        '##########..####################..###############################',
        '######......####################......###########################',
        '###..........##....#############..x......#####....###############',
        '###..............x.#######...###.......x.#####...........########',
        '###................#######...##..........#####..x...x..x.########',
        '#######......##....#########.........#########...........########',
        '#######..##..###############.........#########....####....#######',
        '#######..##..###############..##.##..#########.x.#####..x.#######',
        '#######..#.......###########..#...#..##..#####............#######',
        '#######.......................#...#.......................#######',
        '#######.......................#...#..............#####..#########',
        '#########........###########..#####..##..#############..#########',
        '#########....###############.........#################..#########',
        '#########....###############.........#################..#########',
        '##########..##########################################..#########',
        '##########..##########################################..#########',
        '##########..#########################################....########',
        '##########..#########################################....########',
        '##########..##########################################..#########',
        '##########..##########################################..#########',
        '##########..##########################################..#########',
        '##########..##########################################..#########',
        '##########..##########################################..#########',
        '##########..##########################################....#######',
        '##########..##########################################.x..#######',
        '##########..##########################################....#######',
        '##########..###########################################..########',
        '##########..###########################################..########',
        '##########..###########################################..########',
        '#####.........######################################.........####',
        '#####.........###..#####...####....#################.........####',
        '#####..##.##.......................#################..#####..####',
        '#####..#...#....................x..#################..#...#..####',
        '#####..#...#..###..#####...####....##############.........#..####',
        '#####..#...#..##################..###....########.....#...#..####',
        '##.....#####..##################.......x.########..#..#####..####',
        '##............###################........#######.............####',
        '##............#######################....######..............####',
        '##....################################...######...x.#############',
        '###...################################...######.....#############',
        '#################################################################',
        '#################################################################',
    ])

LEVELS = [
    dict(seals=[(3, 13, 0), (3, 14, 0), (3, 15, 0), (32, 30, 3), (54, 42, 0), (54, 43, 0), (54, 44, 0), (54, 45, 0), (55, 41, 0), (55, 42, 0), (55, 43, 0), (55, 44, 0)],
         foes=[],
         props=[(8, 10), (46, 6), (12, 26), (54, 37), (27, 16), (2, 15)]),
    dict(seals=[(32, 30, 1), (41, 11, 2), (42, 10, 2), (42, 11, 2), (43, 10, 2), (43, 11, 2), (44, 10, 2), (44, 11, 2), (45, 10, 2)],
         foes=[(5, 52, 1, 0, 5), (52, 4, 0, 1, 6)],
         props=[(8, 10), (47, 11), (13, 31), (56, 6), (31, 27), (7, 26)]),
    dict(seals=[(10, 42, 0), (10, 43, 0), (10, 44, 0), (10, 45, 0), (11, 41, 0), (11, 42, 0), (11, 43, 0), (11, 44, 0), (19, 55, 0), (20, 54, 0), (20, 55, 0), (21, 54, 0), (21, 55, 0), (22, 54, 0), (22, 55, 0), (23, 54, 0), (32, 30, 3), (54, 42, 2), (54, 43, 2), (54, 44, 2), (54, 45, 2), (55, 41, 2), (55, 42, 2), (55, 43, 2), (55, 44, 2)],
         foes=[(9, 3, 1, 0, 5), (10, 46, 0, 1, 6), (52, 52, 1, 0, 7)],
         props=[(8, 6), (49, 27), (24, 14), (2, 61), (40, 33), (13, 11)]),
    dict(seals=[(10, 20, 3), (10, 21, 3), (10, 22, 3), (10, 23, 3), (11, 19, 3), (11, 20, 3), (11, 21, 3), (11, 22, 3), (32, 30, 1), (41, 11, 0), (42, 10, 0), (42, 11, 0), (43, 10, 0), (43, 11, 0), (44, 10, 0), (44, 11, 0), (45, 10, 0)],
         foes=[(52, 52, 1, 0, 5), (12, 2, 0, 1, 6), (46, 4, 1, 0, 7), (32, 24, 0, 1, 5)],
         props=[(8, 6), (49, 29), (19, 54), (62, 15), (39, 25), (12, 33)]),
    dict(seals=[(10, 42, 0), (10, 43, 0), (10, 44, 0), (10, 45, 0), (11, 41, 0), (11, 42, 0), (11, 43, 0), (11, 44, 0), (19, 55, 0), (20, 54, 0), (20, 55, 0), (21, 54, 0), (21, 55, 0), (22, 54, 0), (22, 55, 0), (23, 54, 0), (32, 30, 3), (41, 11, 2), (42, 10, 2), (42, 11, 2), (43, 10, 2), (43, 11, 2), (44, 10, 2), (44, 11, 2), (45, 10, 2), (54, 42, 1), (54, 43, 1), (54, 44, 1), (54, 45, 1), (55, 41, 1), (55, 42, 1), (55, 43, 1), (55, 44, 1)],
         foes=[(9, 3, 1, 0, 5), (10, 46, 0, 1, 6), (46, 4, 1, 0, 7), (56, 46, 0, 1, 5), (32, 26, 1, 0, 6)],
         props=[(8, 6), (52, 5), (29, 11), (8, 30), (52, 53), (29, 55)]),
    dict(seals=[(10, 20, 1), (10, 21, 1), (10, 22, 1), (10, 23, 1), (10, 42, 3), (10, 43, 3), (10, 44, 3), (10, 45, 3), (11, 19, 1), (11, 20, 1), (11, 21, 1), (11, 22, 1), (11, 41, 3), (11, 42, 3), (11, 43, 3), (11, 44, 3), (19, 55, 3), (20, 54, 3), (20, 55, 3), (21, 54, 3), (21, 55, 3), (22, 54, 3), (22, 55, 3), (23, 54, 3), (32, 30, 0), (41, 11, 2), (42, 10, 2), (42, 11, 2), (43, 10, 2), (43, 11, 2), (44, 10, 2), (44, 11, 2), (45, 10, 2)],
         foes=[(52, 52, 1, 0, 5), (10, 46, 0, 1, 6), (46, 4, 1, 0, 7), (12, 2, 0, 1, 5), (32, 26, 1, 0, 6), (32, 9, 0, 1, 7)],
         props=[(8, 6), (53, 8), (31, 13), (9, 57), (55, 6), (33, 32)]),
]





class Ground:

    def __init__(self, spec: dict) -> None:
        self.w, self.h = spec["w"], spec["h"]
        self.rows = spec["rows"]
        self.start = tuple(spec["start"])
        self.shrines = [tuple(s) for s in spec["shrines"]]
        self.sanctum = tuple(spec["sanctum"])
        self.sanctum_door = tuple(spec["sanctum_door"])

    def at(self, x: int, y: int) -> str:
        if not (0 <= x < self.w and 0 <= y < self.h):
            return STONE_CH
        return self.rows[y][x]

    def stone(self, x: int, y: int) -> bool:
        return self.at(x, y) == STONE_CH

    def thorn(self, x: int, y: int) -> bool:
        return self.at(x, y) == THORN_CH


GROUND = Ground(WORLD)


class Arrangement:

    def __init__(self, spec: dict) -> None:
        self.seals = {(x, y): c for x, y, c in spec["seals"]}
        self.foes = [dict(ox=ox, oy=oy, dx=dx, dy=dy, ln=ln)
                     for ox, oy, dx, dy, ln in spec["foes"]]
        self.props = [dict(pos=tuple(p), hue=PROP_HUE[i % len(PROP_HUE)])
                      for i, p in enumerate(spec["props"])]


ARRANGEMENTS = [Arrangement(s) for s in LEVELS]


def build_levels() -> list[Level]:
    return [Level(sprites=[Sprite(pixels=[[VOID] * CELL] * CELL, name="body",
                                  blocking=BlockingMode.NOT_BLOCKED,
                                  interaction=InteractionMode.INTANGIBLE, layer=1)
                           .set_position(GROUND.start[0] * CELL,
                                         GROUND.start[1] * CELL)])
            for _ in ARRANGEMENTS]




def _building(x: int, y: int) -> bool:
    return any(abs(x - bx) <= 2 and abs(y - by) <= 2
               for bx, by in GROUND.shrines + [GROUND.sanctum])



# ===================================================================================================================
# PART FIVE: the pre-drawn worlds. Everything that never changes within a level (ground, forest floor, edges, tree
# shadows, shrine houses, the sanctum) is drawn once per theme into one picture of the whole world; each frame cuts the
# camera window out of it and draws the live sprites on top (trees, ponds, thorns, props, creatures...). The pictures
# are module data, not game state.
# ===================================================================================================================
def _scenery(wx: int, wy: int):
    """What grows on a forest cell (art only, no rule reads it): a tree of one of the theme's two shapes, a pond, or
    nothing. Trees stand on the even cells whose surroundings are all forest; woods are patches seven cells wide
    where the trees crowd."""
    if not GROUND.stone(wx, wy) or _building(wx, wy):
        return None
    k = _hash(wx, wy, 7)
    wood = _hash(wx // 7, wy // 7, 17) % 3 == 0
    if wx % 2 == 0 and wy % 2 == 0 and all(
            GROUND.stone(wx + a, wy + b) and not _building(wx + a, wy + b)
            for a in (-1, 0, 1, 2) for b in (-1, 0, 1, 2)):
        if wood:
            return "pine" if k % 3 == 0 else "tree"
        if k % 13 == 0:
            return "pond"
        return "tree" if k % 3 else "pine"
    return None


SHRINE_BOXES = [(bx, by, by - 2) for bx, by in GROUND.shrines] + [(*GROUND.sanctum, GROUND.sanctum[1] - 2)]


def _wall_cells() -> set:
    """Stone drawn as a building: the 5x5 around each shrine and the sanctum."""
    return {(x, y) for x in range(GROUND.w) for y in range(GROUND.h) if GROUND.stone(x, y) and _building(x, y)}


WALLS = _wall_cells()
FLOORS = {(bx + dx, by + dy) for bx, by in GROUND.shrines + [GROUND.sanctum] for dx in (-1, 0, 1) for dy in (-1, 0, 1)}


def _door_of(bx: int, by: int):
    """Which of the building's ring cells is the doorway (the ring cell that is not wall) and on which side."""
    for dx, dy, side in ((0, 2, "S"), (0, -2, "N"), (2, 0, "E"), (-2, 0, "W")):
        if (bx + dx, by + dy) not in WALLS:
            return (bx + dx, by + dy), side
    return None, None


def _window_pixels(bx: int, by: int, h: int) -> list:
    """The lit window panes of a building as (x, y, is_glint) pixels in house coordinates, read from the side-wall
    pattern (so the wall's own light and face colours are never mistaken for glass), minus any pane the doorway cuts."""
    door, _ = _door_of(bx, by)
    cell = (door[0] - (bx - 2), door[1] - (by - 2))
    out = []
    for r, row in enumerate(SIDES[SIDE_OF_HOUSE[h % 6]]):
        for c, ch in enumerate(row):
            if ch in "YW":
                for x in (c, 19 - c):
                    y = 4 + r
                    if (x // CELL, y // CELL) != cell:
                        out.append((x, y, ch == "W"))
    return out


# what grows where, once for every theme: (cell, which-of-two-shapes, variant, sway phase); ponds apart
TREES, PONDS = [], []
for _wy in range(GROUND.h):
    for _wx in range(GROUND.w):
        _kind = _scenery(_wx, _wy)
        if _kind == "pond":
            PONDS.append((_wx, _wy))
        elif _kind in ("tree", "pine"):
            _k = _hash(_wx, _wy, 7)
            TREES.append((_wx, _wy, 1 if _kind == "pine" else 0, (_k >> 5) % 2 + 2 * ((_k >> 8) % 2), _k % 4,
                          (_k >> 14) % 3, _k >> 12))
THORN_CELLS = [(x, y) for y in range(GROUND.h) for x in range(GROUND.w) if GROUND.thorn(x, y)]


def shown(theme: dict, tree: tuple) -> bool:
    """Whether this tree is drawn in this theme: the dunes thin their wood so the sand shows between the palms."""
    return not (theme["thin"] and (tree[6] % theme["thin"]) == 0)


# Where flora and critters stand: bare forest the trees and ponds do not cover (so the edge of the wood, never the path).
# Each is (cell, hash). A stand is three cells wide and two tall and marks them taken so two never overlap.
_TAKEN = set()
for _wx, _wy, *_rest in TREES:
    _TAKEN.update((_a, _b) for _a in range(_wx - 1, _wx + 3) for _b in range(_wy - 1, _wy + 2))
for _wx, _wy in PONDS:
    _TAKEN.update((_a, _b) for _a in range(_wx - 1, _wx + 3) for _b in range(_wy, _wy + 3))


def _stands(salt: int, rate: int) -> list:
    out = []
    for wy in range(GROUND.h - 1):
        for wx in range(GROUND.w - 2):
            if _hash(wx, wy, salt) % rate:
                continue
            block = [(wx + a, wy + b) for a in range(3) for b in range(2)]
            if any((not GROUND.stone(*c)) or _building(*c) or c in _TAKEN for c in block):
                continue
            _TAKEN.update(block)
            out.append((wx, wy, _hash(wx, wy, salt + 1)))
    return out


DRESS = _stands(23, 3)
CRITS = _stands(29, 5)


def _paint_forest_cell(patch, theme, wx, wy, edges):
    """Forest floor with its dressing (a decal of the theme on one cell in three, a dark fleck on some), and a lit lip
    plus a rim on every side that faces the path."""
    k = _hash(wx, wy, 3)
    if k % theme["decor_rate"] == 0:
        kind = theme["decor"][(k >> 4) % len(theme["decor"])]
        blit(patch, 0, 0, decal_art(kind, theme, k >> 9))
    elif k % 2:                                           # the season's own floor texture
        blit(patch, 0, 0, tex_art(FLOOR_TEX, theme["tex"], theme, k >> 4, "floor"))
    n, s, w, e = edges
    if n:
        patch[1, :] = theme["base_hi"]
    if w:
        patch[:, 1] = theme["base_hi"]
    if n:
        patch[0, :] = theme["rim"]
    if s:
        patch[3, :] = theme["rim"]
    if w:
        patch[:, 0] = theme["rim"]
    if e:
        patch[:, 3] = theme["rim"]


def _paint_path_cell(patch, theme, wx, wy, stone_n, stone_w):
    """Walkable ground: a few tidy two-pixel pebbles that each throw a shadow, now and then a worn lighter streak, and
    a cast shadow under every forest or wall edge to the north and west."""
    patch[:] = theme["path"]
    k = _hash(wx, wy, 11)
    if k % 11 == 0:
        y, x = (k >> 3) % 2 + 1, (k >> 6) % 2
        patch[y, x:x + 2] = theme["path_hi"] if theme["path_hi"] != theme["path"] else theme["speck"]
        patch[y + 1, x:x + 2] = theme["speck"]
    elif k % 13 == 5:
        patch[(k >> 4) % 2 + 1, 1:3] = theme["path_hi"]
    elif k % 9 == 2:                                      # a faint texture of the season (grass hairs, leaves, cobbles...)
        blit(patch, 0, 0, tex_art(PATH_TEX, theme["ptex"], theme, k >> 4, "path"))
    if stone_n:
        patch[0, :] = theme["path_lo"]
    if stone_w:
        patch[:, 0] = theme["path_lo"]


def _paint_house(img, theme, bx, by, sanctum):
    """Floor, then the house picture over it with its doorway opened (the path shows through) and a gold-lintelled arch,
    then the eave shadow that falls on the back of the floor."""
    x0, y0 = (bx - 2) * CELL, (by - 2) * CELL
    img[y0 + CELL:y0 + 4 * CELL, x0 + CELL:x0 + 4 * CELL] = floor_art(theme, sanctum)
    house = house_sprite(theme, sanctum)
    door, side = _door_of(bx, by)
    dx, dy = door[0] - (bx - 2), door[1] - (by - 2)
    house[dy * CELL:(dy + 1) * CELL, dx * CELL:(dx + 1) * CELL] = -1          # the doorway: the path shows through
    blit(img, x0, y0, house)
    eave = EAVES[theme["house"] % 6] if not sanctum else EAVES[0]
    roof_shade = YEL if sanctum else theme["roof"][1]
    for i, ch in enumerate(eave):
        under_door = side == "N" and 8 <= 4 + i < 12
        if ch != "." and not under_door:
            dot(img, x0 + CELL + i, y0 + CELL, {"S": roof_shade, "M": BLK, "w": WHT}[ch])
    face = WHT if sanctum else theme["wall"][0]
    blit(img, door[0] * CELL, door[1] * CELL, door_arch(side, face))
    # the house throws a two-pixel shadow to the south and east, but only onto bare path
    shade = theme["path_lo"]
    for y in range(y0 + 5 * CELL, y0 + 5 * CELL + 2):
        for x in range(x0 + 2, x0 + 5 * CELL + 2):
            if img[y, x] == theme["path"]:
                img[y, x] = shade
    for x in range(x0 + 5 * CELL, x0 + 5 * CELL + 2):
        for y in range(y0 + 2, y0 + 5 * CELL):
            if img[y, x] == theme["path"]:
                img[y, x] = shade


def _build_world(theme: dict) -> np.ndarray:
    img = np.full((GROUND.h * CELL, GROUND.w * CELL), theme["base"], dtype=np.int16)
    stone = GROUND.stone

    def cell(x, y):
        return img[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL]

    for wy in range(GROUND.h):
        for wx in range(GROUND.w):
            patch = cell(wx, wy)
            if (wx, wy) in WALLS:
                continue
            if stone(wx, wy):
                edges = (not stone(wx, wy - 1), not stone(wx, wy + 1), not stone(wx - 1, wy), not stone(wx + 1, wy))
                _paint_forest_cell(patch, theme, wx, wy, edges)
                for dx, dy, px, py in CORNERS:               # convex forest corners are rounded off to path
                    if not stone(wx + dx, wy) and not stone(wx, wy + dy):
                        patch[py, px] = theme["path"]
            else:
                _paint_path_cell(patch, theme, wx, wy, stone(wx, wy - 1), stone(wx - 1, wy))

    # the soft shadows under every tree; the trees themselves are live sprites that sway
    for tree in TREES:
        wx, wy = tree[0], tree[1]
        if not shown(theme, tree):
            continue
        for sx in range(-1, 9):
            dot(img, wx * CELL + sx, wy * CELL + 8, theme["base_lo"])
        for sx in range(1, 7):
            dot(img, wx * CELL + sx, wy * CELL + 9, theme["base_lo"])
    for bx, by in GROUND.shrines:
        _paint_house(img, theme, bx, by, False)
    _paint_house(img, theme, GROUND.sanctum[0], GROUND.sanctum[1], True)
    return img


_WORLDS: dict = {}


def world_picture(index: int) -> np.ndarray:
    """The whole-world picture for a level, built the first time it is needed."""
    if index not in _WORLDS:
        _WORLDS[index] = _build_world(THEMES[index % len(THEMES)])
    return _WORLDS[index]


# ===================================================================================================================
# PART SIX: the camera window. A display layer over the (larger than the screen) world: it cuts the camera window out
# of the level's pre-drawn picture and draws every live sprite on top, back to front.
# ===================================================================================================================
# A lost run washes the world dim and red: each colour maps to a darker, warmer one (the creatures are drawn after).
LOSS_TINT = np.array([PNK, BLK, BLK, BLK, BLK, BLK, MAR, RED, MAR, PUR, BLU, ORG, RED, MAR, MAR, MAR], dtype=np.int16)
# the storm cloud over a lost run, and the dark vignette that closes in from the edges of the picture
CLOUD = art(("...kkkk.kkk..", ".kkuuuukuuukk", "kuuuuuuuuuuuk", "kuuwuuuuuwuuk", "kuuuukkkuuuuk", ".kkkkkkkkkkk."))
VIGNETTE = np.zeros((PLAY_H, SCREEN), dtype=bool)
for _y in range(PLAY_H):
    for _x in range(SCREEN):
        _edge = min(_x, SCREEN - 1 - _x, _y, PLAY_H - 1 - _y)
        VIGNETTE[_y, _x] = _edge < 2 or (_edge < 5 and (_x + _y) % 2 == 0)
DIRS8 = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
_CACHE: dict = {}


def cached(key, make):
    """Sprites are small numpy arrays; build each pose once and reuse it every frame."""
    if key not in _CACHE:
        _CACHE[key] = make()
    return _CACHE[key]


def draw_counter(frame: np.ndarray, left: int, full: int, accent: int) -> None:
    """The fixed strip under the world: a black band with the level's accent line on top, the coarse bar (one block per
    COUNTER_UNIT moves) over a dark track as long as the level's whole counter, and the fine row under it that drains
    one pixel per move. Same information as se01's strip, in brighter colours."""
    frame[PLAY_H:, :] = BLK
    frame[PLAY_H, :] = accent
    blocks_full = -(-full // COUNTER_UNIT)
    blocks = -(-max(0, left) // COUNTER_UNIT)
    fine = left - COUNTER_UNIT * (blocks - 1) if left > 0 else 0
    frame[PLAY_H + 1:PLAY_H + 3, 1:1 + blocks_full] = COUNTER_TRACK
    frame[PLAY_H + 1:PLAY_H + 3, 1:1 + blocks] = COUNTER_BAR
    frame[PLAY_H + 3, 1:1 + fine] = COUNTER_TICK


def x_of(cell_coord: int, cam_px: int) -> int:
    """Screen pixel of the middle of a cell."""
    return cell_coord * CELL + CELL // 2 - cam_px


class Window(RenderableUserDisplay):

    def __init__(self, game: "Se02") -> None:
        super().__init__()
        self._g = game

    def _lerp(self, a: int, b: int, k: int) -> int:
        """Pixel position a third (k=1), two thirds (k=2) or all (k=3) of the way from cell a to cell b."""
        return a * CELL + int(round((b - a) * CELL * k / 3))

    # ---- the pieces, each a small method so render_interface reads as the layer list ----------------------------------
    def _ponds(self, frame, theme, camx, camy):
        phase = self._g.beat % 4
        for (wx, wy) in PONDS:
            x, y = wx * CELL - 2 - camx, wy * CELL - camy
            shape = (wx // 2 + wy // 2) % 2
            if -12 < x < SCREEN and -9 < y < PLAY_H:
                blit(frame, x, y, cached(("pond", theme["name"], phase, shape), lambda: pond_art(phase, theme, shape)))

    def _trees(self, frame, theme, camx, camy, k, ruined=False):
        """Every tree on screen, back to front, as a live sprite: the crown slides a pixel and the tip bends on a slow
        beat, each tree on its own phase, so the wood ripples. Nothing about a tree is a rule."""
        t = self._g.beat * 3 + k
        for tree in TREES:
            wx, wy, which, variant, ph, cv, _ = tree
            x, y = wx * CELL - 2 - camx, wy * CELL - 4 - camy
            if -12 < x < SCREEN and -12 < y < PLAY_H + 4 and shown(theme, tree):
                sway = -1 if ruined else (0, 1, 0, -1)[(t // 4 + ph) % 4]      # a lost run: every crown droops one way
                spr = cached(("tree", theme["name"], which, variant, sway, cv),
                             lambda: tree_art(theme, which, variant, sway, cv))
                blit(frame, x, y, spr)

    def _dress(self, frame, theme, camx, camy, k):
        """Flora at the edge of the wood: poppies and bushes, leaf piles, glowing mushrooms, reeds. Each sways, pulses or
        glints on its own beat; none of it is ever on the path."""
        t = self._g.beat * 3 + k
        for wx, wy, h in DRESS:
            x, y = wx * CELL - camx, wy * CELL - camy
            if -9 < x < SCREEN and -8 < y < PLAY_H:
                kind = theme["flora"][(h >> 3) % 2]
                hues = FLORA[kind]["hues"]
                hue = hues[(h >> 5) % len(hues)]
                phase = (t // 2 + h) % 4
                blit(frame, x, y + 9 - len(FLORA[kind]["rows"]), cached(("flora", kind, hue, phase), lambda: flora_art(kind, hue, phase)))

    def _critters(self, frame, theme, camx, camy, k):
        """The season's small animal, sat in the forest: it hops a pixel, twitches and blinks, and never moves cell."""
        t = self._g.beat * 3 + k
        kind = theme["critter"]
        for wx, wy, h in CRITS:
            x, y = wx * CELL - camx, wy * CELL - camy
            if -9 < x < SCREEN and -8 < y < PLAY_H:
                pose = 2 if (t + h) % 11 == 0 else ((t // 3 + h) % 2)
                hop = -1 if (t // 3 + h) % 5 == 0 else 0
                spr = cached(("critter", kind, pose), lambda: critter_art(kind, pose))
                blit(frame, x + (12 - spr.shape[1]) // 2, y + 8 - spr.shape[0] + hop, spr)

    def _thorns(self, frame, camx, camy):
        """The brambles: asleep, awake when the pilgrim is within two cells, furious on the one he walked into."""
        g = self._g
        beat = g.beat
        for (wx, wy) in THORN_CELLS:
            x, y = wx * CELL - camx, wy * CELL - camy
            if -8 < x < SCREEN and -8 < y < PLAY_H:
                near = max(abs(wx - g.x), abs(wy - g.y))
                pose = 2 if (g.bump == (wx, wy) and g.hit) else (1 if near <= 2 else 0)
                blit(frame, x - 2, y - 3, cached(("thorn", pose, (beat + wx + 2 * wy) % 2), lambda: thorn_art(pose, beat + wx + 2 * wy)))

    def _seals(self, frame, lv, camx, camy, k):
        """Seal slabs joined into gates; the colour just lit crumbles away over the three frames and throws sparkles."""
        g = self._g
        live = {c for c in lv.seals if lv.seals[c] not in g.lit or (lv.seals[c] == g.just and k < 3)}
        for (wx, wy) in live:
            x, y = wx * CELL - camx, wy * CELL - camy
            if not (-4 < x < SCREEN and -4 < y < PLAY_H):
                continue
            colour = lv.seals[(wx, wy)]
            same = lambda c: c in live and lv.seals[c] == colour
            tile = seal_tile(colour, not same((wx, wy - 1)), not same((wx, wy + 1)), not same((wx - 1, wy)))
            if colour == g.just and k < 3:
                drop = 30 if k == 1 else 65
                for ty in range(CELL):
                    for tx in range(CELL):
                        if _hash(wx * CELL + tx, wy * CELL + ty, 5) % 100 < drop:
                            tile[ty, tx] = self._ground(wx, wy)
                if _hash(wx, wy, 9) % 3 == 0:
                    sparkle(frame, x + 2, y + 2 - 3 * k, k - 1, SEAL_LIGHT[colour])
            blit(frame, x, y, tile)

    def _ground(self, wx, wy):
        return THEMES[self._g.level_index % len(THEMES)]["path"]

    def _shrines(self, frame, theme, camx, camy, k, front):
        """The braziers: identical to look at, lit ones throw a flame that flares as it is lit and rise sparks. The
        one the pilgrim stands on (`front`) is drawn after him, so its flame is never hidden behind his hood."""
        g = self._g
        for i, (wx, wy) in enumerate(GROUND.shrines):
            if ((g.x, g.y) == (wx, wy)) != front:
                continue
            x, y = wx * CELL - camx, wy * CELL - camy
            if not (-8 < x < SCREEN + 4 and -6 < y + 6 < PLAY_H + 8):
                continue
            size = 0
            if i in g.lit:
                size = (2, 4, 6)[k - 1] if (i == g.just and k < 3) else 6
            blit(frame, x - 1, y - 6, cached(("brazier", size, g.beat % 2), lambda: brazier(size, g.beat)))
            if size == 6:                                          # a lit dais breathes: four gold motes round the bowl
                for ox, oy in ((-3, 2), (6, 2), (-2, 4), (5, 4)):
                    dot(frame, x + ox, y + oy, YEL if (g.beat + ox) % 2 else theme["glow"])
            if size == 6:                                          # two embers rise and fade over the beat
                for j in range(2):
                    rise = (g.beat * 3 + k + 4 * j) % 8
                    dot(frame, x + 1 + (j * 2) + (rise % 2), y - 7 - rise, ORG if rise < 4 else YEL)
            if i == g.just and k < 3:
                sparkle(frame, x + 2, y - 4, k, theme["glow"])

    def _sanctum(self, frame, camx, camy):
        """The portal on the win cell, and a banner on every roof."""
        g = self._g
        sx, sy = GROUND.sanctum
        blit(frame, sx * CELL - 2 - camx, sy * CELL - 2 - camy, cached(("portal", g.beat % 12), lambda: portal_art(g.beat)))
        theme = THEMES[g.level_index % len(THEMES)]
        for bx, by, ry in SHRINE_BOXES:
            x, y = bx * CELL + 1 - camx, ry * CELL - 5 - camy
            if -6 < x < SCREEN and -6 < y < PLAY_H:
                colour = YEL if (bx, by) == GROUND.sanctum else theme["glow"]
                blit(frame, x, y, cached(("flag", colour, g.beat % 2), lambda: flag_art(colour, g.beat)))

    def _houses(self, frame, theme, camx, camy, k):
        """Life in the buildings: candle-lit windows that flicker, a puff of chimney smoke that climbs and fades, and over
        the sanctum a slow fall of gold glitter. Purely decoration; every shrine keeps its own rhythm."""
        t = self._g.beat * 3 + k
        for n, (bx, by, _) in enumerate(SHRINE_BOXES):
            x0, y0 = (bx - 2) * CELL - camx, (by - 2) * CELL - camy
            if not (-20 < x0 < SCREEN and -24 < y0 < PLAY_H + 2):
                continue
            sanctum = (bx, by) == GROUND.sanctum
            for wx, wy, glint in cached(("windows", theme["house"], bx, by), lambda: _window_pixels(bx, by, theme["house"])):
                beat = (t // 2 + n + wx) % 4
                colour = (WHT, YEL, YEL, ORG)[beat] if glint else (YEL, ORG, YEL, WHT)[beat]
                dot(frame, x0 + wx, y0 + wy, colour)
            if sanctum:                                      # gold glitter drifting down from the crown
                for j in range(4):
                    fall = (t // 2 + 3 * j) % 8
                    dot(frame, x0 + 3 + 4 * j + (fall % 2), y0 - 1 + fall // 2, YEL if (t + j) % 3 else WHT)
            else:                                            # smoke from a chimney on the right of the roof
                for j in range(3):
                    rise = (t // 2 + 3 * j + n) % 9
                    if rise < 8:
                        dot(frame, x0 + 15 + ((rise + j) // 3) % 2 * (1 if j % 2 else -1), y0 - 1 - rise,
                            theme["smoke"][0] if rise < 4 else theme["smoke"][1])

    def _props(self, frame, lv, theme, camx, camy):
        g = self._g
        for i, q in enumerate(lv.props):
            x, y = q["pos"][0] * CELL - camx, q["pos"][1] * CELL - camy
            pose = 1 if (g.beat + i) % 4 < 2 else 0
            kind = theme["props"][i % 2]
            spr = cached(("prop", kind, q["hue"], pose), lambda: prop_art(kind, q["hue"], pose, theme))
            if -8 < x < SCREEN and -10 < y < PLAY_H:
                blit(frame, x - (spr.shape[1] - CELL) // 2, y + CELL - spr.shape[0], spr)

    def _life(self, frame, theme, camx, camy, k):
        """A few things that drift and do nothing: seen only over the forest, hidden behind it when they cross a path."""
        g = self._g
        t = g.beat * 3 + k
        for kind, first, count in ((theme["life"], 0, 6), (theme["life2"], 10, 5)):
            for i in range(first, first + count):
                dx, dy = life_position(kind, i, t, g.level_index)
                sx, sy = (dx - camx // 2) % SCREEN, (dy - camy // 2) % PLAY_H
                if not GROUND.stone((camx + sx) // CELL, (camy + sy) // CELL):
                    continue
                for ox, oy, colour in life_pixels(kind, i, t, g.level_index):
                    dot(frame, sx + ox, sy + oy, colour)

    def _creatures(self, frame, theme, camx, camy, k, ruined):
        """The pilgrim and the patrols, back to front. Faces react: the pilgrim blinks now and then, winces when he is
        caught, cheers on the portal and lies dizzy and tearful when the run is over; the patrol that caught him throws
        its fists up and grins and hops, the others look down."""
        g = self._g
        drawn = []
        gloater = ruined and any((f["x"], f["y"]) == (g.x, g.y) for f in g.foes)   # a patrol stands over the fallen
        for f in g.foes:
            fx = self._lerp(f["px"], f["x"], k) - camx
            fy = self._lerp(f["py"], f["y"], k) - camy
            heading = (f["dx"], f["dy"]) if not f["back"] else (-f["dx"], -f["dy"])
            caught_him = bool(g.hit) and (f["x"], f["y"]) == (g.x, g.y)
            mood = "glee" if (caught_him and (k >= 2 or ruined)) else ("shy" if (ruined and g.hit) else "calm")
            hop = -((g.beat + k) % 2) if mood == "glee" and ruined else 0
            spr = cached(("imp", heading, (f["t"] + k // 2) % 2, mood), lambda: imp(heading, f["t"] + k // 2, mood))
            lean = 3 if (mood == "glee" and ruined) else 0                # it steps aside so both can be seen
            drawn.append((fy, "imp", spr, fx - (spr.shape[1] - 7) // 2 - 2 + lean, fy - 4 + hop))
        if g.hit and k < 3 and g.bump is not None:
            half = (g.bump[0] - g.prev_x, g.bump[1] - g.prev_y)
            px = g.prev_x * CELL + int(round(half[0] * CELL * k / 6)) - camx
            py = g.prev_y * CELL + int(round(half[1] * CELL * k / 6)) - camy
        else:
            px = self._lerp(g.prev_x, g.x, k) - camx
            py = self._lerp(g.prev_y, g.y, k) - camy
        hop = 0
        if g.flash:                                         # the pilgrim leaps for joy on the portal
            hop = (0, 3, 5, 3, 1, 0)[min(5, g.FLASH_FRAMES - g.flash)]
        if ruined:
            drawn.append((py, "pilgrim", FALLEN, px - 3 - (2 if gloater else 0), py - 3))
        else:
            mood = "cheer" if g.flash else ("wince" if (g.hit and k < 3) else
                                            ("blink" if (g.beat * 3 + k) % 13 == 0 else "calm"))
            spr = cached(("pilgrim", g.face, (g.beat + k // 2) % 2, mood), lambda: pilgrim(g.face, g.beat + k // 2, mood))
            drawn.append((py - hop, "pilgrim", spr, px - 2 - (spr.shape[1] - 7) // 2, py - 6 - hop))
        for foot, kind, spr, x, y in sorted(drawn, key=lambda d: d[0]):
            if kind == "pilgrim" and not ruined:           # a soft shadow on the ground under his feet
                frame[max(0, min(PLAY_H - 1, py + 4)), max(0, px - 1):max(0, px + 5)] = theme["path_lo"]
            elif kind == "imp":
                frame[max(0, min(PLAY_H - 1, foot + 4)), max(0, x + 1):max(0, x + 6)] = theme["path_lo"]
            blit(frame, x, y, spr)
        if ruined:                                          # dizzy stars circle the fallen pilgrim's head, a tear falls
            for j in range(3):
                a = (g.beat + j * 3) % 8
                dot(frame, px + 1 + DIRS8[a][0] * 3, py - 4 + DIRS8[a][1], YEL)
            blit(frame, px + 4, py - 3 + (g.beat % 2), FALLEN_TEAR)
            cx, cy = max(0, px - 5), max(2, py - 16)             # a small storm cloud sulks over him and rains
            blit(frame, cx, cy, CLOUD)
            for j in range(5):
                fall = (g.beat * 2 + k + 3 * j) % 9
                dot(frame, cx + 2 + 2 * j, cy + 6 + fall, BLU if fall % 2 else LBL)
            if g.beat % 3 == 0:                                  # and now and then a bolt
                for bx, by in ((cx + 6, cy + 6), (cx + 5, cy + 7), (cx + 6, cy + 8), (cx + 5, cy + 9)):
                    dot(frame, bx, by, YEL)
        return px, py

    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        g = self._g
        lv = g.arrangement
        theme = THEMES[g.level_index % len(THEMES)]
        k = max(1, min(3, g.tick))
        ruined = bool(g.dead and k >= 3)                    # the run is over: the slide has finished and the world dims
        if g.hit and k < 3:                                  # a catch: the picture holds still while the burst plays
            camx, camy = g.prev_cam[0] * CELL, g.prev_cam[1] * CELL
        else:
            camx = self._lerp(g.prev_cam[0], g.cam_x, k)
            camy = self._lerp(g.prev_cam[1], g.cam_y, k)
        frame[:PLAY_H] = world_picture(g.level_index)[camy:camy + PLAY_H, camx:camx + SCREEN]

        self._ponds(frame, theme, camx, camy)
        self._trees(frame, theme, camx, camy, k, ruined)
        self._dress(frame, theme, camx, camy, k)
        self._critters(frame, theme, camx, camy, k)
        self._props(frame, lv, theme, camx, camy)            # props sit UNDER the gates and thorns, so they hide nothing
        self._life(frame, theme, camx, camy, k)
        self._thorns(frame, camx, camy)
        self._seals(frame, lv, camx, camy, k)
        self._houses(frame, theme, camx, camy, k)
        self._shrines(frame, theme, camx, camy, k, False)
        self._sanctum(frame, camx, camy)
        if ruined:                                           # dim and redden the world, then draw the creatures true
            frame[:PLAY_H] = LOSS_TINT[frame[:PLAY_H]]
            frame[:PLAY_H][VIGNETTE] = BLK                   # and close the edges in
        px, py = self._creatures(frame, theme, camx, camy, k, ruined)
        self._shrines(frame, theme, camx, camy, k, True)

        sx, sy = GROUND.sanctum
        if g.hit and k < 3 and g.bump is not None:
            bx, by = g.bump[0] * CELL + 2 - camx, g.bump[1] * CELL + 2 - camy
            burst(frame, bx, by, k + 1, FOE_BODY)
            sparkle(frame, bx, by, 2, WHT)
        if g.flash:                                          # the level is won: a shower of the season's petals
            step = g.FLASH_FRAMES + 1 - g.flash
            for j in range(48):
                n = _hash(j, g.level_index, 61)
                y = -(n >> 8) % 24 - 6 + step * 13 + (j % 3)
                x = (n % SCREEN) + int(2 * np.sin(step + j))
                colour = theme["confetti"][j % len(theme["confetti"])]
                if 0 <= y < PLAY_H:
                    dot(frame, x, y, colour)
                    dot(frame, x + 1, y + (j % 2), colour)
        if g.flash:                                          # the sanctum door flares, stars burst out and rise
            r = 2 * (g.FLASH_FRAMES + 1 - g.flash)
            cx, cy = x_of(sx, camx), x_of(sy, camy)
            burst(frame, cx, cy, r, YEL if g.flash % 2 else LBL)
            for j, (dx, dy) in enumerate(DIRS8):
                reach = r + 3 + (j % 2) * 3
                sparkle(frame, cx + dx * reach, cy + dy * reach - (g.FLASH_FRAMES - g.flash), 2 - (g.flash > 3),
                        (YEL, theme["glow"], WHT)[j % 3])
        if g.hit:
            frame[0, :] = FOE_BODY
            frame[PLAY_H - 1, :] = FOE_BODY
            frame[:PLAY_H, 0] = FOE_BODY
            frame[:PLAY_H, SCREEN - 1] = FOE_BODY
        draw_counter(frame, g.moves_left, g.budget, theme["glow"])   # last, so nothing from the world spills into the strip
        return frame


# ===================================================================================================================
# PART SEVEN: the game. The rule code below is se01's, line for line; only the class name and game id differ.
# ===================================================================================================================
class Se02(ARCBaseGame):

    FLASH_FRAMES = 5

    def __init__(self) -> None:
        self.arrangement = ARRANGEMENTS[0]
        self.cam_x = self.cam_y = 0
        self.x, self.y = GROUND.start
        self.lit: set = set()
        self.budget = self.moves_left = BUDGETS[0]
        self.dead = False
        self.foes: list = []
        self.flash = 0
        self.hit = 0
        self.beat = 0
        # art bookkeeping only (the rules never read these): where things stood before this move, which way the
        # pilgrim faces, which shrine was just lit, where a catch happened, and how far the slide has played
        self.prev_x, self.prev_y = GROUND.start
        self.prev_cam = (0, 0)
        self.face = (0, 1)
        self.just = None
        self.bump = None
        self.tick = 3
        self.tail = 0
        camera = Camera(width=SCREEN, height=SCREEN, background=VOID, letter_box=VOID,
                        interfaces=[Window(self)])
        super().__init__(game_id="se02", levels=build_levels(),
                         available_actions=[1, 2, 3, 4], camera=camera)
        self._enter(0)

    def _enter(self, index: int) -> None:
        lv = self.arrangement = ARRANGEMENTS[index]
        self.x, self.y = GROUND.start
        self.lit = set()
        self.budget = self.moves_left = BUDGETS[index]     # the counter is full again on entry and on RESET
        self.dead = False
        self.foes = [dict(x=f["ox"], y=f["oy"], ox=f["ox"], oy=f["oy"], dx=f["dx"],
                          dy=f["dy"], ln=f["ln"], t=0, back=False, px=f["ox"], py=f["oy"])
                     for f in lv.foes]
        self.flash = 0
        self.hit = 0
        self.beat = 0                                  # the art's animation phase starts over with the level
        self.face, self.just, self.bump = (0, 1), None, None
        self.tick, self.tail = 3, 0
        self._follow()
        self.prev_x, self.prev_y = self.x, self.y
        self.prev_cam = (self.cam_x, self.cam_y)
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
        found = self.current_level.get_sprites_by_name("body")
        if found:
            found[0].set_position(self.x * CELL, self.y * CELL)

    def _follow(self) -> None:
        self.cam_x = max(0, min(max(0, GROUND.w - VIEW), self.x - VIEW // 2))
        self.cam_y = max(0, min(max(0, GROUND.h - VIEW_ROWS), self.y - VIEW_ROWS // 2))
        self.camera.x = self.cam_x * CELL
        self.camera.y = self.cam_y * CELL

    def passable(self, x: int, y: int) -> bool:
        if GROUND.stone(x, y) or GROUND.thorn(x, y):
            return False
        colour = self.arrangement.seals.get((x, y))
        return colour is None or colour in self.lit

    def _step_foes(self) -> None:
        for f in self.foes:
            f["t"] += -1 if f["back"] else 1
            if f["t"] >= f["ln"]:
                f["t"], f["back"] = f["ln"], True
            elif f["t"] <= 0:
                f["t"], f["back"] = 0, False
            f["x"], f["y"] = f["ox"] + f["dx"] * f["t"], f["oy"] + f["dy"] * f["t"]

    def _caught(self) -> bool:
        return any((f["x"], f["y"]) == (self.x, self.y) for f in self.foes)

    def step(self) -> None:
        if self.flash:
            self.flash -= 1
            self.tick = min(3, self.tick + 1)          # the last slide frames play while the door flares
            if self.flash == 0:
                self.next_level()
                self.complete_action()
            return
        if self.tail:                                  # the rest of the slide for the move already made
            self.tail -= 1
            self.tick += 1
            if self.tail == 0:
                if self.dead:                          # the catch burst or the last move has played: run over
                    self.lose()
                self.complete_action()
            return

        self.hit = 0
        self.beat += 1
        self.just = None
        self.bump = None
        delta = {GameAction.ACTION1: (0, -1), GameAction.ACTION2: (0, 1),
                 GameAction.ACTION3: (-1, 0), GameAction.ACTION4: (1, 0)}.get(
                     self.action.id)
        if delta is None:
            self.complete_action()
            return

        self.moves_left -= 1                           # every accepted move costs one, a bump included
        self.face = delta
        self.prev_x, self.prev_y = self.x, self.y
        self.prev_cam = (self.cam_x, self.cam_y)
        for f in self.foes:
            f["px"], f["py"] = f["x"], f["y"]

        nx, ny = self.x + delta[0], self.y + delta[1]
        if GROUND.thorn(nx, ny):                       # a thorn: the pilgrim recoils and the run is lost
            self.bump = (nx, ny)
            self.hit = 1
        elif self.passable(nx, ny):
            self.x, self.y = nx, ny
            if (nx, ny) in GROUND.shrines:
                i = GROUND.shrines.index((nx, ny))
                if i not in self.lit:
                    self.just = i
                self.lit.add(i)
            if (nx, ny) == GROUND.sanctum:
                self.flash = self.FLASH_FRAMES
                self.tick = 1
                self._follow()
                self._sync()
                return

        self._step_foes()
        if self._caught():
            if self.bump is None:
                self.bump = (self.x, self.y)
            self.hit = 1
        self.dead = bool(self.hit) or self.moves_left <= 0
        self._follow()
        self._sync()
        self.tick, self.tail = 1, 2                    # play the slide: this frame, then two more
