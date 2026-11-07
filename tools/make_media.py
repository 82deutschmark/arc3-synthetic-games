# Author: Claude Sonnet 5.5
# Date: 07-Nov-2026
# Updated: 07-Nov-2026 -- --all and --stale, plus docs/previews/manifest.json recording which game source each picture was drawn
#   from, so tools/validate.py can fail on stale pictures and the pre-commit hook can redraw only what changed.
# Earlier: 01-Nov-2026, Claude Sonnet 5.5 -- stills only. 30-Oct-2026, Claude Opus 5.5 -- first version.
# PURPOSE: Render a game's pictures from the real engine: the opening frame, and a strip with every level's opening frame.
#   --game ID redraws one game, --stale redraws every game whose source changed since its picture was drawn (or has none),
#   --all redraws everything. Each run updates the manifest. Prints one JSON line per game drawn.
# SRP/DRY check: Pass -- loading and stepping come from tools/runtime.py; the manifest format and staleness test live in
#   this file and validate.py imports them rather than repeating them.
from __future__ import annotations

import argparse
import hashlib
import json

import numpy as np
from PIL import Image

from runtime import CATALOG, ROOT, load_game, perform

PREVIEWS = ROOT / 'docs/previews'
MANIFEST = PREVIEWS / 'manifest.json'

PALETTE = np.array([
    (255, 255, 255), (204, 204, 204), (153, 153, 153), (102, 102, 102), (51, 51, 51), (0, 0, 0), (229, 58, 163),
    (255, 123, 204), (249, 60, 49), (30, 147, 255), (136, 216, 241), (255, 220, 0), (255, 133, 27), (146, 18, 49),
    (79, 204, 48), (163, 86, 214)], dtype=np.uint8)


def source_hash(entry):
    """SHA-256 of the game file as it is on disk (LF endings are forced by .gitattributes)."""
    return hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest()


def read_manifest():
    """Game id -> source hash the pictures were drawn from. Missing or unreadable means nothing is trusted."""
    try:
        return json.loads(MANIFEST.read_text())
    except (OSError, ValueError):
        return {}


def is_stale(entry, manifest):
    """True when a game's pictures are missing or were drawn from a different source."""
    pictures = [ROOT / 'docs' / path for path in entry['media'].values()]
    return manifest.get(entry['id']) != source_hash(entry) or not all(path.is_file() for path in pictures)


def picture(grid, scale):
    grid = np.asarray(grid)
    return Image.fromarray(PALETTE[np.clip(grid, 0, 15)], 'RGB').resize((grid.shape[1] * scale, grid.shape[0] * scale), Image.NEAREST)


def openings_of(game_id):
    """The opening frame of every level, asked of the game directly. The strip ends at the first level the game won't jump to."""
    game = load_game(game_id)
    first = perform(game, 0)
    total = len(getattr(game, '_levels', []) or getattr(game, 'levels', []) or [])
    out = [np.asarray(first.frame[-1])]
    for index in range(1, total):
        try:
            game.set_level(index)
            out.append(np.asarray(game.camera.render(game.current_level.get_sprites())))
        except Exception:
            break
    return out, first, total


def draw(entry):
    """Redraw one game's two pictures into the paths its catalog entry names. Returns the report line."""
    game_id = entry['id']
    openings, first, total = openings_of(game_id)
    picture(openings[0], 4).save(ROOT / 'docs' / entry['media']['play'], optimize=True)
    strip = Image.new('RGB', (128 * len(openings), 128))
    for index, grid in enumerate(openings):
        strip.paste(picture(grid, 2), (index * 128, 0))
    strip.save(ROOT / 'docs' / entry['media']['levels'], optimize=True)
    return {'id': game_id, 'levels': total, 'tiles': len(openings), 'inputs': [int(a) for a in first.available_actions]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--game', help='redraw one game by catalog id')
    group.add_argument('--stale', action='store_true', help='redraw games whose source changed since their pictures were drawn')
    group.add_argument('--all', action='store_true', help='redraw every game')
    args = ap.parse_args()
    manifest = read_manifest()
    entries = CATALOG['games']
    if args.game:
        entries = [entry for entry in entries if entry['id'] == args.game]
        if not entries:
            raise SystemExit(f'Unknown game {args.game!r}; choose a catalog id')
    elif args.stale:
        entries = [entry for entry in entries if is_stale(entry, manifest)]
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        print(json.dumps(draw(entry)))
        manifest[entry['id']] = source_hash(entry)
        # Written after every game so an interrupted run keeps what it finished.
        MANIFEST.write_text(json.dumps(dict(sorted(manifest.items())), indent=2) + '\n', newline='\n')
    if not entries:
        print('previews are current')


if __name__ == '__main__':
    main()
