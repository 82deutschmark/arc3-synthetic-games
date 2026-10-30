# ve15 design: the wind (Claude Opus 5.5 High, 18-Oct-2026)

Parent ve15@375427d6ba41 (the 15-Oct glow-up of a cn04 control copy, renamed from vc15). Published:
**ve15@8ed0290b8fa0** (vet PASS, glowup profile; ve15.vet.json).

The Boss, 18-Oct: "You're drawing a pink box around the puzzle piece but this isn't really a change. You could change
the shape of the puzzle piece or do something more creative."

## The twist

The game underneath is unchanged (hold a piece, move it, turn it, join every dot to one of its kind). New: each level
has a wind, shown by a row of small light-blue arrows along the edge it blows from. Every time you move or turn the
piece you hold, every other piece drifts one cell with the wind, unless the board's edge stops it. A piece you let
go of slides to the far wall. So the picture has to be built against that wall, with every piece but one touching
it, and the one that sticks out has to be placed last, after the others have settled; and every piece has to be
dropped in the right lane across the wind, because the wind, not you, brings it to the wall. You think a move or two
ahead: where a piece will end up once you let it go.

(The brief's idea was "the dots drift"; the dots are part of the pieces, so here the pieces drift, which is the same
idea drawn so it reads: you watch them slide.)

## Why every level needs it

Each level is a finished picture (Son's cn04 generator) with a wind; a level is kept only if one of its fits stands
with all pieces but one against the wind's wall, and its line is built on that (drop each piece in its lane, let the
wind take it, place the last). Every recorded line was then played on a copy with no wind: none clears, because
without the wind the pieces let go never reach the wall. What that check proves is about the line, not the level:
with the wind switched off each level is an ordinary puzzle of the original game, which another line can win (the
wind adds a constraint, it does not unlock anything). ve13's check is stronger (no fit exists at all without a
stamp). Here the wind is what decides how the level must be played: against the wall, last piece last.

## Levels

Seven, all new (gen_ve15.py, seed 18): 13, 17, 18, 29, 28, 41, 44 moves; 2, 3, 3, 4, 4, 5, 5 pieces. Winds as the
player sees them (the view is mirrored left-right): levels 1-3 up, 4 left, 5 down, 6 right, 7 left. From level 3
the pieces you are not holding are purple with their dots hidden until matched (the copy's own rule). Budgets: level
1 400, the others twice the line plus room.

## Look

Board black; pieces white; the held piece light blue in a thin yellow frame (it was pink); pieces not held from
level 3 purple (they were maroon, which reads as red); dots orange, green once paired; a matching landing flashes
white, a mismatched one light grey (it was red). The view layer's colour for the dots (raw 8) was moved from yellow
to orange so the frame is the only yellow. No pink, magenta, red or maroon anywhere: checked over every frame of the
trace and of random play on every level.

## Files

- `build_ve15.py`: the rule edits on the published copy, and the levels written into the source.
- `gen_ve15.py`: `make` (levels and lines) and `trace` (replays in ve15.py, writes ve15.trace.json, re-checks that no
  level clears without the wind). It reuses ../ve13/gen_ve13.py for the pictures and the fit search.
- strips/L<n>.png (../ve13/strips_ve13.py): each level's start, the pictures after its first five moves (the drift),
  and its last picture; the gate's own strips are beside.
