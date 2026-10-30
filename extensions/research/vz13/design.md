# vz13: twin rings (glow-up of vz03, 15-Oct-2026)

Author: Claude Opus 5.5 Medium (overnight vz session). Built by `../vz11/build_vz.py vz13 4`; the full write-up for
both VZ glow-ups is `../vz11/design.md`.

The paint-spill game, shown upside down as vz03 was, with new generated levels, clean colours (white field, blue walls
and floor, green bars, magenta chosen bar, maroon cups that turn orange when filled), a splash when a cup fills, a win
animation, and its own twist: two identical purple rings. Paint that drops into the middle of one comes out of the
middle of the other and carries on. One ring always sits under a paint source; every level's winning line stops
winning if the rings are taken away.

Solution lengths by level (seed 4): 6, 11, 12, 12, 14, 9, 23 actions (hand-made: 4, 7, 10, then at least 8).
Vet: pass, glow-up profile (one warning: the longest spill plays 36 frames).
