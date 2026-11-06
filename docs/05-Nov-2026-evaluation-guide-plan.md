# Evaluation Guide for Open-Weights Models and Synthetic Holdouts: Plan

Author: Gemini 3.8 Flash High, 05-Nov-2026.
Direction: Mark Barney ("write that as a Markdown file, commit and push it to the repo. Make sure you credit yourself as Gemini 3.8 Flash High").

## Scope

In:
- Create `EVALUATION.md` in the repository root explaining:
  1. How to test open-weights models (LLMs/VLMs) on the public 25 ARC-AGI-3 games (runtime setup, harness architectures, observation representation, context management, RHAE scoring).
  2. How to use this repository's synthetic games as holdouts (isolation air-gap, `tools/runtime.py` integration, curated holdout selection around the Slippery Seven cousins, family-based splitting rules, and hash validation).
  3. Attribution crediting Gemini 3.8 Flash High.
- Update `README.md` to reference `EVALUATION.md` in the directory layout table and "Plugging in your agent" section.
- Update `CHANGELOG.md` with version 0.8.3 documenting the new evaluation guide.
- Commit all staged work cleanly and push to the remote repository.

Out:
- No game file changes (`games/*.py`).
- No hash changes in `docs/catalog.json`.

## Architecture

- `EVALUATION.md`: Single source of truth for benchmarking open-weights models and running holdout evaluations against `arcengine`.
- `README.md`: Points developers and researchers directly to `EVALUATION.md`.
- `tools/runtime.py`: Documented as the integration gateway.

## TODOs

1. Create `docs/05-Nov-2026-evaluation-guide-plan.md` (this plan).
2. Commit pending 0.8.2 changes (Claude Sonnet 5.5's catalog highlights for BL01, SS01, KT01) so git history remains cleanly attributable and atomic.
3. Write `EVALUATION.md` in the repo root.
4. Update `README.md` to link `EVALUATION.md`.
5. Add top entry `0.8.3` in `CHANGELOG.md` crediting Gemini 3.8 Flash High.
6. Verify `tools/validate.py` passes using `.venv\Scripts\python`.
7. Commit `0.8.3` and push to `origin/main`.

