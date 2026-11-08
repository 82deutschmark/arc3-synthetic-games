# Changelog

## 0.9.7 — 7 November 2026

Claude Sonnet 5.5, at Mark Barney's call ("that game should also be present in the ARC3 synthetic games repository"), plan in `docs/07-Nov-2026-xa03-crawler-plan.md`: XA03, the crawler, added byte for byte from the version published on the Games page. Six big castle rooms, a key that changes colour and shape, locks, rune gates, crab and guard patrols, two bodies on the later worlds, and a lantern that burns a drop a move. It is not in the highlighted list. Catalog entry, hash and previews included. Not human-tested.

## 0.9.6 — 7 November 2026

Claude Sonnet 5.5, at Mark Barney's call: notes for the assistant fixing the Play links, in `docs/reviews/2026-11-07-play-links-and-lab.md`, linked from `AGENTS.md`. The lab only opens games published to it, so unpublished games (DZ03 and LT05 today) fall back to its browse list; TE02 and SE02 open different games with the same ids; the note records how the lab resolves an id, how games get published and what blocks it. No game or link was changed. The catalog version stays at 0.9.5.

## 0.9.5 — 7 November 2026

Claude Sonnet 5.5, at Mark Barney's call (the five munitions were too complicated to build a coherent game round; make it clear for people and hard for an agent that sees only the frames), plan in `docs/07-Nov-2026-lt04-munitions-rework-plan.md`: a new game, LT05, built from LT04 (LT04 stays in `games/`) and replacing it in the highlighted list. Same nine missions and city. The munitions each do one thing: precision is the building-breaker (two steps off a roof per shot); heavy is unchanged; fire (from mission 5) is a single round that wipes a square about fifty cells across and brings every roof in it down; aid (from mission 4) sends every civilian, crowd and ambulance in the open walking to the spot, never a raider, and does nothing else; signal (was beacon, from mission 1, drawn as a phone) is instant and freezes only the raider at the click for seven steps, confirms it and draws it bigger. House rule instead of the proposed coin flip: anyone under a standing roof is safe from every blast until the roof is down, so you break the house before you can hit who is inside. Plain buildings no longer cost shield (hospitals, schools, people still do). Dropped as undrawn or off-brief: the incident fires and the injured patient, the response meter, the world slow-down, the raiders' double step every 7th turn and the confidence that crept up every 18th turn. Clearer kills: a red cross where a person fell, a green burst where a raider fell, and the shield bar's empty part coloured by what emptied it (red people, violet a hospital or school). Checked in the real engine: each munition and the roof rule behave as written; every mission 1 to 9 was cleared by a scripted signal-then-precision run; aid then fire kills several raiders in one shot and, with the crowd lured at least 36 cells from the target, costs nothing but people in cars that carry a raider; two scripted runs are identical frame for frame; a lost mission goes GAME_OVER and RESET restores it. Not tested: whether a person finds it clear or fun, or the balance of the shield against the great blast; fire's box is not tuned. The Play link follows the catalog's pattern but the lab does not host LT05.

## 0.9.4 - 7 November 2026

Claude Sonnet 5.5, at Mark Barney's call ("blow up DZ02 ... dig sideways ... more peril in freeing the enemies ... two distinct types of sand"), plan in `docs/07-Nov-2026-dz03-sand-mechanics-plan.md`: a new game, DZ03, built from DZ02 (DZ02 stays). Two new sands: packed sand never pours, so a tunnel through it stays open and the hero can travel sideways for one click a square; quicksand pours and also slumps diagonally off ledges into gaps, and gives nothing to climb. Creatures now sleep while sealed in and wake when a square beside them opens, then step toward the hero after each of his moves and fight him if they reach him (a lit star flattens them free). Eight new levels where the straight way down is blocked, so the tunnels matter; every level was shown winnable by a search through the game's own rules, and budgets sit three clicks above the cheapest line found. Not play-tested by a person, and not yet on the Games page. Earth, rock, bedrock, hearts, the star, energy cells, inputs, win and loss are as in DZ02. DZ03 takes DZ02's place in the highlighted list; the DZ02 file stays in `games/`.

## 0.9.3 — 7 November 2026

Gemini 3.8 Flash High, at Mark Barney's call: benchmark review and ranking of all fifteen featured games (including BL02, SS02 and KT02, reflecting the 0.8.8 engine standardizations and 0.9.1 art rebuilds), in docs/reviews/2026-11-07-featured-fifteen-review.md. Identifies the Top 5 strongest games as ARC-AGI-3 holdouts (EH02, BL02, KT02, ST02, SS02) and documents search depth, visual transparency, and design gaps across the full set. Linked from AGENTS.md. No game code changed.


## 0.9.2 — 7 November 2026

Claude Sonnet 5.5, at Mark Barney's call ("I'd like it so that they get regenerated automatically"), plan in `docs/07-Nov-2026-auto-previews-plan.md`: previews can no longer lag their game. `tools/make_media.py` gains `--stale` and `--all` and writes `docs/previews/manifest.json`, the source hash each game's pictures were drawn from. `tools/validate.py` fails a game whose pictures are missing or older than its source. `.githooks/pre-commit` redraws stale pictures and stages them; enable it once per clone with `git config core.hooksPath .githooks` (Git does not clone hooks, so `validate.py` is the backstop for everyone else). Pillow is now in `requirements.txt`, because drawing needs it. The first full redraw changed only four level strips (cg01, dw01, ff01, mp01); every other picture came out byte-identical, so they were already current. Game rules are untouched.

## 0.9.1 — 7 November 2026

Claude Sonnet 5.5, at Mark Barney's call ("I don't want anything to be too busy. Don't forget about animations."): a second art round on all fifteen rebuilt highlighted games (PT02, TE02, DZ02, LT04, ES02, EH02, FF02, SE02, BS02, WF03, ST02, BL02, KT02, WB03, SS02). Backgrounds are calmer, with quieter textures and fewer, larger props, so the pieces you play stand out. Motion is richer: pieces crouch, leap, slide and land with dust, blocked moves bump and wince, lost runs close in or shake, wins and new levels sweep or iris, and the scenery sways during the frames after each action. The game only draws frames when you act, so nothing moves while it waits for you. LT04's late missions get a further calming pass. Rules are unchanged: random play from every level on each game matches the 0.9.0 and 0.8.9 versions step for step.

## 0.9.0 — 7 November 2026

Claude Sonnet 5.5, at Mark Barney's call, plan in `docs/07-Nov-2026-featured-art-glowup-plan.md`: the art of the other thirteen highlighted games is rebuilt, four passes each, as new games under new numbers: PT02, TE02, DZ02, LT04, ES02, EH02, FF02, SE02, BS02, WF03, ST02, BL02 and KT02. They take over the highlighted list; the old files stay in `games/`. Every scene is now named sprites with faces and layers, each level has its own backdrop, props and ambient life, and wins and losses are drawn. The files are roughly two to three times longer, almost all of it picture and animation data. The rules are unchanged: random play from every level on old and new gives identical state, level count and offered actions. Not human-tested; the busiest, LT04, may need a readability look.

## 0.8.9 — 7 November 2026

Claude Sonnet 5.5, at Mark Barney's call: Windy Boats and Shared Supply glowed up as new games, WB03 and SS02, replacing WB02 and SS01 in the highlighted list (the old games stay in `games/`). WB03 is a large open sea seen through a 64 by 64 window that follows the boat you steer, with arrows at the edge for boats out of view, and eight different seas dressed with palm islands, lighthouses, reefs, shoals, a kraken, a sea serpent, pirate ships, currents, whirlpools and a turning wind. SS02 is a fruit market with eight different stalls (conveyor, two trays, blender, colour and shape orders, a revolving rack, a festival), detailed fruit and a vendor cat who reacts. Both follow the public 25's loss, reset and undo rules. Counters are twice the shortest winning line found by search; no person has played either yet.

## 0.8.8 — 7 November 2026

Claude Opus 5.5, at Mark Barney's call: the highlighted games now lose, reset and undo the way ARC Prize's public 25 do (checked in their sources and in the harness). All the custom RESET overrides are gone (pt01, te01, dz01, eh01, wb02, bs01, st01, ss01, kt01, bl01), so RESET follows the engine's rule. Undo no longer gives spent moves back in wb02 and bl01. A wrong pull in kt01 now ends the run instead of silently restarting. The hidden dead-end checks that ended the run the instant a level became unwinnable are out of eh01, bs01 and st01 (bs01's pink danger squares stay). Instead eh01, bs01, st01, wf02 and se01 get a visible move bar, drawn without text, sized at twice the shortest winning line found by search; running it out loses, and in se01 a patrol or thorn now ends the run too, where it used to send you back to the last shrine. se01's world window is one row shorter to make room for its bar. Write-ups and the five games' pictures are redrawn to match. Every game passes `tools/validate.py` and a random-play run with losses and resets through the real engine. Not changed: dz01 (its loss already comes from a visible bar), the hidden clocks in es01 and lt03, level counts, themes, difficulty beyond the new bars.

## 0.8.7 — 6 November 2026

Claude Opus 5.5, at Mark Barney's call: a second pass over the 5-Nov fixes, plan in `docs/06-Nov-2026-featured-fixes-followup-plan.md`. The 0.8.4 review and 0.8.5 fixes are credited to Claude Fable 5.1, who made them (they said "Claude Code"). Fixed: the write-ups for pt01, st01, bs01, eh01 and dz01 still said a loss restarts the level by itself; they now say it ends the run and a reset starts the level again. dz01's perched hand was drawn beside the hero's new row, not the wall he climbed against. lt03's tray missed clicks on the top row of each pod. se01 kept the dead run's animation beat across a reset. bs01 no longer re-runs its level analysis on every level start. Dead code out of wb02, wf02, te01, es01, lt03 and se01; eh01 passes engine arguments by name. Headers no longer cite internal tools, generators or files that are not in this repository, or "the Boss"; st01 gets a full header. `EVALUATION.md` no longer calls the games human-playtested or hardcodes counts, drops LT03's unsourced "eight revisions" and cousins with no source, and its sample loop uses the engine's real state names (it compared against numbers and never ran). The catalog version now matches this changelog. Every game passes `tools/validate.py` and a short random-play run through the real engine. Difficulty, levels, the dead-end detectors and the other design calls in the reviews are unchanged.

## 0.8.6 — 6 November 2026

Claude Sonnet 5.5, at Mark Barney's call: a review of the 0.8.5 fixes and the docs around them, in `docs/reviews/2026-11-06-fixes-and-docs-review.md`, linked from `AGENTS.md`. The fixes check out on a fresh clone and in the real engine. The open items are recorded there, the main one being that `EVALUATION.md` calls the games human-playtested and hardcodes counts, which is wrong. No game or guide was changed. The missing blank line before 0.8.3 is restored.

## 0.8.5 — 5 November 2026

Merged onto 0.8.3 on 6 November 2026 by Claude Opus 5.5 Low, at Mark Barney's call; the game fixes are unchanged.

Claude Fable 5.1, at Mark Barney's call: the defects found by the review are fixed, and only those. A loss now reaches the engine as GAME_OVER in pt01, st01, bs01, eh01 and dz01 (they used to restart the level silently), and RESET restarts the level; the four copies of the action-count workaround are gone. st01, bs01 and se01 report their own ids (they said g014, g019 and xb02). te01 no longer raises inside the engine while tightening the cable. lt03's tray selects a round when clicked and its unused time limit is gone. ff01 marks predators off the window, not just food. dz01 shows a perched hero. Dead code out of se01, eh01 and wb02; headers on pt01, lt03 and es01. Catalog hashes, class names and the st01, wb02, ff01 and lt03 write-ups refreshed. The review records every fix and what was deliberately left alone.

## 0.8.4 — 5 November 2026

Claude Fable 5.1, at Mark Barney's call: an adversarial review of the twelve featured games, in `docs/reviews/2026-11-05-featured-twelve-review.md`. Every featured source file read in full; a random-action probe and a brute-force solver run against the real engine; findings ranked, with a card per game. No game was changed.

## 0.8.3 — 5 November 2026

Gemini 3.8 Flash High, at Mark Barney's call: `EVALUATION.md` guide added. Explains how to test open-weights models (LLMs and VLMs) on the public 25 ARC-AGI-3 games and how to use this repository's synthetic games as an air-gapped holdout suite. Covers `arcengine` runtime interaction, agent harness design (observation formatting, constrained decoding, context compaction, Code-as-Policies scaffolding), RHAE evaluation, the 12 featured games as Slippery Seven cousins, and family-based holdout splitting rules. Linked from `README.md`. The plan is `docs/05-Nov-2026-evaluation-guide-plan.md`.

## 0.8.2 — 5 November 2026

Claude Sonnet 5.5, at Mark Barney's call: three more highlighted games, BL01 Basket Lift, SS01 Shared Supply and KT01 Knot Tying, each with a teaser, "why AI struggles", rules, what's special and the look, written from the game's code and from runs of the real engine (SS01 and BL01 cleared on all eight levels by solver routes; KT01 levels one to six cleared in the engine and all ten solved under its own rule functions). The "not in the public 25" notes and any cousin games are left out until someone who knows the public set can check them. KT01's catalog entry now carries its level count, 10; it was empty. The names are proposals. The plan is `docs/05-Nov-2026-highlight-bl01-ss01-kt01-plan.md`. The page's count line is now "N best games", not "N best of M": the catalog is only the games in this repository, and Mark's picks are hand-picked from far more. The intro says they are the ones he liked most and thinks a person can play, the footer says "every game in this repository", and the README says the same. `catalog.js` carries the new cache version.

## 0.8.1 — 5 November 2026

Claude Sonnet 5.5, at Mark Barney's call: repository docs. The README is rewritten around what the games are for (holdouts for anyone who trained on the 25 public games) and what the user has to get right (keep the agent away from the game source), in Mark's voice. `AGENTS.md` and `CLAUDE.md` are added; `CODING_STANDARDS.md` is now Mark's full standards, with the repo-specific rules in `AGENTS.md`. `.gitattributes` forces LF so the catalog's game hashes verify on Windows, where checkouts were turning every game into a hash mismatch. The release plan moves from `docs/plans/` to `docs/`, named as the standards say.

## 0.8.0 — 5 November 2026

Claude Opus 5.5, at Mark Barney's call: each game's panel now leads with "why AI struggles", written in plain gamer talk, and names the Slippery Seven game it is a cousin of where the repository's own write-ups say so (PT01 and LT03 with SC25, TE01 and ES01 with SK48, SE01 and WF02 with DC22, BS01 with G50T, ST01 with TN36). The long rules, what's special, how it differs from the public 25 and the look fold under "full rules and details". DZ01 is Dig Zone. Every Play link goes to the lab at arc3.sonpham.net, which records plays.

## 0.7.7 — 4 November 2026

Claude Sonnet 5.5: a review pass. Names are title case on every card (Extreme Sneeze, Feeding Frenzy, Lock Target), and the clone line wraps on a phone instead of running off the screen.

## 0.7.6 — 4 November 2026

Claude Opus 5.5 High: more names that spell their tags, at Mark Barney's call. TE01 is Tethered Extraction and PT01 Perfect Target. XB02 is renamed SE01, Shrine Exploration: its file, pictures and catalog entry move to the new tag, and the entry keeps "was": ["xb02"]. The game code is unchanged; its engine id stays internal, as for the other games.

## 0.7.5 — 4 November 2026

Claude Opus 5.5 High: a game's name now spells its tag, at Mark Barney's call. EH01 is Eroding Horizons, WB02 Windy Boats, BS01 Bell Stealth and WF02 Water Flip. HC01 is renamed ST01, Shadow Topple, after its mechanic: its file, pictures and catalog entry move to the new tag, and the entry keeps "was": ["hc01"] so links and mirrors can still find it. XB02's teaser drops the name that did not match its tag.

## 0.7.4 — 4 November 2026

Claude Opus 5.5 High: every card leads with a short teaser instead of the first sentence of its write-up. Mark Barney wrote PT01, TE01, DZ01, LT03, ES01 and FF01's; the rest follow his style, and EH01 gets a name, Burnt Bridges. The teasers live in catalog.json as "teaser", so arc.markbarney.net shows the same words.

## 0.7.3 — 2 November 2026

Claude Opus 5.5 High: a called-out note, at Mark Barney's call. ES01 (an outbreak spread person to person) and LT03 (air strikes on a crowded city) touch what has been in the news, and no guardrail stopped either being built. The note sits under the grid, those two cards carry a red edge, and it leads their panels. The text lives once in catalog.json as "highlight", so arc.markbarney.net shows the same words. The script and stylesheet links carry the version, and the catalog is fetched fresh, so a visitor sees a change as soon as it is pushed.

## 0.7.2 — 2 November 2026

Claude Opus 5.5 High: the front page is data-dense, at Mark Barney's call. The twelve best games are small cards, six to a row on a laptop, all on one screen: opening board, code, level count, controls and one line. A click opens the game's full write-up (what is special, the rules, how it differs from the public 25, its look) with the level strip, a play button and the source. The top line carries the clone command for anyone taking the games into their own training. arc.markbarney.net shows the same cards from this catalog.

## 0.7.1 — 2 November 2026

Claude Sonnet 5.5: the card grid is back, at Mark Barney's call. The long spoiler rows are gone from the front page. Each of the twelve games is a card again (picture, name, one line, the level strip), and MORE opens its rules, what is special, how it differs from the public 25 and its look. The page text is cut to two short lines.

## 0.7.0 — 2 November 2026

Claude Opus 5.5 High: the front page is now a spoilers page, at Mark Barney's call. Each of the twelve games shows what is special about it, its rules written out, how it differs from ARC's public 25 and its look, plus Mark's own words where his reviews have them. Every rule was checked against the game's code, and by playing it where needed, before it went up. Human action numbers are gone from the page and from the why note. The "no instructions" line is gone.

## 0.6.0 — 2 November 2026

Claude Sonnet 5.5 Medium: the front page order follows Mark Barney's call: pt01, te01, dz01, lt03 and es01 lead; wf02 and hc01 are last. li01 is off the page: approved, but not one of the best. ng02 and fr01 are also off the page (ng02 sits too close to eh01 in colour; fr01 is an earlier version of ff01). xb02, a game with a world several screens wide, is added, with its source in `games/` and its pictures. The why note is rewritten around the games' own pictures.

## 0.5.2 — 2 November 2026

Claude Opus 5.5 Medium: the note now says how these games are made (one at a time with a person deep in the loop, the way ARC Prize made theirs), what other synthetic sets publish (a program’s check that a game can be won), and why a person playing is the bottleneck and the tie to reality.

## 0.5.1 — 1 November 2026

Claude Opus 5.5: a card with no recorded human play no longer shows a human row. The dash read as "nobody played this".

## 0.5.0 — 1 November 2026

Claude Sonnet 5.5: four highlighted games moved on, so the page now shows their current versions. lt03 replaces lt02, the older version it was grown from; it carries Mark Barney's Trainable vote. wb02, wf02 and ng02 replace wb01, wf01 and ng01; they were published the same day and have no Trainable vote and no recorded human play yet. The old files and pictures are removed. `tools/make_media.py` now draws stills only.

## 0.4.1 — 31 October 2026

Claude Sonnet 5.5: the page now shows only the highlighted picks, Mark Barney's best. The other approved games are no longer on the page; their source stays in `games/` and their entries stay in `docs/catalog.json`. Removed the compact card.

## 0.4.0 — 31 October 2026

Claude Sonnet 5.5: removed the animated clips. They replayed winning lines recorded by game-building agents (or a fixed walk), not anyone's play. Cards now show the opening frame and the level strip until a person's recorded play can be used.

## 0.3.3 — 31 October 2026

Claude Sonnet 5.5: every card has a Play link to the game's page on arc3.sonpham.net, so visitors' plays count as human plays.

## 0.3.2 — 30 October 2026

Claude Sonnet 5.5: five more highlighted games: ff01, pt01, te01, bs01, es01.

## 0.3.1 — 30 October 2026

Claude Opus 5.5: lead with dz01 and lt02 (lt02 restored). Removed per-game bylines and the note byline; credit is Team Turducken, under the direction of Mark Barney. Clips now run across levels instead of stopping after level one.

## 0.3.0 — 30 October 2026

Claude Opus 5.5: the collection is now only the games Mark Barney marked Trainable, in his page order. Removed the old g-series mirror, lt02 and the transformed extensions. Rebuilt the page with highlight cards and a compact grid, real gameplay clips, human numbers and no rule descriptions or marketing copy. Game files are now byte-for-byte copies.

## 0.2.1 — 30 October 2026

Claude Sonnet 5.5 Medium: added `docs/why.html`, a note in Mark Barney's voice (creativity can't be interpolated, what the ARC-AGI-3 public games are, where these games came from), linked from the front page and its nav. Slimmed the header and the lead so the featured games start at the top of the page.

## 0.2.0 — 30 October 2026

Claude Sonnet 5.5 Medium: the page now leads with two featured games. Added dz01 and lt02 to the catalog (source, hash, preview), a `featured` list in `catalog.json` that the page reads for its order, a looping level-one replay and a strip of every level's first frame for each, and `tools/make_featured_media.py` to render them from the real engine. The replays play a recorded winning line that is not published. Featured games also come first in the browse grid. Validation now covers 55 games.

## 0.1.1 — 29 October 2026

GPT-6.1 Sol: linked the separate transformed mechanic-extension collection from the README and catalog page, distinguishing later-level additions from visual changes and independent originals. Verified the main collection in a clean Python environment.

## 0.1.0 — 29 October 2026

Prepared by GPT-6.1 Sol. Initial standalone snapshot of public authored game runtimes, preserving upstream attribution and adding content-hash provenance. Includes a real exploration collector, pinned dependencies, per-environment reset/action checks, and a responsive buildless browse/download page. Excludes a stale distribution package and all non-allow-listed sources. No claim of expert demonstrations or full-game verification.
