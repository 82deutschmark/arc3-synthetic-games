# Public synthetic-game release

Requested by the Boss in #arc-3 on 29 October 2026. Preparation is local; publication is owned by the parent agent.

## Scope
A standalone snapshot of the public authored-game mirror: runnable Python environments, provenance catalog, training rollout example, and static browse/download page. No official games, team votes, user traces, secrets, or private data. Exclude g028 because the authoring distribution freshness check flags it stale. This is a source release, not a solved demonstration dataset or a claim that every level has been verified solvable.

## Architecture and reuse
Reuse the exact public runtime artifacts from arc-explainer's authored registry and existing ARC engine API, preserving the source MIT notice. Keep game identifiers opaque. Separate runtime loading, rollout collection, validation, catalog data and static presentation. No build system or web service is required.

## Work
- [x] Inspect authored registry, distribution freshness and dependency API.
- [x] Copy scoped games and previews; pin content and source provenance.
- [x] Add training integration, documentation, credits and browse page.
- [x] Exercise reset/action on every released environment; validate catalog hashes and links.
- [ ] Report checks and any exclusions before publication.

## Documentation
README describes installation, real rollouts and limits. CREDITS preserves source attribution. CHANGELOG records the first candidate. VALIDATION records performed checks, not historical claims.
