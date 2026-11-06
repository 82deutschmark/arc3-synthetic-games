<!--
Author: Gemini 3.8 Flash High
Date: 05-Nov-2026
PURPOSE: Guide for testing Open-Weights models on ARC-AGI-3 and using synthetic games as holdouts
SRP/DRY check: Pass — integrates with tools/runtime.py and mirrors arcengine conventions
Updated: 06-Nov-2026, Claude Opus 5.5 — removed claims the repository does not support (a human-playtested set, hardcoded
  game counts, LT03's "eight revisions", cousin games with no source); the sample loop now uses the engine's real state
  names; local Windows paths replaced with repository-relative ones; the featured table points at the catalog instead.
-->

# Evaluating Open-Weights Models on ARC-AGI-3 & Holdout Testing

This guide explains:
1. **How to test an open-weights model** (e.g., Qwen 2.5, Llama 3.3, DeepSeek-V3/R1, Mistral, Gemma 2) on the official **25 public games** for ARC-AGI-3.
2. **How to use the synthetic games in this repository as an unseen holdout benchmark** to evaluate true out-of-distribution reasoning and prevent test contamination.

---

## 1. Background: What Makes ARC-AGI-3 Different

Unlike ARC-AGI-1 and ARC-AGI-2 (which consist of static, few-shot 2D grid input/output puzzles), **ARC-AGI-3 is an interactive reasoning benchmark**. 

AI agents are placed inside unfamiliar, turn-based 2D grid environments powered by `arcengine`.
* **Zero Instructions:** The agent is given no rules, no goals, no tutorial, and no explanations.
* **Active Hypothesis Testing:** The agent must take actions, observe state transitions, deduce the rules and win condition through trial and error, and clear sequential levels.
* **The Public 25:** ARC Prize released 25 demonstration games (such as `ls20`, `ft09`, `vc33`, `dc22`, `g50t`, `m0r0`, `sc25`, `sk48`, `tn36`, `tr87`). Because these games are public, any agent tuned, prompted, or trained on them risks severe overfitting. ARC-AGI-3 holds back its official evaluation games in a private evaluation sandbox.
* **Synthetic Holdouts:** This repository provides ARC-AGI-3 style games built on the same engine (`arcengine`) to serve as unseen holdout environments. The list is `docs/catalog.json`.

---

## 2. Testing Open-Weights Models on the Public 25

Testing an open-weights model on ARC3 requires setting up the environment runtime and building an **agentic evaluation harness**. A raw language or vision model cannot be evaluated with a simple one-shot prompt; it must run within an active decision loop.

### 2.1 The Environment & Runtime

The games run on the `arcengine` Python package. This repository pins the version it was checked with in `requirements.txt`:

```sh
pip install -r requirements.txt
```

To run the public 25 themselves, use ARC Prize's own toolkit and follow its documentation; this repository does not ship or test that client.

### 2.2 Observation & Action Space

At every step, the environment returns an observation:
* **`frames`**: A 64×64 grid represented as a 2D array of integers (color palette IDs 0–15) or rendered RGB image frames.
* **`state`**: Current game status, as a name: `NOT_PLAYED`, `NOT_FINISHED` (still playing), `WIN` or `GAME_OVER`.
* **`levels_completed`**: Count of sequential levels cleared.
* **`available_actions`**: List of valid action IDs for the current step.

The action space consists of 8 discrete actions:
* `0`: **Reset** (restarts the current level or game).
* `1` to `4`: usually **Up**, **Down**, **Left**, **Right**.
* `5`: a game-defined action (interact, toggle, fire, use an item).
* `6`: **Click** (coordinate selection; requires `x` and `y` between 0 and 63).
* `7`: game-defined; often **Undo**.

Each game decides what its actions mean and which ones it offers, so read `available_actions` rather than assuming a fixed meaning. In this repository, for example, ACTION7 is undo in WB02 and TE01 but waits a turn in LT03.

### 2.3 The Open-Weights Agent Harness

To test an open-weights model, wrap it in an agent harness that manages the following:

#### A. Observation Representation
* **Vision-Language Models (VLMs):** Pass the rendered 64×64 PNG directly into the model's visual encoder along with recent action history.
* **Text / Code LLMs:** Format the 64×64 numerical grid as a 2D string, ASCII characters, or a **sparse state diff** (listing only the coordinates that changed between step $t-1$ and step $t$).

#### B. Constrained Action Decoding
Use structured outputs (JSON schema, tool-calling format, or regex-constrained grammar) so the model emits executable actions:
```json
{
  "thought": "The blue box shifted right when I pressed Action 4. Let's move down to align with the goal.",
  "action_id": 2,
  "x": null,
  "y": null
}
```

#### C. Context & Memory Compaction
Naively concatenating raw 64×64 grids across 50+ turns rapidly exhausts context windows (and degrades reasoning). Successful harnesses implement **context compaction**:
* Retain an episodic summary or **hypothesis scratchpad** (e.g., *"Player piece is the 3x3 yellow block at (12, 14); spikes at bottom row reset the level on contact"*).
* Evict intermediate raw frames, keeping only the initial state, the previous frame, and the current frame.

#### D. Active Scaffolding & World Modeling (Code-as-Policies / REPL)
Pure reactive policies (predicting next-action directly from the frame) achieve low success on ARC3. Frontier and open-weights agent pipelines use scaffolding:
* Allowing the model to write Python inspection scripts to analyze grid symmetries, connected components, and coordinate changes.
* Tree search or rollouts: exploring short candidate action paths and backtracking if `GAME_OVER` is triggered.

### 2.4 Metrics & Scoring

* **Relative Human Action Efficiency (RHAE):** ARC Prize's primary metric comparing the agent's total action count against median human action counts to solve each level.
* **Completion Rate:** Percentage of levels completed within an action budget you fix in advance and report.
* **Zero-Shot Generalization:** Success rate on games where the agent has never seen level layouts or mechanic definitions.

---

## 3. Using Our Synthetic Games as a Holdout Suite

When an agent has been developed or fine-tuned against the 25 public demonstration games, its performance on those 25 no longer measures fluid intelligence—it measures memorization or overfitting.

This repository's games are meant to serve as an out-of-distribution holdout suite.

### 3.1 The Air-Gap Rule (Preventing Data Leakage)

> [!CAUTION]
> **Keep your agent away from the repository source code.**
> In `games/*.py`, each file contains the explicit level matrices, mechanic updates, and victory checks. The catalog (`docs/catalog.json`) and web browse pages are intentional spoiler sheets.
> 
> If your coding agent or LLM harness can read local files or browse documentation, it will read the game logic directly. For a valid holdout test, the agent must interact **only** through runtime observations.

### 3.2 Drop-in Integration via `tools/runtime.py`

This repository provides a shared runtime interface in [`tools/runtime.py`](tools/runtime.py). It exposes clean, JSON-serializable observations without modifying game files:

```python
import sys
from pathlib import Path

# Add tools/ to path (run from the repository root)
sys.path.insert(0, str(Path("tools").resolve()))
from runtime import load_game, perform, frame_record

# 1. Load any pinned game from docs/catalog.json
game = load_game("wb02")  # e.g., Windy Boats

# 2. Reset the environment (Action 0)
frame = perform(game, 0)
obs = frame_record(frame)

# obs is a JSON-safe dictionary:
# {
#   'frames': [...],           # 64x64 grid
#   'state': 'NOT_FINISHED',   # or 'WIN' or 'GAME_OVER'
#   'levels_completed': 0,     # Int
#   'available_actions': [1, 2, 3, 4, 5]
# }

# 3. Step through the game with your model harness
while obs["state"] == "NOT_FINISHED":
    action = agent.decide_action(obs)
    # perform(game, action_id, x=32, y=32)
    frame = perform(game, action["id"], x=action.get("x", 32), y=action.get("y", 32))
    obs = frame_record(frame)

if obs["state"] == "WIN":
    print("Game cleared!")
```

### 3.3 Recommended Holdout Suite: The Highlighted Games

The `featured` list in `docs/catalog.json` is Mark Barney's hand-picked best: the games he liked most and thinks a person can play. They are not a human-playtested set; some have no recorded human play at all, and `docs/reviews/` says which. Each highlighted game's `spoiler` entry in the catalog (shown on the browse page) says what makes it hard for a bot, and names the **Slippery Seven** game it is a cousin of where there is one. The Slippery Seven are the seven public games where our agents fail most (`DC22`, `G50T`, `M0R0`, `SC25`, `SK48`, `TN36`, `TR87`).

Read those write-ups to choose holdouts and splits, but keep them away from the agent being tested (section 3.1).

### 3.4 Holdout Splitting Discipline

If you use part of this synthetic collection for training/fine-tuning and part for evaluation:
* **Never split randomly:** Do not do a uniform random train/test split.
* **Split by mechanic family:** If your agent trains on `LT03`, do not evaluate on `PT01` (both rely on aimed fire and facing vectors). If you train on `WF02`, hold out `DC22`-style global switches entirely.

### 3.5 Integrity Check

Always run the smoke test before benchmarking to confirm game file hashes match the catalog:
```sh
python tools/validate.py
```
A clean run checks that every game in the catalog matches its pinned hash, loads, resets and takes one action against the real `arcengine`. It does not check that any game can be won.

---

## 4. Summary Checklist for Researchers

1. **Setup:** Install `requirements.txt` and confirm every game passes `python tools/validate.py`.
2. **Harness:** Build an action loop wrapping your open-weights model using `tools/runtime.py`.
3. **Isolation:** Ensure model prompts and tool calls have zero access to the filesystem (`games/`, `docs/catalog.json`).
4. **Baseline:** Run your model zero-shot on the 25 public ARC3 demonstration games.
5. **Holdout Evaluation:** Run the identical harness on the highlighted synthetic games (`featured` in `docs/catalog.json`). Compare level completion rates and action efficiency to verify true out-of-distribution reasoning.

---

Author: Gemini 3.8 Flash High

