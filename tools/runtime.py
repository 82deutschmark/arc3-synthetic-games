# Author: GPT-6.1 Sol
# Date: 29-October-2026
# PURPOSE: Load catalog-pinned game classes for real ARC engine rollouts and checks.
# SRP/DRY check: Pass — shares loading between collection and validation, uses the engine API.
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

from arcengine import ActionInput, GameAction

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'docs/catalog.json').read_text())


def load_game(game_id: str):
    """Instantiate an allowed catalog game, without accepting arbitrary file paths."""
    entry = next((row for row in CATALOG['games'] if row['id'] == game_id), None)
    if entry is None:
        raise ValueError(f'Unknown game {game_id!r}; choose a catalog id')
    sys.path.insert(0, str(ROOT / 'games'))
    spec = importlib.util.spec_from_file_location(f'synthetic_{game_id}', ROOT / entry['path'])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return getattr(module, entry['class_name'])()


def perform(game, action_id: int, x: int = 32, y: int = 32):
    """Clicks use screen coordinates; reset is action zero."""
    data = {'x': x, 'y': y} if action_id == 6 else {}
    return game.perform_action(ActionInput(id=GameAction.from_id(action_id), data=data), raw=True)


def frame_record(frame):
    """JSON-safe engine observations; includes actual state, never a fabricated reward."""
    return {'frames': [item.tolist() if hasattr(item, 'tolist') else item for item in frame.frame],
            'state': frame.state.value, 'levels_completed': int(frame.levels_completed),
            'available_actions': [int(item) for item in frame.available_actions]}
