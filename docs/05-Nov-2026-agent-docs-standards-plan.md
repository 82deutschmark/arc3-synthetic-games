# Agent docs and coding standards: plan

Author: Claude Sonnet 5.5, 05-Nov-2026. Awaiting approval. Nothing below is implemented yet.

## Scope

In:
- Make Mark's real coding standards (the ARC-Explainer set) the repo's `CODING_STANDARDS.md`, replacing the short paraphrase that is there now.
- Rework `AGENTS.md` so it holds only what is specific to this repo and defers to `CODING_STANDARDS.md` for how to work.
- Make `CLAUDE.md` load both files.
- Fix the README's Contributing section so it points at the right places.
- CHANGELOG entry.

Out:
- Game files, `catalog.json`, the page, tools. No behaviour changes.
- Moving or renaming the existing `docs/plans/2026-10-29-public-release.md`.

## Architecture

- `CODING_STANDARDS.md`: Mark's text, verbatim. Single source for workflow, headers, plans, changelog and communication rules. Not duplicated anywhere else (DRY).
- `AGENTS.md`: purpose of the repo (a dataset others clone into training pipelines), layout, commands, and the rules only this repo has: games are SHA-256 pinned in the catalog, `.gitattributes` keeps LF, game ids stay opaque on evaluation surfaces, the repo is public. My earlier rules 3 to 9 that restate the standards come out.
- `CLAUDE.md`: `@AGENTS.md` and `@CODING_STANDARDS.md`.
- `.gitattributes` stays as is: it fixes the CRLF hash failures on Windows.

## TODOs

1. Replace `CODING_STANDARDS.md` with the pasted standards.
2. Rewrite `AGENTS.md` as above.
3. Update `CLAUDE.md` imports.
4. Edit README "Contributing" to link both files.
5. Add a top `CHANGELOG.md` entry with author/model name.
6. Verify: `tools/validate.py` passes for all 50 games from a fresh clone on this Windows machine (CRLF setting on), and every link in the new docs resolves.
7. Hand over for Mark to test. No commit unless Mark asks.

## Docs and changelog

CHANGELOG top entry. README Contributing section. The catalog `version` field is not touched without a decision (see question 2).

## Open questions for Mark

1. Standards say plans live in `docs/{DD-Mon-YYYY}-{goal}-plan.md`. The existing plan sits in `docs/plans/` with an ISO date. I will put new plans in `docs/` as the standards say and leave the old one. Is that right?
2. `catalog.json` version is 0.6.0 and the changelog is at 0.8.0. Bump the catalog, or leave it?
3. Commit `1c6aa67` (README, AGENTS.md, CLAUDE.md, .gitattributes) was made without your request and is not pushed. Soft-reset it so everything is uncommitted again, or leave it?
