# Author: Claude Sonnet 5.5 Medium
# Date: 30-October-2026
# PURPOSE: Render a featured game's three preview pictures from the real engine: the opening frame, a strip of every
#   level's opening frame, and a looping replay of level one. The replay plays a recorded winning line, passed in from
#   outside the repository, so the line itself is never published.
# SRP/DRY check: Pass — game loading and stepping come from tools/runtime.py; the palette is the one the authoring
#   site uses, stated once here. Nothing else is duplicated.
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from runtime import ROOT, load_game, perform

# The authoring site's 16-colour palette, so these pictures match the existing previews.
PALETTE = [
    (255, 255, 255), (204, 204, 204), (153, 153, 153), (102, 102, 102),
    (51, 51, 51), (0, 0, 0), (229, 58, 163), (255, 123, 204),
    (249, 60, 49), (30, 147, 255), (136, 216, 241), (255, 220, 0),
    (255, 133, 27), (146, 18, 49), (79, 204, 48), (163, 86, 214),
]
POSTER_SCALE = 4      # 64 -> 256, the size of the existing previews
REPLAY_SCALE = 5      # 64 -> 320, an exact multiple so pixels stay square
TILE_SCALE = 2        # strip tiles are 128 px; the page shrinks them smoothly
STEP_MS, SETTLE_MS, RESET_MS, FINISH_MS = 60, 480, 900, 1900


def decode(raw):
    """A trace action is 1-5, 7, or [6, x, y] (a click in screen coordinates)."""
    if isinstance(raw, int):
        return raw, 32, 32
    if isinstance(raw, list) and len(raw) == 3 and raw[0] == 6:
        return 6, int(raw[1]), int(raw[2])
    raise ValueError(f'bad trace action {raw!r}')


def to_image(grid: np.ndarray, scale: int) -> Image.Image:
    rgb = np.array(PALETTE, dtype=np.uint8)[np.clip(grid, 0, 15)]
    return Image.fromarray(rgb, 'RGB').resize((grid.shape[1] * scale, grid.shape[0] * scale), Image.NEAREST)


def play(game_id: str, trace: dict):
    """Play the whole winning line in one game instance. Returns the level-one frame groups and every level's opening."""
    game = load_game(game_id)
    frame = perform(game, 0)
    groups = [[np.asarray(f) for f in frame.frame]]            # level one's frames, one group per step
    openings = [groups[0][-1]]
    for index, level in enumerate(trace['levels']):
        for raw in level['actions']:
            action, x, y = decode(raw)
            frame = perform(game, action, x, y)
            if index == 0:
                groups.append([np.asarray(f) for f in frame.frame])
        if int(frame.levels_completed) != index + 1:
            raise SystemExit(f'level {index + 1} was not cleared by its trace actions')
        if index + 1 < len(trace['levels']):
            openings.append(np.asarray(frame.frame[-1]))
    if frame.state.value != 'WIN':
        raise SystemExit(f'trace finished in state {frame.state.value}, not WIN')
    return groups, openings


def write_gif(groups, path: Path):
    frames, durations = [], []
    for number, group in enumerate(groups):
        for position, grid in enumerate(group):
            last = position == len(group) - 1
            frames.append(to_image(grid, REPLAY_SCALE))
            durations.append((RESET_MS if number == 0 else SETTLE_MS) if last else STEP_MS)
    durations[-1] = FINISH_MS
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=False)
    return len(frames)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', required=True, help='catalog id, e.g. dz01')
    parser.add_argument('--trace', required=True, type=Path, help='winning trace JSON (arc3-trace/1) kept outside this repo')
    parser.add_argument('--out', type=Path, default=ROOT / 'docs/previews')
    args = parser.parse_args()
    trace = json.loads(args.trace.read_text())
    assert trace.get('format') == 'arc3-trace/1', 'unexpected trace format'
    groups, openings = play(args.game, trace)
    args.out.mkdir(parents=True, exist_ok=True)
    to_image(openings[0], POSTER_SCALE).save(args.out / f'{args.game}.png', optimize=True)
    strip = Image.new('RGB', (64 * TILE_SCALE * len(openings), 64 * TILE_SCALE))
    for index, grid in enumerate(openings):
        strip.paste(to_image(grid, TILE_SCALE), (index * 64 * TILE_SCALE, 0))
    strip.save(args.out / f'{args.game}-levels.png', optimize=True)
    count = write_gif(groups, args.out / f'{args.game}-opening.gif')
    print(f'{args.game}: {len(openings)} levels, replay {count} frames')


if __name__ == '__main__':
    main()
