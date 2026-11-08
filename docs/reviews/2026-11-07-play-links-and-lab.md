# Play links and the lab

Date: 7 November 2026. Author: Claude Sonnet 5.5, at Mark Barney's call. Written for the assistant who fixes the Play links. Nothing in this note has been acted on.

## The problem

Every card's Play button links to `https://arc3.sonpham.net/games/<id>`, built from the catalog's `play` field. The lab (`sonpham-org/arc-3`, served at arc3.sonpham.net) only opens games that were published to it. For any other id it still serves its page, then falls back to its browse list. So an unpublished game looks like a link that "doesn't go to the right game".

## How the lab resolves an id (read from its page script, `games-play.js`)

- Every `/games/<anything>` returns the same page (HTTP 200).
- The script asks `GET /api/v1/public/games/current?q=<id>&limit=40` and opens a game only if some `games[].head.gameId` equals `<id>` exactly. No match: the browse list.
- Check a link without a browser: `curl -s "https://arc3.sonpham.net/api/v1/public/games/current?q=<id>&limit=40"` (plain `curl`; Python's default user agent gets a 403). Empty `games` means dead.
- `/games/<id>` always opens the newest version of that id.

## State at the time of writing (checked against the catalog, 67 entries)

- Dead links: **DZ03** and **LT05**, both highlighted. Earlier the same day 13 highlighted games were dead (WB03, SS02, PT02, DZ02, LT04, ES02, EH02, FF02, BS02, WF03, ST02, BL02, KT02); they now resolve, so someone published them.
- **Collisions, still open:** TE02 and SE02 resolve, but to different games. The lab's `te02` was published 2026-10-27 by GPT-6 (Codex); its `se02` on 2026-10-15 by Claude Opus 5.5. The Play button for our TE02 and SE02 opens those, not ours. Publishing ours under the same ids would make them the newest version, and the older games would drop down the tree. Either rename ours, or publish ours as a branch with `--parent` on purpose. Ask Mark; I recommended renaming.
- The catalog's `play` field for older games uses the lab's own ids where they differ from ours (for example st01 links to `g014`, bs01 to `g019`, kt01 to `g036`, se01 to `xb02`). Do not "tidy" those without checking the lab.

## How games reach the lab (from `arc-3/AGENTS.md` and its README)

- Through `scripts/publish_game_versions.py publish`, which calls the lab's API with `ARC3_PUBLISH_TOKEN`. Not through git, not a deploy. The token was not available to me.
- `publish` refuses a source unless `scripts/vet_game.py` passed for those exact bytes. The gate needs a recorded winning trace for every level, and checks that level 1 can't be lost, random play doesn't die in the first 10 actions, levels 2 and up can't be cleared by random play, and every action stays under 60 frames. `--no-vet <reason>` skips it and is meant for historical backfill; the reason goes on the public page. Use it only if Mark says so.
- A new game also needs an entry in `docs/static/games/groups.json` (`--group reskin|variant|original`, `--based-on <public id>`), committed in `arc-3`.
- The lab's rule is that games must not speak: no text on the play surface. Our games draw no letters or digits; I have not run the lab's own check on them.
- Mark has admin on `sonpham-org/arc-3` and said there is no publishing problem. My local clone at `C:\Projects\arc-3` is about 124 commits behind and hits Windows path-length errors on pull, so work from a fresh checkout.

## What LT05 and DZ03 need

Neither has been vetted or published. LT05 is nine missions with a scripted clear of every mission in the real engine (signal then precision), now in `solutions/lt05_clear_missions.py`. It reads engine internals, so it is an oracle-style script, not a frames-only agent. LT05's level 1 can't be lost, but the vet gate's other checks have not been run on it.

## Not done

I did not publish anything, change a Play link, or touch the lab repo.
