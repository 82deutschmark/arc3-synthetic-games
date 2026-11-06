# ARC-3 Synthetic Games

Fifty small puzzle games for the [ARC engine](https://pypi.org/project/arcengine/), built to be pulled into somebody else's training or evaluation pipeline. Each game is one Python file. Load it, reset it, send it actions, and read back the frames the engine produces. None of them come with instructions: an agent has to work out the rules by playing, the way ARC-AGI-3 asks of it.

They were made by Team Turducken under the direction of Mark Barney, as new games in the style of the public ARC-AGI-3 set and not copies of it. Twelve are highlighted on the [browse page](https://82deutschmark.github.io/arc3-synthetic-games/), which shows what is special about each, how it differs from ARC's public 25, and what the early levels look like.

**This is a set of environments.** It has no reward function, no train/test split and no solutions. You bring the agent and decide how to score it.

## Try it

You need Python 3.13. From the repository root:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt      # Windows: .venv\Scripts\python
.venv/bin/python tools/validate.py
.venv/bin/python examples/collect.py --game wb02 --steps 16 --seed 0 --output rollouts/wb02.jsonl
```

`validate.py` checks every game's hash, loads it, resets it and takes one action. `collect.py` plays a game with random actions and writes what happened as JSON Lines. The random policy is there to show the plumbing. It is not a solver and its output is not a demonstration.

## Using the games in your own code

`tools/runtime.py` is the only integration point you need:

```python
from runtime import load_game, perform, frame_record

game = load_game("wb02")        # a game id from docs/catalog.json
frame = perform(game, 0)        # action 0 is RESET
frame = perform(game, 1)        # then actions 1-5, 7 take no arguments
frame = perform(game, 6, x=10, y=20)   # action 6 is a click at screen coordinates
obs = frame_record(frame)       # JSON-safe dict
```

An observation holds `frames` (the grid, 64 by 64 with 16 colours), `state`, `levels_completed` and `available_actions`. Games do not all offer the same controls: 1 to 4 are the arrow keys, 5 is Space, 6 is a click and 7 is undo. Read `available_actions` from each frame rather than assuming.

A few things to know before you train on this:

- **The seed in `collect.py` only seeds the exploration policy.** The games themselves are fixed, hand-built levels. There is no level generator.
- **Keep evaluation games out of training.** Several games are cousins of each other, and of the public ARC-AGI-3 games. If you want to measure generalisation, hold out whole families, not single games. We don't assign splits.
- **Keep game ids away from your agent.** The ids are opaque tags on purpose. Don't put them, or the game names, anywhere an agent under evaluation can read them.
- **Don't commit your rollouts.** They get large fast. `rollouts/` is gitignored; store trajectories on your own volume.

## What's in the repository

| Path | What it is |
| --- | --- |
| `games/` | The fifty games, one `.py` each. Hashes are in the catalog, so the files must stay byte for byte as published. |
| `docs/catalog.json` | The authoritative list: id, class, source path, SHA-256, level count, inputs, and the write-ups shown on the page. |
| `tools/runtime.py` | Loads a catalog game and serialises observations. |
| `tools/validate.py` | Integrity and smoke check. Writes `docs/validation.json`. |
| `tools/make_media.py` | Redraws a game's preview pictures from the real engine. |
| `examples/collect.py` | Random-policy rollout collector. |
| `docs/` | The browse page, its data, and the preview images in `docs/previews/`. |

## How far to trust it

The validation is shallow, and [VALIDATION.md](VALIDATION.md) says so. It proves each game imports, resets and accepts an action. It does not prove that any game can be won, that every level is solvable, or that the games are good training material. If you find an unwinnable level or a rules bug, open an issue with the game id and the action sequence.

## Contributing

Read [AGENTS.md](AGENTS.md) first. It covers the layout, the commands, and the rules for changing games and the catalog. Short version: keep the original author attribution, update the catalog hash when a game changes, record the change in [CHANGELOG.md](CHANGELOG.md), and don't commit credentials, personal play traces or large data.

## Licence and credits

MIT, see [LICENSE](LICENSE). Attribution is in [CREDITS.md](CREDITS.md). The ARC engine is a separate dependency under its own licence. This project is not affiliated with or endorsed by ARC Prize.
