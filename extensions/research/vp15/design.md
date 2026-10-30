# vp15 design (Claude Sonnet 5.5 High, 15-Oct-2026)

New: an arrow tilts the whole board (it shifts one pixel and a pink line lights on that edge) and the avatar slides one
cell per frame until a wall, a closed lock (it stops in the cell before; with the matching key it enters and opens it),
a pusher cell (the throw works as before) or the board edge. Every changer passed applies in order, refills are
collected, moving changers step once per action, and each action costs one step. The last frame settles the board
back. The rule is borrowed from the sliding game (a block slides until it hits something); no code is copied.
Winnability: every level was searched over a model of the slide (breadth-first, least stoppers first) and each
winning line was replayed through the real engine; those lines are the trace (5, 13, 13, 34, 32, 48, 24 arrow
presses). Stopper wall cells added: level 1 one, level 2 one, level 3 four, level 4 two, level 5 two, level 6 three,
level 7 two. Levels 3 and 5 could not be won by stoppers alone (a throw line left no room for a stopper), so one wall was
opened in each: level 3 the wall at column 3 row 8, level 5 the wall at column 5 row 1. Level 1 costs no steps (the vetting gate
wants a first level that cannot be lost). Checks: the stored lines clear all seven levels; with sliding turned off (the
slide length set to one) none of them clears; vet glowup PASS (one warning: the longest action plays 25 frames).

## 18-Oct-2026 dead-end fixes (Claude Opus 5.5 High)

The Boss (18-Oct, on vp15@045db474f8cc): "It might be possible for the player to get stuck in an unwinnable state on
level 4 or 5 onwards." deadend_vp15.py walked every position of every level (cell, key, track phase, cubes taken,
locks, bar) under the slide model, after checking the model against the engine on about forty thousand random
presses, and marked each position from which the exit can no longer be reached. Two kinds mattered: pockets with
no way back even with a bottomless bar (levels 3, 4, 7), and positions where the bar is full yet the cubes left
cannot carry the rest of the route (levels 5, 6, 7). Fixes, found by fix_search_vp15.py and refill_fix_vp15.py and
kept in fixes18.json (raw board columns; the screen shows them mirrored): level 3 walls at (1,7) and (4,6), wall
(9,4) opened; level 4 wall (6,7) opened; level 5 step cost 2 -> 1; level 6 a fourth recharge cube at (10,8), wall
(8,2) opened, wall at (10,2); level 7 wall at (9,2), wall (4,4) opened, step cost 2 -> 1. Level 2 also lost its stray
off-grid wall piece at pixel (54,34) (drawn solid, walked through), found by vp13's path-versus-picture check
(check_path_vs_picture_vp15.py runs it on this mirrored view). After: no such position on any level
(deadend_after_fix.json; before: deadend_before_fix.json). Trace: 5, 13, 13, 25, 32, 40, 24 presses (trace18_vp15.py).
