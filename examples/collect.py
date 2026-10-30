# Author: GPT-6.1 Sol
# Date: 29-October-2026
# PURPOSE: Record real exploration trajectories from released games for agent integration.
# SRP/DRY check: Pass — runtime.py owns game loading and observation serialization.
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from runtime import CATALOG, frame_record, load_game, perform


def main():
    parser = argparse.ArgumentParser(description='Collect random exploration, NOT expert demonstrations.')
    parser.add_argument('--game', default='wb01', choices=[row['id'] for row in CATALOG['games']])
    parser.add_argument('--steps', type=int, default=16)
    parser.add_argument('--seed', type=int, default=0, help='Seeds exploration actions, not game generation.')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.steps < 0:
        parser.error('--steps must be nonnegative')
    if args.output.exists():
        parser.error('Refusing to overwrite an existing rollout')
    rng = random.Random(args.seed)
    game = load_game(args.game)
    frame = perform(game, 0)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        stream.write(json.dumps({'game_id': args.game, 'action': {'id': 0}, 'observation': frame_record(frame)}) + '\n')
        for _ in range(args.steps):
            if frame.state.name in {'WIN', 'GAME_OVER'}:
                break
            actions = [int(item) for item in frame.available_actions if int(item) != 0]
            if not actions:
                break
            action = {'id': rng.choice(actions)}
            if action['id'] == 6:
                action.update(x=rng.randrange(64), y=rng.randrange(64))
            frame = perform(game, **{'action_id': action['id'], 'x': action.get('x', 32), 'y': action.get('y', 32)})
            stream.write(json.dumps({'game_id': args.game, 'action': action, 'observation': frame_record(frame)}) + '\n')
    print(f'Wrote real exploration to {args.output}')


if __name__ == '__main__':
    main()
