# Author: Claude Sonnet 5.5
# Date: 07-Nov-2026
# PURPOSE: Shared core and the random-stroke generator for made-up symbol sets in the style of TR87's 21 glyphs
#   (ported from the copycats project, where it made reskins of TR87). TR87 draws 21 five-by-five symbols in three
#   families of seven, and its rules compare only symbol names, so a new set changes the look and nothing else.
#   Each family keeps the original's style:
#     A  thin strokes: one connected figure, no 2x2 solid block, spans the full 5x5 box;
#     B  closed shapes: one connected figure with an enclosed hole, spans the full box;
#     C  broken shapes: three or more separate dashes, no dash longer than three cells.
#   Within a family the seven symbols are far apart (Hamming distance, turns and mirrors counted as the same), and none is
#   close to any of TR87's originals (tr87_originals.json, bundled) or to a real Latin letter, digit or common CJK or
#   kana character under any turn or mirror. tr87_glyphs_kana.py and tr87_glyphs_cjk.py import the helpers here.
#   Integration: pure numpy plus Pillow (both in requirements.txt). The letter-likeness filter needs a system font
#   with CJK coverage (find_fonts); with none it is skipped and a warning is printed. The sets checked in under
#   tools/glyphs/sets/ were made on macOS, so they are reproducible without any font.
#   Usage: python tools/glyphs/tr87_glyphs.py SEED [--out DIR]  -> prints the set as JSON, writes glyphs_SEED.png to DIR
#   (default tools/glyphs/sets/).
# SRP/DRY check: Pass - searched the repo: no other glyph generator exists; the 5x5 helpers live only here and the
#   kana and CJK generators import them rather than copying them.

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "sets"
SIZE = 5

# System fonts that cover kana, hangul and han, in the order tried. Files that do not exist are skipped.
FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",     # macOS (what the shipped sets were made with)
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "C:/Windows/Fonts/arialuni.ttf",                            # Windows, when Office installed it
    "C:/Windows/Fonts/msgothic.ttc",                            # Windows: kana and han
    "C:/Windows/Fonts/malgun.ttf",                              # Windows: hangul
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",   # Linux
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
)


def find_fonts() -> list[str]:
    """Every candidate font that exists on this machine."""
    return [path for path in FONT_CANDIDATES if Path(path).exists()]


def d4(grid):
    """The eight turns and mirrors of a grid. Two glyphs that are equal under any of these count as the same glyph."""
    out = []
    for quarter_turns in range(4):
        turned = np.rot90(grid, quarter_turns)
        out += [turned, turned[:, ::-1]]
    return out


def components(grid):
    """Connected groups of filled cells (four-neighbour)."""
    seen, groups = set(), []
    for y, x in zip(*np.nonzero(grid)):
        if (y, x) in seen:
            continue
        stack, group = [(y, x)], []
        seen.add((y, x))
        while stack:
            cy, cx = stack.pop()
            group.append((cy, cx))
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < SIZE and 0 <= nx < SIZE and grid[ny, nx] and (ny, nx) not in seen:
                    seen.add((ny, nx))
                    stack.append((ny, nx))
        groups.append(group)
    return groups


def has_hole(grid):
    """An empty cell not reachable from the border through empty cells."""
    empty = 1 - grid
    stack = [(y, x) for y in range(SIZE) for x in range(SIZE) if (y in (0, SIZE - 1) or x in (0, SIZE - 1)) and empty[y, x]]
    seen = set(stack)
    while stack:
        cy, cx = stack.pop()
        for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
            if 0 <= ny < SIZE and 0 <= nx < SIZE and empty[ny, nx] and (ny, nx) not in seen:
                seen.add((ny, nx))
                stack.append((ny, nx))
    return int(empty.sum()) > len(seen)


def block2(grid):
    """True when any 2x2 square is solid."""
    return any(grid[y:y + 2, x:x + 2].all() for y in range(SIZE - 1) for x in range(SIZE - 1))


def full_box(grid):
    """True when the figure touches all four sides of its box."""
    return grid[0].any() and grid[SIZE - 1].any() and grid[:, 0].any() and grid[:, SIZE - 1].any()


def family_ok(family, grid):
    """Whether a grid is a valid member of family A, B or C."""
    count, groups = int(grid.sum()), components(grid)
    if not full_box(grid):
        return False
    if family == "A":
        return 9 <= count <= 13 and len(groups) == 1 and not block2(grid) and not has_hole(grid)
    if family == "B":
        return 13 <= count <= 18 and len(groups) == 1 and has_hole(grid)
    return 9 <= count <= 13 and len(groups) >= 3 and max(len(group) for group in groups) <= 3


def segment(grid, y, x, dy, dx, length):
    for step in range(length):
        if 0 <= y + dy * step < SIZE and 0 <= x + dx * step < SIZE:
            grid[y + dy * step, x + dx * step] = 1


def grow(rng, family):
    """A candidate built from straight strokes, the way the originals are drawn."""
    grid = np.zeros((SIZE, SIZE), dtype=np.int8)
    if family == "C":
        for _ in range(rng.randint(4, 6)):
            dy, dx = rng.choice([(0, 1), (1, 0)])
            segment(grid, rng.randrange(SIZE), rng.randrange(SIZE), dy, dx, rng.randint(1, 3))
        return grid
    if family == "B":
        height, width = rng.randint(3, 5), rng.randint(3, 5)
        top, left = rng.randint(0, SIZE - height), rng.randint(0, SIZE - width)
        segment(grid, top, left, 0, 1, width)
        segment(grid, top + height - 1, left, 0, 1, width)
        segment(grid, top, left, 1, 0, height)
        segment(grid, top, left + width - 1, 1, 0, height)
        strokes = rng.randint(1, 3)
    else:
        strokes = rng.randint(3, 4)
        dy, dx = rng.choice([(0, 1), (1, 0)])
        if dx:
            segment(grid, rng.randrange(SIZE), 0, 0, 1, SIZE)
        else:
            segment(grid, 0, rng.randrange(SIZE), 1, 0, SIZE)
    for _ in range(strokes):
        cells = list(zip(*np.nonzero(grid)))
        y, x = rng.choice(cells)
        dy, dx = rng.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
        segment(grid, y, x, dy, dx, rng.randint(2, 4))
    return grid


# Characters whose look the random strokes must stay away from: Latin, digits, simple han, kana, hangul, symbols.
SCRIPTS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    "一二三十工土士口日田山川人入大小中王丁七卜上下己已弓门干千于才寸廿卄丰円目且旦由甲申电互丑正止巾冂匚凵"
    "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
    "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ#+=<>/%&$@"
)


def render_character(character: str, font, threshold: int, canvas: int = 100, origin=(15, 5), min_side: int = 0):
    """One character drawn by a font and shrunk to a SIZE x SIZE bitmap, or None when it draws nothing usable
    (blank, or its shorter side under min_side pixels, which drops thin marks such as 'l' or a dot)."""
    from PIL import Image, ImageDraw
    image = Image.new("L", (canvas, canvas), 0)
    ImageDraw.Draw(image).text(origin, character, fill=255, font=font)
    box = image.getbbox()
    if not box:
        return None
    cropped = image.crop(box)
    if min(cropped.size) < min_side:
        return None
    side = max(cropped.size)
    square = Image.new("L", (side, side), 0)
    square.paste(cropped, ((side - cropped.size[0]) // 2, (side - cropped.size[1]) // 2))
    return (np.array(square.resize((SIZE, SIZE), Image.BOX)) > threshold).astype(np.int8)


def script_bitmaps():
    """Every character in SCRIPTS drawn by the system fonts at SIZE x SIZE, in all eight turns and mirrors.
    Empty when no usable font exists, in which case the caller skips the letter-likeness filter."""
    from PIL import ImageFont
    fonts = []
    for path in find_fonts():
        try:
            fonts.append(ImageFont.truetype(path, 60))
        except OSError:
            continue
    out = []
    for character in SCRIPTS:
        for font in fonts:
            for threshold in (60, 110):
                bitmap = render_character(character, font, threshold, canvas=90, origin=(10, 5))
                if bitmap is not None and bitmap.sum():
                    out += d4(bitmap)
    return out


def original_glyphs() -> dict:
    """TR87's own 21 symbols (A1..A7, B1..B7, C1..C7) as 5x5 0/1 arrays, from the bundled tr87_originals.json.
    They are used only to keep new glyphs away from them."""
    raw = json.loads((HERE / "tr87_originals.json").read_text(encoding="utf-8"))
    return {name: np.array(rows, dtype=np.int8) for name, rows in raw.items()}


def distance(candidate, others) -> int:
    """Smallest number of differing cells between a candidate and any grid in others."""
    return min(int((candidate != other).sum()) for other in others)


def pick(seed: int):
    rng = random.Random(seed)
    near_orig = [turned for grid in original_glyphs().values() for turned in d4(grid)]
    letters = script_bitmaps()
    if not letters:
        print("warning: no CJK-capable system font found; skipping the letter-likeness filter", file=sys.stderr)
    chosen = {}
    for family in "ABC":
        pool, keys, tries = [], set(), 0
        while len(pool) < 400 and tries < 400000:
            tries += 1
            grid = grow(rng, family)
            key = grid.tobytes()
            if key in keys or not family_ok(family, grid):
                continue
            if distance(grid, near_orig) < 5:
                continue
            if letters and distance(grid, letters) < 4:
                continue
            keys.add(key)
            pool.append(grid)
        # greedy max-min Hamming distance, also against turns and mirrors of the others
        selected, turned = [pool[0]], [d4(pool[0])]
        while len(selected) < 7:
            best = max(pool, key=lambda c: min(int((c != t).sum()) for ts in turned for t in ts))
            selected.append(best)
            turned.append(d4(best))
        chosen[family] = selected
    return chosen


def sheet(chosen, path):
    """A contact sheet: one row per family, seven glyphs per row, black on white."""
    from PIL import Image, ImageDraw
    scale, gap = 12, 10
    image = Image.new("RGB", (7 * (SIZE * scale + gap) + gap, 3 * (SIZE * scale + gap) + gap), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    for row, family in enumerate("ABC"):
        for column, grid in enumerate(chosen[family]):
            for y, x in zip(*np.nonzero(grid)):
                x0, y0 = gap + column * (SIZE * scale + gap) + x * scale, gap + row * (SIZE * scale + gap) + y * scale
                draw.rectangle([x0, y0, x0 + scale - 1, y0 + scale - 1], fill=(0, 0, 0))
    image.save(path)


def parse_args(description: str) -> argparse.Namespace:
    """The command line shared by the three generators: a seed and an output directory."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("seed", type=int, help="random seed; the same seed always gives the same set")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="where to write the sheet and JSON (default tools/glyphs/sets)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args("Random-stroke TR87-style glyph set.")
    args.out.mkdir(parents=True, exist_ok=True)
    result = pick(args.seed)
    sheet(result, args.out / f"glyphs_{args.seed}.png")
    print(json.dumps({family: [grid.tolist() for grid in grids] for family, grids in result.items()}))
