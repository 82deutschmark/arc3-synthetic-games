# ARC-3 Synthetic Games

ARC-AGI-3 style games by Team Turducken, under the direction of Mark Barney. Python source on the ARC engine, no instructions. Page: https://82deutschmark.github.io/arc3-synthetic-games/

## Quick start

Use Python 3.13 (the release was exercised with Python 3.13 and the pinned dependencies below). From the repository root:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/validate.py
.venv/bin/python examples/collect.py --game wb01 --steps 16 --seed 0 --output rollouts/wb01.jsonl
```

The collector runs a real game. Its random policy is an integration example, **not an expert or a solver**. It writes JSON Lines: each row contains game_id, the action just taken, and the resulting observation. The first action is RESET (zero). Observations contain the engine's frames, state, levels_completed and available_actions. Click actions also contain screen x/y coordinates. The collector stops at a terminal state and refuses to overwrite files.

The seed controls the exploration policy, not procedural game generation. No generated-level API is claimed for these environments. Store large trajectory collections on your own data volume rather than in Git.

## Connect a learner

`tools/runtime.py` is the small integration boundary. `load_game(id)` returns a real engine instance; `perform(game, 0)` resets; subsequent `perform` calls accept action IDs and optional click coordinates. Read the returned frame's advertised actions instead of assuming every game has identical controls. Replace the random action choice in `examples/collect.py` with your own agent.

The collection provides environments, not a complete reinforcement-learning system. Define rewards and training targets explicitly. Keep evaluation games and related game families out of training when measuring generalization; this release does not assign or certify train/test splits. Do not interpret failed random exploration as a demonstration target.

## What's included

- `games/`: the current version of each game, byte for byte; `docs/catalog.json` has each file's hash.
- `docs/previews/`: real engine frames: each game's opening screen and the first frame of every level.
- The page shows the highlighted games only. Every approved game is here in `games/` and in `docs/catalog.json`.
- `tools/validate.py`: loads each game, resets it and takes one action. It does not play games through.
- Human numbers on the page come from people's review plays. A dash means none recorded yet. Winning lines are not published.

## Contributing

Include original attribution and a real runnable source artifact. Document game families, required dependencies and reproducible playthrough checks. Do not commit credentials, personal play traces or large data. Keep evaluation reporting distinct from training data collection.
