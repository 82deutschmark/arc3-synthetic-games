# DZ03: sideways digging, two new sands, enemies that come for you

Author: Claude Sonnet 5.5
Date: 07-Nov-2026
Asked by: Mark Barney ("blow up DZ02 into a DZ03: dig sideways without five layers of sand pouring in, more peril when you free the enemies, two distinct new sands in the spirit of Super Mario Bros. 2 worlds 2-1 and 2-3, not a clone").

## What is wrong with DZ02

Every kind of sand falls, so any hole you open lets everything above it pour in. Going sideways means digging out the whole column above the tunnel first, about five layers. The only way through is straight down. Creatures are sealed in their pockets and do nothing until you walk into them, so freeing one is not dangerous.

## Scope

In: a new game, `dz03`, built from `dz02` (new number, old file stays). Two new sands, hunting creatures, eight new levels, art for the new pieces. Rules of everything else (earth, rock, bedrock, hearts, star, energy cells, the bar, the inputs, the win and the loss) stay as in dz02.

Out: nothing that talks on the play surface, no readable titles, no change to dz01 or dz02, no change to the public games. Publishing to the Games page (the arc-3 repo) is a separate step with its own vet report.

## The three sands (what each does when you dig under or beside it)

- **Loose sand** (the DZ02 sand, unchanged): pours straight down into any opening.
- **Packed sand** (new): one click like loose sand, but it holds. It never pours, and what rests on it stays up. Dig along a packed band and the corridor stays open, so you can travel sideways for one click a cell. Loose sand sitting above the band still pours into anything you open directly under it, so a corridor cut into the top row of a band is not safe; the second row down is. The hero can climb one step against it, as against loose sand and earth. A drawn crust of layered ridges tells it apart before you dig. Same cost as loose sand: the new thing is the behaviour, not a new price tier.
- **Quicksand** (new): one click, and it runs. It pours straight down like loose sand, and where it sits on a ledge beside an opening it slumps off the edge diagonally into the gap, so it spreads into corridors and pits around it instead of standing as a wall. The hero cannot climb against it (nothing to grip). A drawn wave pattern tells it apart.

Earth (two clicks, holds), rock (three, holds) and bedrock (never) are unchanged. Colour no longer carries the whole rule: the picture in the tile does (ridges, waves, specks).

## Enemies come for you

A creature is asleep while it is sealed in (no open air beside it other than the hero's own square). The moment a neighbouring square opens, by your digging or by a collapse, it wakes, and from then on every move you make it takes one step toward you through open squares. If it ends up next to you it attacks: the same punch trade as walking into it, so a mole costs a heart and a worm two, a crab costs nothing. A lit star flattens it for free, as before. Creatures that start in an open cave start awake. Droppers (red eyes) keep their DZ02 behaviour. Awake creatures are drawn with a red mouth and a small tremble, asleep ones as before.

This is where the sideways digging pays back: a packed corridor stays open, so it is also a road for whatever you wake.

## Architecture

- `games/dz03.py`, one file like every game here, copied from `games/dz02.py` and edited. Rules stay pure functions on `DigState` (`act`, `settle`, plus new `wake` and `hunt`), art stays data at the top of the art section, `Scene.show` stays the only code that touches sprites.
- New cell values 11 (packed) and 12 (quicksand) sit in the gap below the creature values. Creature values gain a wake bit (8) beside the stripe bits and the dropper bit, so the existing creature helpers keep working.
- Every table that mentions a cell kind gets the two new ones: the character map for level specs (`p` packed, `q` quicksand), dig results, the climb list, the loose-things test, the solid tuple, the name map, the tile art branch and per-theme colours.
- Levels are written by hand and checked by a search written for this (`tools` stays untouched; the search lives in the scratchpad and its results are recorded in the level comments): every level must be winnable, the budget is set a few clicks above the cheapest line found, and a level where the star or an energy cell is skipped must still be possible but tight.

## TODOs

1. Copy dz02 to dz03; change ids, header, docstring.
2. Rules: packed, quicksand (diagonal slump), wake and hunt, the loop bound for settling.
3. Art: two tile pictures per theme, awake creature look, hunter step frame.
4. Search tool in the scratchpad; write and prove each of the eight levels; set budgets and hearts.
5. Play through the real engine: a recorded winning line for each level replays to a win; a mutation check (turn packed sand into loose and see a level become unwinnable or cost more) proves the levels use the new rule.
6. Catalog entry, hash, previews (`tools/make_media.py`), `tools/validate.py`, changelog.

## Docs and changelog touchpoints

`docs/catalog.json` (new entry with its rules text), `docs/previews/`, `docs/validation.json`, `CHANGELOG.md` (new top entry), this plan.
