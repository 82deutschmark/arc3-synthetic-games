# Author: Claude Sonnet 5.5
# Date: 07-Nov-2026
# PURPOSE: A scripted run that clears every mission of LT05 in the real engine, for people vetting the game and for
#   anyone who wants a worked solution as training data. The line it plays on each mission is the one in the 0.9.5
#   changelog: freeze the first raider with a signal (when a signal is left), then hit it with a precision shot (which
#   first takes a standing roof down when the raider is under one), and let the shots land with a few waiting presses.
#   WHAT THIS IS NOT: it is not a frames-only agent. It reads the engine's own state (the list of actors, whether a
#   raider is frozen or under a roof, the ammunition left) and pans the camera by setting the view directly, so a
#   click always lands on the target. It proves the missions can be cleared by that line, with no civilian or
#   responder lost on missions 1 to 8 (mission 9 costs four civilians); it says nothing about whether a person finds
#   the missions clear or fun, and it is not a policy an agent could run from pixels.
#   Integration: loads the game and sends actions through tools/runtime.py (the repo's only game importer); reads the
#   Lt05 object's actors, ammo, view and mission_index. Needs only requirements.txt.
#   Usage: python solutions/lt05_clear_missions.py [--mission N]      (N is 1 to 9; default all)
#   Exit code 0 when every requested mission was cleared, 1 otherwise.
# SRP/DRY check: Pass - searched the repo: no other solver exists; loading and actions come from tools/runtime.py
#   rather than a second copy of the loader; the tool order and click geometry are read from games/lt05.py.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from runtime import load_game, perform  # noqa: E402  (path set up just above)

GAME_ID = "lt05"
MISSION_COUNT = 9
RESET_ACTION = 0
CLICK_ACTION = 6
WAIT_ACTION = 7                  # a press that only lets time pass
STEP_LIMIT = 600                 # safety stop per mission
SCREEN_WIDTH, SCREEN_HEIGHT = 64, 52   # the playable window the camera pans over
TOOL_BUTTON_SPACING, TOOL_BUTTON_OFFSET, TOOL_BUTTON_ROW = 12, 5, 58   # the tool bar along the bottom of the screen
WAITS_AFTER_SHOT = 2             # presses to let a shot land
WAITS_WHEN_OUT_OF_PRECISION = 8  # presses to let the last shot's effects finish when no precision ammo is left


def hostiles(game) -> list[dict]:
    return [actor for actor in game.actors if actor["alive"] and actor["role"] == "hostile"]


def tool_order(game) -> tuple[str, ...]:
    """The game's tool-bar order. It is part of the click layout, so it is read from the game module, not copied here."""
    return sys.modules[type(game).__module__].TOOL_ORDER


def select_tool(game, tool: str) -> None:
    """Click the tool's button on the bar, unless it is already selected."""
    if game.tools[game.tool_index] != tool:
        perform(game, CLICK_ACTION, tool_order(game).index(tool) * TOOL_BUTTON_SPACING + TOOL_BUTTON_OFFSET, TOOL_BUTTON_ROW)
    assert game.tools[game.tool_index] == tool, (tool, game.tools)


def click_world(game, tool: str, world_position: tuple[int, int]) -> None:
    """Select a tool and click a world position, first panning the camera so that point is on screen.
    The pan sets the view directly (the oracle shortcut this script is honest about in its header)."""
    select_tool(game, tool)
    view_x = max(0, min(game.world_width - SCREEN_WIDTH, world_position[0] - SCREEN_WIDTH // 2))
    view_y = max(0, min(game.world_height - SCREEN_HEIGHT, world_position[1] - SCREEN_HEIGHT // 2))
    game.view_x, game.view_y = view_x, view_y
    game.camera.x, game.camera.y = view_x, view_y
    perform(game, CLICK_ACTION, world_position[0] - view_x + 1, world_position[1] - view_y + 1)


def clear_mission(mission: int):
    """Play one mission (0-based) from a fresh start. Returns (game, presses, cleared)."""
    game = load_game(GAME_ID)
    perform(game, RESET_ACTION)
    if mission:
        game.set_level(mission)
    presses = 0
    while game.ending is None and game.mission_index == mission and presses < STEP_LIMIT:
        raiders = hostiles(game)
        if not raiders:
            perform(game, WAIT_ACTION)
            presses += 1
            continue
        raider = raiders[0]
        under_roof = game._building_at(raider["pos"])
        if game.ammo["signal"] > 0 and not game._frozen(raider):
            click_world(game, "signal", raider["pos"])
            presses += 1
        if under_roof:
            click_world(game, "precision", raider["pos"])          # the first shot takes the roof down
            presses += 1
        elif not game._frozen(raider) and game.ammo["signal"] <= 0:
            perform(game, WAIT_ACTION)                                          # nothing to freeze it with: let time pass
            presses += 1
            continue
        else:
            click_world(game, "precision", raider["pos"])
            presses += 1
        for _ in range(WAITS_AFTER_SHOT):
            perform(game, WAIT_ACTION)
            presses += 1
        if game.ammo["precision"] == 0:
            for _ in range(WAITS_WHEN_OUT_OF_PRECISION):
                perform(game, WAIT_ACTION)
                presses += 1
    cleared = game.mission_index != mission or game.ending == "win"
    return game, presses, cleared


def main() -> int:
    parser = argparse.ArgumentParser(description="Clear LT05's missions with the scripted signal-then-precision line.")
    parser.add_argument("--mission", type=int, choices=range(1, MISSION_COUNT + 1), help="one mission, 1 to 9 (default all)")
    args = parser.parse_args()
    missions = [args.mission - 1] if args.mission else range(MISSION_COUNT)
    all_cleared = True
    for mission in missions:
        game, presses, cleared = clear_mission(mission)
        all_cleared &= cleared
        print(f"mission {mission + 1}: {'cleared' if cleared else game.ending or 'not cleared'} in {presses} presses; "
              f"civilians lost {game.ledger['civilian_losses']}, responders lost {game.ledger['responder_losses']}")
    return 0 if all_cleared else 1


if __name__ == "__main__":
    sys.exit(main())
