# vz15, third pass: a failed spill no longer looks won (18-Oct-2026)

Author: Claude Opus 5.5 High. Parent vz15@9f0ac81d18f7 (the 15-Oct colour pass below). Published vz15@2e57e92527ab.

The Boss, 18-Oct: "I won and apparently the level didn't change. This one might be broken." He had filled both cups
on level one. The rule the game enforces, inherited from the original, is that a spill fails if any paint reaches
the floor, and on level one six of the bar layouts fill both cups with the right paint and also splash the floor.
The picture said "won": the cups stayed drawn full (yellow) and the floor lit up yellow too, the very colour of a
full cup, for a few frames before everything reset. The win itself was fine (short animation, the level does change).

Changed: paint on the floor turns the floor white and every cup white at once (white is the game's one failure
colour) and those cups stay white for the rest of the spill whatever lands in them; the floor's fail flash is white;
the splash and win sparks and the win flash are yellow, so white never appears on a win. The step bar at the top
rounds down, so it shortens on level one's first step too. Rules, levels and the trace are unchanged.

Checked: check_picture_vs_count.py walks every reachable bar layout on all seven levels and pours at each: no layout
draws every cup full without the level advancing (the parent had hundreds), and the winning layouts per level are
the parent's exactly. Vet (vz15.vet.json, three seeds): every check passes except the level-one length rule, the
standing bypass. Strips: strips/L1-win-12f.png and strips/L1-floor-spill-fails-13f.png; the vet's own strips beside.

---

# vz15, second pass: new colours (15-Oct-2026)

Author: Claude Fable 5.1 Low. Parent vz15@f87ace5a4dec (the overnight glow-up, design in `../vz15/design.md`).

The Boss: "I don't like all the pink and magenta, how it's used, and the red. It's just not really used well."
Only the view palette changed. The dye, dyed paint and the cups that want dyed paint are purple; the dye patch is
a purple-and-white chequer; a cup that gets the wrong paint, and the fail flash, turn white; pink is kept for one
thing only, the chosen bar (the same accent the other vz games use); red is gone. Plain cups stay maroon, bars
green, paint orange, the field light blue. Rules, levels and the trace are unchanged. Check run: trace replay to
WIN, then one vet.
