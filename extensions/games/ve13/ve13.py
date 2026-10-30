# Author: Claude Opus 5.5 High (18-Oct-2026, the mirror stamp); Claude Sonnet 5.5 High (15-Oct-2026, the first glow-up)
# Date: 18-October-2026
# PURPOSE: ve13, a glow-up of a cn04 control copy with one new rule: mirror stamps. Click a piece to hold it, arrows
#   move it, ACTION5 turns it; a level is won when every connector dot sits on exactly one dot of its own hidden kind.
#   New: black bow-tie stamps printed on the board flip the held piece left to right when it slides onto one, and every
#   level has a piece that only fits once mirrored, which no amount of turning can do. Built by build_ve13.py from the
#   published copy; levels by gen_ve13.py. The view layer at the bottom (colours, half turn) is unchanged.
# SRP/DRY check: Pass -- the game is one class; the stamp rule is two small methods (vstamp_cells, vmirror) called from
#   the arrow move, drawn in the interface; everything else is the copy's own code.
# CHANGELOG 18-Oct-2026 (Claude Opus 5.5 High): mirror stamps; seven new levels that each need one (a mirrored piece);
#   the held piece's frame is yellow, not pink; a mismatched landing flashes black, not red. The Boss: "It's just
#   another box around the game. We could do better."
# CHANGELOG 15-Oct-2026 (Claude Sonnet 5.5 High): glow-up of the control copy, no rule change. The held piece wears a pink outline; a dot that lands on a matching dot flashes and stays green, a mismatched landing flashes red and goes back; dots are orange so green means paired.
# ve13: single-file ARC-AGI-3 game (colours changed; the screen is shown half turn).
# Rule code below: ARC Prize Foundation, MIT licence (notice follows).
#
# MIT License
#
# Copyright (c) 2026 ARC Prize Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Dict, List, Tuple

import numpy as np
from arcengine import (
    ActionInput,
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)
from numpy import ndarray

sprites = {
    "0000pusfglvcns": Sprite(
        pixels=[
            [12, 12, 12, -1, -1, -1],
            [12, -1, 12, 12, 12, 8],
            [12, -1, -1, -1, -1, -1],
            [12, -1, 12, 12, 12, 13],
            [12, 12, 12, -1, -1, -1],
        ],
        name="0000pusfglvcns",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0001gqwehbicqu": Sprite(
        pixels=[
            [-1, 14, 14, 14],
            [-1, 14, -1, 14],
            [8, 14, -1, 14],
            [-1, 14, -1, 14],
            [13, 14, -1, 14],
            [-1, 14, -1, 14],
            [-1, 14, 14, 14],
        ],
        name="0001gqwehbicqu",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0002gbumdnqksn": Sprite(
        pixels=[
            [-1, -1, -1, 11, 11, 11, -1],
            [-1, 8, -1, 11, -1, 11, 8],
            [-1, 11, 11, 11, -1, 11, -1],
            [13, 11, -1, -1, -1, 11, -1],
            [-1, 11, 11, 11, -1, 11, -1],
            [-1, -1, -1, 11, 11, 11, -1],
            [-1, -1, -1, -1, 13, -1, -1],
        ],
        name="0002gbumdnqksn",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0003phpzvjydcv": Sprite(
        pixels=[
            [-1, -1, 8, 14, -1],
            [-1, -1, -1, 14, -1],
            [-1, -1, -1, 14, 13],
            [-1, -1, -1, 14, -1],
            [-1, -1, -1, 14, 8],
            [13, -1, -1, 14, -1],
            [14, 14, 14, 14, -1],
        ],
        name="0003phpzvjydcv",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0004tbubdookfx": Sprite(
        pixels=[
            [15, 15, 15],
            [15, -1, 15],
            [15, -1, 15],
            [15, -1, 8],
            [15, -1, -1],
            [15, 13, -1],
        ],
        name="0004tbubdookfx",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0005xgnvywyzea": Sprite(
        pixels=[
            [13, 9, 9],
            [-1, -1, 9],
            [8, 9, 9],
        ],
        name="0005xgnvywyzea",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0006wivqfyaxzr": Sprite(
        pixels=[
            [11, 11, 11, 11, 11],
            [11, -1, -1, -1, 11],
            [11, 11, 11, 11, 11],
            [-1, 11, -1, 11, -1],
            [-1, 13, -1, 8, -1],
        ],
        name="0006wivqfyaxzr",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0007wxbjxicjeu": Sprite(
        pixels=[
            [-1, 12, 13],
            [12, 12, -1],
            [12, -1, -1],
            [12, 12, -1],
            [-1, 12, 8],
        ],
        name="0007wxbjxicjeu",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0008unyvsrmvhb": Sprite(
        pixels=[
            [8, -1, -1, -1, 13],
            [10, -1, 10, -1, 10],
            [10, 10, 10, 10, 10],
            [-1, 8, -1, 13, -1],
        ],
        name="0008unyvsrmvhb",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0009hlzrfewrmd": Sprite(
        pixels=[
            [13, 11],
            [-1, 11],
            [-1, 11],
            [-1, 11],
            [-1, 11],
            [-1, 13],
        ],
        name="0009hlzrfewrmd",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0010uuknhqagrb": Sprite(
        pixels=[
            [8, -1, -1, -1, -1, -1, 13],
            [14, -1, -1, -1, -1, -1, 14],
            [14, 14, 14, -1, 14, 14, 14],
            [-1, -1, 14, -1, 14, -1, -1],
            [-1, -1, 14, 14, 14, -1, -1],
        ],
        name="0010uuknhqagrb",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0011vjpznxltqu": Sprite(
        pixels=[
            [15, 15, 15, 15, 15, 15, -1],
            [15, -1, -1, -1, -1, 15, 13],
            [15, -1, 15, 15, 15, 15, -1],
            [15, -1, 15, -1, -1, -1, -1],
            [15, -1, 15, -1, -1, -1, -1],
            [15, 15, 15, -1, -1, -1, -1],
            [-1, 8, -1, -1, -1, -1, -1],
        ],
        name="0011vjpznxltqu",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0012ubfwjimbbi": Sprite(
        pixels=[
            [10, 10, 10, 10, 10, 8, -1, -1],
            [10, -1, -1, -1, 10, -1, -1, -1],
            [10, -1, 10, -1, 10, -1, -1, -1],
            [10, -1, 10, 10, 10, 10, -1, -1],
            [10, -1, -1, -1, -1, -1, -1, -1],
            [10, 10, 10, 10, 10, 10, 10, 8],
        ],
        name="0012ubfwjimbbi",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0013quifjzcfgq": Sprite(
        pixels=[
            [8, 14, -1, 14, 8],
            [-1, 14, -1, 14, -1],
            [-1, 14, -1, 14, -1],
            [-1, 14, 14, 14, -1],
        ],
        name="0013quifjzcfgq",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0014njoasulfiw": Sprite(
        pixels=[
            [8],
            [11],
            [8],
        ],
        name="0014njoasulfiw",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0015wrcdrghheq": Sprite(
        pixels=[
            [8, 12, 12, 12],
            [-1, 12, -1, 12],
            [-1, 12, -1, 12],
            [-1, 12, -1, 12],
            [-1, 12, -1, 12],
            [8, 12, 12, 12],
        ],
        name="0015wrcdrghheq",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0016eyjszpslzw": Sprite(
        pixels=[
            [-1, 11, 8, -1],
            [8, 11, -1, -1],
            [-1, 11, 11, 13],
            [-1, 0, -1, -1],
        ],
        name="0016eyjszpslzw",
        visible=True,
        collidable=True,
        tags=["sys_click"],
        layer=1,
    ),
    "0017zfrsgnupoj": Sprite(
        pixels=[
            [-1, 11, 8, -1],
            [8, 11, -1, -1],
            [-1, 11, 11, 13],
            [8, 11, -1, -1],
            [-1, 0, -1, -1],
        ],
        name="0017zfrsgnupoj",
        visible=False,
        collidable=True,
        tags=["sys_click"],
        layer=2,
    ),
    "0018daqpyadwyx": Sprite(
        pixels=[
            [-1, 11, 8, -1, -1, -1],
            [8, 11, -1, -1, -1, -1],
            [-1, 11, 11, 13, -1, -1],
            [8, 11, -1, -1, -1, -1],
            [-1, 11, 11, 11, 11, 8],
            [-1, 0, -1, -1, -1, -1],
        ],
        name="0018daqpyadwyx",
        visible=False,
        collidable=True,
        tags=["sys_click"],
        layer=3,
    ),
    "0019hytjnxfdiw": Sprite(
        pixels=[
            [-1, 11, 8, -1, -1, -1],
            [8, 11, -1, -1, -1, -1],
            [-1, 11, 11, 13, -1, -1],
            [8, 11, -1, -1, -1, -1],
            [-1, 11, 11, 11, 11, 8],
            [8, 11, -1, -1, -1, -1],
            [-1, 0, -1, -1, -1, -1],
        ],
        name="0019hytjnxfdiw",
        visible=False,
        collidable=True,
        tags=["sys_click"],
        layer=4,
    ),
    "0020sgbkbumnay": Sprite(
        pixels=[
            [-1, 11, 8, -1, -1, -1],
            [8, 11, -1, -1, -1, -1],
            [-1, 11, 11, 13, -1, -1],
            [8, 11, -1, -1, -1, -1],
            [-1, 11, 11, 11, 11, 8],
            [8, 11, -1, -1, -1, -1],
            [-1, 11, 11, 11, 13, -1],
        ],
        name="0020sgbkbumnay",
        visible=False,
        collidable=True,
        tags=["sys_click"],
        layer=5,
    ),
    "0021aifjorrdrv": Sprite(
        pixels=[
            [8, -1, 8, -1, 8],
            [14, -1, 14, -1, 14],
            [14, 14, 14, 14, 14],
        ],
        name="0021aifjorrdrv",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0022anglfyizgt": Sprite(
        pixels=[
            [8, 10, 10, 10, 10],
            [-1, -1, -1, -1, 10],
            [-1, 13, 10, 10, 10],
        ],
        name="0022anglfyizgt",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0023ltzbbieezx": Sprite(
        pixels=[
            [-1, 8, 12],
            [-1, -1, 12],
            [13, 12, 12],
        ],
        name="0023ltzbbieezx",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0024qhluijbtoy": Sprite(
        pixels=[
            [-1, 13, -1, -1, -1, -1],
            [11, 11, 11, 11, 11, 13],
            [8, -1, -1, -1, 11, -1],
            [-1, -1, -1, -1, 11, -1],
            [-1, -1, -1, -1, 11, -1],
            [8, 11, -1, -1, 11, -1],
            [-1, 11, 11, 11, 11, 8],
            [-1, -1, 13, -1, -1, -1],
        ],
        name="0024qhluijbtoy",
        visible=False,
        collidable=True,
        tags=["sys_click"],
        layer=6,
    ),
    "0025fqnvowynnz": Sprite(
        pixels=[
            [-1, 0, 11, 11, 11, 13],
            [-1, -1, -1, -1, 11, -1],
            [-1, -1, -1, -1, 11, -1],
            [-1, -1, -1, -1, 11, -1],
            [8, 11, -1, -1, 11, -1],
            [-1, 11, 11, 11, 11, 8],
            [-1, -1, 13, -1, -1, -1],
        ],
        name="0025fqnvowynnz",
        visible=False,
        collidable=True,
        tags=["sys_click"],
        layer=5,
    ),
    "0026xtzwfwcsfz": Sprite(
        pixels=[
            [-1, -1, -1, 0, 11, 13],
            [-1, -1, -1, -1, 11, -1],
            [-1, -1, -1, -1, 11, -1],
            [-1, -1, -1, -1, 11, -1],
            [8, 11, -1, -1, 11, -1],
            [-1, 11, 11, 11, 11, 8],
            [-1, -1, 13, -1, -1, -1],
        ],
        name="0026xtzwfwcsfz",
        visible=False,
        collidable=True,
        tags=["sys_click"],
        layer=4,
    ),
    "0027endmofvmye": Sprite(
        pixels=[
            [-1, -1, -1, -1, 0, -1],
            [-1, -1, -1, -1, 11, -1],
            [-1, -1, -1, -1, 11, -1],
            [8, 11, -1, -1, 11, -1],
            [-1, 11, 11, 11, 11, 8],
            [-1, -1, 13, -1, -1, -1],
        ],
        name="0027endmofvmye",
        visible=False,
        collidable=True,
        tags=["sys_click"],
        layer=3,
    ),
    "0028qfdlavxmxn": Sprite(
        pixels=[
            [-1, -1, -1, -1, 0, -1],
            [8, 11, -1, -1, 11, -1],
            [-1, 11, 11, 11, 11, 8],
            [-1, -1, 13, -1, -1, -1],
        ],
        name="0028qfdlavxmxn",
        visible=False,
        collidable=True,
        tags=["sys_click"],
        layer=2,
    ),
    "0029vpufvyeoxr": Sprite(
        pixels=[
            [8, 11, -1, -1, -1, -1],
            [-1, 11, 11, 11, 0, -2],
            [-1, -1, 13, -1, -1, -1],
        ],
        name="0029vpufvyeoxr",
        visible=True,
        collidable=True,
        tags=["sys_click"],
        layer=1,
    ),
    "0030bwvbcqnslb": Sprite(
        pixels=[
            [14, 14, 8, -1, -1, -1],
            [14, -1, -1, -1, -1, -1],
            [14, -1, -1, -1, 13, -1],
            [14, -1, -1, -1, 14, -1],
            [14, 14, 14, 14, 14, 8],
        ],
        name="0030bwvbcqnslb",
        visible=True,
        collidable=True,
        tags=["sys_click"],
        layer=1,
    ),
    "0031wgsgcgmmcx": Sprite(
        pixels=[
            [-1, -1, 15, 15, 15],
            [13, 15, 15, -1, 15],
            [-1, -1, -1, -1, 15],
            [-1, -1, -1, -1, 15],
            [-1, -1, -1, -1, 15],
            [-1, -1, -1, -1, 15],
            [8, 15, 15, -1, 15],
            [-1, -1, 15, 15, 15],
            [-1, -1, -1, 13, -1],
        ],
        name="0031wgsgcgmmcx",
        visible=False,
        collidable=True,
        tags=["sys_click"],
        layer=4,
    ),
    "0032theriyvghg": Sprite(
        pixels=[
            [-1, -1, 15, 15, 15],
            [13, 15, 15, -1, 15],
            [-1, -1, -1, -1, 0],
            [-1, -1, -1, -1, 15],
            [-1, -1, -1, -1, 15],
            [8, 15, 15, -1, 15],
            [-1, -1, 15, 15, 15],
            [-1, -1, -1, 13, -1],
        ],
        name="0032theriyvghg",
        visible=False,
        collidable=True,
        tags=["sys_click"],
        layer=3,
    ),
    "0033xxbwumnkve": Sprite(
        pixels=[
            [-1, -1, 15, 15, 15],
            [13, 15, 15, -1, 15],
            [-1, -1, -1, -1, 0],
            [-1, -1, -1, -1, 15],
            [8, 15, 15, -1, 15],
            [-1, -1, 15, 15, 15],
            [-1, -1, -1, 13, -1],
        ],
        name="0033xxbwumnkve",
        visible=False,
        collidable=True,
        tags=["sys_click"],
        layer=2,
    ),
    "0034tlmfuvkxfw": Sprite(
        pixels=[
            [-1, -1, 15, 15, 15],
            [13, 15, 15, -1, 15],
            [-1, -1, -1, -1, 0],
            [8, 15, 15, -1, 15],
            [-1, -1, 15, 15, 15],
            [-1, -1, -1, 13, -1],
        ],
        name="0034tlmfuvkxfw",
        visible=True,
        collidable=True,
        tags=["sys_click"],
        layer=1,
    ),
    "0035cnwthztcfw": Sprite(
        pixels=[
            [12, 12, 12, 12],
            [12, -1, -1, 13],
            [12, -1, -1, -1],
            [12, 12, 8, -1],
        ],
        name="0035cnwthztcfw",
        visible=True,
        collidable=True,
        tags=["sys_click"],
        layer=1,
    ),
    "0036elhntsdonx": Sprite(
        pixels=[
            [-1, -1, -1, -1, -1, 13],
            [8, 10, 10, 10, 10, 10],
        ],
        name="0036elhntsdonx",
        visible=True,
        collidable=True,
        tags=["sys_click"],
        layer=1,
    ),
    "0037dncumvkgou": Sprite(
        pixels=[
            [8, -1, -1, -1, -1],
            [9, -1, -1, -1, -1],
            [9, -1, -1, -1, 8],
            [9, 9, 9, 9, 9],
            [9, -1, -1, -1, -1],
            [9, -1, -1, -1, -1],
            [9, 9, 9, 9, 8],
            [-1, -1, 8, -1, -1],
        ],
        name="0037dncumvkgou",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0038ltlnonzzwu": Sprite(
        pixels=[
            [8, -1, -1, -1, -1, -1, -1, -1, -1],
            [14, -1, -1, -1, 8, -1, -1, -1, -1],
            [14, -1, -1, -1, 14, -1, -1, -1, -1],
            [14, -1, -1, -1, 14, -1, -1, -1, 8],
            [14, -1, -1, -1, 14, -1, -1, -1, 14],
            [14, 14, 14, 14, 14, 14, 14, 14, 14],
        ],
        name="0038ltlnonzzwu",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0039sbbbyedvkj": Sprite(
        pixels=[
            [-1, -1, -1, -1, 8],
            [-1, -1, -1, -1, 10],
            [-1, -1, -1, -1, 10],
            [8, 10, 10, 10, 10],
            [-1, -1, 13, -1, -1],
        ],
        name="0039sbbbyedvkj",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0040ictnhpddip": Sprite(
        pixels=[
            [8, -1, -1, -1, 13],
            [11, -1, -1, -1, 11],
            [11, -1, -1, -1, 11],
            [11, 11, 11, 11, 11],
        ],
        name="0040ictnhpddip",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0041jvzywzzqio": Sprite(
        pixels=[
            [-1, -1, -1, 8, 14],
            [-1, -1, -1, -1, 14],
            [-1, -1, -1, -1, 14],
            [13, -1, -1, -1, 14],
            [14, -1, -1, -1, 14],
            [14, 14, 14, 14, 14],
        ],
        name="0041jvzywzzqio",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0042kbfruscvjq": Sprite(
        pixels=[
            [12, 12, 12, 12, 12],
            [13, -1, -1, -1, 8],
        ],
        name="0042kbfruscvjq",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0043qbkakbtngg": Sprite(
        pixels=[
            [-1, -1, -1, -1, -1, 8, -1, 13, -1, -1, -1],
            [-1, -1, -1, -1, 11, 11, 11, 11, 11, -1, -1],
            [-1, -1, -1, -1, 11, 11, 11, 11, 11, -1, -1],
            [-1, -1, -1, 11, 11, 11, 11, -1, -1, -1, -1],
            [-1, -1, -1, 11, 11, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, 11, 11, -1, -1, -1, 11, -1, -1],
            [-1, 13, -1, 11, 11, -1, -1, 11, 11, 11, -1],
            [8, 11, 11, 11, 11, -1, -1, 11, 11, 11, 8],
            [-1, 11, 11, 11, 11, 11, 11, 11, 11, 11, -1],
            [-1, 11, 11, 11, 11, 11, 11, 11, 11, 11, -1],
            [-1, -1, -1, -1, -1, -1, -1, 13, -1, -1, -1],
        ],
        name="0043qbkakbtngg",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0044zizryaziko": Sprite(
        pixels=[
            [-1, 13, -1, 8, -1],
            [-1, 9, 9, 9, -1],
            [-1, 9, 9, 9, -1],
            [-1, 9, -1, 9, -1],
            [8, 9, -1, 9, 13],
        ],
        name="0044zizryaziko",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0045eepaezvwsc": Sprite(
        pixels=[
            [7, 7, 7, 7, 13],
            [7, -1, -1, -1, -1],
            [7, -1, -1, -1, -1],
            [7, -1, -1, -1, -1],
            [8, -1, -1, -1, -1],
        ],
        name="0045eepaezvwsc",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0046keiixwuwrd": Sprite(
        pixels=[
            [-1, -1, -1, -1, 13, -1],
            [-1, 10, 10, 10, 10, 10],
            [-1, 10, -1, -1, -1, 10],
            [-1, 10, -1, -1, 10, 10],
            [8, 10, -1, 10, 10, 13],
            [-1, 10, 10, 10, 8, -1],
        ],
        name="0046keiixwuwrd",
        visible=True,
        collidable=True,
        tags=["sys_click"],
    ),
    "0047gllstmzmuy": Sprite(
        pixels=[
            [8],
        ],
        name="0047gllstmzmuy",
        visible=True,
        collidable=True,
    ),
}
levels = [
    # Level 1
    Level(
        sprites=[
            Sprite(pixels=[[13, -1, -1, -1, -1, -1, -1], [6, -1, -1, -1, 13, -1, -1], [6, 6, 6, 6, 6, -1, -1], [-1, -1, -1, -1, 6, -1, -1], [-1, -1, -1, -1, 6, 6, 6], [-1, -1, -1, -1, 6, -1, -1], [-1, -1, -1, -1, 6, -1, -1]], name='m000', visible=True, collidable=True, tags=["sys_click"]).set_position(4, 12).set_rotation(270),
            Sprite(pixels=[[6, 6, 6, 6, 6, 6, 6], [-1, -1, 6, -1, -1, -1, 13], [-1, -1, 13, -1, -1, -1, -1]], name='m001', visible=True, collidable=True, tags=["sys_click"]).set_position(13, 4).set_rotation(180),
        ],
        grid_size=(20, 20),
        data={
            "BackgroundColour": 15,
            "MaxSteps": 400,
            "Stamps": [[15, 8]],
        },
    ),
    # Level 2
    Level(
        sprites=[
            Sprite(pixels=[[-1, 6, 8, -1, -1, -1, -1, -1], [-1, 6, -1, -1, -1, -1, -1, -1], [-1, 6, -1, -1, -1, -1, -1, -1], [13, 6, 6, 6, 8, -1, -1, -1], [-1, 6, -1, -1, -1, -1, -1, -1], [-1, 6, -1, -1, -1, 8, -1, -1], [-1, 6, -1, -1, -1, 6, -1, -1], [13, 6, 6, 6, 6, 6, 6, 6]], name='m100', visible=True, collidable=True, tags=["sys_click"]).set_position(6, 0).set_rotation(180),
            Sprite(pixels=[[6, -1], [6, -1], [6, -1], [6, 13], [6, -1], [6, -1], [6, -1], [6, 13]], name='m101', visible=True, collidable=True, tags=["sys_click"]).set_position(7, 10).set_rotation(90),
            Sprite(pixels=[[6, 6, 6, 6, 6, 8], [-1, -1, 6, -1, -1, -1], [-1, -1, 6, -1, -1, -1], [-1, -1, 6, 8, -1, -1], [-1, -1, 6, -1, -1, -1], [-1, -1, 8, -1, -1, -1]], name='m102', visible=True, collidable=True, tags=["sys_click"]).set_position(4, 13).set_rotation(270),
        ],
        grid_size=(20, 20),
        data={
            "BackgroundColour": 15,
            "MaxSteps": 75,
            "Stamps": [[17, 6]],
        },
    ),
    # Level 3
    Level(
        sprites=[
            Sprite(pixels=[[-1, -1, -1, -1, 6, -1, -1], [-1, -1, -1, -1, 6, -1, -1], [-1, -1, -1, 13, 6, 6, 8], [-1, -1, -1, -1, 6, -1, -1], [13, -1, -1, -1, 6, -1, -1], [6, 6, 6, 6, 6, 8, -1]], name='m200', visible=True, collidable=True, tags=["sys_click"]).set_position(2, 4).set_rotation(270),
            Sprite(pixels=[[-1, 6, -1, 6], [-1, 6, -1, 6], [13, 6, 6, 6], [-1, -1, -1, 6], [-1, -1, -1, 13]], name='m201', visible=True, collidable=True, tags=["sys_click"]).set_position(5, 14).set_rotation(270),
            Sprite(pixels=[[6, -1, -1], [6, -1, -1], [6, 8, -1], [6, -1, -1], [6, -1, -1], [6, 6, 8]], name='m202', visible=True, collidable=True, tags=["sys_click"]).set_position(17, 0),
        ],
        grid_size=(20, 20),
        data={
            "BackgroundColour": 15,
            "GreyMasking": True,
            "MaxSteps": 100,
            "Stamps": [[14, 12]],
        },
    ),
    # Level 4
    Level(
        sprites=[
            Sprite(pixels=[[6, 6, 6, 6, 6, 6, 6, 6, 6], [-1, -1, 8, -1, -1, -1, -1, -1, 8]], name='m300', visible=True, collidable=True, tags=["sys_click"]).set_position(7, 0),
            Sprite(pixels=[[6, -1], [6, -1], [6, 13], [6, -1], [6, -1], [6, -1]], name='m301', visible=True, collidable=True, tags=["sys_click"]).set_position(7, 12).set_rotation(180),
            Sprite(pixels=[[8, -1, -1, -1, -1, -1], [6, -1, -1, -1, -1, -1], [6, -1, -1, -1, -1, -1], [6, 6, 6, 6, 6, 13], [8, -1, -1, -1, -1, -1]], name='m302', visible=True, collidable=True, tags=["sys_click"]).set_position(6, 3).set_rotation(90),
            Sprite(pixels=[[-1, 8, -1, -1, -1, -1, -1, -1], [-1, 6, 6, 6, 6, 6, -1, -1], [-1, 6, -1, -1, -1, -1, -1, -1], [13, 6, 13, -1, -1, -1, -1, -1], [-1, 6, -1, -1, -1, -1, -1, 8], [-1, 6, -1, -1, -1, -1, -1, 6], [-1, 6, 6, 6, 6, 6, 6, 6]], name='m303', visible=True, collidable=True, tags=["sys_click"]).set_position(12, 4),
        ],
        grid_size=(20, 20),
        data={
            "BackgroundColour": 15,
            "GreyMasking": True,
            "MaxSteps": 100,
            "Stamps": [[14, 15]],
        },
    ),
    # Level 5
    Level(
        sprites=[
            Sprite(pixels=[[-1, -1, -1, -1, 6, -1], [-1, -1, -1, -1, 6, -1], [-1, -1, 13, -1, 6, -1], [8, 6, 6, 6, 6, 13], [-1, -1, 6, -1, 6, -1], [-1, -1, 13, -1, 6, -1], [-1, -1, -1, 13, 6, -1], [-1, -1, -1, -1, 13, -1]], name='m400', visible=True, collidable=True, tags=["sys_click"]).set_position(10, 2).set_rotation(90),
            Sprite(pixels=[[-1, -1, 6], [-1, -1, 6], [-1, -1, 6], [13, 6, 6], [-1, -1, 6], [-1, -1, 6], [-1, -1, 6]], name='m401', visible=True, collidable=True, tags=["sys_click"]).set_position(4, 8).set_rotation(180),
            Sprite(pixels=[[6, 6, 6, 6], [6, -1, -1, 6], [6, -1, -1, 13], [6, 8, -1, -1], [6, -1, -1, -1], [6, -1, -1, -1], [6, 6, 8, -1], [6, -1, -1, -1], [13, -1, -1, -1]], name='m402', visible=True, collidable=True, tags=["sys_click"]).set_position(11, 9).set_rotation(90),
            Sprite(pixels=[[-1, -1, -1, -1, -1, 13, -1, -1, -1], [-1, -1, -1, -1, 13, 6, 8, -1, -1], [-1, -1, -1, 13, -1, 6, -1, -1, -1], [-1, -1, -1, 6, -1, 6, -1, -1, 13], [6, 6, 6, 6, 6, 6, 6, 6, 6]], name='m403', visible=True, collidable=True, tags=["sys_click"]).set_position(0, 0).set_rotation(180),
        ],
        grid_size=(20, 20),
        data={
            "BackgroundColour": 15,
            "GreyMasking": True,
            "MaxSteps": 100,
            "Stamps": [[12, 13]],
        },
    ),
    # Level 6
    Level(
        sprites=[
            Sprite(pixels=[[8, 6, 6, 6], [-1, -1, -1, 6], [-1, 13, 6, 6], [-1, -1, -1, 6], [-1, 13, 6, 6], [-1, -1, -1, 6], [-1, -1, -1, 6], [-1, -1, -1, 6], [-1, -1, 8, 6]], name='m500', visible=True, collidable=True, tags=["sys_click"]).set_position(4, 10).set_rotation(90),
            Sprite(pixels=[[-1, -1, -1, -1, 6, 6, 6], [-1, -1, -1, -1, 6, -1, -1], [-1, -1, -1, -1, 6, -1, -1], [-1, -1, -1, -1, 6, -1, -1], [-1, -1, -1, 8, 6, 13, -1], [-1, -1, -1, -1, 6, -1, -1], [13, 6, 6, 6, 6, -1, -1]], name='m501', visible=True, collidable=True, tags=["sys_click"]).set_position(10, 2).set_rotation(180),
            Sprite(pixels=[[6, 6, 6, 6, 13, -1], [-1, -1, 6, -1, -1, -1], [-1, -1, 6, -1, -1, -1], [-1, -1, 6, -1, -1, -1], [6, 6, 6, 6, 6, 8]], name='m502', visible=True, collidable=True, tags=["sys_click"]).set_position(6, 14).set_rotation(180),
            Sprite(pixels=[[6, 13], [6, -1], [6, -1], [6, -1], [6, -1], [6, -1], [6, -1], [6, -1], [6, -1]], name='m503', visible=True, collidable=True, tags=["sys_click"]).set_position(2, 7).set_rotation(180),
            Sprite(pixels=[[6, 6, 6, 6, 6, -1], [-1, -1, -1, -1, 6, -1], [-1, -1, -1, -1, 6, -1], [-1, -1, -1, -1, 6, -1], [-1, -1, -1, 8, 6, 8]], name='m504', visible=True, collidable=True, tags=["sys_click"]).set_position(3, 1).set_rotation(270),
        ],
        grid_size=(20, 20),
        data={
            "BackgroundColour": 15,
            "GreyMasking": True,
            "MaxSteps": 100,
            "Stamps": [[17, 15], [4, 7]],
        },
    ),
    # Level 7
    Level(
        sprites=[
            Sprite(pixels=[[13, 6, 6, 8], [-1, 6, -1, -1], [-1, 6, -1, -1], [-1, 6, -1, -1], [-1, 6, 6, 8], [-1, 6, -1, -1], [-1, 6, -1, -1], [-1, 13, -1, -1]], name='m600', visible=True, collidable=True, tags=["sys_click"]).set_position(6, 14).set_rotation(90),
            Sprite(pixels=[[-1, -1, 13, -1, -1], [6, 6, 6, -1, -1], [6, -1, 6, -1, -1], [6, -1, 6, -1, -1], [6, -1, 6, -1, -1], [6, 6, 6, 6, 8], [6, -1, 6, -1, -1], [6, -1, 6, -1, -1]], name='m601', visible=True, collidable=True, tags=["sys_click"]).set_position(8, 5),
            Sprite(pixels=[[6, 13], [6, -1], [6, -1], [6, -1], [6, -1], [6, -1], [6, -1]], name='m602', visible=True, collidable=True, tags=["sys_click"]).set_position(0, 12).set_rotation(180),
            Sprite(pixels=[[-1, 13, -1, -1], [-1, 6, -1, -1], [-1, 6, -1, -1], [8, 6, 6, 6], [-1, 6, -1, 6], [-1, 6, 6, 6]], name='m603', visible=True, collidable=True, tags=["sys_click"]).set_position(16, 5),
            Sprite(pixels=[[8, 6, 6, 6], [-1, 6, -1, 6], [-1, 6, -1, 6], [-1, 6, -1, 6], [8, 6, 6, 6], [-1, 13, -1, -1]], name='m604', visible=True, collidable=True, tags=["sys_click"]).set_position(16, 12).set_rotation(180),
        ],
        grid_size=(20, 20),
        data={
            "BackgroundColour": 15,
            "GreyMasking": True,
            "MaxSteps": 100,
            "Stamps": [[14, 16], [4, 5]],
        },
    ),
]
BACKGROUND_COLOR = 4
# the mirror stamp, drawn over two board cells by two (six pixels square): a black bow-tie, the same both ways
VSTAMP_ICON = ['X....X', 'XX..XX', 'XXXXXX', 'XXXXXX', 'XX..XX', 'X....X']
PADDING_COLOR = 4


class lvealyvptn(RenderableUserDisplay):
    """."""

    def __init__(self, pguodduwhg: int):
        self.pguodduwhg = pguodduwhg
        self.current_steps = pguodduwhg
        self.vgame = None

    def upqoakzziq(self, pguodduwhg: int) -> None:
        self.pguodduwhg = pguodduwhg

    def tebogkqnvk(self, lwcfelugjm: int) -> None:
        self.current_steps = max(0, min(lwcfelugjm, self.pguodduwhg))

    def vdraw_outline(self, frame: np.ndarray) -> None:
        """A one-pixel ring just outside the held piece, drawn only over the board's own colour."""
        g = self.vgame
        s = g.xseexqzst if g else None
        if s is None or not s.is_visible or g.vbg is None:
            return
        x0, y0 = 2 + 3 * s.x - 1, 2 + 3 * s.y - 1
        x1, y1 = 2 + 3 * (s.x + s.width), 2 + 3 * (s.y + s.height)
        colour = _vx_raw(11) if _VX_PALETTE[g.vbg] != 11 else _vx_raw(0)
        for x in range(x0, x1 + 1):
            for y in (y0, y1):
                if 2 <= x < 62 and 2 <= y < 62 and frame[y, x] == g.vbg:
                    frame[y, x] = colour
        for y in range(y0, y1 + 1):
            for x in (x0, x1):
                if 2 <= x < 62 and 2 <= y < 62 and frame[y, x] == g.vbg:
                    frame[y, x] = colour

    def vdraw_stamps(self, frame: np.ndarray) -> None:
        g = self.vgame
        if g is None or g.vbg is None:
            return
        for sx, sy in g.vstamps:
            for j, row in enumerate(VSTAMP_ICON):
                for i, ch in enumerate(row):
                    x, y = 2 + 3 * sx + i, 2 + 3 * sy + j
                    if ch == "X" and 0 <= x < 64 and 0 <= y < 64 and frame[y, x] == g.vbg:
                        frame[y, x] = _vx_raw(5)

    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        self.vdraw_stamps(frame)
        self.vdraw_outline(frame)
        if self.pguodduwhg == 0:
            return frame
        zykjreppvy = 32
        x_offset = (64 - zykjreppvy) // 2
        vloaukxere = self.current_steps / self.pguodduwhg
        tixxrxgjjq = round(zykjreppvy * vloaukxere)
        tixxrxgjjq = min(tixxrxgjjq, zykjreppvy)
        hpvclytfhu = zykjreppvy - tixxrxgjjq
        for x in range(zykjreppvy):
            if x < hpvclytfhu:
                frame[0, x_offset + x] = 0
            else:
                frame[0, x_offset + x] = 4
        return frame


class Ve13(ARCBaseGame):
    def __init__(self) -> None:
        yrrliudnw = Camera(background=BACKGROUND_COLOR, letter_box=PADDING_COLOR)
        self.xseexqzst: Sprite | None = None
        self.uysylxuqw: dict[str, ndarray] = {}
        self.hlxyvcmpk: dict[str, ndarray] = {}
        self.iahpylgry: dict[str, set[tuple[int, int]]] = {}
        self.ydfurpdwv: dict[str, set[tuple[int, int]]] = {}
        self.dxcfrrcpp = False
        self.ojcsxidcz = 150
        self.kpgnbcoir = lvealyvptn(pguodduwhg=self.ojcsxidcz)
        self.spcewphwy = False
        self.kpgnbcoir.vgame = self
        self.vbg = None
        self.vmask = 4
        self.vq = []
        self.vdefer = False
        self.vdone = False
        self.vM = set()
        self.vX = set()
        self.vstamps = []      # top-left board cells of the level's mirror stamps (each covers two by two)
        self.vflipped = False  # the held piece was flipped by a stamp during this action (plays the flip frames)
        yrrliudnw.replace_interface([self.kpgnbcoir])
        super().__init__(game_id="ve13", levels=levels, camera=yrrliudnw)

    def on_set_level(self, level: Level) -> None:
        """."""
        self.spcewphwy = False
        self.ojcsxidcz = level.get_data("MaxSteps") or 150
        self.kpgnbcoir.upqoakzziq(self.ojcsxidcz)
        self.kpgnbcoir.tebogkqnvk(self.ojcsxidcz)
        rfymfyoqro = level.get_data("BackgroundColour")
        self.vbg = rfymfyoqro if rfymfyoqro is not None else BACKGROUND_COLOR
        self.vq = []
        if rfymfyoqro is not None:
            self.camera.letter_box = rfymfyoqro
            self.camera.background = rfymfyoqro
        else:
            self.camera.letter_box = BACKGROUND_COLOR
            self.camera.background = BACKGROUND_COLOR
        self.dxcfrrcpp = level.get_data("GreyMasking") or False
        self.xseexqzst = None
        self.uysylxuqw = {}
        self.hlxyvcmpk = {}
        qjbdypwyab: Dict[Tuple[int, int], List[Sprite]] = {}
        for sprite in level.get_sprites():
            self.hlxyvcmpk[sprite.name] = sprite.pixels.copy()
            sprite.color_remap(13, 8)
            self.uysylxuqw[sprite.name] = sprite.pixels.copy()
            if self.dxcfrrcpp:
                sprite.pixels = np.where(sprite.pixels >= 0, self.vmask, sprite.pixels)
            bndozsgqlx = (sprite.x, sprite.y)
            qjbdypwyab.setdefault(bndozsgqlx, []).append(sprite)
        self.vausolnec: Dict[Sprite, List[Sprite]] = {}
        self.ztpxqonhr = True
        for xboircnqmu in qjbdypwyab.values():
            xboircnqmu.sort(key=lambda s: s.layer)
            for sprite in xboircnqmu:
                self.vausolnec[sprite] = xboircnqmu
                sprite.set_layer(0)
        ychunvaasr = [s for s in level.get_sprites() if s.is_visible]
        if ychunvaasr:
            ikljwmewzw = min(ychunvaasr, key=lambda s: s.x**2 + s.y**2)
            self.swfljqaiqu(ikljwmewzw)
        self.uqlndqojuf()
        self.rqolqpqwo = False
        self.vM, self.vX = self.vpairs()
        self.vstamps = [tuple(c) for c in (level.get_data("Stamps") or [])]

    def swfljqaiqu(self, sprite: Sprite) -> None:
        """."""
        if self.xseexqzst:
            self.bewtoqvzlr()
        self.xseexqzst = sprite
        self.xseexqzst.set_layer(4)
        self.uysylxuqw[sprite.name] = sprite.pixels.copy()
        if self.dxcfrrcpp:
            sprite.pixels = self.hlxyvcmpk[sprite.name].copy()
            sprite.color_remap(13, 8)
        else:
            sprite.pixels = np.where(
                (sprite.pixels >= 0) & (sprite.pixels != 8) & (sprite.pixels != 13) & (sprite.pixels != 3),
                0,
                sprite.pixels,
            )
        self.uqlndqojuf()

    def bewtoqvzlr(self) -> None:
        """."""
        if self.xseexqzst and self.xseexqzst.name in self.uysylxuqw:
            self.xseexqzst.pixels = self.uysylxuqw[self.xseexqzst.name]
            self.xseexqzst.color_remap(13, 8)
            if self.dxcfrrcpp:
                self.xseexqzst.pixels = np.where(
                    (self.xseexqzst.pixels >= 0) & (self.xseexqzst.pixels != 8) & (self.xseexqzst.pixels != 13),
                    self.vmask,
                    self.xseexqzst.pixels,
                )
            self.xseexqzst.set_layer(0)
        self.xseexqzst = None

    def uqlndqojuf(self) -> None:
        """."""
        sprites = self.current_level.get_sprites()
        self.iahpylgry = {}
        self.ydfurpdwv = {}
        for sprite in sprites:
            if not sprite.is_visible:
                continue
            if sprite == self.xseexqzst:
                if self.dxcfrrcpp:
                    sprite.pixels = self.hlxyvcmpk[sprite.name].copy()
                    sprite.color_remap(13, 8)
                else:
                    glumbzosvi = self.hlxyvcmpk[sprite.name]
                    sprite.pixels = glumbzosvi.copy()
                    sprite.pixels = np.where(
                        (sprite.pixels >= 0) & (sprite.pixels != 8) & (sprite.pixels != 13) & (sprite.pixels != 3),
                        0,
                        sprite.pixels,
                    )
                    sprite.color_remap(13, 8)
            else:
                sprite.pixels = self.hlxyvcmpk[sprite.name].copy()
                sprite.color_remap(13, 8)
                if self.dxcfrrcpp:
                    sprite.pixels = np.where(sprite.pixels >= 0, self.vmask, sprite.pixels)
        rnogpwdbcy: dict[tuple[int, int], list[tuple[Sprite, int, int]]] = {}
        xatynhmnbp: dict[tuple[int, int], list[tuple[Sprite, int, int]]] = {}
        zowwgsnegx: dict[tuple[int, int], list[tuple[Sprite, int, int]]] = {}
        for sprite in sprites:
            if not sprite.is_visible:
                continue
            rndgaphcrj = self.hlxyvcmpk[sprite.name]
            npahqszgub = sprite.pixels.copy()
            sprite.pixels = rndgaphcrj
            qvvtgkzeou = sprite.render()
            sprite.pixels = npahqszgub
            for y in range(qvvtgkzeou.shape[0]):
                for x in range(qvvtgkzeou.shape[1]):
                    if qvvtgkzeou[y, x] == 8:
                        jtuveswkeo = sprite.x + x
                        szhneaucff = sprite.y + y
                        if (jtuveswkeo, szhneaucff) not in rnogpwdbcy:
                            rnogpwdbcy[jtuveswkeo, szhneaucff] = []
                        if (jtuveswkeo, szhneaucff) not in zowwgsnegx:
                            zowwgsnegx[jtuveswkeo, szhneaucff] = []
                        rnogpwdbcy[jtuveswkeo, szhneaucff].append((sprite, x, y))
                        zowwgsnegx[jtuveswkeo, szhneaucff].append((sprite, x, y))
                    if qvvtgkzeou[y, x] == 13:
                        jtuveswkeo = sprite.x + x
                        szhneaucff = sprite.y + y
                        if (jtuveswkeo, szhneaucff) not in xatynhmnbp:
                            xatynhmnbp[jtuveswkeo, szhneaucff] = []
                        if (jtuveswkeo, szhneaucff) not in zowwgsnegx:
                            zowwgsnegx[jtuveswkeo, szhneaucff] = []
                        xatynhmnbp[jtuveswkeo, szhneaucff].append((sprite, x, y))
                        zowwgsnegx[jtuveswkeo, szhneaucff].append((sprite, x, y))
        for meivkrsgum, yazvvwzuhr in rnogpwdbcy.items():
            if len(yazvvwzuhr) == 2:
                for sprite, dhtdorktvh, ylyefycpzi in yazvvwzuhr:
                    if sprite.name not in self.iahpylgry:
                        self.iahpylgry[sprite.name] = set()
                    self.iahpylgry[sprite.name].add((dhtdorktvh, ylyefycpzi))
        for meivkrsgum, yazvvwzuhr in xatynhmnbp.items():
            if len(yazvvwzuhr) == 2:
                for sprite, dhtdorktvh, ylyefycpzi in yazvvwzuhr:
                    if sprite.name not in self.iahpylgry:
                        self.iahpylgry[sprite.name] = set()
                    self.iahpylgry[sprite.name].add((dhtdorktvh, ylyefycpzi))
        for meivkrsgum, yazvvwzuhr in zowwgsnegx.items():
            if len(yazvvwzuhr) == 2:
                for sprite, dhtdorktvh, ylyefycpzi in yazvvwzuhr:
                    if sprite.name not in self.ydfurpdwv:
                        self.ydfurpdwv[sprite.name] = set()
                    self.ydfurpdwv[sprite.name].add((dhtdorktvh, ylyefycpzi))
        for sprite in sprites:
            if not sprite.is_visible:
                continue
            if sprite.name in self.iahpylgry:
                fvuquzeqwr = set()
                for x, y in self.iahpylgry[sprite.name]:
                    if sprite.rotation == 0:
                        fvuquzeqwr.add((x, y))
                    elif sprite.rotation == 90:
                        pxgcthczsv = y
                        jtmtjfqmcv = sprite.pixels.shape[0] - 1 - x
                        fvuquzeqwr.add((pxgcthczsv, jtmtjfqmcv))
                    elif sprite.rotation == 180:
                        pxgcthczsv = sprite.pixels.shape[1] - 1 - x
                        jtmtjfqmcv = sprite.pixels.shape[0] - 1 - y
                        fvuquzeqwr.add((pxgcthczsv, jtmtjfqmcv))
                    elif sprite.rotation == 270:
                        pxgcthczsv = sprite.pixels.shape[1] - 1 - y
                        jtmtjfqmcv = x
                        fvuquzeqwr.add((pxgcthczsv, jtmtjfqmcv))
                for x, y in fvuquzeqwr:
                    if 0 <= y < sprite.pixels.shape[0] and 0 <= x < sprite.pixels.shape[1]:
                        if sprite.pixels[y, x] == 8 or sprite.pixels[y, x] == 13:
                            sprite.pixels[y, x] = 3
            if self.dxcfrrcpp and sprite != self.xseexqzst:
                dyrxesvcbp = (self.hlxyvcmpk[sprite.name] == 8) | (self.hlxyvcmpk[sprite.name] == 13)
                sprite.pixels = np.where(dyrxesvcbp & (sprite.pixels != 3), self.vmask, sprite.pixels)

    def sjwqloivve(self) -> bool:
        """."""
        for sprite in self.current_level.get_sprites():
            if not sprite.is_visible:
                continue
            wnvxfvordi = self.hlxyvcmpk[sprite.name].copy()
            if sprite.name in self.iahpylgry:
                for x, y in self.iahpylgry[sprite.name]:
                    if sprite.rotation == 0:
                        pxgcthczsv, jtmtjfqmcv = (x, y)
                    elif sprite.rotation == 90:
                        pxgcthczsv = y
                        jtmtjfqmcv = wnvxfvordi.shape[0] - 1 - x
                    elif sprite.rotation == 180:
                        pxgcthczsv = wnvxfvordi.shape[1] - 1 - x
                        jtmtjfqmcv = wnvxfvordi.shape[0] - 1 - y
                    elif sprite.rotation == 270:
                        pxgcthczsv = wnvxfvordi.shape[1] - 1 - y
                        jtmtjfqmcv = x
                    else:
                        continue
                    if 0 <= jtmtjfqmcv < wnvxfvordi.shape[0] and 0 <= pxgcthczsv < wnvxfvordi.shape[1]:
                        if wnvxfvordi[jtmtjfqmcv, pxgcthczsv] == 8 or wnvxfvordi[jtmtjfqmcv, pxgcthczsv] == 13:
                            wnvxfvordi[jtmtjfqmcv, pxgcthczsv] = 3
            if np.any((wnvxfvordi == 8) | (wnvxfvordi == 13)):
                return False
        return True

    def complete_action(self) -> None:
        # while the frame queue is being built the game's own completion is only noted, then released by step()
        if self.vdefer:
            self.vdone = True
        else:
            super().complete_action()

    def vpairs(self):
        """(matched cells, landed-but-mismatched cells) in board coordinates, read from the game's own tables."""
        M, X = set(), set()
        for sprite in self.current_level.get_sprites():
            if not sprite.is_visible:
                continue
            for x, y in self.iahpylgry.get(sprite.name, ()):
                M.add((sprite.x + x, sprite.y + y))
            for x, y in self.ydfurpdwv.get(sprite.name, ()):
                if (x, y) not in self.iahpylgry.get(sprite.name, ()):
                    X.add((sprite.x + x, sprite.y + y))
        return M, X - M

    def vpix(self, sprite: Sprite, x: int, y: int):
        """Where the dot seen at (x, y) in the turned sprite lives in its own pixel array (the game's own mapping)."""
        r, h, w = sprite.rotation, sprite.pixels.shape[0], sprite.pixels.shape[1]
        if r == 0:
            return x, y
        if r == 90:
            return y, h - 1 - x
        if r == 180:
            return w - 1 - x, h - 1 - y
        return w - 1 - y, x

    def vpaint(self, cells, colour: int) -> None:
        for sprite in self.current_level.get_sprites():
            if not sprite.is_visible:
                continue
            base = self.hlxyvcmpk[sprite.name].copy()
            keep = sprite.pixels
            sprite.pixels = base
            seen = sprite.render()
            sprite.pixels = keep
            for (cx, cy) in cells:
                x, y = cx - sprite.x, cy - sprite.y
                if 0 <= y < seen.shape[0] and 0 <= x < seen.shape[1] and seen[y, x] in (8, 13):
                    px, py = self.vpix(sprite, x, y)
                    if 0 <= py < sprite.pixels.shape[0] and 0 <= px < sprite.pixels.shape[1]:
                        sprite.pixels[py, px] = colour

    def vflash_frame(self, ok, bad) -> None:
        self.uqlndqojuf()
        shown_mask = _VX_PALETTE[self.vmask]
        self.vpaint(ok, _vx_raw(0) if (shown_mask != 0 or not self.dxcfrrcpp) else _vx_raw(11))
        self.vpaint(bad, _vx_raw(5))

    def vturn_frame(self, stage: int) -> None:
        """A turn in three frames: the dots first, then the body half drawn, then the body whole (the settle frame)."""
        self.uqlndqojuf()
        s = self.xseexqzst
        if s is None:
            return
        yy, xx = np.indices(s.pixels.shape)
        dots = (s.pixels == 8) | (s.pixels == 13) | (s.pixels == 3)
        show = dots | ((yy + xx) % 2 == 0) if stage == 2 else dots
        s.pixels = np.where(show, s.pixels, -1)

    def step(self) -> None:
        if self.vq:
            self.vq.pop(0)()
            if not self.vq and not self.rqolqpqwo:
                super().complete_action()
            return
        level = self.current_level
        held = self.xseexqzst
        rot_before = held.rotation if held is not None else None
        self.vdefer, self.vdone = True, False
        try:
            self.vstep_base()
        finally:
            self.vdefer = False
        frames = []
        if self.vflipped and self.current_level is level:
            frames += [lambda: self.vturn_frame(1), lambda: self.vturn_frame(2)]
        self.vflipped = False
        if self.current_level is level:
            M, X = self.vpairs()
            newM, newX = M - self.vM, X - self.vX
            self.vM, self.vX = M, X
            if newM or newX:
                frames += [lambda: self.vflash_frame(newM, newX)] * 2
            if frames:
                frames += [self.uqlndqojuf]
        else:
            self.vM, self.vX = self.vpairs()
        if frames:
            frames.pop(0)()
            self.vq = frames
        elif self.vdone:
            super().complete_action()

    def vstep_base(self) -> None:
        if self.rqolqpqwo:
            self.next_level()
            self.complete_action()
            return
        "."
        self.kpgnbcoir.tebogkqnvk(self.ojcsxidcz - self._action_count)
        if self._action_count >= self.ojcsxidcz:
            self.lose()
            self.complete_action()
            return
        if self.action.id == GameAction.ACTION6:
            hrabyvqhf = self.action.data["x"]
            ddociqhfi = self.action.data["y"]
            xwmbrpwwuh = self.camera.display_to_grid(int(hrabyvqhf), int(ddociqhfi))
            if xwmbrpwwuh:
                grid_x, grid_y = xwmbrpwwuh
                bazxmockbn = None
                for sprite in self.current_level.get_sprites():
                    if self.ixutchviko(sprite, grid_x, grid_y, tqpvgsnhag=True):
                        if sprite.is_visible:
                            bazxmockbn = sprite
                            break
                if bazxmockbn:
                    if bazxmockbn == self.xseexqzst:
                        xboircnqmu = self.vausolnec[bazxmockbn]
                        if len(xboircnqmu) > 1:
                            pmiftlcmmv = self.aqrmljjiyi(bazxmockbn, grid_x, grid_y)
                            if pmiftlcmmv == 0:
                                self.eliexourzp(xboircnqmu)
                                self.uqlndqojuf()
                            else:
                                self.bewtoqvzlr()
                        else:
                            self.bewtoqvzlr()
                    else:
                        self.swfljqaiqu(bazxmockbn)
            self.spcewphwy = True
        elif self.action.id == GameAction.ACTION5:
            if self.xseexqzst:
                xboircnqmu = self.vausolnec[self.xseexqzst]
                if len(xboircnqmu) > 1:
                    self.eliexourzp(xboircnqmu)
                else:
                    self.xseexqzst.rotate(90)
                self.rnwsvakqem(self.xseexqzst)
                self.uqlndqojuf()
                if self.sjwqloivve():
                    self.rqolqpqwo = True
                    return
            self.spcewphwy = False
        elif self.action.id in [
            GameAction.ACTION1,
            GameAction.ACTION2,
            GameAction.ACTION3,
            GameAction.ACTION4,
        ]:
            if self.xseexqzst:
                dx = 0
                dy = 0
                if self.action.id == GameAction.ACTION1:
                    dy = -1
                elif self.action.id == GameAction.ACTION2:
                    dy = 1
                elif self.action.id == GameAction.ACTION3:
                    dx = -1
                elif self.action.id == GameAction.ACTION4:
                    dx = 1
                if self.current_level.grid_size is None:
                    return
                grid_width, grid_height = self.current_level.grid_size
                wmboymgbdp = self.xseexqzst.x + dx
                pzeiojzfae = self.xseexqzst.y + dy
                vbefore = self.vstamp_cells(self.xseexqzst)
                if wmboymgbdp >= 0 and pzeiojzfae >= 0 and (wmboymgbdp + self.xseexqzst.width <= grid_width) and (pzeiojzfae + self.xseexqzst.height <= grid_height):
                    self.xseexqzst.move(dx, dy)
                # slid onto a stamp: a drawn cell of the piece now covers a stamp cell it did not cover before
                if self.vstamp_cells(self.xseexqzst) - vbefore:
                    self.vmirror(self.xseexqzst)
                    self.vflipped = True
                self.uqlndqojuf()
                if self.sjwqloivve():
                    self.rqolqpqwo = True
                    return
            self.spcewphwy = False
        self.complete_action()

    def vstamp_cells(self, sprite: Sprite) -> set:
        """The stamp cells under a drawn cell (body or dot) of this piece."""
        if not self.vstamps:
            return set()
        drawn = sprite.render()
        ys, xs = np.nonzero(drawn >= 0)
        cells = {(sprite.x + int(x), sprite.y + int(y)) for x, y in zip(xs, ys)}
        stamp = {(sx + i, sy + j) for sx, sy in self.vstamps for i in (0, 1) for j in (0, 1)}
        return cells & stamp

    def vmirror(self, sprite: Sprite) -> None:
        """Flip the piece left to right where it stands. Its own pixels are flipped and its turn reversed: the
        engine draws pixels turned clockwise, and flipping the pixels then turning the other way draws exactly the
        mirror image of the old picture, in the same box. The dots and their hidden kinds go with the pixels."""
        for table in (self.hlxyvcmpk, self.uysylxuqw):
            if sprite.name in table:
                table[sprite.name] = np.fliplr(table[sprite.name]).copy()
        sprite.pixels = np.fliplr(sprite.pixels).copy()
        sprite.set_rotation((-sprite.rotation) % 360)

    def eliexourzp(self, xboircnqmu: List[Sprite]) -> None:
        if not self.xseexqzst:
            return
        index = xboircnqmu.index(self.xseexqzst)
        wtjzyytlp, uxiivqvld = (self.xseexqzst.x, self.xseexqzst.y)
        self.xseexqzst.set_visible(False)
        if self.ztpxqonhr:
            yqhjuzznpx = index + 1
            if yqhjuzznpx >= len(xboircnqmu):
                self.ztpxqonhr = False
                yqhjuzznpx = index - 1
                if yqhjuzznpx < 0:
                    self.ztpxqonhr = True
                    yqhjuzznpx = index
        else:
            yqhjuzznpx = index - 1
            if yqhjuzznpx < 0:
                self.ztpxqonhr = True
                yqhjuzznpx = index + 1
                if yqhjuzznpx >= len(xboircnqmu):
                    self.ztpxqonhr = False
                    yqhjuzznpx = index
        self.swfljqaiqu(xboircnqmu[yqhjuzznpx])
        self.xseexqzst.set_visible(True)
        self.xseexqzst.set_position(wtjzyytlp, uxiivqvld)

    def ixutchviko(self, sprite: Sprite, x: int, y: int, tqpvgsnhag: bool = False) -> bool:
        vnyhkelzfz = x >= sprite.x and y >= sprite.y and (x < sprite.x + sprite.width) and (y < sprite.y + sprite.height)
        if not vnyhkelzfz:
            return False
        if not tqpvgsnhag:
            return vnyhkelzfz
        pmiftlcmmv = self.aqrmljjiyi(sprite, x, y)
        return bool(pmiftlcmmv >= 0)

    def aqrmljjiyi(self, sprite: Sprite, x: int, y: int) -> int:
        rlyhwkcjod = x - sprite.x
        ptlfqxtwai = y - sprite.y
        pixels = sprite.render()
        return int(pixels[ptlfqxtwai, rlyhwkcjod])

    def rnwsvakqem(self, sprite: Sprite) -> None:
        if not self.current_level.grid_size:
            return
        grid_width, grid_height = self.current_level.grid_size
        max_x = max(0, grid_width - sprite.width)
        max_y = max(0, grid_height - sprite.height)
        wmboymgbdp = max(0, min(sprite.x, max_x))
        pzeiojzfae = max(0, min(sprite.y, max_y))
        sprite.set_position(wmboymgbdp, pzeiojzfae)


# -- copy layer: colours and view (half turn) ----------------------------------------------------
# The finished frame is recoloured and then shown half turn. It is done in the camera, so every
# redraw (each action, Undo, a level jump) shows it. The game itself still reads its own,
# untouched board: get_pixels uses the raw render. Input is turned back before the game reads it.
import numpy as _vx_np  # noqa: E402
from arcengine import ActionInput as _VxActionInput, GameAction as _VxGameAction  # noqa: E402

_VX_PALETTE = _vx_np.array([10, 12, 7, 14, 0, 1, 15, 3, 12, 6, 4, 13, 5, 8, 11, 9], dtype=_vx_np.int64)
def _vx_raw(shown):
    """A raw colour whose shown colour is `shown` (so the game's own code can ask for a colour by what the player sees)."""
    return int(_vx_np.nonzero(_VX_PALETTE == shown)[0][0])


_VX_ARROW = {1: 2, 2: 1, 3: 4, 4: 3}


def _vx_show(frame):
    a = _vx_np.asarray(frame)
    out = a.copy()
    m = (a >= 0) & (a <= 15)
    out[m] = _VX_PALETTE[a[m].astype(_vx_np.int64)]
    return _vx_np.ascontiguousarray(_vx_np.rot90(out, k=2)).astype(a.dtype)


def _vx_unview(x, y):
    return 63 - x, 63 - y


_VX_CAMS = {}


def _vx_cam(cam):
    base = type(cam)
    if getattr(base, "_vx_layer", False):
        return cam
    sub = _VX_CAMS.get(base)
    if sub is None:
        def render(self, sprites, _base=base):
            return _vx_show(_base.render(self, sprites))
        sub = type("_VxCam", (base,), {"_vx_layer": True, "render": render})
        _VX_CAMS[base] = sub
    cam.__class__ = sub
    return cam


Ve13.camera = property(lambda self: _vx_cam(self._camera))
_vx_perform = Ve13.perform_action


def _vx_perform_action(self, action_input, raw=False):
    aid = action_input.id.value if hasattr(action_input.id, "value") else int(action_input.id)
    if aid in _VX_ARROW:
        action_input = _VxActionInput(id=_VxGameAction.from_id(_VX_ARROW[aid]), data=action_input.data)
    elif aid == 6 and action_input.data and "x" in action_input.data:
        d = dict(action_input.data)
        d["x"], d["y"] = _vx_unview(int(d["x"]), int(d["y"]))
        action_input = _VxActionInput(id=action_input.id, data=d)
    return _vx_perform(self, action_input, raw)


Ve13.perform_action = _vx_perform_action
