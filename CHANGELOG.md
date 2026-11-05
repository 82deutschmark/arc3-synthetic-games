# Changelog

## 0.8.2 — 5 November 2026

Claude Code, at Mark Barney's call: the defects found by the review are fixed, and only those. A loss now reaches the engine as GAME_OVER in pt01, st01, bs01, eh01 and dz01 (they used to restart the level silently), and RESET restarts the level; the four copies of the action-count workaround are gone. st01, bs01 and se01 report their own ids (they said g014, g019 and xb02). te01 no longer raises inside the engine while tightening the cable. lt03's tray selects a round when clicked and its unused time limit is gone. ff01 marks predators off the window, not just food. dz01 shows a perched hero. Dead code out of se01, eh01 and wb02; headers on pt01, lt03 and es01. Catalog hashes, class names and the st01, wb02, ff01 and lt03 write-ups refreshed. The review records every fix and what was deliberately left alone.

## 0.8.1 — 5 November 2026

Claude Code, at Mark Barney's call: an adversarial review of the twelve featured games, in `docs/reviews/2026-11-05-featured-twelve-review.md`. Every featured source file read in full; a random-action probe and a brute-force solver run against the real engine; findings ranked, with a card per game. No game was changed.

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
