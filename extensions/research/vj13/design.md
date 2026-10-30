# vj13: the junction levels (glow-up of vj03)

## 18-Oct-2026 revision (Claude Opus 5.5 High), after the Boss's review

The Boss: "Level 2 is far too difficult because it doesn't allow enough exploration and then level 3 is far too
easy." Level 2 allowed 11 presses for an 8-press line (3 to spare); level 3 allowed 11 for an 8-press line, one ring
change, and random play cleared it far more often than level 2. What changed:
- Level 2's budget is 16 (twice its line). Nothing else on the level changed.
- Level 3 is new: three rings in a V. The first and second share one purple junction cell, the second and third
  another. The yellow piece starts in the far top corner of the first ring and its frame is on the top row of the
  third, so it changes rings twice. Shortest line 12 presses, budget 24. The board is still drawn at twice size.
- Every press flashes the tracks it turned (tiles white for a frame, pieces ringed), and the budget bar and level dots
  only paint margin or plain board (as in vj15). Levels 1 and 4 to 9 and their budgets are unchanged.
Built by build/ (vj13's own copy of the vj15 builder): build/retune.py writes the design, rebuilds vj13.py and records
the trace; build/strips.py draws one strip per level.

## 15-Oct-2026 first version


Author: Claude Sonnet 5.5 High, 15-October-2026.

New: a level inserted after level two (the old levels three to eight are now four to nine). Two rings touch at one cell, marked by a fixed purple box; the yellow piece starts on one ring only and its frame is on the other ring only, so the player turns the first ring until the piece sits on the purple cell, then turns the second ring to carry it round to the frame. The game's own move code already carries "whatever stands on the cell" for every track that cell belongs to, so a cell numbered in two tracks is a junction with no rule change (probed: the piece moves with whichever ring turns). No harder level was added at the end.
Shared pass as in vj11: shown colours, landing swell, 20-frame win on levels one and two and 10 later; the seven old levels use their shortest lines (found by search) with budgets of the line plus about a third; level 1 is loose (150) so random play cannot lose it.
The one check run: on the new level the piece and its frame share only the junction cell, so no line that skips the junction can win; the one vet pass is PASS. Built by build/build_vj.py and build/design_vj13.py (in the vj11 folder).
