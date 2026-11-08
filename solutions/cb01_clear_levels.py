# Author: Claude Sonnet 5.5
# Date: 08-Nov-2026
# PURPOSE: Clear every level of CB01 in the real engine, for people vetting the game and as a worked solution.
#   It searches the game's own rules (the pure functions at the top of games/cb01.py) breadth first, one beat at a time,
#   for the fewest beats that destroy all three towers, then turns that route into real inputs: action 5 to flip to the
#   card, a click inside the drop band, an arrow key for a beat with no card. The inputs go through tools/runtime.py and
#   the script checks the engine's own level counter moved on after each level.
#   WHAT THIS IS NOT: it is not a frames-only agent. It reads the rules module and tracks the selected card itself, so it
#   proves the levels can be won by that route with the real controls, and says nothing about whether a person finds the
#   levels clear or fun, or how hard they are for an agent that has to learn the controls from pictures.
#   Usage: python solutions/cb01_clear_levels.py [--level N]     (N is 1 to 6; default all)
#   Exit code 0 when every requested level was cleared, 1 otherwise.
# SRP/DRY check: Pass - no other CB01 solver exists; loading and input go through tools/runtime.py; the rules, the grid
#   size and the band geometry are read from games/cb01.py rather than copied.
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / 'tools'))

from runtime import load_game, perform  # noqa: E402  (path set up just above)

GAME_ID = 'cb01'
CYCLE, CLICK, PASS_KEY = 5, 6, 1
MAX_BEATS = 16


def rules():
    """The loaded game's own module, so the search uses exactly the rules the engine plays."""
    return sys.modules[type(load_game(GAME_ID)).__module__]


def moves(cb, st):
    """Every beat worth trying: a pass, or one card of each kind dropped in any free band column."""
    out = [('pass', None)]
    seen = set()
    for index, kind in enumerate(st.hand):
        if kind not in seen:
            seen.add(kind)
            out += [(index, col) for col in range(cb.COLS) if cb.can_deploy(st, col)]
    return out


def apply_move(cb, level, st, move):
    nxt = st.copy()
    if move[0] == 'pass':
        return nxt, cb.run_beat(level, nxt, None)
    nxt.sel = move[0]
    return nxt, cb.run_beat(level, nxt, move[1])


def search(cb, level):
    """Breadth first over beats with the wheel ignored, so the first win found uses the fewest beats."""
    start = cb.new_state(level)
    free = dict(level, dark=0)
    layer, seen = {start.key()[:3] + start.key()[4:]: (start, [])}, set()
    for _ in range(MAX_BEATS):
        nxt = {}
        for _, (st, path) in layer.items():
            for move in moves(cb, st):
                after, outcome = apply_move(cb, free, st, move)
                if outcome == 'win':
                    return path + [move]
                if outcome == 'lose':
                    continue
                key = after.key()[:3] + after.key()[4:]
                if key not in seen:
                    seen.add(key)
                    nxt[key] = (after, path + [move])
        layer = nxt
    return None


def inputs_for(cb, level, route):
    """Turn a route into (action, x, y) presses, tracking which card is selected exactly as the game does."""
    st, presses = cb.new_state(level), []
    for move in route:
        if move[0] == 'pass':
            presses.append((PASS_KEY, 0, 0))
            cb.run_beat(level, st, None)
            continue
        index, col = move
        presses += [(CYCLE, 0, 0)] * ((index - st.sel) % len(st.hand))
        presses.append((CLICK, col * cb.CELL + cb.CELL // 2, cb.BAND_ROW * cb.CELL + cb.CELL // 2))
        st.sel = index
        cb.run_beat(level, st, col)
    return presses


def clear_level(number):
    """Play one level (1-based) in the real engine from a fresh start. Returns (route, cleared)."""
    game = load_game(GAME_ID)
    cb = sys.modules[type(game).__module__]
    perform(game, 0)
    if number > 1:
        game.set_level(number - 1)
    level = cb.LEVELS[number - 1]
    route = search(cb, level)
    if route is None:
        return None, False
    before = game._score
    for action, x, y in inputs_for(cb, level, route):
        perform(game, action, x, y)
    return route, game._score == before + 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--level', type=int)
    args = ap.parse_args()
    cb = rules()
    numbers = [args.level] if args.level else range(1, len(cb.LEVELS) + 1)
    failed = 0
    for number in numbers:
        route, cleared = clear_level(number)
        print(f'level {number}: {"cleared" if cleared else "NOT cleared"} in {len(route) if route else "no"} beats; route {route}')
        failed += not cleared
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
