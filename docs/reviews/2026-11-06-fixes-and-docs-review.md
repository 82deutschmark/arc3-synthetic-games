# Review of the defect fixes and the docs around them

Date: 6 November 2026. Reviewer: Claude Sonnet 5.5, asked by Mark Barney to look at the recent refactor and fixes. Written so the next assistant on this repo finds it. Nothing in this note has been acted on yet except where it says so.

Reviewed: commit `13ee7c9` (the fixes from `docs/reviews/2026-11-05-featured-twelve-review.md`), the merge `6edf7b4`, and the docs that landed around them.

## The fixes hold up

Checked on a fresh clone of `6edf7b4` with `core.autocrlf=true`, using the real engine through `tools/runtime.py`:

- `tools/validate.py`: 50 of 50 pass. `docs/validation.json` is current.
- pt01, eh01, bs01, ff01, wb02: random play (6 seeds, 3,000 actions each) hands the engine GAME_OVER; after every one, RESET restarted the level with `levels_completed` unchanged (117, 270, 604, 123 and 48 times).
- st01 and dz01: random play never reaches a loss, so the loss was set up by hand in the real engine. st01: a dead board set as the pending topple, then actions until the phase ends. dz01: `g.st.clicks = 0`, then one move. Both gave GAME_OVER, and RESET restored the opening frame, the board and progress. This proves the loss path and the reset, not that a player can reach the loss by normal play.
- st01, bs01 and se01 report `game_id` `st01`, `bs01`, `se01` with classes `St01`, `Bs01`, `Se01`. bs01 loads in about 0.07 s despite the import-time search.
- Reading the dz01 and st01 diffs: the `handle_reset` override replaces the four copies of the `_action_count` workaround. Dropping st01's old `level_reset` and `full_reset` overrides is safe, because the engine's `level_reset` calls `set_level`, which rebuilds the level.

Not checked: te01's no-raise fix in `tighten()`, lt03's tray click selecting a round, ff01's off-window markers, dz01's perched-hand drawing. They load and validate; their behaviour was not exercised.

## Open items

### 1. `EVALUATION.md` makes claims that are not true. Needs fixing.

It was added by another assistant in `9f3ee8e` (0.8.3) and says things Mark has contradicted or the repo does not support. Mark has not yet asked for a fix. Under `CODING_STANDARDS.md`, write a plan in `docs/` first.

- Line 24 and line 109: "50 clean, human-playtested games" and "50 synthetic games". Not human-playtested as a set. Mark picked 15 as the ones he liked most and thinks a person can play; the other games have not been singled out. The 2026-11-05 review found that six of the original twelve highlighted games have no human play record at all.
- Lines 157 and 159: "Recommended Holdout Suite: The 12 Featured Games" and "12 hand-curated games that underwent human playtesting and iterative tuning (e.g. LT03 went through eight revisions)". The highlighted set is 15 now, the playtesting claim is false for several, and the "eight revisions" claim has no source in the repo.
- Lines 190, 196, 200: hardcoded "50" and "12". `AGENTS.md` rule 5 says counts live in `docs/catalog.json`, not in prose.
- Not audited: the technical advice (harness design, RHAE scoring, constrained decoding). Check it before treating it as correct.

What the doc should reflect, from Mark: the highlighted games are his hand-picked best from far more games than this repo holds; they are the ones he liked most and thinks a person can play. The games are holdouts for people who trained on the 25 public games. The real risk to an evaluation is an agent reading the game source, not anyone guessing ids. Do not publish a total number of games made; Mark was not sure of it.

### 2. Catalog `version` is stale

`docs/catalog.json` has `"version": "0.6.0"`; the changelog is well past 0.8. Nothing in this repo reads the field. arc.markbarney.net might. Mark has not decided between removing it and leaving it. Ask before touching it.

### 3. The 2026-11-05 review is partly out of date

It says "the twelve featured games", and the set is 15. It did not read BL01, SS01, KT01 or the other 35 games. Its header still says "Nothing was changed in any game", which the appended "Fixes applied" section supersedes.

### 4. Process gaps in the fix commit

- No plan doc in `docs/` for the fixes, which the standards require before substantive edits.
- Headers in the changed games name the author as "Claude Code", a tool. The standards ask for the model name.

### 5. Changelog format

The blank line before the 0.8.3 entry was missing (fixed with this note).

## Design calls still with Mark

None of these were changed, on purpose. From the 2026-11-05 review:

- Four games auto-detect dead ends and kill the player on the spot (eh01, bs01, st01, dz01); bs01 also paints its own danger overlay.
- Hidden clocks in es01 and lt03.
- Levels padded by reusing layouts (te01, pt01, st01, se01).
- Six of the original twelve have never been played by a person.
- The themes of es01 and lt03.
- wf02 left alone because it is shallow, not broken, and its ACTION5 only works on lever 0.

## Added since the 2026-11-05 review

BL01, SS01 and KT01 are highlighted (changelog 0.8.2). All eight levels of SS01 and BL01 were cleared through the real engine by solver routes; KT01 levels one to six were cleared in the engine and all ten solved under its own rule functions. Their write-ups leave out the "not in the public 25" notes and any cousin games because those could not be checked from this repo. The names Basket Lift, Shared Supply and Knot Tying are proposals; only Basket Lift is Mark's.
