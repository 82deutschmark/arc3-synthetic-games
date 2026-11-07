# Author: Claude Sonnet 5.5
# Date: 07-November-2026
# PURPOSE: ff02, a redraw of ff01 (the fish game in a sea several screens big). THE RULES ARE UNCHANGED: every level's
#   data, the swim and current and tide logic, who can eat whom, the bites and lives, the time bar, the yellow "next
#   heading" pixels and the edge marks for fish off the window all behave exactly as in ff01. What changed is the art:
#   the whole scene is built from named engine Sprites (sea, surface, far landmarks, jellyfish, currents, sea bed,
#   props, kelp, vents, bubbles, every fish, the player, edge marks, the HUD) instead of being painted onto the finished
#   frame; fish are drawn from small pictures with eyes, mouths, fins, bellies, gills and stripes; every level has its own
#   sea bed, its own big shaded landmarks (reef towers, a wrecked ship, a ribcage, ruins) and its own props; a few things
#   move for no reason (kelp, anemones, clams, crabs, jellyfish, vent glow, glints, bubbles, fin shimmer, blinks); a
#   cleared level throws a shower of sparkles and confetti and the fish grins, and a lost run tints the edges red as the
#   fish rolls over with crossed-out eyes.
#   Level data below came from a level generator that is not part of this repository.
# Updated: 07-November-2026, Claude Sonnet 5.5 -- round A: calmer, more readable pictures (less speckle, dither and clutter); rules untouched.
# Updated: 07-November-2026, Claude Sonnet 5.5 -- round B (animation): a move now plays three quick frames (the fish and every other
#   fish glide to their new cell and a short wake trails the fish), a wall bump squints, nudges and puffs, a bite flashes the edges
#   red, a growth flashes the fish, a cleared level shuts as an iris round the fish and opens on the next one, and the sea (kelp,
#   jellyfish, bubbles, glints, fire) keeps moving through those frames. Level-clear confetti and fireworks are thinner. Rules untouched.
# Updated: 07-November-2026, Claude Sonnet 5.5 -- round C (final look): calmer and livelier. The currents have far fewer chevrons, spread evenly,
#   with the streaks kept clear of them; the bed has fewer, roomier props in fewer colours and the landmarks lose their pore, seam and
#   groove speckle; the HUD loses its magenta dots; the fish stretches as it glides and settles on arrival, with a clearer wake of two
#   streaks and a bubble, a bigger bump puff and a thick red frame and white flash on a bite; an eaten fish flashes white and leaves a
#   little star instead of vanishing; the level-clear hop is quick then hovers, with thinner confetti; a lost run closes a solid
#   frame and a round spotlight on the fish instead of a red checker. Rules untouched.
# SRP/DRY check: Pass -- one self-contained game file (the site execs it alone). The rule code is ff01's, moved
#   unchanged into _rules(); everything below it only reads game state and moves sprites. Level data is generated
#   outside this repository and pasted between the GENERATED markers.
# CHANGELOG
# 07-Nov-2026 (Claude Sonnet 5.5): first version. ff01's rules, scene rebuilt as named sprites.
# 07-Nov-2026 (Claude Sonnet 5.5): second pass, critique and redraw. Solid shaded landmarks (towers, spires, wreck, ribs,
#   ruins) replace the faint dithered far shapes and now hang in the middle water of the tall seas too; jellyfish with
#   faces and rising bubbles give the open water life; bed has strata and pebbles; more props (urchin, clam, chest,
#   coral branch, crystal, mushroom coral) and three kelp styles; fish redrawn with eyes, gills, mouths that open, and
#   reactions (blink, chomp after a meal, wince after a bite, grin on a win, crossed-out eyes and a tear on a loss);
#   richer HUD (fish lives, pearls, tide pips, time bar that warms up as it runs out); currents lose the blue ripples;
#   loss tint is now a red vignette so the fish stays readable.
# 07-Nov-2026 (Claude Sonnet 5.5): third pass, variety and life. Three fish species per size with two- and four-pixel eyes and
#   a four-phase tail swing; thirty new props (grass, worms, lanterns, glow-shrooms, lures, wreck and bone-yard and ruin
#   pieces) with per-level sets and spacing, so the lagoon and crystal beds are no longer crowded; each level its own sea
#   (depth fade, far hills, sunlight columns, a drifting thing: sparkles, plankton, embers, spores, ash, orbs, petals);
#   seahorses; floating islands, crystal clusters, coral heads, orbs and wreckage replace the dark floating rocks;
#   landmarks come alive (blinking tower tips and wreck portholes, giant kelp that leans); currents let the sea show through;
#   welcome bubbles, fireworks and streamers on a level clear, a dimmed red run-over with sinking tears.
# 07-Nov-2026 (Claude Sonnet 5.5): fifth pass (round A, calm and readable): the dither across the deep water is gone (flat sea, one
#   thin seam above the floor), landmarks, hills, sand and sunlight columns lose their speckle, currents have half the streaks,
#   and fewer, further-apart props, specks, bubbles, glints, jellyfish and floaters leave the fish and currents room.
# 07-Nov-2026 (Claude Sonnet 5.5): fourth pass, polish. Level one's volcano vents are red and yellow with no black dots (they read
#   as eyes on the purple hills); the short seas' far hills are lower and level one's are dark red; the deep-water dither starts
#   later and is thinner (levels three and six were noisy); floating things keep out of the current lanes and away from the
#   fish's starting spots; drifting specks stay out of the currents; the tall seas get a few more floaters.
#
# 07-Nov-2026 (Claude Sonnet 5.5): sixth pass (round B, animation). One action = three frames (FR): rules run once on the first
#   frame and the rest only tween the picture (fish and camera glide, currents slide, wake, bump, bite flash), so the final frame is
#   the same state as before. Iris close on a level clear and open on the next. Win shower/confetti/fireworks thinned.
#
# How the picture is built (so the next person can find things):
#   * The engine camera is moved over a world-sized scene. Every sprite's y is the world y plus HUD_H, so the four HUD
#     rows sit above world row 0 and the camera (which follows the fish exactly as ff01's window did) lines up.
#   * Fish art is text rows. Where a fish's "next heading" pixel goes is worked out from ff01's silhouette (_TELL_ART),
#     so it is in exactly the old place whatever the new art looks like. Hit boxes are the old boxes (FISH_W / FISH_H).
#   * Anything that animates only changes with the game's own step counter, so the picture is a pure function of state.

import math
import random
from functools import lru_cache

import numpy as np
from arcengine import ARCBaseGame, BlockingMode, Camera, GameAction, Level, Sprite

# ---------------------------------------------------------------------------
# Screen and palette (same numbers as ff01; greys 1-4 are never used)
# ---------------------------------------------------------------------------
SCREEN = 64
HUD_H = 4                  # rows 0-3 are the HUD; the window onto the sea is below it
VIEW_W, VIEW_H = SCREEN, SCREEN - HUD_H
FLOOR_ROWS = 6             # the sea bed fills the bottom rows of the world

WHITE, BLACK, MAGENTA, PINK, RED, BLUE, SKY, YELLOW, ORANGE, MAROON, GREEN, PURPLE = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
SEA = BLUE
CURRENT_WATER = SKY
FLOW_MARK = WHITE
NEXT_MARK = YELLOW          # "where this goes next", on currents and on fish alike
PLAYER_C = GREEN
TIER_C = {1: ORANGE, 2: PINK, 3: MAGENTA, 4: RED, 5: MAROON}
HUD_BG = PURPLE

UP, RIGHT, DOWN, LEFT = 0, 1, 2, 3
DV = ((0, -1), (1, 0), (0, 1), (-1, 0))

SWIM = 2                   # player pixels per arrow press
FISH_SPEED = 1
BITE_GRACE = 8             # steps of blinking safety after a bite
WIN_FRAMES = 12
FR = 3                     # frames drawn for one ordinary action: the rules run on the first, the rest only glide the picture
EASE = (0.5, 1.0, 1.0)     # how far through its move each of those frames shows things (art only)
IRIS_CLOSE = (36, 24, 13, 5)   # radius of the iris round the fish over the last four level-clear frames
IRIS_OPEN = (20,)             # radius of the iris on the first frame of the next level; it is fully open one frame later
DEATH_FRAMES = 6


def rise_of(w):
    """How high the cheering fish has hopped by win frame w: a quick hop to the top, then a little hover (round C)."""
    return min(2 * w, 8) + (1 if w > 6 and w % 4 < 2 else 0)

# Layers, low to high. The far landmarks and jellyfish sit under the currents, so a current always reads on top.
(L_SEA, L_FAR, L_SURFACE, L_MID, L_PROP, L_CURRENT, L_BED, L_FISH, L_PLAYER, L_MARK, L_FX, L_WASH,
 L_HUD) = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 20


def _check_rows(name, rows):
    """Import-time guard: every picture row of one picture must be the same length."""
    assert len({len(r) for r in rows}) == 1, f"ragged picture {name}: {[len(r) for r in rows]}"


# ---------------------------------------------------------------------------
# Fish art, facing right. Three species per size, all inside the same box, so every hit box is ff01's.
#   B body  d dark back  b belly  h highlight / spots  s stripe  g gill  f fin (shimmers between two colours)
#   t tail (a fin that also swings: its outer column rises and falls over four frames)
#   e eye white (an eye is two or four of these, with a black pupil k)  k pupil / black
#   m mouth line (black)  M mouth: body colour shut, black when open  . water
# Species 0 is the sleek one (the player is always this one), 1 is the round spotted one, 2 is the long striped one.
# ---------------------------------------------------------------------------
_ART = {
    1: [["t.dBBB.",
         "ttBBekM",
         "t.sbbb."],
        ["tt.dBB.",
         "tBBBekM",
         "tt.bbb."],
        ["t.BdBB.",
         "ttsBekM",
         "t.bsbb."]],
    2: [["....ff...",
         "t..dBsBB.",
         "ttBBBsekM",
         "t..bbsbbm",
         "....f...."],
        ["....f....",
         "t.dBBBee.",
         "ttBBBBekM",
         "t.bbbbbbm",
         "....f...."],
        ["....f....",
         "t.sBsBBB.",
         "ttsBsBekM",
         "t.sbsbbbm",
         "....f...."]],
    3: [[".....ff.....",
         "t..dBBBsBB..",
         "tt.BBBBsBeeB",
         "tttBBBBsgekM",
         "t..bbbbsbbbm",
         ".....f..f..."],
        [".....ff.....",
         "t..dBBhBBBd.",
         "ttBBBBBBBeeB",
         "tttBBhBBBekM",
         "t.bbbbhbbbbm",
         ".....f..f..."],
        [".....ff.....",
         "t.dBBsBBsBB.",
         "ttBBBsBBsBee",
         "tttBBsBBsgek",
         "t.bbbsbbsbbm",
         ".....f..f..."]],
    4: [["......fff......",
         "t....BBdsdBB...",
         "tt..BBBBsBhBeeB",
         "ttttBBBBsBBBekM",
         "tt..bbbbsbbgbbm",
         "t....bbbbsbb...",
         "......f..f....."],
        ["......ff.......",
         "t...dBBBBBBd...",
         "tt.BBBhBBBBBeeB",
         "ttttBBBBBhBBekM",
         "tt.bbbbbbbbbbbm",
         "t...bbbhbbbbb..",
         "......f..f....."],
        [".......f.......",
         "t...dBsBBsBBd..",
         "tt.BBBsBBsBBeeB",
         "ttttBBsBBsBBekM",
         "tt.bbbsbbsbbbbm",
         "t...bbsbbsbb...",
         ".......f......."]],
    5: [["........ffff.......",
         "t......BBdBsBdB....",
         "tt....BBBBBsBBBhB..",
         "ttt..BBBBBBsBBBeeBB",
         "ttttttBBBBBsBBBekBM",
         "ttt..bbbbbbsbbbgbbm",
         "tt....bbbbbsbbbbbb.",
         "t......bbbbsbbbb...",
         "........ff..ff....."],
        ["........ffff.......",
         "t.....dBBBBhBBBd...",
         "tt...BBhBBBBBBBBBB.",
         "ttt.BBBBBBhBBBBeeBB",
         "ttttttBBBBBBBBBekBM",
         "ttt..bbbbhbbbbbgbbm",
         "tt...bbbbbbbbbbbbb.",
         "t.....bbbbhbbbb....",
         "........ff..ff....."],
        ["........ffff.......",
         "t.....dBsBBsBBsBd..",
         "tt...BBBsBBsBBsBBB.",
         "ttt..BBBsBBsBBseeBB",
         "ttttttBBsBBsBBsekBM",
         "ttt..bbbsbbsbbsbbbm",
         "tt...bbbsbbsbbsbbb.",
         "t.....bbsbbsbbsb...",
         "........ff..ff....."]],
}
# ff01's silhouettes, kept ONLY to place the "next heading" pixel exactly where ff01 put it.
_TELL_ART = {
    1: ["f..BBB.", ".BBBBeB", "f..bbb."],
    2: ["....f....", "f..BBBB..", ".fBBBBBeB", "f..bbbbb.", "....f...."],
    3: [".....ff.....", "f...fBsBB...", "ff.BBBsBBBe.", "fffBBBsBBBBk", "f..bbbsbbbb.", ".....f......"],
    4: ["......fff......", "f....BBBsBB....", "ff..BBBBsBBBB..", "ffffBBBBsBBBekB", "ff..bbbbsbbbbb.", "f....bbbbsbb...",
        "......f..f....."],
    5: ["........ffff.......", "f......BBBBsBB.....", "ff....BBBBBsBBBB...", "fff..BBBBBBsBBBBB..", "ffffffBBBBBsBBBekB.",
        "fff..bbbbbbsbbbbbbb", "ff....bbbbbsbbbbb..", "f......bbbbsbbb....", "........ff..ff....."],
}
SPECIES = 3
FISH_W = {s: len(_TELL_ART[s][0]) for s in _TELL_ART}
FISH_H = {s: len(_TELL_ART[s]) for s in _TELL_ART}
for _s in _ART:
    assert len(_ART[_s]) == SPECIES
    for _v, _rows in enumerate(_ART[_s]):
        _check_rows(f"fish{_s}.{_v}", _rows)
        assert len(_rows) == FISH_H[_s] and len(_rows[0]) == FISH_W[_s], (_s, _v)
    _check_rows(f"tell{_s}", _TELL_ART[_s])


def _cells(rows, flip):
    out = []
    w = len(rows[0])
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != '.':
                out.append((w - 1 - x if flip else x, y, ch))
    return tuple(out)


ART_R = {(s, v): _cells(a, False) for s, vs in _ART.items() for v, a in enumerate(vs)}
ART_L = {(s, v): _cells(a, True) for s, vs in _ART.items() for v, a in enumerate(vs)}


def _tell_pixel(cells, w, h, d):
    """The body pixel that shows a fish's next heading: its outermost pixel on that side, on the
    middle row (left/right) or the middle column (up/down). (ff01's rule, unchanged.)"""
    body = [(x, y) for x, y, _ in cells]
    if d in (LEFT, RIGHT):
        row = [p for p in body if p[1] == h // 2] or body
        return min(row) if d == LEFT else max(row)
    col = [p for p in body if p[0] == w // 2] or body
    return min(col, key=lambda p: p[1]) if d == UP else max(col, key=lambda p: p[1])


TELL = {(s, facing, d): _tell_pixel(_cells(_TELL_ART[s], not facing), FISH_W[s], FISH_H[s], d)
        for s in _TELL_ART for facing in (True, False) for d in range(4)}
for (_s, _f, _d), (_tx, _ty) in TELL.items():           # every species must have a body cell under every tell pixel
    for _v in range(SPECIES):
        assert any((x, y) == (_tx, _ty) for x, y, _ in (ART_R if _f else ART_L)[(_s, _v)]), (_s, _v, _f, _d)

# Lives are little fish: tail, back, eye, belly. A lost life is the same fish in silhouette.
LIFE_ICON = ((0, 0, ORANGE), (1, 0, GREEN), (2, 0, GREEN), (3, 0, WHITE), (4, 0, GREEN),
             (0, 1, ORANGE), (1, 1, WHITE), (2, 1, WHITE), (3, 1, GREEN))
LIFE_W = 6

# Fish colours: (body, belly, fin, fin when it shimmers, stripe, dark back). Body colours are ff01's tier colours so that
# the edge marks and the fish agree; yellow is never used on a fish (it is the "next heading" colour).
PAL_TIER = {
    1: (ORANGE, WHITE, MAROON, RED, MAROON, RED),
    2: (PINK, WHITE, MAGENTA, PURPLE, MAGENTA, MAGENTA),
    3: (MAGENTA, PINK, PURPLE, PINK, PURPLE, PURPLE),
    4: (RED, ORANGE, MAROON, MAGENTA, MAROON, MAROON),
    5: (MAROON, RED, PURPLE, RED, RED, BLACK),
}
PAL_PLAYER = (GREEN, WHITE, ORANGE, MAGENTA, PURPLE, PURPLE)
PAL_FLASH = (WHITE, SKY, YELLOW, PINK, PINK, SKY)        # the level-clear flash
PAL_DEAD = (MAROON, RED, PURPLE, PURPLE, BLACK, BLACK)   # a lost run: the fish rolls over, red and dark

EYE_OPEN, EYE_BLINK, EYE_DEAD, EYE_CHEER, EYE_WINCE = range(5)
TAIL_SWING = (0, -1, 0, 1)                                # rows the outer tail column moves over the four phases


@lru_cache(maxsize=None)
def fish_img(pal, size, var, facing, tell, phase, eyes, mouth=0):
    """One fish picture. var = species 0-2; tell = heading whose yellow pixel to show (or None); phase 0-3 = tail swing
    and fin shimmer; eyes: open, blinking (the white takes the body colour, a dark pupil line stays), crossed out with a
    tear (a lost run), cheering (shut, happy) or wincing (squeezed); mouth 1 = open (a chomp after a meal, a cheer)."""
    body, belly, fin, fin2, stripe, dark = pal
    w, h = FISH_W[size], FISH_H[size]
    cells = ART_R[(size, var)] if facing else ART_L[(size, var)]
    sil = {(x, y) for x, y, _ in cells}
    img = np.full((h, w), -1, dtype=np.int8)
    tail_end = 0 if facing else w - 1
    shim = fin if phase % 2 == 0 else fin2
    for x, y, ch in cells:
        if ch == 'e':
            if eyes == EYE_DEAD:                  # crossed out: a black X over the white
                c = BLACK if (x + y) % 2 == 0 else WHITE
            else:
                c = (WHITE, body, BLACK, BLACK, BLACK)[eyes]
        elif ch in 'km':
            c = BLACK
        elif ch == 'M':
            c = BLACK if mouth else body
        elif ch == 't':
            c = shim
            if x == tail_end:                     # the tip of the tail flicks up and down
                y = max(0, min(h - 1, y + TAIL_SWING[phase % 4]))
        else:
            c = {'B': body, 'b': belly, 'h': belly, 'd': dark, 'g': stripe, 'f': shim, 's': stripe}[ch]
            # big fish get a black outline round the body so they read against the water
            if size >= 4 and ch in 'Bbdh' and any((x + dx, y + dy) not in sil for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                c = BLACK
        img[y, x] = c
    if eyes == EYE_DEAD:                      # a tear under the crossed-out eye
        for x, y, ch in cells:
            if ch == 'e' and (x, y + 1) in sil and (x, y + 1) not in {(a, b) for a, b, c2 in cells if c2 == 'e'}:
                img[y + 1, x] = SKY
    if tell is not None:
        tx, ty = TELL[(size, facing, tell)]
        img[ty, tx] = NEXT_MARK
    return img

def bend(img, facing, axis, mode):
    """Squash and stretch for the player's glide (round C). axis 0 = swimming sideways, 1 = up or down. mode +1 stretches the fish
    one pixel along its move (the tail trails), -1 squashes it on arrival (one pixel shorter, a quick settle). The copied or dropped
    line is a column of plain body behind the eye. Returns (picture, x shift, y shift) so the head stays where it was."""
    h, w = img.shape
    col = 2 if facing else w - 3                       # a body column behind the eye, whichever way the fish faces
    row = h // 2
    out, sx, sy = img, 0, 0
    if axis == 0 and mode > 0:
        out = np.insert(out, col, out[:, col], axis=1)
        sx = -1 if facing else 0
    elif axis == 0:
        out = np.delete(out, col, axis=1)
        sx = 1 if facing else 0
    elif mode > 0:
        out = np.insert(out, row, out[row, :], axis=0)
    else:
        out = np.delete(out, col, axis=1)
        sx = 1 if facing else 0
    return out, sx, sy


# ---------------------------------------------------------------------------
# Levels. Each: world w,h; player start and size; meals to grow at; meals to clear; lives;
# tide period; time budget (0 = none); currents [x, y, w, h, strength, headings];
# fish [x, y, size, headings]. Headings: 0 up, 1 right, 2 down, 3 left, one per tide.
# ---------------------------------------------------------------------------
# <<<GENERATED
LEVEL_DATA = [
    {"w": 128, "h": 60, "player": [6, 28], "size": 1, "grow": [], "eat": 2, "lives": 3, "period": 8, "budget": 0, "zones": [[0, 16, 88, 24, 3, [1, 3]]], "fish": [[21, 27, 1, [1, 2, 3]], [8, 4, 1, [3, 1]], [37, 32, 1, [3, 2]], [21, 12, 1, [0, 3]], [29, 39, 1, [1, 0]]]},
    {"w": 192, "h": 60, "player": [6, 28], "size": 1, "grow": [3], "eat": 5, "lives": 3, "period": 8, "budget": 107, "zones": [[0, 16, 160, 16, 3, [3, 1]], [56, 32, 128, 16, 3, [3, 1]]], "fish": [[138, 4, 1, [3, 2, 1]], [22, 11, 1, [1, 0, 2, 0]], [169, 31, 1, [1, 3]], [91, 48, 1, [3, 1, 3, 0]], [152, 11, 1, [1, 2, 0]], [35, 11, 2, [0, 1, 0, 3]], [178, 35, 2, [2, 3, 1]], [108, 44, 1, [2, 1]], [62, 40, 4, [0, 3, 1]]]},
    {"w": 128, "h": 120, "player": [6, 58], "size": 1, "grow": [3], "eat": 6, "lives": 3, "period": 7, "budget": 91, "zones": [[0, 8, 16, 56, 4, [2, 0]], [32, 8, 64, 16, 4, [1, 3, 1, 3]], [56, 48, 64, 16, 4, [0, 2, 3]]], "fish": [[32, 76, 1, [2, 1, 3, 0]], [115, 37, 1, [3, 0, 3, 2]], [119, 59, 1, [3, 1, 3, 1]], [51, 20, 1, [0, 2]], [12, 73, 2, [1, 3, 0]], [106, 40, 1, [0, 1]], [101, 62, 1, [3, 1, 0]], [48, 6, 2, [2, 0, 2, 0]], [37, 84, 1, [1, 3]], [103, 14, 3, [2, 0]], [84, 68, 3, [0, 3, 1, 3]]]},
    {"w": 192, "h": 120, "player": [6, 58], "size": 2, "grow": [3, 7], "eat": 8, "lives": 3, "period": 7, "budget": 170, "zones": [[0, 48, 88, 24, 3, [1, 3]], [96, 16, 16, 96, 2, [1, 2]], [136, 8, 24, 104, 2, [3, 0]]], "fish": [[52, 36, 1, [0, 2]], [80, 70, 1, [0, 2]], [37, 55, 2, [1, 3, 1, 3]], [108, 23, 1, [0, 1, 2]], [129, 105, 4, [1, 3, 2, 3]], [72, 21, 4, [1, 3, 0, 3]], [80, 63, 2, [1, 3, 1, 3]], [27, 39, 4, [3, 2, 3, 1]], [110, 9, 4, [1, 0, 1, 2]], [114, 102, 3, [2, 0]], [53, 21, 3, [1, 2, 3]], [156, 66, 5, [1, 2]], [78, 36, 5, [2, 0, 3]]]},
    {"w": 256, "h": 60, "player": [6, 28], "size": 2, "grow": [4], "eat": 8, "lives": 3, "period": 6, "budget": 135, "zones": [[0, 8, 16, 40, 4, [0, 2, 1, 2]], [24, 16, 120, 16, 3, [3, 1, 2]], [160, 8, 64, 16, 4, [3, 1, 3, 1]], [72, 32, 120, 16, 3, [1, 0]]], "fish": [[77, 15, 2, [1, 2, 3]], [168, 25, 2, [2, 1, 3]], [190, 22, 2, [1, 3, 0]], [225, 29, 1, [1, 3]], [109, 39, 2, [1, 3, 0]], [62, 13, 2, [1, 3, 1, 3]], [162, 34, 3, [0, 2, 0, 1]], [205, 16, 2, [1, 3, 0]], [236, 24, 3, [3, 2, 1]], [96, 48, 3, [3, 1, 0, 1]], [234, 12, 5, [1, 3]], [55, 47, 4, [1, 3, 2]], [57, 2, 4, [3, 0, 1]]]},
    {"w": 192, "h": 180, "player": [6, 88], "size": 2, "grow": [3, 7], "eat": 9, "lives": 3, "period": 7, "budget": 154, "zones": [[0, 80, 72, 24, 4, [1, 2, 1, 3]], [24, 40, 72, 16, 2, [1, 0]], [64, 56, 120, 16, 4, [1, 3, 0]], [0, 8, 104, 24, 3, [0, 3, 2]]], "fish": [[125, 41, 1, [3, 1, 3, 1]], [148, 31, 1, [3, 2]], [66, 88, 1, [0, 1]], [89, 156, 2, [3, 2, 0]], [104, 21, 4, [1, 3, 2]], [127, 54, 4, [2, 3]], [156, 37, 3, [3, 1, 3, 2]], [52, 89, 2, [3, 1, 3, 1]], [94, 164, 3, [0, 2, 0, 2]], [123, 21, 2, [0, 3]], [139, 45, 2, [3, 1]], [149, 3, 5, [1, 3]], [24, 21, 5, [0, 1, 2]], [150, 128, 5, [3, 2, 0]]]},
    {"w": 256, "h": 120, "player": [6, 58], "size": 3, "grow": [4, 8], "eat": 10, "lives": 3, "period": 6, "budget": 168, "zones": [[0, 8, 24, 64, 3, [0, 3, 2]], [24, 64, 152, 16, 3, [1, 3, 1, 3]], [176, 80, 80, 24, 3, [3, 0]], [32, 24, 64, 24, 4, [2, 0, 3, 1]], [136, 16, 64, 16, 3, [1, 3]]], "fish": [[113, 49, 2, [3, 0]], [202, 97, 3, [1, 2, 0, 2]], [34, 34, 3, [2, 1, 3, 1]], [143, 20, 3, [3, 2, 1]], [103, 85, 3, [2, 3, 0, 1]], [216, 52, 4, [1, 3]], [89, 53, 5, [3, 2, 3, 1]], [219, 88, 3, [1, 2, 1, 3]], [41, 42, 4, [3, 1, 2]], [158, 27, 4, [3, 2, 3, 0]], [108, 93, 3, [1, 0, 3]], [220, 37, 5, [3, 1]], [91, 40, 4, [1, 3, 1, 3]], [118, 57, 4, [0, 2, 1]], [169, 12, 4, [0, 1]], [189, 68, 4, [1, 3]]]},
    {"w": 256, "h": 180, "player": [6, 88], "size": 3, "grow": [4, 8], "eat": 11, "lives": 3, "period": 6, "budget": 195, "zones": [[0, 80, 120, 24, 3, [1, 3, 2, 0]], [216, 72, 16, 64, 3, [1, 2, 0]], [48, 56, 112, 16, 3, [3, 1]], [88, 136, 88, 16, 2, [3, 1]], [72, 40, 152, 16, 3, [3, 1]], [32, 152, 104, 16, 4, [1, 3, 1, 3]]], "fish": [[120, 151, 2, [0, 2]], [39, 141, 3, [2, 0, 1]], [46, 38, 3, [2, 3, 1]], [188, 112, 3, [1, 0, 1, 3]], [54, 53, 3, [1, 0]], [104, 64, 5, [3, 0]], [106, 165, 4, [2, 0, 3]], [41, 156, 4, [2, 0, 1]], [49, 30, 3, [2, 3, 0, 1]], [192, 103, 3, [2, 1]], [74, 65, 5, [3, 1, 2]], [80, 77, 5, [1, 2]], [99, 157, 3, [2, 3, 1]], [159, 126, 4, [1, 0, 1, 3]], [190, 75, 4, [0, 1, 2]], [204, 94, 4, [3, 2, 1]], [116, 127, 4, [1, 3, 2, 3]]]},
]
# GENERATED>>>

levels = [Level(sprites=[], grid_size=(SCREEN, SCREEN), name=f"ff02-{i + 1}", data={"i": i})
          for i in range(len(LEVEL_DATA))]

# ---------------------------------------------------------------------------
# Scenery art. Props are text rows: '.' see-through; a b c are the prop's own three colours (main, light, dark);
# w white, k black, g green, r red, o orange, m maroon are fixed. Never yellow (the heading colour), never grey.
# ---------------------------------------------------------------------------
FIXED = dict(w=WHITE, k=BLACK, g=GREEN, r=RED, o=ORANGE, m=MAROON, s=SKY, n=PINK, v=PURPLE, u=BLUE)

PROPS = {
    "fan":    [["b.b.b.b", "ab.a.ba", ".aabaa.", ".aaaaa.", "..aba..", "..aaa..", "...c...", "..ccc.."]],
    "brain":  [["..aaa..", ".abaaba", "aabaaba", "acaacac", "ccccccc"]],
    "tube":   [["..b.b", "b.a.a", "a.a.a", "a.a.c", "a.a.c", "aca.c", "aaaac", "ccccc"]],
    "star":   [["..a..", ".aba.", "aabaa", ".a.a.", "a...a"]],
    "shell":  [["..b..", ".bab.", "babab", ".ccc."]],
    "rock":   [["..bbb..", ".baaaac", "baaaaac", "ccccccc"]],
    "bone":   [["ww...ww", ".wwwww.", "ww...ww"]],
    "amph":   [[".aaa.", "..a..", ".abac", "abaac", "abaac", ".aacc", "..cc."]],
    "anchor": [["..aaa..", "..aba..", "..aaa..", "..aba..", "aaaaaaa", "..aba..", "a.aba.a", ".aabaa.", "..aaa.."]],
    "column": [["bbbbbb", ".bbbbc", ".abaac", ".abaac", ".abaac", ".abaac", ".abgac", ".abaac", ".abaac", ".aaaac", "abbbbc", "aaaaaa"]],
    # new this pass: creatures with faces and a few treasures
    "urchin": [["a.a.a.a", ".aaaaa.", "awkawka", ".aacaa.", "..ccc.."]],
    "chest":  [[".aaaaa.", "abbbbba", "acckcca", "abbbbba", "ccccccc"]],
    "coral":  [["b..b..b", "a..a..a", "ab.a.ba", ".aabaa.", "..aaa..", "..aba..", "..aaa..", "..ccc.."]],
    "crystal": [["...b...", "..bab..", ".bbaab.", ".baaab.", "baaaaab", "baaaaac", "ccccccc"]],
    "shroom": [[".bbbbb.", "baaaaab", "aaaaaaa", "..ccc..", "..ccc.."]],
    # two-frame props: the anemone sways, the crab shuffles its legs, the clam opens on its pearl
    "anemone": [["b.b.b.b", "a.a.a.a", ".a.a.a.", ".aaaaa.", ".acaca.", ".ccccc."],
                [".b.b.b.", ".a.a.a.", "a.a.a.a", ".aaaaa.", ".acaca.", ".ccccc."]],
    "crab":    [[".w...w.", "aaaaaaa", ".acaca.", "a.a.a.a"],
                [".w...w.", "aaaaaaa", ".acaca.", ".a.a.a."]],
    "clam":    [["..bbb..", ".baaab.", "baaaaab", "accccca", ".ccccc."],
                ["bb...bb", "baa.aab", "baawaab", "accccca", ".ccccc."]],
}
# Third-pass props. Same letters as above plus fixed s sky, n pink, v purple, u blue. Several have two or three frames:
# grass and worms sway, lanterns and glow things pulse, a snail waves its feelers, a hermit crab shuffles.
PROPS.update({
    "seagrass": [["b..b..b.", "a..ab.a.", "ab.aa.ab", "aa.aa.aa", "aabaabaa", ".aaaaaa.", "..acca.."],
                 [".b..b..b", ".a.ba..a", "ba.aa.ba", "aa.aa.aa", "aabaabaa", ".aaaaaa.", "..acca.."],
                 ["b..b...b", "a.ba..a.", "aa.a.aab", "aa.aa.aa", "aabaabaa", ".aaaaaa.", "..acca.."]],
    "tubeworm": [["b.bb.b.", "aba.aba", "aba.aba", ".c.b.c.", ".c.a.c.", ".cacac.", "ccccccc"],
                 [".b.bb.b", "aba.aba", "aba.aba", ".c.b.c.", ".c.a.c.", ".cacac.", "ccccccc"],
                 ["bbb.bbb", ".a...a.", ".a.b.a.", ".c.a.c.", ".c.a.c.", ".cacac.", "ccccccc"]],
    "starfish": [["...a...", "...a...", "aaabaaa", ".aabaa.", ".aa.aa.", "aa...aa"]],
    "snail":   [["w.....w", ".w...w.", "..aaa..", ".abbba.", "abaaaba", "abacaba", "accccca", "kcccccc"],
                [".w...w.", "w.....w", "..aaa..", ".abbba.", "abaaaba", "abacaba", "accccca", "kcccccc"]],
    "barrel":  [[".ccccc.", "aaaaaaa", "abbbbba", "ccccccc", "aaaaaaa", "abbbbba", "aaaaaaa", ".ccccc."]],
    "cannon":  [["...aaaa.", "..abbba.", "caaaaaaa", "caacaaaa", "cc.aaa.a", "c..a.a.."]],
    "wheel":   [["..b.b.b..", "...aaa...", "b.aabaa.b", ".aabkbaa.", "b.aabaa.b", "...aaa...", "..b.b.b.."]],
    "lantern": [["..ccc..", ".caaac.", ".abwba.", ".abwba.", ".caaac.", "..ccc..", "...c..."],
                ["..ccc..", ".cbbbc.", ".bwwwb.", ".bwwwb.", ".cbbbc.", "..ccc..", "...c..."]],
    "fishbone": [["w.......", "ww.w.w.w", ".wwwwwww", "ww.w.w.w", "w......."]],
    "spine":   [["..ww..", ".wwww.", "..ww..", ".wwww.", "..ww..", ".wwww.", "..ww.."]],
    "skull":   [[".wwwww.", "wwwwwww", "wkkwkkw", "wkkwkkw", ".wwwww.", ".wkwkw.", ".wwwww."]],
    "statue":  [["..bbb..", ".baabc.", ".akaka.", ".baaac.", "..aac..", ".aaaac.", "aaaaaac", "abbbbbc", "aaaaaac"]],
    "lavarock": [["..aaa...", ".aabaa..", "aabaaaa.", "aaaaabaa", "acaaaacc", "cccccccc"],
                 ["..aaa...", ".aaaaa..", "aaaaaba.", "abaaaaaa", "acaaaacc", "cccccccc"]],
    "spikes":  [["..a....a.", "..a...aba", ".aba..aba", ".aba.aaba", "aabaaaaba", "aaaaaaaaa", "ccccccccc"]],
    "glowshroom": [["..bbb..", ".baaab.", "baawaab", "..aaa..", "...a...", "...a...", "..ccc.."],
                   ["..bbb..", ".bwwwb.", "bwwwwwb", "..aaa..", "...a...", "...a...", "..ccc.."]],
    "lure":    [["....b..", "...b...", "..b....", "..a....", "..a.aa.", "..aaaaa", "..acaca", ".ccccc."],
                ["...bb..", "...bb..", "..b....", "..a....", "..a.aa.", "..aaaaa", "..acaca", ".ccccc."]],
    "sponge":  [["a.b.a.b", "ab.ab.a", "aa.aa.a", "aaaaaaa", "abaaaba", "acaaaca", "ccccccc"]],
    "pen":     [["...b...", "..bab..", ".bbabb.", "bbbabbb", "...a...", "...a...", "...c...", "...c..."]],
    "hermit":  [[".w...w.", "..bbb..", ".baaab.", "baabaab", "bcaaaac", ".ca.a.a", "..a.a.a"],
                [".w...w.", "..bbb..", ".baaab.", "baabaab", "bcaaaac", ".c.a.a.", "..a.a.a"]],
    "geode":   [[".aaaaa.", "abbbbba", "abwwwba", "abwbwba", "abbbbba", "aaaaaaa"]],
    "coins":   [["..oo...", ".owwo.o", "owwwoow", "oowoooo", "mmmmmmm"]],
    "bubbleco": [["..bb.b..", ".baab.b.", "baaaabab", "baaaabaa", ".baab.aa", "..aa..a.", "..cc..c."]],
    "ripple":  [["..a.a.a..", ".aba.aba.", "aaaaaaaaa", "acaaaaaca", "ccccccccc"]],
    "stump":   [["bbbbbbb", "baaaaac", "baaaaac", ".aaaac.", "aaaaaac", "abbbbbc"]],
    "jar":     [["..bbb..", "...a...", "..aaa..", ".aaaaa.", "aabaaac", "aabaaac", "acaaacc", ".ccccc."]],
})
ANIMATED = {"seagrass": 3, "tubeworm": 3, "snail": 2, "lantern": 2, "lavarock": 2, "glowshroom": 2, "lure": 2,
            "hermit": 2, "anemone": 2}        # kind -> number of frames to cycle; crab and clam have their own moves

for _k, _fr in PROPS.items():
    for _f in _fr:
        _check_rows(_k, _f)
WIGGLERS = ("anemone", "crab", "clam")
PROP_SCALE = {"column": 1}            # everything else is drawn at double size: chunky early-console shapes

VENT_ROWS = ["...ggg...", "..aagaa..", ".aabaaca.", "aaabaaaac", "aaaaaaaaa"]
for _rows in (VENT_ROWS,):
    _check_rows("vent", _rows)


@lru_cache(maxsize=None)
def prop_img(kind, frame, pal):
    legend = dict(FIXED, a=pal[0], b=pal[1], c=pal[2])
    rows = PROPS[kind][frame % len(PROPS[kind])]
    img = np.full((len(rows), len(rows[0])), -1, dtype=np.int8)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != '.':
                img[y, x] = legend[ch]
    return img


@lru_cache(maxsize=None)
def vent_img(body, glow, frame):
    """A vent cone with a lava mouth that flickers between two glow colours."""
    legend = dict(a=body, b=glow, c=MAROON if body not in (MAROON, BLACK) else BLACK, g=glow if frame == 0 else RED)
    img = np.full((5, 9), -1, dtype=np.int8)
    for y, row in enumerate(VENT_ROWS):
        for x, ch in enumerate(row):
            if ch != '.':
                img[y, x] = legend[ch]
    return img


@lru_cache(maxsize=None)
def kelp_img(style, kh, frame, body, hi):
    """A swaying kelp strand, frames 0-3 lean 0, right, 0, left. Three styles: 0 ribbon (alternating blades),
    1 leafy (round leaves and a float at the tip), 2 frond (thin stem, short side fronds)."""
    n = kh + 3
    img = np.full((n, 10), -1, dtype=np.int8)
    lean = math.sin(frame * math.pi / 2)
    for k in range(n):                         # k counts up from the root
        c = 4 + int(round(2 * (k / n) * lean))
        row = n - 1 - k
        if style == 0:
            img[row, c], img[row, c + 1] = hi, body
            if k >= 2 and k % 4 == 2:
                img[row, c - 2:c] = body
                img[row, c - 2] = hi
            if k >= 2 and k % 4 == 0:
                img[row, c + 2:c + 4] = body
                img[row, c + 3] = hi
        elif style == 1:
            img[row, c] = body
            if k % 6 in (2, 3) and k >= 2:       # a round leaf, one side then the other
                side = -1 if (k // 6) % 2 else 1
                for j in (1, 2, 3):
                    cc = c + side * j
                    if 0 <= cc < 10:
                        img[row, cc] = hi if (j == 3 or k % 6 == 2) else body
            if k == n - 1:                       # the float at the tip
                img[row, c - 1:c + 2] = hi
                img[max(0, row - 1), c] = hi
        else:
            img[row, c] = hi if k % 2 else body
            if k % 3 == 1 and k >= 2:
                for j in (1, 2):
                    for cc in (c - j, c + j):
                        if 0 <= cc < 10 and (k // 3) % 2 == (j + (cc > c)) % 2:
                            img[row, cc] = body if j == 1 else hi
    return img


@lru_cache(maxsize=None)
def glint_img(colour, phase):
    """A twinkle that does nothing: nothing, a dot, a little plus, a dot."""
    img = np.full((3, 3), -1, dtype=np.int8)
    if phase in (1, 3):
        img[1, 1] = colour
    elif phase == 2:
        img[1, :] = colour
        img[:, 1] = colour
    return img


POP_STAR = np.array([[-1, YELLOW, -1], [YELLOW, WHITE, YELLOW], [-1, YELLOW, -1]], dtype=np.int8)   # what an eaten fish leaves for a moment
BUBBLE = np.array([[-1, WHITE, -1], [WHITE, -1, WHITE], [-1, WHITE, -1]], dtype=np.int8)
BUBBLE_S = np.array([[WHITE, SKY], [SKY, WHITE]], dtype=np.int8)

# ---------------------------------------------------------------------------
# Jellyfish: drifting, pulsing, smiling. w light, s main, p rim, k eyes. Four pictures: bell open/squeezed x tentacle wave.
# ---------------------------------------------------------------------------
_BELL = (["..wwwww..",
          ".wsssssw.",
          "wsskssksw",
          "wsssksssw",
          "ppppppppp"],
         ["...www...",
          "..wsssw..",
          ".wsksksw.",
          ".wsssssw.",
          ".ppppppp."])
for _r in _BELL:
    _check_rows("jelly", _r)
JELLY_W, JELLY_H = 9, 10
JELLY_PALS = ((SKY, WHITE, PURPLE), (WHITE, SKY, MAGENTA), (PINK, WHITE, ORANGE))      # (main, light, rim)


@lru_cache(maxsize=None)
def jelly_img(pal_i, bell, wave):
    """Bell (open or squeezed, with a smiling face) over five trailing strands that wiggle between two shapes."""
    main, light, rim = JELLY_PALS[pal_i]
    legend = dict(s=main, w=light, p=rim, k=BLACK)
    img = np.full((JELLY_H, JELLY_W), -1, dtype=np.int8)
    for y, row in enumerate(_BELL[bell]):
        for x, ch in enumerate(row):
            if ch != '.':
                img[y, x] = legend[ch]
    for si, c in enumerate((1, 2, 4, 6, 7)):
        length = 5 if si == 2 else (4 if si % 2 else 5)
        for r in range(length):
            xx = c + (1 if (r + wave + si) % 4 in (1, 2) else 0) - (1 if bell and si in (0, 4) else 0)
            if 0 <= xx < JELLY_W:
                img[5 + r, xx] = light if (r + si) % 2 else main
    return img


# ---------------------------------------------------------------------------
# Landmarks: big solid shaded shapes far behind the action (reef towers, spires, a wreck, a ribcage, ruins). Each is a
# mask lit from the upper left: a bright rim on the lit edges, a dark rim on the shaded ones, and speckle.
# ---------------------------------------------------------------------------
def _taper_fill(m, x0, x1, y0, y1):
    m[y0:y1, max(0, x0):max(0, x1)] = True


def lm_mask(kind, rnd, hh, sway=0.0):
    """Return (mask, details). details are (x, y, colour) with colour None meaning the shaded-edge colour."""
    det = []
    if kind == "mound":
        ww = rnd.randrange(hh + 6, int(1.4 * hh) + 12)
        m = np.zeros((hh, ww), dtype=bool)
        for dx in range(ww):
            n = int(round(hh * math.sqrt(max(0.0, 1 - ((dx + .5 - ww / 2) / (ww / 2)) ** 2))))
            if n:
                m[hh - n:, dx] = True
    elif kind == "boulder":                    # a floating lump of reef rock: an ellipse with a couple of bumps
        ww = rnd.randrange(14, 26)
        m = np.zeros((hh, ww), dtype=bool)
        ys_, xs_ = np.mgrid[0:hh, 0:ww]
        m[((xs_ + .5 - ww / 2) / (ww / 2)) ** 2 + ((ys_ + .5 - hh / 2) / (hh / 2)) ** 2 < 1] = True
        for _ in range(2):
            bx = rnd.randrange(2, ww - 5)
            m[max(0, hh // 5 - 2):hh // 5 + 1, bx:bx + 4] |= m[hh // 5 + 1:hh // 5 + 2, bx:bx + 4]
    elif kind == "spire":
        ww = max(9, hh // 2 + rnd.randrange(2, 8))
        m = np.zeros((hh, ww), dtype=bool)
        for dx in range(ww):
            n = int(hh * (1 - abs(dx + .5 - ww / 2) / (ww / 2))) + rnd.randrange(-1, 2)
            n = max(0, min(hh, n))
            if n:
                m[hh - n:, dx] = True
    elif kind == "tower":                      # a reef tower: tapering trunk with two or three arms that turn upward
        tw, arm = rnd.randrange(8, 12), rnd.randrange(8, 13)
        ww = tw + 2 * arm
        m = np.zeros((hh, ww), dtype=bool)
        for y in range(hh):
            wy = max(4, int(tw * (0.55 + 0.45 * y / hh)))
            m[y, ww // 2 - wy // 2: ww // 2 - wy // 2 + wy] = True
        for k in range(rnd.randrange(2, 4)):
            by, side = rnd.randrange(hh // 5, hh * 3 // 4), (-1, 1)[k % 2]
            edge = ww // 2 + side * (tw // 2)
            tip = edge + side * arm
            a, b = sorted((edge, tip))
            m[by:by + 3, a:b] = True
            tx = tip - (2 if side > 0 else 0)
            m[max(0, by - rnd.randrange(6, 13)):by + 3, max(0, tx):tx + 3] = True
    elif kind == "strand":                     # giant kelp: a wavy stem with blades
        ww = 14
        m = np.zeros((hh, ww), dtype=bool)
        ph = rnd.random() * 6 + sway
        for y in range(hh):
            sx = 5 + int(round(2 * math.sin(y / 5.0 + ph)))
            m[y, sx:sx + 3] = True
            if y % 7 == 3:
                m[y:y + 2, max(0, sx - 4):sx] = True
            if y % 7 == 6:
                m[y:y + 2, sx + 3:min(ww, sx + 7)] = True
    elif kind == "hull":                       # a sunken ship: raked hull, two masts with a yard, portholes, planks
        ww, hhh = rnd.randrange(38, 50), max(18, min(hh, 28))
        hh = hhh
        m = np.zeros((hh, ww), dtype=bool)
        y0 = hh * 5 // 12
        for y in range(y0, hh):
            inset = (y - y0) * (ww // 6) // max(1, hh - y0)
            m[y, inset:ww - inset // 2] = True
        for dx in range(ww * 3 // 4, ww):      # the bow slopes away
            m[y0:y0 + (dx - ww * 3 // 4) // 2, dx] = False
        for mx in (ww // 4, ww // 2):
            m[0:y0, mx:mx + 2] = True
            m[3:5, mx - 4:mx + 6] = True
        for px in range(6, ww - 12, 6):
            det.append((px, y0 + 3, SKY))
            det.append((px + 1, y0 + 3, SKY))
    elif kind == "ribs":                       # a giant ribcage lying on the bed
        ww, hh = rnd.randrange(30, 42), max(14, min(hh, 24))
        m = np.zeros((hh, ww), dtype=bool)
        m[hh - 2:, :] = True
        for x0 in range(2, ww - 6, 7):
            for t in range(hh - 1):
                xx = x0 + int(round(4 * math.sin(math.pi * t / (hh - 1))))
                m[hh - 1 - t, xx:xx + 3] = True
    elif kind == "tusk":                       # a curved tusk standing out of the sand
        ww = hh // 2 + 8
        m = np.zeros((hh, ww), dtype=bool)
        for t in range(hh):
            x0 = int((t / hh) ** 2 * (ww - 8))
            m[hh - 1 - t, x0:x0 + max(1, 7 - t * 6 // hh)] = True
    elif kind == "arch":                       # two fluted pillars and a lintel, sometimes chipped
        ww = rnd.randrange(20, 30)
        m = np.zeros((hh, ww), dtype=bool)
        m[:, 0:5] = True
        m[:, ww - 5:ww] = True
        m[0:4, :] = True
        m[hh - 3:, 0:7] = True
        m[hh - 3:, ww - 7:ww] = True
        for y in range(6, hh - 3, 4):          # round C: a few flutes, not a stripe on every other row
            det.append((2, y, None))
            det.append((ww - 3, y, None))
        if rnd.random() < .5:
            m[0:rnd.randrange(4, hh // 2 + 4), 0:5] = False
            m[0:4, 0:ww // 3] = False
    elif kind == "column":                     # one fluted pillar with a capital and a base
        ww = 9
        m = np.zeros((hh, ww), dtype=bool)
        m[:, 1:8] = True
        m[0:3, :] = True
        m[hh - 3:, :] = True
        for y in range(5, hh - 3, 4):
            det.append((4, y, None))
        if rnd.random() < .6:                  # a broken top
            cut = rnd.randrange(3, max(4, hh // 3))
            for dx in range(ww):
                m[0:cut + (dx * 3) % 4, dx] = False
    elif kind == "isle":                       # a floating island: flat bumpy top with tufts, a tapering underside
        ww = rnd.randrange(20, 34)
        hh = max(8, min(hh, 14))
        m = np.zeros((hh, ww), dtype=bool)
        for dx in range(ww):
            t = abs(dx + .5 - ww / 2) / (ww / 2)
            depth = max(2, int((hh - 1) * (1 - t ** 1.6)) + 1)
            m[0:depth, dx] = True
            if dx % 5 == 2:
                det.append((dx, 0, GREEN))
            if dx % 7 == 3 and depth > 4:
                det.append((dx, depth - 2, None))
    elif kind == "cluster":                    # a cluster of crystal spikes leaning together
        ww = rnd.randrange(14, 22)
        hh = max(10, min(hh, 20))
        m = np.zeros((hh, ww), dtype=bool)
        for cx, hgt in ((ww // 2, hh), (ww // 4, hh * 2 // 3), (ww * 3 // 4, hh * 3 // 5), (ww // 8 + 1, hh // 3)):
            for y in range(hgt):
                half = y * 3 // hgt
                m[hh - hgt + y, max(0, cx - half):cx + half + 1] = True
    elif kind == "dome":                       # a rounded coral head with brain-like grooves
        ww = rnd.randrange(hh + 4, int(1.5 * hh) + 8)
        m = np.zeros((hh, ww), dtype=bool)
        for dx in range(ww):
            n = int(round(hh * math.sqrt(max(0.0, 1 - ((dx + .5 - ww / 2) / (ww / 2)) ** 2))))
            if n:
                m[hh - n:, dx] = True
    elif kind == "orb":                        # a glowing bubble-rock the size of a house
        ww = hh = rnd.randrange(9, 14)
        m = np.zeros((hh, ww), dtype=bool)
        ys_, xs_ = np.mgrid[0:hh, 0:ww]
        m[((xs_ + .5 - ww / 2) / (ww / 2)) ** 2 + ((ys_ + .5 - hh / 2) / (hh / 2)) ** 2 < 1] = True
        det.extend([(ww // 3, hh // 3, WHITE), (ww // 3 + 1, hh // 3, WHITE), (ww // 3, hh // 3 + 1, WHITE)])
    elif kind == "wreckage":                   # a broken plank raft with a stub of mast
        ww = rnd.randrange(22, 34)
        hh = max(10, min(hh, 16))
        m = np.zeros((hh, ww), dtype=bool)
        for dx in range(ww):
            top = hh - 4 - dx // 6
            m[max(0, top):max(0, top) + 4, dx] = True
        m[0:hh - 4, ww // 3:ww // 3 + 2] = True
        m[2:4, ww // 3 - 3:ww // 3 + 5] = True
        for dx in range(2, ww, 5):
            det.append((dx, hh - 3 - dx // 6, None))
    else:
        raise ValueError(kind)
    return m, det


def shade(mask, det, fill, rim, dark, tex):
    """Lit from the upper left: bright rim on top and left edges, dark rim on bottom and right edges, speckle between."""
    hh, ww = mask.shape
    img = np.full((hh, ww), -1, dtype=np.int8)
    pad = np.pad(mask, 1)
    for y in range(hh):
        for x in range(ww):
            if not mask[y, x]:
                continue
            if not pad[y, x + 1] or not pad[y + 1, x]:        # nothing above or to the left
                c = rim
            elif not pad[y + 1, x + 2] or not pad[y + 2, x + 1]:   # nothing right or below
                c = dark
            elif (x * 5 + y * 3) % 61 == 0:
                c = tex
            else:
                c = fill
            img[y, x] = c
    for x, y, c in det:
        if 0 <= y < hh and 0 <= x < ww and mask[y, x]:
            img[y, x] = dark if c is None else c
    return img


@lru_cache(maxsize=None)
def landmark_img(theme_i, kind, hh, seed, hang, sway=0, floater=None):
    """(picture, lights). lights are (x, y, w) spots inside the picture where a little inert light blinks: wreck portholes,
    the tips of towers, spires and crystal clusters. sway 0-2 is the frame of a giant kelp strand's slow lean."""
    th = THEMES[theme_i]
    rnd = random.Random(seed)
    if kind == "stal":                         # a stalactite is a spire (or a tower) turned upside down
        mask, det = lm_mask("spire", rnd, hh)
        mask, det = mask[::-1], []
    else:
        mask, det = lm_mask(kind, rnd, hh, sway * 0.9)
    fill, rim, dark, tex = th["lm"] if floater is None else floater
    img = shade(mask, det, fill, rim, dark, tex)
    lights = []
    if kind == "hull":
        lights = [(x, y, 2) for x, y, c in det if c == SKY and x % 2 == 0 and mask[y, x]]
    elif kind in ("tower", "spire") or (floater is not None and kind in ("cluster", "orb")):
        top = int(np.argmax(mask.any(axis=1)))
        xs = np.nonzero(mask[top])[0]
        if len(xs):
            lights = [(int(xs[len(xs) // 2]) - 1, top - 2, 3)]
    return img, tuple(lights)


# One look per level. tint = the colour the deep water fades into; deep = how far down (0-1) the fade starts; bed = (sand
# top, sand body, sand speckle, deep layer); kelp = (body, highlight) or None (then the kelp spots grow `tall` props
# instead); kstyle = kelp style; props = what grows on the bed; gap = the empty run between two props; pals = prop colour
# sets (main, light, dark); far = the landmarks standing on the bed; lmgap = the run between two of them; hang = those
# hanging from the surface; lm = landmark colours (fill, bright rim, dark rim, speckle); fl = what floats in the middle
# water of the tall seas, each as (kind, colours); vent = (cone, glow); glint = twinkle colours; jelly = which jellyfish
# colours drift here; ridge = the colour of the far hills; shafts = sunlight columns; motes = (kind, (colour a, colour b))
# of the one small thing that drifts about here; crit = seahorse colours; small = scatter tiny starfish and grass tufts.
THEMES = [
    dict(tint=SKY, deep=.72, bed=(WHITE, ORANGE, RED, MAROON), kelp=(GREEN, WHITE), kstyle=1, tall=("fan",),
         props=("fan", "brain", "seagrass", "star", "anemone", "clam", "coral"),
         gap=(12, 28), pals=((MAGENTA, PINK, PURPLE), (GREEN, WHITE, BLACK), (YELLOW, ORANGE, MAROON)),
         far=("tower", "spire", "tower", "dome"), lmgap=(26, 60), hang=(), lm=(RED, ORANGE, MAROON, MAGENTA), fl=(),
         vent=(RED, YELLOW), glint=(WHITE, ORANGE), jelly=(0, 1, 2), ridge=MAROON, shafts=True,
         motes=("sparkle", (WHITE, PINK)), crit=((ORANGE, PINK), (PINK, WHITE)), small=False),
    dict(tint=GREEN, deep=.7, bed=(GREEN, MAROON, BLACK, BLACK), kelp=(GREEN, ORANGE), kstyle=0, tall=("tube",),
         props=("seagrass", "rock", "shell", "anemone", "snail", "clam", "tubeworm"),
         gap=(5, 14), pals=((MAROON, RED, BLACK), (PURPLE, MAGENTA, BLACK), (GREEN, WHITE, BLACK), (ORANGE, PINK, MAROON)),
         far=("strand", "strand", "strand"), lmgap=(8, 36), hang=(), lm=(BLACK, GREEN, PURPLE, GREEN), fl=(),
         vent=(MAROON, ORANGE), glint=(GREEN, ORANGE), jelly=(1, 2), ridge=GREEN, shafts=True,
         motes=("plankton", (GREEN, WHITE)), crit=((GREEN, WHITE), (ORANGE, PINK)), small=True),
    dict(tint=MAROON, deep=.45, bed=(MAROON, BLACK, ORANGE, BLACK), kelp=None, kstyle=0, tall=("spikes", "tube", "rock"),
         props=("lavarock", "rock", "spikes", "crab", "crystal", "urchin", "hermit", "lavarock", "tube"),
         gap=(5, 14), pals=((PURPLE, MAROON, BLACK), (ORANGE, RED, MAROON), (RED, ORANGE, MAROON)),
         far=("spire", "spire", "mound"), lmgap=(8, 36), hang=("stal", "stal"), lm=(BLACK, MAROON, PURPLE, MAROON),
         fl=(("dome", (RED, ORANGE, MAROON, ORANGE)), ("cluster", (MAROON, ORANGE, BLACK, RED))),
         vent=(BLACK, ORANGE), glint=(ORANGE, RED), jelly=(0,), ridge=MAROON, shafts=False,
         motes=("ember", (ORANGE, RED)), crit=(), small=True),
    dict(tint=MAGENTA, deep=.55, bed=(PINK, PURPLE, MAGENTA, PURPLE), kelp=None, kstyle=2, tall=("fan", "pen", "brain"),
         props=("fan", "brain", "pen", "anemone", "coral", "clam", "shroom"),
         gap=(14, 30), pals=((MAGENTA, PINK, PURPLE), (ORANGE, PINK, MAROON), (GREEN, WHITE, BLACK)),
         far=("tower", "tower", "spire"), lmgap=(26, 64), hang=("stal",), lm=(PURPLE, PINK, BLACK, MAGENTA),
         fl=(("cluster", (MAGENTA, WHITE, PURPLE, PINK)), ("isle", (PURPLE, PINK, BLACK, MAGENTA))),
         vent=(PURPLE, PINK), glint=(PINK, WHITE), jelly=(1, 0, 2), ridge=PURPLE, shafts=False,
         motes=("spore", (PINK, WHITE)), crit=((PINK, WHITE), (ORANGE, PINK)), small=False),
    dict(tint=PURPLE, deep=.7, bed=(ORANGE, MAROON, BLACK, BLACK), kelp=(MAROON, ORANGE), kstyle=2, tall=("anchor", "amph"),
         props=("anchor", "amph", "barrel", "cannon", "crab", "chest", "lantern"),
         gap=(6, 16), pals=((MAROON, ORANGE, BLACK), (PURPLE, MAGENTA, BLACK), (ORANGE, PINK, MAROON)),
         far=("hull", "spire", "hull", "mound"), lmgap=(8, 36), hang=(), lm=(BLACK, MAROON, PURPLE, MAROON), fl=(),
         vent=(MAROON, ORANGE), glint=(ORANGE, PINK), jelly=(0, 2), ridge=PURPLE, shafts=False,
         motes=("plankton", (ORANGE, WHITE)), crit=((ORANGE, WHITE),), small=True),
    dict(tint=PURPLE, deep=.3, bed=(PURPLE, BLACK, MAGENTA, BLACK), kelp=None, kstyle=0, tall=("lure", "tube", "glowshroom"),
         props=("lure", "glowshroom", "tubeworm", "crab", "star", "crystal", "shroom", "sponge", "glowshroom"),
         gap=(5, 14), pals=((MAGENTA, PINK, PURPLE), (ORANGE, PINK, MAROON), (GREEN, WHITE, BLACK), (RED, ORANGE, MAROON)),
         far=("spire", "tower", "spire"), lmgap=(8, 36), hang=("stal", "stal"), lm=(BLACK, PURPLE, PURPLE, MAGENTA),
         fl=(("orb", (PURPLE, WHITE, BLACK, SKY)), ("cluster", (PURPLE, PINK, BLACK, MAGENTA))),
         vent=(PURPLE, MAGENTA), glint=(PINK, ORANGE, MAGENTA), jelly=(1, 0, 2), ridge=PURPLE, shafts=False,
         motes=("lantern", (WHITE, PURPLE)), crit=(), small=True),
    dict(tint=PURPLE, deep=.5, bed=(WHITE, PURPLE, BLACK, BLACK), kelp=None, kstyle=0, tall=("bone", "rock", "spine"),
         props=("bone", "fishbone", "spine", "skull", "rock", "star", "shell", "crab", "urchin", "bone"),
         gap=(5, 14), pals=((PURPLE, MAGENTA, BLACK), (MAROON, RED, BLACK), (ORANGE, PINK, MAROON)),
         far=("ribs", "tusk", "ribs", "mound"), lmgap=(8, 36), hang=("stal",), lm=(BLACK, WHITE, PURPLE, PINK),
         fl=(("cluster", (PINK, WHITE, PURPLE, WHITE)), ("tusk", (PINK, WHITE, PURPLE, WHITE))),
         vent=(BLACK, RED), glint=(WHITE, PINK), jelly=(1, 2), ridge=PURPLE, shafts=False,
         motes=("ash", (WHITE, PINK)), crit=(), small=True),
    dict(tint=PURPLE, deep=.55, bed=(GREEN, ORANGE, MAROON, MAROON), kelp=(GREEN, PINK), kstyle=1, tall=("column",),
         props=("column", "statue", "amph", "anemone", "crab", "chest", "seagrass"),
         gap=(7, 18), pals=((ORANGE, PINK, MAROON), (PINK, WHITE, MAGENTA), (GREEN, WHITE, BLACK)),
         far=("arch", "column", "arch", "column", "mound"), lmgap=(10, 40), hang=("stal",), lm=(MAROON, ORANGE, BLACK, PURPLE),
         fl=(("isle", (ORANGE, WHITE, MAROON, PINK)), ("wreckage", (MAROON, ORANGE, BLACK, PURPLE))),
         vent=(MAROON, ORANGE), glint=(GREEN, WHITE), jelly=(0, 1, 2), ridge=MAROON, shafts=True,
         motes=("petal", (PINK, GREEN)), crit=((ORANGE, PINK), (GREEN, WHITE)), small=True),
]


@lru_cache(maxsize=None)
def sea_img(i, w, h):
    """The whole level's water: plain sea, a lighter band under the surface and a depth tint that dithers in from a depth
    of its own (high up in the abyss, only near the floor in the lagoon): an ordered dither that thickens with depth, and a
    solid strip on the floor itself."""
    th = THEMES[i]
    full_h = h + HUD_H
    img = np.full((full_h, w), SEA, dtype=np.int8)
    ys, xs = np.mgrid[0:full_h, 0:w]
    level = (ys / full_h - th["deep"]) / (1 - th["deep"])          # 0 where the fade starts, 1 at the floor
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0       # ordered dither: a smooth fade, no stripes
    # Calm pass: no more dither across the deep water. One quiet seam of thin dots just above the floor strip, then flat colour.
    img[(level > .8) & (bayer[ys % 4, xs % 4] < .25) & ((full_h - ys) <= 10)] = th["tint"]
    img[(full_h - ys) <= 6] = th["tint"]
    return img


@lru_cache(maxsize=None)
def ridge_img(i, w, h):
    """Far hills behind everything: a rolling silhouette in the level's ridge colour with a lighter dithered crest."""
    th = THEMES[i]
    rh = 34 if h >= 100 else 11
    img = np.full((rh, w), -1, dtype=np.int8)
    for x in range(w):
        top = rh - int(rh * (.45 + .25 * math.sin(x / 17.0 + i) + .2 * math.sin(x / 7.0 + 2 * i) + .1 * math.sin(x / 41.0)))
        top = max(1, min(rh - 1, top))
        img[top:, x] = th["ridge"]
    return img


@lru_cache(maxsize=64)
def shaft_img(hh, phase):
    """A column of sunlight slanting down to the right: sparse sky-coloured streaks that creep along, bright edges."""
    ww = 11
    img = np.full((hh, ww), -1, dtype=np.int8)
    for y in range(hh):
        for x in range(ww):
            if x in (0, ww - 1) and (y + phase) % 4 < 2:
                img[y, x] = SKY
    return _shift_rows(img)


def _shift_rows(img):
    """Lean the shaft: every third row moves one pixel right (and the picture is padded to keep its width)."""
    hh, ww = img.shape
    out = np.full((hh, ww + hh // 3 + 1), -1, dtype=np.int8)
    for y in range(hh):
        out[y, y // 3:y // 3 + ww] = img[y]
    return out


# ---------------------------------------------------------------------------
# Quiet life that does nothing: seahorses bobbing, and one kind of small drifting thing per level.
# ---------------------------------------------------------------------------
_SEAHORSE = (["...bbb..", "..abaaa.", "..akaaaa", "...aaa..", "..abab.w", "..aaaa..", "..abab..", "..aaa...", ".aaa....",
              ".aab....", ".aa.a..."],
             ["...bbb..", "..abaaa.", "..akaaaa", "...aaa..", "..abab..", "..aaaa.w", "..abab..", "..aaa...", ".aaa....",
              ".aab....", ".aa..a.."])
for _r in _SEAHORSE:
    _check_rows("seahorse", _r)
SEAHORSE_W, SEAHORSE_H = 8, 11


@lru_cache(maxsize=None)
def seahorse_img(pal, frame):
    legend = dict(a=pal[0], b=pal[1], k=BLACK, w=WHITE)
    img = np.full((SEAHORSE_H, SEAHORSE_W), -1, dtype=np.int8)
    for y, row in enumerate(_SEAHORSE[frame]):
        for x, ch in enumerate(row):
            if ch != '.':
                img[y, x] = legend[ch]
    return img


@lru_cache(maxsize=None)
def mote_img(kind, cols, phase):
    """The drifting things, each in four phases: embers flicker, spores pulse, ash and petals turn, plankton glimmers,
    lantern orbs breathe, sparkles twinkle."""
    a, b = cols
    if kind == "ember":
        return np.array([[a, -1], [b if phase % 2 else a, a]], dtype=np.int8) if phase != 3 else np.array([[b, -1], [a, b]], dtype=np.int8)
    if kind == "spore":
        img = np.full((3, 3), -1, dtype=np.int8)
        img[1, 1] = b if phase % 2 else a
        if phase in (1, 2):
            img[0, 1] = img[2, 1] = img[1, 0] = img[1, 2] = a
        return img
    if kind == "ash":
        return np.array([[a, b]], dtype=np.int8) if phase % 2 else np.array([[b], [a]], dtype=np.int8)
    if kind == "petal":
        return (np.array([[a, b], [-1, a]], dtype=np.int8) if phase % 2 else np.array([[b, -1], [a, b]], dtype=np.int8))
    if kind == "plankton":
        return np.array([[a if phase % 2 else b]], dtype=np.int8) if phase != 2 else np.array([[a, b]], dtype=np.int8)
    if kind == "lantern":                          # a soft orb: white heart, coloured ring, breathing in and out
        img = np.full((5, 5), -1, dtype=np.int8)
        ring = b if phase in (0, 1) else SKY
        for x, y in ((1, 0), (2, 0), (3, 0), (0, 1), (4, 1), (0, 2), (4, 2), (0, 3), (4, 3), (1, 4), (2, 4), (3, 4)):
            img[y, x] = ring
        img[1:4, 1:4] = ring if phase == 2 else b
        img[2, 2] = a
        if phase in (1, 2):
            img[1, 2] = img[2, 1] = img[2, 3] = img[3, 2] = a
        return img
    return glint_img(a if phase < 2 else b, (1, 2, 1, 0)[phase])             # sparkle


def _mote_pos(kind, x0, y0, k, n, w, h):
    """Where a drifting thing is at step n: a pure function of the step count, wrapped round the world."""
    if kind == "ember":
        return x0 + int(round(2 * math.sin(n / 9.0 + k))), (y0 - n // 2 - k * 3) % h
    if kind == "spore":
        return x0 + int(7 * math.sin(n / 23.0 + k * 1.3)), y0 + int(5 * math.sin(n / 17.0 + k * 2.1))
    if kind == "ash":
        return x0 + int(3 * math.sin(n / 15.0 + k)), (y0 + n // 3 + k) % h
    if kind == "petal":
        return (x0 + n // 4 + int(2 * math.sin(n / 7.0 + k))) % w, (y0 + n // 3) % h
    if kind == "plankton":
        return x0 + int(9 * math.sin(n / 31.0 + k)), y0 + int(4 * math.cos(n / 27.0 + k * 1.7))
    if kind == "lantern":
        return x0 + int(4 * math.sin(n / 37.0 + k)), y0 + int(6 * math.sin(n / 29.0 + k * 2))
    return x0, y0                                   # sparkle: stays put, only blinks


@lru_cache(maxsize=None)
def port_img(colour):
    """A lit porthole: two pixels."""
    return np.full((1, 2), colour, dtype=np.int8)


@lru_cache(maxsize=None)
def bed_img(bed, i):
    """The sea bed's front edge: a bright top with pebbles, speckled sand, a darker deep layer, in the level's colours."""
    top, body, spot, deep = THEMES[i]["bed"]
    bh = 8
    img = np.full((bh, len(bed)), -1, dtype=np.int8)
    for x, height in enumerate(bed):
        for d in range(height):
            if d == 0:
                c = top
            elif d == 1 and x % 13 in (3, 4):          # a pebble sitting on the sand
                c = top
            elif d >= height - 2 and height > 3:
                c = deep if (x + d) % 3 else body
            else:
                c = spot if (x * 7 + d * 13) % 29 == 0 else body
            img[bh - height + d, x] = c
    return img


@lru_cache(maxsize=None)
def surface_img(w, phase):
    """The water line along the top of the world: sky water, white crests and a ripple that drift."""
    img = np.full((2, w), SKY, dtype=np.int8)
    xs = np.arange(w)
    img[0, ((xs + phase) % 7) < 3] = WHITE
    img[1, ((xs - phase) % 6) < 2] = SEA
    return img


@lru_cache(maxsize=4096)
def zone_img(zw, zh, now, nxt, ox, oy):
    """One current: a bright rim, light streaks that run with the flow, and white chevrons pointing the way it runs now. Each chevron's yellow pixel sits
    two cells from its centre on the side the water runs next (ff01's rule, unchanged): a yellow tip means "same
    again", a yellow dot behind it "turning back", a yellow arm end "turning that way". (The blue ripples of the first
    pass are gone: they only muddied the yellow dots.)"""
    img = np.full((zh, zw), -1, dtype=np.int8)
    dx, dy = DV[now]
    # Third pass: the water of a current is a bright rim and long streaks that run WITH the flow and creep along it; between
    # the streaks the sea behind (landmarks, jellyfish, bed) shows through. The chevrons and yellow marks are unchanged.
    ys_, xs_ = np.mgrid[0:zh, 0:zw]
    along, across = (xs_ * dx + ys_ * dy), (ys_ * abs(dx) + xs_ * abs(dy))
    drift = ox * dx + oy * dy
    px, py = -dy, dx
    nx, ny = DV[nxt]
    L, W = (zw, zh) if dx else (zh, zw)                    # L runs along the flow, W across it
    n_a, n_w = max(1, int(round(L / 16.0))), max(1, W // 14)
    rows = [int((k + .5) * W / n_w) for k in range(n_w)]   # chevron rows, spread evenly across the lane
    # Round C: calmer lane. The long streaks keep clear of the chevron rows, and the chevrons are spaced evenly (about every
    # sixteen along, one row per fourteen across, none of the old every-eight lattice), so the flow reads at a glance.
    near = np.min(np.abs(across[..., None] - np.array(rows)), axis=-1)
    img[(across % 8 == 4) & (((along - drift) % 12) < 7) & (near > 3)] = CURRENT_WATER
    img[0, :] = img[-1, :] = img[:, 0] = img[:, -1] = CURRENT_WATER
    for r, row in enumerate(rows):
        for k in range(n_a):
            lo = int((k + (.5 if r % 2 else 0)) * L / n_a) + 4
            a_pos = (lo + (ox if dx else oy)) % L          # the drift counts up in the flow direction
            mx, my = (a_pos, row) if dx else (row, a_pos)
            pts = [(mx + 2 * dx, my + 2 * dy), (mx + dx + px, my + dy + py), (mx + dx - px, my + dy - py),
                   (mx + 2 * px, my + 2 * py), (mx - 2 * px, my - 2 * py)]
            tell = (mx + 2 * nx, my + 2 * ny)
            for x, y in pts:
                if 0 <= x < zw and 0 <= y < zh and (x, y) != tell:
                    img[y, x] = FLOW_MARK
            if 0 <= tell[0] < zw and 0 <= tell[1] < zh:
                img[tell[1], tell[0]] = NEXT_MARK
    for x, y in ((0, 0), (zw - 1, 0), (0, zh - 1), (zw - 1, zh - 1)):   # corners cut, as before
        img[y, x] = -1
    return img


@lru_cache(maxsize=512)
def hud_img(lives, eat, eaten, left, bar):
    """The four HUD rows: lives (little fish, a dark silhouette for each one lost), one pearl per meal needed (shiny once
    eaten), the tide's yellow pips, and the time bar (row 3, shrinking from the right; it warms to orange then red as
    it runs out; bar < 0 means this level has none)."""
    img = np.full((HUD_H, SCREEN), HUD_BG, dtype=np.int8)
    img[0, :] = BLACK                                     # round C: plain rules, no magenta dots
    img[3, :] = BLACK
    for n in range(3):
        for ix, iy, c in LIFE_ICON:
            img[1 + iy, 1 + n * LIFE_W + ix] = c if n < lives else (BLACK if c != WHITE else RED)
    big = eat <= 9                                        # fat 2x2 pearls while they fit, thin ones for the long levels
    step, x0 = (3, 19) if big else (2, 19)
    for n in range(eat):
        x = x0 + n * step
        if n < eaten:
            if big:
                img[1:3, x:x + 2] = ((WHITE, SKY), (SKY, PINK))
            else:
                img[1:3, x] = WHITE
        elif big:
            img[1:3, x:x + 2] = SEA
        else:
            img[1:3, x] = SEA
    for n in range(left):
        img[1:3, 62 - n * 2] = NEXT_MARK
    if bar >= 0:
        frac = bar / SCREEN
        img[3, :bar] = WHITE if frac > .5 else (ORANGE if frac > .22 else RED)
    return img


@lru_cache(maxsize=256)
def wash_img(stage, ox, oy):
    """The tint of a lost run (round C, no checker): a solid maroon frame thickens in from the edges with a thin red rim, and from
    stage three a round spotlight closes on the fish, so the fish stays the one clear thing on a calm dark field."""
    img = np.full((VIEW_H, VIEW_W), -1, dtype=np.int8)
    ys, xs = np.mgrid[0:VIEW_H, 0:VIEW_W]
    edge = np.minimum(np.minimum(xs, VIEW_W - 1 - xs), np.minimum(ys, VIEW_H - 1 - ys))
    img[edge < stage * 2] = MAROON
    img[edge < min(2, stage)] = RED
    if stage >= 3:
        r = (30, 24, 17)[min(stage, 5) - 3]
        img[((xs - ox) ** 2 + (ys - oy) ** 2 > r * r) & (img < 0)] = MAROON
    return img


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------
class Ff02(ARCBaseGame):
    # art-only animation state (defaults; set per action in step())
    pending_open = False
    open_t = 1
    tw_left = 0
    tw_t = 0
    tw_frac = 1.0
    pre = None
    clk = 0
    shut = False
    bump = None
    bit = False
    grew = False
    vpos = (0, 0)
    pops = {}

    def __init__(self):
        super().__init__(game_id='ff02', levels=levels, camera=Camera(0, 0, SCREEN, SCREEN, SEA, SEA, []),
                         win_score=len(levels), available_actions=[1, 2, 3, 4])

    # -- level setup --------------------------------------------------------
    def on_set_level(self, level):
        self._load_level(self.level_index)
        self._build_scene(level)
        self._sync()

    def _load_level(self, i):
        d = LEVEL_DATA[i]
        self.w, self.h = d["w"], d["h"]
        self.px, self.py = d["player"]
        self.size = d["size"]
        self.grow = list(d["grow"])
        self.eat = d["eat"]
        self.lives = d["lives"]
        self.period = d["period"]
        self.budget = d["budget"]
        self.moves_left = d["budget"]
        self.zones = [tuple(z[:5]) + (tuple(z[5]),) for z in d["zones"]]
        self.zone_drift = [[0, 0] for _ in self.zones]
        # fish: [x, y, size, alive, facing_right, headings]
        self.fish = [[f[0], f[1], f[2], True, f[3][0] != LEFT, tuple(f[3])] for f in d["fish"]]
        self.facing = True
        self.eaten = 0
        self.grace = 0
        self.step_count = 0
        self.bursts = []
        self.pops = {}                               # art only: fish just eaten -> the picture number they were eaten on
        self.clk, self.tw_left, self.tw_t, self.tw_frac, self.pre = 0, 0, 0, 1.0, None
        self.shut, self.bump, self.bit, self.grew = False, None, False, False
        self.open_t = 0 if self.pending_open else len(IRIS_OPEN)       # an iris opens only after a level clear
        self.winning = 0
        self.dying = 0
        self.finale = False
        # scenery from a fixed formula of the level number, so it is identical every time
        self.bed = [3 + int(1.5 + 1.5 * math.sin(x / 9.0 + i) + math.sin(x / 23.0 + 2 * i))
                    for x in range(self.w)]
        self.kelp = [(x, 6 + (x * 7 + i * 3) % 7) for x in range(9 + i * 5 % 13, self.w - 2, 23 + i % 3 * 4)]
        self.vents = [x for x in range(30 + i * 7 % 20, self.w - 6, 64)]

    # -- the scene: every thing on screen is a named sprite --------------------------------------------------
    def _build_scene(self, level):
        level.remove_all_sprites()
        i, th = self.level_index, THEMES[self.level_index]
        rnd = random.Random(4000 + i)
        full_h = self.h + HUD_H
        tall = self.h >= 100

        def add(name, pix, x, y, layer, tags, scale=1):
            sp = Sprite(pix, name=name, x=x, y=y, layer=layer, tags=list(tags), scale=scale,
                        blocking=BlockingMode.NOT_BLOCKED, collidable=False)
            level.add_sprite(sp)
            return sp

        add("sea", sea_img(i, self.w, self.h), 0, 0, L_SEA, ["backdrop"])
        ridge = ridge_img(i, self.w, self.h)
        add("far_hills", ridge, 0, full_h - ridge.shape[0] - 2, L_SEA, ["backdrop"])

        # sunlight columns where the level has sun: they slant down through the water and shimmer
        self.shafts = []
        if th["shafts"]:
            srnd = random.Random(7000 + i)
            sh_h = min(self.h * 6 // 10, 64)
            x = srnd.randrange(6, 30)
            while x < self.w - 20:
                sp = add(f"sunlight_{len(self.shafts)}", shaft_img(sh_h, 0), x, HUD_H + 2, L_SURFACE, ["light"])
                self.shafts.append((sp, x, sh_h, len(self.shafts)))
                x += srnd.randrange(46, 78)

        # landmarks: big shaded shapes standing on the bed (and hanging from the surface), in the middle water too
        lo, hi = (int(self.h * .3), int(self.h * .6)) if tall else (14, 34)
        lrnd = random.Random(5000 + i)
        self.beacons, self.strands = [], []
        lm_n = [0]

        def landmark(name, kind, hh, seed, x, y_of, floater=None, layer=L_FAR):
            img, lights = landmark_img(i, kind, hh, seed, False, 0, floater)
            sp = add(f"{name}_{lm_n[0]}", img, x, y_of(img), layer, ["landmark", kind])
            if kind == "strand":                  # giant kelp leans slowly one way and the other
                self.strands.append((sp, kind, hh, seed, x, lm_n[0]))
            for lx, ly, lw in lights:
                col = th["glint"]
                bsp = add(f"beacon_{lm_n[0]}_{lx}", glint_img(col[0], 1) if lw == 3 else port_img(ORANGE), x + lx, sp.y + ly,
                          L_MID, ["beacon"])
                self.beacons.append((bsp, x + lx, sp.y + ly, lw, col, len(self.beacons)))
            lm_n[0] += 1
            return img

        x = lrnd.randrange(0, 14)
        while x < self.w - 10:
            kind = lrnd.choice(th["far"])
            img = landmark("landmark", kind, lrnd.randrange(lo, hi + 1), lrnd.randrange(10 ** 6), x,
                           lambda im: full_h - 3 - im.shape[0])
            x += img.shape[1] + lrnd.randrange(*th["lmgap"])
        x = lrnd.randrange(10, 40)
        while th["hang"] and x < self.w - 10:
            img, _ = landmark_img(i, "stal", lrnd.randrange(10, max(12, int(self.h * (.5 if tall else .22)))), lrnd.randrange(10 ** 6), True)
            add(f"hanging_{lm_n[0]}", img, x, HUD_H + 2, L_FAR, ["landmark", "stal"])
            x += img.shape[1] + lrnd.randrange(30, 80)
            lm_n[0] += 1

        if tall and th["fl"]:                  # floating things so the middle of a deep sea is never bare: bright, and each level's own
            for k in range(self.w * self.h // 1600):
                kind, cols = th["fl"][k % len(th["fl"])]
                for _try in range(8):          # keep floaters out of the current lanes so they never muddy a lane
                    fy = lrnd.randrange(int(self.h * .12), int(self.h * .72)) + HUD_H
                    fx = lrnd.randrange(4, self.w - 30)
                    if not any(fx < z[0] + z[2] and z[0] < fx + 24 and fy < z[1] + HUD_H + z[3] and z[1] + HUD_H < fy + 18
                               for z in self.zones) and not any(fx - 6 < f[0] < fx + 30 and fy - 6 < f[1] + HUD_H < fy + 24
                                                                for f in self.fish):
                        break
                landmark("floating", kind, lrnd.randrange(8, 17), lrnd.randrange(10 ** 6), fx,
                         lambda im, fy=fy: fy, floater=cols)

        self.surface_sp = add("surface", surface_img(self.w, 0), 0, HUD_H, L_SURFACE, ["surface"])
        self.surface_key = 0

        # jellyfish drifting in the open water: they pulse and smile and do nothing at all
        self.jellies = []
        jrnd = random.Random(6000 + i)
        for k in range(max(2, self.w * self.h // 3800)):
            for _try in range(10):             # keep a jellyfish off every fish's starting spot so the two never blur together
                jx, jy = jrnd.randrange(12, self.w - 24), jrnd.randrange(14, max(16, self.h - 40))
                if not any(fx - 16 < jx < fx + 20 and fy - 14 < jy < fy + 18 for fx, fy in [(self.px, self.py)] + [(f[0], f[1]) for f in self.fish]):
                    break
            pal_i = th["jelly"][k % len(th["jelly"])]
            sp = add(f"jelly_{k}", jelly_img(pal_i, 0, 0), jx, jy + HUD_H, L_MID, ["jelly"])
            self.jellies.append([sp, jx, jy, pal_i, k, None])
        # seahorses bob about in the quiet corners of some seas
        self.horses = []
        for k in range(len(th["crit"]) * (2 if self.w * self.h > 10000 else 1)):
            pal = th["crit"][k % len(th["crit"])]
            hx, hy = jrnd.randrange(16, self.w - 24), jrnd.randrange(12, max(14, self.h - 30))
            sp = add(f"seahorse_{k}", seahorse_img(pal, 0), hx, hy + HUD_H, L_MID, ["seahorse"])
            self.horses.append([sp, hx, hy, pal, k, None])
        # the level's own small drifting things
        self.motes = []
        mkind, mcols = th["motes"]
        for k in range(max(4, min(50, self.w * self.h // (5000 if mkind == "sparkle" else 900)))):
            mx, my = jrnd.randrange(2, self.w - 4), jrnd.randrange(4, self.h - 6)
            if any(z[0] - 2 <= mx < z[0] + z[2] and z[1] - 2 <= my < z[1] + z[3] for z in self.zones):
                continue                        # no drifting specks over a current: they would read as flow marks
            sp = add(f"{mkind}_{k}", mote_img(mkind, mcols, 0), mx, my + HUD_H, L_MID, ["mote", mkind])
            self.motes.append([sp, mkind, mcols, mx, my, k, None])
        # ambient bubbles rising here and there
        self.amb = []
        for k in range(self.w // 30):
            ax, ay0 = jrnd.randrange(2, self.w - 4), jrnd.randrange(0, self.h)
            big = k % 3 == 0
            sp = add(f"drift_bubble_{k}", BUBBLE if big else BUBBLE_S, ax, ay0 + HUD_H, L_MID, ["bubble"])
            self.amb.append((sp, ax, ay0, k, big))

        self.zone_sp = [add(f"current_{zi}", zone_img(z[2], z[3], self.zone_heading(zi), self.zone_heading(zi, 1), 0, 0),
                            z[0], z[1] + HUD_H, L_CURRENT, ["current"]) for zi, z in enumerate(self.zones)]
        self.zone_key = [None] * len(self.zones)
        add("bed", bed_img(tuple(self.bed), i), 0, full_h - 8, L_BED, ["bed"])

        # props along the bed. animated ones (anemone, grass, worms, lanterns, glow-things, snails, crabs, clams) and kelp
        # are kept in lists the sync moves
        self.wigglers, self.kelp_sp = [], []
        x = rnd.randrange(3, 9)
        while x < self.w - 12:
            kind = rnd.choice(th["props"])
            pal = rnd.choice(th["pals"])
            img, sc = prop_img(kind, 0, pal), PROP_SCALE.get(kind, 2)
            if not any(abs(x - v) < 12 for v in self.vents):
                sp = add(f"prop_{x}", img, x, full_h - self.bed[x] + 2 - img.shape[0] * sc, L_PROP, ["prop", kind], sc)
                if kind in ANIMATED or kind in WIGGLERS:
                    self.wigglers.append((sp, kind, pal, x, len(self.wigglers)))
            x += img.shape[1] * sc + rnd.randrange(th["gap"][0] * 2, th["gap"][1] * 2)     # round C: roomier bed
        if th["small"]:                        # tiny seabed detail between the big props: little stars and grass tufts
            for k in range(self.w // 72):
                sx = rnd.randrange(2, self.w - 10)
                kind = ("starfish", "seagrass", "starfish", "shell")[k % 4]
                pal = rnd.choice(th["pals"])
                img = prop_img(kind, 0, pal)
                sp = add(f"tiny_{k}", img, sx, full_h - self.bed[sx] + 2 - img.shape[0], L_PROP, ["prop", kind, "tiny"])
                if kind == "seagrass":
                    self.wigglers.append((sp, kind, pal, sx, len(self.wigglers)))
        for n, (kx, kh) in enumerate(self.kelp):
            if th["kelp"]:
                img = kelp_img(th["kstyle"], kh, 0, *th["kelp"])
                sp = add(f"kelp_{n}", img, kx - 8, full_h - self.bed[kx] + 2 - img.shape[0] * 2, L_PROP, ["kelp"], 2)
                self.kelp_sp.append((sp, kh, n))
            else:                                                   # no kelp here: a taller prop grows in its place
                kind = th["tall"][n % len(th["tall"])]
                img, sc = prop_img(kind, 0, th["pals"][n % len(th["pals"])]), PROP_SCALE.get(kind, 2)
                sp = add(f"tall_{n}", img, kx, full_h - self.bed[kx] + 2 - img.shape[0] * sc, L_PROP, ["prop", kind], sc)
                if kind in ANIMATED:
                    self.wigglers.append((sp, kind, th["pals"][n % len(th["pals"])], kx, len(self.wigglers)))

        # vents with a lava mouth and a stream of bubbles (the bubbles hide inside currents, as ff01's did)
        self.vent_sp, self.bubbles = [], []
        for n, vx in enumerate(self.vents):
            base = self.h - self.bed[vx]
            self.vent_sp.append(add(f"vent_{n}", vent_img(*th["vent"], 0), vx - 9, base + HUD_H - 8, L_PROP, ["vent"], 2))
            span = max(1, base - 10)
            for k in range(4):
                self.bubbles.append((add(f"bubble_{n}_{k}", BUBBLE, vx - 1, base + HUD_H, L_PROP, ["bubble"]), vx, base, k * span // 4))

        # glints: little twinkles low in the water that do nothing
        self.glints = []
        for n in range(4):
            gx, gy = rnd.randrange(2, self.w - 4), rnd.randrange(self.h * 3 // 5, self.h - 8)
            colour = th["glint"][n % len(th["glint"])]
            self.glints.append((add(f"glint_{n}", glint_img(colour, 1), gx, gy + HUD_H, L_PROP, ["glint"]), colour, n))

        # the fish, one named sprite each (species by index), and a mark on the window's edge for each when out of view
        self.fish_sp, self.mark_sp, self.fish_key = [], [], [None] * len(self.fish)
        self.fish_var = [(n * 2 + f[2]) % SPECIES for n, f in enumerate(self.fish)]
        for n, f in enumerate(self.fish):
            self.fish_sp.append(add(f"fish_{n}", fish_img(PAL_TIER[f[2]], f[2], self.fish_var[n], f[4], None, 0, 0, 0), f[0],
                                    f[1] + HUD_H, L_FISH, ["fish", f"tier{f[2]}"]))
            self.mark_sp.append(add(f"mark_{n}", np.full((2, 2), TIER_C[f[2]], dtype=np.int8), 0, 0, L_MARK, ["mark"]))
        self.player_sp = add("player", fish_img(PAL_PLAYER, self.size, 0, True, None, 0, 0, 0), self.px, self.py + HUD_H,
                             L_PLAYER, ["player"])
        self.player_key = None
        self.fx_sp = add("fx", np.full((VIEW_H, VIEW_W), -1, dtype=np.int8), 0, HUD_H, L_FX, ["fx"])
        self.wash_sp = add("wash", wash_img(1, 32, 28), 0, HUD_H, L_WASH, ["wash"])
        self.wash_sp.set_visible(False)
        self.hud_sp = add("hud", hud_img(0, 0, 0, 0, -1), 0, 0, L_HUD, ["hud"])

    # -- queries the drawing and the rules share ------------------------------------------------------------
    def camera_xy(self, px=None, py=None):
        px, py = (self.px if px is None else px), (self.py if py is None else py)
        cx = px + FISH_W[self.size] // 2 - VIEW_W // 2
        cy = py + FISH_H[self.size] // 2 - VIEW_H // 2
        return max(0, min(self.w - VIEW_W, cx)), max(0, min(self.h - VIEW_H, cy))

    def tide(self, ahead=0):
        return self.step_count // self.period + ahead

    def zone_heading(self, zi, ahead=0):
        heads = self.zones[zi][5]
        return heads[self.tide(ahead) % len(heads)]

    def fish_heading(self, f, ahead=0):
        return f[5][self.tide(ahead) % len(f[5])]

    def _zone_at(self, x, y, size):
        """The current carrying a body whose top-left is (x, y): the first zone holding its centre."""
        cx, cy = x + FISH_W[size] // 2, y + FISH_H[size] // 2
        for zi, (zx, zy, zw, zh, st, heads) in enumerate(self.zones):
            if zx <= cx < zx + zw and zy <= cy < zy + zh:
                return zi
        return -1

    def _zone_at_point(self, x, y):
        for zi, (zx, zy, zw, zh, st, heads) in enumerate(self.zones):
            if zx <= x < zx + zw and zy <= y < zy + zh:
                return zi
        return -1

    def _clamp(self, x, y, size):
        return (max(0, min(self.w - FISH_W[size], x)),
                max(2, min(self.h - FLOOR_ROWS - FISH_H[size], y)))

    def _carry(self, x, y, size):
        zi = self._zone_at(x, y, size)
        if zi < 0:
            return x, y
        dx, dy = DV[self.zone_heading(zi)]
        st = self.zones[zi][4]
        return self._clamp(x + dx * st, y + dy * st, size)

    @staticmethod
    def _touch(ax, ay, asz, bx, by, bsz):
        return ax < bx + FISH_W[bsz] and ax + FISH_W[asz] > bx and ay < by + FISH_H[bsz] and ay + FISH_H[asz] > by

    def _eat(self):
        for f in self.fish:
            if f[3] and f[2] <= self.size and self._touch(self.px, self.py, self.size, f[0], f[1], f[2]):
                f[3] = False
                self.eaten += 1
                self.bursts.append([f[0] + FISH_W[f[2]] // 2, f[1] + FISH_H[f[2]] // 2, 2, 0, 0])
                if self.grow and self.eaten >= self.grow[0]:
                    self.grow.pop(0)
                    self.size += 1
                    self.px, self.py = self._clamp(self.px, self.py, self.size)
                    self.bursts.append([self.px + FISH_W[self.size] // 2, self.py + FISH_H[self.size] // 2, 3, 0, 1])
                    self.grew = True
        return self.eaten >= self.eat

    # -- one action: the rules (ff01's, unchanged), then the picture follows the state ------------------------
    def step(self):
        """One engine call = one picture. An ordinary action plays FR of them: the rules run on the first, the others only
        glide the picture to the state the rules already reached (art only: the state never waits on the animation)."""
        self.clk += 1
        self.tw_frac, self.tw_t = 1.0, 0
        if self.pending_open:                      # the iris opening on a new level, after a level clear
            self.open_t += 1
            if self.open_t >= len(IRIS_OPEN):
                self.pending_open = False
                self.complete_action()
            self._sync()
            return
        if self.tw_left:
            self.tw_left -= 1
            self.tw_t = FR - self.tw_left
            self.tw_frac = EASE[self.tw_t - 1]
            if not self.tw_left:
                self.complete_action()
            self._sync()
            return
        self.pre = None
        plain = self.action.id != GameAction.RESET and not (self.winning or self.dying)
        if plain:
            self.bump, self.bit, self.grew = None, False, False
            snap = {"p": (self.px, self.py), "fish": [(f[0], f[1]) for f in self.fish],
                    "drift": [tuple(d) for d in self.zone_drift]}
        alive = [f[3] for f in self.fish]
        self._rules()
        for idx, f in enumerate(self.fish):          # art only: an eaten fish pops instead of vanishing
            if alive[idx] and not f[3]:
                self.pops[idx] = self.clk
        if plain and self.is_action_complete():    # the rules finished the action: hold it open for the glide frames
            self._action_complete = False
            self.pre, self.tw_left, self.tw_t, self.tw_frac = snap, FR - 1, 1, EASE[0]
        self._sync()

    @staticmethod
    def _age(bursts):
        """Grow every ring two steps; each keeps its previous radius so the picture can grow it smoothly."""
        return [[x, y, r + 2, k, r] for x, y, r, k, _ in bursts if r < 6]

    def _rules(self):
        if self.action.id == GameAction.RESET:
            self.complete_action()
            return
        if self.winning:                     # the level-clear animation, one frame per call
            self.winning += 1
            self.bursts = [[x, y, r + 2, k, r + 2] for x, y, r, k, _ in self.bursts if r < 6]
            if self.winning > WIN_FRAMES:
                self.winning = 0
                self.finale = self.is_last_level()      # art only: keep the sparkles on the final picture
                self.next_level()
                if self.finale:
                    self.complete_action()
                else:                                   # art only: the iris is shut; the next level opens it before the action ends
                    self.shut, self.pending_open = True, True
            return
        if self.dying:                       # the last bite: the fish rolls over and sinks
            self.dying += 1
            if self.dying > DEATH_FRAMES:
                self.lose()
                self.complete_action()
            return
        self.bursts = self._age(self.bursts)
        aid = self.action.id.value

        # 1. you swim, then the current you are in carries you
        if aid in (1, 2, 3, 4):
            d = (UP, DOWN, LEFT, RIGHT)[aid - 1]
            if d == LEFT:
                self.facing = False
            elif d == RIGHT:
                self.facing = True
            tx, ty = self.px + DV[d][0] * SWIM, self.py + DV[d][1] * SWIM
            self.px, self.py = self._clamp(tx, ty, self.size)
            if (self.px, self.py) != (tx, ty):          # art only: the fish met the edge of the sea
                self.bump = d
        self.px, self.py = self._carry(self.px, self.py, self.size)
        if self._eat():
            return self._start_win()

        # 2. every other fish swims its heading for this tide, then its current carries it
        for f in self.fish:
            if not f[3]:
                continue
            h = self.fish_heading(f)
            if h == LEFT:
                f[4] = False
            elif h == RIGHT:
                f[4] = True
            x, y = self._clamp(f[0] + DV[h][0] * FISH_SPEED, f[1] + DV[h][1] * FISH_SPEED, f[2])
            f[0], f[1] = self._carry(x, y, f[2])
        for zi in range(len(self.zones)):
            dx, dy = DV[self.zone_heading(zi)]
            st = self.zones[zi][4]
            self.zone_drift[zi][0] = (self.zone_drift[zi][0] + dx * st) % 64
            self.zone_drift[zi][1] = (self.zone_drift[zi][1] + dy * st) % 64
        self.step_count += 1
        if self._eat():
            return self._start_win()

        # 3. bigger fish bite
        if self.grace > 0:
            self.grace -= 1
        else:
            for f in self.fish:
                if f[3] and f[2] > self.size and self._touch(self.px, self.py, self.size, f[0], f[1], f[2]):
                    self.lives -= 1
                    self.grace = BITE_GRACE
                    self.bit = True
                    self.bursts.append([self.px + FISH_W[self.size] // 2, self.py + FISH_H[self.size] // 2, 2, 1, 0])
                    break
        if self.budget:
            self.moves_left -= 1
        if self.lives <= 0 or (self.budget and self.moves_left <= 0):
            self.lives = max(0, self.lives)
            self.dying = 1
            return
        self.complete_action()

    def _start_win(self):
        self.winning = 1

    # -- the picture --------------------------------------------------------------------------------------------
    @staticmethod
    def _seen(x, y, w, h, cx, cy, margin=6):
        """Is a sprite (sprite coordinates, so y already includes the HUD rows) anywhere near the window? Things that are
        far away are left as they were: they are redrawn the moment they come back into view."""
        return x < cx + VIEW_W + margin and x + w > cx - margin and y < cy + SCREEN + margin and y + h > cy - margin

    def _sync(self):
        """Move every sprite to match the state. Pictures change only through cached arrays, so a step stays cheap, and
        the third pass's extra life (motes, horses, beacons, strands, sunlight) is only touched when it is in view."""
        fr, pre = self.tw_frac, self.pre
        if pre:                                                 # glide: the fish is drawn part-way through its move
            vpx = pre["p"][0] + int((self.px - pre["p"][0]) * fr)
            vpy = pre["p"][1] + int((self.py - pre["p"][1]) * fr)
        else:
            vpx, vpy = self.px, self.py
        self.vpos = (vpx, vpy)
        cx, cy = self.camera_xy(vpx, vpy)
        self.camera.x, self.camera.y = cx, cy
        n, c = self.step_count, self.clk                        # n = the game's steps; c = pictures drawn (FR per step)
        a = c / FR                                              # the same clock in steps, smooth between them
        th = THEMES[self.level_index]
        seen = self._seen

        phase = (c // 3) % 7                                    # surface crests drift
        if phase != self.surface_key:
            self.surface_key = phase
            self.surface_sp.pixels = surface_img(self.w, phase)

        for zi, (zx, zy, zw, zh, st, heads) in enumerate(self.zones):   # currents: only re-draw those in view
            if zx < cx + VIEW_W and zx + zw > cx and zy + HUD_H < cy + SCREEN and zy + HUD_H + zh > cy:
                dr = self.zone_drift[zi]
                if pre:                                         # the streaks and chevrons slide the short way to their new place
                    dr = [(pre["drift"][zi][k] + int((((dr[k] - pre["drift"][zi][k] + 32) % 64) - 32) * fr)) % 64 for k in (0, 1)]
                key = (self.zone_heading(zi), self.zone_heading(zi, 1), *dr)
                if key != self.zone_key[zi]:
                    self.zone_key[zi] = key
                    self.zone_sp[zi].pixels = zone_img(zw, zh, *key)

        for sp, kh, idx in self.kelp_sp:
            sp.pixels = kelp_img(th["kstyle"], kh, (c // 4 + idx) % 4, *th["kelp"])
        for sp, kind, pal, x0, idx in self.wigglers:
            if kind == "clam":                                  # the clam opens now and then to show its pearl
                sp.pixels = prop_img(kind, 1 if (c // 8 + idx) % 5 == 0 else 0, pal)
            elif kind == "crab":                                # the crab sidles back and forth and shuffles its legs
                sp.pixels = prop_img(kind, (c // 3 + idx) % 2, pal)
                sp.set_position(max(0, x0 + int(round(2 * (abs((a / 3 + idx * 3) % 12 - 6) - 3)))), sp.y)
            elif kind == "hermit":                              # the hermit crab carries its shell the other way, slowly
                sp.pixels = prop_img(kind, (c // 5 + idx) % 2, pal)
                sp.set_position(max(0, x0 + int(abs((a / 5 + idx * 5) % 16 - 8)) - 4), sp.y)
            elif kind == "lantern" or kind == "glowshroom" or kind == "lure":     # glow things pulse, out of step with one another
                sp.pixels = prop_img(kind, 1 if (c // 6 + idx) % 3 == 0 else 0, pal)
            else:                                               # grass, worms, anemones, snails, lava rocks: a slow shift
                sp.pixels = prop_img(kind, (c // 4 + idx) % ANIMATED[kind], pal)
        for k, sp in enumerate(self.vent_sp):
            sp.pixels = vent_img(*th["vent"], (c // 2 + k) % 2)
        for sp, vx, base, j in self.bubbles:
            by = base - 9 - (int(a * 2) + j) % max(1, base - 10)
            bx = vx + (1 if (by // 4) % 2 else 0)
            sp.set_position(bx - 1, by - 1 + HUD_H)
            sp.set_visible(self._zone_at_point(bx, by) < 0)
        for sp, colour, idx in self.glints:
            pat = (0, 1, 2, 3, 0, 0)[((c + idx * 9) // 4) % 6]
            sp.pixels = glint_img(colour, pat)
            sp.set_visible(pat > 0)
        for jel in self.jellies:                                # jellyfish: a slow figure of eight, a pulse, a wave
            sp, jx, jy, pal_i, k, key = jel
            nk = (pal_i, 1 if (c // 5 + k) % 4 in (1, 2) else 0, (c // 3 + k) % 2)
            if nk != key:
                jel[5] = nk
                sp.pixels = jelly_img(*nk)
            sp.set_position(jx + int(round(8 * math.sin(a / 29.0 + k * 1.7))),
                            jy + HUD_H + int(round(6 * math.sin(a / 19.0 + k * 2.3))))
        for hs in self.horses:                                  # seahorses bob and flutter their fins
            sp, hx, hy, pal, k, key = hs
            px_, py_ = hx + int(round(3 * math.sin(a / 21.0 + k))), hy + HUD_H + int(round(5 * math.sin(a / 13.0 + k * 1.9)))
            if seen(px_, py_, SEAHORSE_W, SEAHORSE_H, cx, cy):
                nk = (c // 4 + k) % 2
                if nk != key:
                    hs[5] = nk
                    sp.pixels = seahorse_img(pal, nk)
                sp.set_position(px_, py_)
        for mt in self.motes:                                   # the level's own drifting things
            sp, kind, cols, mx, my, k, key = mt
            qx, qy = (int(v) for v in _mote_pos(kind, mx, my, k, a, self.w, self.h))
            if seen(qx, qy + HUD_H, 5, 5, cx, cy):
                nk = (c // 4 + k) % 4
                if nk != key:
                    mt[6] = nk
                    sp.pixels = mote_img(kind, cols, nk)
                sp.set_position(qx, qy + HUD_H)
        for bsp, bx, by, bw, cols, k in self.beacons:           # lights on towers, spires and wreck portholes blink
            if seen(bx, by, 3, 3, cx, cy):
                pat = ((c // 4 + k * 5) % 8)
                if bw == 3:
                    bsp.pixels = glint_img(cols[(c // 72 + k) % len(cols)], (1, 2, 1, 0, 0, 0, 0, 0)[pat])
                else:
                    bsp.pixels = port_img((ORANGE, WHITE, ORANGE, ORANGE, SKY, ORANGE, WHITE, SKY)[pat])
        for sp, kind, hh, seed, bx, k in self.strands:          # the giant kelp leans slowly
            if seen(bx, sp.y, 14, hh, cx, cy):
                sp.pixels = landmark_img(self.level_index, kind, hh, seed, False, (0, 1, 2, 1)[(c // 10 + k) % 4])[0]
        for sp, sx, sh_h, k in self.shafts:                     # sunlight creeps
            if seen(sx, sp.y, 11 + sh_h // 3, sh_h, cx, cy):
                sp.pixels = shaft_img(sh_h, (c // 8 + k) % 4)
        for sp, ax, ay0, k, big in self.amb:                    # ambient bubbles climb, wobbling sideways
            ay = (ay0 - int((a + k * 5) * (1 + k % 2))) % self.h
            sp.set_position(ax + (1 if (ay // 5 + k) % 2 else 0), ay + HUD_H)

        show_marks = not (self.winning or self.dying)
        for idx, f in enumerate(self.fish):
            sp, mark = self.fish_sp[idx], self.mark_sp[idx]
            if not f[3]:
                age = c - self.pops.get(idx, -9)
                mark.set_visible(False)
                if 0 <= age <= 1:                               # eaten: a white flash of the whole fish, then a little star
                    if age == 0:
                        sp.pixels = fish_img(PAL_FLASH, f[2], self.fish_var[idx], f[4], None, 0, EYE_CHEER, 1)
                        sp.set_position(f[0], f[1] + HUD_H)
                    else:
                        sp.pixels = POP_STAR
                        sp.set_position(f[0] + FISH_W[f[2]] // 2 - 1, f[1] + FISH_H[f[2]] // 2 - 1 + HUD_H)
                    self.fish_key[idx] = ("pop", age)
                    sp.set_visible(True)
                else:
                    sp.set_visible(False)
                continue
            big_mouth = 1 if f[2] >= 3 and (c // 3 + idx * 5) % 9 == 0 else 0    # the big ones snap their jaws now and then
            key = (f[2], f[4], self.fish_heading(f, 1), (c // 2 + idx) & 3, 1 if (c + idx * 21) % 51 < 2 else 0, big_mouth)
            if key != self.fish_key[idx]:
                self.fish_key[idx] = key
                sp.pixels = fish_img(PAL_TIER[f[2]], f[2], self.fish_var[idx], key[1], key[2], key[3], key[4], key[5])
            gx, gy = f[0], f[1]
            if pre:                                             # every fish glides to its new cell with the fish
                gx, gy = pre["fish"][idx][0] + int((f[0] - pre["fish"][idx][0]) * fr), pre["fish"][idx][1] + int((f[1] - pre["fish"][idx][1]) * fr)
            sp.set_position(gx, gy + HUD_H)
            sp.set_visible(True)
            # every fish off the window: a 2x2 mark in its colour on the window's edge, on the line towards it
            fx = gx + FISH_W[f[2]] // 2 - cx
            fy = gy + FISH_H[f[2]] // 2 - cy
            if show_marks and not (0 <= fx < VIEW_W and 0 <= fy < VIEW_H):
                mark.set_position(cx + max(0, min(VIEW_W - 2, fx)), cy + HUD_H + max(0, min(VIEW_H - 2, fy)))
                mark.set_visible(True)
            else:
                mark.set_visible(False)

        self._sync_player()
        self._sync_effects(cx, cy)
        left = self.period - n % self.period
        bar = max(0, int(math.ceil(SCREEN * self.moves_left / self.budget))) if self.budget else -1
        self.hud_sp.pixels = hud_img(self.lives, self.eat, self.eaten, left, bar)
        self.hud_sp.set_position(cx, cy)

    def _sync_player(self):
        sp, c, t = self.player_sp, self.clk, self.tw_t
        vpx, vpy = self.vpos
        if self.dying:                          # belly up, red and dark, crossed-out eyes, sinking
            key = ("dead", self.size, self.facing)
            pix, flip = fish_img(PAL_DEAD, self.size, 0, self.facing, None, 0, EYE_DEAD, 0), True
            pos, visible = (self.px, self.py + HUD_H + min(self.dying, 4)), True
        elif self.winning:                      # the level-clear dance: grin, spin, rise and flash
            w = self.winning
            spin = self.facing if (w // 2) % 2 == 0 else not self.facing
            pal = PAL_FLASH if w % 4 >= 2 else PAL_PLAYER
            key = ("win", self.size, spin, pal is PAL_FLASH)
            pix, flip = fish_img(pal, self.size, 0, spin, None, w % 4, EYE_CHEER, 1), False
            pos, visible = (self.px, self.py - rise_of(w) + HUD_H), True
        else:
            hurt = self.grace > 0
            chomp = 1 if (self.bursts or hurt) else 0       # mouth open after a meal, and in a wince after a bite
            squint = self.bump is not None and t in (1, 2)  # a bump on the edge of the sea: eyes shut for a moment
            eyes = EYE_WINCE if hurt else (EYE_BLINK if (c % 69 in (15, 16) or squint) else EYE_OPEN)
            flash = (self.grew and t in (1, 3)) or (self.bit and t == 1)    # just grew, or just bitten: a quick white flash
            sq = 0                                          # squash and stretch: long while gliding, short when it lands
            pre = self.pre
            if pre and t in (1, 2) and (self.px != pre["p"][0] or self.py != pre["p"][1]):
                horiz = abs(self.px - pre["p"][0]) >= abs(self.py - pre["p"][1])
                sq = (1 if t == 1 else -1) * (1 if horiz else 2)
            key = ("swim", self.size, self.facing, c & 3, eyes, chomp, flash, sq)
            pix, flip = fish_img(PAL_FLASH if flash else PAL_PLAYER, self.size, 0, self.facing, None, c & 3, eyes, chomp), False
            bx_ = by_ = 0
            if sq:
                horiz = abs(sq) == 1
                pix, bx_, by_ = bend(pix, self.facing, 0 if horiz else 1, 1 if sq > 0 else -1)
                if not horiz and sq > 0 and self.py > pre["p"][1]:
                    by_ = -1                                # a stretch while sinking trails above, so the head leads
            px_, py_ = vpx + bx_, vpy + by_
            if self.bump is not None and t in (1, 2):       # nudge into the edge, then bounce back off it
                px_ += DV[self.bump][0] * (1 if t == 1 else -1)
                py_ += DV[self.bump][1] * (1 if t == 1 else -1)
            pos = (px_, py_ + HUD_H)
            visible = not (hurt and c % 2 == 1 and t not in (1, FR))  # blinks while safe after a bite; the last picture is always whole
        if self.winning:
            key = key + (self.winning % 2,)
        if key != self.player_key:
            self.player_key = key
            sp.pixels = pix
            sp.set_mirror_ud(flip)
        sp.set_position(*pos)
        sp.set_visible(visible)

    def _sync_effects(self, cx, cy):
        """Rings where something was eaten or bit, a wake behind the swimming fish, a puff on a bump, a welcome of bubbles at
        the start of a level, the level-clear shower, the lost-run tint and the iris between levels, on one see-through
        sheet laid over the window; hidden when nothing is happening."""
        t, c, pre = self.tw_t, self.clk, self.pre
        calm = not (self.winning or self.dying)
        arriving = c < 6 * FR and calm and not self.pending_open
        moved = bool(pre and t and calm and (self.px != pre["p"][0] or self.py != pre["p"][1]))
        bumped = bool(self.bump is not None and t and calm)
        bitten = bool(self.bit and t in (1, 2) and calm)
        burp = bool(calm and not self.finale and self.step_count % 9 == 4 and c >= 3)
        iris = self.shut or self.pending_open or (self.winning > WIN_FRAMES - 4 and not self.is_last_level())
        active = bool(self.bursts or self.winning or self.dying or self.finale or arriving or moved or bumped or bitten or burp
                      or iris)
        self.fx_sp.set_visible(active)
        self.wash_sp.set_visible(bool(self.dying))
        if self.dying:
            ox_, oy_ = self.px + FISH_W[self.size] // 2 - cx, self.py + FISH_H[self.size] // 2 - cy
            self.wash_sp.pixels = wash_img(min(self.dying, 5), max(0, min(VIEW_W - 1, ox_)), max(0, min(VIEW_H - 1, oy_)))
            self.wash_sp.set_position(cx, cy + HUD_H)
        if not active:
            return
        sheet = np.full((VIEW_H, VIEW_W), -1, dtype=np.int8)

        def dot(wx, wy, colour, big=False):
            sx, sy = wx - cx, wy - cy
            for ox, oy in (((0, 0), (1, 0), (0, 1), (1, 1)) if big else ((0, 0),)):
                if 0 <= sx + ox < VIEW_W and 0 <= sy + oy < VIEW_H:
                    sheet[sy + oy, sx + ox] = colour

        def ring(wx, wy, r, colours):
            for k in range(8):
                a = k * math.pi / 4
                dot(int(round(wx + r * math.cos(a))), int(round(wy + r * math.sin(a))), colours[k % 2], r >= 4)

        def star(wx, wy, colour):
            for ox, oy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                dot(wx + ox, wy + oy, colour)

        def bubble(wx, wy):
            for ox, oy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                dot(wx + ox, wy + oy, WHITE)

        for bx, by, r, kind, r0 in self.bursts:             # rings grow smoothly from their last size
            ring(bx, by, int(round(r0 + (r - r0) * self.tw_frac)), (RED, YELLOW) if kind else (WHITE, SKY))
        vpx, vpy = self.vpos
        centre_x = self.px + FISH_W[self.size] // 2
        vcx, vcy = vpx + FISH_W[self.size] // 2, vpy + FISH_H[self.size] // 2
        if moved:                                            # a wake: two clear streaks trail the fish and a big bubble rises
            ddx, ddy = self.px - pre["p"][0], self.py - pre["p"][1]
            mx, my = (int(math.copysign(1, ddx)) if abs(ddx) >= abs(ddy) else 0, int(math.copysign(1, ddy)) if abs(ddy) > abs(ddx) else 0)
            ocx, ocy = pre["p"][0] + FISH_W[self.size] // 2, pre["p"][1] + FISH_H[self.size] // 2
            half = (FISH_W[self.size] if mx else FISH_H[self.size]) // 2
            side = (FISH_H[self.size] if mx else FISH_W[self.size]) // 2 - 1     # the streaks run along the fish's two long edges
            if t < FR:
                for k in (-1, 1):
                    for j in range(5 - t):
                        dot(ocx - mx * (half + 1 + j) - my * k * side, ocy - my * (half + 1 + j) + mx * k * side,
                            WHITE if j < 3 and t == 1 else SKY)
                dot(ocx - mx * (half + 3), ocy - my * (half + 3) - 2, WHITE, True)
        if bumped and t < FR:                                # a puff on the edge the fish bumped: three round clouds fly apart
            bdx, bdy = DV[self.bump]
            hx = vcx + bdx * (FISH_W[self.size] // 2 + 1)
            hy = vcy + bdy * (FISH_H[self.size] // 2 + 1)
            for k in (-1, 0, 1):
                dot(hx + abs(bdy) * k * (2 * t + 1) - bdx * (t - 1), hy + abs(bdx) * k * (2 * t + 1) - bdy * (t - 1),
                    WHITE if t == 1 else SKY, True)
        if bitten:                                           # a bite: a thick red frame flashes round the window, then thins
            w_ = 3 if t == 1 else 1
            sheet[:w_, :] = sheet[-w_:, :] = sheet[:, :w_] = sheet[:, -w_:] = RED
        if burp and calm:                                    # now and then the fish lets out a bubble, which rises
            dot(vpx + (FISH_W[self.size] if self.facing else -1), vpy + FISH_H[self.size] // 2 - (c % FR), WHITE)
        if arriving:                                         # a welcome: bubbles lift off the fish as the level opens
            ta = c / FR
            for k in range(5):
                bubble(centre_x + (k - 2) * 4 + (c + k) % 2, int(self.py + FISH_H[self.size] // 2 - 2 - ta * 3 - k * 2))
        if self.winning or self.finale:
            w = self.winning or WIN_FRAMES
            centre_y = self.py - rise_of(w) + FISH_H[self.size] // 2
            if self.winning:
                ring(centre_x, centre_y, 2 + w * 3, (WHITE, YELLOW))
                for k in range(1):                               # two fireworks pop around the window, one after another
                    if w >= 2 + k * 3:
                        fx0, fy0 = cx + 10 + (k * 23) % (VIEW_W - 20), cy + 8 + (k * 17) % (VIEW_H - 16)
                        ring(fx0, fy0, (w - 2 - k * 3) + 1, ((ORANGE, GREEN)[k], WHITE))
            for k in range(4):                                  # a turning crown of sparkles
                a = k * math.pi / 2 + w * 0.35
                rad = 5 + int(w * 1.6)
                star(centre_x + int(round(rad * math.cos(a))), centre_y + int(round(rad * math.sin(a))),
                     (YELLOW, WHITE, PINK)[(k + w) % 3])
            for k in range(6):                                  # confetti tumbling down the window
                colour = (ORANGE, GREEN, PINK, MAGENTA, WHITE, SKY)[k % 6]
                fx_ = cx + (k * 37 + 5) % (VIEW_W - 2) + (w % 2) + int(round(2 * math.sin(w / 2.0 + k)))
                fy_ = cy + (k * 13 + w * 4 + (k % 3) * 9) % (VIEW_H - 2)
                dot(fx_, fy_, colour, True)
                if k % 4 == 0:                                  # every fourth one trails a streamer
                    dot(fx_, fy_ - 2, colour)
                    dot(fx_, fy_ - 3, colour)
        if self.dying:
            d = self.dying
            centre_y = self.py + FISH_H[self.size] // 2
            ring(centre_x, centre_y, 2 + d, (PINK, WHITE))
            for k in range(2):                                  # last bubbles float up from the fish
                bubble(centre_x + (k * 2 - 1) * 3 + (d % 2), centre_y - d * 2 - k * 4)
        if iris:                                                 # the iris: shuts round the fish on a clear, opens on the next sea
            if self.shut:
                sheet[:, :] = BLACK
            else:
                r = IRIS_CLOSE[self.winning - (WIN_FRAMES - 3)] if not self.pending_open else IRIS_OPEN[min(self.open_t, len(IRIS_OPEN) - 1)]
                ox_, oy_ = self.px + FISH_W[self.size] // 2 - cx, self.py + FISH_H[self.size] // 2 - cy
                if self.winning:
                    oy_ -= rise_of(self.winning)
                ys, xs = np.mgrid[0:VIEW_H, 0:VIEW_W]
                sheet[(xs - ox_) ** 2 + (ys - oy_) ** 2 > r * r] = BLACK
        self.fx_sp.pixels = sheet
        self.fx_sp.set_position(cx, cy + HUD_H)
