# Synthetic Games

A snapshot of authored interactive reasoning environments, packaged for people building agents and collecting training trajectories. Browse the [collection page](https://82deutschmark.github.io/arc3-synthetic-games/) or inspect the [machine-readable catalog](docs/catalog.json).

This is an independent community collection, not an official ARC Prize benchmark. The snapshot contains **55 authored environments**: 53 from the public arc-explainer mirror, plus two featured games, **dz01** and **lt02**, added on 30 October 2026 from the authors' own workspace. The page leads with those two. Game identifiers deliberately stay opaque. There are no expert demonstrations, trained models, or generated-level solvers in this initial package.

## Quick start

Use Python 3.13 (the release was exercised with Python 3.13 and the pinned dependencies below). From the repository root:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/validate.py
.venv/bin/python examples/collect.py --game g001 --steps 16 --seed 0 --output rollouts/g001.jsonl
```

The collector runs a real game. Its random policy is an integration example, **not an expert or a solver**. It writes JSON Lines: each row contains game_id, the action just taken, and the resulting observation. The first action is RESET (zero). Observations contain the engine's frames, state, levels_completed and available_actions. Click actions also contain screen x/y coordinates. The collector stops at a terminal state and refuses to overwrite files.

The seed controls the exploration policy, not procedural game generation. No generated-level API is claimed for these environments. Store large trajectory collections on your own data volume rather than in Git.

## Companion collection: transformed mechanic extensions

The [rotated and recoloured mechanic extensions](extensions/README.md) are included separately from the authored catalog. Some introduce an extra mechanic on later levels; others introduce their rule immediately. The companion notes distinguish visual transformations from rule changes, identify the parent family, and record the introduction level and replay evidence. They are not counted as independent original games or mixed into the primary collector catalog.

## Connect a learner

`tools/runtime.py` is the small integration boundary. `load_game(id)` returns a real engine instance; `perform(game, 0)` resets; subsequent `perform` calls accept action IDs and optional click coordinates. Read the returned frame's advertised actions instead of assuming every game has identical controls. Replace the random action choice in `examples/collect.py` with your own agent.

The collection provides environments, not a complete reinforcement-learning system. Define rewards and training targets explicitly. Keep evaluation games and related game families out of training when measuring generalization; this release does not assign or certify train/test splits. Do not interpret failed random exploration as a demonstration target.

## What's included

- `games/`: self-contained mirrored runtimes plus their shared sprite helper.
- `docs/catalog.json`: class names, paths, content hashes, pinned upstream links and exclusions.
- `docs/previews/`: initial-frame previews from the same public mirror; these are illustrative, not live game playback. The two featured games also have a looping level-one replay and a strip of every level's first frame, rendered by `tools/make_featured_media.py` from the real engine.
- `examples/collect.py`: real random exploration trajectory collector.
- `tools/validate.py`: hash checks plus real reset/action checks for each environment.
- `docs/`: buildless catalog page with search, source and download links.

For GitHub Pages, publish **main / docs**. No build tooling, server or credentials are required. To preview, serve `docs` with any static HTTP server; opening the HTML through `file://` can prevent catalog fetching.

## Provenance and scope

The exact authored allow-list comes from the upstream `authored-ids.json`. Only that list is eligible; contributed games, official benchmark games, held-out source collections, user traces, votes and team data are not bundled. The upstream distribution freshness check flagged g028 stale, so it is omitted pending a refreshed, verified package.

Source artifacts come from `82deutschmark/arc-explainer` at the commit pinned in the catalog. Each copied Python file has a release-packaging comment header; its original body is unchanged. `sha256` hashes the packaged file and `upstream_sha256` hashes its original upstream bytes. Original in-file notices are retained. See [credits](CREDITS.md) and [MIT license](LICENSE).

## Verification and limits

[Validation results](docs/validation.json) describe the checks actually run: file integrity, previews, imports, RESET and one advertised action for all released games. These checks do **not** establish full-game solvability, optimal solutions, equivalent difficulty, or training benefit. Historical authoring verifiers are not republished as evidence of current full-game passes.

## Contributing

Include original attribution and a real runnable source artifact. Document game families, required dependencies and reproducible playthrough checks. Do not commit credentials, personal play traces or large data. Keep evaluation reporting distinct from training data collection.
