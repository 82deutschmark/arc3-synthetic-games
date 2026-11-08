# Glyph tools

Made-up symbols for games that need a script nobody can read: pixel shapes that look like writing, or almost like a real character, but are not one. They follow TR87's three styles of five-by-five symbol, so a game can use them as labels, dictionary entries or signals where the shape matters and the meaning is learned from play.

Each generator writes seven symbols per family:

| Family | Shape | Rule |
| --- | --- | --- |
| A | thin strokes | one connected figure, no solid 2×2 block, no hole |
| B | closed shape | one connected figure with an enclosed hole |
| C | broken shape | several separate dashes, none longer than three cells |

Every symbol touches all four sides of its 5×5 box. Within a family the seven are far apart, with turns and mirrors counted as the same symbol. None is close to one of TR87's own 21 symbols (`tr87_originals.json`, used only for that check) or, where a font is available, to a Latin letter or digit.

## Use a set that is already made

`sets/glyphs_*.json` hold finished sets. Each file has the keys `A`, `B` and `C`, each a list of seven 5×5 grids of 0 (empty) and 1 (filled). The kana and CJK files also have `from`, the real characters each symbol was made from. Next to each file is a `.png` contact sheet. Read these first; most uses need nothing more.

## Make a new one

Run from the repo root with the virtualenv's Python (`numpy` and `Pillow` are in `requirements.txt`). The same seed always gives the same set. Output goes to `sets/` unless you pass `--out`.

```sh
.venv/bin/python tools/glyphs/tr87_glyphs_kana.py 34     # Windows: .venv\Scripts\python
```

| Script | Makes | Needs |
| --- | --- | --- |
| `tr87_glyphs_kana.py` | Real katakana and hangul, hand-drawn at 5×5, then changed by one or two pixels so each is almost a character. Best for a script that looks real and is not. | Nothing but numpy. Same result on every OS. |
| `tr87_glyphs_cjk.py` | Thousands of real CJK, hangul and kana characters shrunk to 5×5, keeping the ones that come out as clean figures. | A system font that covers those ranges (see below). |
| `tr87_glyphs.py` | Random straight strokes, the way the originals are drawn. Slow (minutes). | Pillow and a font for the letter filter; without a font the filter is skipped with a warning. |

The shipped kana sets are seeds 31, 32 and 33 and regenerate byte for byte on Windows. The shipped CJK and random-stroke sets were made on macOS with Arial Unicode, and neither regenerated identically on a Windows machine (seeds 21 and 1 were tried). Different fonts are the likely cause; it was not isolated for the random-stroke generator. Treat the shipped files as the reference and a regenerated set as a new set. A font with thin coverage draws empty boxes for characters it lacks, and those can pass as shapes, so look at a new CJK sheet before using it.

## Files

- `tr87_glyphs.py`: shared helpers (turns and mirrors, connectivity, holes, the family rules), font lookup, the random-stroke generator, the contact sheet and the command line.
- `tr87_glyphs_kana.py`, `tr87_glyphs_cjk.py`: the other two generators; they import the shared helpers.
- `tr87_originals.json`: TR87's 21 symbols as 5×5 grids, kept so new symbols can be tested against them.
- `sets/`: sample JSON sets and their sheets.
