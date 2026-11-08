# Fix the repo's framing: open training data, holdouts are the evaluator's job

Author: Claude Sonnet 5.5
Date: 07-Nov-2026
Asked by: Mark Barney ("It absolutely can carry the solutions ... we're going to release these to everybody and be like, 'look, here's training data for your agents' ... if those people want to use these as a held-out test set, they'll use the harness, and their agent won't have access to the source code").
Status: done in the same change as this plan, because the direction was explicit.

## What was wrong

`AGENTS.md` and `README.md` told agents the repo carries "no solutions" and no play traces or rollouts, and framed the repo as holdouts first. That wording came in with the 5-Nov-2026 README and AGENTS rewrite (commit 1c6aa67). It grew out of two older lines that meant something else: the 29-Oct-2026 release plan's "no user traces, secrets, or private data" (privacy of real people's play) and "not a solved demonstration dataset or a claim that every level has been verified solvable" (do not overclaim). Neither forbids shipping solutions. The same plan describes the repo as a dataset others clone into training pipelines.

## Scope

In: the wording in `AGENTS.md` (purpose, rules 3 and 4), `README.md` (why they exist, the catch, the "before you point anything at it" list, contributing) and one sentence in `EVALUATION.md`. Out: the games, the catalog, `docs/why.html` (Mark's own positioning), and the holdout how-to itself (`EVALUATION.md` section 3), which stays as advice for people who choose to hold games out.

## The rule now

- The repo is open training data. Source, solutions, solvers, win paths and play records are welcome, and the browse page is a spoilers page on purpose.
- Contributions say plainly what they prove (for example "cleared every mission in the real engine", not "is fun").
- Still out: credentials, personal data, virtualenvs and caches. Very large raw rollouts stay out because of size, not secrecy (`rollouts/` stays gitignored).
- Holdout use is the evaluator's setup: they run their agent through `tools/runtime.py` with no access to these files. Nothing is held back from the repo for that reason.

## First solution added

`solutions/lt05_clear_missions.py`: the scripted clear of LT05's nine missions that the 0.9.5 changelog described but nobody could find (it was a scratch script in an earlier session). Rebuilt onto `tools/runtime.py`, run against the current game, header states that it reads engine internals. The scratch script's "aid" experiments, which lose on missions 7 to 9, are not included.

## Docs and changelog

`CHANGELOG.md` entry. No game changed, so no hashes or previews move.
