# Are our games out of distribution, or just too hard?

Author: Claude Opus 5.5, 22 November 2026, for a GPT agent to run
Asked for by: Mark Barney (the Boss)

## The question

ARC-AGI-3 is now saturated: GPT-6.2 Astra is reported to clear it fully. Our fifteen featured games were made to be learnable
training data that is hard for AI in ways a person finds easy. In one earlier run, GPT-6.1 Terra cleared most of Simon
Ouellette's homemade games and very little of ours. That leaves three possible readings:

1. **Out of distribution, and learnable.** The model struggles to *discover* our rules, but can play them once it knows them.
   This is what we want from training data.
2. **Too hard.** The model fails even when told the rules, because the levels are long, fiddly or unfair. People may fail too.
3. **Not really hard.** The earlier gap came from the older model, the 15-minute cap or the harness, not from the games.

The experiment separates these, for each game and for the set as a whole.

## What we already have, and why it is not enough

The earlier runs (`docs/models.html`, raw runs on `/Volumes/Team 4TB/data/arc3-terra-showcase-20261111/` and
`.../arc3-external-showcase-20261112/`) ran each game **once**, with a **15-minute cap**, and several of ours ended on
**inference timeouts** rather than the model being stuck. There was no positive control, no rules-given condition and almost
no human data. One run per game cannot close anything.

## Design

### Game sets (all pinned by file hash, all run through the same harness)

| Set | Games | Role |
| --- | --- | --- |
| Ours | The 15 featured games in `docs/catalog.json` `featured`, at the hashes in the catalog | The thing being tested |
| Simon Ouellette | The 22 native homemade games in `docs/replays/external-terra/simon-inventory.json`, pinned as in `provenance.json` | Reference set made by a person, also meant as training data |
| Red Blue Pill | MM01, SK01, RS01 as pinned in `provenance.json` | Small second reference set |
| ARC-AGI-3 public 25 | The official public games | **Positive control.** A model that saturates ARC-3 should clear these in our harness. If it does not, the harness or the budget is the bottleneck and nothing else can be read. |

Every game gets an opaque alias in the prompts, as before. No titles, no file names and no source code reach the model.

### Conditions

- **A. Cold.** Exactly the ARC-AGI-3 situation: frames in, actions out, no instructions.
- **B. Rules given.** The same, plus a short rules sheet at the start of each game: what the pieces are, what the controls do,
  what wins and what loses. **No level solutions.** Run B on every game where A cleared level one in fewer than two of its
  three runs; skip it where A already cleared level one reliably.
- **C. Genre probe** (no play). Show the model the first three frames of level one and the list of available actions, and
  ask two separate questions in two separate calls: "Does this look like any existing game or puzzle? Name it, or say none."
  and "What do you think the goal is?" Run on every game in every set, three times each.

Rules sheets must be written the same way for every set, so no set gets better instructions. Use one fixed prompt: a model
reads the game's source and writes at most 120 words covering pieces, controls, win and loss, with no level-specific
advice. Store every sheet in the run folder. The Boss reads the sheets for our fifteen only to confirm they are not wrong;
he does not rewrite them.

### Model and budget

- **Primary model:** GPT-6.2 Astra, at the reasoning setting at which it is reported to saturate ARC-AGI-3. Record the exact
  model name, effort setting and the model's published knowledge cutoff.
- **Optional second model:** GPT-6.2 Sol at medium, condition A only, if the budget allows. It continues the earlier GPT-6.1
  results.
- **Time:** 30 minutes per game. Raise the per-call inference timeout so that a slow reply does not end a run. Log wall time
  for every action, so results can also be cut at 15 minutes and compared with the earlier runs.
- **Runs:** three per game per condition (the team's rule: three seeds before closing anything). Each run starts fresh,
  with no memory carried between runs or between games.
- **Order:** shuffle the play order across all sets for each of the three passes, so time of day and service load do not
  line up with one set.

### People (this part is for the Boss and the team, not the GPT agent)

Hard for a machine means nothing unless people can play the game. Keep this small, because it is hard to get people to play.

- Each volunteer plays, cold, **level one only** of four of our games and four of Simon's, mixed in a random order, through
  the lab at arc3.sonpham.net so the plays are recorded.
- For each game, note: cleared level one (yes or no), minutes taken, and "would you keep playing?" (yes, maybe or no).
- Use any lab plays that already exist for these games as well.
- Three or four volunteers is enough to tell "easy for people" from "people get lost too" for the games they cover.

## What to measure

Per game, per condition, over its three runs:

- **Level-one clear rate** (0 to 3 of 3). This matters most: a game whose first level the model never beats gives no
  training data at all.
- **Share of levels cleared** (levels cleared divided by the game's levels, since level counts differ).
- **Actions per cleared level**, and, where a human baseline exists, the ARC efficiency score for that level.
- **Time to first clear.**
- **Why each failed level failed**, read from the run logs with one fixed rubric:
  - never worked out the goal;
  - worked out the goal but misread a rule;
  - could not tell animation from the effect of its own action (seen in the earlier logs);
  - knew what to do but ran out of moves or made execution mistakes;
  - ran out of time.

  A separate model pass classifies every failed level. A person spot-checks ten of those classifications.
- **Genre probe:** whether the model names a known game, and whether its goal guess matches the rules sheet.

Per set: the median across games of each measure, with a bootstrap interval that resamples **games**, not runs. The game is
the unit; the three runs of a game are not independent evidence.

## How to read the results

Write these readings down before looking. They are readings, not pass marks.

| What we see | What it means | What to do |
| --- | --- | --- |
| Public 25: the model clears most levels cold | The harness and budget are fine; the rest can be read | Continue |
| Public 25: the model does not | The harness or budget is the bottleneck | Stop and fix the harness. Do not interpret the other sets. |
| Ours: low cold, much higher with rules | **Out of distribution, and learnable.** The hard part is discovering the rule. | Keep. Consider an easier first level that teaches the rule by playing. |
| Ours: low cold, still low with rules, and people clear level one | Too hard to execute: levels too long or too fiddly | Shorten the early levels or add a ramp level |
| Ours: low in both, and people also get lost | Too hard or unclear | Fix the game, not the model |
| Ours: high cold | Not out of distribution for this model; the earlier gap came from the older model or the 15-minute cap | Say so plainly |
| Genre probe: the model names a known game far more often for Simon's and the public 25 than for ours | Direct evidence our games are new to it | Report it alongside the play results |

Give every one of our fifteen games its own short verdict in plain words: out of distribution and learnable, too hard to
execute, unclear, or easy for this model.

## Things that could fool us

- **Training contamination.** The public 25 are certainly in the model's training data. Simon's games were published on
  6 October 2026. Ours were published in October and November 2026. If the model's cutoff is after those dates, any set may
  be partly memorised. Record the cutoff and say what it allows.
- **Different level counts and lengths.** Compare shares of levels and the level-one rate, never raw level totals.
- **Harness limits.** The earlier logs show the model confusing animation with the effect of its action. If that cause
  dominates our failures but not Simon's, the gap partly measures how our games animate. That is still a real finding, but
  it is a different one from "hard to discover". The failure rubric exists to catch this.
- **One person's taste.** The fifteen were hand-picked by one person. That is the claim being tested, not a flaw to hide.

## Respect for other people's games

Simon's and Red Blue Pill's games are a reference, not a target. The report never ranks their games' quality and never calls
them easy as a criticism. Being learnable is the point of a training set. Credit both, with links, wherever results appear.

## Running it (for the GPT agent)

- **Reuse, don't rebuild.** The earlier runner is `duck_terra_showcase.py`, with `prepare_and_run.py`, `finalize_external.py`,
  `publish_records.py` and the handoff notes in `/Volumes/Team 4TB/data/arc3-external-showcase-20261112/simon-remaining15/`
  (read `HANDOFF.md` first). Change the model, effort, time cap and per-call timeout. Add the rules sheet for condition B
  and a separate script for the genre probe.
- **Where data goes.** All raw runs go to `/Volumes/Team 4TB/data/arc3-ood-experiment-<date>/`. If that drive is not mounted,
  stop and say so; do not fall back to the internal drive.
- **Machine limits.** Run at most two games at once on the Mac Mini. Use `python3.13`. No Kaggle submissions, and nothing
  sent to Son's machines.
- **Run in stages.** First do one pass of condition A on all four sets and look at the public 25 before spending more. Then
  run the remaining passes, then condition B, then the probe. A single pass of A is enough to catch a broken harness.
- **Output.** Write `docs/reviews/<date>-out-of-distribution-results.md` (plain words, per-game verdicts, the reading from the
  table above) and a machine-readable results JSON next to it. Do not change the front page. Do not publish replays or
  results on the site until the Boss has read the report.
- **Credit.** Credit yourself by model name and effort level in file headers and the CHANGELOG.

## TODO

- [ ] Pin all four sets by hash; write the alias map
- [ ] Write the rules sheets with the fixed prompt; Boss checks ours
- [ ] Adapt the runner: model, effort, 30-minute cap, longer call timeout, rules-sheet option, per-action timing
- [ ] Condition A, pass one, all sets; check the public 25 control
- [ ] Condition A, passes two and three
- [ ] Condition B on games that qualify, three passes
- [ ] Genre probe, all games, three times
- [ ] Classify the failures; spot-check ten
- [ ] Human level-one check (Boss and team)
- [ ] Analysis, per-game verdicts and report; hand to the Boss
