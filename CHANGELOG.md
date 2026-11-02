# Changelog

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
