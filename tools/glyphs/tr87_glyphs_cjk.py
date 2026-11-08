# Author: Claude Sonnet 5.5
# Date: 07-Nov-2026
# PURPOSE: Made-up symbol sets taken from real writing: shrink thousands of real CJK, hangul, kana, Yi and radical
#   characters to 5x5 and keep the ones that come out as clean figures in TR87's three styles:
#     A  thin strokes: one connected figure, no 2x2 solid block;
#     B  closed shapes: one connected figure with an enclosed hole;
#     C  broken shapes: an A figure cut into dashes (how the original broken row reads).
#   Exact Latin letters and digits, and TR87's 21 originals under any turn or mirror, are left out.
#   Needs a system font that covers the CJK ranges. The shipped sets glyphs_cjk_21/22/23 were made on macOS with
#   Arial Unicode and are checked in under tools/glyphs/sets/, so nobody needs to run this to use them. On Windows or
#   Linux the result depends on which font find_fonts() finds: a font with thin coverage draws empty boxes for missing
#   characters, which can pass as shapes, so look at the sheet before trusting a new set. Prefer tr87_glyphs_kana.py
#   when no wide-coverage font is installed.
#   Integration: imports the shared helpers, font lookup and bundled TR87 originals from tr87_glyphs.py. Output is
#   glyphs_cjk_SEED.json (source characters under "from", then rows A, B, C) and glyphs_cjk_SEED.png.
#   Usage: python tools/glyphs/tr87_glyphs_cjk.py SEED [--out DIR]   (default DIR tools/glyphs/sets/)
# SRP/DRY check: Pass - rendering (render_character), helpers, font lookup, sheet and the command line come from
#   tr87_glyphs.py; only the character ranges, the pool filter and the dash-cutting are new here.

from __future__ import annotations

import json
import random
import sys

import numpy as np
from PIL import ImageFont

import tr87_glyphs as T

# Unicode blocks drawn from: han, hangul syllables, Kangxi radicals, radical supplement, katakana, hiragana, bopomofo,
# Yi, hangul jamo.
RANGES = [(0x4E00, 0x9FFF), (0xAC00, 0xD7A3), (0x2F00, 0x2FD5), (0x2E80, 0x2EF3), (0x30A0, 0x30FF),
          (0x3040, 0x309F), (0x3100, 0x312F), (0xA000, 0xA48C), (0x3131, 0x318E)]
LATIN = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
MIN_GLYPH_SIDE = 25             # a character whose shorter side is under this many pixels at font size 60-70 is a mark, not a figure


def load_font(size: int):
    """The first usable CJK-capable system font at the given size; exits with a plain message when there is none."""
    for path in T.find_fonts():
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    sys.exit("No CJK-capable system font found (see FONT_CANDIDATES in tr87_glyphs.py). "
             "Use tr87_glyphs_kana.py, or the sets already in tools/glyphs/sets/.")


def latin_bitmaps():
    """Latin letters and digits at 5x5 in all eight turns and mirrors, to keep new glyphs away from them."""
    font = load_font(60)
    out = []
    for character in LATIN:
        for threshold in (60, 110):
            bitmap = T.render_character(character, font, threshold, min_side=MIN_GLYPH_SIDE)
            if bitmap is not None and bitmap.sum():
                out += T.d4(bitmap)
    return out


def broken(glyph, rng):
    """Cut a stroke figure into dashes of one to three cells."""
    cut = glyph.copy()
    cells = list(zip(*np.nonzero(cut)))
    rng.shuffle(cells)
    for y, x in cells:
        groups = T.components(cut)
        if len(groups) >= 4 and max(len(group) for group in groups) <= 3:
            break
        big = [group for group in groups if len(group) > 3]
        if big and (y, x) in big[0] and cut.sum() > 9:
            cut[y, x] = 0
    return cut


def pool(seed: int):
    """Candidate A and B figures (character, grid) from a shuffled sample of the ranges, plus the seeded generator."""
    rng = random.Random(seed)
    font = load_font(70)
    characters = [chr(code) for low, high in RANGES for code in range(low, high + 1)]
    rng.shuffle(characters)
    latin = latin_bitmaps()
    originals = [turned for glyph in T.original_glyphs().values() for turned in T.d4(glyph)]
    seen, thin, closed = set(), [], []
    for character in characters[:30000]:
        for threshold in (70, 95, 120):
            bitmap = T.render_character(character, font, threshold, min_side=MIN_GLYPH_SIDE)
            if bitmap is None or not T.full_box(bitmap) or bitmap.tobytes() in seen:
                continue
            seen.add(bitmap.tobytes())
            if T.distance(bitmap, latin) < 3 or T.distance(bitmap, originals) < 4:
                continue
            count, groups = int(bitmap.sum()), T.components(bitmap)
            if len(groups) != 1:
                continue
            if 9 <= count <= 14 and not T.block2(bitmap) and not T.has_hole(bitmap):
                thin.append((character, bitmap))
            elif 12 <= count <= 18 and T.has_hole(bitmap) and sum(
                    bitmap[y:y + 2, x:x + 2].all() for y in range(T.SIZE - 1) for x in range(T.SIZE - 1)) <= 1:
                closed.append((character, bitmap))
    return thin, closed, rng


def spread(candidates, count):
    """Greedy max-min Hamming distance pick of `count` (character, grid) pairs, turns and mirrors counted as the same."""
    selected = [candidates[0]]
    turned = [T.d4(candidates[0][1])]
    while len(selected) < count:
        best = max(candidates, key=lambda c: min(int((c[1] != t).sum()) for ts in turned for t in ts))
        selected.append(best)
        turned.append(T.d4(best[1]))
    return selected


if __name__ == "__main__":
    args = T.parse_args("TR87-style glyphs shrunk from real CJK, hangul and kana characters.")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args.out.mkdir(parents=True, exist_ok=True)
    thin, closed, rng = pool(args.seed)
    rng.shuffle(thin)
    rng.shuffle(closed)
    row_a = spread(thin[:300], 7)
    row_b = spread(closed[:300], 7)
    used = {glyph.tobytes() for _, glyph in row_a}
    rest = [pair for pair in thin if pair[1].tobytes() not in used]
    row_c = [(character, broken(glyph, rng)) for character, glyph in spread(rest, 7)]
    chosen = {"A": [g for _, g in row_a], "B": [g for _, g in row_b], "C": [g for _, g in row_c]}
    T.sheet(chosen, args.out / f"glyphs_cjk_{args.seed}.png")
    (args.out / f"glyphs_cjk_{args.seed}.json").write_text(
        json.dumps({"from": {"A": [c for c, _ in row_a], "B": [c for c, _ in row_b], "C": [c for c, _ in row_c]},
                    **{name: [g.tolist() for g in glyphs] for name, glyphs in chosen.items()}}, ensure_ascii=False),
        encoding="utf-8")
    print(len(thin), len(closed))
