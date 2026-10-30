# Rotated and recoloured games with mechanic extensions

Author: GPT-6.1 Sol
Date: 29-October-2026

These are a separate companion collection to the original authored games. They retain public-game ancestry and visual transformations while adding rules or a new use of existing rules. They must not be counted as independent original mechanics merely because they look different.

## Late-level extensions

- **vj11**: a walker is added on level 2, combining arrow movement with riding the turning tracks.
- **vj13**: level 3 adds junction transfers between rings. This is a topology extension using existing movement rules, not a newly implemented rule. The revised third level needs two transfers.
- **vj15**: buttonless tracks from level 2 force global-turn actions, which disturb the other tracks too.
- **vj17**: spinner buttons from level 2 advance by a visible changing count; the added finale requires them.

## Other transformed mechanic extensions

- **vz11**: sideways current changes falling paint paths.
- **vz13**: paired paint portals; this is the historical rotated version, superseded by the later unrotated **pf21** pipe remake. Kept here as an explicitly historical research artifact, not silently presented as the newest build.
- **vz15**: paint dyeing and colour-specific cups. Includes the later visible-failure repair.
- **vz17**: current direction changes after player moves, so spill timing matters.
- **ve13**: mirror stamps flip pieces, making fits possible that rotation alone cannot produce.
- **ve15**: unheld pieces drift in wind. Existing ablation evidence only proves the saved line needs wind, not that the level is impossible without wind.
- **vp15**: arrows slide through the maze and apply changers crossed; includes the later dead-end repair.
- **vh17**: switching active panels determines which tiles accept clicks.

The second group introduces its added rule from the first level; it is not mislabeled as a late-level surprise. Cosmetic-only V-series changes, pure recolours and the unchanged copycat pack are not included.

## Files and use

`games/<id>/<id>.py` is a standalone runtime source using ARCEngine and NumPy. It contains no release helper dependency. Instantiate the game class recorded in `manifest.json`, reset it, and step ARCEngine actions exactly as for the primary collection. Titles remain opaque IDs.

`manifest.json` is **researcher-facing**: parent games, transformations, mechanics, introductory levels, source checksums and evidence paths. Keep this mechanic-spoiling metadata out of agent observations.

`research/<id>/` contains the existing recorded winning trace, old vet report and design notes. The old report is historical; `previous_vet_source_matches` records whether it matches the copied bytes. `verification.json` records this extraction's engine replay results. `prepare.py` is an optional extraction/replay tool for the original workstation, not a dependency of the games.

## Provenance and attribution

All runtime files are copied byte-for-byte from `VoynichLabs/autoresearch-arena`, under `arc3games/polish/`; the precise paths and checksums are in the manifest. These are local source snapshots, not a claim to have fetched the newest upstream or visually checked the live site.

The public-game rule code in every included runtime file carries the full **MIT license**, copyright **ARC Prize Foundation (2026)**. Those notices and the author/modification headers remain intact. The transformation and mechanic-extension work is credited in each file to its original contributors; this extraction does not replace those authors with the packager's name. Preserve all embedded notices when redistributing. The top-level release license does not erase these third-party notices.

All parents in this extraction are ordinary public training-game families (lp85, sp80, cn04, ls20, ft09). No held-out or test-only family source is bundled. Mentioning a general slide or direction-changing idea in a design note does not bundle a held-out game's implementation.

## Verification limits

Saved winning traces were replayed from reset through every recorded level to WIN in the installed ARCEngine; each action's frames were checked for 64×64 dimensions and palette indices 0–15, and level boundaries were checked against trace boundaries. See `verification.json` for per-game outcomes and `manifest.json` for dependency versions.

This does not assert that every possible state is recoverable, that humans approved a given version for training, that the games have independent difficulty, that a novel rule is mathematically necessary, or that harness scores improved. Do not convert a successful replay into a human Trainable verdict. No GPU runs or model inference were launched.
