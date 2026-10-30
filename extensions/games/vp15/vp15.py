# Author: Claude Sonnet 5.5 High (15-Oct); Claude Opus 5.5 High (18-Oct dead-end fixes)
# Date: 18-October-2026
# PURPOSE: vp15, the glow-up of vp05 (a recoloured, mirrored copy of a public maze-and-key game) fused with the
#   tilt-and-slide idea: an arrow tilts the whole board and the avatar slides until a wall, a closed lock (it stops in
#   the cell before; with the matching key it enters and opens it as before), a pusher cell or the board edge. Every
#   changer passed on the way applies, in order; refills are collected; moving changers step once per action. Each
#   action still costs one step. One cell per frame; the first frame shifts the board a pixel and lights a pink
#   line on the tilted edge; the last frame settles. Levels needing it carry stopper wall cells so that every level
#   is winnable by sliding (see design.md). Built by build_vp15.py from views/vp05/vp05.py; engine edit in engine_patch.py.
# SRP/DRY check: Pass -- the slide rule is one state machine (_slide_frame/_slide_end) in front of the control
#   copy's own per-move tail (_finish_move); its changer, pusher and lock code is reused untouched.
# CHANGELOG
#   18-Oct-2026 Claude Opus 5.5 High: no level can be left unwinnable any more. A full search of every position
#     (deadend_vp15.py) found pockets with no way back on levels 3, 4 and 7, and spots on levels 5, 6 and 7 where
#     the bar is full but the recharges are used up and the rest of the route is longer than the bar. Fixed with the
#     wall, recharge cube and step-cost edits in fixes18.json; see VSERIES_2026-10-18_status/vp15.md. Level 2's
#     stray wall piece one pixel off the grid (drawn solid, walked through) is dropped, as in vp13.
#   15-Oct-2026 Claude Sonnet 5.5 High: slide-on-tilt, pink edge line, stopper walls where a level needed one.
# vp15: single-file ARC-AGI-3 game (colours changed; the screen is shown mirrored left-right).
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

import math
from typing import List, Optional, Set, Tuple

import numpy as np
from arcengine import (
    ARCBaseGame,
    BlockingMode,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)

"."
sprites = {
    "ajdspzphhd": Sprite(
        pixels=[
            [14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14],
        ],
        name="ajdspzphhd",
        visible=False,
        collidable=True,
        tags=["xfmluydglp"],
    ),
    "eqatonpohu": Sprite(
        pixels=[
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        ],
        name="eqatonpohu",
        visible=True,
        collidable=True,
        tags=["eqatonpohu"],
        layer=1,
    ),
    "fesygzfqui": Sprite(
        pixels=[
            [4, 4, 4, 4, -2],
            [4, 4, 4, 4, -2],
            [4, 4, 4, 4, -2],
            [4, 4, 4, 4, -2],
            [4, 4, 4, 4, -2],
        ],
        name="fesygzfqui",
        visible=True,
        collidable=True,
        tags=["ihdgageizm"],
        layer=-5,
    ),
    "fywfjzkxlm": Sprite(
        pixels=[
            [-1, 0, -1],
            [-1, 0, -1],
            [0, 0, 0],
        ],
        name="fywfjzkxlm",
        visible=True,
        collidable=True,
    ),
    "ghizzeqtoh": Sprite(
        pixels=[
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ],
        name="ghizzeqtoh",
        visible=False,
        collidable=True,
        tags=["ghizzeqtoh"],
        layer=5,
    ),
    "gngifvjddu": Sprite(
        pixels=[
            [0, 0, -1],
            [-1, 0, 0],
            [0, -1, 0],
        ],
        name="gngifvjddu",
        visible=True,
        collidable=True,
    ),
    "grcpfuizfp": Sprite(
        pixels=[
            [-1, 0, -1],
            [0, 0, -1],
            [-1, 0, 0],
        ],
        name="grcpfuizfp",
        visible=True,
        collidable=True,
        layer=1,
    ),
    "hahdypcdru": Sprite(
        pixels=[
            [14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14],
        ],
        name="hahdypcdru",
        visible=False,
        collidable=True,
        tags=["xfmluydglp"],
    ),
    "hoswmpiqkw": Sprite(
        pixels=[
            [0, 0, 0, 0, 0, 0, 0],
            [0, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ],
        name="hoswmpiqkw",
        visible=False,
        collidable=True,
        tags=["hoswmpiqkw"],
        layer=-1,
    ),
    "ihdgageizm": Sprite(
        pixels=[
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
        ],
        name="ihdgageizm",
        visible=True,
        collidable=True,
        tags=["ihdgageizm"],
        layer=-5,
    ),
    "irgjxweouz": Sprite(
        pixels=[
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
        ],
        name="irgjxweouz",
        visible=False,
        collidable=True,
        tags=["xfmluydglp"],
    ),
    "kapcaakvb_b": Sprite(
        pixels=[
            [1, 1, 1, 1, 1],
            [-2, -2, -2, -2, -2],
            [-2, -2, -2, -2, -2],
            [-2, -2, -2, -2, -2],
            [-2, -2, -2, -2, -2],
        ],
        name="kapcaakvb_b",
        visible=True,
        collidable=True,
        tags=["gbvqrjtaqo"],
    ),
    "krdypjjivz": Sprite(
        pixels=[
            [-2, -2, -2, -2, -2],
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
        ],
        name="krdypjjivz",
        visible=True,
        collidable=True,
        tags=["ihdgageizm"],
        layer=-5,
    ),
    "kvynsvxbpi": Sprite(
        pixels=[
            [0, -1, -1],
            [-1, 0, -1],
            [-1, -1, 0],
        ],
        name="kvynsvxbpi",
        visible=True,
        collidable=True,
        tags=["kvynsvxbpi"],
    ),
    "lujfinsby_t": Sprite(
        pixels=[
            [-2, -2, -2, -2, -2],
            [-2, -2, -2, -2, -2],
            [-2, -2, -2, -2, -2],
            [-2, -2, -2, -2, -2],
            [1, 1, 1, 1, 1],
        ],
        name="lujfinsby_t",
        visible=True,
        collidable=True,
        tags=["gbvqrjtaqo"],
    ),
    "mkfbgalsbe": Sprite(
        pixels=[
            [0, -1, 0],
            [0, -1, 0],
            [0, 0, 0],
        ],
        name="mkfbgalsbe",
        visible=True,
        collidable=True,
    ),
    "mkjdaccuuf": Sprite(
        pixels=[
            [-2, -2, -2, -2, -2],
            [-2, 0, -2, -2, -2],
            [-2, -2, 0, 0, -2],
            [-2, -2, 0, -2, -2],
            [-2, -2, -2, -2, -2],
        ],
        name="mkjdaccuuf",
        visible=True,
        collidable=False,
        tags=["ttfwljgohq"],
        layer=-1,
    ),
    "mxfhnkdzvf": Sprite(
        pixels=[
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
            [-2, -2, -2, -2, -2],
        ],
        name="mxfhnkdzvf",
        visible=True,
        collidable=True,
        tags=["ihdgageizm"],
        layer=-5,
    ),
    "neltxxziap": Sprite(
        pixels=[
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
            [14],
        ],
        name="neltxxziap",
        visible=False,
        collidable=True,
        tags=["xfmluydglp"],
    ),
    "njpewhmtfd": Sprite(
        pixels=[
            [5, 5, 5, 5, 5, 5, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, 5, 5, 5, 5, 5, 5],
        ],
        name="njpewhmtfd",
        visible=True,
        collidable=True,
        tags=["vjotnebuqo", "vfkkzdgxzx"],
        layer=-3,
    ),
    "nnjhdcanjk": Sprite(
        pixels=[
            [-1, 0, 0],
            [0, -1, 0],
            [-1, 0, -1],
        ],
        name="nnjhdcanjk",
        visible=True,
        collidable=True,
    ),
    "npxgalaybz": Sprite(
        pixels=[
            [11, 11, 11],
            [11, -1, 11],
            [11, 11, 11],
        ],
        name="npxgalaybz",
        visible=True,
        collidable=False,
        tags=["npxgalaybz"],
        layer=-1,
    ),
    "nszegiawib": Sprite(
        pixels=[
            [3, 3, -1, -1, -1, -1, -1, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
        ],
        name="nszegiawib",
        visible=True,
        collidable=True,
        layer=-4,
    ),
    "rhsxkxzdjz": Sprite(
        pixels=[
            [-2, -2, -2, -2, -2],
            [-2, -2, 0, -2, -2],
            [-2, 1, 0, 0, -2],
            [-2, -2, 1, -2, -2],
            [-2, -2, -2, -2, -2],
        ],
        name="rhsxkxzdjz",
        visible=True,
        collidable=True,
        tags=["rhsxkxzdjz"],
        layer=-1,
    ),
    "rjlbuycveu": Sprite(
        pixels=[
            [5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5],
        ],
        name="rjlbuycveu",
        visible=True,
        collidable=False,
        tags=["rjlbuycveu"],
        layer=-3,
    ),
    "sfqyzhzkij": Sprite(
        pixels=[
            [12, 12, 12, 12, 12],
            [12, 12, 12, 12, 12],
            [9, 9, 9, 9, 9],
            [9, 9, 9, 9, 9],
            [9, 9, 9, 9, 9],
        ],
        name="sfqyzhzkij",
        visible=True,
        collidable=True,
        tags=["sfqyzhzkij"],
    ),
    "soyhouuebz": Sprite(
        pixels=[
            [-2, -2, -2, -2, -2],
            [-2, 9, 14, 14, -2],
            [-2, 9, 0, 8, -2],
            [-2, 12, 12, 8, -2],
            [-2, -2, -2, -2, -2],
        ],
        name="soyhouuebz",
        visible=True,
        collidable=False,
        tags=["soyhouuebz"],
        layer=-1,
    ),
    "sqpmiygfvh": Sprite(
        pixels=[
            [11],
        ],
        name="sqpmiygfvh",
        visible=True,
        collidable=True,
        layer=3,
    ),
    "tihiodtoj_l": Sprite(
        pixels=[
            [-2, -2, -2, -2, 1],
            [-2, -2, -2, -2, 1],
            [-2, -2, -2, -2, 1],
            [-2, -2, -2, -2, 1],
            [-2, -2, -2, -2, 1],
        ],
        name="tihiodtoj_l",
        visible=True,
        collidable=True,
        tags=["gbvqrjtaqo"],
    ),
    "ubspnhafvq": Sprite(
        pixels=[
            [0, 0, 0],
            [-1, -1, 0],
            [0, -1, 0],
        ],
        name="ubspnhafvq",
        visible=True,
        collidable=False,
        layer=-2,
    ),
    "ubyunwkbpx": Sprite(
        pixels=[
            [-2, 4, 4, 4, 4],
            [-2, 4, 4, 4, 4],
            [-2, 4, 4, 4, 4],
            [-2, 4, 4, 4, 4],
            [-2, 4, 4, 4, 4],
        ],
        name="ubyunwkbpx",
        visible=True,
        collidable=True,
        tags=["ihdgageizm"],
        layer=-5,
    ),
    "vjotnebuqo": Sprite(
        pixels=[
            [5, 5, 5, 5, 5, 5, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, 5, 5, 5, 5, 5, 5],
        ],
        name="vjotnebuqo",
        visible=True,
        collidable=True,
        tags=["vjotnebuqo"],
        layer=-3,
    ),
    "wgmbtyhvbc": Sprite(
        pixels=[
            [0, -1, 0],
            [-1, 0, -1],
            [0, -1, 0],
        ],
        name="wgmbtyhvbc",
        visible=True,
        collidable=True,
        tags=["wgmbtyhvbc"],
        layer=10,
    ),
    "xfmluydglp": Sprite(
        pixels=[
            [14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14],
            [14, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14],
            [14, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14],
            [14, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14],
            [14, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14],
            [14, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14],
            [14, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14],
            [14, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14],
            [14, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14],
            [14, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14],
            [14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14],
        ],
        name="xfmluydglp",
        visible=False,
        collidable=True,
        tags=["xfmluydglp"],
    ),
    "xvrpzkggig": Sprite(
        pixels=[
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        ],
        name="xvrpzkggig",
        visible=True,
        collidable=True,
    ),
    "yjgargdic_r": Sprite(
        pixels=[
            [1, -2, -2, -2, -2],
            [1, -2, -2, -2, -2],
            [1, -2, -2, -2, -2],
            [1, -2, -2, -2, -2],
            [1, -2, -2, -2, -2],
        ],
        name="yjgargdic_r",
        visible=True,
        collidable=True,
        tags=["gbvqrjtaqo"],
    ),
}
levels = [
    # Level 1
    Level(
        sprites=[
            sprites["eqatonpohu"].clone().set_position(1, 53),
            sprites["ghizzeqtoh"].clone().set_position(1, 53),
            sprites["hoswmpiqkw"].clone().set_position(33, 9),
            sprites["ihdgageizm"].clone().set_position(4, 0),
            sprites["ihdgageizm"].clone().set_position(9, 0),
            sprites["ihdgageizm"].clone().set_position(4, 5),
            sprites["ihdgageizm"].clone().set_position(14, 0),
            sprites["ihdgageizm"].clone().set_position(19, 0),
            sprites["ihdgageizm"].clone().set_position(24, 0),
            sprites["ihdgageizm"].clone().set_position(29, 0),
            sprites["ihdgageizm"].clone().set_position(39, 0),
            sprites["ihdgageizm"].clone().set_position(44, 0),
            sprites["ihdgageizm"].clone().set_position(49, 0),
            sprites["ihdgageizm"].clone().set_position(54, 0),
            sprites["ihdgageizm"].clone().set_position(59, 0),
            sprites["ihdgageizm"].clone().set_position(4, 10),
            sprites["ihdgageizm"].clone().set_position(4, 15),
            sprites["ihdgageizm"].clone().set_position(4, 20),
            sprites["ihdgageizm"].clone().set_position(4, 25),
            sprites["ihdgageizm"].clone().set_position(59, 15),
            sprites["ihdgageizm"].clone().set_position(59, 20),
            sprites["ihdgageizm"].clone().set_position(59, 25),
            sprites["ihdgageizm"].clone().set_position(59, 30),
            sprites["ihdgageizm"].clone().set_position(59, 20),
            sprites["ihdgageizm"].clone().set_position(59, 25),
            sprites["ihdgageizm"].clone().set_position(59, 30),
            sprites["ihdgageizm"].clone().set_position(59, 35),
            sprites["ihdgageizm"].clone().set_position(59, 40),
            sprites["ihdgageizm"].clone().set_position(59, 45),
            sprites["ihdgageizm"].clone().set_position(59, 35),
            sprites["ihdgageizm"].clone().set_position(59, 40),
            sprites["ihdgageizm"].clone().set_position(59, 45),
            sprites["ihdgageizm"].clone().set_position(59, 50),
            sprites["ihdgageizm"].clone().set_position(59, 55),
            sprites["ihdgageizm"].clone().set_position(59, 50),
            sprites["ihdgageizm"].clone().set_position(59, 55),
            sprites["ihdgageizm"].clone().set_position(54, 55),
            sprites["ihdgageizm"].clone().set_position(49, 55),
            sprites["ihdgageizm"].clone().set_position(44, 55),
            sprites["ihdgageizm"].clone().set_position(39, 55),
            sprites["ihdgageizm"].clone().set_position(34, 55),
            sprites["ihdgageizm"].clone().set_position(29, 55),
            sprites["ihdgageizm"].clone().set_position(24, 55),
            sprites["ihdgageizm"].clone().set_position(19, 55),
            sprites["ihdgageizm"].clone().set_position(4, 40),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(4, 50),
            sprites["ihdgageizm"].clone().set_position(9, 50),
            sprites["ihdgageizm"].clone().set_position(4, 55),
            sprites["ihdgageizm"].clone().set_position(9, 55),
            sprites["ihdgageizm"].clone().set_position(14, 55),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(54, 25),
            sprites["ihdgageizm"].clone().set_position(54, 20),
            sprites["ihdgageizm"].clone().set_position(34, 0),
            sprites["ihdgageizm"].clone().set_position(59, 10),
            sprites["ihdgageizm"].clone().set_position(59, 5),
            sprites["ihdgageizm"].clone().set_position(54, 15),
            sprites["ihdgageizm"].clone().set_position(54, 10),
            sprites["ihdgageizm"].clone().set_position(44, 5),
            sprites["ihdgageizm"].clone().set_position(39, 5),
            sprites["ihdgageizm"].clone().set_position(34, 5),
            sprites["ihdgageizm"].clone().set_position(29, 5),
            sprites["ihdgageizm"].clone().set_position(54, 50),
            sprites["ihdgageizm"].clone().set_position(54, 45),
            sprites["ihdgageizm"].clone().set_position(24, 5),
            sprites["ihdgageizm"].clone().set_position(19, 5),
            sprites["ihdgageizm"].clone().set_position(9, 35),
            sprites["ihdgageizm"].clone().set_position(9, 45),
            sprites["ihdgageizm"].clone().set_position(19, 50),
            sprites["ihdgageizm"].clone().set_position(9, 40),
            sprites["ihdgageizm"].clone().set_position(49, 5),
            sprites["ihdgageizm"].clone().set_position(54, 5),
            sprites["ihdgageizm"].clone().set_position(49, 50),
            sprites["ihdgageizm"].clone().set_position(14, 50),
            sprites["ihdgageizm"].clone().set_position(14, 5),
            sprites["ihdgageizm"].clone().set_position(9, 5),
            sprites["ihdgageizm"].clone().set_position(9, 30),
            sprites["ihdgageizm"].clone().set_position(9, 25),
            sprites["ihdgageizm"].clone().set_position(9, 20),
            sprites["ihdgageizm"].clone().set_position(9, 15),
            sprites["ihdgageizm"].clone().set_position(9, 10),
            sprites["ihdgageizm"].clone().set_position(49, 10),
            sprites["ihdgageizm"].clone().set_position(44, 20),
            sprites["ihdgageizm"].clone().set_position(39, 10),
            sprites["ihdgageizm"].clone().set_position(44, 10),
            sprites["ihdgageizm"].clone().set_position(49, 15),
            sprites["ihdgageizm"].clone().set_position(29, 10),
            sprites["ihdgageizm"].clone().set_position(29, 15),
            sprites["ihdgageizm"].clone().set_position(39, 15),
            sprites["ihdgageizm"].clone().set_position(44, 15),
            sprites["ihdgageizm"].clone().set_position(49, 20),
            sprites["ihdgageizm"].clone().set_position(14, 15),
            sprites["ihdgageizm"].clone().set_position(19, 15),
            sprites["ihdgageizm"].clone().set_position(24, 15),
            sprites["ihdgageizm"].clone().set_position(24, 10),
            sprites["ihdgageizm"].clone().set_position(19, 10),
            sprites["ihdgageizm"].clone().set_position(14, 10),
            sprites["ihdgageizm"].clone().set_position(29, 20),
            sprites["ihdgageizm"].clone().set_position(39, 20),
            sprites["ihdgageizm"].clone().set_position(24, 20),
            sprites["ihdgageizm"].clone().set_position(29, 40),
            sprites["ihdgageizm"].clone().set_position(19, 20),
            sprites["ihdgageizm"].clone().set_position(14, 20),
            sprites["ihdgageizm"].clone().set_position(54, 30),
            sprites["ihdgageizm"].clone().set_position(24, 40),
            sprites["ihdgageizm"].clone().set_position(14, 45),
            sprites["ihdgageizm"].clone().set_position(29, 35),
            sprites["ihdgageizm"].clone().set_position(4, 30).color_remap(None, 4),
            sprites["ihdgageizm"].clone().set_position(4, 35),
            sprites["ihdgageizm"].clone().set_position(54, 35),
            sprites["ihdgageizm"].clone().set_position(54, 40),
            sprites["ihdgageizm"].clone().set_position(14, 40),
            sprites["ihdgageizm"].clone().set_position(24, 50),
            sprites["ihdgageizm"].clone().set_position(29, 50),
            sprites["ihdgageizm"].clone().set_position(39, 50),
            sprites["ihdgageizm"].clone().set_position(44, 50),
            sprites["ihdgageizm"].clone().set_position(34, 50),
            sprites["ihdgageizm"].clone().set_position(29, 30),
            sprites["kvynsvxbpi"].clone().set_position(35, 11),
            sprites["nszegiawib"].clone().set_position(32, 8).set_rotation(180),
            sprites["rhsxkxzdjz"].clone().set_position(19, 30),
            sprites["rjlbuycveu"].clone().set_position(34, 10),
            sprites["sfqyzhzkij"].clone().set_position(34, 45),
            sprites["vjotnebuqo"].clone().set_position(33, 9),
            sprites["wgmbtyhvbc"].clone().set_position(3, 55).set_scale(2),
            sprites["xvrpzkggig"].clone(),
            sprites["ihdgageizm"].clone().set_position(39, 25),
        ],
        grid_size=(64, 64),
        data={
            "StepCounter": 42,
            "kvynsvxbpi": 5,
            "GoalColor": 9,
            "GoalRotation": 0,
            "StartShape": 5,
            "StartColor": 9,
            "StartRotation": 270,
            "Fog": False,
            "StepsDecrement": 0,
        },
    ),
    # Level 2
    Level(
        sprites=[
            sprites["eqatonpohu"].clone().set_position(1, 53),
            sprites["ghizzeqtoh"].clone().set_position(1, 53),
            sprites["hoswmpiqkw"].clone().set_position(13, 39),
            sprites["ihdgageizm"].clone().set_position(4, 0),
            sprites["ihdgageizm"].clone().set_position(9, 0),
            sprites["ihdgageizm"].clone().set_position(4, 5),
            sprites["ihdgageizm"].clone().set_position(14, 0),
            sprites["ihdgageizm"].clone().set_position(19, 0),
            sprites["ihdgageizm"].clone().set_position(24, 0),
            sprites["ihdgageizm"].clone().set_position(29, 0),
            sprites["ihdgageizm"].clone().set_position(39, 0),
            sprites["ihdgageizm"].clone().set_position(44, 0),
            sprites["ihdgageizm"].clone().set_position(49, 0),
            sprites["ihdgageizm"].clone().set_position(54, 0),
            sprites["ihdgageizm"].clone().set_position(59, 0),
            sprites["ihdgageizm"].clone().set_position(4, 10),
            sprites["ihdgageizm"].clone().set_position(4, 15),
            sprites["ihdgageizm"].clone().set_position(4, 20),
            sprites["ihdgageizm"].clone().set_position(4, 25),
            sprites["ihdgageizm"].clone().set_position(4, 30),
            sprites["ihdgageizm"].clone().set_position(4, 35),
            sprites["ihdgageizm"].clone().set_position(59, 15),
            sprites["ihdgageizm"].clone().set_position(59, 20),
            sprites["ihdgageizm"].clone().set_position(59, 25),
            sprites["ihdgageizm"].clone().set_position(59, 30),
            sprites["ihdgageizm"].clone().set_position(59, 20),
            sprites["ihdgageizm"].clone().set_position(59, 25),
            sprites["ihdgageizm"].clone().set_position(59, 30),
            sprites["ihdgageizm"].clone().set_position(59, 35),
            sprites["ihdgageizm"].clone().set_position(59, 40),
            sprites["ihdgageizm"].clone().set_position(59, 45),
            sprites["ihdgageizm"].clone().set_position(59, 35),
            sprites["ihdgageizm"].clone().set_position(59, 40),
            sprites["ihdgageizm"].clone().set_position(59, 45),
            sprites["ihdgageizm"].clone().set_position(59, 50),
            sprites["ihdgageizm"].clone().set_position(59, 55),
            sprites["ihdgageizm"].clone().set_position(59, 50),
            sprites["ihdgageizm"].clone().set_position(59, 55),
            sprites["ihdgageizm"].clone().set_position(54, 55),
            sprites["ihdgageizm"].clone().set_position(49, 55),
            sprites["ihdgageizm"].clone().set_position(44, 55),
            sprites["ihdgageizm"].clone().set_position(39, 55),
            sprites["ihdgageizm"].clone().set_position(34, 55),
            sprites["ihdgageizm"].clone().set_position(29, 55),
            sprites["ihdgageizm"].clone().set_position(24, 55),
            sprites["ihdgageizm"].clone().set_position(19, 55),
            sprites["ihdgageizm"].clone().set_position(4, 40),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(4, 50),
            sprites["ihdgageizm"].clone().set_position(9, 50),
            sprites["ihdgageizm"].clone().set_position(4, 55),
            sprites["ihdgageizm"].clone().set_position(9, 55),
            sprites["ihdgageizm"].clone().set_position(14, 55),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(54, 30),
            sprites["ihdgageizm"].clone().set_position(34, 0),
            sprites["ihdgageizm"].clone().set_position(59, 10),
            sprites["ihdgageizm"].clone().set_position(59, 5),
            sprites["ihdgageizm"].clone().set_position(54, 15),
            sprites["ihdgageizm"].clone().set_position(54, 10),
            sprites["ihdgageizm"].clone().set_position(9, 35),
            sprites["ihdgageizm"].clone().set_position(9, 45),
            sprites["ihdgageizm"].clone().set_position(19, 50),
            sprites["ihdgageizm"].clone().set_position(9, 40),
            sprites["ihdgageizm"].clone().set_position(54, 5),
            sprites["ihdgageizm"].clone().set_position(14, 45),
            sprites["ihdgageizm"].clone().set_position(14, 50),
            sprites["ihdgageizm"].clone().set_position(9, 5),
            sprites["ihdgageizm"].clone().set_position(9, 30),
            sprites["ihdgageizm"].clone().set_position(9, 25),
            sprites["ihdgageizm"].clone().set_position(19, 30),
            sprites["ihdgageizm"].clone().set_position(24, 30),
            sprites["ihdgageizm"].clone().set_position(19, 40),
            sprites["ihdgageizm"].clone().set_position(19, 45),
            sprites["ihdgageizm"].clone().set_position(19, 35),
            sprites["ihdgageizm"].clone().set_position(39, 15),
            sprites["ihdgageizm"].clone().set_position(39, 35),
            sprites["ihdgageizm"].clone().set_position(44, 30),
            sprites["ihdgageizm"].clone().set_position(34, 45),
            sprites["ihdgageizm"].clone().set_position(14, 5),
            sprites["ihdgageizm"].clone().set_position(39, 20),
            sprites["ihdgageizm"].clone().set_position(44, 20),
            sprites["ihdgageizm"].clone().set_position(24, 20),
            sprites["ihdgageizm"].clone().set_position(44, 25),
            sprites["ihdgageizm"].clone().set_position(39, 40),
            sprites["ihdgageizm"].clone().set_position(39, 45),
            sprites["ihdgageizm"].clone().set_position(24, 35),
            sprites["ihdgageizm"].clone().set_position(24, 25),
            sprites["ihdgageizm"].clone().set_position(24, 50),
            sprites["ihdgageizm"].clone().set_position(19, 25),
            sprites["ihdgageizm"].clone().set_position(24, 40),
            sprites["ihdgageizm"].clone().set_position(24, 45),
            sprites["ihdgageizm"].clone().set_position(29, 45),
            sprites["ihdgageizm"].clone().set_position(29, 30),
            sprites["ihdgageizm"].clone().set_position(29, 25),
            sprites["ihdgageizm"].clone().set_position(24, 15),
            sprites["ihdgageizm"].clone().set_position(44, 35),
            sprites["ihdgageizm"].clone().set_position(29, 50),
            sprites["ihdgageizm"].clone().set_position(34, 50),
            sprites["kvynsvxbpi"].clone().set_position(15, 41),
            sprites["npxgalaybz"].clone().set_position(15, 16),
            sprites["npxgalaybz"].clone().set_position(40, 51),
            sprites["nszegiawib"].clone().set_position(12, 38),
            sprites["rhsxkxzdjz"].clone().set_position(49, 45),
            sprites["rjlbuycveu"].clone().set_position(14, 40),
            sprites["sfqyzhzkij"].clone().set_position(29, 40),
            sprites["vjotnebuqo"].clone().set_position(13, 39),
            sprites["wgmbtyhvbc"].clone().set_position(3, 55).set_scale(2),
            sprites["xvrpzkggig"].clone(),
            sprites["ihdgageizm"].clone().set_position(9, 20),
        ],
        grid_size=(64, 64),
        data={
            "StepCounter": 42,
            "kvynsvxbpi": 5,
            "GoalColor": 9,
            "GoalRotation": 270,
            "StartShape": 5,
            "StartColor": 9,
            "StartRotation": 0,
            "Fog": False,
        },
    ),
    # Level 3
    Level(
        sprites=[
            sprites["eqatonpohu"].clone().set_position(1, 53),
            sprites["fesygzfqui"].clone().set_position(4, 5),
            sprites["ghizzeqtoh"].clone().set_position(1, 53),
            sprites["hoswmpiqkw"].clone().set_position(53, 49),
            sprites["ihdgageizm"].clone().set_position(4, 0),
            sprites["ihdgageizm"].clone().set_position(9, 0),
            sprites["ihdgageizm"].clone().set_position(14, 0),
            sprites["ihdgageizm"].clone().set_position(19, 0),
            sprites["ihdgageizm"].clone().set_position(24, 0),
            sprites["ihdgageizm"].clone().set_position(29, 0),
            sprites["ihdgageizm"].clone().set_position(39, 0),
            sprites["ihdgageizm"].clone().set_position(44, 0),
            sprites["ihdgageizm"].clone().set_position(49, 0),
            sprites["ihdgageizm"].clone().set_position(59, 0),
            sprites["ihdgageizm"].clone().set_position(4, 10),
            sprites["ihdgageizm"].clone().set_position(4, 15),
            sprites["ihdgageizm"].clone().set_position(4, 20),
            sprites["ihdgageizm"].clone().set_position(4, 25),
            sprites["ihdgageizm"].clone().set_position(4, 30),
            sprites["ihdgageizm"].clone().set_position(4, 35),
            sprites["ihdgageizm"].clone().set_position(59, 20),
            sprites["ihdgageizm"].clone().set_position(59, 25),
            sprites["ihdgageizm"].clone().set_position(59, 30),
            sprites["ihdgageizm"].clone().set_position(59, 35),
            sprites["ihdgageizm"].clone().set_position(59, 40),
            sprites["ihdgageizm"].clone().set_position(59, 45),
            sprites["ihdgageizm"].clone().set_position(59, 50),
            sprites["ihdgageizm"].clone().set_position(59, 55),
            sprites["ihdgageizm"].clone().set_position(49, 55),
            sprites["ihdgageizm"].clone().set_position(44, 55),
            sprites["ihdgageizm"].clone().set_position(39, 55),
            sprites["ihdgageizm"].clone().set_position(34, 55),
            sprites["ihdgageizm"].clone().set_position(29, 55),
            sprites["ihdgageizm"].clone().set_position(24, 55),
            sprites["ihdgageizm"].clone().set_position(19, 55),
            sprites["ihdgageizm"].clone().set_position(4, 40),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(4, 50),
            sprites["ihdgageizm"].clone().set_position(9, 50),
            sprites["ihdgageizm"].clone().set_position(4, 55),
            sprites["ihdgageizm"].clone().set_position(9, 55),
            sprites["ihdgageizm"].clone().set_position(14, 55),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(34, 0),
            sprites["ihdgageizm"].clone().set_position(59, 10),
            sprites["ihdgageizm"].clone().set_position(59, 5),
            sprites["ihdgageizm"].clone().set_position(39, 10),
            sprites["ihdgageizm"].clone().set_position(14, 25),
            sprites["ihdgageizm"].clone().set_position(19, 45),
            sprites["ihdgageizm"].clone().set_position(19, 35),
            sprites["ihdgageizm"].clone().set_position(49, 50),
            sprites["ihdgageizm"].clone().set_position(39, 35),
            sprites["ihdgageizm"].clone().set_position(14, 30),
            sprites["ihdgageizm"].clone().set_position(49, 45),
            sprites["ihdgageizm"].clone().set_position(49, 40),
            sprites["ihdgageizm"].clone().set_position(14, 20),
            sprites["ihdgageizm"].clone().set_position(14, 50),
            sprites["ihdgageizm"].clone().set_position(39, 5),
            sprites["ihdgageizm"].clone().set_position(44, 45),
            sprites["ihdgageizm"].clone().set_position(19, 50),
            sprites["ihdgageizm"].clone().set_position(44, 40),
            sprites["ihdgageizm"].clone().set_position(39, 50),
            sprites["ihdgageizm"].clone().set_position(44, 20),
            sprites["ihdgageizm"].clone().set_position(39, 20),
            sprites["ihdgageizm"].clone().set_position(19, 10),
            sprites["ihdgageizm"].clone().set_position(14, 35),
            sprites["ihdgageizm"].clone().set_position(39, 15),
            sprites["ihdgageizm"].clone().set_position(34, 35),
            sprites["ihdgageizm"].clone().set_position(14, 10),
            sprites["ihdgageizm"].clone().set_position(14, 15),
            sprites["ihdgageizm"].clone().set_position(49, 35),
            sprites["ihdgageizm"].clone().set_position(24, 35),
            sprites["ihdgageizm"].clone().set_position(34, 10),
            sprites["ihdgageizm"].clone().set_position(24, 10),
            sprites["ihdgageizm"].clone().set_position(59, 15),
            sprites["ihdgageizm"].clone().set_position(54, 55),
            sprites["ihdgageizm"].clone().set_position(44, 35),
            sprites["ihdgageizm"].clone().set_position(39, 40),
            sprites["ihdgageizm"].clone().set_position(39, 45),
            sprites["ihdgageizm"].clone().set_position(44, 50),
            sprites["kapcaakvb_b"].clone().set_position(54, 4),
            sprites["kvynsvxbpi"].clone().set_position(55, 51),
            sprites["mxfhnkdzvf"].clone().set_position(54, 0),
            sprites["npxgalaybz"].clone().set_position(35, 16),
            sprites["npxgalaybz"].clone().set_position(20, 31),
            sprites["nszegiawib"].clone().set_position(52, 48),
            sprites["rhsxkxzdjz"].clone().set_position(49, 10),
            sprites["rjlbuycveu"].clone().set_position(54, 50),
            sprites["sfqyzhzkij"].clone().set_position(9, 45),
            sprites["soyhouuebz"].clone().set_position(29, 45),
            sprites["vjotnebuqo"].clone().set_position(53, 49),
            sprites["wgmbtyhvbc"].clone().set_position(3, 55).set_scale(2),
            sprites["xvrpzkggig"].clone(),
            sprites["yjgargdic_r"].clone().set_position(8, 5),
            sprites["ihdgageizm"].clone().set_position(24, 50),
            sprites["ihdgageizm"].clone().set_position(29, 25),
            sprites["ihdgageizm"].clone().set_position(54, 10),
            sprites["ihdgageizm"].clone().set_position(44, 15),
            sprites["ihdgageizm"].clone().set_position(9, 35),
            sprites["ihdgageizm"].clone().set_position(24, 30),
        ],
        grid_size=(64, 64),
        data={
            "StepCounter": 42,
            "kvynsvxbpi": 5,
            "GoalColor": 9,
            "GoalRotation": 180,
            "StartShape": 5,
            "StartColor": 12,
            "StartRotation": 0,
            "Fog": False,
        },
    ),
    # Level 4
    Level(
        sprites=[
            sprites["eqatonpohu"].clone().set_position(1, 53),
            sprites["fesygzfqui"].clone().set_position(29, 20),
            sprites["fesygzfqui"].clone().set_position(4, 35),
            sprites["ghizzeqtoh"].clone().set_position(1, 53),
            sprites["hoswmpiqkw"].clone().set_position(8, 4),
            sprites["ihdgageizm"].clone().set_position(4, 0),
            sprites["ihdgageizm"].clone().set_position(9, 0),
            sprites["ihdgageizm"].clone().set_position(4, 5),
            sprites["ihdgageizm"].clone().set_position(14, 0),
            sprites["ihdgageizm"].clone().set_position(19, 0),
            sprites["ihdgageizm"].clone().set_position(24, 0),
            sprites["ihdgageizm"].clone().set_position(29, 0),
            sprites["ihdgageizm"].clone().set_position(39, 0),
            sprites["ihdgageizm"].clone().set_position(44, 0),
            sprites["ihdgageizm"].clone().set_position(49, 0),
            sprites["ihdgageizm"].clone().set_position(54, 0),
            sprites["ihdgageizm"].clone().set_position(59, 0),
            sprites["ihdgageizm"].clone().set_position(4, 10),
            sprites["ihdgageizm"].clone().set_position(4, 15),
            sprites["ihdgageizm"].clone().set_position(4, 20),
            sprites["ihdgageizm"].clone().set_position(4, 25),
            sprites["ihdgageizm"].clone().set_position(4, 30),
            sprites["ihdgageizm"].clone().set_position(59, 15),
            sprites["ihdgageizm"].clone().set_position(59, 20),
            sprites["ihdgageizm"].clone().set_position(59, 25),
            sprites["ihdgageizm"].clone().set_position(59, 30),
            sprites["ihdgageizm"].clone().set_position(59, 20),
            sprites["ihdgageizm"].clone().set_position(59, 25),
            sprites["ihdgageizm"].clone().set_position(59, 30),
            sprites["ihdgageizm"].clone().set_position(59, 35),
            sprites["ihdgageizm"].clone().set_position(59, 40),
            sprites["ihdgageizm"].clone().set_position(59, 45),
            sprites["ihdgageizm"].clone().set_position(59, 35),
            sprites["ihdgageizm"].clone().set_position(59, 40),
            sprites["ihdgageizm"].clone().set_position(59, 45),
            sprites["ihdgageizm"].clone().set_position(59, 50),
            sprites["ihdgageizm"].clone().set_position(59, 55),
            sprites["ihdgageizm"].clone().set_position(59, 50),
            sprites["ihdgageizm"].clone().set_position(59, 55),
            sprites["ihdgageizm"].clone().set_position(54, 55),
            sprites["ihdgageizm"].clone().set_position(49, 55),
            sprites["ihdgageizm"].clone().set_position(44, 55),
            sprites["ihdgageizm"].clone().set_position(39, 55),
            sprites["ihdgageizm"].clone().set_position(34, 55),
            sprites["ihdgageizm"].clone().set_position(29, 55),
            sprites["ihdgageizm"].clone().set_position(24, 55),
            sprites["ihdgageizm"].clone().set_position(19, 55),
            sprites["ihdgageizm"].clone().set_position(4, 40),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(4, 50),
            sprites["ihdgageizm"].clone().set_position(9, 50),
            sprites["ihdgageizm"].clone().set_position(4, 55),
            sprites["ihdgageizm"].clone().set_position(9, 55),
            sprites["ihdgageizm"].clone().set_position(14, 55),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(59, 10),
            sprites["ihdgageizm"].clone().set_position(59, 5),
            sprites["ihdgageizm"].clone().set_position(14, 10),
            sprites["ihdgageizm"].clone().set_position(9, 10),
            sprites["ihdgageizm"].clone().set_position(24, 25),
            sprites["ihdgageizm"].clone().set_position(29, 30),
            sprites["ihdgageizm"].clone().set_position(19, 10),
            sprites["ihdgageizm"].clone().set_position(9, 20),
            sprites["ihdgageizm"].clone().set_position(29, 25),
            sprites["ihdgageizm"].clone().set_position(29, 35),
            sprites["ihdgageizm"].clone().set_position(19, 50),
            sprites["ihdgageizm"].clone().set_position(39, 50),
            sprites["ihdgageizm"].clone().set_position(9, 15),
            sprites["ihdgageizm"].clone().set_position(49, 10),
            sprites["ihdgageizm"].clone().set_position(44, 10),
            sprites["ihdgageizm"].clone().set_position(39, 45),
            sprites["ihdgageizm"].clone().set_position(39, 50),
            sprites["ihdgageizm"].clone().set_position(44, 50),
            sprites["ihdgageizm"].clone().set_position(19, 25),
            sprites["ihdgageizm"].clone().set_position(39, 35),
            sprites["ihdgageizm"].clone().set_position(14, 50),
            sprites["ihdgageizm"].clone().set_position(9, 45),
            sprites["ihdgageizm"].clone().set_position(29, 5),
            sprites["ihdgageizm"].clone().set_position(14, 15),
            sprites["ihdgageizm"].clone().set_position(34, 0),
            sprites["ihdgageizm"].clone().set_position(29, 10),
            sprites["ihdgageizm"].clone().set_position(34, 5),
            sprites["ihdgageizm"].clone().set_position(54, 10),
            sprites["kapcaakvb_b"].clone().set_position(19, 34),
            sprites["kapcaakvb_b"].clone().set_position(44, 19),
            sprites["krdypjjivz"].clone().set_position(39, 30),
            sprites["kvynsvxbpi"].clone().set_position(10, 6),
            sprites["lujfinsby_t"].clone().set_position(39, 26),
            sprites["mkjdaccuuf"].clone().set_position(24, 30),
            sprites["mxfhnkdzvf"].clone().set_position(19, 30),
            sprites["mxfhnkdzvf"].clone().set_position(44, 15),
            sprites["npxgalaybz"].clone().set_position(35, 51),
            sprites["npxgalaybz"].clone().set_position(20, 16),
            sprites["nszegiawib"].clone().set_position(7, 3).set_rotation(90),
            sprites["rjlbuycveu"].clone().set_position(9, 5),
            sprites["sfqyzhzkij"].clone().set_position(54, 5),
            sprites["soyhouuebz"].clone().set_position(34, 30),
            sprites["tihiodtoj_l"].clone().set_position(45, 25),
            sprites["tihiodtoj_l"].clone().set_position(25, 40),
            sprites["tihiodtoj_l"].clone().set_position(45, 40),
            sprites["ubyunwkbpx"].clone().set_position(49, 25),
            sprites["ubyunwkbpx"].clone().set_position(29, 40),
            sprites["ubyunwkbpx"].clone().set_position(49, 40),
            sprites["vjotnebuqo"].clone().set_position(8, 4),
            sprites["wgmbtyhvbc"].clone().set_position(3, 55).set_scale(2),
            sprites["xvrpzkggig"].clone(),
            sprites["yjgargdic_r"].clone().set_position(33, 20),
            sprites["yjgargdic_r"].clone().set_position(8, 35),
            sprites["ihdgageizm"].clone().set_position(39, 15),
            sprites["ihdgageizm"].clone().set_position(54, 35),
        ],
        grid_size=(64, 64),
        data={
            "StepCounter": 42,
            "kvynsvxbpi": 5,
            "GoalColor": 9,
            "GoalRotation": 0,
            "StartShape": 4,
            "StartColor": 14,
            "StartRotation": 0,
            "Fog": False,
            "StepsDecrement": 1,
        },
    ),
    # Level 5
    Level(
        sprites=[
            sprites["ajdspzphhd"].clone().set_position(14, 35),
            sprites["eqatonpohu"].clone().set_position(1, 53),
            sprites["fesygzfqui"].clone().set_position(29, 20),
            sprites["fesygzfqui"].clone().set_position(39, 40),
            sprites["ghizzeqtoh"].clone().set_position(1, 53),
            sprites["hoswmpiqkw"].clone().set_position(53, 4),
            sprites["ihdgageizm"].clone().set_position(4, 0),
            sprites["ihdgageizm"].clone().set_position(9, 0),
            sprites["ihdgageizm"].clone().set_position(4, 5),
            sprites["ihdgageizm"].clone().set_position(19, 0),
            sprites["ihdgageizm"].clone().set_position(24, 0),
            sprites["ihdgageizm"].clone().set_position(29, 0),
            sprites["ihdgageizm"].clone().set_position(39, 0),
            sprites["ihdgageizm"].clone().set_position(44, 0),
            sprites["ihdgageizm"].clone().set_position(49, 0),
            sprites["ihdgageizm"].clone().set_position(54, 0),
            sprites["ihdgageizm"].clone().set_position(59, 0),
            sprites["ihdgageizm"].clone().set_position(4, 10),
            sprites["ihdgageizm"].clone().set_position(4, 15),
            sprites["ihdgageizm"].clone().set_position(4, 20),
            sprites["ihdgageizm"].clone().set_position(4, 25),
            sprites["ihdgageizm"].clone().set_position(4, 30),
            sprites["ihdgageizm"].clone().set_position(4, 35),
            sprites["ihdgageizm"].clone().set_position(59, 50),
            sprites["ihdgageizm"].clone().set_position(59, 55),
            sprites["ihdgageizm"].clone().set_position(39, 55),
            sprites["ihdgageizm"].clone().set_position(34, 55),
            sprites["ihdgageizm"].clone().set_position(29, 55),
            sprites["ihdgageizm"].clone().set_position(24, 55),
            sprites["ihdgageizm"].clone().set_position(19, 55),
            sprites["ihdgageizm"].clone().set_position(4, 40),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(4, 50),
            sprites["ihdgageizm"].clone().set_position(9, 50),
            sprites["ihdgageizm"].clone().set_position(4, 55),
            sprites["ihdgageizm"].clone().set_position(9, 55),
            sprites["ihdgageizm"].clone().set_position(14, 55),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(59, 5),
            sprites["ihdgageizm"].clone().set_position(49, 10),
            sprites["ihdgageizm"].clone().set_position(49, 5),
            sprites["ihdgageizm"].clone().set_position(29, 30),
            sprites["ihdgageizm"].clone().set_position(9, 20),
            sprites["ihdgageizm"].clone().set_position(24, 30),
            sprites["ihdgageizm"].clone().set_position(24, 20),
            sprites["ihdgageizm"].clone().set_position(34, 30),
            sprites["ihdgageizm"].clone().set_position(49, 45),
            sprites["ihdgageizm"].clone().set_position(49, 20),
            sprites["ihdgageizm"].clone().set_position(44, 55),
            sprites["ihdgageizm"].clone().set_position(49, 55),
            sprites["ihdgageizm"].clone().set_position(59, 10),
            sprites["ihdgageizm"].clone().set_position(59, 20),
            sprites["ihdgageizm"].clone().set_position(59, 25),
            sprites["ihdgageizm"].clone().set_position(59, 35),
            sprites["ihdgageizm"].clone().set_position(59, 40),
            sprites["ihdgageizm"].clone().set_position(59, 45),
            sprites["ihdgageizm"].clone().set_position(39, 45),
            sprites["ihdgageizm"].clone().set_position(44, 45),
            sprites["ihdgageizm"].clone().set_position(29, 35),
            sprites["ihdgageizm"].clone().set_position(9, 5),
            sprites["ihdgageizm"].clone().set_position(34, 45),
            sprites["ihdgageizm"].clone().set_position(29, 10),
            sprites["ihdgageizm"].clone().set_position(14, 20),
            sprites["ihdgageizm"].clone().set_position(14, 0),
            sprites["ihdgageizm"].clone().set_position(19, 30),
            sprites["ihdgageizm"].clone().set_position(14, 30),
            sprites["ihdgageizm"].clone().set_position(9, 15),
            sprites["ihdgageizm"].clone().set_position(29, 45),
            sprites["ihdgageizm"].clone().set_position(14, 50),
            sprites["ihdgageizm"].clone().set_position(9, 45),
            sprites["ihdgageizm"].clone().set_position(49, 15),
            sprites["ihdgageizm"].clone().set_position(59, 15),
            sprites["ihdgageizm"].clone().set_position(44, 10),
            sprites["kapcaakvb_b"].clone().set_position(34, 4),
            sprites["kapcaakvb_b"].clone().set_position(49, 29),
            sprites["krdypjjivz"].clone().set_position(54, 55),
            sprites["krdypjjivz"].clone().set_position(39, 30),
            sprites["kvynsvxbpi"].clone().set_position(55, 6),
            sprites["lujfinsby_t"].clone().set_position(54, 51),
            sprites["lujfinsby_t"].clone().set_position(39, 26),
            sprites["mkjdaccuuf"].clone().set_position(19, 10),
            sprites["mxfhnkdzvf"].clone().set_position(34, 0),
            sprites["mxfhnkdzvf"].clone().set_position(49, 25),
            sprites["npxgalaybz"].clone().set_position(15, 46),
            sprites["npxgalaybz"].clone().set_position(45, 6),
            sprites["npxgalaybz"].clone().set_position(10, 11),
            sprites["nszegiawib"].clone().set_position(52, 3).set_rotation(180),
            sprites["rhsxkxzdjz"].clone().set_position(14, 35),
            sprites["rjlbuycveu"].clone().set_position(54, 5),
            sprites["sfqyzhzkij"].clone().set_position(49, 40),
            sprites["soyhouuebz"].clone().set_position(29, 25),
            sprites["tihiodtoj_l"].clone().set_position(55, 30),
            sprites["tihiodtoj_l"].clone().set_position(20, 25),
            sprites["ubyunwkbpx"].clone().set_position(59, 30),
            sprites["ubyunwkbpx"].clone().set_position(24, 25),
            sprites["vjotnebuqo"].clone().set_position(53, 4),
            sprites["wgmbtyhvbc"].clone().set_position(3, 55).set_scale(2),
            sprites["xvrpzkggig"].clone(),
            sprites["yjgargdic_r"].clone().set_position(33, 20),
            sprites["yjgargdic_r"].clone().set_position(43, 40),
            sprites["ihdgageizm"].clone().set_position(14, 15),
            sprites["ihdgageizm"].clone().set_position(19, 40),
        ],
        grid_size=(64, 64),
        data={
            "StepsDecrement": 1,
            "StepCounter": 42,
            "kvynsvxbpi": 0,
            "GoalColor": 8,
            "GoalRotation": 180,
            "StartShape": 4,
            "StartColor": 12,
            "StartRotation": 0,
            "Fog": False,
        },
    ),
    # Level 6
    Level(
        sprites=[
            sprites["eqatonpohu"].clone().set_position(1, 53),
            sprites["ghizzeqtoh"].clone().set_position(1, 53),
            sprites["hahdypcdru"].clone().set_position(14, 40),
            sprites["hahdypcdru"].clone().set_position(14, 10),
            sprites["hoswmpiqkw"].clone().set_position(53, 34),
            sprites["hoswmpiqkw"].clone().set_position(53, 49),
            sprites["ihdgageizm"].clone().set_position(4, 0),
            sprites["ihdgageizm"].clone().set_position(9, 0),
            sprites["ihdgageizm"].clone().set_position(4, 5),
            sprites["ihdgageizm"].clone().set_position(14, 0),
            sprites["ihdgageizm"].clone().set_position(19, 0),
            sprites["ihdgageizm"].clone().set_position(24, 0),
            sprites["ihdgageizm"].clone().set_position(29, 0),
            sprites["ihdgageizm"].clone().set_position(39, 0),
            sprites["ihdgageizm"].clone().set_position(59, 0),
            sprites["ihdgageizm"].clone().set_position(4, 10),
            sprites["ihdgageizm"].clone().set_position(4, 15),
            sprites["ihdgageizm"].clone().set_position(4, 20),
            sprites["ihdgageizm"].clone().set_position(4, 25),
            sprites["ihdgageizm"].clone().set_position(4, 30),
            sprites["ihdgageizm"].clone().set_position(4, 35),
            sprites["ihdgageizm"].clone().set_position(59, 25),
            sprites["ihdgageizm"].clone().set_position(59, 30),
            sprites["ihdgageizm"].clone().set_position(59, 35),
            sprites["ihdgageizm"].clone().set_position(59, 40),
            sprites["ihdgageizm"].clone().set_position(59, 45),
            sprites["ihdgageizm"].clone().set_position(59, 50),
            sprites["ihdgageizm"].clone().set_position(59, 55),
            sprites["ihdgageizm"].clone().set_position(49, 55),
            sprites["ihdgageizm"].clone().set_position(44, 55),
            sprites["ihdgageizm"].clone().set_position(39, 55),
            sprites["ihdgageizm"].clone().set_position(34, 55),
            sprites["ihdgageizm"].clone().set_position(29, 55),
            sprites["ihdgageizm"].clone().set_position(24, 55),
            sprites["ihdgageizm"].clone().set_position(19, 55),
            sprites["ihdgageizm"].clone().set_position(4, 40),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(4, 50),
            sprites["ihdgageizm"].clone().set_position(9, 50),
            sprites["ihdgageizm"].clone().set_position(4, 55),
            sprites["ihdgageizm"].clone().set_position(9, 55),
            sprites["ihdgageizm"].clone().set_position(14, 55),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(34, 0),
            sprites["ihdgageizm"].clone().set_position(59, 10),
            sprites["ihdgageizm"].clone().set_position(59, 5),
            sprites["ihdgageizm"].clone().set_position(29, 35),
            sprites["ihdgageizm"].clone().set_position(24, 35),
            sprites["ihdgageizm"].clone().set_position(34, 35),
            sprites["ihdgageizm"].clone().set_position(49, 35),
            sprites["ihdgageizm"].clone().set_position(49, 40),
            sprites["ihdgageizm"].clone().set_position(49, 45),
            sprites["ihdgageizm"].clone().set_position(49, 50),
            sprites["ihdgageizm"].clone().set_position(49, 30),
            sprites["ihdgageizm"].clone().set_position(44, 30),
            sprites["ihdgageizm"].clone().set_position(19, 15),
            sprites["ihdgageizm"].clone().set_position(14, 35),
            sprites["ihdgageizm"].clone().set_position(24, 15),
            sprites["ihdgageizm"].clone().set_position(34, 30),
            sprites["ihdgageizm"].clone().set_position(19, 35),
            sprites["ihdgageizm"].clone().set_position(29, 15),
            sprites["ihdgageizm"].clone().set_position(14, 30),
            sprites["ihdgageizm"].clone().set_position(34, 15),
            sprites["ihdgageizm"].clone().set_position(14, 15),
            sprites["ihdgageizm"].clone().set_position(34, 20),
            sprites["ihdgageizm"].clone().set_position(14, 20),
            sprites["ihdgageizm"].clone().set_position(54, 55),
            sprites["ihdgageizm"].clone().set_position(44, 0),
            sprites["ihdgageizm"].clone().set_position(54, 0),
            sprites["ihdgageizm"].clone().set_position(59, 15),
            sprites["ihdgageizm"].clone().set_position(44, 25),
            sprites["ihdgageizm"].clone().set_position(59, 20),
            sprites["ihdgageizm"].clone().set_position(44, 35),
            sprites["ihdgageizm"].clone().set_position(44, 50),
            sprites["ihdgageizm"].clone().set_position(39, 50),
            sprites["ihdgageizm"].clone().set_position(44, 45),
            sprites["ihdgageizm"].clone().set_position(44, 40),
            sprites["ihdgageizm"].clone().set_position(44, 5),
            sprites["ihdgageizm"].clone().set_position(54, 15),
            sprites["kapcaakvb_b"].clone().set_position(49, 4),
            sprites["kvynsvxbpi"].clone().set_position(55, 51),
            sprites["kvynsvxbpi"].clone().set_position(55, 36),
            sprites["mkjdaccuuf"].clone().set_position(14, 10),
            sprites["mxfhnkdzvf"].clone().set_position(49, 0),
            sprites["njpewhmtfd"].clone().set_position(53, 34),
            sprites["npxgalaybz"].clone().set_position(40, 6),
            sprites["npxgalaybz"].clone().set_position(10, 46),
            sprites["npxgalaybz"].clone().set_position(10, 6),
            sprites["nszegiawib"].clone().set_position(52, 48),
            sprites["nszegiawib"].clone().set_position(52, 33),
            sprites["rhsxkxzdjz"].clone().set_position(34, 40),
            sprites["rjlbuycveu"].clone().set_position(54, 50),
            sprites["rjlbuycveu"].clone().set_position(54, 35),
            sprites["sfqyzhzkij"].clone().set_position(24, 50),
            sprites["soyhouuebz"].clone().set_position(24, 30),
            sprites["tihiodtoj_l"].clone().set_position(50, 20),
            sprites["ubyunwkbpx"].clone().set_position(54, 20),
            sprites["vjotnebuqo"].clone().set_position(53, 49),
            sprites["wgmbtyhvbc"].clone().set_position(3, 55).set_scale(2),
            sprites["xfmluydglp"].clone().set_position(19, 20),
            sprites["xvrpzkggig"].clone(),
            sprites["npxgalaybz"].clone().set_position(55, 41),
            sprites["ihdgageizm"].clone().set_position(39, 20),
            sprites["ihdgageizm"].clone().set_position(29, 5),
            sprites["ihdgageizm"].clone().set_position(19, 45),
            sprites["ihdgageizm"].clone().set_position(54, 10),
        ],
        grid_size=(64, 64),
        data={
            "StepCounter": 42,
            "kvynsvxbpi": [5, 0],
            "GoalColor": [9, 8],
            "GoalRotation": [90, 180],
            "StartShape": 0,
            "StartColor": 14,
            "StartRotation": 0,
            "Fog": False,
            "StepsDecrement": 1,
        },
    ),
    # Level 7
    Level(
        sprites=[
            sprites["eqatonpohu"].clone().set_position(1, 53),
            sprites["ghizzeqtoh"].clone().set_position(1, 53),
            sprites["hoswmpiqkw"].clone().set_position(28, 49),
            sprites["ihdgageizm"].clone().set_position(4, 0),
            sprites["ihdgageizm"].clone().set_position(9, 0),
            sprites["ihdgageizm"].clone().set_position(4, 5),
            sprites["ihdgageizm"].clone().set_position(14, 0),
            sprites["ihdgageizm"].clone().set_position(19, 0),
            sprites["ihdgageizm"].clone().set_position(24, 0),
            sprites["ihdgageizm"].clone().set_position(29, 0),
            sprites["ihdgageizm"].clone().set_position(39, 0),
            sprites["ihdgageizm"].clone().set_position(44, 0),
            sprites["ihdgageizm"].clone().set_position(49, 0),
            sprites["ihdgageizm"].clone().set_position(54, 0),
            sprites["ihdgageizm"].clone().set_position(59, 0),
            sprites["ihdgageizm"].clone().set_position(4, 10),
            sprites["ihdgageizm"].clone().set_position(4, 15),
            sprites["ihdgageizm"].clone().set_position(4, 20),
            sprites["ihdgageizm"].clone().set_position(4, 25),
            sprites["ihdgageizm"].clone().set_position(4, 30),
            sprites["ihdgageizm"].clone().set_position(4, 35),
            sprites["ihdgageizm"].clone().set_position(59, 20),
            sprites["ihdgageizm"].clone().set_position(59, 30),
            sprites["ihdgageizm"].clone().set_position(59, 45),
            sprites["ihdgageizm"].clone().set_position(59, 50),
            sprites["ihdgageizm"].clone().set_position(59, 55),
            sprites["ihdgageizm"].clone().set_position(59, 55),
            sprites["ihdgageizm"].clone().set_position(54, 55),
            sprites["ihdgageizm"].clone().set_position(49, 55),
            sprites["ihdgageizm"].clone().set_position(44, 55),
            sprites["ihdgageizm"].clone().set_position(39, 55),
            sprites["ihdgageizm"].clone().set_position(34, 55),
            sprites["ihdgageizm"].clone().set_position(29, 55),
            sprites["ihdgageizm"].clone().set_position(24, 55),
            sprites["ihdgageizm"].clone().set_position(19, 55),
            sprites["ihdgageizm"].clone().set_position(4, 40),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(4, 50),
            sprites["ihdgageizm"].clone().set_position(9, 50),
            sprites["ihdgageizm"].clone().set_position(4, 55),
            sprites["ihdgageizm"].clone().set_position(9, 55),
            sprites["ihdgageizm"].clone().set_position(14, 55),
            sprites["ihdgageizm"].clone().set_position(4, 45),
            sprites["ihdgageizm"].clone().set_position(34, 0),
            sprites["ihdgageizm"].clone().set_position(59, 10),
            sprites["ihdgageizm"].clone().set_position(59, 5),
            sprites["ihdgageizm"].clone().set_position(24, 40),
            sprites["ihdgageizm"].clone().set_position(44, 10),
            sprites["ihdgageizm"].clone().set_position(44, 5),
            sprites["ihdgageizm"].clone().set_position(44, 15),
            sprites["ihdgageizm"].clone().set_position(39, 45),
            sprites["ihdgageizm"].clone().set_position(24, 45),
            sprites["ihdgageizm"].clone().set_position(34, 45),
            sprites["ihdgageizm"].clone().set_position(24, 50),
            sprites["ihdgageizm"].clone().set_position(34, 50),
            sprites["ihdgageizm"].clone().set_position(44, 20),
            sprites["ihdgageizm"].clone().set_position(44, 25),
            sprites["ihdgageizm"].clone().set_position(19, 50),
            sprites["ihdgageizm"].clone().set_position(24, 35),
            sprites["ihdgageizm"].clone().set_position(39, 50),
            sprites["ihdgageizm"].clone().set_position(9, 45),
            sprites["ihdgageizm"].clone().set_position(14, 50),
            sprites["ihdgageizm"].clone().set_position(19, 45),
            sprites["ihdgageizm"].clone().set_position(29, 15),
            sprites["ihdgageizm"].clone().set_position(59, 15),
            sprites["ihdgageizm"].clone().set_position(59, 25),
            sprites["ihdgageizm"].clone().set_position(59, 35),
            sprites["ihdgageizm"].clone().set_position(59, 40),
            sprites["ihdgageizm"].clone().set_position(44, 45),
            sprites["ihdgageizm"].clone().set_position(24, 15),
            sprites["ihdgageizm"].clone().set_position(19, 20),
            sprites["ihdgageizm"].clone().set_position(54, 45),
            sprites["ihdgageizm"].clone().set_position(34, 40),
            sprites["ihdgageizm"].clone().set_position(34, 5),
            sprites["ihdgageizm"].clone().set_position(24, 10),
            sprites["ihdgageizm"].clone().set_position(24, 30),
            sprites["ihdgageizm"].clone().set_position(19, 30),
            sprites["ihdgageizm"].clone().set_position(14, 20),
            sprites["ihdgageizm"].clone().set_position(14, 30),
            sprites["irgjxweouz"].clone().set_position(54, 5),
            sprites["kapcaakvb_b"].clone().set_position(39, 19),
            sprites["krdypjjivz"].clone().set_position(34, 35),
            sprites["kvynsvxbpi"].clone().set_position(30, 51),
            sprites["lujfinsby_t"].clone().set_position(34, 31),
            sprites["mkjdaccuuf"].clone().set_position(19, 40),
            sprites["mxfhnkdzvf"].clone().set_position(39, 15),
            sprites["npxgalaybz"].clone().set_position(30, 21),
            sprites["npxgalaybz"].clone().set_position(50, 6),
            sprites["npxgalaybz"].clone().set_position(15, 46),
            sprites["npxgalaybz"].clone().set_position(40, 6),
            sprites["npxgalaybz"].clone().set_position(55, 51),
            sprites["npxgalaybz"].clone().set_position(10, 6),
            sprites["nszegiawib"].clone().set_position(27, 48),
            sprites["rhsxkxzdjz"].clone().set_position(54, 10),
            sprites["rjlbuycveu"].clone().set_position(29, 50),
            sprites["sfqyzhzkij"].clone().set_position(19, 15),
            sprites["soyhouuebz"].clone().set_position(9, 40),
            sprites["tihiodtoj_l"].clone().set_position(40, 30),
            sprites["ubyunwkbpx"].clone().set_position(44, 30),
            sprites["vjotnebuqo"].clone().set_position(28, 49),
            sprites["wgmbtyhvbc"].clone().set_position(3, 55).set_scale(2),
            sprites["xvrpzkggig"].clone(),
            sprites["ihdgageizm"].clone().set_position(39, 10),
            sprites["ihdgageizm"].clone().set_position(34, 25),
            sprites["ihdgageizm"].clone().set_position(49, 10),
        ],
        grid_size=(64, 64),
        data={
            "StepsDecrement": 1,
            "StepCounter": 42,
            "kvynsvxbpi": 0,
            "GoalColor": 8,
            "GoalRotation": 180,
            "StartShape": 1,
            "StartColor": 12,
            "StartRotation": 0,
            "Fog": True,
        },
    ),
]
BACKGROUND_COLOR = 3
PADDING_COLOR = 3
ubupgomgin = -1
epeqflmtfc = 0
dqifgqaxrg = 1
oazrnhzatr = 2
iisukudgvu = 3
kacnekcwsp = 4
avbdwkmqcy = 5
ijbilzmvdl = 6
yffnqoouus = 7
tqogkgimes = 8
jninpsotet = 9
vgcsccvckt = 10
dhxmtlewyv = 11
epqvqkpffo = 12
qqkmepheqb = 13
bejggpjowv = 14
eqvdisyxbr = 15
zoghkczvvt = 5
_SLIDE_MAX = 99  # longest slide in cells; 1 turns sliding off (the needed-check)
_TILT_PINK = 13  # raw colour that this copy's palette shows as pink
xvzyzqolqz = 5


class hbuhvkxlhc(RenderableUserDisplay):
    """."""

    bfdcztirdu: List[Tuple[int, int]]

    def __init__(self, vjhajnbdzr: "Vp15", osgviligwp: int):
        self.vjhajnbdzr = vjhajnbdzr
        self.osgviligwp = osgviligwp
        self.current_steps = osgviligwp
        self.efipnixsvl = 1

    def kbkdzqocik(self, kapizhweba: int) -> None:
        self.current_steps = max(0, min(kapizhweba, self.osgviligwp))

    def vytykscvhe(self, efipnixsvl: int) -> None:
        self.efipnixsvl = efipnixsvl

    def mfyzdfvxsm(self) -> bool:
        if self.current_steps >= 0:
            self.current_steps -= self.efipnixsvl
        return self.current_steps >= 0

    def nzukewekzr(self) -> None:
        self.current_steps = self.osgviligwp

    @staticmethod
    def _tilted(frame: np.ndarray, dx: int, dy: int) -> np.ndarray:
        """The board (rows 0-60) shifts one pixel the tilted way; a one-pixel pink line lights on that edge. The key box
        and the step bar keep still. Raw coordinates: the view layer turns the result like everything else."""
        src = frame.copy()
        board = np.roll(src[:61], (dy, dx), axis=(0, 1))
        if dy:
            board[-1 if dy < 0 else 0, :] = BACKGROUND_COLOR
        if dx:
            board[:, -1 if dx < 0 else 0] = BACKGROUND_COLOR
        frame[:61] = board
        frame[52:61, 0:12] = src[52:61, 0:12]
        if dy:
            frame[0 if dy < 0 else 60, :] = _TILT_PINK
        if dx:
            frame[:61, 0 if dx < 0 else 63] = _TILT_PINK
        return frame

    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        tilt = getattr(self.vjhajnbdzr, "_tilt", None)
        if tilt is not None:
            frame = self._tilted(frame, tilt[0], tilt[1])
        if self.osgviligwp == 0 or self.vjhajnbdzr.ebfuxzbvn:
            return frame
        yydgfgfvvh = 1.5
        if self.vjhajnbdzr.oeuabekjf:
            for i in range(64):
                for fbklvtfnjh in range(64):
                    if (
                        math.dist(
                            (i, fbklvtfnjh),
                            (
                                self.vjhajnbdzr.gudziatsk.y + yydgfgfvvh,
                                self.vjhajnbdzr.gudziatsk.x + yydgfgfvvh,
                            ),
                        )
                        > 20.0
                    ):
                        frame[i, fbklvtfnjh] = avbdwkmqcy
            if self.vjhajnbdzr.htkmubhry and self.vjhajnbdzr.htkmubhry.is_visible:
                sprite = self.vjhajnbdzr.htkmubhry.render()
                wmdkkxqkw = 3
                toxqhfsju = 55
                for i in range(self.vjhajnbdzr.htkmubhry.height):
                    for rejdvlfhdv in range(self.vjhajnbdzr.htkmubhry.width):
                        if sprite[i][rejdvlfhdv] != -1:
                            frame[toxqhfsju + i, wmdkkxqkw + rejdvlfhdv] = sprite[i][rejdvlfhdv]
        for i in range(self.osgviligwp):
            wmdkkxqkw = 13 + i
            toxqhfsju = 61
            frame[toxqhfsju : toxqhfsju + 2, wmdkkxqkw] = dhxmtlewyv if self.osgviligwp - i - 1 < self.current_steps else iisukudgvu
        for bsyrmrqsrq in range(3):
            wmdkkxqkw = 56 + 3 * bsyrmrqsrq
            toxqhfsju = 61
            for x in range(2):
                frame[toxqhfsju : toxqhfsju + 2, wmdkkxqkw + x] = tqogkgimes if self.vjhajnbdzr.aqygnziho > bsyrmrqsrq else iisukudgvu
        return frame


class xajlyftlyn:
    def wgxrzqzazj(self) -> bool:
        return False


class twkzhcfelv(xajlyftlyn):
    qeekhxkoad = 8
    boafatmkhi = 6

    def __init__(self, sprite: Sprite, fjzuynaokm: Set[Tuple[int, int]]) -> None:
        self.fjzuynaokm = fjzuynaokm
        self.sprite = sprite
        self.sprite.set_blocking(BlockingMode.BOUNDING_BOX)
        self.width = self.sprite.width
        self.height = self.sprite.height
        self.start_x = self.sprite.x
        self.start_y = self.sprite.y
        self.dx = 0
        self.dy = 0
        if sprite.name.endswith("t"):
            self.dy = -1
        elif sprite.name.endswith("b"):
            self.dy = 1
        elif sprite.name.endswith("r"):
            self.dx = 1
        elif sprite.name.endswith("l"):
            self.dx = -1
        self.target_x = self.sprite.x
        self.target_y = self.sprite.y
        self.is_pushing = False
        self.aqxtoxeino: Optional[Sprite] = None
        self._anim_elapsed = 0
        self._anim_duration = 1
        self._anim_from_x = float(self.sprite.x)
        self._anim_from_y = float(self.sprite.y)
        self._anim_to_x = float(self.sprite.x)
        self._anim_to_y = float(self.sprite.y)
        self._carry_x = 0.0
        self._carry_y = 0.0

    def ullzqnksoj(self, aqxtoxeino: Sprite) -> int:
        wall_cx, wall_cy = (self.sprite.x + 1 * self.dx, self.sprite.y + 1 * self.dy)
        xwjnqmqiaz = None
        for acdeadlbzx in range(1, 12):
            nskortmtde = wall_cx + self.dx * self.width * acdeadlbzx
            wsotwbexvh = wall_cy + self.dy * self.height * acdeadlbzx
            if (nskortmtde, wsotwbexvh) in self.fjzuynaokm:
                xwjnqmqiaz = acdeadlbzx
                break
        if xwjnqmqiaz is None:
            return 0
        return max(0, xwjnqmqiaz - 1)

    def mfnyvivrar(self, dxegqdlzda: float) -> float:
        if dxegqdlzda < 0.5:
            return 4 * dxegqdlzda * dxegqdlzda * dxegqdlzda
        return 1 - (-2 * dxegqdlzda + 2) ** 3 / 2

    def monctmxmpp(self, dutvzjyvok: int, xxnitqxuds: int, ilzothrych: int) -> None:
        self._anim_elapsed = 0
        self._anim_duration = max(1, int(ilzothrych))
        self._anim_from_x = float(self.sprite.x)
        self._anim_from_y = float(self.sprite.y)
        self._anim_to_x = float(dutvzjyvok)
        self._anim_to_y = float(xxnitqxuds)
        self._carry_x = 0.0
        self._carry_y = 0.0

    def qeoitwygzm(self, srkcilioyp: bool) -> bool:
        if self._anim_elapsed >= self._anim_duration:
            dx = int(round(self._anim_to_x - self.sprite.x))
            dy = int(round(self._anim_to_y - self.sprite.y))
            if dx or dy:
                self.sprite.move(dx, dy)
                if srkcilioyp and self.aqxtoxeino is not None:
                    self.aqxtoxeino.move(dx, dy)
            return False
        self._anim_elapsed += 1
        dxegqdlzda = self._anim_elapsed / self._anim_duration
        hpaysqkbgh = self.mfnyvivrar(dxegqdlzda)
        enzdcdjnzt = self._anim_from_x + (self._anim_to_x - self._anim_from_x) * hpaysqkbgh
        kyaecjvpph = self._anim_from_y + (self._anim_to_y - self._anim_from_y) * hpaysqkbgh
        kdsuujxuag = enzdcdjnzt - float(self.sprite.x) + self._carry_x
        sihdbliheu = kyaecjvpph - float(self.sprite.y) + self._carry_y
        vzkxmdfnba = int(kdsuujxuag)
        acjrijfisx = int(sihdbliheu)
        self._carry_x = kdsuujxuag - vzkxmdfnba
        self._carry_y = sihdbliheu - acjrijfisx
        if vzkxmdfnba or acjrijfisx:
            self.sprite.move(vzkxmdfnba, acjrijfisx)
            if srkcilioyp and self.aqxtoxeino is not None:
                self.aqxtoxeino.move(vzkxmdfnba, acjrijfisx)
        return True

    def prpxgfxlcm(self, aqxtoxeino: Sprite) -> bool:
        if not self.sprite.collides_with(aqxtoxeino):
            return False
        gguyvrkohc = self.ullzqnksoj(aqxtoxeino)
        if gguyvrkohc <= 0:
            return False
        self.aqxtoxeino = aqxtoxeino
        self.is_pushing = True
        self.target_x = self.start_x + self.dx * self.width * gguyvrkohc
        self.target_y = self.start_y + self.dy * self.height * gguyvrkohc
        self.monctmxmpp(self.target_x, self.target_y, self.qeekhxkoad)
        return True

    def wgxrzqzazj(self) -> bool:
        if self.is_pushing:
            if self.qeoitwygzm(srkcilioyp=True):
                return True
            self.target_x = self.start_x
            self.target_y = self.start_y
            self.is_pushing = False
            self.monctmxmpp(self.target_x, self.target_y, self.boafatmkhi)
            return True
        return self.qeoitwygzm(srkcilioyp=False)


class dboxixicic:
    def __init__(self, oypxsalqjo: Sprite, sprite: Sprite, pawjyrnadt: int = 5) -> None:
        self.bfdcztirdu = oypxsalqjo
        self._sprite = sprite
        self._cell = pawjyrnadt
        self._start_x = sprite.x
        self._start_y = sprite.y
        self._dir = 0
        self._undo_x: Optional[int] = None
        self._undo_y: Optional[int] = None
        self._undo_dir: Optional[int] = None

    def bkuguqrpvq(self) -> None:
        self._dir = 0
        self._sprite.set_position(self._start_x, self._start_y)
        self._undo_x = None
        self._undo_y = None
        self._undo_dir = None

    def qrttfzbifu(self) -> None:
        self._dir = (self._dir + 2) % 4

    def npdjlrkhsg(self) -> Tuple[int, int]:
        if not self.bfdcztirdu:
            return (0, 0)
        msmljuaejl = (
            self._dir,
            (self._dir - 1) % 4,
            (self._dir + 1) % 4,
            (self._dir + 2) % 4,
        )
        for acdeadlbzx in msmljuaejl:
            dx, dy = self.nakogfhyus(acdeadlbzx)
            rbaqncskoi = self._sprite.x + dx * self._cell
            uodlwwyprt = self._sprite.y + dy * self._cell
            if self.iiosonyanc(rbaqncskoi, uodlwwyprt):
                self._dir = acdeadlbzx
                return (dx, dy)
        return (0, 0)

    def step(self) -> bool:
        folqexnjmf = self._sprite.x
        yxlpsejtoh = self._sprite.y
        wsdeleuewc = self._dir
        dx, dy = self.npdjlrkhsg()
        if dx == 0 and dy == 0:
            self._undo_x = None
            self._undo_y = None
            self._undo_dir = None
            return False
        self._undo_x = folqexnjmf
        self._undo_y = yxlpsejtoh
        self._undo_dir = wsdeleuewc
        self._sprite.set_position(folqexnjmf + dx * self._cell, yxlpsejtoh + dy * self._cell)
        return True

    def fwtnsrvkrz(self) -> bool:
        if self._undo_x is None or self._undo_y is None or self._undo_dir is None:
            return False
        self._sprite.set_position(self._undo_x, self._undo_y)
        self._dir = self._undo_dir
        self._undo_x = None
        self._undo_y = None
        self._undo_dir = None
        return True

    def iiosonyanc(self, x: int, y: int) -> bool:
        if not self.bfdcztirdu:
            return False
        return self.vtfcqjvbeo(x, y) and self.uczkzlpcwg(x, y) >= 0

    def vtfcqjvbeo(self, x: int, y: int) -> bool:
        return x >= self.bfdcztirdu.x and y >= self.bfdcztirdu.y and (x < self.bfdcztirdu.x + self.bfdcztirdu.width) and (y < self.bfdcztirdu.y + self.bfdcztirdu.height)

    def uczkzlpcwg(self, x: int, y: int) -> int:
        akcoyirktv = x - self.bfdcztirdu.x
        cgpwxobidt = y - self.bfdcztirdu.y
        if akcoyirktv < 0 or akcoyirktv >= self.bfdcztirdu.width or cgpwxobidt < 0 or (cgpwxobidt >= self.bfdcztirdu.height):
            return -1
        return int(self.bfdcztirdu.pixels[cgpwxobidt, akcoyirktv])

    def nakogfhyus(self, acdeadlbzx: int) -> Tuple[int, int]:
        if acdeadlbzx == 0:
            return (0, 1)
        if acdeadlbzx == 1:
            return (1, 0)
        if acdeadlbzx == 2:
            return (0, -1)
        return (-1, 0)


class Vp15(ARCBaseGame):
    def __init__(self) -> None:
        shumwqpzsq = levels[0].get_data("StepCounter") if levels else 0
        osgviligwp = shumwqpzsq if shumwqpzsq else 0
        self._step_counter_ui = hbuhvkxlhc(self, osgviligwp)
        self.ijessuuig = []
        self.tnkekoeuk = [epqvqkpffo, jninpsotet, bejggpjowv, tqogkgimes]
        self.dhksvilbb = [0, 90, 180, 270]
        self.ijessuuig.append(sprites["gngifvjddu"])
        self.ijessuuig.append(sprites["fywfjzkxlm"])
        self.ijessuuig.append(sprites["mkfbgalsbe"])
        self.ijessuuig.append(sprites["nnjhdcanjk"])
        self.ijessuuig.append(sprites["grcpfuizfp"])
        self.ijessuuig.append(sprites["ubspnhafvq"])
        self.oeuabekjf = False
        xngzmcbxu = Camera(
            width=16,
            height=16,
            background=BACKGROUND_COLOR,
            letter_box=PADDING_COLOR,
            interfaces=[self._step_counter_ui],
        )
        super().__init__(game_id="vp15", levels=levels, camera=xngzmcbxu, available_actions=[1, 2, 3, 4])
        self.wbcenorpju()

    def wbcenorpju(self) -> None:
        """."""
        hgkhqetaxy = self.current_level.get_data("StepsDecrement")
        efipnixsvl = 2 if hgkhqetaxy is None else hgkhqetaxy
        self._step_counter_ui.vytykscvhe(efipnixsvl)
        rnaomksehd = self.current_level.get_data("StepCounter")
        if rnaomksehd:
            self._step_counter_ui.osgviligwp = rnaomksehd
            self._step_counter_ui.nzukewekzr()

    def on_set_level(self, level: Level) -> None:
        """."""
        self._levels[self._current_level_index] = self._clean_levels[self._current_level_index].clone()
        self.gudziatsk = self.current_level.get_sprites_by_tag("sfqyzhzkij")[0]
        self.gudziatsk.set_blocking(BlockingMode.BOUNDING_BOX)
        self.gisrhqpee = self.gudziatsk.width
        self.tbwnoxqgc = self.gudziatsk.height
        self.htkmubhry = self.current_level.get_sprites_by_tag("wgmbtyhvbc")[0]
        self.htkmubhry_2 = self.current_level.get_sprites_by_tag("eqatonpohu")[0]
        self.tsynhckng = self.current_level.get_sprites_by_tag("ghizzeqtoh")[0]
        self.srgbthxut = self.current_level.get_sprites_by_tag("kvynsvxbpi")
        self.plrpelhym = self.current_level.get_sprites_by_tag("rjlbuycveu")
        self.lvrnuajbl = [False] * len(self.srgbthxut)
        self.fwckfzsyc = 0
        self.hiaauhahz = 0
        self.cklxociuu = 0
        self.wbcenorpju()
        ezhluetmc = self.current_level.grid_size
        if ezhluetmc is not None:
            self.drtdqwdbc = ezhluetmc[0]
            self.qlgmdayuo = ezhluetmc[1]
        self.ehwheiwsk = []
        self.yjdexjsoa = []
        self.oeuabekjf = self.current_level.get_data("Fog")
        self.ldxlnycps = self.current_level.get_data("kvynsvxbpi")
        if isinstance(self.ldxlnycps, int):
            self.ldxlnycps = [self.ldxlnycps]
        ldgzgjdsrf = self.current_level.get_data("GoalRotation")
        if isinstance(ldgzgjdsrf, int):
            ldgzgjdsrf = [ldgzgjdsrf]
        lbgtuaplev = self.current_level.get_data("GoalColor")
        if isinstance(lbgtuaplev, int):
            lbgtuaplev = [lbgtuaplev]
        for dinyecvyq in range(len(self.plrpelhym)):
            self.ehwheiwsk.append(self.dhksvilbb.index(ldgzgjdsrf[dinyecvyq]))
            self.yjdexjsoa.append(self.tnkekoeuk.index(lbgtuaplev[dinyecvyq]))
            self.srgbthxut[dinyecvyq].pixels = self.ijessuuig[self.ldxlnycps[dinyecvyq]].pixels.copy()
            self.srgbthxut[dinyecvyq].color_remap(epeqflmtfc, self.tnkekoeuk[self.yjdexjsoa[dinyecvyq]])
            self.srgbthxut[dinyecvyq].set_rotation(self.dhksvilbb[self.ehwheiwsk[dinyecvyq]])
        self.qetwzqzzik()
        self.aqdxgoyvu = sprites["sqpmiygfvh"].clone()
        self.current_level.add_sprite(self.aqdxgoyvu)
        self.aqdxgoyvu.set_visible(False)
        self.aqygnziho = 3
        self.ofoahudlo: List[Sprite] = []
        self.byotxmvkt: List[Sprite] = []
        self.alsxlhizr: List[Sprite] = []
        self.ebfuxzbvn = 0
        self.akoadfsur = 0
        self.ltwrkifkx = self.gudziatsk.x
        self.zyoimjaei = self.gudziatsk.y
        self.wsoslqeku: List[dboxixicic] = []
        for uedjpektbg in self.current_level.get_sprites_by_tag("xfmluydglp"):
            for ocajwvfus in ("ttfwljgohq", "soyhouuebz", "rhsxkxzdjz"):
                for hasivfwip in self.current_level.get_sprites_by_tag(ocajwvfus):
                    if uedjpektbg.collides_with(hasivfwip, ignoreMode=True):
                        self.wsoslqeku.append(dboxixicic(uedjpektbg, hasivfwip))
        fjzuynaokm: Set[Tuple[int, int]] = set()
        for qoceexndvw in self.current_level.get_sprites_by_tag("ihdgageizm"):
            fjzuynaokm.add((qoceexndvw.x, qoceexndvw.y))
        for grbudvkafa in self.current_level.get_sprites_by_tag("rjlbuycveu"):
            fjzuynaokm.add((grbudvkafa.x, grbudvkafa.y))
        self.hasivfwip: List[twkzhcfelv] = []
        for ojwauijaoq in self.current_level.get_sprites_by_tag("gbvqrjtaqo"):
            self.hasivfwip.append(twkzhcfelv(ojwauijaoq, fjzuynaokm))
        self.euemavvxz: List[xajlyftlyn] = []
        self._slide = None
        self._tilt = None

    def mrznumynfe(self, zccgflmau: int, qoxqcbqfp: int, xzejejszi: int, eutrvdkbx: int) -> List[Sprite]:
        """."""
        ehiovmywu = self.current_level._sprites
        return [xfemxgpuj for xfemxgpuj in ehiovmywu if xfemxgpuj.x >= zccgflmau and xfemxgpuj.x < zccgflmau + xzejejszi and (xfemxgpuj.y >= qoxqcbqfp) and (xfemxgpuj.y < qoxqcbqfp + eutrvdkbx)]

    def txnfzvzetn(self, juldcpkjse: int, ullicjtklz: int) -> Tuple[bool, bool]:
        ttiyzlpkgh = self.mrznumynfe(juldcpkjse, ullicjtklz, self.gisrhqpee, self.tbwnoxqgc)
        bwdzgjttjp = False
        yubyobdoss = False
        for mvcsnkcqz in ttiyzlpkgh:
            if mvcsnkcqz.tags is None:
                break
            elif "ihdgageizm" in mvcsnkcqz.tags:
                bwdzgjttjp = True
                break
            elif "rjlbuycveu" in mvcsnkcqz.tags:
                wyhfvzxukh = self.plrpelhym.index(mvcsnkcqz)
                if not self.bejndxqqzf(wyhfvzxukh):
                    self.htkmubhry_2.color_remap(None, epeqflmtfc)
                    self.akoadfsur = zoghkczvvt
                    bwdzgjttjp = True
            elif "npxgalaybz" in mvcsnkcqz.tags:
                yubyobdoss = True
                self._step_counter_ui.kbkdzqocik(self._step_counter_ui.osgviligwp)
                self.ofoahudlo.append(mvcsnkcqz)
                self.current_level.remove_sprite(mvcsnkcqz)
            elif "ttfwljgohq" in mvcsnkcqz.tags:
                self.fwckfzsyc = (self.fwckfzsyc + 1) % len(self.ijessuuig)
                self.htkmubhry.pixels = self.ijessuuig[self.fwckfzsyc].pixels.copy()
                self.htkmubhry.color_remap(epeqflmtfc, self.tnkekoeuk[self.hiaauhahz])
                if self.vqfjzzkhid():
                    self.akoadfsur = zoghkczvvt
            elif "soyhouuebz" in mvcsnkcqz.tags:
                lwphyolnjb = (self.hiaauhahz + 1) % len(self.tnkekoeuk)
                self.htkmubhry.color_remap(self.tnkekoeuk[self.hiaauhahz], self.tnkekoeuk[lwphyolnjb])
                self.hiaauhahz = lwphyolnjb
                if self.vqfjzzkhid():
                    self.akoadfsur = zoghkczvvt
            elif "rhsxkxzdjz" in mvcsnkcqz.tags:
                self.cklxociuu = (self.cklxociuu + 1) % 4
                self.htkmubhry.set_rotation(self.dhksvilbb[self.cklxociuu])
                if self.vqfjzzkhid():
                    self.akoadfsur = zoghkczvvt
        return (bwdzgjttjp, yubyobdoss)

    def step(self) -> None:
        if self._slide is None or self.euemavvxz or self.ebfuxzbvn > 0 or self.akoadfsur > 0:
            pass
        else:
            self._slide_frame()
            return
        if self.euemavvxz:
            for i in range(len(self.euemavvxz) - 1, -1, -1):
                kgppvertad = self.euemavvxz[i]
                if not kgppvertad.wgxrzqzazj():
                    del self.euemavvxz[i]
            if not self.euemavvxz:
                self.txnfzvzetn(self.gudziatsk.x, self.gudziatsk.y)
                self.complete_action()
            return
        if self.ebfuxzbvn > 0:
            self.ebfuxzbvn -= 1
            if self.ebfuxzbvn > 0:
                return
            self.aqdxgoyvu.set_visible(False)
            self.htkmubhry.set_visible(True)
            self.complete_action()
            return
        if self.akoadfsur > 0:
            self.akoadfsur -= 1
            if self.akoadfsur > 0:
                return
            self.htkmubhry_2.color_remap(None, avbdwkmqcy)
            self.tsynhckng.set_visible(False)
            for pidqulszaw in self.current_level.get_sprites_by_tag("hoswmpiqkw"):
                pidqulszaw.set_visible(False)
            self.complete_action()
            return
        hnrvmfooc = 0
        feyjbrwyb = 0
        etvjlacrau = False
        if self.action.id == GameAction.ACTION1:
            feyjbrwyb = -1
            etvjlacrau = True
        elif self.action.id == GameAction.ACTION2:
            feyjbrwyb = 1
            etvjlacrau = True
        elif self.action.id == GameAction.ACTION3:
            hnrvmfooc = -1
            etvjlacrau = True
        elif self.action.id == GameAction.ACTION4:
            hnrvmfooc = 1
            etvjlacrau = True
        if not etvjlacrau:
            self.complete_action()
            return
        # vp15: the arrow tilts the world. This frame only shows the tilt (and steps the moving changers once per
        # action, as before); each following frame slides the avatar one cell (see _slide_frame).
        self._slide = {"dx": hnrvmfooc, "dy": feyjbrwyb, "moved": 0, "refilled": False}
        for arilbvrrme in self.wsoslqeku:
            arilbvrrme.step()
        self._tilt = (hnrvmfooc, feyjbrwyb)
        return

    def _on_pusher(self) -> bool:
        for shdkimnqse in self.hasivfwip:
            if shdkimnqse.sprite.collides_with(self.gudziatsk) and shdkimnqse.ullzqnksoj(self.gudziatsk) > 0:
                return True
        return False

    def _on_unopened_lock(self) -> bool:
        for i, lk in enumerate(self.plrpelhym):
            if not self.lvrnuajbl[i] and lk.x == self.gudziatsk.x and lk.y == self.gudziatsk.y:
                return True
        return False

    def _slide_frame(self) -> None:
        """One cell of the slide: the cell's events apply in order, exactly as a single step used to apply them."""
        s = self._slide
        if s["moved"] >= _SLIDE_MAX:
            self._slide_end(False)
            return
        juldcpkjse = self.gudziatsk.x + s["dx"] * self.gisrhqpee
        ullicjtklz = self.gudziatsk.y + s["dy"] * self.tbwnoxqgc
        bwdzgjttjp, yubyobdoss = self.txnfzvzetn(juldcpkjse, ullicjtklz)
        if bwdzgjttjp:
            self._slide_end(True)  # wall, edge or a closed lock: the avatar stays in the cell before it
            return
        self.gudziatsk.set_position(juldcpkjse, ullicjtklz)
        s["moved"] += 1
        s["refilled"] = s["refilled"] or yubyobdoss
        # a hint flash, a pusher cell or a lock the key opens ends the slide on this cell
        if self.akoadfsur or self._on_pusher() or self._on_unopened_lock():
            self._slide_end(False)

    def _slide_end(self, blocked: bool) -> None:
        s = self._slide
        self._slide = None
        self._tilt = None  # the last frame of the slide: the board settles back
        if blocked and s["moved"] == 0:
            for arilbvrrme in self.wsoslqeku:
                arilbvrrme.fwtnsrvkrz()  # a refused slide does not advance the tracks, as a refused step did not
        if self.akoadfsur:
            return  # flash frames count down in step() and then complete the action; not charged, as before
        self._finish_move(s["refilled"])

    def _finish_move(self, yubyobdoss: bool) -> None:
        """The per-move tail of the control copy: charge the bar, pusher throw, win check, life loss. Once per action."""
        bkuguqrpvq = not yubyobdoss and (not self._step_counter_ui.mfyzdfvxsm())
        if not bkuguqrpvq:
            for shdkimnqse in self.hasivfwip:
                if shdkimnqse.prpxgfxlcm(self.gudziatsk):
                    self.euemavvxz.append(shdkimnqse)
                    return
        if self.pbznecvnfr():
            self.next_level()
            self.complete_action()
            return
        if bkuguqrpvq:
            self.aqygnziho -= 1
            if self.aqygnziho == 0:
                self.lose()
                self.complete_action()
                return
            self.aqdxgoyvu.set_visible(True)
            self.aqdxgoyvu.set_scale(64)
            self.aqdxgoyvu.set_position(0, 0)
            self.htkmubhry.set_visible(False)
            self.ebfuxzbvn = xvzyzqolqz
            self.lvrnuajbl = [False] * len(self.plrpelhym)
            self.gudziatsk.set_position(self.ltwrkifkx, self.zyoimjaei)
            self.qetwzqzzik()
            for iybkldaxol in self.ofoahudlo:
                self.current_level.add_sprite(iybkldaxol)
            for spssohsnbq in self.byotxmvkt:
                self.current_level.add_sprite(spssohsnbq)
            for lztoedneuu in self.alsxlhizr:
                self.current_level.add_sprite(lztoedneuu)
            self.ofoahudlo = []
            self.byotxmvkt = []
            self.alsxlhizr = []
            self._step_counter_ui.kbkdzqocik(self._step_counter_ui.osgviligwp)
            self.tsynhckng.set_visible(False)
            for pidqulszaw in self.current_level.get_sprites_by_tag("hoswmpiqkw"):
                pidqulszaw.set_visible(False)
            for opdsmckaqo in self.current_level.get_sprites_by_tag("vjotnebuqo"):
                opdsmckaqo.set_visible(True)
            for arilbvrrme in self.wsoslqeku:
                arilbvrrme.bkuguqrpvq()
            return
        self.complete_action()

    def qetwzqzzik(self) -> None:
        self.cklxociuu = self.dhksvilbb.index(self.current_level.get_data("StartRotation"))
        self.hiaauhahz = self.tnkekoeuk.index(self.current_level.get_data("StartColor"))
        self.fwckfzsyc = self.current_level.get_data("StartShape")
        self.htkmubhry.pixels = self.ijessuuig[self.fwckfzsyc].pixels.copy()
        self.htkmubhry.color_remap(epeqflmtfc, self.tnkekoeuk[self.hiaauhahz])
        self.htkmubhry.set_rotation(self.dhksvilbb[self.cklxociuu])

    def vqfjzzkhid(self) -> bool:
        if self.level_index > 0:
            return False
        uhftkonsvn = False
        for wyhfvzxukh, spssohsnbq in enumerate(self.plrpelhym):
            pidqulszaw = self.current_level.get_sprite_at(spssohsnbq.x - 1, spssohsnbq.y - 1, "hoswmpiqkw")
            if self.bejndxqqzf(wyhfvzxukh) and (not self.lvrnuajbl[wyhfvzxukh]):
                uhftkonsvn = True
                if pidqulszaw:
                    pidqulszaw.set_visible(True)
            elif pidqulszaw:
                pidqulszaw.set_visible(False)
        self.tsynhckng.set_visible(uhftkonsvn)
        return uhftkonsvn

    def bejndxqqzf(self, wyhfvzxukh: int) -> bool:
        return self.fwckfzsyc == self.ldxlnycps[wyhfvzxukh] and self.hiaauhahz == self.yjdexjsoa[wyhfvzxukh] and (self.cklxociuu == self.ehwheiwsk[wyhfvzxukh])

    def pbznecvnfr(self) -> bool:
        for i, spssohsnbq in enumerate(self.plrpelhym):
            if not self.lvrnuajbl[i] and self.gudziatsk.x == spssohsnbq.x and (self.gudziatsk.y == spssohsnbq.y) and self.bejndxqqzf(i):
                self.lvrnuajbl[i] = True
                self.byotxmvkt.append(self.plrpelhym[i])
                self.alsxlhizr.append(self.srgbthxut[i])
                self.current_level.remove_sprite(self.plrpelhym[i])
                self.current_level.remove_sprite(self.srgbthxut[i])
                opdsmckaqo = self.current_level.get_sprite_at(spssohsnbq.x - 1, spssohsnbq.y - 1, "vjotnebuqo")
                if opdsmckaqo and "vfkkzdgxzx" in opdsmckaqo.tags:
                    opdsmckaqo.set_visible(False)
                    pidqulszaw = self.current_level.get_sprite_at(spssohsnbq.x - 1, spssohsnbq.y - 1, "hoswmpiqkw")
                    if pidqulszaw:
                        pidqulszaw.set_visible(False)
                    self.tsynhckng.set_visible(False)
        for i in range(len(self.lvrnuajbl)):
            if not self.lvrnuajbl[i]:
                return False
        return True


# -- copy layer: colours and view (mirrored left-right) ----------------------------------------------------
# The finished frame is recoloured and then shown mirrored left-right. It is done in the camera, so every
# redraw (each action, Undo, a level jump) shows it. The game itself still reads its own,
# untouched board: get_pixels uses the raw render. Input is turned back before the game reads it.
import numpy as _vx_np  # noqa: E402
from arcengine import ActionInput as _VxActionInput, GameAction as _VxGameAction  # noqa: E402

_VX_PALETTE = _vx_np.array([1, 11, 2, 5, 13, 0, 4, 10, 15, 12, 7, 8, 9, 6, 3, 14], dtype=_vx_np.int64)
_VX_ARROW = {3: 4, 4: 3}


def _vx_show(frame):
    a = _vx_np.asarray(frame)
    out = a.copy()
    m = (a >= 0) & (a <= 15)
    out[m] = _VX_PALETTE[a[m].astype(_vx_np.int64)]
    return _vx_np.ascontiguousarray(out[:, ::-1]).astype(a.dtype)


def _vx_unview(x, y):
    return 63 - x, y


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


Vp15.camera = property(lambda self: _vx_cam(self._camera))
_vx_perform = Vp15.perform_action


def _vx_perform_action(self, action_input, raw=False):
    aid = action_input.id.value if hasattr(action_input.id, "value") else int(action_input.id)
    if aid in _VX_ARROW:
        action_input = _VxActionInput(id=_VxGameAction.from_id(_VX_ARROW[aid]), data=action_input.data)
    elif aid == 6 and action_input.data and "x" in action_input.data:
        d = dict(action_input.data)
        d["x"], d["y"] = _vx_unview(int(d["x"]), int(d["y"]))
        action_input = _VxActionInput(id=action_input.id, data=d)
    return _vx_perform(self, action_input, raw)


Vp15.perform_action = _vx_perform_action
