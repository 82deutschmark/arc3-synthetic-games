# AGENTS.md

Guidance for AI coding agents working in this repo. Humans: start with [README.md](README.md).

**How to work here is in [CODING_STANDARDS.md](CODING_STANDARDS.md). Read it first and follow it.** That includes the plan-before-code rule, the file headers, the changelog, and not committing unless asked. This file only covers what is specific to this repo.

## What this repo is for

New ARC-AGI-3 style games for other people to clone and run in their own training and evaluation pipelines. The main use is as holdouts for anyone who trained on the 25 public games and has nothing left to test on. The games are the product. Judge every change by whether an outsider who clones this gets games that load and behave exactly as documented, on any OS, with only `requirements.txt` installed.

It is not a training system. No rewards, no splits, no solutions, and nothing here should claim any.

## Layout

- `games/*.py`: one game per file, on `arcengine`. Game rules live in these files and nowhere else.
- `docs/catalog.json`: the single source of truth for the game list. `docs/catalog.js` renders it into `docs/index.html`, and arc.markbarney.net mirrors it from the same file, so treat the schema as public.
- `tools/runtime.py`: the shared loader and observation serialiser. The only place games get imported.
- `tools/validate.py`: integrity and smoke check. Rewrites `docs/validation.json`.
- `tools/make_media.py`: redraws `docs/previews/` from the real engine (`--game ID`, `--stale`, `--all`) and records the source hash each picture came from in `docs/previews/manifest.json`.
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
3. **The source is readable by design,** and so is the browse page, which is a spoilers page. Don't write examples or docs that suggest putting either in front of an agent being tested.
4. **Public repo.** No credentials, personal data, play traces, rollouts, virtualenvs or caches. `rollouts/` is gitignored for this.
5. **Don't hardcode counts or versions in prose.** Game counts, highlighted counts and version numbers live in `docs/catalog.json` and `CHANGELOG.md`. Docs point at them.
6. **Be honest about scope.** The README and `VALIDATION.md` say what the checks prove. Extend them if you extend the checks, and report failures as failures.
