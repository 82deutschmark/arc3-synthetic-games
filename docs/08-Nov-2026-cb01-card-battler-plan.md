# CB01: a card battler in the style of Clash Royale (plan only, nothing built yet)

Author: Claude Sonnet 5.5
Date: 08-Nov-2026
Asked by: Mark Barney ("mechanics similar to the original Clash Royale"). He then narrowed it: "I don't want anything too crazy.
What I'm really looking for first is a plan on how it could be done." So this file is the plan and the feasibility read.
No game code has been written. Implementation waits for his go-ahead on this plan.

## Feasibility read (short, honest)

**Yes, it can be done, and a small version is a good fit.** The engine is turn based and deterministic, with a 64 by 64
picture and a fixed set of inputs. Clash Royale is real time, but its core is already a clock plus a few rules:
elixir fills at a steady rate, a hand of four cards cycles in a fixed order (it is not random after the first deal),
units walk down a lane on their own, and towers shoot. All of that can run on a tick. What we lose is the thumb
speed. What we keep is the part people actually like: spend a limited resource on the right counter at the right moment.

What is hard, honestly:
- **Readability.** A 64 by 64 picture has to hold two towers a side, two lanes, a river, a hand of four cards and a
  meter. Units will be five or six pixels across. They must be told apart by shape and colour alone, with no text.
- **Fun is unproven until someone plays it.** Turn-based Clash tends to turn into a tactics puzzle. That is fine
  for this project (it is what an ARC game is), but it is a different feeling from the phone game.
- **No hidden information.** The enemy's plan has to be visible, otherwise a person cannot learn the game cold.

## The smallest rule set that still feels like Clash Royale

The board is a tall arena. The enemy is at the top, you are at the bottom, a river runs across the middle with one
bridge in each of two lanes. Each side has two towers, one at the end of each lane.

1. **Time moves when you press.** Every press (move the lane cursor, change the selected card, or play it) lets
   one tick of the match pass: units walk, towers shoot, elixir fills. There is no wait key. Dithering costs time, just
   like in the real game. A visible bar along the side drains with the match; when it empties the match is over.
2. **Elixir.** A row of ten pips. One fills every couple of ticks. Each card shows its cost as pips on the card.
3. **A hand of four cards**, with the next card shown beside it. Playing a card sends it to the back of the line and
   brings in the next one, in a fixed order, as in the real game.
4. **Three kinds of unit, one clear counter triangle**, told apart by shape and colour:
   the Giant is slow and tough and only goes for towers; the Archers shoot from a distance and beat the Giant as it
   walks; the Swarm is cheap, fast and kills Archers, but the Giant's stomp wipes it out. Every card is one of these.
5. **You place a card at your side of a lane** (left lane or right lane). After that it acts on its own: walks,
   fights what it meets, hits the tower at the end.
6. **Two towers a side**, each with a visible health bar and a shot that hits the nearest unit in range.
7. **The enemy plays a fixed, visible script.** The top of the picture shows the enemy's elixir and the card they will
   play next. Nothing is random, so a person can read the plan and counter it. That is also what makes it a puzzle.
8. **Winning and losing are visible.** Destroy both enemy towers to win the level. You lose when both of yours fall,
   or when the clock bar empties with your side behind. Loss is shown (towers crumble, the bar empties), never a
   silent restart. Reset, undo and the loss rule follow the public games: reset restarts the level, undo takes back the
   board but never gives back clock time.

Inputs: Left and Right pick the lane, Up and Down change the selected card, Space plays it, undo as the engine defines it.
(No click needed, so a cold player can find everything with the arrow keys.)

## What I dropped, and why

King tower and its wake-up rule; spells and buildings; evolutions, rarity and card levels; double-speed elixir and
overtime; placing a unit anywhere on your half (only the lane is chosen); random starting hands; units that change
target mid-walk in clever ways; emotes; two-player. Each of these adds rules without adding the main feeling.

## What it will and will not feel like

Plays like Clash Royale: the elixir squeeze, the rotating hand, counter-playing what the enemy just dropped,
pushing one lane while defending the other, towers as the goal.
Does not: no reflexes, no free placement, no deck building, no opponent that reacts to you (the enemy is a script).

## Id

**CB01** (a Clash-style battler). Checked: no existing game here uses it, and it shares no pair of letters with any of
the 25 public games' tags. The id is only a tag; nothing readable ends up in the game.

## Art

Early-console cartridge look: flat saturated fields, no grey, no text on the play surface. The arena is one green and one
blue field split by a river and two bridges. Towers, units and cards are named sprites (not specks): the Giant is a
big square-shouldered figure, the Archers a small figure with a bow arc, the Swarm three tiny bodies. Enemy side
warm colours, your side cool colours. A card shows its unit picture and its cost as pips.

## Plan of work (if approved)

1. Build `games/cb01.py` with the engine, rules as plain functions first (tick, fight, towers), art and engine glue last.
2. Four levels: one lane with a scripted Giant push; two lanes; the enemy mixes the three kinds; a tight clock.
3. Write a solver that searches presses over the real engine and records the winning routes in `solutions/`.
4. Make previews (`tools/make_media.py`), add the catalog entry and a changelog entry, run `tools/validate.py`.
5. Check by hand in the engine that the picture reads: units told apart, the bar and the enemy's next card visible.
6. Branch and pull request. Publishing to the Games page is left to the scheduled task on the Mac Mini.
7. A plain note to the Boss: what plays like Clash Royale, what does not, what is rough.

## Open calls I made so the Boss does not have to

- Every press ticks the clock (instead of a free selection). It keeps the pressure and avoids a wait key.
- Two towers per side, no king.
- Win by destroying both enemy towers, with the clock as the fail.
- Four levels for the first version.

## Docs and changelog touchpoints

`docs/catalog.json` (entry and hash), `docs/previews/`, `docs/validation.json`, `CHANGELOG.md`, `solutions/cb01_*.py`.
No count or version is written into prose.
