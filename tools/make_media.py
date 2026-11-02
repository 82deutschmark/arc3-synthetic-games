# Author: Claude Opus 5.5
# Date: 30-October-2026
# Updated: 01-November-2026, Claude Sonnet 5.5 -- stills only. The clips replayed lines recorded by game-building agents, not a
#   person's play, so the clip, the fixed walk and the recorded-line path are gone.
# PURPOSE: Render one game's pictures from the real engine: the opening frame, and a strip with every level's opening frame.
#   Prints the level count, how many openings it drew, and the inputs the game offers.
# SRP/DRY check: Pass -- loading and stepping come from tools/runtime.py; replaces make_featured_media.py.
from __future__ import annotations

import argparse
import json

import numpy as np
from PIL import Image

from runtime import ROOT, load_game, perform

PALETTE = np.array([
    (255, 255, 255), (204, 204, 204), (153, 153, 153), (102, 102, 102), (51, 51, 51), (0, 0, 0), (229, 58, 163),
    (255, 123, 204), (249, 60, 49), (30, 147, 255), (136, 216, 241), (255, 220, 0), (255, 133, 27), (146, 18, 49),
    (79, 204, 48), (163, 86, 214)], dtype=np.uint8)


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', required=True)
    args = ap.parse_args()
    out = ROOT / 'docs/previews'
    openings, first, total = openings_of(args.game)
    picture(openings[0], 4).save(out / f'{args.game}.png', optimize=True)
    strip = Image.new('RGB', (128 * len(openings), 128))
    for index, grid in enumerate(openings):
        strip.paste(picture(grid, 2), (index * 128, 0))
    strip.save(out / f'{args.game}-levels.png', optimize=True)
    print(json.dumps({'id': args.game, 'levels': total, 'tiles': len(openings),
                      'inputs': [int(a) for a in first.available_actions]}))


if __name__ == '__main__':
    main()
