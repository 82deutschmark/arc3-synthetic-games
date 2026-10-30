# vj15: the space track (glow-up of vj05)

## 19-Oct-2026 revision (Claude Opus 5.5 High), after the Boss's third review

The Boss: "Again very unclear what the space bar is meant to do, and the mechanics on level 2 seem broken. A lot of
these levels are just exactly like the original. They need to use the level generator." What changed:
- Level 1 teaches the spacebar: one ring, drawn with the purple rim, a yellow piece on it two cells past its frame.
  Its two buttons are hidden and cannot be pressed until the first spacebar press; that press turns the rimmed ring
  under the piece and the buttons pop in (a white box, then a pink one). Then three presses of the back button bring
  the piece home. Four moves.
- Levels 2-8 come from Son's generator (arc-3 pcg/pcg/lp85.py): generator level k of seeds 265, 13, 15, 5, 4, 4, 1.
  On each, one track (B, C, B, C, C, B, C) loses its buttons, gets the rim and turns only with the spacebar; it was
  kept only when the level cannot be won without it. Shortest lines 10, 12, 14, 15, 16, 15, 19; budgets twice that.
- Patterned tiles, the press flash, and the edge budget bar as before.

## 18-Oct-2026 evening revision (Claude Opus 5.5 High), after the Boss's second review

The Boss: "It's not clear what the spacebar is doing in this game and it just seems like the buttons are broken on
level 2." Turning every track at once moved rows of identical tiles, so the spacebar looked like nothing; level 2's
top pair of buttons turned a row with no piece and identical tiles, so it looked broken. What changed:
- The spacebar (ACTION5) turns one track only: the level's space track, drawn with a purple rim and carrying no
  buttons. On level 1 the one ring is rimmed too (it keeps its buttons) so the first spacebar press shows the rimmed
  ring turning under the piece. The purple corner marks are gone.
- Every track's tiles are patterned: every third tile white, the rest light blue, adjusted so no track is all alike.
  Any turn therefore visibly shifts the pattern, and the white flash still follows each press.
- Every level re-solved for the new rule (build/retune.py holds the picks): space tracks A, A, B, B, B, 25, C, D for
  levels 1-8; extra yellow pieces and frames on levels 3, 4, 5, 7 (two) and 8, chosen so random play cannot clear
  them; budgets twice the shortest line (level 1 stays 150).

## 18-Oct-2026 revision (Claude Opus 5.5 High), after the Boss's review

The Boss: buttons drawn over things, buttons that do not work, levels that look unwinnable. What changed:
- The budget pie is gone. On the tall levels (4, 5, 6, 8) it was painted on the board, and on level 5 over the left
  button. The budget is the plain one-pixel bar down the left edge (green left, red spent), as in the other glow-ups,
  and the bar and the level dots now only paint margin or plain board, never a tile, piece, frame or button.
- Every press shows what it turned: the tiles of each turned track flash white for a frame and the pieces on it get a
  ring (three frames). A press that only shifted identical tiles (level 2's and level 5's top buttons, level 7's short
  track) used to change nothing on screen but the budget. ACTION5 flashes every track.
- Budgets are about twice the shortest line (level 1 stays 150): 28, 42, 30, 30, 26, 32, 28 for levels 2 to 8, against
  15, 30, 19, 27, 15, 11, 20 before. Level 5 (line 20) and level 3 (line 22) are held near one and a half and two by
  random play, which clears them above that.
- Level 7 is rebuilt: its seven-press line could not get any room without random play clearing it. Track A (the long
  one) now has no buttons and the purple marks, D keeps its buttons, and two extra yellow pieces and frames make the
  line sixteen presses.
- Every track with no buttons carries the purple marks (level 7's track C moved under ACTION5 without them).
Built by build/ (vj15's own copy of the VJ builder, so the fix cannot change vj11, vj13 or vj17): build/retune.py
sets the design, rebuilds vj15.py and records the trace; build/strips.py draws one strip per level.

## 15-Oct-2026 first version


Author: Claude Sonnet 5.5 High, 15-October-2026.

New: (a) the budget is an 11-pixel pie in the top-left corner, full green, losing a wedge clockwise (maroon) with every press; empty means lost. (b) ACTION5 turns every track one step forward (clockwise on a ring) at once, tracks taken in name order, with a short ripple round each piece (three frames); it costs one press. From level 2, one track per level (two in the big sixth level, where tracks share cells) has no buttons and carries purple corner marks; its pieces can only move with ACTION5, which also turns the other tracks, and the player puts those right with their buttons. Levels where the line would have been nearly all ACTION5 presses (so random play could stumble into it) got one extra yellow piece and frame, found by search, so the line is mostly button presses (levels 2, 3, 4, 5 and 7). `available_actions` is 5 and 6.
Shared pass as in vj11 (shown colours, landing swell, 20-frame win on levels one and two and 10 later). Budgets: the line plus about a third, never under 11 (so a random player cannot die in its first ten actions); level 1 is loose (150).
The one check run: with every ACTION5 removed from the stored lines, levels 2 to 8 all fail; the one vet pass is PASS. Built by build/build_vj.py and build/design_vj15.py (in the vj11 folder).
