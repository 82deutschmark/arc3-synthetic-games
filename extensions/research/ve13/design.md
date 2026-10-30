# ve13 design: the mirror stamp (Claude Opus 5.5 High, 18-Oct-2026)

Parent ve13@99556028667e (the 15-Oct glow-up of a cn04 control copy, renamed from vc13). Published:
**ve13@33e9bc4b0cf3** (vet PASS, glowup profile; ve13.vet.json).

The Boss, 18-Oct: "It's just another box around the game. We could do better."

## The twist

The game is unchanged underneath: click a piece to hold it, arrows move it, ACTION5 turns it, and a level is won
when every connector dot sits on exactly one dot of its own (hidden) kind. New: black bow-tie stamps printed on the
board, two cells by two. Slide the piece you hold onto a stamp (an arrow move that makes one of its drawn cells
cover a stamp cell it did not cover before) and it flips into its mirror image, left to right, where it stands,
with a three-frame flip (dots, half the body, all of it). Turning can never make a mirror image, so a piece that
starts mirrored can only be fixed by steering it across a stamp, and crossing a stamp by accident flips a piece
that was right. The player plans a route through a stamp to make the piece that fits.

## Why every level needs it

Each level was made backwards from a finished picture (Son's cn04 generator), and one piece (two on levels 6 and
7) starts as its mirror image; the piece is lopsided in its line drawing (not only in where its dots sit), so the
flip is a visible change of shape. The fit search was run, to the end, over the pieces as they start with turns
only: no level has any fit without mirroring. And each level's recorded line was played on a copy with the stamps
taken away: none clears. On level 1 (two pieces) either piece can be the one you flip: flipping the other gives
the mirror image of the whole picture, which fits as well. The recorded line flips the second piece; a level-one
partner whose flip changes nothing (its mirror image one of its turns) would let the mirrored picture fit with no
stamp at all, so with two pieces "flip one of them" is the lesson.

## Levels

Seven, all new (gen_ve13.py, seed 18): 15, 22, 30, 32, 34, 35, 42 moves; level 1 has two pieces and one stamp,
levels 2-3 three pieces, 4-5 four, 6-7 five pieces and two stamps. From level 3 the pieces you are not holding are
white and their dots hidden until matched (the copy's own rule). Budgets: level 1 400 (random play cannot run it
dry), the others twice the line plus room.

## Look

Board blue; every piece purple; the held piece light blue in a thin yellow frame (it was a pink outline); dots
orange, green once paired; a matching landing flashes white (yellow where the pieces not held are white); a
mismatched landing flashes black (it was red). No pink, magenta or red anywhere: checked over every frame of the
trace and of random play on every level.

## Files

- `build_ve13.py`: the rule edits on the published copy, and the levels written into the source.
- `gen_ve13.py`: `make` (levels, lines) and `trace` (replays in ve13.py, writes ve13.trace.json, re-checks that no
  level clears without the stamps).
- `strips_ve13.py`: strips/L<n>.png per level (start, the flip, the last picture); the gate's own strips are beside.
- `levels_ve13.json`, `lines_ve13.json`: the levels and their raw lines.
