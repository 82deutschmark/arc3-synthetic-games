# ARC-3 Synthetic Games

New ARC-AGI-3 style games, one Python file each, running on the ARC engine. Made by Team Turducken, under the direction of Mark Barney.

## Why they exist

ARC-AGI-3 has 25 public games. These are more of them, made the same way, and they're free for everyone to use. Train your agents on them: the source, the levels and any solutions or play records added here are all open. Or, if you trained your agent on all 25 and have nothing left to test it on, hold some back as your holdouts: games you haven't seen, your agent hasn't seen, and nobody told it the rules.

They aren't copies of the public games. Plenty are cousins of the ones agents fail hardest (the Slippery Seven, see the catalog), and the [browse page](https://82deutschmark.github.io/arc3-synthetic-games/) says what makes a bot sweat on each highlighted game. The page shows only Mark's hand-picked best, the ones he liked most and thinks a person can play. The other games in `games/` are in the catalog too, but nobody has singled them out the same way. Train on all of them, some of them or none. If you want a clean holdout, keep the games you hold back out of your training. Your call.

## Nothing is hidden

The source is right here, on purpose. Anyone, or any coding agent, who can read `games/dz01.py` can read the rules and the win condition. The browse page is a spoilers page on purpose, too. For training, that's the point: read whatever helps.

If you use some games as a held-out test, the harness is on you. Run your agent through `tools/runtime.py` so it only sees what the engine gives it (frames in, actions out), with no access to this repo's files. Nothing here is held back to make that easier.

## Try it

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt      # Windows: .venv\Scripts\python
.venv/bin/python tools/validate.py
.venv/bin/python examples/collect.py --game wb02 --steps 16 --seed 0 --output rollouts/wb02.jsonl
```

`validate.py` checks every game's hash, loads it, resets it and takes one action. `collect.py` plays one game with random button mashing and writes JSON Lines. It's there to show the plumbing. It's not a solver, and what it writes is not a demonstration.

## Plugging in your agent

`tools/runtime.py` is all you need. For an in-depth guide on testing open-weights models and using these games as an air-gapped holdout suite, see [EVALUATION.md](EVALUATION.md).

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
- No rewards and no train/test split. You decide what counts as success and how to divide the games. Solutions, solvers and play records are welcome in this repo as training data.
- Several games share ideas with each other. If you split them yourself, split by family, not at random.
- Rollouts get big fast. `rollouts/` is gitignored; keep your data somewhere else.

## GPT-6.1 Terra replays

One attempt per game with the Duck harness, medium reasoning, and a 15-minute cap.
Open a replay to step through the boards, Terra's recorded decision notes,
Python tool calls, and their results. The full recording contains the engine frames.

| Game | Levels cleared | Moves | Ended by | Replay |
| --- | ---: | ---: | --- | --- |
| DZ03 | 0 / 8 | 109 | Inference timeout | [Run Inspector](https://82deutschmark.github.io/arc3-synthetic-games/replays/terra-medium/viewer.html#run=dz03&game=0&turn=1) · [Frame recording](docs/replays/terra-medium/dz03.jsonl.gz) |
| EH02 | 1 / 8 | 76 | Time limit | [Run Inspector](https://82deutschmark.github.io/arc3-synthetic-games/replays/terra-medium/viewer.html#run=eh02&game=0&turn=1) · [Frame recording](docs/replays/terra-medium/eh02.jsonl.gz) |
| BL02 | 0 / 8 | 103 | Inference timeout | [Run Inspector](https://82deutschmark.github.io/arc3-synthetic-games/replays/terra-medium/viewer.html#run=bl02&game=0&turn=1) · [Frame recording](docs/replays/terra-medium/bl02.jsonl.gz) |

## What's in here

| Path | What it is |
| --- | --- |
| `EVALUATION.md` | Guide for testing open-weights models and setting up holdouts. |
| `games/` | The games, one `.py` each. Hashes are in the catalog, so don't edit them. |
| `docs/catalog.json` | The list of games: id, class, path, hash, levels, inputs, and the write-ups the page shows. |
| `docs/index.html` | The browse page. |
| `docs/previews/` | Real engine frames: each game's opening screen, plus a strip of the opening of every level. Redrawn by `tools/make_media.py` (needs Pillow, which `requirements.txt` installs); `validate.py` fails if one is out of date. |
| `tools/runtime.py` | Loads a game, serialises observations. |
| `tools/validate.py` | The smoke check. Writes `docs/validation.json`. |
| `tools/make_media.py` | Redraws a game's pictures from the real engine. |
| `tools/glyphs/` | Generators and finished sets of made-up 5×5 symbols in TR87's style, for games that need a script nobody can read. See its README. |
| `examples/collect.py` | The random-policy collector. |
| `solutions/` | Scripted clears and other worked solutions, one file per game, each saying what it proves. |

## How far to trust it

Not very far, and [VALIDATION.md](VALIDATION.md) says so. The check proves a game loads, resets and takes an action. It doesn't prove any game can be won or that every level is solvable. Found an unwinnable level or a broken rule? Open an issue with the game id and the actions that got you there.

## Contributing

If you're a person, read this README and [CREDITS.md](CREDITS.md). If you're an agent, or sending one in, read [AGENTS.md](AGENTS.md) and [CODING_STANDARDS.md](CODING_STANDARDS.md). Don't commit credentials or personal data. Solutions and play records are welcome; say what each one proves. Very large raw rollouts aren't, because of their size.

## Licence

MIT, see [LICENSE](LICENSE). The ARC engine is a separate dependency under its own licence. Not affiliated with or endorsed by ARC Prize.
