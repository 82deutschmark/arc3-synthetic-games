# Featured games: follow-up fixes and guide corrections

Author: Claude Opus 5.5
Date: 06-Nov-2026
Asked by: Mark Barney ("review them again ... fix any of those problems"; the fixes credit Claude Fable 5.1). Mark told the reviewer of `docs/reviews/2026-11-06-fixes-and-docs-review.md` that this session does the work.

## Scope

In:

- Credit the 5-Nov review and fixes to Claude Fable 5.1 (headers, changelog, review). Done first.
- A second read-only review of each of the twelve originally featured games, looking for bugs the 5-Nov fixes introduced and objective defects still left: crashes, broken loss or reset paths, controls drawn as live that do nothing, module-level state shared between game instances, dead code, catalog write-ups that contradict the code, and header problems against `CODING_STANDARDS.md`. Each finding is checked by a second, sceptical reviewer who reproduces it and tests the patch in a scratch copy before anything lands.
- `EVALUATION.md`: remove the false claims listed in the 2026-11-06 review (human-playtested set, hardcoded counts, LT03's "eight revisions", cousins with no source), fix its sample code (the engine reports state as a name, not 0/1/2) and the Windows-only local paths.
- The 2026-11-05 review's header: say that fixes were applied afterwards.
- Catalog `version`: brought up to the changelog's version. AGENTS.md rule 5 says version numbers live in `docs/catalog.json` and `CHANGELOG.md`, so the two must agree.

Out (design calls that stay with Mark): difficulty, level counts and layouts, the dead-end detectors, bs01's danger overlay, budgets, lives and timers, the hidden clocks in es01 and lt03, duplicated levels, themes, wf02's lever-0-only ACTION5 and click-anywhere flash.

## Architecture

Game rules stay in `games/*.py`, one file per game. Reviewers never edit the checkout; patches they verify are applied in one place by this session, then `tools/validate.py` refreshes `docs/validation.json` and the catalog hashes are recomputed for every changed file.

## TODOs

1. Credits to Claude Fable 5.1. Done.
2. Review and adversarial check of the twelve games (read-only, in scratch copies).
3. Apply the verified patches; update headers with an "Updated" line per changed game.
4. Recompute catalog hashes; run `tools/validate.py` (every game must pass); replay each changed behaviour through `tools/runtime.py`.
5. `EVALUATION.md` corrections; review header note; catalog version.
6. Changelog entry 0.8.7; commit and push to main.

## Docs and changelog touchpoints

`CHANGELOG.md` (0.8.7), `EVALUATION.md`, `docs/catalog.json` (hashes, version, any write-up a fix makes wrong), `docs/validation.json`, `docs/reviews/2026-11-05-featured-twelve-review.md` header, and `docs/reviews/2026-11-06-fixes-and-docs-review.md` (mark its open items as handled).
