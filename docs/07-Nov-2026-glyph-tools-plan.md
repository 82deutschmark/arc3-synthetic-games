# Glyph tools: bring the TR87-style symbol generators into this repo

Author: Claude Sonnet 5.5
Date: 07-Nov-2026
Asked by: Mark Barney ("make sure those old files for making the glyphs get moved into this repository ... they will be useful for people making synthetic games ... don't make a mess ... file headers up to the coding standards").
Status: done, with the checks and their limits listed under Verification. Written alongside the work because the move was explicitly requested.

## Scope

In: the three generators of made-up five-by-five symbol sets in TR87's three styles, their shared helpers, TR87's 21 original symbols as data (used only to keep new symbols away from them), the sample sets that were already generated, and a short README. Out: the copycats project's reskin builders (`build_tr87_kana.py`, `build_views.py`, `publish_views.py`), which are tied to that project's internals and to TR87 reskins; nothing is deleted from the copycats project (this is a copy).

## Architecture

All in `tools/glyphs/`: `tr87_glyphs.py` (shared helpers, font lookup, rendering, the random-stroke generator, the contact sheet and the command line), `tr87_glyphs_kana.py` and `tr87_glyphs_cjk.py` (import the helpers; only their own tables and filters are new), `tr87_originals.json`, `sets/` (sample JSON and PNG sheets). No other part of the repo imports them.

Changes from the originals, all for any-OS use and the repo rules: TR87's 21 symbols come from a bundled JSON instead of another project's file; system fonts are looked up across macOS, Windows and Linux instead of two macOS paths, and a missing font gives a clear message (or skips the letter filter in the random generator); outputs go to `--out` (default `tools/glyphs/sets/`) and are written as UTF-8 (the originals would fail on a Windows default encoding); a console that is not UTF-8 no longer breaks the kana printout; magic numbers are named; the file headers follow `CODING_STANDARDS.md`. The algorithms and their random-number order are unchanged.

## Verification

1. Regenerate the kana seeds 31, 32 and 33 and compare byte for byte with the shipped sets. Result: identical, all three, on Windows.
2. Regenerate the CJK set (seed 21) and the random-stroke set (seed 1). Result: both run to the end on Windows (CJK in about half a minute, random strokes in about four minutes), and neither matches its shipped set byte for byte. The shipped sets used macOS's Arial Unicode and this machine's fonts are MS Gothic and Malgun Gothic, which is the likely cause. I did not isolate it for the random-stroke generator (for instance by running it with the letter filter off on both machines), so that is a guess. The regenerated CJK set passes the rule check below. Whether it contains empty-box glyphs from missing characters has not been looked at.
3. Check every shipped set and the regenerated CJK set: seven glyphs per row, 5×5, none equal to another under any turn or mirror, none equal to a TR87 original. Result: all pass.

## Docs and changelog

`tools/glyphs/README.md`, a row in `README.md` and the layout list in `AGENTS.md`, and a `CHANGELOG.md` entry. No game changed, so no hash or preview changes.
