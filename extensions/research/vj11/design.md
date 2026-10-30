# vj11: the walker (glow-up of vj01)

Author: Claude Sonnet 5.5 High, 15-October-2026.

New: a pink walker with a face that ACTION1-4 move one cell over floor and track cells. Walls (purple blocks), buttons, pieces and frames of another colour refuse it with a one-pixel nudge; track cells cannot be walked along (a track is ridden: when its track turns the walker rides along with its cell), and it has its own pink frame; a level clears only when the walker is home too. Level 1 is unchanged (no walker). From level 2 the frame sits in a walled pocket whose one door is a track cell, so the walker must ride before it walks; levels 4 and 7 need two separate rides (a short walled corridor between two tracks). Arrow moves cost no budget. Shared pass: shown colours (blue board, light blue track cells, pink buttons with a thin "<" for L and a solid ">" for R, hollow frames in the colour of the piece they want, green and red budget bar, white and maroon level dots, black margin only), a four-frame swell when a piece lands in its own frame, a 20-frame win on levels one and two (each piece pulses, then a sweep) and 10 frames later. Budgets: level 1 is loose (30) so random play cannot lose it; later levels are the winning line plus about a third.
The one check run: the stored line with its arrow moves removed fails levels 2 to 8 (walker not home); the one vet pass is PASS.
Built by build/build_vj.py (shared with vj13, vj15, vj17); walker placement by build/design_walker.py reusing each level's existing winning line.

## 18-October-2026 revision (Claude Opus 5.5 High), after the Boss's review of vj11@e7ff8c192c0b

Published as vj11@370f0cca1708. The rules, the walker and level order are unchanged. What changed, all behind the
builder's TIDY flag (vj11 only; vj13 and vj17 build exactly as before):
- HUD: the level dots (left, three pixels each) and the budget bar (right) share the top row of the picture. No board
  reaches that row: level 1 (grid 32x19 to 31x19) and level 8 (63x63 to 62x63) each lose an empty grid column, which
  is the top or bottom row of the picture after the quarter turn. build/tidy_vj11.json holds the trims.
- Buttons: the control copy's solid shapes, grey for L and purple for R (was pink with white chevrons). Every button
  keeps a free grid unit from every other sprite and from the board edge: build/tidy_vj11.py moved four buttons
  (level 1's bottom button, level 3's two touching pairs, level 4's button on the orange frame) and
  build/design_walker.py moved three more on level 4 to give the walker's pocket room.
- Walker: a solid green square with a green frame, maroon walls; no pink anywhere (checked on every frame of the
  winning line). The pockets now keep a free unit from every button (levels 2 and 6 re-placed; level 4 kept with the
  three button moves; the rest unchanged).
- Every press flashes the tiles of the tracks it turned white on the press's own frame and rings the pieces and the
  walker on them (three frames), so a press that shifts identical tiles still shows its track.
- Budgets: twice the line's presses (16, 32, 28, 22, 38, 28, 40 for levels 2 to 8; level 1 stays 30). The vet's
  random player still clears none of levels 2 to 8.
- Checks: every press on every level changes the picture; nothing touches a button or the HUD; the HUD covers no
  board pixel; the trace wins all eight in the engine; on levels 2 to 8 the presses alone do not win and walking
  alone cannot reach home. Vet PASS (vj11.vet.json). Strips: strips/L1.png to L8.png from build/strips.py.
Rebuild order: tidy_vj11.py, design_walker.py, build_vj.py vj11, strips.py, then one vet pass.
