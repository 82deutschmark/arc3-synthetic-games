# Adversarial review of the twelve featured games

Date: 5 November 2026. Reviewer: Claude Code, asked by Mark Barney to read every featured game's source as a hostile senior engineer and game designer and report what does not hold up against the games ARC Prize ships.

Scope: the twelve games in `featured` in `docs/catalog.json`, read in full (8,644 lines), plus `tools/`, `examples/`, the engine package (arcengine 0.9.3) and the catalog write-ups. Nothing was changed in any game. All numbers below come from scripts run against the real engine in this checkout; the scripts are described at the end.

## Verdict in one paragraph

The ideas are better than the games. Five of the twelve have a mechanic ARC Prize's public set does not have (shadow toppling, lantern-by-retreat, wind on the boats you are not steering, bells that herd guards, a tether that wraps). But as shipped, the set has one problem that swamps everything else: **almost nothing can be lost, and almost every level is small enough to be solved by blind search.** Ten of the twelve games never report a loss to the engine in 2,000 random actions; most of them cannot report one at all. Blind random clicking clears the first level of ten of the twelve. A one-page breadth-first search solves every level of Windy Boats, Water Flip and Bell Stealth in under a tenth of a second each, and the hardest Bell Stealth level has 757 reachable positions in total. ARC Prize's games are built so that a careless agent runs out of actions; these are built so that a careless agent gets a free retry with no signal that anything happened. Fix that one thing and the set is defensible. Leave it and "this could have been yelled into Claude Code" is a fair comment, because the hard part of an ARC game, the part that takes a person, is calibrating the cost of being wrong, and that part was skipped on every game.

## How the measurements were taken

| Check | What it does | Result |
|---|---|---|
| Repo validator | `tools/validate.py`: hash, import, reset, one action | 50 of 50 pass |
| Random probe | 2,000 uniformly random actions, 3 seeds, per game, through `tools/runtime.py` | Table A |
| Brute force | Breadth-first search over each game's own rule functions, 400,000-position cap, 8 games | Table B |
| Dead-end cost | Timing the winnability searches four games run inside play | All under 0.02 s per call |
| Art | Opening frame of every featured game | Notes per game |

### Table A. What blind random play achieves

| Game | Levels cleared, per seed | Times the engine saw GAME_OVER | ms per action | Frames per action (mean / max) |
|---|---|---|---|---|
| pt01 Perfect Target | 1, 1, 1 | 0, 0, 0 | 0.3 | 3.1 / 20 |
| te01 Tethered Extraction | 1, 0, 0 | 0, 0, 0 | 0.6 | 2.3 / 4 |
| dz01 Dig Zone | 0, 0, 0 | 0, 0, 0 | 0.8 | 2.0 / 5 |
| lt03 Lock Target | 0, 1, 1 | 0, 0, 0 | 10.4 | 6.0 / 11 |
| es01 Extreme Sneeze | 2, 2, 2 | 0, 0, 0 | 1.2 | 5.1 / 21 |
| eh01 Eroding Horizons | 2, 1, 1 | 0, 0, 0 | 0.4 | 3.5 / 23 |
| ff01 Feeding Frenzy | 0, 1, 1 | 0, 14, 14 | 0.2 | 1.1 / 14 |
| se01 Shrine Exploration | 0, 0, 0 | 0, 0, 0 | 0.2 | 3.0 / 3 |
| wb02 Windy Boats | 0, 1, 0 | 5, 5, 6 | 1.0 | 2.1 / 4 |
| bs01 Bell Stealth | 1, 1, 0 | 0, 0, 0 | 0.6 | 3.2 / 15 |
| wf02 Water Flip | 0, 0, 1 | 0, 0, 0 | 0.3 | 3.6 / 14 |
| st01 Shadow Topple | 1, 1, 1 | 0, 0, 0 | 0.5 | 4.0 / 10 |

Read the third column. Only Feeding Frenzy and Windy Boats ever tell the engine the player lost. In the other ten, dying is an animation followed by a silent level restart (pt01, dz01, eh01, bs01, st01, se01) or there is no way to die at all (wf02, se01, es01 levels 1 to 3, lt03 missions 1 to 3). ARC's harness scores on actions taken and levels completed; a game that never ends a run is a game where the only cost of a mistake is the action it took.

### Table B. Brute force: reachable positions and shortest solution

Breadth-first search over the game's own rule function, from the level's start. "Reachable" is every distinct position the search visited before it found a win.

| Game | Shortest solution, levels 1 to 8 (moves) | Reachable positions, levels 1 to 8 |
|---|---|---|
| wf02 Water Flip | 5, 12, 18, 25, 30, 39, 53, 70 | 9, 113, 285, 374, 851, 5,062, 1,120, 1,872 |
| bs01 Bell Stealth | 8, 21, 23, 27, 33, 38, 45, 50 | 94, 187, 293, 211, 240, 327, 757, 634 |
| te01 Tethered Extraction | 15, 29, 41, 43, 43, 45, 45, 73 | 188, 292, 110, 117, 146, 209, 132, 109 |
| wb02 Windy Boats | 12, 11, 15, 19, 17, 14, 19, 22 | 344, 334, 13,293, 10,443, 8,199, 8,844, 8,359, 5,670 |
| st01 Shadow Topple | 1, 12, 11, 15, 15, over cap, over cap, over cap | 3, 4,066, 2,496, 39,996, 33,261, >400k, >400k, >400k |
| pt01 Perfect Target | 6, 20, 25, 25, 28, over cap, over cap, over cap | 93, 15,314, 25,345, 25,045, 50,969, >400k, >400k, >400k |
| eh01 Eroding Horizons | 7, 16, over cap, over cap, over cap, over cap, over cap, over cap | 55, 90,745, >400k, >400k, >400k, >400k, >400k, >400k |
| dz01 Dig Zone | 13, 16, 18, over cap, over cap, over cap, over cap, over cap | 12,207, 108,915, 212,938, >400k, >400k, >400k, >400k, >400k |

"Over cap" means the search hit 400,000 distinct positions without finding a win, which says the level has real depth, not that it is unwinnable (the repo's own checks and the human records show those levels are won).

Three things to take from Table B. First, the whole of Water Flip, Bell Stealth, Tethered Extraction and Windy Boats is a few hundred to a few thousand positions per level; a solver that knows nothing about the game finishes each in milliseconds. Tethered Extraction is the surprise: all its floating-point geometry collapses to 109 to 292 positions per level, because the rover only ever stands on whole cells. The complexity is in the drawing, not in the game. ARC Prize's games are not immune to search either, but theirs are 64x64 boards with large state; a 4x4 harbour with three boats is not. Second, the levels with depth are Shadow Topple 6 to 8, Eroding Horizons 3 to 8, Perfect Target 6 to 8 and Dig Zone 4 to 8; those are the levels in this set that could stand next to a public ARC game. Third, the shortest solutions are short: Water Flip level 1 is five presses of the same button, Shadow Topple level 1 is one click, Bell Stealth level 1 is eight moves. A tutorial level is fine; a tutorial level that random clicking clears in a few hundred actions is not teaching anything, it is giving away a level-completed point.

## The problems that cut across the whole set

Ranked by how much they would embarrass the set in front of an ARC Prize designer.

### 1. Being wrong costs nothing

- pt01: dying plays a sinking animation, then `_enter()` rebuilds the level in place. `lose()` is never called. The engine, and therefore the harness, never learns a death happened.
- dz01, eh01, bs01, st01: death is an animation followed by `level_reset()`, then a line that pokes the engine's private action counter so the next RESET does not wipe progress. Four games carry the identical hack.
- se01: no loss state exists. Caught or stung, you are teleported to the last shrine. No counter, no budget.
- wf02: no loss state, no budget, no undo needed. Any order of presses eventually arrives.
- es01 levels 1 to 3 and lt03 missions 1 to 3: the lose condition is switched off by level index.
- wb02: the 240-dot allowance does produce GAME_OVER, but the override of `handle_reset` turns it into a level retry with the allowance refilled. The catalog says "running out ends the game". It does not.
- te01 and ff01 do call `lose()`, and RESET then restarts the level. These are the only two with teeth, and ff01 hands out three lives first.

ARC Prize's games generally have no explicit death either, but they are scored on action count against a human baseline, and they are deep enough that wasted actions matter. These games are shallow enough (Table B) that wasted actions do not.

### 2. Four games solve themselves for the player

st01, bs01, eh01 and dz01 run a search after every move and, when the position can no longer be won, kill the player and restart the level on the spot. From a human-interface view this is kind. From a benchmark view it is the single most generous reward signal you could give an agent: an instant, unambiguous "that move was fatal" at the exact step it happened. The agent never has to reason about dead ends, which in these four games is the entire puzzle. bs01 goes further and paints a pink chequer on every cell a guard could catch you on next turn. The game annotates its own threats. ARC Prize's games show consequences; they do not forecast them.

### 3. Hidden state the screen cannot show

ARC's founding rule is that everything needed is on the screen. Six of the twelve break it in a way a cold human would call unfair rather than clever.

- es01: five separate clocks. The alien acts on even ticks, infected people cough every fourth, gunmen every third, civilians every eighth (offset by their index), doctors every fifth. Nothing on screen shows any of them. Also the win target counts doctors and gunmen as people to infect; the catalog says so, the screen does not.
- lt03: threat timers that make an untouched target explode, a recharge counter, aid that freezes the city on alternate ticks, a sensor that goes stale every third tick from mission 7. The HUD tries to show these in a four-pixel strip with seven instruments. It is unreadable without the legend in catalog.json.
- te01: positions, cable length and blade contact are floating-point numbers (obstacles at 3.2 to 3.8, cable budget 7.8). The frame is a rounded picture of a hidden continuous state; the player cannot see exactly how much cable is left or exactly where a blade will stop them.
- ff01: predators off-screen are not marked (only edible fish are), so bites arrive from outside the window. The one-pixel yellow "next heading" tell is invisible at 64x64.
- dz01: "perched" is a boolean with no on-screen cue; a lit star makes sand digs free and also blows away the whole column above; a creature skips its punch-back on its last stripe. Three rules learned only by surprise.
- se01 and es01 and lt03 and ff01 are all scrolling worlds. ARC's public set has two scrolling games out of 25; this set has four out of twelve, and in two of them (se01, lt03) the world is 65x65 or 128x104 behind a 64-wide window.

Hidden information as the mechanic (eh01's lantern, se01's unmarked shrine-to-gate mapping) is a legitimate design. Hidden clocks and hidden floats are not; they are the game not telling the player what the rules are.

### 4. Level counts are padded

- te01: eight "stages" are four layouts. Levels 2, 3 and 5 are byte-identical geometry (3 adds a blade, 5 adds a second blade and the hood); 4 and 6 are 2 and 5 stretched by one row.
- pt01: level 8 is level 7 plus one galleon. Levels 2 and 3 are target practice against ships that cannot shoot.
- st01: levels 6 to 8 are two rooms separated by a wall; level 8's two rooms start with identical left halves.
- se01: six levels on one 65x65 map, changing only which gates are where and where the patrols walk.
- wf02 level 1 is five presses of one button. st01 level 1 is one click without turning the light. bs01 level 1 is one bell and one guard.

ARC Prize's games have fewer levels (typically 5 to 8) but each one introduces or recombines a rule. Here the count is held at eight by reuse.

### 5. Nobody has played six of them

`human` in the catalog is null for lt03, ff01, se01, wb02, bs01 and wf02. Of the six that have a record, es01 has 44 actions and one level; st01 four of eight levels; te01 seven of eight. ARC Prize's whole method is cold human testing with action counts that become the baseline. Six of your best twelve have no baseline at all, and the page says so by omission. Every game header also cites a generator or solver (gen_dig.py, assemble.py, solve2.py, ff01_gen.py, "the level solver") that is not in the repository, so the claim "levels were generated and checked" cannot be verified by anyone who clones this. `tools/validate.py` is a smoke test and says so.

### 6. The games do not know their own names

st01's class is `G014` and it reports `game_id="g014"`; bs01 is `G019`/`g019`; se01 is `Xb02`/`xb02`. Every frame these three return carries the wrong id. The catalog maps around it with `class_name`, which is why nothing crashes, but a reviewer opening `games/st01.py` reads "candidate task g014" on line 1. Three of twelve. Separately, three files (pt01, lt03, es01) have no author/date/purpose header, which your own CODING_STANDARDS.md requires of every Python file.

### 7. The controls mean something different in every game

Within one set, ACTION5 is: cycle boat (wb02), flip lever 0 only (wf02), turn the light clockwise (st01), reel the cable (te01), fire the cannon (pt01), light the lantern (eh01), spray (es01), light a star (dz01), switch munitions (lt03). ACTION7 is undo in wb02 and te01 and "wait a turn" in lt03. In wf02 lever 0 answers ACTION5 but lever 1 only answers clicks. In lt03 the munitions tray looks clickable and flashes when clicked, but clicking does not select; only ACTION5 does. ARC's public games vary too, but a set presented as one collection with one "controls" line per card should not have a second lever that silently ignores the key the first lever obeys.

### 8. The engine is used as a frame pump

Five of the twelve (ff01, st01, se01, eh01, dz01) paint the whole screen inside `RenderableUserDisplay.render_interface` and keep zero or one placeholder sprite in the level; pt01 and bs01 use real sprites and paint only lines and borders that way. That works, and it is why performance is fine. But arcengine's own tooling (the `sys_click` tags, `get_sprite_at`, `_get_valid_actions`, the hidden-state hook) exists so ARC's graph builder can see what is on the board. A game with no sprites is invisible to it. st01 is the only one of the five that bothered to tag an invisible board sprite so clicks are discoverable.

### 9. Theme

es01 (spread an outbreak through a city) and lt03 (air strikes that kill schoolchildren and ambulance crews) will not be touched by ARC Prize or by most labs that would otherwise train on this set, whatever the mechanics are worth. The catalog highlights that "we hit no guardrails" building them. That is not a feature of the games; it narrows who can use them. lt03 is the richest simulation in the set and it is wearing the theme most likely to keep it out of any benchmark.

### 10. Code hygiene

Not the main event, but a senior engineer would flag these in a review:

- Dead parameters and fields: se01 stores an `order` list per level that no rule reads; lt03 computes `time_limit` per mission and never checks it; st01's `sun0` is 0 in every level; eh01's `_build(..., before)` is always None and `_cell_center_px` is unused.
- Crash paths inside the ARC server: te01's `tighten()` raises `ValueError` if its own invariant fails; bs01's `analyse()` raises at level load if a level has more than 60,000 states or is unwinnable.
- Module-global caches that grow for the life of the process and are shared between game instances: st01 `_WINNABLE`, bs01 `_LIVE` and `_MODELS`, pt01 `_LAND_CACHE`.
- Four copies of the same hack: `self._action_count = max(1, self._action_count)` after a level reset, in st01, eh01, bs01, dz01. It exists because the engine's default RESET does a full reset when the action count is zero; the fix belongs in one override of `handle_reset`, which te01 and eh01 already have.
- Two styles stitched in one file: te01 has `move(level, state, direction)` next to `plan_step(level,state,direction)`; es01 and lt03 chain statements with semicolons and use one-letter names; wb02 mixes both. pt01 has 13 lines over 120 columns, es01 14.
- Fragile init order: wb02, ff01, pt01, dz01 set attributes before `super().__init__` because the base constructor calls `on_set_level`. Works, undocumented, and `ff01` and `pt01` pass `debug`, `win_score` and `available_actions` positionally.
- Header cruft: "the Boss", "NT80 revision", internal commit hashes, CHANGELOG paragraphs about art arguments. A public source file is not a chat log.

## Game by game, best to worst as an ARC task

### 1. eh01 Eroding Horizons (744 lines)

The best idea in the set. Walking shows nothing; stepping back lights the cell you left and burns one of its two marks; a cell with no marks is gone. That is a real information-cost mechanic and it is yours. Mark called it "probably a perfect training game" and the human record (836 actions, all 8 levels) says it was actually played.

What is wrong: the dead-end detector (problem 2) does the hard thinking for the agent. The board is 7x6 and level 1 has no marks at all. Winning needs a non-obvious triple step (stand on the ring, step back to light it, step on again), which is consistent but nowhere hinted. Code references a `solve2.py` audit that is not here.

Fix: remove the auto-death, keep the scar rule, and let an agent that burns its way home sit in the dead position until it resets. Add a tiny counter of marks burned so the budget is visible. Three more boards at 9x7.

### 2. bs01 Bell Stealth (809 lines)

Cleanest code of the twelve: pure rules, real sprites, a tile cache, levels validated at load. The idea (ring bells to herd guards onto plates, loads flow downhill between adjacent guards) is good.

What is wrong: the pink danger chequer and the instant death on any unwinnable position make it close to self-solving. 757 reachable positions in the hardest level. The downhill-flow rule (load plus height difference of two or more) is numeric and has no cue beyond die pips. `analyse()` can raise at level entry. Reports itself as g019.

Fix: drop the danger overlay and the auto-death. Double the board to 12x12 or add a second guard type. Rename the class.

### 3. st01 Shadow Topple (632 lines)

A novel rule (the shadow is the landing footprint; it runs longer over holes) and a clean implementation of it. Levels 6 to 8 are among the few levels in the set that a 400,000-position search could not exhaust, which means they have real depth.

What is wrong: auto-death on unwinnable (problem 2). Level 1 is one click. Levels 6 to 8 are copy-pasted rooms. The light always starts in the same place and `sun0` is unused. Reports itself as g014. The catalog's "the shadows decide where every block lands, all at once" is wrong: you topple one block per click.

Fix: remove auto-death. Replace level 1 with a two-click board that forces one light turn. Vary `sun0`. Fix the write-up.

### 4. pt01 Perfect Target (850 lines)

Everything is telegraphed one action ahead, every enemy script is fixed, nothing is random. This is the closest to ARC's own values. Human-played to completion (373 actions).

What is wrong: death never reaches the engine (problem 1). There is no action budget, so you can bump a wall forever and wait out any firing cycle; every level reduces to "wait for the gap". Enemies never move. Levels 2 and 3 are unarmed targets; 8 is 7 plus one ship. Random play clears level 1 in every seed.

Fix: call `lose()`. Give each level an action allowance drawn on the HUD. Let one ship type move along a route.

### 5. wb02 Windy Boats (308 lines)

Pure logical state, full re-render each frame, nice to read. The wind-on-the-others rule is good. Mark's own note says "It's easy". It is: 4x4 and 5x4 boards, 344 reachable positions in level 1, 22 moves at most for the longest solution.

What is wrong: the allowance refills on retry so it never bites. A no-op click on the selected boat costs a dot (a trap, not a rule). The catalog's "a boat only drops anchor if you hand control away" is right, but it is also visible the moment it happens (anchor icon, furled sail), so "a rule nobody tells it" overstates it. Dead tie-breaking loop that the comment admits can never run. Header leftovers ("NT80 revision", "the Boss").

Fix: 6x6 boards with two wind directions per level (a flag that flips every N moves would make it a real puzzle). Make the allowance a game budget, not a level budget. Don't charge for clicking the boat you already hold.

### 6. dz01 Dig Zone (927 lines)

The most mechanics of any game here: dig costs by material, falling sand, hearts, creatures with stripes, droppers, stars, energy cells, a click budget. The budget bar and the depth dot are a good HUD. Human-played to completion (380 actions). Random play clears nothing, which is the right answer.

What is wrong: too many rules for an agent to isolate, three of them hidden (problem 3). Auto-death when the budget is out (problem 2), with the restart hack. Levels credited to a generator that is not here.

Fix: cut droppers and energy cells from levels 1 to 4 so the rules arrive one at a time. Show "perched" (a one-pixel hand on the wall). Ship the generator or stop citing it.

### 7. te01 Tethered Extraction (726 lines)

Mark: "Awesome game. Mechanics are great." The tether-that-wraps idea deserves that. It is the only game with a real loss (blade contact ends the run).

What is wrong: it is a continuous-geometry physics toy drawn on a 64x64 grid (problem 3). Eight levels are four layouts. `tighten()` can raise mid-action. Two coding styles in one file. Undo is free and unlimited, which with a deterministic world means an agent can scrub through any level. And Table B: every level has between 109 and 292 reachable positions, fewer than any other game here. All that geometry buys no depth.

Fix: re-derive the rules on integers: cable length in cells, obstacles on cell boundaries, blades on cells. Then the screen is the state. Build four more genuinely different layouts and drop the stretched duplicates.

### 8. wf02 Water Flip (504 lines)

Clear visuals (target line, green tank, red rim on the tank that refuses). The lever-reverses-a-whole-circuit twist is a good one.

What is wrong: it is the classic water-jug puzzle with no cost of any kind. Nine reachable positions in level 1; 5,062 in the largest. Random clicking clears level 1 in a seed. A click anywhere that is not a control flashes every control (a free map of the buttons). ACTION5 works on lever 0 only.

Fix: a pour budget per level, drawn as pips. Make ACTION5 cycle which lever is live, or remove it and make everything a click. Remove the click-anywhere hint.

### 9. ff01 Feeding Frenzy (472 lines)

Deterministic tides are a smart replacement for the randomness this genre usually has, and the time bar and lives are honest.

What is wrong: it is an arcade game with three lives, a blink-after-bite grace period and off-screen predators (problem 3). Hitboxes are bounding boxes while the art has empty corners, so you get bitten by water. The one-pixel heading tell is unreadable. Zero sprites in the level. Levels credited to a missing generator; no human has played it.

Fix: mark predators on the window edge the way edible fish are marked. Make the tell a two-pixel bar. Cut lives to one and let the time bar be the only budget.

### 10. se01 Shrine Exploration (731 lines)

The best pixel art in the set. The walking slide is nice.

What is wrong: it is a walk. No loss, no budget, no counter; patrols and thorns teleport you to the last shrine for free. Six levels on one map. The `order` list in every level is never read. The shrine-to-gate mapping is hidden and the gate is a long scroll away from the shrine, so cause and effect are separated by hundreds of actions. No human has played it. Reports itself as xb02.

Fix: count steps and draw them; drop the player to the start, not the last shrine, on a catch; put each gate within one screen of its shrine on the early levels so the rule is learnable, then move them apart.

### 11. es01 Extreme Sneeze (738 lines)

Fully deterministic and the host-hopping idea is original.

What is wrong: five invisible clocks (problem 3), a win target that includes doctors and gunmen with no count on screen, a 26-pixel face as a health bar, a vent rule that is one obscure special case, and a cliff between level 1 (a 7x6 room with every AI switched off) and level 2 (a 20x10 scrolling map with everything on). Random play clears two levels in every seed. No header. Dense one-letter code with 200-column lines. Human record: 44 actions, one level. And the theme (problem 9).

Fix: one clock. Show it. Make the goal count visible (pips for people left). Re-theme it; the mechanics do not need the outbreak.

### 12. lt03 Lock Target (1,203 lines)

This is where the most effort went and it shows: four wards, nine missions, persistent damage, crowds, ambulances, beacons, aid, stale sensors, cars with passengers. As a simulation it is the richest thing in the repository.

As an ARC task it is the weakest, for exactly that reason. Roughly fifteen interacting systems, most of them timers no screen can show (problem 3), on a world four times the window. ARC's public games have two to four mechanics each and a cold human finds them in minutes. A cold human will not find the exploding-target timer, the alternate-tick slowdown, or the recharge period here. Missions 1 to 3 cannot be lost. `time_limit` is computed and never used. The tray is clickable but clicking does not select. The HUD is seven instruments in four pixel rows. No header; semicolon-chained code; a 30-field snapshot deep-copied per mission. No human has played it. And the theme (problem 9).

Fix: this is two games. Keep "aim late at a walking target" (missions 1 to 3, with precision and heavy only, and a real budget) as one small clean game. Everything from mission 4 on is a different game that needs a different, larger canvas than ARC gives you.

## What ARC Prize does that this set does not

- Every game is played cold by several people before release and their action counts are published. Six of your twelve have never been played.
- Two to four rules per game, all discoverable from one screen, no clocks the player cannot see.
- No auto-detection of dead ends and no forecast of danger; the player finds out by trying.
- A fixed action budget per game in the harness, so shallow levels still cost something.
- Levels that each add a rule, not levels that repeat geometry.
- One control convention per game, documented by behaviour, with no key that works on one object and not its twin.

## What this review did not do

- No human played anything for this review. Everything above is from source and from scripts.
- The random probe is a floor, not a ceiling: a game random play clears is certainly too easy; a game it does not clear may still be shallow (Table B covers that for seven games; ff01, se01, es01 and lt03 have no pure rule function to search and were not brute-forced).
- The ARC harness's own action limits and scoring were not reproduced; comparisons to the public 25 are from their published descriptions, not from running them.
- The other 38 games in the catalog were not read.

## Scripts

Three throwaway scripts were run from a scratch directory against this checkout and are not committed: a random-action probe over `tools/runtime.py` (2,000 actions, seeds 0 to 2, per game), a breadth-first solver calling each game's rule functions (`advance`, `pour`/`refusal`, `fell`, `resolve`, `Core.act`, `transition`, `act`), and a timer for the in-game winnability searches. Anyone can reproduce Table A with `examples/collect.py` and a loop; Table B needs the solver, which is forty lines per game and is worth adding to `tools/` if you want the numbers to stay honest as levels change.

## Fixes applied on 5 November 2026 (same day, after this review)

Every change is a defect fix; nothing about difficulty, level count, theme or the dead-end detectors was changed, because those are design decisions for Mark. All twelve games still pass `tools/validate.py`; the catalog hashes, class names and three write-ups were refreshed to match. Each fix was driven to its loss state with a script against the real engine and checked: the engine reports GAME_OVER, and a RESET restarts the same level with progress kept.

| Game | What changed |
|---|---|
| pt01 | A sunk player now ends the run (`lose()`) instead of silently rebuilding the level. `handle_reset` restarts the level, or the whole game only when nothing has been played or it is won. Keyword arguments to the engine. Header added. |
| st01 | Reports itself as st01, class `St01` (was g014/`G014`). A lost position ends the run as GAME_OVER instead of a silent restart; the action-count workaround is gone. The winnability memo lives on the game instance, not the module. |
| bs01 | Reports itself as bs01, class `Bs01` (was g019/`G019`). A dead end ends the run as GAME_OVER; workaround gone. Every level's state space is searched once at import, so a level that is too large or unwinnable fails at load, never mid-play. |
| eh01 | A dead end ends the run as GAME_OVER; workaround gone. Unused `before` parameter and `_cell_center_px` removed. |
| dz01 | A broken hero ends the run as GAME_OVER; workaround gone. A perched hero shows a white hand on the wall he holds, so that state is on screen. Keyword arguments to the engine. |
| te01 | Cable tightening no longer raises an exception inside the engine when a shortening step would lengthen the path; the step is skipped. Keyword arguments to the engine. |
| se01 | Reports itself as se01, class `Se01` (was xb02/`Xb02`). The per-level `order` list that no rule read is gone. |
| lt03 | Clicking a round in the tray selects it (it only flashed before); a locked round still only flashes. The per-mission `time_limit` that nothing read is gone. Header added. |
| es01 | Header added. |
| ff01 | Every fish off the window is now marked on the edge, predators included; before, only food was marked and bites arrived from nowhere. Keyword arguments to the engine. |
| wb02 | Dead tie-breaking loop removed; leftover docstring removed. |
| catalog | Hashes for the eleven changed files; class names for st01, bs01, se01; st01's "all at once" claim corrected; wb02's "running out ends the game" now says a reset restarts the level; ff01's and lt03's rules updated for the two behaviour changes. |

Left alone on purpose: wf02 (nothing in it is broken, it is just shallow), the four dead-end detectors, the pink danger overlay in bs01, the hidden clocks in es01 and lt03, the duplicated levels, the themes, and the asymmetric ACTION5 in wf02. Those are the design calls in the ranked list above.

Random play after the fixes (600 actions, three seeds): pt01, eh01, bs01 and ff01 now hand the engine a GAME_OVER several times per run; wb02 still does; st01 and dz01 can lose but random play rarely finds the dead end. Levels cleared by random play did not change, as expected, because nothing about difficulty changed.
