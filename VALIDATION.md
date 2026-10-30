# Validation — 29 October 2026

## 30 October 2026 update (featured games)

- `tools/validate.py`: all 55 catalog games pass, including the new dz01 and lt02, and every featured id is checked for its replay and level strip.
- `tools/make_featured_media.py`: each game's recorded winning line cleared every level through the real engine and ended in WIN before any picture was written.
- `node --check docs/catalog.js`: pass. The page was loaded from a local static server at desktop and phone width; the featured cards rendered and the grid listed the featured games first.
- Not verified: GitHub Pages delivery after publication, and full-game solvability beyond the one recorded line per game.

## 29 October 2026

Python 3.13 with arcengine 0.9.3 and numpy 2.4.3.

- `tools/validate.py`: all 53 catalog games pass integrity, preview presence, module import, real RESET and one advertised action. Shared sprite helper hash passes.
- `examples/collect.py --game g001 --steps 16 --seed 0`: wrote 17 real JSONL rows; every frame is 64 by 64, initial action RESET. Output is ignored and removed after inspection.
- `node --check docs/catalog.js`: pass.
- Static HTML local asset references resolve; catalog contains 53 unique IDs.
- `check_dist_current.py` against authoring collection: 53 current, g028 stale; stale game omitted.

- Independent clean Python 3.13 virtual environment installation: pinned requirements installed successfully; all 53 reset/action checks passed again, and the collector produced 17 real rows with 64-by-64 frames. Temporary rollout removed.
- Release tree excluding the separately prepared extensions: no private machine paths or common credential/key patterns found. No Git metadata existed at verification time, so there was no staging area to inspect.

Not verified: browser rendering/interaction, GitHub Pages delivery, external source links after publication, full-game solvability or learning benefit.
