# CB01: a small card battler in the style of Clash Royale (plan only, nothing built yet)

Author: Claude Sonnet 5.5 (plan revised after a four-design comparison and a three-judge review)
Date: 08-Nov-2026
Asked by: Mark Barney. First "mechanics similar to the original Clash Royale", then "nothing too crazy, a plan first", then
a steer: keep the core loop, slow units that go for towers, win by taking down the THREE enemy towers, no numeric timer
(maybe a circle losing slices), action button cycles the hand, click deploys, and each level teaches one thing the way
Clash Royale's tutorial does. No game code exists yet. Building waits for the Boss's go-ahead.

## Feasibility, short

Yes. The engine is turn based and deterministic, which suits a small tower-push game. Clash Royale's real-time rush
becomes a step-by-step push you watch play out. What is kept: choosing a card, choosing where it goes, then watching
slow units do their own thing against towers. What is lost: thumb speed. This will feel more like a tactics puzzle
than the phone game, and that is the one real risk to the fun. A paper mock of the picture should be checked first.

## The four ways to do the clock (the Boss asked for options)

1. **Beat Wheel. Time moves only when you drop a card.** Cycling cards is free. Each drop lets the world play one beat
   (units walk, fight, towers shoot) and one slice of the wheel goes dark for good. Plain, nothing moves while you think.
2. **Every-Press Clock.** Every input, even flipping through the hand, costs time. Pressure is real, but a newcomer
   pays for simply looking at their hand, and flipping cards becomes a hidden wait button.
3. **Pour Clock.** The wheel doubles as the elixir: each beat a slice pours into a meter you spend on cards. Elegant
   and most like Clash Royale, but two gauges moving together are hard to tell apart on a 64 by 64 picture, and waiting
   has to be discovered.
4. **Patience Ring.** The enemy plays a fixed list of cards and the ring shows how many it has left. Charming, but a
   newcomer reads the ring as tower health, and showing the whole future makes each level solve-once.

All three reviewers (a first-time player, an AI that must struggle, and a game producer) ranked **Beat Wheel** first and
agreed on the grafts below. That is the recommendation.

## Recommended design: Beat Wheel, with grafts

- **Field.** Three enemy towers across the top, each with a few health pips. A bright band across the bottom third is
  where you may drop units. A hand of unit pictures along the very bottom, the chosen one raised and framed.
- **Controls.** Action 5 flips to the next card in the hand (free, nothing else moves). A click inside the band drops the
  chosen card there. A click outside the band does nothing and costs nothing, but the band flashes so a cold player
  learns where legal ground is. The first card is already selected, so the first thing a person discovers is the click.
  The second card appearing in level two is what teaches action 5.
- **Units walk straight to the nearest tower, slowly.** So the column you click decides which tower you hit.
- **The clock.** A round wheel of eight slices, each with two shades, so sixteen readable steps. One shade goes dark at
  the end of every beat and never comes back. The next one to go blinks first, so a loss never comes as a surprise.
  No numbers, no words. Tight levels start with some slices already dark.
- **One drop = one round of play**, a few small steps of motion, so units visibly get somewhere within a few clicks. If
  the hand is empty, or you want the world to keep going, any arrow press plays one beat with no card (it costs a slice
  like any beat). Level one ends with an empty hand and the world still moving, so this is learned by doing.
- **Winning.** All three enemy towers down.
- **Losing.** The wheel goes fully dark with an enemy tower standing. It is shown: the wheel darkens, the towers flash,
  then the level restarts. Never a silent restart. From the defence level on, an enemy that reaches your edge takes a
  slice off the wheel (a leak), so no second health system is needed.
- **Undo** takes back the board and the hand but not the slice, the same as the public games. The slice flashes on undo
  so a player can see why it stayed dark. Reset restarts the level.
- **No elixir.** The hand is finite and the wheel is the only other limit. This was the main simplification: one gauge,
  one job.
- **Art.** Early-console look, flat saturated fields, no grey (rubble and dark slices stay coloured). Towers, wheel and
  four unit shapes get the most pixels: Walker small and round, Tank wide and dark, Archer thin with a visible arrow dot,
  Runner lean and leaning forward. Your side cool colours, the enemy warm. Named sprites, no text anywhere.

## Levels: one idea each, learned by the last card failing

1. **Straight to the tower.** One card, the Walker. Towers do not shoot. Teaches click-to-drop and that the column picks the tower.
2. **Towers shoot back.** A Walker dies on arrival. A second card, the Tank, soaks the shots. Teaches cycling (action 5).
3. **Out-reach them.** A guard blocks the path and a tower hits hard. The Archer shoots over it. Teaches ranged.
4. **Fast hands.** The wheel is short and the Tank is too slow; the Runner finishes the job. Teaches fast attackers.
5. **Three different towers.** One guarded, one hard-hitting, one plain, so one spammed card cannot win. Teaches mixing.
6. **The push.** An enemy shows a small marker at the top edge a beat before it arrives and walks at your side; leaks cost
   slices. Teaches defending as well as attacking. Pick leaks or own towers for this level, not both.

Each level should have two or three workable answers, not one hidden intended order.

## What this plays like, and what it does not

Like Clash Royale: choosing the right unit for the tower, units doing their own thing, tanks soaking, archers out-ranging,
a running clock, three towers to topple. Not like it: no elixir, no real-time reflexes, no free placement anywhere on the
field, no deck building, and the opponent is mostly buildings until the last level.

## Risks and how they are handled

- **Feels like a puzzle, not a battle.** Mock it on paper first and keep levels short with visible motion.
- **Hard for an AI is only moderate.** The state is small and exact, so a searcher could brute-force early levels. The
  defences are: it must discover the controls from the picture, the first obvious card is wrong at least once per level,
  slow units show mistakes many beats later, and the wheel punishes blind trial. This is honest: the hardness is
  middling and needs checking with a real solver.
- **Readability.** Eight wedges, health pips and four silhouettes in a few pixels is tight. Fallback: six wedges.
- **Action 5 as pure card selection** departs from the older rule that the fifth action must do something in the world.
  The Boss asked for it by name, so the plan follows him. It never acts as a wait: waiting is the arrow press.
- **Engine fit not yet checked.** Whether one input can play out several animated beats before control returns must be
  confirmed in the first hour of the build; if not, a drop becomes a single step and the wheel is rebalanced.
- **Vetting gate.** A winning recording is needed to pass it, or a Boss-approved bypass.

## Id

**CB01**. No existing game here uses it, and it shares no two letters with any of the 25 public games. The id is only a tag.

## Plan of work (if approved)

1. Check the engine can animate several steps per input; draw one level's picture and look at it.
2. Build `games/cb01.py`: rules as plain functions first (walk, fight, tower shots, wheel), art and engine glue last.
3. Build the six levels above; tune the wheel by playing.
4. Write a solver that searches the real engine and records a winning route per level in `solutions/`.
5. Previews (`tools/make_media.py`), catalog entry, changelog entry, `tools/validate.py`.
6. Branch and pull request. The scheduled task files it on the Games page; nothing is published by hand.
7. A plain note to the Boss: what plays like Clash Royale, what does not, what is rough.

## Docs and changelog touchpoints

`docs/catalog.json`, `docs/previews/`, `docs/validation.json`, `CHANGELOG.md`, `solutions/cb01_*.py`.
