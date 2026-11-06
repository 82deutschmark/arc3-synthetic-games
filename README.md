# ARC-3 Synthetic Games

New ARC-AGI-3 style games, one Python file each, running on the ARC engine. Made by Team Turducken, under the direction of Mark Barney.

## Why they exist

ARC-AGI-3 has 25 public games. If you trained your agent on all 25, congratulations, you've got nothing left to test it on. These are your holdouts. Games you haven't seen, your agent hasn't seen, and nobody told it the rules.

They aren't copies of the public games. Plenty are cousins of the ones agents fail hardest (the Slippery Seven, see the catalog), and the [browse page](https://82deutschmark.github.io/arc3-synthetic-games/) says how each highlighted game differs from the public set and what makes a bot sweat. Want to train on them instead? Go ahead, but then you've burned your holdout. Your call.

## The catch

The source is right here. Anyone, or any coding agent, who can read `games/dz01.py` can read the rules and the win condition. The browse page is a spoilers page on purpose, too.

So the harness is on you. Your agent should only ever see what the engine gives it: frames in, actions out. If it can open files in this repo, you're not testing anything.

## Try it

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt      # Windows: .venv\Scripts\python
.venv/bin/python tools/validate.py
.venv/bin/python examples/collect.py --game wb02 --steps 16 --seed 0 --output rollouts/wb02.jsonl
```

`validate.py` checks every game's hash, loads it, resets it and takes one action. `collect.py` plays one game with random button mashing and writes JSON Lines. It's there to show the plumbing. It's not a solver, and what it writes is not a demonstration.

## Plugging in your agent

`tools/runtime.py` is all you need:

```python
from runtime import load_game, perform, frame_record

game = load_game("wb02")                # any id from docs/catalog.json
frame = perform(game, 0)                # 0 is RESET
frame = perform(game, 1)                # 1-5 and 7 take no arguments
frame = perform(game, 6, x=10, y=20)    # 6 is a click, in screen coordinates
obs = frame_record(frame)               # JSON-safe dict
```

An observation is `frames` (the grid), `state`, `levels_completed` and `available_actions`. Games don't all have the same buttons: 1 to 4 are the arrows, 5 is Space, 6 is a click, 7 is undo. Read `available_actions` off each frame, don't assume.

A few things before you point anything at it:

- The `--seed` in `collect.py` seeds the random policy only. The games are hand-built levels. There's no level generator.
- No rewards, no train/test split, no solutions. You decide what counts as success.
- Several games share ideas with each other. If you split them yourself, split by family, not at random.
- Rollouts get big fast. `rollouts/` is gitignored; keep your data somewhere else.

## What's in here

| Path | What it is |
| --- | --- |
| `games/` | The games, one `.py` each. Hashes are in the catalog, so don't edit them. |
| `docs/catalog.json` | The list of games: id, class, path, hash, levels, inputs, and the write-ups the page shows. |
| `docs/index.html` | The browse page. |
| `docs/previews/` | Real engine frames: each game's opening screen, plus a strip of the opening of every level. |
| `tools/runtime.py` | Loads a game, serialises observations. |
| `tools/validate.py` | The smoke check. Writes `docs/validation.json`. |
| `tools/make_media.py` | Redraws a game's pictures from the real engine. |
| `examples/collect.py` | The random-policy collector. |

## How far to trust it

Not very far, and [VALIDATION.md](VALIDATION.md) says so. The check proves a game loads, resets and takes an action. It doesn't prove any game can be won or that every level is solvable. Found an unwinnable level or a broken rule? Open an issue with the game id and the actions that got you there.

## Contributing

If you're a person, read this README and [CREDITS.md](CREDITS.md). If you're an agent, or sending one in, read [AGENTS.md](AGENTS.md) and [CODING_STANDARDS.md](CODING_STANDARDS.md). Don't commit credentials, play traces or big data.

## Licence

MIT, see [LICENSE](LICENSE). The ARC engine is a separate dependency under its own licence. Not affiliated with or endorsed by ARC Prize.
