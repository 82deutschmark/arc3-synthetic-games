# Author: Claude Sonnet 5.5
# Date: 07-November-2026
# PURPOSE: kt02 redraws kt01 (engine id g036, the cord on the lattice of slats) with far richer art. The RULES ARE UNCHANGED:
#   same ten levels in the same order, same slat layouts, start and finish eyelets, marked crossings and two-pass order,
#   same inputs (the four directions, ACTION5 to pull, ACTION7 to take the cord back one cell), the same safe take-back,
#   the same once-decided pull (a good pull moves on, a wrong pull ends the run as GAME_OVER). The rule code and the
#   level data below are kt01's, copied across untouched. What is new is only the picture: every level is a different
#   sewing-table cloth (its own weave, hem and palette) with its own slat colours, scattered props with faces (yarn
#   balls, thimbles, buttons, mushrooms, butterflies, moons, clouds, stars), a little creature that walks the top margin,
#   a thread rack, a head with several faces, sparkles round the finish when a pull holds, and a red, dimmed, wilted
#   "run over" look with a sad head when a pull fails. Everything on screen is a named engine sprite on a layer; nothing is
#   painted onto the finished frame, and no letters or digits are drawn anywhere.
# SRP/DRY check: Pass -- rules (try_step, failed_marks, build_board, the slide helpers) are kt01's, copied verbatim; the art
#   is pixel data and small builders that only read the game state; the game class only wires state to sprites. kt01 is not
#   edited and nothing is imported from it.
# CHANGELOG: 07-Nov-2026 (Claude Sonnet 5.5) -- first version of kt02: a full redraw of kt01 for the Boss's "really improved
#   art" pass. Per-level cloth, slats, props and creatures; faces on the head and the props; win sparkle; drawn loss look.
#   07-Nov-2026 pass 3 (Claude Sonnet 5.5) -- variety and life: six-pixel head overhanging its cell; twelve-pixel hero creatures
#   with faces; per-level trim, shimmer on the cloth, ambient drifters (petals, fireflies, hearts, birds, bubbles, embers,
#   comet); a second walker on the bottom margin; calmer gingham and plaid; level-clear ribbon shower and prop hop;
#   props and walkers go dim with tears on a lost run; spools shine. Rules untouched.
#   07-Nov-2026 pass 4 (Claude Sonnet 5.5) -- polish: calmer trims (dots, dashes) on levels 4, 6 and 8 in place of the loud
#   flag and ric-rac; bigger streamer scraps in the level-clear shower; unused code removed. Rules untouched.

import math

import numpy as np


from arcengine import (
    ARCBaseGame,
    BlockingMode,
    Camera,
    GameAction,
    InteractionMode,
    Level,
    Sprite,
)


# ── the sixteen ARC colours by name (1 to 4 are greys and are never used for art) ──
WHT, BLK, MAG, PNK, RED, BLU, LBL, YEL, ORG, MAR, GRN, PUR = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15

# ── rule-carrying colours (kt01's, so the marks and the cord read exactly as before) ──
RIM = BLK          # black: slat rim, start eyelet, eyes
UNDER = BLK        # black: a strand gone into the groove at a crossing
JUNCTION = YEL     # a crossing that asks for nothing (no level carries one)
WANT_H = BLU       # blue: the across strand must end on top
WANT_V = WHT       # white: the up-and-down strand must end on top
CORD = LBL         # light blue strand
PLAYER = PUR       # purple head
END = PUR          # purple finish eyelet; the cord's colour on a good pull
START = RIM
PETAL_TURN = WHT   # the one corner-flower petal that turns


# ── the parent's slide helpers, unchanged ──────────────────────────────────────

def begin_translation(game, names=(), position=None, repaint=None, limit=8):
    game._translation_path = None
    sprites = {s.name: (s.x, s.y) for s in game.current_level.get_sprites()
               if any(s.name == n or (n.endswith('*') and s.name.startswith(n[:-1]))
                      for n in names)}
    game._translation_capture = (game.current_level, sprites,
        (game.camera.x, game.camera.y), position, position() if position else None,
        repaint, limit)

def translation_position(game, position):
    return getattr(game, '_translation_point', None) or position

def advance_translation(game):
    motion = getattr(game, '_translation_motion', None)
    if motion is None:
        return False
    motion['frame'] += 1
    t = motion['frame'] / motion['count']
    def lerp(a, b):
        return tuple(round(x + (y - x) * t) for x, y in zip(a, b))
    for sprite, start, end in motion['sprites']:
        sprite.set_position(*(motion['path'][motion['frame']-1] if motion['path'] else lerp(start, end)))
    game.camera.x, game.camera.y = lerp(motion['camera'][0], motion['camera'][1])
    if motion['point'] is not None:
        game._translation_point = lerp(*motion['point'])
    if motion['repaint'] is not None:
        motion['repaint']()
    if motion['frame'] == motion['count']:
        game._translation_motion = None
        game._translation_point = None
        if motion['complete']:
            game.complete_action()
    return True

def finish_translation(game, complete=True):
    capture = getattr(game, '_translation_capture', None)
    game._translation_capture = None
    if capture is None or capture[0] is not game.current_level or game._next_level:
        if complete:
            game.complete_action()
        return
    level, previous, camera, position, point, repaint, limit = capture
    sprites = []
    distances = []
    path = getattr(game, "_translation_path", None)
    for sprite in level.get_sprites():
        if sprite.name not in previous:
            continue
        start, end = previous[sprite.name], (sprite.x, sprite.y)
        distance = max(abs(start[0] - end[0]), abs(start[1] - end[1]))
        if distance or path:
            sprites.append((sprite, start, end))
            distances.append(distance)
    points = (point, position()) if position else None
    if points:
        distances.append(max(abs(a-b) for a,b in zip(*points)))
    count = len(path) if path else max(distances, default=0)
    if count < 2 or (not path and count > limit):
        if complete:
            game.complete_action()
        return
    game._translation_motion = dict(frame=0, count=count, sprites=sprites,
        camera=(camera, (game.camera.x, game.camera.y)), point=points, repaint=repaint,
        complete=complete, path=path)
    advance_translation(game)

def clear_translation(game):
    game._translation_path = None
    game._translation_capture = None
    game._translation_motion = None
    game._translation_point = None


# ── refined level data; the parent's cord and crossing rules below are unchanged ──

N = 16
CELL = 4
LO, HI = 1, N - 2

UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)
DIRS = (UP, DOWN, LEFT, RIGHT)

LEVELS_SPEC = [{'cols': [],
  'rows': [],
  'cuts': [],
  'start': (3, 4),
  'end': (4, 9),
  'marks': {},
  'undos': 4,
  'track': [(3, 4),
            (4, 4),
            (5, 4),
            (6, 4),
            (7, 4),
            (8, 4),
            (9, 4),
            (7, 5),
            (7, 6),
            (7, 7),
            (6, 7),
            (5, 7),
            (4, 7),
            (4, 8),
            (4, 9)]},
 {'cols': [5],
  'rows': [5],
  'cuts': [],
  'start': (2, 12),
  'end': (12, 2),
  'marks': {(5, 5): 'v'},
  'undos': 4,
  'track': [(2, 2),
            (2, 3),
            (2, 4),
            (2, 5),
            (2, 6),
            (2, 7),
            (2, 8),
            (2, 9),
            (2, 10),
            (2, 11),
            (2, 12),
            (3, 2),
            (3, 5),
            (3, 11),
            (4, 2),
            (4, 5),
            (4, 11),
            (5, 2),
            (5, 3),
            (5, 4),
            (5, 5),
            (5, 6),
            (5, 7),
            (5, 8),
            (5, 9),
            (5, 10),
            (5, 11),
            (6, 2),
            (6, 5),
            (6, 11),
            (7, 2),
            (7, 5),
            (7, 11),
            (8, 2),
            (8, 5),
            (8, 11),
            (9, 2),
            (9, 5),
            (9, 11),
            (10, 2),
            (10, 5),
            (10, 11),
            (11, 2),
            (11, 3),
            (11, 4),
            (11, 5),
            (11, 6),
            (11, 7),
            (11, 8),
            (11, 9),
            (11, 10),
            (11, 11),
            (12, 2),
            (12, 5),
            (13, 5)]},
 {'cols': [6],
  'rows': [6, 10],
  'cuts': [],
  'start': (2, 3),
  'end': (6, 11),
  'marks': {(6, 6): 'v'},
  'crossings': [(6, 6)],
  'undos': 4,
  'track': [(2, 3),
            (2, 4),
            (2, 5),
            (2, 6),
            (2, 7),
            (2, 8),
            (2, 9),
            (2, 10),
            (2, 11),
            (2, 12),
            (3, 3),
            (3, 6),
            (3, 10),
            (3, 12),
            (4, 3),
            (4, 6),
            (4, 10),
            (4, 12),
            (5, 3),
            (5, 6),
            (5, 10),
            (5, 12),
            (6, 3),
            (6, 4),
            (6, 5),
            (6, 6),
            (6, 7),
            (6, 8),
            (6, 9),
            (6, 10),
            (6, 11),
            (6, 12),
            (7, 3),
            (7, 6),
            (7, 10),
            (7, 12),
            (8, 3),
            (8, 6),
            (8, 10),
            (8, 12),
            (9, 3),
            (9, 6),
            (9, 10),
            (9, 12),
            (10, 3),
            (10, 6),
            (10, 10),
            (10, 12),
            (11, 3),
            (11, 6),
            (11, 10),
            (11, 12),
            (12, 3),
            (12, 4),
            (12, 5),
            (12, 6),
            (12, 7),
            (12, 8),
            (12, 9),
            (12, 10),
            (12, 11),
            (12, 12)]},
 {'cols': [9],
  'rows': [9],
  'cuts': [],
  'start': (1, 2),
  'end': (13, 13),
  'marks': {(9, 9): 'h'},
  'undos': 4,
  'track': [(1, 2),
            (1, 3),
            (1, 4),
            (1, 5),
            (1, 6),
            (1, 7),
            (1, 8),
            (1, 9),
            (1, 10),
            (1, 11),
            (1, 12),
            (1, 13),
            (2, 2),
            (2, 9),
            (2, 13),
            (3, 2),
            (3, 9),
            (3, 13),
            (4, 2),
            (4, 9),
            (4, 13),
            (5, 2),
            (5, 9),
            (5, 13),
            (5, 14),
            (5, 15),
            (6, 2),
            (6, 9),
            (6, 13),
            (7, 2),
            (7, 9),
            (7, 13),
            (8, 2),
            (8, 9),
            (8, 13),
            (9, 2),
            (9, 3),
            (9, 4),
            (9, 5),
            (9, 6),
            (9, 7),
            (9, 8),
            (9, 9),
            (9, 10),
            (9, 11),
            (9, 12),
            (9, 13),
            (10, 2),
            (10, 9),
            (10, 13),
            (11, 2),
            (11, 9),
            (11, 13),
            (12, 2),
            (12, 9),
            (12, 13),
            (13, 2),
            (13, 3),
            (13, 4),
            (13, 5),
            (13, 6),
            (13, 7),
            (13, 8),
            (13, 9),
            (13, 10),
            (13, 11),
            (13, 12),
            (13, 13)]},
 {'cols': [4, 10],
  'crossings': [(4, 5), (10, 10)],
  'cuts': [],
  'end': (10, 6),
  'marks': {(4, 5): 'h', (10, 10): 'v'},
  'rows': [5, 10],
  'start': (1, 1),
  'track': [(1, 1),
            (1, 2),
            (1, 3),
            (1, 4),
            (1, 5),
            (1, 6),
            (1, 7),
            (1, 8),
            (1, 9),
            (1, 10),
            (1, 11),
            (1, 12),
            (1, 13),
            (1, 14),
            (2, 1),
            (2, 5),
            (2, 10),
            (2, 14),
            (3, 1),
            (3, 5),
            (3, 10),
            (3, 14),
            (4, 1),
            (4, 2),
            (4, 3),
            (4, 4),
            (4, 5),
            (4, 6),
            (4, 7),
            (4, 8),
            (4, 9),
            (4, 10),
            (4, 11),
            (4, 12),
            (4, 13),
            (4, 14),
            (5, 1),
            (5, 5),
            (5, 10),
            (5, 14),
            (6, 1),
            (6, 5),
            (6, 10),
            (6, 14),
            (7, 1),
            (7, 5),
            (7, 10),
            (7, 14),
            (8, 1),
            (8, 5),
            (8, 10),
            (8, 14),
            (9, 1),
            (9, 5),
            (9, 10),
            (9, 14),
            (10, 1),
            (10, 2),
            (10, 3),
            (10, 4),
            (10, 5),
            (10, 6),
            (10, 7),
            (10, 8),
            (10, 9),
            (10, 10),
            (10, 11),
            (10, 12),
            (10, 13),
            (10, 14),
            (11, 1),
            (11, 5),
            (11, 10),
            (11, 14),
            (12, 1),
            (12, 5),
            (12, 10),
            (12, 14),
            (13, 1),
            (13, 5),
            (13, 10),
            (13, 14),
            (14, 1),
            (14, 2),
            (14, 3),
            (14, 4),
            (14, 5),
            (14, 6),
            (14, 7),
            (14, 8),
            (14, 9),
            (14, 10),
            (14, 11),
            (14, 12),
            (14, 13),
            (14, 14)],
  'undos': 4},
 {'cols': [4, 8, 12],
  'crossings': [(4, 5), (12, 5), (8, 11)],
  'cuts': [],
  'end': (8, 6),
  'marks': {(4, 5): 'h', (8, 11): 'v', (12, 5): 'h'},
  'rows': [5, 11],
  'start': (1, 1),
  'track': [(1, 1),
            (1, 2),
            (1, 3),
            (1, 4),
            (1, 5),
            (1, 6),
            (1, 7),
            (1, 8),
            (1, 9),
            (1, 10),
            (1, 11),
            (1, 12),
            (1, 13),
            (1, 14),
            (2, 1),
            (2, 5),
            (2, 11),
            (2, 14),
            (3, 1),
            (3, 5),
            (3, 11),
            (3, 14),
            (4, 1),
            (4, 2),
            (4, 3),
            (4, 4),
            (4, 5),
            (4, 6),
            (4, 7),
            (4, 8),
            (4, 9),
            (4, 10),
            (4, 11),
            (4, 12),
            (4, 13),
            (4, 14),
            (5, 1),
            (5, 5),
            (5, 11),
            (5, 14),
            (6, 1),
            (6, 5),
            (6, 11),
            (6, 14),
            (7, 1),
            (7, 5),
            (7, 11),
            (7, 14),
            (8, 1),
            (8, 2),
            (8, 3),
            (8, 4),
            (8, 5),
            (8, 6),
            (8, 7),
            (8, 8),
            (8, 9),
            (8, 10),
            (8, 11),
            (8, 12),
            (8, 13),
            (8, 14),
            (9, 1),
            (9, 5),
            (9, 11),
            (9, 14),
            (10, 1),
            (10, 5),
            (10, 11),
            (10, 14),
            (11, 1),
            (11, 5),
            (11, 11),
            (11, 14),
            (12, 1),
            (12, 2),
            (12, 3),
            (12, 4),
            (12, 5),
            (12, 6),
            (12, 7),
            (12, 8),
            (12, 9),
            (12, 10),
            (12, 11),
            (12, 12),
            (12, 13),
            (12, 14),
            (13, 1),
            (13, 5),
            (13, 11),
            (13, 14),
            (14, 1),
            (14, 2),
            (14, 3),
            (14, 4),
            (14, 5),
            (14, 6),
            (14, 7),
            (14, 8),
            (14, 9),
            (14, 10),
            (14, 11),
            (14, 12),
            (14, 13),
            (14, 14)],
  'undos': 4},
 {'cols': [4, 8, 12],
  'crossings': [(4, 4), (8, 4), (12, 4), (8, 12)],
  'cuts': [],
  'end': (12, 13),
  'marks': {(4, 4): 'h', (8, 4): 'h', (8, 12): 'v', (12, 4): 'h'},
  'rows': [4, 8, 12],
  'start': (1, 1),
  'track': [(1, 1),
            (1, 2),
            (1, 3),
            (1, 4),
            (1, 5),
            (1, 6),
            (1, 7),
            (1, 8),
            (1, 9),
            (1, 10),
            (1, 11),
            (1, 12),
            (1, 13),
            (1, 14),
            (2, 1),
            (2, 4),
            (2, 8),
            (2, 12),
            (2, 14),
            (3, 1),
            (3, 4),
            (3, 8),
            (3, 12),
            (3, 14),
            (4, 1),
            (4, 2),
            (4, 3),
            (4, 4),
            (4, 5),
            (4, 6),
            (4, 7),
            (4, 8),
            (4, 9),
            (4, 10),
            (4, 11),
            (4, 12),
            (4, 13),
            (4, 14),
            (5, 1),
            (5, 4),
            (5, 8),
            (5, 12),
            (5, 14),
            (6, 1),
            (6, 4),
            (6, 8),
            (6, 12),
            (6, 14),
            (7, 1),
            (7, 4),
            (7, 8),
            (7, 12),
            (7, 14),
            (8, 1),
            (8, 2),
            (8, 3),
            (8, 4),
            (8, 5),
            (8, 6),
            (8, 7),
            (8, 8),
            (8, 9),
            (8, 10),
            (8, 11),
            (8, 12),
            (8, 13),
            (8, 14),
            (9, 1),
            (9, 4),
            (9, 8),
            (9, 12),
            (9, 14),
            (10, 1),
            (10, 4),
            (10, 8),
            (10, 12),
            (10, 14),
            (11, 1),
            (11, 4),
            (11, 8),
            (11, 12),
            (11, 14),
            (12, 1),
            (12, 2),
            (12, 3),
            (12, 4),
            (12, 5),
            (12, 6),
            (12, 7),
            (12, 8),
            (12, 9),
            (12, 10),
            (12, 11),
            (12, 12),
            (12, 13),
            (12, 14),
            (13, 1),
            (13, 4),
            (13, 8),
            (13, 12),
            (13, 14),
            (14, 1),
            (14, 2),
            (14, 3),
            (14, 4),
            (14, 5),
            (14, 6),
            (14, 7),
            (14, 8),
            (14, 9),
            (14, 10),
            (14, 11),
            (14, 12),
            (14, 13),
            (14, 14)],
  'undos': 4},
 {'cols': [4, 12],
  'rows': [4, 12],
  'cuts': [],
  'start': (14, 14),
  'end': (12, 14),
  'marks': {(4, 4): 'h', (4, 12): 'v', (12, 4): 'v', (12, 12): 'v'},
  'undos': 3},
 {'cols': [4, 8, 12],
  'crossings': [(4, 4), (8, 8), (12, 12)],
  'cuts': [],
  'end': (14, 3),
  'marks': {(4, 4): 'h', (8, 8): 'v', (12, 12): 'h'},
  'rows': [4, 8, 12],
  'start': (1, 1),
  'track': [(1, 1),
            (1, 2),
            (1, 3),
            (1, 4),
            (1, 5),
            (1, 6),
            (1, 7),
            (1, 8),
            (1, 9),
            (1, 10),
            (1, 11),
            (1, 12),
            (1, 13),
            (1, 14),
            (2, 1),
            (2, 4),
            (2, 8),
            (2, 12),
            (2, 14),
            (3, 1),
            (3, 4),
            (3, 8),
            (3, 12),
            (3, 14),
            (4, 1),
            (4, 2),
            (4, 3),
            (4, 4),
            (4, 5),
            (4, 6),
            (4, 7),
            (4, 8),
            (4, 9),
            (4, 10),
            (4, 11),
            (4, 12),
            (4, 13),
            (4, 14),
            (5, 1),
            (5, 4),
            (5, 8),
            (5, 12),
            (5, 14),
            (6, 1),
            (6, 4),
            (6, 8),
            (6, 12),
            (6, 14),
            (7, 1),
            (7, 4),
            (7, 8),
            (7, 12),
            (7, 14),
            (8, 1),
            (8, 2),
            (8, 3),
            (8, 4),
            (8, 5),
            (8, 6),
            (8, 7),
            (8, 8),
            (8, 9),
            (8, 10),
            (8, 11),
            (8, 12),
            (8, 13),
            (8, 14),
            (9, 1),
            (9, 4),
            (9, 8),
            (9, 12),
            (9, 14),
            (10, 1),
            (10, 4),
            (10, 8),
            (10, 12),
            (10, 14),
            (11, 1),
            (11, 4),
            (11, 8),
            (11, 12),
            (11, 14),
            (12, 1),
            (12, 2),
            (12, 3),
            (12, 4),
            (12, 5),
            (12, 6),
            (12, 7),
            (12, 8),
            (12, 9),
            (12, 10),
            (12, 11),
            (12, 12),
            (12, 13),
            (12, 14),
            (13, 1),
            (13, 4),
            (13, 8),
            (13, 12),
            (13, 14),
            (14, 1),
            (14, 2),
            (14, 3),
            (14, 4),
            (14, 5),
            (14, 6),
            (14, 7),
            (14, 8),
            (14, 9),
            (14, 10),
            (14, 11),
            (14, 12),
            (14, 13),
            (14, 14)],
  'undos': 4},
 {'cols': [3, 6, 9, 12],
  'crossings': [(3, 4), (6, 4), (9, 4), (12, 4), (6, 12)],
  'cuts': [],
  'end': (14, 13),
  'marks': {(3, 4): 'h', (6, 4): 'h', (6, 12): 'v', (9, 4): 'h', (12, 4): 'v'},
  'rows': [4, 8, 12],
  'start': (1, 1),
  'track': [(1, 1),
            (1, 2),
            (1, 3),
            (1, 4),
            (1, 5),
            (1, 6),
            (1, 7),
            (1, 8),
            (1, 9),
            (1, 10),
            (1, 11),
            (1, 12),
            (1, 13),
            (1, 14),
            (2, 1),
            (2, 4),
            (2, 8),
            (2, 12),
            (2, 14),
            (3, 1),
            (3, 2),
            (3, 3),
            (3, 4),
            (3, 5),
            (3, 6),
            (3, 7),
            (3, 8),
            (3, 9),
            (3, 10),
            (3, 11),
            (3, 12),
            (3, 13),
            (3, 14),
            (4, 1),
            (4, 4),
            (4, 8),
            (4, 12),
            (4, 14),
            (5, 1),
            (5, 4),
            (5, 8),
            (5, 12),
            (5, 14),
            (6, 1),
            (6, 2),
            (6, 3),
            (6, 4),
            (6, 5),
            (6, 6),
            (6, 7),
            (6, 8),
            (6, 9),
            (6, 10),
            (6, 11),
            (6, 12),
            (6, 13),
            (6, 14),
            (7, 1),
            (7, 4),
            (7, 8),
            (7, 12),
            (7, 14),
            (8, 1),
            (8, 4),
            (8, 8),
            (8, 12),
            (8, 14),
            (9, 1),
            (9, 2),
            (9, 3),
            (9, 4),
            (9, 5),
            (9, 6),
            (9, 7),
            (9, 8),
            (9, 9),
            (9, 10),
            (9, 11),
            (9, 12),
            (9, 13),
            (9, 14),
            (10, 1),
            (10, 4),
            (10, 8),
            (10, 12),
            (10, 14),
            (11, 1),
            (11, 4),
            (11, 8),
            (11, 12),
            (11, 14),
            (12, 1),
            (12, 2),
            (12, 3),
            (12, 4),
            (12, 5),
            (12, 6),
            (12, 7),
            (12, 8),
            (12, 9),
            (12, 10),
            (12, 11),
            (12, 12),
            (12, 13),
            (12, 14),
            (13, 1),
            (13, 4),
            (13, 8),
            (13, 12),
            (13, 14),
            (14, 1),
            (14, 2),
            (14, 3),
            (14, 4),
            (14, 5),
            (14, 6),
            (14, 7),
            (14, 8),
            (14, 9),
            (14, 10),
            (14, 11),
            (14, 12),
            (14, 13),
            (14, 14)],
  'undos': 4}]

DECOR_CELLS = ()


def build_board(spec: dict) -> tuple[dict, dict]:
    track: dict[tuple[int, int], bool] = {}
    for i in range(LO, HI + 1):
        for cell in ((i, LO), (i, HI), (LO, i), (HI, i)):
            track[cell] = True
    for x in spec["cols"]:
        for y in range(LO, HI + 1):
            track[(x, y)] = True
    for y in spec["rows"]:
        for x in range(LO, HI + 1):
            track[(x, y)] = True
    if "track" in spec:
        track = {tuple(c): True for c in spec["track"]}
    for cell in spec["cuts"]:
        track.pop(tuple(cell), None)

    junctions: dict[tuple[int, int], str | None] = {}
    for x in spec["cols"]:
        for y in spec["rows"]:
            if (x, y) in track:
                junctions[(x, y)] = spec["marks"].get((x, y))
    if "crossings" in spec:
        # An unmarked open meeting of slats is ordinary track: it may turn but cannot be reused.
        # Only the visibly railed crossings have the established straight-through/two-pass rule.
        junctions = {tuple(cell): spec["marks"].get(tuple(cell)) for cell in spec["crossings"]}
    return track, junctions


def axis_of(direction: tuple[int, int]) -> str:
    return "H" if direction[1] == 0 else "V"


def initial_state(spec: dict) -> dict:
    start = tuple(spec["start"])
    return {"pos": start, "spent": {start}, "cross": {}, "arms": {start: set()}}


def clone_state(state: dict) -> dict:
    return {
        "pos": state["pos"],
        "spent": set(state["spent"]),
        "cross": dict(state["cross"]),
        "arms": {k: set(v) for k, v in state["arms"].items()},
    }


def try_step(state: dict, direction: tuple[int, int], track: dict, junctions: dict):
    dx, dy = direction
    axis = axis_of(direction)
    passed: list[tuple[int, int]] = []
    cur = (state["pos"][0] + dx, state["pos"][1] + dy)
    while True:
        if cur not in track:
            return None
        if cur not in junctions:
            break
        if axis in state["cross"].get(cur, ()) or cur in passed:
            return None
        passed.append(cur)
        cur = (cur[0] + dx, cur[1] + dy)
    if cur in state["spent"]:
        return None

    out = clone_state(state)
    back = (-dx, -dy)
    out["arms"].setdefault(state["pos"], set()).add(direction)
    for cell in passed:
        arms = out["arms"].setdefault(cell, set())
        arms.add(back)
        arms.add(direction)
        out["cross"][cell] = out["cross"].get(cell, ()) + (axis,)
    out["arms"].setdefault(cur, set()).add(back)
    out["spent"].add(cur)
    out["pos"] = cur
    return out


def failed_marks(state: dict, junctions: dict) -> list:
    bad = []
    for cell, mark in junctions.items():
        if mark is None:
            continue
        order = state["cross"].get(cell, ())
        if len(order) < 2 or order[1] != ("H" if mark == "h" else "V"):
            bad.append(cell)
    return bad


def knot_holds(state: dict, junctions: dict) -> bool:
    return not failed_marks(state, junctions)


def state_key(state: dict) -> tuple:
    return (state["pos"], frozenset(state["spent"]),
            tuple(sorted(state["cross"].items())))



# ══════════════════════════════════════════════════════════════════════════════════════════════
# ART. Everything below only draws; it reads the state and never changes a rule.
# Text-row sprites use one letter per colour; '.' is transparent. Letters with a fixed colour are listed in INK;
# a, b, c are passed in per sprite so one design can be recoloured for any level.
# ══════════════════════════════════════════════════════════════════════════════════════════════

INK = {'k': BLK, 'w': WHT, 'y': YEL, 'r': RED, 'o': ORG, 'g': GRN, 'p': PNK, 'm': MAG, 'u': PUR, 'l': LBL,
       'n': MAR, 'e': BLU}


def paint(rows, **ink) -> list[list[int]]:
    """Text rows to a pixel grid. Extra keyword letters (a, b, c ...) recolour the design."""
    table = dict(INK)
    table.update(ink)
    return [[-1 if ch == '.' else table[ch] for ch in row] for row in rows]


def frames_of(designs, **ink) -> list:
    return [np.array(paint(rows, **ink), dtype=np.int8) for rows in designs]


def shifted(rows, dx: int, top: int = 99) -> tuple:
    """Slide the first `top` rows sideways by dx (used for sway); lower rows stay put."""
    out = []
    for i, row in enumerate(rows):
        if i < top and dx:
            w = len(row)
            row = ('.' * dx + row)[:w] if dx > 0 else (row[-dx:] + '.' * -dx)
        out.append(row)
    return tuple(out)


def outlined(grid: np.ndarray, colour: int = BLK) -> np.ndarray:
    """Add a one-pixel outline round every filled pixel, inside the same box (leave a border when you draw)."""
    h, w = grid.shape
    out = grid.copy()
    for y in range(h):
        for x in range(w):
            if grid[y, x] != -1:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and grid[ny, nx] != -1:
                    out[y, x] = colour
                    break
    return out


# ── the head: a round purple tip with a face; the way it last moved decides where it looks ──
_HEAD = {
    # Six by six, drawn one pixel past its cell on every side (see _place_head) so the knob reads bigger than the 4-pixel
    # lattice while the cord itself stays four wide. P body, h pink cheek/shine, w white of the eye, k outline and pupil.
    "front": (".kkkk.", "kPhPPk", "kwkkwk", "khPPhk", "kPkkPk", ".kkkk."),
    "up":    (".kkkk.", "kwkkwk", "kPhPPk", "kPPPPk", "kPPPPk", ".kkkk."),
    "down":  (".kkkk.", "kPhPPk", "kPPPPk", "kwkkwk", "khkkhk", ".kkkk."),
    "left":  (".kkkk.", "kPhPPk", "kkwkwk", "khPPhk", "kPkkPk", ".kkkk."),
    "right": (".kkkk.", "kPhPPk", "kwkwkk", "khPPhk", "kPkkPk", ".kkkk."),
    "happy": (".kkkk.", "kPhPPk", "kkPPkk", "khPPhk", "kwwwwk", ".kkkk."),     # squinting grin: the pull held
    "sad":   (".kkkk.", "kPhPPk", "kwkkwk", "klPPlk", "kkPPkk", ".kkkk."),     # tears and a frown: the pull failed
    "blink": (".kkkk.", "kPhPPk", "kPPPPk", "khPPhk", "kPkkPk", ".kkkk."),     # eyes shut while it waits
}
FACING = {UP: "up", DOWN: "down", LEFT: "left", RIGHT: "right"}
HEAD_FRAMES = {face: np.array(paint(rows, P=PLAYER, h=PNK), dtype=np.int8) for face, rows in _HEAD.items()}


# ── slat tiles: a bevelled wooden strip with a black rim wherever it meets cloth ──
def _slat(cell, track, wood) -> list[list[int]]:
    """One wooden slat tile. An edge facing cloth gets a black rim, then a light line (top and left) or a shadow
    line (bottom and right) inside it, so a run of slats reads as one rounded rod. A corner where both sides face
    cloth is cut round; an inside corner whose diagonal is cloth is black. Only crossings keep plain body colour."""
    body, hi, shade = wood
    x, y = cell
    px = [[body] * CELL for _ in range(CELL)]
    up, down = (x, y - 1) in track, (x, y + 1) in track
    left, right = (x - 1, y) in track, (x + 1, y) in track
    for k in range(CELL):
        if not up:
            px[0][k], px[1][k] = RIM, hi
        if not down:
            px[CELL - 1][k], px[CELL - 2][k] = RIM, shade
        if not left:
            px[k][0], px[k][1] = RIM, hi
        if not right:
            px[k][CELL - 1], px[k][CELL - 2] = RIM, shade
    for j, i, dx, dy in ((0, 0, -1, -1), (0, 3, 1, -1), (3, 0, -1, 1), (3, 3, 1, 1)):
        side_x, side_y = (x + dx, y) in track, (x, y + dy) in track
        if not side_x and not side_y:
            px[j][i] = -1
        elif side_x and side_y and (x + dx, y + dy) not in track:
            px[j][i] = RIM
    if up and down and left and right:                  # a crossing: a bright rivet and its shadow
        px[1][1], px[2][2] = hi, shade
    elif (x * 5 + y * 3) % 4 == 0:                      # a grain fleck on some plain runs, never on the rim
        gy, gx = 1 + (x + y) % 2, 1 + (x * 2 + y) % 2
        if px[gy][gx] == body:
            px[gy][gx] = shade
    return px


def _crossing(mark: str | None) -> list[list[int]]:
    # kt01's two bars per marked crossing, along the strand that must end on top.
    colour = JUNCTION if mark is None else WANT_H if mark == 'h' else WANT_V
    px = [[-1] * CELL for _ in range(CELL)]
    if mark == 'h':
        px[0] = [colour] * CELL
        px[3] = [colour] * CELL
    else:
        for row in px:
            row[0] = row[3] = colour
    return px


def _eyelet(colour: int) -> list[list[int]]:
    px = [[colour] * CELL for _ in range(CELL)]
    for y in range(1, CELL - 1):
        for x in range(1, CELL - 1):
            px[y][x] = -1
    return px


def _arm(px, direction, colour) -> None:
    # kt01's two-pixel arm toward one side of the cell.
    if direction == UP:
        rows, cols = (0, 1), (1, 2)
    elif direction == DOWN:
        rows, cols = (2, 3), (1, 2)
    elif direction == LEFT:
        rows, cols = (1, 2), (0, 1)
    else:
        rows, cols = (1, 2), (2, 3)
    for r in rows:
        for c in cols:
            px[r][c] = colour


def _cord_pixels(arms, order, colour) -> list[list[int]]:
    """The strand in one cell. At a crossing laid twice the first strand is drawn gone-under and
    the second over it, exactly kt01's pixel order."""
    px = [[-1] * CELL for _ in range(CELL)]
    if len(order) == 2:
        under_axis = order[0]
        for axis in (under_axis, order[1]):
            for direction in arms:
                if axis_of(direction) == axis:
                    _arm(px, direction, UNDER if axis == under_axis else colour)
    else:
        for direction in arms:
            _arm(px, direction, colour)
    return px


def _spool(thread: int, phase: int = 0) -> list[list[int]]:
    # A wooden spool wound with coloured thread: bench scenery in the right margin, it counts nothing. The shine slides
    # between two spots (phase 0 and 1) so the thread looks to be turning.
    shine = WHT if thread != WHT else YEL
    top = [RIM, shine if phase else thread, thread, RIM]
    low = [RIM, thread, thread if phase else shine, RIM]
    return [[ORG, YEL, YEL, ORG], top, low, [ORG, MAR, MAR, ORG]]


def _rack(count: int) -> list[list[int]]:
    """The wooden shelf the spools stand on: a shelf above the first spool and one under each, with the
    shelf board's light edge on top. Height 6*(count-1)+8 so it lines up with SPOOL_TOP and SPOOL_GAP."""
    height = 6 * (count - 1) + 8
    px = [[MAR] * CELL for _ in range(height)]
    shelves = [0] + [6 * i + 6 for i in range(count)]
    for s in shelves:
        for k in range(CELL):
            px[s][k], px[s + 1][k] = YEL, ORG
    for r in range(height):
        px[r][0] = RIM if px[r][0] == MAR else px[r][0]
    return px


def _daisy(phase: int, petal: int, wilted: bool = False) -> list[list[int]]:
    px = [[-1] * CELL for _ in range(CELL)]
    if wilted:                                          # a drooping flower: petals fallen, head bowed
        px[1][1], px[2][0], px[2][1], px[2][2], px[3][1] = MAR, MAR, ORG, MAR, GRN
        return px
    petals = ((0, 1), (1, 2), (2, 1), (1, 0))
    for k, (r, c) in enumerate(petals):
        px[r][c] = PETAL_TURN if k == phase % 4 else petal
    px[1][1] = ORG
    px[3][2] = GRN
    return px


def _hint_pixels() -> list[list[int]]:
    # Level two's wordless picture, kt01's exact pixels: a strand across, two dots, a bar.
    px = [[-1] * 10 for _ in range(18)]
    for r in (0, 1):
        px[r] = [CORD] * 10
    px[4][4] = YEL
    px[6][4] = px[6][5] = YEL
    for r in range(8, 18):
        px[r][4] = px[r][5] = WANT_V
    return px


def _tag() -> list[list[int]]:
    """A black felt label sewn under level two's picture, with a yellow and orange running stitch round the edge."""
    w, h = 13, 22
    px = [[BLK] * w for _ in range(h)]
    for i in range(w):
        px[0][i] = px[h - 1][i] = YEL if i % 2 == 0 else ORG
    for j in range(h):
        px[j][0] = px[j][w - 1] = YEL if j % 2 == 0 else ORG
    px[0][0] = px[0][w - 1] = px[h - 1][0] = px[h - 1][w - 1] = -1
    return px


SHOWER = 14
SHOWER_COLOURS = (YEL, PNK, ORG, GRN, WHT, MAG, LBL, RED)


def _scrap(colour: int, turned: bool) -> list[list[int]]:
    """A streamer of ribbon: three pixels wide and five tall with a pale highlight, or turned on its side as it tumbles."""
    if turned:
        return [[colour, colour, colour, colour, -1], [WHT, WHT, colour, colour, colour], [-1, colour, colour, colour, colour]]
    return [[-1, colour, colour], [colour, colour, -1], [colour, WHT, -1], [-1, colour, WHT], [colour, colour, -1]]


def _spark(colour: int, big: bool) -> list[list[int]]:
    if big:
        return [[-1, -1, colour, -1, -1], [-1, colour, WHT, colour, -1], [colour, WHT, WHT, WHT, colour],
                [-1, colour, WHT, colour, -1], [-1, -1, colour, -1, -1]]
    return [[-1, colour, -1], [colour, WHT, colour], [-1, colour, -1]]


# ── props: small scenes you could stand on a sewing table. Each builder returns animation frames. ──
def b_yarn(a, b):
    """A ball of yarn with a face; it blinks."""
    open_ = ("..kkkk..", ".kbaaak.", "kbaaaaak", "kakaakak", "kpaaaapk", "kaakkaak", ".kaaaak.", "..kkkk..")
    shut = ("..kkkk..", ".kbaaak.", "kbaaaaak", "kaaaaaak", "kpaaaapk", "kaakkaak", ".kaaaak.", "..kkkk..")
    return frames_of([open_, open_, shut], a=a, b=b)


def b_thimble(a, b):
    rows = ("........", "..kkkk..", ".kaaaak.", "kanaanak", "kaaaaaak", "kanaanak", "kbbbbbbk", ".kkkkkk.")
    wink = ("........", "..kkkk..", ".kaaaak.", "kaaanaak", "kanaaank", "kaaaaaak", "kbbbbbbk", ".kkkkkk.")
    return frames_of([rows, wink], a=a, b=b)


def b_button(a, b):
    rows = ("..kkkk..", ".kbaaak.", "kbaaaaak", "kaaaaaak", "kakaakak", "kaaaaaak", ".kaaaak.", "..kkkk..")
    thread = ("..kkkk..", ".kbaaak.", "kakaakak", "kaakkaak", "kakaakak", "kaaaaaak", ".kaaaak.", "..kkkk..")
    return frames_of([rows, thread], a=a, b=b)


def b_pincushion(a, b):
    rows = (".b...y..", ".w...w.b", ".w.b.w.w", ".kkkkkk.", "kaaaaaak", "kaaaabak", ".kkkkkk.", "........")
    glint = (".b...w..", ".w...w.b", ".w.b.w.w", ".kkkkkk.", "kaaaaaak", "kaaaabak", ".kkkkkk.", "........")
    return frames_of([rows, glint], a=a, b=b, y=YEL)


def b_mushroom(a, b):
    rows = ("..kkkk..", ".kawaak.", "kaaaawak", "kwaaaaak", "kkkkkkkk", ".kbkkbk.", ".kbbbbk.", "..kkkk..")
    return frames_of([rows], a=a, b=b)


def b_flower(a, b):
    """A flower with a face that sways on its stem."""
    head = ("..aaaa..", ".abbbba.", "abkbbkba", "abbkkbba", ".abbbba.", "..aaaa..", "...gg...", "..gggg..")
    return frames_of([head, shifted(head, 1, 6), head, shifted(head, -1, 6)], a=a, b=b)


def b_butterfly(a, b):
    open_ = ("aa....aa", "aaa..aaa", "abbkkbba", "aabkkbaa", ".aakkaa.", "..akka..", "...kk...", "........")
    folded = ("........", "..a..a..", "..aaaa..", ".abkkba.", ".abkkba.", "..akka..", "...kk...", "........")
    return frames_of([open_, folded], a=a, b=b)


def b_spoolbig(a, b):
    rows = ("kkkkkkkk", "kbbbbbbk", ".kaaaak.", ".kabaak.", ".kaaabk.", ".kabaak.", "kbbbbbbk", "kkkkkkkk")
    shift = ("kkkkkkkk", "kbbbbbbk", ".kaaaak.", ".kaabak.", ".kabaak.", ".kaaabk.", "kbbbbbbk", "kkkkkkkk")
    return frames_of([rows, shift], a=a, b=b)


def b_cloud(a, b):
    """A fat cloud with a face (12 by 8): used on the sky level; it drifts."""
    g = np.full((8, 12), -1, dtype=np.int8)
    for cx, cy, r in ((3.3, 4.3, 2.6), (6.0, 3.0, 3.0), (8.8, 4.3, 2.6)):
        for y in range(8):
            for x in range(12):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    g[y, x] = a
    g[5, 3:9] = a
    g = outlined(g)
    g[4, 4] = g[4, 7] = BLK
    g[5, 5] = g[5, 6] = BLK
    return [g]


def b_star(a, b):
    """A little star that twinkles: bright cross, then a dot."""
    cross = (".a..", "aaa.", ".a..", "....")
    dot = ("....", ".a..", "....", "....")
    return frames_of([cross, dot, cross, cross], a=a)


def b_flower4(a, b):
    rows = (".a..", "aba.", ".ag.", "..g.")
    sway = ("..a.", ".aba", "..ag", "..g.")
    return frames_of([rows, sway], a=a, b=b)


def b_heart(a, b):
    rows = ("a..a", "aaaa", ".aa.", "....")
    beat = ("a..a", "aaaa", "aaaa", ".aa.")
    return frames_of([rows, beat], a=a)


def b_bead(a, b):
    rows = (".aa.", "abaa", "aaaa", ".aa.")
    return frames_of([rows], a=a, b=WHT)


# ── pass 2 props: eight-by-eight creatures and objects, each with a face that blinks or wiggles ──
def _blink(rows, row, shut):
    """The same picture with one row swapped: the blink frame."""
    out = list(rows)
    out[row] = shut
    return tuple(out)


def b_moon(a, b):
    """A crescent moon cut from two discs, outlined, with a closed sleepy eye, a rosy cheek and a glint; it opens an eye now and then."""
    g = np.full((8, 8), -1, dtype=np.int8)
    for y in range(8):
        for x in range(8):
            if (x - 3.4) ** 2 + (y - 3.5) ** 2 <= 8.4 and (x - 5.6) ** 2 + (y - 2.7) ** 2 > 6.0:
                g[y, x] = a
    g = outlined(g)
    g[2, 3] = WHT                    # glint
    g[5, 2] = PNK                    # cheek
    shut, wide = g.copy(), g.copy()
    shut[3, 2] = shut[3, 3] = BLK    # a closed eye: a dash
    wide[3, 2], wide[4, 2] = BLK, BLK  # an open eye: two pixels down
    return [shut, shut, wide, shut]


def b_owl(a, b):
    r = ("k.kkkk.k", "kakaakak", "kwwkkwwk", "kwkwwkwk", "kaayyaak", "kabbbbak", ".kabbak.", "..kyyk..")
    s = _blink(_blink(r, 2, "kaaaaaak"), 3, "kakaakak")
    return frames_of([r, r, r, s], a=a, b=b)


def b_cat(a, b):
    r = ("kk....kk", "kbkkkkbk", "kaaaaaak", "kakaakak", "kaappaak", "kaakkaak", ".kaaaak.", "..kkkk..")
    return frames_of([r, r, _blink(r, 3, "kaaaaaak")], a=a, b=b)


def b_bunny(a, b):
    r = (".kk..kk.", "kbk..kbk", "kbk..kbk", ".kaaaak.", "kakaakak", "kaappaak", ".kaaaak.", "..kkkk..")
    return frames_of([r, r, r, _blink(r, 4, "kaaaaaak")], a=a, b=b)


def b_frog(a, b):
    r = (".kk..kk.", "kwwkkwwk", "kwkaakwk", "kaaaaaak", "kakkkkak", "kaaaaaak", "kbaaaabk", ".kk..kk.")
    s = _blink(_blink(r, 1, "kaakkaak"), 2, "kaaaaaak")
    return frames_of([r, r, r, s], a=a, b=b)


def b_penguin(a, b):
    r = ("..kkkk..", ".kaaaak.", "kakaakak", "kaaooaak", "kawwwwak", "kawwwwak", ".kawwak.", "..oo.oo.")
    return frames_of([r, r, _blink(r, 2, "kaaaaaak")], a=a, b=b)


def b_ghost(a, b):
    r = ("..kkkk..", ".kaaaak.", "kakaakak", "kakaakak", "kaakkaak", "kaaaaaak", "kaaaaaak", "kakkakak")
    s = ("..kkkk..", ".kaaaak.", "kaaaaaak", "kakaakak", "kaakkaak", "kaaaaaak", "kaaaaaak", "kkakkaka")
    return frames_of([r, r, s, r], a=a, b=b)


def b_bat(a, b):
    up = ("k......k", "kk.kk.kk", "kakkkkak", "kawkkwak", ".kaaaak.", "..kwwk..", "...kk...", "........")
    down = ("........", "k..kk..k", "kakkkkak", "kawkkwak", ".kaaaak.", "..kwwk..", "...kk...", "........")
    return frames_of([up, down], a=a, b=b)


def b_pumpkin(a, b):
    r = ("...gg...", ".kkggkk.", "kabaabak", "kakaakak", "kaaaaaak", "kakwwkak", ".kaaaak.", "..kkkk..")
    return frames_of([r, r, _blink(r, 3, "kaaaaaak")], a=a, b=b)


def b_apple(a, b):
    r = ("...kg...", ".kkkgkk.", "kawaaaak", "kwaaaaak", "kakaakak", "kaakkaak", ".kaaaak.", "..kkkk..")
    return frames_of([r, r, _blink(r, 4, "kaaaaaak")], a=a, b=b)


def b_cupcake(a, b):
    r = ("...rr...", "..kaak..", ".kaaaak.", "kakaakak", "kkkkkkkk", ".kbwbwk.", ".kbbbbk.", "..kkkk..")
    return frames_of([r, r, _blink(r, 3, "kaaaaaak")], a=a, b=b)


def b_icecream(a, b):
    r = ("..kkkk..", ".kwaaak.", "kakaakak", "kaappaak", "kkkkkkkk", ".kbkbbk.", "..kbbk..", "...kk...")
    return frames_of([r, r, _blink(r, 2, "kaaaaaak")], a=a, b=b)


def b_bell(a, b):
    r = ("...kk...", "..kaak..", ".kawaak.", ".kaaaak.", "kakaakak", "kaaaaaak", "kkkkkkkk", "..kbbk..")
    swing = _blink(r, 7, "...kbbk.")
    return frames_of([r, swing], a=a, b=b)


def b_acorn(a, b):
    r = ("..kkkk..", ".kbbbbk.", "kbkbkbbk", "kkkkkkkk", "kakaakak", ".kaaaak.", "..kaak..", "...kk...")
    return frames_of([r, r, _blink(r, 4, "kaaaaaak")], a=a, b=b)


def b_fish(a, b):
    r = ("........", "..kkkk.k", ".kaaaakk", "kwkaaabk", "kaaaaabk", ".kaaaakk", "..kkkk.k", "........")
    t = ("........", "..kkkk..", ".kaaaak.", "kwkaaabk", "kaaaaabk", ".kaaaakk", "..kkkk.k", "........")
    return frames_of([r, t], a=a, b=b)


def b_balloon(a, b):
    r = ("..kkkk..", ".kwaaak.", "kwaaaaak", "kakaakak", "kaaaaaak", ".kaaaak.", "..kkkk..", "...k....")
    return frames_of([r, _blink(r, 7, "....k...")], a=a, b=b)


def b_sun(a, b):
    r = ("o..oo..o", ".kkkkkk.", "kaaaaaak", "kakaakak", "kaakkaak", "kaaaaaak", ".kkkkkk.", "o..oo..o")
    t = ("..o..o..", ".kkkkkk.", "kaaaaaak", "kakaakak", "kaakkaak", "kaaaaaak", ".kkkkkk.", "..o..o..")
    return frames_of([r, t], a=a, b=b)


def b_rocket(a, b):
    r = ("...kk...", "..kaak..", ".kallak.", ".kaaaak.", ".kaaaak.", "kbkaakbk", "kb.kk.bk", "..yooy..")
    return frames_of([r, _blink(r, 7, "...yy...")], a=a, b=b)


def b_ufo(a, b):
    r = ("..kkkk..", ".kwlllk.", "klkllklk", "kaaaaaak", "kayaayak", ".kkkkkk.", "........", "........")
    return frames_of([r, _blink(r, 4, "kawaawak")], a=a, b=b)



# ── pass 3 heroes: twelve-by-twelve creatures (three cells square) with real faces; each level gets one or two ──
def _disc(g, cx, cy, r, colour):
    for y in range(g.shape[0]):
        for x in range(g.shape[1]):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                g[y, x] = colour


def _hero(a, b, ears, face='plain'):
    """A big round-headed creature. `ears` picks round, point, long or none; `face` plain, owl (huge eyes and a beak) or
    frog (eyes up on bumps and a wide mouth). Returns three frames: eyes open, eyes open, eyes shut."""
    g = np.full((12, 12), -1, dtype=np.int8)
    if ears == 'round':
        _disc(g, 2.3, 2.3, 2.0, a)
        _disc(g, 8.7, 2.3, 2.0, a)
    elif ears == 'point':
        for y, w in ((0, 1), (1, 2), (2, 3)):
            g[y, 2:2 + w] = a
            g[y, 10 - w:10] = a
    elif ears == 'long':
        g[0:5, 2:4] = a
        g[0:5, 8:10] = a
    if face == 'frog':
        _disc(g, 2.6, 2.8, 2.2, a)
        _disc(g, 8.4, 2.8, 2.2, a)
    _disc(g, 5.5, 6.8, 4.3, a)
    _disc(g, 5.5, 8.8, 2.5, b)
    if ears == 'round':                            # inner ear
        g[2, 2] = g[2, 9] = b
    if ears == 'long':
        g[1:3, 2] = b
        g[1:3, 9] = b
    g = outlined(g)
    if face == 'owl':
        _disc(g, 3.3, 5.3, 1.9, WHT)
        _disc(g, 7.7, 5.3, 1.9, WHT)
        g = outlined(g)
        g[5, 3] = g[6, 3] = g[5, 8] = g[6, 8] = BLK
        g[7, 5] = g[7, 6] = ORG                    # beak
        g[8, 5] = g[8, 6] = ORG
        g[9, 3:9] = np.where(g[9, 3:9] == b, YEL, g[9, 3:9])
    elif face == 'frog':
        g[3, 2] = g[3, 9] = WHT
        g[4, 2] = g[4, 9] = BLK
        g[4, 4] = g[4, 7] = BLK                    # nostrils
        g[8, 2:10] = BLK                           # a wide, wide mouth
        g[9, 3:9] = np.where(g[9, 3:9] == b, PNK, g[9, 3:9])
    else:
        g[5, 3] = g[6, 3] = g[5, 8] = g[6, 8] = BLK
        g[5, 4] = g[5, 9] = WHT                    # glints
        g[7, 5] = g[7, 6] = BLK                    # nose
        g[8, 4] = g[8, 7] = BLK                    # smile
        g[9, 5] = g[9, 6] = BLK
        g[7, 2] = g[7, 9] = PNK                    # cheeks
    shut = g.copy()
    for ex in ((3, 8) if face != 'frog' else (2, 9)):
        top = 5 if face != 'frog' else 3
        shut[top, ex] = a if face != 'owl' else WHT
    if face == 'owl':
        shut[5, 3] = shut[5, 8] = WHT
    return [g, g, g, shut]


def b_bear(a, b):
    return _hero(a, b, 'round')


def b_cat3(a, b):
    return _hero(a, b, 'point')


def b_bunny3(a, b):
    return _hero(a, b, 'long')


def b_owl3(a, b):
    return _hero(a, b, 'point', 'owl')


def b_frog3(a, b):
    return _hero(a, b, 'none', 'frog')


# kind -> (cells wide, cells high, builder, ticks per animation frame, bob offsets for a gentle drift)
PROPS = {
    'yarn': (2, 2, b_yarn, 2, ()), 'thimble': (2, 2, b_thimble, 3, ()), 'button': (2, 2, b_button, 3, ()),
    'pincushion': (2, 2, b_pincushion, 2, ()), 'mushroom': (2, 2, b_mushroom, 1, ()),
    'flower': (2, 2, b_flower, 1, ()), 'butterfly': (2, 2, b_butterfly, 1, ((0, 0), (1, -1), (2, 0), (1, 1))),
    'spoolbig': (2, 2, b_spoolbig, 2, ()), 'moon': (2, 2, b_moon, 3, ()),
    'cloud': (3, 2, b_cloud, 1, ((0, 0), (1, 0), (2, 0), (3, 0), (2, 0), (1, 0))),
    'star': (1, 1, b_star, 1, ()), 'flower4': (1, 1, b_flower4, 1, ()), 'heart': (1, 1, b_heart, 2, ()),
    'bead': (1, 1, b_bead, 1, ()),
    'owl': (2, 2, b_owl, 2, ()), 'cat': (2, 2, b_cat, 2, ()), 'bunny': (2, 2, b_bunny, 2, ()),
    'frog': (2, 2, b_frog, 2, ()), 'penguin': (2, 2, b_penguin, 2, ()), 'ghost': (2, 2, b_ghost, 2, ((0, 0), (0, -1), (0, 0), (0, 1))),
    'bat': (2, 2, b_bat, 1, ((0, 0), (1, 0), (2, 0), (1, 0))), 'pumpkin': (2, 2, b_pumpkin, 2, ()),
    'apple': (2, 2, b_apple, 2, ()), 'cupcake': (2, 2, b_cupcake, 2, ()), 'icecream': (2, 2, b_icecream, 2, ()),
    'bell': (2, 2, b_bell, 1, ()), 'acorn': (2, 2, b_acorn, 2, ()), 'fish': (2, 2, b_fish, 1, ((0, 0), (1, 0), (2, 0), (1, 0))),
    'balloon': (2, 2, b_balloon, 1, ((0, 0), (0, -1), (0, -2), (0, -1))), 'sun': (2, 2, b_sun, 1, ()),
    'rocket': (2, 2, b_rocket, 1, ()), 'ufo': (2, 2, b_ufo, 1, ((0, 0), (1, 0), (2, 0), (1, 0))),
    'bear': (3, 3, b_bear, 2, ()), 'cat3': (3, 3, b_cat3, 2, ()), 'bunny3': (3, 3, b_bunny3, 2, ()),
    'owl3': (3, 3, b_owl3, 2, ()), 'frog3': (3, 3, b_frog3, 2, ()),
}


# ── the creature that walks the top margin of the cloth; legs alternate and it never does anything ──
def b_ladybug(a, b):
    """Ten by four, facing right: red shell with spots, a black head with a white eye, legs that alternate."""
    one = ("..kkkkk...", ".kabaabkkk", "kaabaakkwk", ".k.k.k.kk.")
    two = ("..kkkkk...", ".kabaabkkk", "kaabaakkwk", "..k.k.k.k.")
    return frames_of([one, two], a=a, b=b)


def b_bee(a, b):
    """A striped bee: wings beat above, stripes along the back, a black eye and a stinger."""
    one = ("..w.ww....", ".kabkabkkk", "kabkabkkwk", ".kkkkkkk..")
    two = ("...wwww...", ".kabkabkkk", "kabkabkkwk", ".kkkkkkk..")
    return frames_of([one, two], a=a, b=b)


def b_caterpillar(a, b):
    """Round segments with a face; the humps take turns to rise."""
    one = ("..kk.kk.kk", ".kaakabkak", "kaabkaakwk", "kkkkkkkkkk")
    two = (".kk.kk..kk", "kaakabkakk", "kaabkaakwk", ".kk.kkkkkk")
    return frames_of([one, two], a=a, b=b)


def b_snail(a, b):
    """A shell with a spiral on a soft body, one eye on a stalk."""
    one = (".kkkk....k", "kabbak...k", "kabaakkkwk", "kkkkkkkkkk")
    two = (".kkkk...k.", "kabbak..kk", "kabaakkkwk", "kkkkkkkkkk")
    return frames_of([one, two], a=a, b=b)


def b_mouse(a, b):
    """A mouse facing right: round ear, pink nose and a tail behind that flicks."""
    one = ("..kk......", ".kbakkkk..", "kaaaaaaakw", ".k.k..k.kk")
    two = ("..kk......", ".kbakkkk..", "kkaaaaaakw", "k.k.k.k.kk")
    return frames_of([one, two], a=a, b=b)


def b_crab(a, b):
    """A crab: claws that open and close, two stalk eyes, legs that shuffle."""
    one = ("k.k.kk.k.k", "kkkabbakkk", ".kaaaaaak.", ".k.k..k.k.")
    two = ("kk......kk", "kkkabbakkk", ".kaaaaaak.", "k.k.kk.k.k")
    return frames_of([one, two], a=a, b=b)


def b_duck(a, b):
    """A duck on a waddle: round body, white eye, orange bill and a bobbing tail."""
    one = ("....kkk...", "k.kkaakwk.", "kkaaaaaakb", ".kkaaaakk.")
    two = ("....kkk...", "..kkaakwk.", "kkaaaaaakb", "..kkaakk..")
    return frames_of([one, two], a=a, b=b)


def b_beetle(a, b):
    """A shiny beetle: a domed shell with a seam, two horns, six legs that scuttle."""
    one = ("....k.k...", ".kkkabakkk", "kaabaabkkw", ".k.k.k.kk.")
    two = ("....k.k...", ".kkkabakkk", "kaabaabkkw", "..k.k.k.k.")
    return frames_of([one, two], a=a, b=b)


MOVERS = {'ladybug': b_ladybug, 'bee': b_bee, 'caterpillar': b_caterpillar, 'snail': b_snail,
          'mouse': b_mouse, 'crab': b_crab, 'duck': b_duck, 'beetle': b_beetle}

MOVER_W = 10


def relined(frames, colour):
    """Dark cloths swallow a black outline, so on them every outline pixel (black touching empty space) is redrawn
    in a bright line colour; eyes and other inner black stay black."""
    out = []
    for f in frames:
        g = f.copy()
        h, w = f.shape
        for y in range(h):
            for x in range(w):
                if f[y, x] == BLK and any(not (0 <= x + dx < w and 0 <= y + dy < h) or f[y + dy, x + dx] == -1
                                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    g[y, x] = colour
        out.append(g)
    return out


def dressed(frames, theme):
    return relined(frames, theme['line']) if theme.get('line') is not None else frames


# A sad, dimmed twin of any picture: every colour goes one step darker and redder, and each eye (a black pixel ringed by
# colour in the upper half) gets a tear running down from it. Used for the props and walkers on a lost run.
TINT = {WHT: PNK, YEL: ORG, ORG: RED, PNK: MAG, LBL: BLU, GRN: PUR, BLU: PUR, RED: MAR, MAG: MAR, PUR: MAR}


def grieved(frames):
    out = []
    for f in frames:
        g = f.copy()
        h, w = f.shape
        for y in range(h):
            for x in range(w):
                g[y, x] = TINT.get(int(f[y, x]), f[y, x])
        for y in range(1, int(h * 0.55) + 1):
            for x in range(w):
                if f[y, x] != BLK or y + 1 >= h or f[y + 1, x] in (-1, BLK):
                    continue
                around = [f[y + dy, x + dx] for dx, dy in ((1, 0), (-1, 0), (0, -1)) if 0 <= x + dx < w]
                if sum(1 for v in around if v not in (-1, BLK)) >= 2:
                    g[y + 1, x] = LBL
        out.append(g)
    return out


# ── the cloth of each level: a 64 by 64 backdrop built from a weave, a hem and a pattern ──
def _hem_band(style: str, hem: int, hem2: int) -> np.ndarray:
    """The three-pixel border strip for the top edge (3 rows by 64 columns); the other edges are this strip turned.
    Each level has its own trim so no two tables share an edge."""
    xs = np.arange(64)
    band = np.full((3, 64), hem, dtype=np.int8)
    if style == 'stitch':                       # a hem line and a dashed running stitch
        band[1, :] = -1
        band[2, xs % 2 == 1] = -1
    elif style == 'scallop':                    # little half-round bumps
        band[1, xs % 6 >= 4] = hem2
        band[2, :] = hem2
        band[2, (xs % 6 == 1) | (xs % 6 == 2)] = hem
    elif style == 'zigzag':                     # a two-colour ric-rac ribbon
        for y in range(3):
            band[y, ((xs + y) % 4) >= 2] = hem2
    elif style == 'beads':                      # a row of beads between two threads
        band[1, xs % 3 == 1] = hem2
        band[1, xs % 3 == 0] = -1
    elif style == 'checker':                    # a racing-flag border
        for y in range(2):
            band[y, ((xs // 2) + y) % 2 == 1] = hem2
    elif style == 'dots':                       # a calm row of round dots on a plain hem (quieter than a flag)
        band[1, xs % 4 == 1] = hem2
        band[1, xs % 4 == 2] = hem2
    elif style == 'dash':                       # a plain hem with one stitched line of long dashes
        band[1, xs % 6 < 3] = hem2
    return band


def make_cloth(theme: dict, track=(), phase: int = 0) -> np.ndarray:
    """The 64 by 64 backdrop. `phase` (0, 1 or 2) moves a slow glint across the pattern's main ink: the cloth shimmers."""
    base, ink = theme['cloth'], theme['ink']
    ys, xs = np.mgrid[0:64, 0:64]
    cloth = np.full((64, 64), base, dtype=np.int8)
    kind = theme['pat']
    if kind == 'tufts':          # little tufts of yellow and white blossom
        cloth[(ys % 16 == 3) & ((xs % 16 == 3) | (xs % 16 == 4))] = ink[0]
        cloth[(ys % 16 == 11) & ((xs % 16 == 11) | (xs % 16 == 12))] = ink[1]
        cloth[(ys % 16 == 2) & (xs % 16 == 3)] = ink[0]
    elif kind == 'quilt':        # a stitched diamond quilt
        cloth[(((xs + ys) % 8 == 0) | ((xs - ys) % 8 == 0)) & ((xs // 2 + ys // 2) % 2 == 0)] = ink[0]
    elif kind == 'polka':
        shift = ((ys // 8) % 2) * 4
        cloth[(((xs + shift) % 8) // 2 == 1) & ((ys % 8) // 2 == 1)] = ink[0]
    elif kind == 'gingham':      # big calm eight-pixel checks, a stitch in the middle of each light one
        light = ((xs // 8) + (ys // 8)) % 2 == 1
        cloth[light] = ink[0]
        cloth[light & ((xs % 8 == 3) | (xs % 8 == 4)) & ((ys % 8 == 3) | (ys % 8 == 4))] = theme.get('stitch', base)
    elif kind == 'dashes':       # a few puffs of white, like wind on a clear sky
        cloth[(ys % 8 == 5) & ((xs + (ys // 8) * 4) % 8 < 2)] = ink[0]
    elif kind == 'plaid':        # two wide tartan bands each way and a few bright thread dots, nothing finer
        cloth[((xs % 32) >= 13) & ((xs % 32) < 17)] = ink[0]
        cloth[((ys % 32) >= 13) & ((ys % 32) < 17)] = ink[0]
        cloth[(xs % 32 == 23) & (ys % 8 == 0)] = ink[1]
        cloth[(ys % 32 == 23) & (xs % 8 == 0)] = ink[1]
    elif kind == 'argyle':
        d = np.abs(xs % 16 - 8) + np.abs(ys % 16 - 8)
        cloth[(d == 6) & ((xs + ys) % 2 == 0)] = ink[0]
    elif kind == 'stripes':
        cloth[(ys % 8) < 2] = ink[0]
    elif kind == 'confetti':     # a night cloth sprinkled with bright thread ends
        seed = 7
        for _ in range(60):
            seed = (seed * 1103515245 + 12345) & 0x7fffffff
            x, y = (seed >> 4) % 64, (seed >> 12) % 64
            cloth[y, x] = ink[(seed >> 20) % len(ink)]
    # the shimmer: one third of the main-ink pixels (by blocks of five) turn to the glint colour, a different third each phase
    glint = theme.get('glint')
    if glint is not None:
        cloth[(cloth == ink[0]) & (((xs // 5) + (ys // 5)) % 3 == phase)] = glint
    # a one-pixel halo of plain cloth round every slat, so a busy weave never runs into a slat's black rim
    for cx, cy in track:
        cloth[max(0, cy * CELL - 1):cy * CELL + CELL + 1, max(0, cx * CELL - 1):cx * CELL + CELL + 1] = base
    # the trim round the edge: the band is laid on all four sides (turned for the sides) over the cloth
    band = _hem_band(theme.get('trim', 'stitch'), theme['hem'], theme.get('hem2', theme['hem']))
    for edge, strip in ((cloth[0:3, :], band), (cloth[61:64, :], band[::-1]),
                        (cloth[:, 0:3], band.T), (cloth[:, 61:64], band.T[:, ::-1])):
        edge[strip != -1] = strip[strip != -1]
    return cloth


# ── ambient life: little things that drift, rise, wander, fly or twinkle over the cloth and do nothing at all ──
def a_petal(a, b):
    return frames_of([(".a.", "aab", ".a."), ("a..", "aab", "..a")], a=a, b=b)


def a_flake(a, b):
    return frames_of([(".a.", "aaa", ".a."), ("a.a", ".b.", "a.a")], a=a, b=b)


def a_leaf(a, b):
    return frames_of([(".aa", "aab", "ba."), ("aa.", "baa", ".ab")], a=a, b=b)


def a_sprinkle(a, b):
    return frames_of([("a.", "a.", "b."), (".a", ".a", ".b")], a=a, b=b)


def a_bubble(a, b):
    return frames_of([(".a.", "a.a", ".a."), ("ba.", "a.a", ".a.")], a=a, b=b)


def a_ember(a, b):
    return frames_of([("a.", "ab"), (".a", "ba")], a=a, b=b)


def a_heart(a, b):
    return frames_of([("a.a", "aaa", ".a."), ("b.a", "aaa", ".a.")], a=a, b=b)


def a_firefly(a, b):
    return frames_of([(".a.", "aba", ".a."), ("...", ".b.", "..."), ("...", ".a.", "...")], a=a, b=b)


def a_bird(a, b):
    return frames_of([("a...a", ".a.a.", "..a.."), ("..a..", ".aaa.", "a...a")], a=a, b=b)


def a_twinkle(a, b):
    return frames_of([(".a.", "aba", ".a."), ("...", ".a.", "..."), ("...", "...", "..."), ("...", ".b.", "...")], a=a, b=b)


def a_comet(a, b):
    return frames_of([("a....", ".a...", "..b..", "...b.", "....w")], a=a, b=b)


# style -> (how it moves, builder)
AMBIENT = {'petal': ('fall', a_petal), 'flake': ('fall', a_flake), 'leaf': ('fall', a_leaf),
           'sprinkle': ('fall', a_sprinkle), 'bubble': ('rise', a_bubble), 'ember': ('rise', a_ember),
           'heart': ('rise', a_heart), 'firefly': ('wander', a_firefly), 'bird': ('fly', a_bird),
           'twinkle': ('twinkle', a_twinkle), 'comet': ('shoot', a_comet)}
SWAY = (0, 1, 2, 1)


def ambient_pose(mode: str, k: int, clock: int, level: int):
    """Where ambient sprite k is at this clock tick: (x, y, frame index, visible). Pure arithmetic, no state."""
    bx, by = 6 + (k * 29 + level * 11) % 50, 4 + (k * 17 + level * 7) % 50
    if mode == 'fall':
        return bx + SWAY[(clock // 3 + k) % 4], (by + clock) % 76 - 8, (clock // 4 + k) % 2, True
    if mode == 'rise':
        return bx + SWAY[(clock // 4 + k) % 4], 68 - (clock + by) % 76, (clock // 3 + k) % 2, True
    if mode == 'wander':
        return (bx + round(5 * math.sin(clock / 8 + k * 2.1)), by + round(3 * math.cos(clock / 6 + k)),
                (clock // 2 + k) % 3, True)
    if mode == 'fly':
        return (clock * 2 + bx * 3) % 96 - 14, by % 36 + 6 + (clock // 4) % 2, (clock // 2 + k) % 2, True
    if mode == 'twinkle':
        return bx, by, (clock // 2 + k * 3) % 4, True
    phase = (clock + k * 45) % 80          # shoot: a streak crosses the corner now and then
    return bx // 2 + phase * 3 - 4, by // 3 + phase * 2 - 4, 0, phase < 16


# ── the ten themes: cloth, trim, glint, wood, props, heroes, walkers, ambient life, spool thread ──
# amb entries are (style, colours, how many); `hero` props are the big twelve-pixel creatures.
THEMES = [
    # 1  garden table: green cloth, blossom tufts, scalloped hem, a bear, petals and fireflies
    dict(cloth=GRN, pat='tufts', ink=(YEL, WHT), glint=WHT, trim='scallop', hem=YEL, hem2=WHT, wood=(ORG, YEL, MAR), petal=YEL,
         hero=[('bear', ORG, YEL), ('bunny3', WHT, PNK)],
         big=[('mushroom', RED, WHT), ('flower', RED, YEL), ('frog', LBL, YEL), ('butterfly', PNK, YEL), ('butterfly', LBL, WHT), ('mushroom', ORG, WHT), ('flower', PNK, YEL)],
         small=[('flower4', YEL, ORG), ('flower4', WHT, YEL), ('flower4', PNK, YEL), ('bead', MAG, 0)] * 2,
         amb=[('petal', (PNK, WHT), 4), ('firefly', (YEL, ORG), 2)],
         mover=('snail', ORG, PNK), mover2=('mouse', LBL, PNK), thread=(RED, YEL, PNK, LBL)),
    # 2  night quilt: blue cloth with stitched diamonds, bead trim, an owl, fireflies and a shooting star
    dict(cloth=BLU, pat='quilt', ink=(LBL,), glint=YEL, trim='beads', hem=YEL, hem2=PNK, wood=(ORG, YEL, MAR), petal=PNK,
         hero=[('owl3', ORG, YEL)],
         big=[('moon', YEL, 0), ('cat', WHT, PNK), ('yarn', PUR, PNK), ('butterfly', MAG, PNK), ('button', YEL, ORG)],
         small=[('star', YEL, 0), ('star', WHT, 0), ('star', PNK, 0), ('star', YEL, 0), ('star', LBL, 0)] * 2,
         amb=[('firefly', (YEL, ORG), 4), ('comet', (ORG, YEL), 1)],
         mover=('bee', YEL, BLK), mover2=('crab', ORG, YEL), thread=(YEL, PNK, WHT, ORG)),
    # 3  grape velvet: purple cloth with magenta polka dots, zigzag ribbon, a frog and rising hearts
    dict(cloth=PUR, pat='polka', ink=(MAG,), glint=PNK, trim='zigzag', hem=PNK, hem2=YEL, wood=(RED, ORG, MAR), petal=PNK,
         hero=[('frog3', GRN, YEL)],
         big=[('cupcake', PNK, YEL), ('pincushion', RED, YEL), ('button', LBL, BLU), ('yarn', GRN, YEL), ('spoolbig', LBL, ORG)],
         small=[('heart', PNK, 0), ('heart', YEL, 0), ('bead', LBL, 0), ('bead', YEL, 0)] * 2,
         amb=[('heart', (PNK, YEL), 5)],
         mover=('caterpillar', GRN, YEL), mover2=('duck', YEL, ORG), thread=(PNK, YEL, LBL, GRN)),
    # 4  gingham cloth: big calm orange and yellow checks, racing-flag trim, a cat, leaves and birds
    dict(cloth=ORG, pat='gingham', ink=(YEL,), trim='dots', hem=RED, hem2=YEL, wood=(MAR, ORG, RED), petal=PNK,
         hero=[('cat3', PUR, PNK)],
         big=[('apple', RED, WHT), ('penguin', BLU, LBL), ('pincushion', PUR, YEL), ('yarn', BLU, LBL), ('acorn', YEL, RED), ('button', PUR, PNK)],
         small=[('bead', BLU, 0), ('heart', RED, 0), ('flower4', PUR, YEL), ('bead', GRN, 0)] * 2,
         amb=[('leaf', (RED, GRN), 4), ('bird', (PUR,), 2)],
         mover=('ladybug', RED, BLK), mover2=('mouse', PUR, PNK), thread=(GRN, BLU, PUR, WHT)),
    # 5  sky picnic: light blue cloth, fat clouds with faces, a bunny, birds and bubbles
    dict(cloth=LBL, pat='dashes', ink=(WHT,), glint=YEL, trim='scallop', hem=WHT, hem2=YEL, wood=(ORG, YEL, MAR), petal=YEL,
         hero=[('bunny3', WHT, PNK)],
         big=[('cloud', WHT, 0), ('balloon', RED, 0), ('cloud', WHT, 0), ('sun', YEL, 0), ('cloud', WHT, 0), ('butterfly', MAG, PNK)],
         small=[('star', WHT, 0), ('star', YEL, 0), ('bead', PNK, 0), ('flower4', PNK, YEL)] * 2,
         amb=[('bird', (BLK,), 3), ('bubble', (WHT, YEL), 3)],
         mover=('bee', YEL, BLK), mover2=('duck', WHT, ORG), thread=(BLU, RED, YEL, PNK)),
    # 6  tartan: red plaid cloth with wide bands, green bamboo slats, zigzag trim, an owl, leaves
    dict(cloth=RED, pat='plaid', ink=(MAR, YEL), glint=ORG, trim='dash', hem=YEL, hem2=GRN, wood=(GRN, YEL, MAR), petal=YEL,
         hero=[('owl3', PUR, PNK)],
         big=[('bell', YEL, ORG), ('acorn', ORG, MAR), ('bunny', WHT, PNK), ('thimble', YEL, ORG), ('pincushion', LBL, BLU)],
         small=[('heart', YEL, 0), ('bead', LBL, 0), ('star', YEL, 0), ('flower4', WHT, YEL)] * 2,
         amb=[('leaf', (YEL, ORG), 4), ('twinkle', (YEL, WHT), 3)],
         mover=('caterpillar', YEL, BLK), mover2=('crab', ORG, YEL), thread=(LBL, YEL, GRN, WHT)),
    # 7  argyle: maroon cloth with red diamonds, bead trim, a cat, embers rising
    dict(cloth=MAR, pat='argyle', ink=(RED,), glint=ORG, trim='beads', hem=ORG, hem2=YEL, wood=(ORG, YEL, MAR), petal=ORG,
         hero=[('cat3', YEL, ORG)],
         big=[('ghost', WHT, 0), ('fish', ORG, YEL), ('spoolbig', PNK, YEL), ('button', LBL, BLU), ('mushroom', YEL, WHT)],
         small=[('star', YEL, 0), ('heart', PNK, 0), ('bead', LBL, 0), ('flower4', YEL, ORG)] * 2,
         amb=[('ember', (YEL, ORG), 6)],
         mover=('snail', LBL, YEL), mover2=('beetle', GRN, YEL), thread=(YEL, LBL, PNK, GRN)),
    # 8  candy cloth: magenta with pink polka dots, racing-flag trim, a frog, sprinkles and hearts
    dict(cloth=MAG, pat='polka', ink=(PNK,), glint=YEL, trim='dots', hem=YEL, hem2=WHT, wood=(ORG, YEL, MAR), petal=YEL,
         hero=[('frog3', GRN, YEL)],
         big=[('icecream', LBL, ORG), ('cupcake', WHT, YEL), ('butterfly', YEL, ORG), ('button', YEL, ORG), ('thimble', LBL, BLU)],
         small=[('heart', WHT, 0), ('heart', YEL, 0), ('bead', LBL, 0), ('star', YEL, 0)] * 2,
         amb=[('sprinkle', (YEL, GRN, ORG, WHT), 6), ('heart', (WHT, YEL), 2)],
         mover=('ladybug', LBL, BLK), mover2=('mouse', WHT, PNK), thread=(LBL, YEL, GRN, ORG)),
    # 9  cheesecloth: yellow stripes, scalloped hem, a bear, green bubbles
    dict(cloth=YEL, pat='stripes', ink=(ORG,), glint=RED, trim='scallop', hem=RED, hem2=ORG, wood=(MAR, ORG, RED), petal=RED,
         hero=[('bear', MAR, ORG)],
         big=[('pumpkin', ORG, RED), ('penguin', PUR, LBL), ('fish', BLU, LBL), ('mushroom', RED, WHT), ('apple', GRN, RED), ('spoolbig', RED, ORG)],
         small=[('heart', RED, 0), ('bead', BLU, 0), ('flower4', PUR, ORG), ('bead', GRN, 0)] * 2,
         amb=[('bubble', (GRN, WHT), 4)],
         mover=('caterpillar', PUR, PNK), mover2=('crab', RED, ORG), thread=(PUR, BLU, RED, GRN)),
    # 10  night cloth: black with bright thread confetti, bead trim, an owl, twinkles and a comet
    dict(cloth=BLK, line=LBL, pat='confetti', ink=(YEL, PNK, LBL, WHT, ORG, GRN), glint=WHT, trim='beads', hem=MAG, hem2=YEL, wood=(ORG, YEL, MAR), petal=PNK,
         hero=[('owl3', PUR, PNK)],
         big=[('moon', YEL, 0), ('bat', PUR, 0), ('rocket', RED, YEL), ('ufo', GRN, 0), ('butterfly', PNK, YEL)],
         small=[('star', YEL, 0), ('star', PNK, 0), ('star', LBL, 0), ('heart', RED, 0), ('star', WHT, 0),
                ('bead', GRN, 0), ('star', ORG, 0), ('flower4', PNK, YEL)] * 2,
         amb=[('twinkle', (YEL, PNK, LBL, WHT, ORG, GRN), 8), ('comet', (PNK, YEL), 1)],
         mover=('bee', YEL, BLK), mover2=('beetle', PNK, YEL), thread=(YEL, PNK, LBL, GRN)),
]

SPOOL_X, SPOOL_TOP, SPOOL_GAP = N * CELL - CELL, 8, 6   # where kt01's retract studs sat
DAISY_CELLS = ((0, 0), (0, N - 1), (N - 1, N - 1))      # cloth corners, off every board
HINT_X, HINT_Y = 53, 34   # level two's picture, in the cloth right of its board
TAG_X, TAG_Y = 51, 32     # the felt label under it
MOVER_Y = 0               # the creature walks the very top margin of the cloth
MOVER2_Y = 60             # a second one walks the bottom margin the other way
MOVER_SPAN = 4 * (N - 3) - MOVER_W   # how far it can go from x = 4 before the corner flower


def plan_props(index: int, track: dict, spec: dict) -> list:
    """Scatter the level's props on free cloth, deterministically. A prop only goes where every cell it covers is
    off the slats, off the top margin (the creature's lane), off the corner flowers, the spool rack and level two's
    picture. Returns (name, kind, x, y, frames, period, bob, sad frames) rows. Heroes are placed first so they get the
    open ground; any that find no free three-by-three simply do not appear on that level."""
    theme = THEMES[index]
    blocked = set(track)
    blocked |= {(x, 0) for x in range(N)} | {(x, N - 1) for x in range(N)} | {(c[0], c[1]) for c in DAISY_CELLS}
    blocked |= {(N - 1, y) for y in range(1, 8)}
    if index == 1:
        blocked |= {(cx, cy) for cx in range(12, 16) for cy in range(8, 14)}
    seed = 1000 + index * 77
    plan = []

    def pick(wide, high, a, b, kind):
        nonlocal seed
        spots = [(cx, cy) for cy in range(N - high + 1) for cx in range(N - wide + 1)
                 if all((cx + i, cy + j) not in blocked for i in range(wide) for j in range(high))]
        if not spots:
            return
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        cx, cy = spots[(seed >> 8) % len(spots)]
        for i in range(wide):
            for j in range(high):
                blocked.add((cx + i, cy + j))
        _, _, builder, period, bob = PROPS[kind]
        px, py = cx * CELL, cy * CELL
        frames = dressed(builder(a, b), theme)
        plan.append((f"prop_{len(plan):02d}_{kind}", kind, px, py, frames, period, bob, grieved(frames)))

    for kind, a, b in theme['hero']:
        pick(PROPS[kind][0], PROPS[kind][1], a, b, kind)
    for kind, a, b in theme['big']:
        pick(PROPS[kind][0], PROPS[kind][1], a, b, kind)
    for kind, a, b in theme['small']:
        pick(1, 1, a, b, kind)
    return plan


def build_levels() -> list[Level]:
    levels: list[Level] = []
    for index, spec in enumerate(LEVELS_SPEC):
        theme = THEMES[index]
        track, junctions = build_board(spec)
        start, end = tuple(spec["start"]), tuple(spec["end"])
        sprites: list[Sprite] = []

        def add(pixels, name, x, y, layer, tags=(), visible=True):
            sprites.append(Sprite(
                pixels=pixels, name=name, x=x, y=y, layer=layer, tags=list(tags),
                blocking=BlockingMode.NOT_BLOCKED,
                interaction=InteractionMode.INTANGIBLE, visible=visible,
            ))

        # the world: cloth, then props (each one a named sprite with its own frames), then the walker
        add(make_cloth(theme, track), "cloth", 0, 0, -6, ("cloth",))
        for name, kind, px, py, frames, period, bob, sad in plan_props(index, track, spec):
            add(frames[0], name, px, py, -4, ("prop", kind))
        mover_kind, mover_a, mover_b = theme['mover']
        add(dressed(MOVERS[mover_kind](mover_a, mover_b), theme)[0], "mover", 4, MOVER_Y, -3, ("creature",))
        m2_kind, m2_a, m2_b = theme['mover2']
        add(dressed(MOVERS[m2_kind](m2_a, m2_b), theme)[0], "mover2", 4, MOVER2_Y, -3, ("creature",))
        # ambient life: drifting, rising, wandering, flying and twinkling things between the props and the slats
        k = 0
        for style, cols, count in theme['amb']:
            for _ in range(count):
                frames = AMBIENT[style][1](cols[k % len(cols)], cols[(k + 1) % len(cols)])
                add(frames[0], f"amb_{k:02d}", 0, -9, -2, ("ambient",))
                k += 1
        # the lattice and its cord
        for cell in sorted(track):
            add(_slat(cell, track, theme['wood']), f"t_{cell[0]}_{cell[1]}", cell[0] * CELL, cell[1] * CELL, -1, ("slat",))
        add(_eyelet(END), "anchor", end[0] * CELL, end[1] * CELL, 0, ("eyelet",))
        if start != end:
            add(_eyelet(START), "eyelet", start[0] * CELL, start[1] * CELL, 0, ("eyelet",))
        for cell in sorted(track):
            add([[-1] * CELL for _ in range(CELL)], f"cord_{cell[0]}_{cell[1]}",
                cell[0] * CELL, cell[1] * CELL, 1, ("cord",))
        for cell in sorted(junctions):
            add(_crossing(junctions[cell]), f"x_{cell[0]}_{cell[1]}", cell[0] * CELL, cell[1] * CELL, 2, ("mark",))
            mark = junctions[cell]
            if mark is not None:
                solid = [[WANT_H if mark == "h" else WANT_V] * CELL for _ in range(CELL)]
                add(solid, f"flash_{cell[0]}_{cell[1]}", cell[0] * CELL, cell[1] * CELL, 3,
                    ("flash",), visible=False)
        if index == 1:
            add(_tag(), "tag", TAG_X, TAG_Y, 3, ("picture",))
            add(_hint_pixels(), "hint", HINT_X, HINT_Y, 4, ("picture",))
        # corner flowers: they change each move and do nothing
        for k, cell in enumerate(DAISY_CELLS):
            add(_daisy(k, theme['petal']), f"daisy_{k}", cell[0] * CELL, cell[1] * CELL, 0, ("daisy",))
        # the thread rack in the right margin: inert, as since 21-Oct (the number of spools is kt01's 'undos')
        add(_rack(spec["undos"]), "rack", SPOOL_X, SPOOL_TOP - 2, 4, ("rack",))
        for i in range(spec["undos"]):
            add(_spool(theme['thread'][i % len(theme['thread'])]), f"spool_{i}", SPOOL_X, SPOOL_TOP + i * SPOOL_GAP, 5, ("spool",))
        # feedback sprites, hidden until needed: win sparkles round the finish, a dimming veil for a lost run
        for k in range(6):
            add(_spark(YEL, False), f"spark_{k}", 0, 0, 9, ("spark",), visible=False)
        # the level-clear shower: ribbon scraps that rain down the whole frame while a good pull tightens
        for k in range(SHOWER):
            add(_scrap(SHOWER_COLOURS[k % len(SHOWER_COLOURS)], False), f"shower_{k:02d}", 0, -9, 10, ("shower",), visible=False)
        add(make_veil(), "veil", 0, 0, 7, ("veil",), visible=False)
        add(HEAD_FRAMES["front"], "head", start[0] * CELL, start[1] * CELL, 8, ("head",))
        levels.append(Level(sprites=sprites, grid_size=(N * CELL, N * CELL)))
    return levels


def make_veil() -> np.ndarray:
    """A black frame with rounded-off corners laid over a lost run: a clean vignette, no speckle."""
    ys, xs = np.mgrid[0:64, 0:64]
    edge = np.minimum(np.minimum(xs, ys), np.minimum(63 - xs, 63 - ys))
    corner = np.minimum(xs, 63 - xs) + np.minimum(ys, 63 - ys)
    veil = np.full((64, 64), -1, dtype=np.int8)
    veil[(edge < 1) | (corner < 9)] = BLK
    return veil


def lost_cloth(cloth: np.ndarray, theme: dict) -> np.ndarray:
    """The same cloth after a lost pull: every plain pixel goes deep maroon (black on dark cloths) and every
    patterned or hemmed pixel goes red, so the whole table looks wounded while the weave stays visible."""
    base = theme['cloth']
    dim = BLK if base in (MAR, BLK) else MAR
    return np.where(cloth == base, dim, RED).astype(np.int8)


class Kt02(ARCBaseGame):

    CINCH_FRAMES = 8
    # Where the win sparkles sit round the finish eyelet, in pixels from its centre.
    SPARK_RING = ((-7, -2), (-4, -6), (1, -8), (5, -5), (7, 0), (5, 5), (0, 7), (-5, 5))
    SPARK_COLOURS = (YEL, WHT, PNK, LBL, ORG, GRN)

    def __init__(self) -> None:
        spec = LEVELS_SPEC[0]
        self.track, self.junctions = build_board(spec)
        self.state = initial_state(spec)
        self.history: list[dict] = []
        self.cinch = 0
        self.pull_good = None
        self.pull_bad = ()
        self.pull_order = {}
        self.pull_length = 0
        self.tick = 0
        self.clock = 0
        self.facing = "front"
        self._cache_level = None
        camera = Camera(
            width=N * CELL, height=N * CELL,
            background=BLK, letter_box=BLK,
        )
        super().__init__(game_id="kt02", levels=build_levels(), camera=camera,
                         available_actions=[1, 2, 3, 4, 5, 7])

    def on_set_level(self, level: Level) -> None:
        clear_translation(self)
        spec = LEVELS_SPEC[self.level_index]
        self.track, self.junctions = build_board(spec)
        self.state = initial_state(spec)
        self.history = []
        self.cinch = 0
        self.pull_good = None
        self.pull_bad = ()
        self.pull_order = {}
        self.pull_length = 0
        self.tick = 0
        self.clock = 0
        self.facing = "front"
        self._cache_level = None
        self._redraw()

    def level_reset(self) -> None:
        clear_translation(self)
        super().level_reset()

    def full_reset(self) -> None:
        clear_translation(self)
        super().full_reset()

    # ── drawing: sprites take their pixels from the state; nothing here changes a rule ──

    def _sprite(self, name: str):
        found = self.current_level.get_sprites_by_name(name)
        return found[0] if found else None

    def _scenery(self):
        """The level's animated scenery, looked up once per level object: (sprite, frames, period, bob, x, y, sad frames)
        for each prop, plus the walkers, the ambient sprites, the spools and the cloth's shimmer variants. Rebuilt
        whenever the engine hands us a fresh level object."""
        if self._cache_level is not self.current_level:
            theme = THEMES[self.level_index]
            plan = plan_props(self.level_index, self.track, LEVELS_SPEC[self.level_index])
            props = []
            for name, kind, px, py, frames, period, bob, sad in plan:
                sprite = self._sprite(name)
                if sprite is not None:
                    props.append((sprite, frames, period, bob, px, py, sad))
            self._props = props
            self._walkers = []
            for name, (kind, a, b), lane in (("mover", theme['mover'], MOVER_Y), ("mover2", theme['mover2'], MOVER2_Y)):
                frames = dressed(MOVERS[kind](a, b), theme)
                self._walkers.append((self._sprite(name), frames, grieved(frames), lane))
            self._ambient = []
            k = 0
            for style, cols, count in theme['amb']:
                mode, builder = AMBIENT[style]
                for _ in range(count):
                    self._ambient.append((self._sprite(f"amb_{k:02d}"), mode, k, builder(cols[k % len(cols)], cols[(k + 1) % len(cols)])))
                    k += 1
            self._daisies = [self._sprite(f"daisy_{k}") for k in range(len(DAISY_CELLS))]
            self._sparks = [self._sprite(f"spark_{k}") for k in range(6)]
            self._shower = [self._sprite(f"shower_{k:02d}") for k in range(SHOWER)]
            self._spools = [(self._sprite(f"spool_{i}"), theme['thread'][i % len(theme['thread'])])
                            for i in range(LEVELS_SPEC[self.level_index]["undos"])]
            self._veil = self._sprite("veil")
            self._cloth = self._sprite("cloth")
            if self._cloth is not None:
                self._cloth_ok = [make_cloth(theme, self.track, p) for p in range(3 if theme.get('glint') is not None else 1)]
                self._cloth_bad = lost_cloth(self._cloth_ok[0], theme)
            self._cache_level = self.current_level
        return self._props

    def _place_head(self) -> None:
        head = self._sprite("head")
        if head is None:
            return
        px, py = translation_position(self, (self.state["pos"][0] * CELL, self.state["pos"][1] * CELL))
        px, py = px - 1, py - 1            # the six-pixel head overhangs its four-pixel cell by one on each side
        if self.cinch and self.pull_good and self.cinch in (6, 5):
            # The whole tip draws one pixel back along its actual incoming strand, then settles
            # in the eyelet. This tug never changes the cord state or the decided outcome.
            previous = self.history[-1]["pos"] if self.history else self.state["pos"]
            px += (previous[0] > self.state["pos"][0]) - (previous[0] < self.state["pos"][0])
            py += (previous[1] > self.state["pos"][1]) - (previous[1] < self.state["pos"][1])
        head.set_position(px, py)

    def _animate_scenery(self, failed: bool) -> None:
        """Gentle life that does nothing. Props change frame and drift with the move count, the two walkers cross the
        top and bottom margins, the corner flowers turn a petal, the ambient things drift and twinkle, the spools
        shine, the cloth shimmers. A good pull makes the props hop for joy; a failed one turns them sad and dim."""
        good = self.pull_good is True
        for sprite, frames, period, bob, bx, by, sad in self._scenery():
            index = (self.tick // period + bx // CELL) % len(frames)
            sprite.pixels = (sad if failed else frames)[index]
            if failed:
                sprite.set_position(bx, by + 1)                   # a slump
            elif good:
                sprite.set_position(bx, by - (self.cinch % 2))    # a hop
            elif bob:
                dx, dy = bob[(self.tick + bx // CELL) % len(bob)]
                sprite.set_position(bx + dx, by + dy)
        span = MOVER_SPAN
        for n, (walker, frames, sad, lane) in enumerate(self._walkers):
            if walker is None:
                continue
            along = (self.tick * (2 + n) + 17 * n) % (2 * span)
            forward = along <= span                               # the top one starts rightwards, the bottom one leftwards
            frame = (sad if failed else frames)[self.tick % 2]
            if forward == (n == 0):
                walker.pixels = frame
            else:
                walker.pixels = frame[:, ::-1].copy()
            pos = along if forward else 2 * span - along
            walker.set_position(CELL + (pos if n == 0 else span - pos), lane)
        for sprite, mode, k, frames in self._ambient:
            if sprite is None:
                continue
            x, y, frame, visible = ambient_pose(mode, k, self.clock, self.level_index)
            sprite.set_visible(visible and not failed)
            if visible and not failed:
                sprite.pixels = frames[frame % len(frames)]
                sprite.set_position(x, y)
        for i, (spool, thread) in enumerate(self._spools):
            if spool is not None:
                spool.pixels = np.array(_spool(thread, (self.tick // 2 + i) % 2), dtype=np.int8)
        petal = THEMES[self.level_index]['petal']
        for k, daisy in enumerate(self._daisies):
            if daisy is not None:
                daisy.pixels = np.array(_daisy(self.tick + k, petal, failed), dtype=np.int8)
        # the level-clear shower: scraps rain down the whole frame while a good pull tightens
        for k, scrap in enumerate(self._shower):
            if scrap is None:
                continue
            y = (8 - self.cinch) * 9 + (k * 23) % 14 - 12
            showing = good and self.cinch > 0 and -3 < y < 64
            scrap.set_visible(showing)
            if showing:
                scrap.pixels = np.array(_scrap(SHOWER_COLOURS[k % len(SHOWER_COLOURS)], (self.cinch + k) % 2 == 0), dtype=np.int8)
                scrap.set_position(2 + (k * 37 + 5) % 58 + (self.cinch + k) % 3, y)

    def _life(self, failed: bool) -> None:
        """Everything that is only for looking at: the scenery, the walkers, the ambient things and the cloth."""
        self._scenery()
        self._animate_scenery(failed)
        if self._cloth is not None:
            shimmer = self._cloth_ok[(self.clock // 3) % len(self._cloth_ok)]
            self._cloth.pixels = self._cloth_bad if failed and self.cinch <= 3 else shimmer

    def _redraw(self) -> None:
        state = self.state
        decided = self.pull_good is not None
        good_pull = self.pull_good is True
        failed = self.pull_good is False
        # A monotone tension wave starts at the finish and runs back through the route. A good pull runs it in
        # purple and holds the intact, settled purple cord; a failed one runs it in magenta.
        progress = min(1.0, (self.CINCH_FRAMES - self.cinch + 1) / 6) if decided else 0.0
        threshold = self.pull_length * (1 - progress)
        wave = END if good_pull else MAG
        for cell in self.track:
            sprite = self._sprite(f"cord_{cell[0]}_{cell[1]}")
            if sprite is None:
                continue
            arms = state["arms"].get(cell)
            if arms:
                colour = wave if decided and self.pull_order.get(cell, -1) >= threshold else CORD
                sprite.pixels = np.array(_cord_pixels(arms, state["cross"].get(cell, ()), colour),
                                         dtype=np.int8)
                sprite.set_visible(True)
            else:
                sprite.set_visible(False)
        for cell, mark in self.junctions.items():
            if mark is not None:
                flash = self._sprite(f"flash_{cell[0]}_{cell[1]}")
                if flash is not None:
                    # Failed crossings alone fill in their own mark colour. The rest of the cord
                    # stays light blue; this cannot be confused with a successful tightening wave.
                    flash.set_visible(self.cinch > 2 and cell in self.pull_bad)
        self._life(failed)
        head = self._sprite("head")
        if head is not None:
            if failed:
                face = "sad"
            elif good_pull and self.cinch <= 5:
                face = "happy"
            else:
                face = self.facing
                if face in ('front', 'down', 'left', 'right') and self.tick % 6 == 5 and not decided:
                    face = 'blink'
            head.pixels = HEAD_FRAMES[face]
        self._place_head()
        # win sparkles ring the finish while a good pull tightens, and stay on the last level's settled frame
        end = LEVELS_SPEC[self.level_index]["end"]
        cx, cy = end[0] * CELL + CELL // 2, end[1] * CELL + CELL // 2
        for k, spark in enumerate(self._sparks):
            if spark is None:
                continue
            showing = good_pull and self.cinch <= 6 and (k + self.cinch) % 3 != 0
            spark.set_visible(showing)
            if showing:
                dx, dy = self.SPARK_RING[(k + self.cinch) % len(self.SPARK_RING)]
                big = (k + self.cinch) % 2 == 0
                spark.pixels = np.array(_spark(self.SPARK_COLOURS[(k + self.cinch) % 6], big), dtype=np.int8)
                size = 5 if big else 3
                spark.set_position(min(N * CELL - size, max(0, cx + dx - size // 2)),
                                   min(N * CELL - size, max(0, cy + dy - size // 2)))
        if self._veil is not None:
            self._veil.set_visible(failed and self.cinch <= 3)


    # ── kt01's controls, unchanged apart from the facing and the redraw calls ──

    def lay(self, direction: tuple[int, int]) -> bool:
        nxt = try_step(self.state, direction, self.track, self.junctions)
        if nxt is None:
            return False
        self.history.append(self.state)
        self.state = nxt
        self.facing = FACING[direction]
        return True

    def retract(self) -> bool:
        # 21-Oct-2026: no ration. A take-back works whenever any cord is laid, so a cord run into a
        # dead end (every way forward spent or off the slats) can always be backed out of. It still
        # costs a press like any move. It refuses only at the start eyelet, where nothing is laid.
        if not self.history:
            return False
        self.state = self.history.pop()
        if self.history:
            previous = self.history[-1]["pos"]
            dx, dy = self.state["pos"][0] - previous[0], self.state["pos"][1] - previous[1]
            direction = ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))
            self.facing = FACING[direction]
        else:
            self.facing = "front"
        return True

    def pull(self) -> bool:
        if self.state["pos"] != tuple(LEVELS_SPEC[self.level_index]["end"]):
            return False
        # Decide once. Later frames read only this frozen result and the frozen route.
        self.pull_bad = tuple(failed_marks(self.state, self.junctions))
        self.pull_good = not self.pull_bad
        route = []
        states = self.history + [self.state]
        for before, after in zip(states, states[1:]):
            start, end = before["pos"], after["pos"]
            dx = (end[0] > start[0]) - (end[0] < start[0])
            dy = (end[1] > start[1]) - (end[1] < start[1])
            cell = start
            while cell != end:
                route.append(cell)
                cell = (cell[0] + dx, cell[1] + dy)
        route.append(self.state["pos"])
        self.pull_length = len(route) - 1
        self.pull_order = {cell: index for index, cell in enumerate(route)}
        self.cinch = self.CINCH_FRAMES
        return True

    def _settle(self) -> None:
        if self.pull_good:
            self.next_level()
        else:
            # A wrong pull ends the run, as a loss does in the public games; RESET restarts the level.
            self.lose()

    def step(self) -> None:
        if self.action.id == GameAction.RESET:
            self.complete_action()
            return
        self.clock += 1                # the ambient clock runs on every frame, slide frames included
        if advance_translation(self):
            self._life(self.pull_good is False)
            return
        begin_translation(self, position=lambda: (self.state['pos'][0]*CELL, self.state['pos'][1]*CELL),
                          repaint=self._place_head, limit=CELL)
        if self.cinch:
            self.cinch -= 1
            if self.cinch == 0:
                self._settle()
                self._redraw()
                finish_translation(self)
            else:
                self._redraw()
            return

        self.tick += 1
        action = self.action.id
        if action == GameAction.ACTION1:
            self.lay(UP)
        elif action == GameAction.ACTION2:
            self.lay(DOWN)
        elif action == GameAction.ACTION3:
            self.lay(LEFT)
        elif action == GameAction.ACTION4:
            self.lay(RIGHT)
        elif action == GameAction.ACTION5:
            if self.pull():
                self._redraw()
                return
        elif action == GameAction.ACTION7:
            self.retract()
        self._redraw()
        finish_translation(self)
