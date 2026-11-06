# ARC-AGI-3 candidate task se01 (Shrine Exploration).
# Updated: 05-November-2026, Claude Fable 5.1 -- the game is se01 (it reported itself as xb02); the unused per-level
#   "order" list is gone (no rule ever read it).
# Updated: 06-November-2026, Claude Fable 5.1 -- a RESET or a new level restarts the art's animation beat too, so the
#   first frame no longer carries the old run's flame, pond and flower phase; unused constants removed.
#
# Author: Claude Sonnet 5.5 Max
# Date: 31-October-2026
# PURPOSE: Version 2 of xb01 (shrines and seals in a scrolling world). Rules, map, levels, routes, the colours a
#          rule reads, the inputs and the camera are unchanged; only the drawing changed. The world is still
#          painted from the model each frame (it is larger than the 64-pixel camera), but from one pre-drawn
#          world picture plus a few live pieces: a hooded pilgrim and horned patrols with faces, thorn bushes,
#          barred seal slabs that join into gates, braziers, brick shrine buildings with roofs, a sanctum door
#          with a stair, oaks, pines, ponds and flowers. Walking, patrols and scrolling slide over three frames
#          and settle on the last.
# SRP/DRY check: Pass. The art helpers below are a small sprite set kept in this file so it stands alone;
#          the rules (Ground, Arrangement, passable, _step_foes, _caught, _send_back) are
#          the xb01 code unchanged.
# CHANGELOG
# 31-Oct-2026 (Claude Sonnet 5.5 Max): xb02, sprite glow-up of xb01. Art and a three-frame slide only.

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

# Palette names used by the art only (the rule colours are the named constants further down).
WHT, BLK, MAG, PNK, RED, BLU, LBL, YEL, ORG, MAR, GRN, PUR = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
LEGEND = dict(k=BLK, w=WHT, m=MAR, o=ORG, y=YEL, g=GRN, b=BLU, l=LBL, p=PNK, c=MAG, r=RED, u=PUR, t=MAR, s=GRN)


def art(rows, legend=None) -> np.ndarray:
    """Draw a sprite from text rows: '.' is see-through, a letter is a palette colour."""
    legend = legend or LEGEND
    out = np.full((len(rows), len(rows[0])), -1, dtype=np.int16)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                out[y, x] = legend[ch]
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


# ---- scenery -----------------------------------------------------------------------------------------------
OAK = art((".kk.kk..", "kggkggk.", "kgggggkk", "kgkgkgkk",       # a broad oak: bumpy crown, shaded underside
           "kkgkgkkk", ".kkkkkk.", "..kttk..", ".tt..tt."))
OAK_B = art(("..kk.kk.", ".kggkggk", "kkgggggk", "kkgkgkgk",
             "kkkgkgkk", ".kkkkkk.", "..kttk..", ".tt..tt."))
PINE = art(("...kk...", "..kggk..", ".kggggk.", "..kgkk..",
            ".kgkgkk.", "kgkgkkkk", "kkkkkkkk", "...tt..."))


def pond_art(phase: int) -> np.ndarray:
    """A round blue pond; three light glints travel round it on the beat."""
    rows = ["..bbbb..", ".bbbbbb.", "bbbbbbbb", "bbbbbbbb", "bbbbbbbb", ".bbbbbb.", "..bbbb..", "........"]
    spr = art(rows)
    for y, x in ((1, 3), (3, 5), (4, 1)):
        xx = (x + phase) % 8
        if spr[y, xx] >= 0:
            spr[y, xx] = LBL
    spr[2, 1] = LBL if phase % 2 == 0 else BLU           # a shore glint
    return spr


# ---- buildings ----------------------------------------------------------------------------------------------
def brick_tile(face: int, mortar: int, row: int) -> np.ndarray:
    return art(("fffm", "mmmm", "fmff", "mmmm") if row % 2 == 0 else ("fmff", "mmmm", "fffm", "mmmm"),
               dict(f=face, m=mortar))


ROOF_TILE = art(("kkkk", "oooo", "mmmm", "mkmk"))      # a maroon tiled roof with an orange ridge
ROOF_TILE_B = art(("kkkk", "oooo", "mmmm", "kmkm"))
ARCH = art(("ollllllllllo", "okkkkkkkkkko", "okkkkyykkkko", "okkkyyyykkko"))     # the sanctum door: a wide gate in the wall
ARCH_B = art(("ollllllllllo", "okkkkkkkkkko", "okkkkkkkkkko", "okkkyyyykkko"))
PAD = art((".llllll.", "llyyyyll", "llyyyyll", ".llllll."))     # the glowing light-blue pad in front of the gate
PAD_B = art((".llllll.", "llwwwwll", "llwwwwll", ".llllll."))


# ---- the creatures --------------------------------------------------------------------------------------------
PILGRIM = {
    (0, 1): (".kkkk.", "kkkkkk", "kwkkwk", "kmmmmk", "kkkkkk", ".kkkk."),
    (0, -1): (".kkkk.", "kkkkkk", "kkkkkk", "kkmmkk", "kkmmkk", ".kkkk."),
    (-1, 0): (".kkkk.", "kkkkkk", "kwkkkk", "kmmmmm", "kkkkkk", ".kkkk."),
    (1, 0): (".kkkk.", "kkkkkk", "kkkkwk", "mmmmmk", "kkkkkk", ".kkkk."),
}
PILGRIM_LEGS = (".k..k.", "..kk..")


def pilgrim(face: tuple, leg: int) -> np.ndarray:
    """A black hooded pilgrim with two white eyes, a maroon scarf and walking legs."""
    return art(PILGRIM[face] + (PILGRIM_LEGS[leg % 2],))


def imp(heading: tuple, leg: int) -> np.ndarray:
    """A magenta horned patrol. Each eye is half white, half black: the black half looks where it is heading."""
    top, bottom = {(0, 1): ("ww", "kk"), (0, -1): ("kk", "ww"),
                   (-1, 0): ("kw", "kw"), (1, 0): ("wk", "wk")}[heading]
    rows = ("c.....c", "ccccccc",
            "c" + top + "c" + top + "c",
            "c" + bottom + "c" + bottom + "c",
            "ckwkwkc", ".ccccc.",
            ("cc...cc", ".cc.cc.")[leg % 2])
    return art(rows)


THORN = art(("c.cc.c", ".cccc.", "ckckcc", "cckckc", ".kkkk."))        # a tangle of bramble, no stalk, no face
THORN_ALT = art(("cc.c.c", ".cccc.", "cckckc", "ckckcc", ".kkkk."))


def burst(frame: np.ndarray, cx: int, cy: int, radius: int, colour: int) -> None:
    """A little star: eight rays, grown one pixel at a time (the catch flash)."""
    h, w = frame.shape
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        for r in range(max(1, radius - 1), radius + 1):
            x, y = cx + dx * r, cy + dy * r
            if 0 <= x < w and 0 <= y < h:
                frame[y, x] = colour if r == radius else WHT


# ---- the shrine brazier, the seal slab, the flowers ------------------------------------------------------------
FLAME_A = ("..w.", ".ww.", ".wyw", "wwyw")
FLAME_B = (".w..", ".ww.", "wyw.", "wyww")
BOWL = ("pppp", "kppk", ".kk.", "kkkk")


def brazier(flame_size: int, frame_index: int, rim: int) -> np.ndarray:
    """Four wide, eight tall: four rows of flame (0 to 4 of them lit) over the bowl on its stem."""
    flame = FLAME_A if frame_index % 2 == 0 else FLAME_B
    rows = ["...." if r < 4 - flame_size else flame[r] for r in range(4)]
    out = art(tuple(rows) + BOWL)
    out[4, :] = np.where(out[4, :] >= 0, rim, out[4, :])
    return out


def seal_tile(colour: int, top: bool, bottom: bool, left: bool) -> np.ndarray:
    """A barred slab in the seal's colour. Black only where it meets something that is not the same gate, so a
    block of cells joins into one gate; the black planks inside are the bars."""
    t = np.full((4, 4), colour, dtype=np.int16)
    t[:, 3] = BLK                                      # the bars
    if top:
        t[0, :] = BLK
    if bottom:
        t[3, :] = BLK
    if left:
        t[:, 0] = BLK
    return t


def flower(petal: int, centre: int, open_: bool) -> np.ndarray:
    if open_:
        return art(("p.p.", ".c..", "p.p.", ".sg."), dict(p=petal, c=centre, s=GRN, g=GRN))
    return art(("....", ".p..", ".s..", ".sg."), dict(p=petal, s=GRN, g=GRN))


VOID, STONE_HUE, GROUND_HUE = 5, 14, 11
BRICK_FACE, BRICK_MORTAR = 12, 13
SEAL_HUE = (8, 9, 15, 1)
PLATE_OFF = 7
FOE_BODY = 6
PROP_HUE = (6, 7, 10, 0, 12, 15)

CELL = 4
VIEW = 16
SCREEN = VIEW * CELL

STONE_CH, THORN_CH = "#", "x"
CORNERS = ((-1, -1, 0, 0), (1, -1, 3, 0), (-1, 1, 0, 3), (1, 1, 3, 3))


def _hash(x: int, y: int, salt: int) -> int:
    n = (x * 73856093) ^ (y * 19349663) ^ (salt * 83492791)
    n = (n ^ (n >> 13)) & 0xFFFFFFFF
    n = (n * 1274126177) & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFFFFFFFF


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


def _scenery(wx: int, wy: int):
    if not GROUND.stone(wx, wy) or _building(wx, wy):
        return None
    k = _hash(wx, wy, 7)
    wood = _hash(wx // 7, wy // 7, 17) % 3 == 0
    if wx % 2 == 0 and wy % 2 == 0 and all(
            GROUND.stone(wx + a, wy + b) and not _building(wx + a, wy + b)
            for a in (-1, 0, 1, 2) for b in (-1, 0, 1, 2)):
        if wood:
            return "pine" if k % 4 else "tree"
        if k % 5 == 0:
            return "pond" if k % 3 == 0 else "tree"
        return None
    if k % 7 == 1 and any(not GROUND.stone(wx + a, wy + b)
                          for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
        return "bush"
    return None



# ---- the pre-drawn world -------------------------------------------------------------------------------------
# Everything that never changes (fields, tracks, stepped edges, brick buildings, roofs, thorn bushes, trees,
# bushes) is drawn once into one picture of the whole world; each frame cuts the camera window out of it and
# draws the live pieces on top. The picture is module data, not game state, so copy.deepcopy never touches it.
SHRINE_BOXES = [(bx, by, by - 2) for bx, by in GROUND.shrines] + [(*GROUND.sanctum, GROUND.sanctum[1] - 3)]


def _wall_cells() -> set:
    """Stone drawn as a building: the 5x5 around each shrine and the sanctum, and the roof row above it."""
    cells = set()
    for x in range(GROUND.w):
        for y in range(GROUND.h):
            if GROUND.stone(x, y) and _building(x, y):
                cells.add((x, y))
    for bx, by, ry in SHRINE_BOXES:
        for x in range(bx - 2, bx + 3):
            if GROUND.stone(x, ry):
                cells.add((x, ry))
    return cells


WALLS = _wall_cells()
ROOFS = {(bx + dx, ry) for bx, by, ry in SHRINE_BOXES for dx in range(-2, 3) if (bx + dx, ry) in WALLS}


def _shave(patch: np.ndarray, px: int, py: int, colour: int) -> None:
    """Step a corner by three pixels (the corner pixel and its two neighbours along the edges)."""
    sx, sy = (1 if px == 0 else -1), (1 if py == 0 else -1)
    patch[py, px] = colour
    patch[py, px + sx] = colour
    patch[py + sy, px] = colour


def _build_world():
    img = np.full((GROUND.h * CELL, GROUND.w * CELL), STONE_HUE, dtype=np.int16)
    stone = GROUND.stone
    ponds = []

    def cell(x, y):
        return img[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL]

    for wy in range(GROUND.h):
        for wx in range(GROUND.w):
            patch = cell(wx, wy)
            if (wx, wy) in WALLS:
                continue
            if stone(wx, wy):
                for dx, dy, px, py in CORNERS:
                    if not stone(wx + dx, wy) and not stone(wx, wy + dy):
                        _shave(patch, px, py, GROUND_HUE)
                continue
            patch[:] = GROUND_HUE
            for dx, dy, px, py in CORNERS:
                if (stone(wx + dx, wy) and stone(wx, wy + dy)
                        and (wx + dx, wy) not in WALLS and (wx, wy + dy) not in WALLS):
                    _shave(patch, px, py, STONE_HUE)

    # the buildings: brick walls, scalloped roofs, and a black outline wherever a wall meets anything else
    for (wx, wy) in WALLS:
        if (wx, wy) in ROOFS:
            tile = (ROOF_TILE if (wx + wy) % 2 == 0 else ROOF_TILE_B).copy()
        else:
            tile = brick_tile(BRICK_FACE, BRICK_MORTAR, wy)
        if (wx, wy - 1) not in WALLS:
            tile[0, :] = BLK
        if (wx, wy + 1) not in WALLS:
            tile[3, :] = BLK
        if (wx - 1, wy) not in WALLS:
            tile[:, 0] = BLK
        if (wx + 1, wy) not in WALLS:
            tile[:, 3] = BLK
        cell(wx, wy)[:] = tile

    for wy in range(GROUND.h):
        for wx in range(GROUND.w):
            if GROUND.thorn(wx, wy):
                blit(img, wx * CELL - 1, wy * CELL, THORN if (wx + wy) % 2 == 0 else THORN_ALT)

    for wy in range(GROUND.h):
        for wx in range(GROUND.w):
            kind = _scenery(wx, wy)
            if kind is None or (wx, wy) in WALLS:
                continue
            k = _hash(wx, wy, 7)
            if kind == "pond":
                ponds.append((wx, wy))
            elif kind == "bush":
                continue                                     # no thickets: the edge steps are enough
            elif any((wx + a, wy + b) in WALLS for a in (0, 1) for b in (0, 1)):
                continue
            elif kind == "pine":
                blit(img, wx * CELL, wy * CELL, PINE)
            else:
                spr = OAK if (k >> 3) % 3 else OAK_B
                blit(img, wx * CELL, wy * CELL, flip(spr) if (k >> 5) % 2 else spr)
    return img, ponds


WORLD_IMG, PONDS = _build_world()


class Window(RenderableUserDisplay):

    def __init__(self, game: "Se01") -> None:
        super().__init__()
        self._g = game

    def _lerp(self, a: int, b: int, k: int) -> int:
        """Pixel position a third (k=1), two thirds (k=2) or all (k=3) of the way from cell a to cell b."""
        return a * CELL + int(round((b - a) * CELL * k / 3))

    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        g = self._g
        lv = g.arrangement
        k = max(1, min(3, g.tick))
        if g.hit and k < 3:                                  # a catch: the picture holds still, then jumps back
            camx, camy = g.prev_cam[0] * CELL, g.prev_cam[1] * CELL
        else:
            camx = self._lerp(g.prev_cam[0], g.cam_x, k)
            camy = self._lerp(g.prev_cam[1], g.cam_y, k)
        frame[:] = WORLD_IMG[camy:camy + SCREEN, camx:camx + SCREEN]

        for (wx, wy) in PONDS:
            x, y = wx * CELL - camx, wy * CELL - camy
            if -8 < x < SCREEN and -8 < y < SCREEN:
                blit(frame, x, y, pond_art(g.beat % 4))

        # seal slabs: joined into gates; the colour just lit crumbles away over the three frames
        live = {c for c in lv.seals if lv.seals[c] not in g.lit or (lv.seals[c] == g.just and k < 3)}
        for (wx, wy) in live:
            x, y = wx * CELL - camx, wy * CELL - camy
            if not (-4 < x < SCREEN and -4 < y < SCREEN):
                continue
            colour = lv.seals[(wx, wy)]
            same = lambda c: c in live and lv.seals[c] == colour
            tile = seal_tile(SEAL_HUE[colour], not same((wx, wy - 1)), not same((wx, wy + 1)),
                             not same((wx - 1, wy)))
            if colour == g.just and k < 3:
                drop = 30 if k == 1 else 65
                for ty in range(CELL):
                    for tx in range(CELL):
                        if _hash(wx * CELL + tx, wy * CELL + ty, 5) % 100 < drop:
                            tile[ty, tx] = GROUND_HUE
            blit(frame, x, y, tile)

        # the shrine braziers: identical to look at, lit ones throw a white flame that flares as it is lit
        for i, (wx, wy) in enumerate(GROUND.shrines):
            x, y = wx * CELL - camx, wy * CELL - camy
            if not (-8 < x < SCREEN and -8 < y + 4 < SCREEN + 8):
                continue
            size = 0
            if i in g.lit:
                size = (1, 3, 4)[k - 1] if (i == g.just and k < 3) else 4
            blit(frame, x, y - 4, brazier(size, g.beat, PLATE_OFF))

        # the sanctum: a great arched door in the wall and a stair up to it
        sx, sy = GROUND.sanctum
        x, y = sx * CELL - camx, sy * CELL - camy
        blit(frame, x - CELL, y + CELL, ARCH if (g.beat // 2) % 2 == 0 else ARCH_B)
        blit(frame, x - 2, y, PAD if g.beat % 2 == 0 else PAD_B)

        for i, q in enumerate(lv.props):
            x, y = q["pos"][0] * CELL - camx, q["pos"][1] * CELL - camy
            if -4 < x < SCREEN and -4 < y < SCREEN:
                blit(frame, x, y, flower(q["hue"], GROUND_HUE if q["hue"] == 0 else 0,
                                         (g.beat + i) % 4 < 2))

        # creatures, back to front so a lower one stands in front of a higher one
        drawn = []
        for f in g.foes:
            fx = self._lerp(f["px"], f["x"], k) - camx
            fy = self._lerp(f["py"], f["y"], k) - camy
            heading = (f["dx"], f["dy"]) if not f["back"] else (-f["dx"], -f["dy"])
            drawn.append((fy, imp(heading, f["t"] + k // 2), fx - 2, fy - 3))
        if g.hit and k < 3 and g.bump is not None:
            half = (g.bump[0] - g.prev_x, g.bump[1] - g.prev_y)
            px = g.prev_x * CELL + int(round(half[0] * CELL * k / 6)) - camx
            py = g.prev_y * CELL + int(round(half[1] * CELL * k / 6)) - camy
        else:
            px = self._lerp(g.prev_x, g.x, k) - camx
            py = self._lerp(g.prev_y, g.y, k) - camy
        drawn.append((py, pilgrim(g.face, g.beat + k // 2), px - 1, py - 3))
        for _, spr, x, y in sorted(drawn, key=lambda d: d[0]):
            blit(frame, x, y, spr)

        if g.hit and k < 3 and g.bump is not None:
            burst(frame, g.bump[0] * CELL + 2 - camx, g.bump[1] * CELL + 2 - camy, k + 1, FOE_BODY)

        if g.flash:                                          # the sanctum door flares, sparks rise
            r = 2 * (g.FLASH_FRAMES + 1 - g.flash)
            burst(frame, x_of(sx, camx), x_of(sy, camy), r, YEL if g.flash % 2 else LBL)

        if g.hit:
            frame[0, :] = FOE_BODY
            frame[SCREEN - 1, :] = FOE_BODY
            frame[:, 0] = FOE_BODY
            frame[:, SCREEN - 1] = FOE_BODY
        return frame


def x_of(cell_coord: int, cam_px: int) -> int:
    """Screen pixel of the middle of a cell."""
    return cell_coord * CELL + CELL // 2 - cam_px


class Se01(ARCBaseGame):

    FLASH_FRAMES = 5

    def __init__(self) -> None:
        self.arrangement = ARRANGEMENTS[0]
        self.cam_x = self.cam_y = 0
        self.x, self.y = GROUND.start
        self.lit: set = set()
        self.anchor = GROUND.start
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
        super().__init__(game_id="se01", levels=build_levels(),
                         available_actions=[1, 2, 3, 4], camera=camera)
        self._enter(0)

    def _enter(self, index: int) -> None:
        lv = self.arrangement = ARRANGEMENTS[index]
        self.x, self.y = GROUND.start
        self.lit = set()
        self.anchor = GROUND.start
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
        self.cam_y = max(0, min(max(0, GROUND.h - VIEW), self.y - VIEW // 2))
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

    def _send_back(self) -> None:
        self.x, self.y = self.anchor
        self.hit = 1
        self._follow()

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

        self.face = delta
        self.prev_x, self.prev_y = self.x, self.y
        self.prev_cam = (self.cam_x, self.cam_y)
        for f in self.foes:
            f["px"], f["py"] = f["x"], f["y"]

        nx, ny = self.x + delta[0], self.y + delta[1]
        if GROUND.thorn(nx, ny):
            self.bump = (nx, ny)
            self._send_back()
        elif self.passable(nx, ny):
            self.x, self.y = nx, ny
            if (nx, ny) in GROUND.shrines:
                i = GROUND.shrines.index((nx, ny))
                if i not in self.lit:
                    self.just = i
                self.lit.add(i)
                self.anchor = (nx, ny)
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
            self._send_back()
        self._follow()
        self._sync()
        self.tick, self.tail = 1, 2                    # play the slide: this frame, then two more
