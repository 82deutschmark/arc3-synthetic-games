<!--
Author: Gemini 3.8 Flash High
Date: 07-Nov-2026
PURPOSE: Comprehensive review and benchmark ranking of the fifteen featured games in docs/catalog.json
SRP/DRY check: Pass — synthesizes catalog metadata, engine rules, and empirical search/transparency findings
-->

# Benchmark review and ranking of the fifteen featured games

Date: 7 November 2026. Reviewer: Gemini 3.8 Flash High, asked by Mark Barney to evaluate the fifteen ARC-AGI-3 synthetic games singled out as his favorites in `docs/catalog.json` and determine which ones are the strongest as AI evaluation benchmarks.

Scope: the fifteen games in `featured` in `docs/catalog.json` (`PT02`, `TE02`, `DZ02`, `LT04`, `ES02`, `EH02`, `FF02`, `SE02`, `WB03`, `BS02`, `WF03`, `ST02`, `BL02`, `SS02`, `KT02`). Evaluated against the core design principles of ARC-AGI-3, the empirical search findings from the 5 November review, the `v0.8.8` engine/loss standardizations, and the `v0.9.1` sprite rebuilds.

---

## 1. Executive Verdict: The Five Strongest Games

Since the original adversarial review of the initial twelve on 5 November 2026, the featured set has undergone three major evolutions:
1. **The addition of BL, SS, and KT** (expanding the set from 12 to 15).
2. **The `v0.8.8` standardization pass:** removing custom `handle_reset` overrides, eliminating silent restarts, stripping hidden instant-loss oracles out of `EH`, `BS`, and `ST`, and adding honest, visible move/fuse bars.
3. **The `v0.9.0` and `v0.9.1` art and animation rebuilds:** migrating from procedural HUD rendering to named, layered sprites with clean feedback animations.

When judged strictly as **unseen holdout environments for evaluating frontier reasoning agents**, five games stand out as exceptionally strong:

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │  1. EH02 (Eroding Horizons)  │  Information-as-Cost / Memory Puzzles   │
  │  2. BL02 (Basket Lift)       │  Inverted Physics & Counterweight Bal.  │
  │  3. KT02 (Knot Tying)        │  Topological & Temporal Path Planning   │
  │  4. ST02 (Shadow Topple)     │  Deep Indirect Manipulation (High BFS)  │
  │  5. SS02 (Shared Supply)     │  FIFO Scheduling & Long-Horizon Routing │
  └────────────────────────────────────────────────────────────────────────┘
```

These five games share the hallmarks of the best ARC-AGI-3 tasks:
- **Zero Hidden State:** The 64×64 frame completely and faithfully captures the environment state. There are no invisible asynchronous clocks, off-screen hazards, or masked continuous physics.
- **Search Resistance:** None of them can be solved by depth-first or breadth-first search in tens of milliseconds, nor cleared by random button-mashing.
- **Active Hypothesis Testing:** An agent can infer the 2 to 4 core operating rules within a few actions through deliberate, low-cost probing.
- **Calibrated Stakes:** Consequence is enforced through visible move allowances or physical layout commitment, rather than instant auto-killing or consequence-free wandering.
- **Thematic Neutrality:** Clean, abstract, or playful themes completely suitable for academic benchmarking without triggering safety guardrails.

---

## 2. Deep Dive: The Top 5 Strongest Games

### 1. EH02 — Eroding Horizons
* **Core Mechanic:** Stepping into darkness reveals nothing; stepping *backward* illuminates the tile just vacated, but burns one of its two scar marks. When both marks are spent, the tile drops into an abyss.
* **Why It’s Elite:** This is the most original and intellectually elegant concept in the repository. It turns **information gathering into an irreversible consumable resource**. An agent cannot blindly explore without destroying the terrain needed to retreat. Every observation carries a permanent topological cost.
* **Benchmark Standing:** In early builds, an internal dead-end search killed the player the instant a board became unwinnable (acting as an unintended hint oracle). In `v0.8.8`, this was replaced with a visible move bar and honest loss conditions. It tests counterfactual deduction, frontier tracking, and path conservation.
* **Room for Polish:** Ensure the triple-step win pattern (step onto goal ring, step back to light it, step on again) is gently introduced on Level 1 so an agent does not assume the goal ring is impassable.

### 2. BL02 — Basket Lift
* **Core Mechanic:** A balance and counterweight platformer. The player cannot walk off ledges into open air. Pressing **Down** does not translate the farmer down; it releases the counterweighted lift pan. Empty-handed, the farmer weighs 1 block; carried fruit adds 2 or 3. Later levels introduce gravity inversion (**Up**) and phase-shifting blue crystal blocks via a lever.
* **Why It’s Elite:** Directly disrupts the baseline inductive biases of neural agents. In standard gridworlds, `Down` translates coordinates `(y -> y + 1)`. Here, `Down` triggers a physics calculation: the heavier pan sinks and the lighter pan rises. If weights match, nothing moves. To descend, you must carry weight; to ascend, you must shed it.
* **Benchmark Standing:** 100% discrete, integer-cell physics with clean causal chains. The 320-press burning fuse provides a generous exploration budget while strictly bounding infinite loops. The blue crystal phase mechanics in levels 6–8 require rigorous multi-step forward planning.

### 3. KT02 — Knot Tying
* **Core Mechanic:** Thread a continuous cord through a slat lattice from a start eyelet to a finish eyelet. At every crossing, the strand must pass straight through twice (horizontal and vertical). Color-coded crossing bars determine which strand must end up on top; **the second pass across an intersection is the one that stays on top**.
* **Why It’s Elite:** It isolates **temporal-topological reasoning**. Modern vision-language models and RL agents struggle severely with braid theory and sequential self-avoiding paths because an intersection cannot be judged in isolation: its state depends strictly on the *order of visits*.
* **Benchmark Standing:** Zero hidden state; slats, eyelets, and crossing priority bars are 100% visible. The player can use Undo locally, but pulling the cord tight at the finish with an incorrect knot snaps the cord and triggers `GAME_OVER`. It offers 10 tightly calibrated levels with increasing crossing complexity.

### 4. ST02 — Shadow Topple
* **Core Mechanic:** You never push blocks directly. You rotate the ambient sun angle (clockwise/counter-clockwise), projecting directional shadows across floor pits. Clicking a block topples it into holes along its shadow projection.
* **Why It’s Elite:** A masterclass in indirect manipulation (analogous to the public game `TN36`). You never move the entity that changes the board; you manipulate the environmental vector that dictates where entities fall.
* **Combinatorial Depth:** In empirical search testing, levels 6 to 8 exceeded 400,000 reachable states without exhausting the tree. It cannot be brute-forced by shallow search.
* **Benchmark Standing:** Replaced the previous instant-loss detector with a visible step allowance in `v0.8.8`. The clean sprite redraws in `v0.9.1` make the landing footprints and hole boundaries unambiguous.

### 5. SS02 — Shared Supply
* **Core Mechanic:** A shared FIFO stream of incoming fruit arrives in a fixed order. The player routes each fruit to a selected skewer. Each skewer requires a specific target sequence shown on its order card.
* **Why It’s Elite:** Tests **long-horizon constraint satisfaction and queue dispatching**. Greedily placing the current fruit on the first matching skewer quickly starves or clogs the skewers for subsequent fruits. An agent must hold the entire arrival pipeline in memory and plan placements 6 to 10 steps ahead.
* **Benchmark Standing:** Each of the 8 levels systematically introduces a distinct mechanical constraint (conveyor belts, dual trays, blenders for disposal, shape vs. color abstraction cards, rotating carousels). Every rule is deducible from screen feedback.

---

## 3. The Contenders: Strong Games with Specific Caveats

* **PT02 (Perfect Target):** Excellent directional combat logic. Ships can only be damaged from the stern lamps, and enemy guns telegraph firing lanes one turn ahead on fixed rhythmic beats. Completely deterministic.
  * *Caveat:* Enemies never move, so once the firing cycle is deduced, it reduces to static geometric evasion. Levels 1 to 3 are too easy (random play clears level 1 consistently), though levels 6 to 8 (rotating galleons, multi-batteries) have real depth.
* **DZ02 (Dig Zone):** Rich, tactile excavation inspired by *SMB2*. Ground hardness, falling sand physics, and click limits create authentic puzzle density.
  * *Caveat:* Introduces slightly too many overlapping mechanics at once (sand physics, droppers, stars, perched states, striped creatures, energy cells). An agent struggles to isolate confounding causal factors.
* **WB03 (Windy Boats):** The core mechanic—steering one sailboat causes unanchored boats to drift downwind—is brilliant and forces multi-entity tracking.
  * *Caveat:* `WB02` had a tiny search space (300 to 13,000 states). `WB03` addressed this with a large open sea and moving hazards (krakens, serpents, reefs), but the multi-screen viewport scrolling adds visual tracking friction rather than pure logical depth.
* **BS02 (Bell Stealth):** Clean acoustic herding where ringing bells lures guards onto pressure pads while load pips transfer downhill.
  * *Caveat:* Even on level 8, the reachable state space was measured at under 800 distinct states. A basic BFS solver clears every level in milliseconds. The pink danger squares also reveal guard threat zones rather than forcing the agent to infer them.
* **TE02 (Tethered Extraction):** Fascinating concept (winding cable around posts while avoiding cutting blades).
  * *Caveat:* Despite looking like continuous geometry, the rover moves on discrete integer cells, yielding a surprisingly small state space (100–300 positions per level). Unlimited undo also allows an agent to scrub through without high stakes.

---

## 4. The Outliers: Weaker as ARC-3 Benchmarks

* **WF03 (Water Flip):** Standard water-jug volume balancing with a circuit-inversion twist. The state space is far too small (Level 1 can be beaten in 5 presses of the same button; max level is ~5,000 states), and there is virtually no penalty for random clicking.
* **SE02 (Shrine Exploration):** A massive 65×65 world where stepping on a shrine unlocks a gate 40 tiles away off-screen. It tests long-range memory of an expansive walk rather than deductive puzzle-solving.
* **ES02 (Extreme Sneeze) & LT04 (Lock Target):** Mechanically ambitious simulations, but both violate ARC-3's visual transparency rule:
  * They rely on **hidden multi-rate clocks** (civilians moving every 8th tick, doctors every 5th, gunmen every 3rd, target explosion timers) that cannot be deduced from a static frame.
  * Both feature themes (spreading an urban biological contagion, launching guided air strikes in crowded civilian sectors) that trigger automated safety refusals in many foundation models, limiting their utility in academic benchmarks.
* **FF02 (Feeding Frenzy):** An arcade survival game with dynamic tides and growth hierarchies. It tests real-time reactive evasion rather than turn-based cognitive reasoning.

---

## 5. Comparative Evaluation Matrix

| Game | Deductive Clarity | Search Depth | Visual Honesty | Consequence Calibration | Overall Benchmark Grade | Primary Reasoning Mode |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **EH02 (Eroding Horizons)** | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | **A+** | Information-as-resource, path memory |
| **BL02 (Basket Lift)** | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | **A+** | Counterweight balance, gravity inversion |
| **KT02 (Knot Tying)** | ★★★★★ | ★★★★☆ | ★★★★★ | ★★★★★ | **A** | Temporal topological ordering |
| **ST02 (Shadow Topple)** | ★★★★☆ | ★★★★★ | ★★★★★ | ★★★★☆ | **A** | Indirect spatial projection, high BFS |
| **SS02 (Shared Supply)** | ★★★★★ | ★★★★☆ | ★★★★★ | ★★★★☆ | **A** | FIFO scheduling, constraint satisfaction |
| **PT02 (Perfect Target)** | ★★★★☆ | ★★★☆☆ | ★★★★★ | ★★★★☆ | **B+** | Rhythmic timing, directional facing |
| **DZ02 (Dig Zone)** | ★★★☆☆ | ★★★★☆ | ★★★★☆ | ★★★★☆ | **B+** | Structural excavation, material costs |
| **WB03 (Windy Boats)** | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ★★★★☆ | **B** | Multi-agent downwind drift, navigation |
| **BS02 (Bell Stealth)** | ★★★★☆ | ★★☆☆☆ | ★★★★☆ | ★★★☆☆ | **B** | Acoustic herding, downhill flow |
| **TE02 (Tethered Extraction)**| ★★★☆☆ | ★★☆☆☆ | ★★★☆☆ | ★★★☆☆ | **B-** | Cable wrapping (shallow state space) |
| **WF03 (Water Flip)** | ★★★☆☆ | ★☆☆☆☆ | ★★★★☆ | ★★☆☆☆ | **C+** | Discrete liquid transfer (trivial BFS) |
| **LT04 (Lock Target)** | ★★☆☆☆ | ★★★★☆ | ★★☆☆☆ | ★★★☆☆ | **C** | Tactical simulation (hidden clocks/theme) |
| **ES02 (Extreme Sneeze)** | ★★☆☆☆ | ★★★☆☆ | ★★☆☆☆ | ★★☆☆☆ | **C** | Host-hopping (hidden clocks/theme) |
| **SE02 (Shrine Exploration)**| ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | **C-** | Remote trigger exploration (disconnected) |
| **FF02 (Feeding Frenzy)** | ★★☆☆☆ | ★★☆☆☆ | ★★★☆☆ | ★★☆☆☆ | **D+** | Real-time arcade reflex survival |

---

## 6. Recommendations for Holdout Evaluation Suites

For researchers constructing an unseen holdout benchmark from this repository:
1. **Core 5-Game Suite:** Use `EH02`, `BL02`, `KT02`, `ST02`, and `SS02`. This covers information economics, inverted counterweight physics, topology, indirect manipulation, and FIFO queue scheduling with zero rule overlap.
2. **Extended 7-Game Suite:** Add `PT02` (for rhythmic combat and directional armor) and `DZ02` (for excavation physics).
3. **Splitting Discipline:** Never split games sharing mechanics between training and holdouts. If an agent trains on `ST02`, hold out `TN36`-style indirect manipulation. If it trains on `BL02`, hold out gravity and balance mechanics.

