# Add the crawler (XA03) to the games

Author: Claude Sonnet 5.5 Medium
Date: 07-Nov-2026
Asked by: Mark Barney ("that game should also be present in the ARC3 synthetic games repository").

## Scope

In: one game, XA03 (the crawler: six big castle rooms, two bodies, keys, rune gates, patrols, a lantern), added byte for byte
from the version published on the Games page (arc-3 pull request 150). Its catalog entry, previews, hash, changelog line.
Out: any change to the game, any change to other games, the highlighted list (it is not highlighted).

## Architecture

`games/xa03.py` is the published file, unchanged. `docs/catalog.json` gets one entry in the existing schema (hash, levels,
inputs, play link, spoiler block written from the code and a run of the real engine). Previews come from `tools/make_media.py`.
The id stays `xa03` because that is the code the Games page uses; the shrines game already sits here as SE01 (was XB02).

## TODOs

1. Copy the file. 2. Catalog entry and hash. 3. `make_media.py --game xa03`. 4. `validate.py` passes. 5. Version bump and changelog.

## Docs and changelog touchpoints

`docs/catalog.json`, `docs/previews/`, `docs/validation.json`, `CHANGELOG.md`. No count or version is written into prose.
