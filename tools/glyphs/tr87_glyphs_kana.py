# Author: Claude Sonnet 5.5
# Date: 07-Nov-2026
# PURPOSE: Made-up symbol sets that look like almost-a-character: real katakana and hangul, hand-drawn cleanly at TR87's
#   5x5 size (the BASE table), then changed by one or two pixels (a stroke end moved, a tick added or dropped) so each reads
#   as a character that is slightly off and is not any real one. Sorted into TR87's three rows by shape: A one open
#   figure, B one figure with a closed loop, C several separate strokes. Each pixel change keeps the symbol in its row.
#   Seven per row, kept at least a pixel away from TR87's 21 originals under any turn or mirror. This is the generator
#   to use for new games: it needs only numpy (no fonts), so it gives the same result on every OS.
#   Integration: imports the shared 5x5 helpers and the bundled TR87 originals from tr87_glyphs.py. Output is
#   glyphs_kana_SEED.json (the source characters under "from", then the A, B and C rows as 5x5 0/1 grids) and
#   glyphs_kana_SEED.png. The checked-in sets glyphs_kana_31/32/33 in tools/glyphs/sets/ are seeds 31, 32 and 33.
#   Usage: python tools/glyphs/tr87_glyphs_kana.py SEED [--out DIR]   (default DIR tools/glyphs/sets/)
# SRP/DRY check: Pass - the helpers (d4, components, has_hole, block2, full_box, sheet, original_glyphs, parse_args) are
#   imported from tr87_glyphs.py; only the character table and the nudging logic are new here.

from __future__ import annotations

import json
import random
import sys

import numpy as np

import tr87_glyphs as T

# Real characters as 5x5 row strings ('#' filled), separated by '|'.
BASE = {
    "コ": "#####|....#|....#|....#|#####", "ヨ": "#####|....#|#####|....#|#####",
    "ユ": "####.|...#.|...#.|...#.|#####", "ロ": "#####|#...#|#...#|#...#|#####",
    "サ": ".#.#.|#####|.#.#.|...#.|..#..", "キ": "..#..|#####|..#..|#####|..#..",
    "ケ": ".#...|#####|#..#.|...#.|..#..", "ヒ": "#....|#..##|###..|#....|#####",
    "レ": "#....|#....|#....|#..#.|###..", "ム": "..#..|..#..|.#...|#..#.|#####",
    "ラ": "#####|.....|#####|...#.|.##..", "ニ": ".###.|.....|.....|.....|#####",
    "ハ": ".#.#.|.#..#|#...#|#...#|.....", "ツ": "#.#.#|#.#.#|....#|...#.|###..",
    "シ": "##...|....#|##..#|...#.|###..", "カ": ".#...|#####|.#..#|.#..#|#..##",
    "チ": "####.|..#..|#####|..#..|.#...", "テ": "#####|.....|#####|..#..|.#...",
    "ナ": "..#..|#####|..#..|..#..|.#...", "フ": "#####|....#|....#|...#.|.##..",
    "ホ": "..#..|#####|..#..|#.#.#|..#..", "ヲ": "#####|....#|#####|...#.|.##..",
    "ワ": "#####|#...#|....#|...#.|.##..", "ン": "#....|.#..#|....#|...#.|###..",
    "구": "####.|...#.|#####|..#..|..#..", "나": "#..#.|#..#.|#..##|#..#.|####.",
    "마": "###.#|#.#.#|#.###|#.#.#|###.#", "바": "#.#.#|#####|#.#.#|###.#|....#",
    "거": "###.#|..#.#|..###|..#.#|..#.#", "너": "#...#|#...#|#.###|#...#|###.#",
    "더": "###.#|#...#|#.###|#...#|###.#", "오": ".###.|.#.#.|.###.|..#..|#####",
    "그": "####.|...#.|...#.|.....|#####", "고": "####.|...#.|.....|..#..|#####",
    "다": "###.#|#...#|#..##|#...#|###.#", "라": "###.#|..#.#|#####|#...#|###.#",
    "호": "..#..|#####|.#.#.|.###.|#####", "비": "#.#.#|#####|#.#.#|###.#|....#",
    "도": "####.|#....|####.|..#..|#####", "토": "####.|#....|####.|#.#..|#####",
    "로": "###..|..#..|###..|#.#..|#####", "모": "####.|#..#.|####.|..#..|#####",
}


def grid(rows: str):
    """'#####|....#|...' to a 5x5 0/1 array."""
    return np.array([[1 if cell == "#" else 0 for cell in row] for row in rows.split("|")], dtype=np.int8)


def family(glyph) -> str:
    """Which TR87 row a glyph belongs to: C several strokes, B one figure with a closed loop, A one open figure."""
    if len(T.components(glyph)) > 1:
        return "C"
    return "B" if T.has_hole(glyph) else "A"


def nudge(glyph, rng, edits: int):
    """Change `edits` pixels next to the strokes (drop a stroke end or add a neighbour), keeping the row the same.
    Returns None when 200 tries find no valid change."""
    original_family = family(glyph)
    neighbours = ((0, 1), (1, 0), (0, -1), (-1, 0))
    for _ in range(200):
        changed = glyph.copy()
        for _ in range(edits):
            filled = list(zip(*np.nonzero(changed)))
            near = {(y + dy, x + dx) for y, x in filled for dy, dx in neighbours
                    if 0 <= y + dy < T.SIZE and 0 <= x + dx < T.SIZE and not changed[y + dy, x + dx]}
            ends = [(y, x) for y, x in filled
                    if sum(1 for dy, dx in neighbours
                           if 0 <= y + dy < T.SIZE and 0 <= x + dx < T.SIZE and changed[y + dy, x + dx]) == 1]
            if rng.random() < 0.5 and ends:
                y, x = rng.choice(ends)
                changed[y, x] = 0
            else:
                y, x = rng.choice(sorted(near))
                changed[y, x] = 1
        if (family(changed) == original_family and not T.block2(changed) and changed.sum() >= 7
                and T.full_box(changed) and (changed != glyph).sum() == edits):
            return changed
    return None


def build(seed: int) -> dict:
    """Seven glyphs per row from one seed: {"from": {row: [characters]}, "A": [...], "B": [...], "C": [...]}."""
    rng = random.Random(seed)
    originals = [turned for glyph in T.original_glyphs().values() for turned in T.d4(glyph)]
    rows = {"A": [], "B": [], "C": []}
    names = list(BASE)
    rng.shuffle(names)
    for character in names:
        nudged = nudge(grid(BASE[character]), rng, rng.choice([1, 2]))
        if nudged is None or T.distance(nudged, originals) < 3:
            continue
        row = family(nudged)
        if len(rows[row]) < 7:
            rows[row].append((character, nudged))
    # top up a short row with a second nudge of a character already in that row's family
    for row_name, row in rows.items():
        pool = [character for character in names if family(grid(BASE[character])) == row_name]
        turn = 0
        while len(row) < 7 and pool:
            character = pool[turn % len(pool)]
            turn += 1
            nudged = nudge(grid(BASE[character]), rng, 2)
            if nudged is not None and all((nudged != other).sum() > 1 for _, other in row):
                row.append((character, nudged))
    return rows


if __name__ == "__main__":
    args = T.parse_args("Katakana and hangul nudged by one or two pixels: TR87-style glyphs that are almost characters.")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")        # the console may not be UTF-8 (Windows)
    args.out.mkdir(parents=True, exist_ok=True)
    rows = build(args.seed)
    chosen = {name: [glyph for _, glyph in row] for name, row in rows.items()}
    T.sheet(chosen, args.out / f"glyphs_kana_{args.seed}.png")
    (args.out / f"glyphs_kana_{args.seed}.json").write_text(
        json.dumps({"from": {name: [character for character, _ in row] for name, row in rows.items()},
                    **{name: [glyph.tolist() for glyph in glyphs] for name, glyphs in chosen.items()}},
                   ensure_ascii=False),
        encoding="utf-8")
    print({name: "".join(character for character, _ in row) for name, row in rows.items()})
