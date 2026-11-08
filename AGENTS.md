# AGENTS.md

Guidance for AI coding agents working in this repo. Humans: start with [README.md](README.md).

**How to work here is in [CODING_STANDARDS.md](CODING_STANDARDS.md). Read it first and follow it.** That includes the plan-before-code rule, the file headers, the changelog, and not committing unless asked. This file only covers what is specific to this repo.

## What this repo is for

New ARC-AGI-3 style games, released for everyone to clone and use as training data for their agents. Anyone who wants a held-out test set can use them that way too: they run their agent through the harness, with no access to the source. The games are the product. Judge every change by whether an outsider who clones this gets games that load and behave exactly as documented, on any OS, with only `requirements.txt` installed.

It is not a training system: no rewards, no train/test split, and nothing here should claim any. Solutions, solvers, win paths and play records are welcome as training data. Add them, and say plainly what each one proves (for example "cleared every mission in the real engine").

## Layout

- `games/*.py`: one game per file, on `arcengine`. Game rules live in these files and nowhere else.
- `docs/catalog.json`: the single source of truth for the game list. `docs/catalog.js` renders it into `docs/index.html`, and arc.markbarney.net mirrors it from the same file, so treat the schema as public.
- `tools/runtime.py`: the shared loader and observation serialiser. The only place games get imported.
- `tools/validate.py`: integrity and smoke check. Rewrites `docs/validation.json`.
- `tools/make_media.py`: redraws `docs/previews/` from the real engine (`--game ID`, `--stale`, `--all`) and records the source hash each picture came from in `docs/previews/manifest.json`.
- `tools/glyphs/`: generators and finished sets of made-up 5×5 symbols in TR87's style (`tr87_glyphs*.py`, `sets/`), for games that need an unreadable script. Reuse these rather than drawing new glyphs by hand; the README there says what each needs.
- `solutions/`: scripted clears and other worked solutions, one file per game. Each says in its header what it proves and what it doesn't (for example whether it reads engine internals rather than frames).
- `.githooks/pre-commit`: runs `make_media.py --stale` and stages the result. Turn it on once per clone with `git config core.hooksPath .githooks`.
- `examples/collect.py`: random-policy rollout example.
- `docs/*-plan.md`: plans, named as the standards say.

## Commands

Use a virtualenv, not the system Python.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt     # Windows: .venv\Scripts\python
.venv/bin/python tools/validate.py                      # PASS for every game, exit 0
.venv/bin/python examples/collect.py --game wb02 --steps 16 --output rollouts/x.jsonl
```

`validate.py` is the only check, and it is shallow: hashes, stale previews, import, a reset and one action. It says nothing about whether a game can be won. After changing a game, play it through `tools/runtime.py`, confirm the thing you changed actually changed, and say what you did and didn't check.

## Open review notes

Read these before starting work. They list what is known to be wrong or undecided, and what needs Mark's call.

- [docs/reviews/2026-11-07-featured-fifteen-review.md](docs/reviews/2026-11-07-featured-fifteen-review.md): benchmark review and ranking of all fifteen featured games as ARC-AGI-3 holdouts, covering the Top 5 strongest games and the design gaps in the rest.
- [docs/reviews/2026-11-06-fixes-and-docs-review.md](docs/reviews/2026-11-06-fixes-and-docs-review.md): the fixes verified, and the open items, starting with `EVALUATION.md`, which makes claims that aren't true.
- [docs/reviews/2026-11-07-play-links-and-lab.md](docs/reviews/2026-11-07-play-links-and-lab.md): why Play buttons land on the wrong game (the lab only opens games published to it), which links are dead, the TE02 and SE02 id collision, and how games get onto the lab.
- [docs/reviews/2026-11-05-featured-twelve-review.md](docs/reviews/2026-11-05-featured-twelve-review.md): the adversarial review of the featured games and the design calls it left for Mark.

## Rules for this repo

1. **Games are hash-pinned.** `docs/catalog.json` holds each game's SHA-256 and `validate.py` enforces it. Change a game, update its hash in the same change, and redraw its pictures (`make_media.py --stale`; the pre-commit hook does it for you). `.gitattributes` forces LF line endings so the hashes hold on Windows. Leave it alone.
2. **Ids are short tags** like `DZ01`. Renaming a game means moving its file and previews, and keeping the old id in the entry's `"was"` list so old links still resolve.
3. **Nothing here is hidden, by design.** The source, any solutions and the browse page (a spoilers page) are public, and they are training data. Holdout use is the evaluator's job: they run their agent through `tools/runtime.py` with no access to these files, and an example that evaluates an agent should do the same. Never hold something back from the repo for that reason.
4. **Public repo.** No credentials, personal data, virtualenvs or caches. Solutions and play records are welcome. Very large raw rollouts stay out because of their size; `rollouts/` is gitignored for that.
5. **Don't hardcode counts or versions in prose.** Game counts, highlighted counts and version numbers live in `docs/catalog.json` and `CHANGELOG.md`. Docs point at them.
6. **Be honest about scope.** The README and `VALIDATION.md` say what the checks prove. Extend them if you extend the checks, and report failures as failures.
