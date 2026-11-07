# Featured games: art glow-up, several passes

Author: Claude Sonnet 5.5
Date: 07-Nov-2026
Asked by: Mark Barney ("do the art on the other featured games ... really improved ... several passes ... use the sprite engine ... the quality metric is length: the same length as the ARC3 games").

## Scope

In: new art for the thirteen featured games not yet rebuilt: pt01, te01, dz01, lt03, es01, eh01, ff01, se01, bs01, wf02, st01, bl01, kt01. Each is rebuilt as a new game under a new number (pt02, te02, dz02, lt04, es02, eh02, ff02, se02, bs02, wf03, st02, bl02, kt02), because a rebuilt game gets a new id. The old files stay. The target is the public 25's weight: a few thousand lines of real art, sprite and level content, not padding.

Out: rules, levels, level order, inputs, click geometry, win and loss outcomes, move limits. They stay exactly as they are. Nothing on the play surface may speak, and nothing may hand the agent the rule.

## Architecture

Every thing on screen is a named engine sprite with layers and faces, drawn large enough to read, per `autoresearch-arena/arc3games/sprite_book.py` and the new wb03 and ss02. Each game goes through four passes by separate authors: build the scene; critique against the public games and wb03/ss02 and redraw what is weak; add variety per level and life; final polish. A shared check, `equiv.py`, plays the same random lines on the old and new file and fails if state, levels completed or offered actions ever differ.

## TODOs

1. Four art passes per game (workflow).
2. Same-rules check per game.
3. Catalog entries for the thirteen, previews, hashes, `featured` swap, validate.
4. Changelog 0.9.0, commit, push.

## Docs and changelog touchpoints

`docs/catalog.json`, `docs/previews/`, `CHANGELOG.md`, `docs/validation.json`.
