# Featured games lead the page

Author: Claude Sonnet 5.5 Medium
Date: 30-October-2026
Requested by the Boss: "glow up this page to lead with the games I'm most proud of, like DZ01 and LT02 or LT03."

## Finding

The 53 released games are the old public mirror (g-series). DZ01 and LT02 are not in it, so a layout change alone cannot
lead with them. They have to be added to the collection first. There is no LT03 in any branch of the authoring work; LT02
is the newest game of that family, so LT02 is the one featured.

## Scope

- Add DZ01 and LT02 to the catalog as ordinary authored games (source, hash, preview), beside the 53 existing ones.
- A `featured` list in `docs/catalog.json` names the games the page leads with, in order. The page reads it; no ids are
  hard-coded in the HTML.
- Lead the page with those games: a large looping opening, every level's first frame, controls, credits and links.
- Previews are real engine frames. The looping opening replays one recorded winning line through the real engine. The line
  itself is not published (the release carries no expert demonstrations).

## Architecture

- `games/dz01.py`, `games/lt02.py`: the original sources unchanged behind a release-packaging header.
- `tools/make_featured_media.py`: renders the three pictures per game from the real engine; the winning line is passed in
  from outside the repository.
- `docs/catalog.json`: two new `games` rows plus `featured`. Optional per-game fields (`levels`, `controls`, `note`,
  `credit`, `media`, `origin`) are used by the featured cards only.
- `docs/catalog.js`, `docs/index.html`, `docs/style.css`: featured section first, then the existing collection with the
  featured games shown first in the grid.

## Not decided here

Publishing. Both games are unpublished designs until this branch is pushed, and the release plan in the authoring
workspace schedules the full release after the 2 November close. The branch is committed locally and not pushed.
