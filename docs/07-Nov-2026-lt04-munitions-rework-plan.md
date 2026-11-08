# Plan: LT04 munitions rework

Date: 07-Nov-2026. Author: Claude Sonnet 5.5, at Mark Barney's direction. Status: waiting for approval, nothing in `games/lt04.py` has been changed.

## Why

Mark's call: the five munitions are too complicated for a person to work out, and a coherent game can't be built on them. The goal is a game that is maximally clear to a person and maximally hard for an AI agent. The rework gives each munition one job that a person can see.

## What the code does today

From `games/lt04.py` (`TOOLS` at line 67, `_resolve`, `_impact`, `_respond`, `_frozen`, `_observe`). Heavy, precision and fire kill everything in a box. Heavy and fire also trigger `_respond` (ambulances sent, crowds converge, hostiles rush). Aid heals, puts out fires, pulls nearby civilians, resolves incidents and slows the world. Beacon refreshes observations, confirms identities, and freezes hostiles within 7 cells.

## Target design (one line each)

| Munition | Delay | Job |
|---|---|---|
| Precision | 1 | Small blast. Wrecks more infrastructure than today. 50% of the time the target survives. |
| Heavy | 4 | Unchanged unless Mark says otherwise. |
| Fire | 2 | Becomes the devastating one: kills nearly everything on screen. |
| Aid | 2 | Lures every civilian, ambulance and crowd toward the target. Never hostiles. Nothing else. |
| Signal (was Beacon) | 0 | Instantly freezes the one hostile at the click, marks it with a bigger signature, for long enough to switch munitions and fire. |

The intended play loop: Signal the hostiles, Aid to draw the innocents away, switch to Fire and flatten the rest.

## Decisions I'm making unless Mark says otherwise

1. **The coin is deterministic.** The precision coin is derived from game state (mission, tick, shot count, position), not a random number generator. The engine replays and undoes by re-running actions, so a true random call would break undo. It still looks like a coin flip to a player. Mark's "AI-confusing" intent is kept, because the rule is not visible on screen.
2. **A miss is drawn.** A precision shot that spares its target shows a visible fizzle. A coin flip with no feedback would be unclear to people, which is the opposite of the goal.
3. **Plain buildings stop costing risk.** Today every damaged building costs 3 risk, so the screen-wide blast would end the run at once. Plain buildings cost nothing. Hospitals and schools keep their penalty, and civilians and responders keep theirs, so the lure is what makes the big blast safe.
4. **Aid reaches the whole map**, not a 20-cell box, so "everybody leaves" is clear. It loses heal, fire-out, incident-resolve and world-slow.
5. **Heavy and Fire stop triggering `_respond`.** Aid is the only thing that moves crowds. Otherwise two systems pull people around.
6. **Signal has radius 1 and freezes for 6 turns.** That covers one switch (1 turn) plus Fire's delay (2) with room to spare. It drops the area reveal, the 4-confidence reveal and the 18-cell radius.
7. **Signal is available from mission 1.** Aid keeps its current unlock (fourth mission), because the lure only matters once crowds exist. Fire's unlock mission is open (see questions).
8. **The phone icon** is a new 12-pixel-wide sprite in the tool bar, replacing the beacon.

## Where the code changes

- `TOOLS`, `TOOL_ORDER`, unlock rules: `games/lt04.py`, one place.
- `_resolve`, `_impact`, `_respond`, `_frozen`, `_observe`: same file, rewritten to the table above.
- Tool-bar sprites and the shot and impact drawing: same file's art section.
- No new modules. Nothing is shared with `lt03.py`.

## TODOs, in order

1. Read all of `lt04.py` that touches munitions, including the art, so no rule is left half-changed.
2. Change the rules.
3. Redraw the Signal icon and the fire and miss effects.
4. Drive the real engine through `tools/runtime.py`: each munition once, the precision coin on a fixed run (replayed twice, identical; undo restores it), Aid never moving a hostile, Signal freezing only the clicked hostile, Fire clearing the screen without ending the run once civilians are lured off, and a full mission 1 win.
5. Update the catalog hash and the LT04 write-up in `docs/catalog.json`. The pre-commit hook redraws the previews (or run `make_media.py --stale`).
6. Update the file header, the changelog (a new top entry) and any docs that describe the old munitions.

## Out of scope

Other games, the lab upload, difficulty tuning beyond what the new rules force.

## Docs and changelog touchpoints

`CHANGELOG.md` top entry; `docs/catalog.json` (hash, `lt04` write-up); `docs/previews/` (regenerated); `docs/previews/manifest.json` (regenerated).

## Open questions for Mark

1. **Edit LT04 in place, or make it a new number (LT05)?** LT04 is a day old and unpublished. I'd edit in place. A new number keeps the old rules readable in `games/`.
2. **Which mission unlocks Fire?** It is available from mission 1 today. A screen-wide blast from the start skips the lesson.
3. **Does Heavy stay as is?** With Fire taking the big-blast role, Heavy and Fire overlap unless Heavy is trimmed or dropped.
