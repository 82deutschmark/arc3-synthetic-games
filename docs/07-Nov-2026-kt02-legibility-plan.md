# KT02: make the noise mean something

Author: Claude Sonnet 5.5
Date: 07-Nov-2026
Asked by: Mark Barney (a human cannot tell if they are on the right track or what to do; an agent cannot filter noise, so every moving thing must carry meaning; no smiley faces, use a made-up script instead; change the scenery; the level 2 hint does not read).
Status: BUILT as a new game, KT03 (`games/kt03.py`), on 07-Nov-2026, after Mark's fourth reply ("obviously it needs a new ID ... whatever makes the most sense ... the edges of the screen aren't important, I lean towards bigger stuff ... the glyphs change ... get it done"). KT02 is unchanged. What follows is the plan as written; "As built" below says where the build differs.

## As built (KT03)

- **New id, KT02 untouched.** KT03 takes KT02's place in the highlighted list, as LT05 and DZ03 did.
- **Open decisions settled by the recommendation:** a good pull away from the finish is free (only wrong pulls use a pull); ramp cut-offs 1-3 / 4-6 / 7-10; edit-in-place replaced by a new id.
- **Bigger glyphs, not 4×4 corner glyphs.** Mark said the edges do not matter and to lean bigger, so the signals are glyph tiles in the open cloth instead: 12×12 px (the 5×5 glyph doubled) where a 3×3-cell gap exists, 8×8 where only 2×2 does. Four per level. They use the existing 5×5 kana set 31 from `tools/glyphs/sets/`, so the 4×4 generator work was dropped. Every level got at least four tiles; level 10 only has room for the small size.
- **The glyphs change as you go wrong.** Closed shapes in yellow when on track (purple when on the finish), broken dashes in pink when wrong (orange when stuck), open strokes in light blue after an undo and white after a blocked move. (First built in green and red; swapped for yellow and pink at Mark's call, because green and red mean different things in different cultures. The wrong cloth is pink and magenta, never purple, which means ready.) Tile k shows glyph `(first + k) % 7` of the family, so tiles differ and each state has its own shapes.
- **Mood follows what is shown.** The whole cloth turns red and dim, the two creatures swap ends and the props droop while the glyphs say wrong. Refinement of the plan's "mood stays live on every level": on levels 7-10 nothing is live, so the mood changes only after a pull (otherwise it would give away what the pull is meant to report). STUCK, the undo marker and the pulls-left rack stay live on every level.
- **Crossings.** Bars recolour by state on levels where it is live: light blue after one pass, yellow when held, pink and dashed (shape as well as colour) when doomed or failed. A pull shows the same on every level until the next input.
- **Pull.** As in I below. A pull on the finish with an unfinished crossing counts as wrong. The wave colour is the verdict; wrong crossings flash during the pull and stay marked after it.
- **No free-running motion.** The ambient drifters, the corner flowers, the idle blink, the spool shine and the cloth shimmer are gone; the creatures and props are still unless the state changes.
- **Teaching panel** replaces the old level-2 tag and picture, on levels 2 and 4 (the first of each mark): two strips, each a crossing picture beside a glyph tile. The picture the mark asks for sits beside the closed yellow glyph, the other one beside the broken pink glyph.
- **Not done or not checked:** no person has played it. The pulls-left counter is three plain white lights in the small right margin (the first build used a rack of coloured spools, which Mark found too busy); it is easy to miss if you are not looking for it. The panel's crossing pictures are subtle at 5×5. Whether the ramp cut-offs feel right is untested. The play checks were scratch scripts and are not in the repo; `solutions/kt03_clear_levels.py` is.
Revision: Mark does not want to learn the rule by losing a level. Space is now a pull that plays the cinch animation in a different colour when the knot is wrong, and the player gets three pulls (I). Early levels get live help that fades (J). The glyph generators now live in this repo under `tools/glyphs/` (see `docs/07-Nov-2026-glyph-tools-plan.md`).

## What is wrong (read from `games/kt02.py`)

1. **Every key press repaints dozens of pixels for no reason.** `self.clock` ticks on every frame, so props change frame, two walkers walk, ambient drifters drift, corner daisies turn, spools shine and the cloth shimmers (`_animate_scenery`, `_life`). A frame diff after a move says nothing about what the move did.
2. **Nothing reports crossing state.** The mark is the same before, during and after you cross it. The verdict arrives only at the pull, and the failed crossing's flash is hidden again when the animation ends (`flash.set_visible(self.cinch > 2 ...)`).
3. **Undo is invisible.** Nothing in the frame says it exists, when to use it, or where it takes you back to.
4. **The level 2 hint** (`_hint_pixels`: a strand, two dots, a bar) teaches nothing, and level 4's other mark type has none.
5. **Dead decoration looks like a counter.** The rack's spools equal `undos` but undo is unlimited. The daisies count nothing.

## Scope

In: the picture, the feedback, and two small action-meaning changes: (1) Space works anywhere, not only at the finish, and changes no cord state away from the finish, (2) a wrong pull no longer ends the run at once; the player has three pulls (see I). Out: the puzzle itself: slat layouts, start and finish cells, marks, the two-pass rule, level order, the move and undo rules. `try_step`, `failed_marks`, `build_board` and the level data stay byte-for-byte as they are. Nothing may speak: no letters or digits.

## Design

**Principle.** Everything on screen is either static, or changes only because the state changed, and the same change always means the same thing.

**A. State, worked out locally from the cord (no search, no solver).** `kt02.py` computes it from `state` each frame:
- WAITING: a marked crossing with no pass yet.
- ONE PASS: first pass laid, still can be right.
- DOOMED: the first pass used the strand that is supposed to end on top. An axis can be crossed only once per crossing, so the second pass must then be the wrong strand. This is exact, not a guess.
- HELD: both passes laid, order correct. FAILED: both laid, order wrong.
- STUCK: no legal move from here and not at the finish.
- READY: the head is on the finish and every mark holds.
- Whether the rest of the route can still reach the finish is deliberately not computed. That would be an oracle.

**B. Crossing = picture of its goal.** Each marked crossing draws the finished over/under it wants (iconic, needs no learning). It then goes through WAITING, ONE PASS (pulses), HELD (locks, bright) and DOOMED/FAILED (red, stays red until undo or RESET, including after a lost pull).

**C. A made-up script for global state, taken from the copycats glyph work.** Three generators for TR87-style glyphs, ported from the sister project `autoresearch-arena/arc3games/copycats/views` into `tools/glyphs/` (with checked-in sample sets under `tools/glyphs/sets/`), each writing seven glyphs per family as 5×5 JSON: `tr87_glyphs.py` (random straight strokes), `tr87_glyphs_cjk.py` (real CJK/Hangul/kana shrunk to 5×5) and `tr87_glyphs_kana.py` (hand-drawn katakana and hangul moved by one or two pixels so each reads as almost-a-character). All keep TR87's three families (A thin open stroke, B closed shape with a hole, C broken dashes), keep every new glyph far from the original 21 under any turn or mirror, and drop exact Latin letters and digits. Reuse the kana-nudge set (closest to "looks like a character but isn't").
- **The family carries the meaning, the shape is a permutation.** B (closed) = HELD / ON TRACK, C (broken) = WRONG / FAILED, A (open stroke) = WAITING / ONE PASS. Within a family any glyph means the same thing, so a level can use its own permutation and still read.
- Signals needed: ON TRACK, WRONG, STUCK, READY, UNDO USED, BLOCKED. Colour and shape both differ.
- **Size is the catch.** The set is 5×5; KT02's cells and margins are 4 px. Either add a size parameter to the generators (they hard-code 5 through `SIZE` and the family rules, so this needs an eyeball check) or put 5×5 plates in open cloth (position varies by level). Recommend 4×4 for the corners and crossings.
- Shown in the cloth corner cells now holding the daisies, so the same signal sits in every corner. Signals sit on a dark plate in solid colour. Any decorative glyph in the scenery is tone-on-tone with the cloth and never on a plate, so the two cannot be confused.

**D. Undo made visible.**
- A marker sits on the cell undo would return to. It is faint normally and bright while WRONG or STUCK.
- The UNDO USED glyph flashes and the removed cord flashes as it retracts.
- Level 1 has a dead-end spur (cells (8,4) and (9,4)), so it teaches undo through STUCK without any new level.

**E. Characters and mood.**
- Walkers stop free-running. They stand at the left or top end while ON TRACK, and when WRONG or STUCK they move to the opposite side and take the existing `grieved` palette (red/dim). Props do the same. No faces carry meaning.
- When WRONG, the hem turns to the existing red cloth. The full veil stays for GAME OVER only, so the two read differently.
- Ambient drifters and the cloth shimmer: removed, or made static. Daisies are replaced by the glyphs.

**F. Rack becomes the pulls counter.** Three spools, one dulled by each wrong pull (see I). They stop shining on the clock and change only when a pull is used or on RESET. This replaces the inert spools that today look like a counter and count nothing.

**G. Teaching.** The level 2 tag is replaced by a small two-entry dictionary panel in TR87's style: tile of "across, then down" next to the tile of the HELD crossing, and the reverse next to the DOOMED one. Level 4 gets the same panel for the other mark. If a playtest still fails, add a smaller level 2, which would be a separate decision because it changes the levels.

**H. Scenery change.** New per-level prop sets replacing the face-props, chosen to stay out of the glyph colours (black and the signal colours are reserved). Optional tone-on-tone glyph embroidery per level, one permutation each.

**I. Pull (Space) and three pulls.** Mark, 07-Nov-2026: the pull plays the animation it plays now, in a different colour when it was done the wrong way; the player gets three pulls.
- Space is a pull wherever the head is. The cord tightens from the head back along the route, as at the finish today. The colour of the wave is the verdict: purple when nothing is wrong, a different colour (the existing magenta wave) when something is. Each wrong crossing is also marked in its own colour on the settled frame until the next input, because an agent may only see that frame.
- "Wrong" is a crossing that is DOOMED or FAILED (A). Away from the finish, a crossing nobody has crossed yet is not wrong. At the finish an unfinished crossing is wrong, because the knot would not hold.
- A good pull at the finish clears the level, as now. A good pull anywhere else shows the good colour and changes nothing.
- A pull changes no cord state and writes no history entry, so undo does not undo it.
- Three pulls per attempt, shown by the rack (F). Each wrong pull uses one up. The third wrong pull ends the run (GAME_OVER with the red veil, as now). RESET restores all three.
- Level 1 has no marked crossings: a pull away from the finish shows the good colour; at the finish it clears the level.
- Open question, see Decisions: whether a good pull away from the finish also costs one.

**J. Difficulty ramp (cut-offs are my guess).** Live help fades; the pull stays on every level.
- Levels 1-3: live crossing states and corner glyphs, including DOOMED on the first pass.
- Levels 4-6: live HELD / FAILED once both passes are laid, no first-pass DOOMED.
- Levels 7-10: no live crossing state; the pull is the only feedback on the crossings.
- STUCK, the undo marker, the pulls-left rack and the mood of the scenery stay live on every level.

## Reuse

`lost_cloth`, `grieved`, `_spark`, the head and glide code and `_slat` stay. Glyph pixels use the existing `paint()` text-row format. No new modules; new builders go in `kt02.py` next to `_crossing` and `_daisy`.

## TODOs

1. Pick the glyph set from `tools/glyphs/` (kana-nudge, 4×4 variant if feasible), view the sheet, choose six to eight glyphs across the three families, and check by script that no two are equal under any turn or mirror.
2. Add the pure state functions (A) and unit-check them against hand-worked boards, including the first-pass DOOMED case on levels 2, 4, 5 and 7. Add the three-pull logic to `step()` and check that a pull away from the finish leaves `state`, `history` and the level index unchanged, that the third wrong pull is GAME_OVER, and that RESET restores three.
3. Crossing sprites (B), glyph corners (C), undo marker and flash (D).
4. Mood for walkers, props, hem (E); stop free-running motion; pulls-left rack (F).
5. Dictionary panels (G); new scenery (H).
6. Play levels 1 to 10 through `tools/runtime.py`: win each, take a wrong first pass, hit a dead end, undo out, lose a pull. Confirm the frame changes only where intended (diff the frames after a no-op bump and after a move).
7. `tools/make_media.py --game KT02`, update the hash in `docs/catalog.json`, run `tools/validate.py`.

## Docs and changelog

`CHANGELOG.md` entry; `docs/catalog.json` hash and any description; README/EVALUATION unchanged unless they describe KT02's feedback. A how-to-play note goes on the browse page only, never anywhere an agent sees it.

## Decisions for Mark

All settled; see "As built" at the top. (Open questions 1 to 4 below were answered by Mark's "whatever makes the most sense" and "obviously it needs a new ID".)

Settled by Mark: DOOMED on the first pass is wanted ("learning the rule by losing the level is insanely annoying"); Space is a pull that plays the animation in a different colour when wrong; three pulls; early levels easier; glyphs come from the copycats work, now in `tools/glyphs/`.

1. Does a good pull away from the finish cost one of the three? Recommended: no, only wrong pulls use one up, so checking is free while you are right and costs when you are wrong.
2. Ramp cut-offs: 1-3 / 4-6 / 7-10 as above, or different?
3. Glyph size: add a size parameter and generate 4×4 (recommended), or 5×5 plates in open cloth?
4. Edit KT02 in place, or ship this as a new id and keep KT02 as it is? Space working anywhere and the three-pull rule change what actions do, so I lean towards a new id.
