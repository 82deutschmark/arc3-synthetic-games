# Sources and credits

## Released game runtimes and preview images

Source: [82deutschmark/arc-explainer](https://github.com/82deutschmark/arc-explainer), `server/data/arc3-games/`, pinned to the commit in `docs/catalog.json`. Its MIT notice credits **Mark Barney and contributors** and is preserved verbatim in `LICENSE`. Existing per-file author notices remain in the source body. Catalog entries link to the exact original artifact, not a floating branch.

These games originate in the authoring collection at [sonpham-org/autoresearch-arena](https://github.com/sonpham-org/autoresearch-arena/tree/master/arc3games). This release uses the already-public mirror artifacts rather than claiming a new blanket license over the complete authoring repository. It does not redistribute unrelated community games or official benchmark sources.

## Engine

[ARC engine](https://pypi.org/project/arcengine/) is an external dependency. Its own license and attribution apply; the engine is not vendored here. The engine provides the game, action and frame API used by this collection. This project is not affiliated with or endorsed by ARC Prize.

## Release integration

Packaging, runtime adapter, exploration example, validation tools and catalog page: GPT-6.1 Sol, 29 October 2026, prepared for the Boss's public synthetic-game collection. New integration work follows the MIT terms in `LICENSE`; no upstream attribution is replaced.

## Featured games: dz01 and lt02

Added 30 October 2026 from the authors' own workspace, not from the older public mirror, so their catalog rows carry a version and a content hash instead of an arc-explainer link. Each source is copied unchanged behind a short release header.

- **dz01**: designed by Mark Barney, built by Claude Opus 5.5, with parts adapted from an earlier game by Claude Opus 5.5, Claude Fable 5.1 and Claude Opus 5. The full author notes stay in the file header.
- **lt02**: the file carries no author line; its commit trail credits GPT-6 Astra Ultra, working for Mark Barney, for every change.

Packaging, the featured section and the preview renderer: Claude Sonnet 5.5 Medium, 30 October 2026.
