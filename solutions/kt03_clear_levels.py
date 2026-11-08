# Author: Claude Sonnet 5.5
# Date: 07-Nov-2026
# PURPOSE: A worked solution for KT03 (and the same puzzle in KT02, whose rules and levels are identical): for each of the
#   ten levels it searches the game's own rules for a cord line from the start eyelet to the finish with every marked crossing
#   held, then plays that line through the real engine and pulls on the finish, and checks that the level cleared. Good as
#   training data for what a finished knot looks like, and as proof that every level can be won.
#   WHAT THIS IS NOT: it is not a frames-only agent. It calls the game's own rule functions (try_step, failed_marks, state_key,
#   build_board) to search, so it knows the board in advance. It proves each level is winnable by a cord line the engine accepts;
#   the lines are depth-first finds, not the shortest, and it says nothing about whether a person finds the levels clear or fun.
#   Integration: loads the game and sends actions through tools/runtime.py (the repo's only game importer). Needs only
#   requirements.txt. Level 10 takes a few seconds.
#   Usage: python solutions/kt03_clear_levels.py [--game kt03|kt02] [--level N]     (N is 1 to 10; default all)
#   Exit code 0 when every requested level was cleared, 1 otherwise.
# SRP/DRY check: Pass - searched the repo: no other KT solver exists; loading and actions come from tools/runtime.py, and the
#   search reuses the game module's own rule functions instead of restating the rules here.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from runtime import load_game, perform  # noqa: E402  (path set up just above)

LEVEL_COUNT = 10
RESET_ACTION = 0
PULL_ACTION = 5


def find_line(rules, level_index: int):
    """Depth-first search over the game's own rules for a list of directions that lays a cord from the start to the finish with
    every marked crossing held. Returns None when there is none."""
    spec = rules.LEVELS_SPEC[level_index]
    track, junctions = rules.build_board(spec)
    end = tuple(spec["end"])
    seen = set()
    stack = [(rules.initial_state(spec), [])]
    while stack:
        state, line = stack.pop()
        key = rules.state_key(state)
        if key in seen:
            continue
        seen.add(key)
        if state["pos"] == end and not rules.failed_marks(state, junctions):
            return line
        for direction in rules.DIRS:
            following = rules.try_step(state, direction, track, junctions)
            if following is not None:
                stack.append((following, line + [direction]))
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Clear KT03's levels with a cord line found by searching the game's rules.")
    parser.add_argument("--game", choices=("kt03", "kt02"), default="kt03", help="which of the two identical puzzles to play")
    parser.add_argument("--level", type=int, choices=range(1, LEVEL_COUNT + 1), help="one level, 1 to 10 (default all)")
    args = parser.parse_args()
    game = load_game(args.game)
    rules = sys.modules[type(game).__module__]        # the game module, for its rule functions
    actions = {rules.UP: 1, rules.DOWN: 2, rules.LEFT: 3, rules.RIGHT: 4}
    perform(game, RESET_ACTION)
    levels = [args.level - 1] if args.level else range(LEVEL_COUNT)
    all_cleared = True
    for level_index in levels:
        line = find_line(rules, level_index)
        if line is None:
            print(f"level {level_index + 1}: no winning line found")
            all_cleared = False
            continue
        if level_index:
            game.set_level(level_index)
        for direction in line:
            perform(game, actions[direction])
        frame = perform(game, PULL_ACTION)
        cleared = game.level_index != level_index or frame.state.name == "WIN"   # the engine moved on, or this was the last level
        all_cleared &= cleared
        print(f"level {level_index + 1}: {len(line)} moves then a pull -> {'cleared' if cleared else frame.state.name}")
    return 0 if all_cleared else 1


if __name__ == "__main__":
    sys.exit(main())
