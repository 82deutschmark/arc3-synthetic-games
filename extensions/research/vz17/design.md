# vz17: the turning current (glow-up of vz07, 15-Oct-2026)

Author: Claude Opus 5.5 Medium (overnight vz session). Built by `../vz11/build_vz.py vz17 2`; the full write-up for
the VZ glow-ups is `../vz11/design.md`.

The paint-spill game, mirrored on the diagonal as vz07 was, with new generated levels, clean colours (yellow field,
maroon walls and floor, green bars, magenta chosen bar, purple cups, blue paint), a splash when a cup fills, a win
animation, and its own twist, as66's always-changing direction: an orange field with white stripes pushes falling
paint one cell sideways per row, and its push turns round after every move (a slide or a click; not a spill). The
stripes are redrawn each move to lean the way it pushes now, so the player times the spill, wasting a move (a click
on empty space) when the field leans the wrong way. Every level's winning line stops winning both without the field
and with a field that never turns.

Solution lengths by level (seed 2): 6, 10, 14, 18, 12, 14, 16 actions (hand-made: 4, 7, 10, then at least 8).
Vet: pass, glow-up profile.
