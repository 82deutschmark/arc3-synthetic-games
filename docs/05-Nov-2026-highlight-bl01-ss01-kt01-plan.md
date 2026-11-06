# Highlight BL01, SS01 and KT01: plan

Author: Claude Sonnet 5.5, 05-Nov-2026. Scope set by Mark's direction in session ("add SS01 and KT01", and BL01 earlier). Mark also said BL01 should be in.

## Scope

In:
- Add BL01, SS01 and KT01 to the highlighted set in `docs/catalog.json`: each gets a `spoiler` entry (teaser, why AI struggles, rules, what's special, look) and goes in `featured`.
- Fix KT01's `levels` (null in the catalog, 10 in the engine and on its strip).

Out:
- Game files and their hashes. No game changes.
- The "not in the public 25" text and any named cousin games: I can't check those from this repo, so they are left out. The page hides sections that are missing.
- `markSaid` quotes: Mark has not said these can be published.
- KT01's play link (points at `g036`) and class name (`G036`): unverified, left alone.

## Architecture

- `docs/catalog.json` is the only data file. `docs/catalog.js` already renders any entry with a `spoiler`, so the page code does not change.
- Entries follow the existing ones (teaser, hard, rules, special, look).
- Every statement in a write-up comes from the game's code, its pictures, or a run of the real engine.

## TODOs

1. Read each game's rules in its source and look at its pictures. Done.
2. Run each game through the real engine with a solver route: SS01 and BL01 all eight levels, KT01 levels one to six in the engine and all ten by the game's own rule functions. Done.
3. Write the three `spoiler` entries and add the ids to `featured`; set KT01 `levels` to 10.
4. `tools/validate.py` passes for every game and the featured pictures exist.
5. Load the page in a browser and look at the new cards and panels.
6. Changelog entry.

## Docs and changelog

Top `CHANGELOG.md` entry. No README change: it points at the catalog and carries no counts.

## Open for Mark

- Names. The tags have to spell a name. Proposed: BL01 Basket Lift (yours), SS01 Shared Supply, KT01 Knot Tying.
- Order on the page. The three go last.
- Whether to quote any of Mark's comments on these cards.
