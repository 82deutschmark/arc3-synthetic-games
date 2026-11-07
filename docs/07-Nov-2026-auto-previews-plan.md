# Plan: previews regenerate automatically

Written after the work was done, at Mark's instruction to just get it done.

**Scope.** In: pictures in `docs/previews/` cannot silently lag their game. Out: any change to a game, the catalog schema, or the GitHub-side automation (a bot commit to `main` was rejected as a source of tree fights).

**Architecture.** `tools/make_media.py` owns drawing and the staleness test (source SHA-256 vs `docs/previews/manifest.json`). `tools/validate.py` imports that test and fails stale or missing pictures, so anyone who clones is covered. `.githooks/pre-commit` runs `make_media.py --stale` and stages the output, so the committer never has to remember. Pillow is added to `requirements.txt`.

**TODOs.** 1 Manifest and `--stale`/`--all`. 2 validate check. 3 Hook plus `core.hooksPath`. 4 Full redraw. 5 Verify: all games pass; a deliberately stale entry fails validate and the hook redraws it. 6 Docs: README, AGENTS.md, CHANGELOG 0.9.2.

**Known limit.** Hooks are not cloned; each clone runs `git config core.hooksPath .githooks` once. The validate check is the backstop.
