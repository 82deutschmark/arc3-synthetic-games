# Handoff prompt: run the out-of-distribution experiment

Author: Claude Opus 5.5, 22 November 2026
Paste everything below the line into the GPT agent that will run the experiment.

---

You are running an experiment for Mark Barney (call him the Boss) on his open set of ARC-AGI-3 style games, the repository
`82deutschmark/arc3-synthetic-games` (local checkout: `/Users/macmini/GitHub/arc3-synthetic-games`). Work in a new branch or
worktree, never directly on `main`.

**Read first, in full:** `docs/22-Nov-2026-out-of-distribution-experiment-plan.md`. It is the design. Do not redesign it; if
something in it cannot be done, stop and say what and why.

**The question.** ARC-AGI-3 is saturated by GPT-6.2 Astra. Are the Boss's fifteen featured games new to such a model and
learnable (the goal: they are meant as training data), too hard to be useful training data, or not really hard? Answer it
per game and for the set.

**Order, and where to stop:**

1. Pin all four game sets by hash and write the alias map. No titles, file names or source reach the model.
2. **Stage 0, the genre probe, on every game.** Then stop and send the Boss a short report before any play runs.
3. Stage 1: one pass of the cold condition on all four sets. Check Simon Ouellette's set, which is the harness check. If the
   model fails most of it, stop: the harness or the budget is broken, and nothing else can be read.
4. Stages 2 and 3: the remaining cold passes, then the rules-given condition on the games that qualify.
5. Failure classification, the analysis and the report.

**Reuse, don't rebuild.** The earlier runner and its notes are in
`/Volumes/Team 4TB/data/arc3-external-showcase-20261112/simon-remaining15/` (read `HANDOFF.md`, then
`duck_terra_showcase.py`, `prepare_and_run.py`, `finalize_external.py`, `publish_records.py`). Change the model, the effort,
the time cap and the per-call timeout, and add the rules-sheet option and the probe script.

**Hard rules:**

- Raw runs go to `/Volumes/Team 4TB/data/arc3-ood-experiment-<date>/`. If that drive is not mounted, stop and say so. Never
  fall back to the internal drive.
- At most two games running at once on the Mac Mini. Use `python3.13`. No Kaggle submissions. Nothing sent to Son's
  machines.
- Three runs per game per condition. Each run starts fresh.
- Rules sheets are written by one fixed prompt from the mechanics code with every level layout removed, at most 120 words,
  with no level-specific advice. The Boss checks only the sheets for his fifteen, against the rules in `docs/catalog.json`.
- Simon's and Red Blue Pill's games are a reference, not a target. Never rank their quality or call them easy as a
  criticism. Credit both, with links.
- Do not change the front page, the Why page or the Models page. Do not publish replays or results on the site until the
  Boss has read the report.
- Credit yourself by model name and effort level in every file header and in a top `CHANGELOG.md` entry.

**Deliverables:**

- `docs/reviews/<date>-out-of-distribution-results.md`: plain words, the stage 0 finding first, then a one-line verdict for
  each of the fifteen (new and learnable / too hard to execute / too hard to be useful training data / unclear / easy for
  this model), then the reading from the plan's table, then what could have fooled us.
- A machine-readable results file next to it.
- A pull request to `main` with both, and the raw runs left on the drive.

**Talking to the Boss.** He is a video game producer, not a statistician. Lead with the answer, in a few plain sentences.
No tables of decimals, no hashes, no code in messages to him. Say plainly what you could not check.
