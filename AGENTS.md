# AGENTS.md

Guidance for AI coding agents working in this repository. Humans should start with [README.md](README.md).

## What this repository is for

This is a **published dataset of synthetic ARC-AGI-3 style games**, made to be cloned by other people and dropped into their training and evaluation pipelines. The games are the product. Every decision should be judged by whether an outside user who clones this repo gets games that load, run and behave exactly as documented, on any OS, with nothing else installed beyond `requirements.txt`.

It is not an application and not a training system. It has no rewards, no splits and no solutions, and must not claim any.

## Layout

- `games/*.py`: one game each, built on `arcengine`. Rules live in these files and nowhere else.
- `docs/catalog.json`: the single source of truth for the game list (id, class name, path, SHA-256, levels, inputs, write-ups). `docs/catalog.js` renders it into `docs/index.html`, and the separate site arc.markbarney.net mirrors it, so treat its schema as a public interface.
- `tools/runtime.py`: the shared loader and observation serialiser. The only place games are imported.
- `tools/validate.py`: integrity and smoke check; rewrites `docs/validation.json`.
- `tools/make_media.py`: regenerates `docs/previews/` from the real engine.
- `examples/collect.py`: random-policy rollout example.
- `docs/plans/`: dated plans for substantive changes.

## Commands

Python 3.13. Use a virtualenv, never the system interpreter.

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt     # Windows: .venv\Scripts\python
.venv/bin/python tools/validate.py                      # must print PASS for every game, exit 0
.venv/bin/python examples/collect.py --game wb02 --steps 16 --output rollouts/x.jsonl
```

There is no test suite beyond `validate.py`. It checks hashes, imports, a reset and one action. It does **not** show a game is winnable. After changing a game, play it for real through `tools/runtime.py` and confirm the behaviour you changed, then say what you did and did not check.

## Rules

1. **Games are hashed.** `docs/catalog.json` stores each game's SHA-256 and `validate.py` enforces it. If you change a game, update its hash in the same commit. `.gitattributes` forces LF endings so hashes match on Windows; do not remove it.
2. **Game ids are opaque.** Never put game names or descriptive ids into anything an agent under evaluation could read, such as observations, filenames in examples, or prompts. Renaming a game means moving its file and previews and keeping the old id in the entry's `"was"` list so links still resolve.
3. **Reuse before you write.** Search for an existing helper before adding one. Shared loading belongs in `tools/runtime.py`. Don't duplicate game rules outside the game's file.
4. **Real behaviour only.** No fabricated data, placeholder logic or invented rewards. Don't describe a game as solved or verified unless you played it and can say how.
5. **Attribution.** Keep original author lines. Every new or modified Python, JavaScript, HTML or CSS file starts with a comment giving the actual author model, date, purpose and an SRP/DRY note. JSON stays comment-free. Full text in [CODING_STANDARDS.md](CODING_STANDARDS.md).
6. **Record changes.** For anything substantive, write a dated plan in `docs/plans/` first, then add a `CHANGELOG.md` entry afterwards. Keep `docs/catalog.json`'s `version` in step with the changelog.
7. **This repo is public.** Never commit credentials, personal data, play traces, generated rollouts, virtualenvs or caches. `rollouts/` is gitignored for that reason.
8. **Stay honest about scope.** `VALIDATION.md` and the README state what the checks prove. If you extend the checks, update them; if something fails, say so.
9. **Commits.** Stage only the paths you mean to change and read the diff first. Don't commit or push unless asked.

## Known loose ends

- `docs/catalog.json` `version` (0.6.0) has fallen behind `CHANGELOG.md` (0.8.0).
- `docs/plans/2026-10-29-public-release.md` still has its last checklist item open.
