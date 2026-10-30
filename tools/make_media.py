# Author: Claude Opus 5.5
# Date: 30-October-2026
# PURPOSE: Render one game's pictures from the real engine: opening frame, each level's opening frame, and a short
#   gameplay clip of level one. A recorded line, kept outside this repository, drives the clip when one still clears
#   level one; otherwise the clip is a short fixed walk of real moves. Prints which it used.
# SRP/DRY check: Pass -- loading and stepping come from tools/runtime.py; replaces make_featured_media.py.
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from runtime import ROOT, load_game, perform

PALETTE = np.array([
    (255, 255, 255), (204, 204, 204), (153, 153, 153), (102, 102, 102), (51, 51, 51), (0, 0, 0), (229, 58, 163),
    (255, 123, 204), (249, 60, 49), (30, 147, 255), (136, 216, 241), (255, 220, 0), (255, 133, 27), (146, 18, 49),
    (79, 204, 48), (163, 86, 214)], dtype=np.uint8)
MAX_CLIP_FRAMES = 140


def picture(grid, scale):
    grid = np.asarray(grid)
    return Image.fromarray(PALETTE[np.clip(grid, 0, 15)], 'RGB').resize((grid.shape[1] * scale, grid.shape[0] * scale), Image.NEAREST)


def decode(raw):
    return (raw, 32, 32) if isinstance(raw, int) else (6, int(raw[1]), int(raw[2]))


def run_line(game_id, trace):
    """Play a recorded line. Returns level-one frame groups and every opening reached, or None if level one isn't cleared."""
    game = load_game(game_id)
    frame = perform(game, 0)
    groups, openings = [[np.asarray(f) for f in frame.frame]], [np.asarray(frame.frame[-1])]
    for index, level in enumerate(trace['levels']):
        for raw in level['actions']:
            frame = perform(game, *decode(raw))
            if index == 0:
                groups.append([np.asarray(f) for f in frame.frame])
        if int(frame.levels_completed) != index + 1:
            return (groups, openings) if index else None
        if frame.state.value != 'WIN':
            openings.append(np.asarray(frame.frame[-1]))
    return groups, openings


def walk(game_id):
    """No usable line: a fixed walk through whatever actions the game offers, resetting if the run ends."""
    game = load_game(game_id)
    frame = perform(game, 0)
    groups = [[np.asarray(f) for f in frame.frame]]
    actions = [int(a) for a in frame.available_actions]
    moves = [a for a in actions if a in (1, 2, 3, 4)] or actions
    pattern = [m for m in moves for _ in range(4)] + ([5] if 5 in actions else [])
    for step in range(48):
        action = pattern[step % len(pattern)]
        x, y = (8 + (step * 11) % 48, 8 + (step * 7) % 48)
        frame = perform(game, action, x, y)
        groups.append([np.asarray(f) for f in frame.frame])
        if frame.state.value in ('GAME_OVER', 'WIN'):
            break
    return groups


def direct_openings(game_id, known):
    """Fill level openings the line didn't reach by asking the game for the level directly, where it allows that."""
    game = load_game(game_id)
    frame = perform(game, 0)
    out = list(known)
    total = len(getattr(game, '_levels', []) or getattr(game, 'levels', []) or [])
    for index in range(len(out), total):
        try:
            game.set_level(index)
            out.append(np.asarray(game.camera.render(game.current_level.get_sprites())))
        except Exception:
            break
    return out, frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', required=True)
    ap.add_argument('--traces', type=Path, nargs='*', default=[])
    args = ap.parse_args()
    out, source, result = ROOT / 'docs/previews', 'walk', None
    for path in args.traces:
        try:
            result = run_line(args.game, json.loads(path.read_text()))
        except Exception:
            result = None
        if result:
            source = 'line'
            break
    groups, openings = result if result else (walk(args.game), [])
    if not openings:
        openings = [groups[0][-1]]
    openings, first = direct_openings(args.game, openings)
    picture(openings[0], 4).save(out / f'{args.game}.png', optimize=True)
    strip = Image.new('RGB', (128 * len(openings), 128))
    for index, grid in enumerate(openings):
        strip.paste(picture(grid, 2), (index * 128, 0))
    strip.save(out / f'{args.game}-levels.png', optimize=True)
    frames, times = [], []
    for number, group in enumerate(groups):
        for position, grid in enumerate(group):
            last = position == len(group) - 1
            frames.append(picture(grid, 4))
            times.append((800 if number == 0 else 260) if last else 60)
    keep = frames[:MAX_CLIP_FRAMES]
    times = times[:MAX_CLIP_FRAMES]
    times[-1] = 1600
    keep[0].save(out / f'{args.game}-play.gif', save_all=True, append_images=keep[1:], duration=times, loop=0)
    print(json.dumps({'id': args.game, 'clip': source, 'tiles': len(openings), 'frames': len(keep),
                      'inputs': [int(a) for a in first.available_actions]}))


if __name__ == '__main__':
    main()
