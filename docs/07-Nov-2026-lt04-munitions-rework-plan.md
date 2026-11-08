# Plan: LT05, a rework of LT04's munitions

Date: 07-Nov-2026. Author: Claude Sonnet 5.5, at Mark Barney's direction. Status: waiting for approval. Nothing has been built. LT05 is a new game in its own file, `games/lt05.py`, made from `games/lt04.py`; LT04 stays as it is.

## Why

Mark's call: the five munitions are too complicated for a person to work out, and a coherent game can't be built on them. The goal is a fun shoot-'em-up for people that is hard for an AI agent that sees only the frames, as a person does. So every rule must be learnable from the picture. Difficulty comes from reading the screen, not from hidden timing or dice.

## What the code does today

From `games/lt04.py` (`TOOLS` at line 67, `_resolve`, `_impact`, `_respond`, `_frozen`, `_observe`). Heavy, precision and fire kill everything in a box. Heavy and fire also trigger `_respond` (ambulances sent, crowds converge, hostiles rush). Aid heals, puts out fires, pulls nearby civilians, resolves incidents and slows the world. Beacon refreshes observations, confirms identities, and freezes hostiles within 7 cells.

## Target design (one line each)

| Munition | Delay | Job |
|---|---|---|
| Precision | 1 | Bunker-buster. Wrecks buildings faster than any other munition (two integrity per shot). |
| Heavy | 4 | Unchanged unless Mark says otherwise. |
| Fire | 2 | Becomes the devastating one: kills nearly everything on screen. |
| Aid | 2 | Lures every civilian, ambulance and crowd toward the target. Never hostiles. Nothing else. |
| Signal (was Beacon) | 0 | Instantly freezes the one hostile at the click, marks it with a bigger signature, for long enough to switch munitions and fire. |

The intended play loop: Signal the hostiles, Aid to draw the innocents away, switch to Fire and flatten the rest.

**The house rule, in place of the coin.** A hostile inside a building is immune to every blast until the building has collapsed. Buildings already show their integrity on the roof (intact, cracked, a hole, rubble), and when one collapses, whoever was inside runs out at the door. So the player breaks the building, watches the roof fall, sees the red dot come out, then shoots it. There is no randomness. An agent has to link the roof cracks to why some shots kill and some don't.

## Decisions I'm making unless Mark says otherwise

1. **No dice.** Mark's coin flip is replaced by the house rule above, because a coin cannot be learned from the picture. A shot at a house that spares its hostile is drawn with a visible glance-off spark, so a person sees why.
2. **The two hidden clocks go.** LT04's hostiles take a double step on every 7th turn, and an unconfirmed hostile gains confidence every 18th turn. Neither is on screen. LT05 drops both. The attack fuse meter and the stale-sensor eye stay, because they are drawn. This answers the other assistant's visual-honesty note, after checking it against the code: civilians and ambulances do not move on hidden multi-turn clocks.
3. **Plain buildings stop costing risk.** Today every damaged building costs 3 risk, so the screen-wide blast would end the run at once. Plain buildings cost nothing. Hospitals and schools keep their penalty, and civilians and responders keep theirs, so the lure is what makes the big blast safe.
4. **Aid reaches the whole map**, not a 20-cell box, so "everybody leaves" is clear. It loses heal, fire-out, incident-resolve and world-slow.
5. **Heavy and Fire stop triggering `_respond`.** Aid is the only thing that moves crowds. Otherwise two systems pull people around.
6. **Signal has radius 1 and freezes for 6 turns.** That covers one switch (1 turn) plus Fire's delay (2) with room to spare. It drops the area reveal, the 4-confidence reveal and the 18-cell radius.
7. **Signal is available from mission 1.** Aid keeps its current unlock (fourth mission), because the lure only matters once crowds exist. Fire's unlock mission is open (see questions).
8. **The phone icon** is a new 12-pixel-wide sprite in the tool bar, replacing the beacon.

## Where the code changes

- `TOOLS`, `TOOL_ORDER`, unlock rules: `games/lt05.py`, one place.
- `_resolve`, `_impact`, `_respond`, `_frozen`, `_observe`: same file, rewritten to the table above, plus the house rule and the two clocks removed.
- Tool-bar sprites and the shot and impact drawing: same file's art section.
- No new modules. Nothing is shared with `lt03.py`.

## TODOs, in order

1. Read all of `lt04.py` that touches munitions, including the art, so no rule is left half-changed.
2. Change the rules.
3. Redraw the Signal icon and the fire and miss effects.
4. Drive the real engine through `tools/runtime.py`: each munition once, a hostile inside a building surviving shots until the roof collapses, then dying once it runs out (replayed twice, identical; undo restores it), Aid never moving a hostile, Signal freezing only the clicked hostile, Fire clearing the screen without ending the run once civilians are lured off, and a full mission 1 win.
5. Add LT05 to `docs/catalog.json` (hash, class, write-up, featured list; the featured count then changes, so check with Mark which game it replaces) and mention LT05 in the LT04 entry. The pre-commit hook redraws the previews (or run `make_media.py --stale`).
6. Update the file header, the changelog (a new top entry) and any docs that describe the old munitions.

## Out of scope

Other games, the lab upload, difficulty tuning beyond what the new rules force.

## Docs and changelog touchpoints

`CHANGELOG.md` top entry; `docs/catalog.json` (hash, `lt04` write-up); `docs/previews/` (regenerated); `docs/previews/manifest.json` (regenerated).

## Open questions for Mark

1. ~~Edit in place or new number~~ Settled: a new game, LT05.
2. **Which mission unlocks Fire?** It is available from mission 1 today. A screen-wide blast from the start skips the lesson.
3. **Does Heavy stay as is?** With Fire taking the big-blast role, Heavy and Fire overlap unless Heavy is trimmed or dropped.
