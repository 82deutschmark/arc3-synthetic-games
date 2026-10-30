# vz11, vz13, vz15 and vz17: the VZ glow-up (15-Oct-2026)

Author: Claude Opus 5.5 Medium (overnight vz session). Built by `build_vz.py` in this folder; vz13's files sit in
`../vz13/`.

## The idea

vz01 and vz03 were colour-and-view copies of the paint-spill game: same rules, same levels, nobody had reviewed them.
The Boss asked for "some other sort of glow-up". Each one keeps its view (vz11 a quarter turn, vz13 a half turn) and
gets new levels from Son's level generator, clean colours, a visible answer when paint lands right, a real win
animation, and one twist of its own that every level needs.

- **vz11, the current.** A light striped field sits in the middle of the board. Paint falling through it is pushed one
  cell sideways for every row it falls, the way the stripes lean; it falls straight again below the field. The player
  has to place bars so the paint enters the field at the right spot, or catch it before or after.
- **vz13, the twin rings.** Two identical hollow squares. A drop of paint that lands in the middle of one comes out of
  the middle of the other and carries on falling. One ring always sits under a paint source; the player decides
  whether the paint reaches it.

- **vz15, the dye patch** (added later that night). Paint that falls through a chequered patch turns magenta and
  passes the colour on; magenta cups take only magenta paint and the others only plain paint. See `../vz15/design.md`.
- **vz17, the turning current** (added later that night). Like vz11's current, but its push turns round after every
  move and its stripes show which way it pushes now, so the spill has to be timed. See `../vz17/design.md`.

## The look

Nothing the player must read is black or grey. vz11: blue field, maroon walls and floor, green bars, a magenta chosen
bar, orange cups that turn yellow (the paint's colour) when filled, a light-blue current with white stripes. vz13: white
field, blue walls and floor, green bars, magenta chosen bar, maroon cups that turn orange (the paint's colour), purple
rings. A filled cup throws two drops up and out. A win flashes the paint and the cups and sends sparks up from every
cup before the next level.

## Levels

From `pcg/pcg/sp80.py` (Son's generator), run on this game's own rules so the twist is designed in, with three
changes made by patching it from `build_vz.py`, never copying it:

- the length target is brought down to the hand-made curve (the generator's own ran about twice as long): about 4-7
  actions on level 1 rising to about 12-15 on level 7. What came out is longer from level 2 on, because the short
  levels it found were the ones a random player could clear (see below), and those are thrown away. vz11 (seed 10):
  6, 16, 13, 13, 20, 17, 27 actions, against the hand-made 4, 7, 10 and at least 8 on the last three;
- from level 2 on every level has at least two pieces, and a level is rejected if random play clears it even once in
  1500 runs of its whole step budget (the generator's own test was too gentle for the vet);
- a level is kept only if its stored winning line wins with the twist and stops winning with the twist taken away.

Level 1 is the gentle one: a long step budget and no limit on spills, so random play cannot lose it (the vet asks
this; the original loses any random player on level 1 because of its budget and five-spill limit).

## Checks run

1. The generator's own: every level's line replayed through the real engine; random play does not clear it.
2. The twist is needed: every level's line stops winning when the twist is removed (inside the generator).
3. The whole trace, turned into screen moves for the view, replayed through the finished single file: WIN.
4. `scripts/vet_game.py --profile glowup`, once per game. Results are in the status file.
