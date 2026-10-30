# Author: Claude Sonnet 5.5 High
# Date: 15-October-2026
# PURPOSE: vh17, the glow-up of vh07 (a recoloured, diagonally mirrored copy of a public tile-and-card puzzle): the
#   shown board is two panels, left and right, and only the live panel takes clicks. ACTION3 makes the left panel
#   live, ACTION4 the right; the live panel wears a one-pixel yellow frame, the other a maroon one; a click in the
#   dead panel is refused (its frame flashes pink, nothing changes, no step is spent). Colours: no shown grey or
#   black for anything the player reads. Boss note 15-Oct-2026: "black, dark gray and gray are always problematic,
#   change them; add one mechanic on level one, e.g. actions one to four pick the left or right panel".
# SRP/DRY check: Pass -- the panel rule and its frames live only in the copy layer at the bottom (the game's own
#   rule code is untouched except available_actions); level text is written by build_vh.py.
# CHANGELOG
#   15-Oct-2026 Claude Sonnet 5.5 High: panels, ACTION3/ACTION4 (available_actions [3, 4, 6]); the old arrow
#     remapping of the copy layer is gone (the game has no arrow actions).
#   15-Oct-2026 Claude Sonnet 5.5 High: new palette (no shown grey; the empty board is the allowed black).
#   15-Oct-2026 Claude Sonnet 5.5 High: new level 1, a row of three tiles and two cards laid across both panels, so
#     the left tile cannot be pressed until ACTION3. Its budget is 200 (the vetting gate refuses a level one that
#     random play can run dry).
#   15-Oct-2026 Claude Sonnet 5.5 High: a seventh level (Son's ft09 generator, seed 17) because the vetting gate
#     wants 7-12 levels and the control copy has 6. Levels 2-6 are the control copy's, with both panels in use.
# vh17: single-file ARC-AGI-3 game (colours changed; the screen is shown mirrored on the diagonal).
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

sprites = {
    "AcT": Sprite(
        pixels=[
            [12, 12],
            [12, 12],
        ],
        name="AcT",
        visible=True,
        collidable=True,
    ),
    "aIV": Sprite(
        pixels=[
            [0, 14],
            [0, 0],
        ],
        name="aIV",
        visible=True,
        collidable=True,
    ),
    "ajm": Sprite(
        pixels=[
            [2, 2, 0],
            [2, 15, 2],
            [2, 2, 2],
        ],
        name="ajm",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "aPM": Sprite(
        pixels=[
            [3, 3, 3],
            [3, 11, 0],
            [3, 0, 2],
        ],
        name="aPM",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "APy": Sprite(
        pixels=[
            [2, 0, 0],
            [0, 8, 2],
            [2, 0, 2],
        ],
        name="APy",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "AQG": Sprite(
        pixels=[
            [0, 3, 3],
            [2, 15, 3],
            [0, 2, 0],
        ],
        name="AQG",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "aRa": Sprite(
        pixels=[
            [2, 0, 2],
            [2, 9, 2],
            [2, 2, 0],
        ],
        name="aRa",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "ASc": Sprite(
        pixels=[
            [2, 0, 0],
            [3, 14, 2],
            [3, 3, 3],
        ],
        name="ASc",
        visible=True,
        collidable=False,
        tags=["bsT"],
    ),
    "AzN": Sprite(
        pixels=[
            [15, 15],
            [15, 15],
        ],
        name="AzN",
        visible=True,
        collidable=True,
    ),
    "Bbi": Sprite(
        pixels=[
            [3, 0, 3],
            [2, 11, 2],
            [3, 0, 3],
        ],
        name="Bbi",
        visible=True,
        collidable=False,
        tags=["bsT"],
    ),
    "bdj": Sprite(
        pixels=[
            [12, 12],
            [12, 12],
        ],
        name="bdj",
        visible=True,
        collidable=True,
    ),
    "bqV": Sprite(
        pixels=[
            [0, -1, 0, -1, 0],
        ],
        name="bqV",
        visible=True,
        collidable=True,
    ),
    "BvX": Sprite(
        pixels=[
            [2, 0, 2],
            [3, 14, 0],
            [3, 3, 3],
        ],
        name="BvX",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "bzH": Sprite(
        pixels=[
            [-1, -1, 6, -1, -1],
            [-1, -1, -1, -1, -1],
            [6, -1, -1, -1, 6],
            [-1, -1, -1, -1, -1],
            [-1, -1, 6, -1, -1],
            [-1, -1, -1, -1, -1],
            [6, -1, -1, -1, 6],
            [-1, -1, -1, -1, -1],
            [-1, -1, 6, -1, -1],
        ],
        name="bzH",
        visible=True,
        collidable=True,
    ),
    "cgN": Sprite(
        pixels=[
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        ],
        name="cgN",
        visible=True,
        collidable=False,
        layer=-2,
    ),
    "ciC": Sprite(
        pixels=[
            [6, 7, 6],
            [7, 10, 7],
            [6, 7, 6],
        ],
        name="ciC",
        visible=True,
        collidable=True,
        tags=["NTi"],
    ),
    "CKH": Sprite(
        pixels=[
            [3, 0, 2],
            [0, 8, 0],
            [0, 2, 2],
        ],
        name="CKH",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "cWS": Sprite(
        pixels=[
            [2, 2, 2],
            [0, 9, 0],
            [0, 2, 0],
        ],
        name="cWS",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "dhm": Sprite(
        pixels=[
            [6, 6, 6],
            [6, 7, 6],
            [6, 7, 6],
        ],
        name="dhm",
        visible=True,
        collidable=True,
    ),
    "dta": Sprite(
        pixels=[
            [2, 0, 2],
            [0, 12, 2],
            [0, 0, 0],
        ],
        name="dta",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "dvQ": Sprite(
        pixels=[
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        ],
        name="dvQ",
        visible=True,
        collidable=False,
        layer=-2,
    ),
    "dwp": Sprite(
        pixels=[
            [3, 3, 3],
            [0, 10, 3],
            [0, 0, 3],
        ],
        name="dwp",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "DYr": Sprite(
        pixels=[
            [2],
            [2],
        ],
        name="DYr",
        visible=True,
        collidable=True,
    ),
    "EEB": Sprite(
        pixels=[
            [8, 8],
            [8, 8],
            [9, 9],
            [9, 9],
        ],
        name="EEB",
        visible=True,
        collidable=True,
    ),
    "Eev": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 2, 2],
            [2, 2, 2],
        ],
        name="Eev",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "ejV": Sprite(
        pixels=[
            [8, 8],
            [8, 8],
        ],
        name="ejV",
        visible=True,
        collidable=True,
    ),
    "EQX": Sprite(
        pixels=[
            [0, 2, 0],
            [2, 12, 2],
            [0, 0, 2],
        ],
        name="EQX",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "ewB": Sprite(
        pixels=[
            [6, 6, 6],
            [6, 7, 6],
            [6, 6, 6],
        ],
        name="ewB",
        visible=True,
        collidable=True,
    ),
    "ewH": Sprite(
        pixels=[
            [6, 7, 6],
            [7, 7, 7],
            [6, 7, 6],
        ],
        name="ewH",
        visible=True,
        collidable=True,
    ),
    "Ewx": Sprite(
        pixels=[
            [2, 0, 2],
            [0, 8, 0],
            [2, 0, 2],
        ],
        name="Ewx",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "fBi": Sprite(
        pixels=[
            [8, 8],
            [8, 8],
            [12, 12],
            [12, 12],
        ],
        name="fBi",
        visible=True,
        collidable=True,
    ),
    "FfJ": Sprite(
        pixels=[
            [3, 0, 0],
            [3, 12, 0],
            [3, 0, 2],
        ],
        name="FfJ",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "fjN": Sprite(
        pixels=[
            [0, 0, 0],
            [2, 8, 2],
            [2, 2, 2],
        ],
        name="fjN",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "FLH": Sprite(
        pixels=[
            [2, 2, 2],
            [0, 15, 3],
            [3, 3, 3],
        ],
        name="FLH",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "fPj": Sprite(
        pixels=[
            [0, 2, 0],
            [2, 14, 2],
            [0, 3, 0],
        ],
        name="fPj",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "Fpw": Sprite(
        pixels=[
            [6, 7, 6],
            [7, 7, 7],
            [6, 7, 6],
        ],
        name="Fpw",
        visible=True,
        collidable=True,
    ),
    "FRs": Sprite(
        pixels=[
            [3, 2, 2],
            [0, 11, 0],
            [3, 2, 3],
        ],
        name="FRs",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "fsp": Sprite(
        pixels=[
            [7, 7, 6],
            [7, 10, 7],
            [6, 7, 7],
        ],
        name="fsp",
        visible=True,
        collidable=True,
        tags=["NTi", "gOi"],
    ),
    "fTG": Sprite(
        pixels=[
            [6, 6, 6],
            [7, 6, 7],
            [6, 6, 6],
        ],
        name="fTG",
        visible=True,
        collidable=True,
    ),
    "FvN": Sprite(
        pixels=[
            [3, 0, 0],
            [2, 9, 2],
            [3, 0, 0],
        ],
        name="FvN",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "gdG": Sprite(
        pixels=[
            [0, 2, 2],
            [2, 8, 2],
            [2, 2, 2],
        ],
        name="gdG",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "gFd": Sprite(
        pixels=[
            [14, 14],
            [14, 14],
        ],
        name="gFd",
        visible=True,
        collidable=True,
    ),
    "guB": Sprite(
        pixels=[
            [3, 2, 3],
            [0, 11, 0],
            [3, 2, 3],
        ],
        name="guB",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "gYF": Sprite(
        pixels=[
            [12, 12],
            [12, 12],
        ],
        name="gYF",
        visible=True,
        collidable=True,
    ),
    "GYn": Sprite(
        pixels=[
            [0, 2, 2],
            [2, 9, 2],
            [0, 2, 2],
        ],
        name="GYn",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "hGV": Sprite(
        pixels=[
            [3, 3, 2],
            [3, 12, 0],
            [2, 0, 2],
        ],
        name="hGV",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "hIX": Sprite(
        pixels=[
            [0, 0, 0],
            [3, 14, 0],
            [3, 3, 3],
        ],
        name="hIX",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "Hkx": Sprite(
        pixels=[
            [9, 9, 9],
            [9, 9, 9],
            [9, 9, 9],
        ],
        name="Hkx",
        visible=True,
        collidable=True,
        tags=["Hkx", "gOi"],
    ),
    "htK": Sprite(
        pixels=[
            [8, 8],
            [8, 8],
        ],
        name="htK",
        visible=True,
        collidable=True,
    ),
    "IFI": Sprite(
        pixels=[
            [3, 2, 0],
            [3, 15, 2],
            [3, 2, 0],
        ],
        name="IFI",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "ImU": Sprite(
        pixels=[
            [6, 7, 7],
            [7, 10, 7],
            [7, 7, 7],
        ],
        name="ImU",
        visible=True,
        collidable=True,
        tags=["NTi", "gOi"],
    ),
    "iSM": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 2, 2],
            [2, 2, 2],
        ],
        name="iSM",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "iTO": Sprite(
        pixels=[
            [6, 6, 6],
            [6, 7, 6],
            [6, 6, 7],
        ],
        name="iTO",
        visible=True,
        collidable=True,
    ),
    "iVf": Sprite(
        pixels=[
            [3, 3, 3],
            [3, 9, 2],
            [3, 0, 2],
        ],
        name="iVf",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "jGI": Sprite(
        pixels=[
            [0, 2, 2],
            [0, 12, 0],
            [0, 2, 0],
        ],
        name="jGI",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "Jir": Sprite(
        pixels=[
            [9, 9],
            [9, 9],
        ],
        name="Jir",
        visible=True,
        collidable=True,
    ),
    "jqz": Sprite(
        pixels=[
            [2, 0, 0],
            [3, 12, 2],
            [3, 3, 3],
        ],
        name="jqz",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "jRD": Sprite(
        pixels=[
            [3, 2, 3],
            [0, 11, 0],
            [3, 2, 3],
        ],
        name="jRD",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "jsT": Sprite(
        pixels=[
            [14, 14],
            [14, 14],
        ],
        name="jsT",
        visible=True,
        collidable=True,
    ),
    "KBg": Sprite(
        pixels=[
            [2, 2, 3],
            [0, 8, 0],
            [2, 2, 3],
        ],
        name="KBg",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "kEq": Sprite(
        pixels=[
            [0, 0, 2],
            [2, 9, 2],
            [2, 2, 2],
        ],
        name="kEq",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "kJY": Sprite(
        pixels=[
            [9, 9],
            [9, 9],
        ],
        name="kJY",
        visible=True,
        collidable=True,
    ),
    "KOm": Sprite(
        pixels=[
            [2, 0, 3],
            [0, 9, 3],
            [2, 0, 3],
        ],
        name="KOm",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "KpR": Sprite(
        pixels=[
            [3, 0, 3],
            [3, 11, 2],
            [3, 0, 3],
        ],
        name="KpR",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "KrW": Sprite(
        pixels=[
            [2, 0, 2],
            [2, 12, 2],
            [2, 2, 2],
        ],
        name="KrW",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "kUt": Sprite(
        pixels=[
            [9, 9],
            [9, 9],
        ],
        name="kUt",
        visible=True,
        collidable=True,
    ),
    "kvt": Sprite(
        pixels=[
            [2, 0, 0],
            [0, 14, 0],
            [2, 0, 2],
        ],
        name="kvt",
        visible=True,
        collidable=False,
        tags=["bsT"],
    ),
    "kyg": Sprite(
        pixels=[
            [3, 0, 3],
            [2, 11, 2],
            [3, 0, 3],
        ],
        name="kyg",
        visible=True,
        collidable=False,
        tags=["bsT"],
    ),
    "KYk": Sprite(
        pixels=[
            [0, 0, 0],
            [0, 12, 2],
            [2, 0, 2],
        ],
        name="KYk",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "LDC": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 12, 2],
            [2, 0, 2],
        ],
        name="LDC",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "LfP": Sprite(
        pixels=[
            [2, 0, 2],
            [2, 8, 0],
            [2, 2, 2],
        ],
        name="LfP",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "LgL": Sprite(
        pixels=[
            [12, 12],
            [12, 12],
            [9, 9],
            [9, 9],
        ],
        name="LgL",
        visible=True,
        collidable=True,
    ),
    "LIx": Sprite(
        pixels=[
            [3, 0, 3],
            [0, 11, 2],
            [3, 2, 3],
        ],
        name="LIx",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "lMN": Sprite(
        pixels=[
            [2, 0, 2],
            [2, 12, 2],
            [2, 0, 2],
        ],
        name="lMN",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "LRU": Sprite(
        pixels=[
            [15, 15],
            [15, 15],
        ],
        name="LRU",
        visible=True,
        collidable=True,
    ),
    "Lua": Sprite(
        pixels=[
            [0, 0, 3],
            [2, 14, 3],
            [0, 2, 3],
        ],
        name="Lua",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "lVU": Sprite(
        pixels=[
            [0, -1, 0, -1, 0],
        ],
        name="lVU",
        visible=True,
        collidable=True,
    ),
    "Lzf": Sprite(
        pixels=[
            [2, 2, 0],
            [2, 9, 2],
            [2, 2, 2],
        ],
        name="Lzf",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "MEF": Sprite(
        pixels=[
            [2, 0, 2],
            [0, 8, 0],
            [2, 0, 2],
        ],
        name="MEF",
        visible=True,
        collidable=True,
    ),
    "mnE": Sprite(
        pixels=[
            [3, 3, 3],
            [3, 12, 0],
            [2, 2, 3],
        ],
        name="mnE",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "mrc": Sprite(
        pixels=[
            [2, 0, 2],
            [2, 9, 2],
            [2, 2, 2],
        ],
        name="mrc",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "mTg": Sprite(
        pixels=[
            [2, 0, 0],
            [2, 9, 2],
            [2, 2, 2],
        ],
        name="mTg",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "MTx": Sprite(
        pixels=[
            [8, 8],
            [8, 8],
        ],
        name="MTx",
        visible=True,
        collidable=True,
    ),
    "ndN": Sprite(
        pixels=[
            [2, 0, 2],
            [0, 8, 0],
            [2, 2, 2],
        ],
        name="ndN",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "NGA": Sprite(
        pixels=[
            [3, 3, 3],
            [3, 15, 0],
            [2, 2, 0],
        ],
        name="NGA",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "nGy": Sprite(
        pixels=[
            [12, 12],
            [12, 12],
            [8, 8],
            [8, 8],
        ],
        name="nGy",
        visible=True,
        collidable=True,
    ),
    "nkM": Sprite(
        pixels=[
            [3, 2, 3],
            [2, 11, 2],
            [3, 2, 3],
        ],
        name="nkM",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "Nod": Sprite(
        pixels=[
            [2],
        ],
        name="Nod",
        visible=True,
        collidable=True,
    ),
    "NTi": Sprite(
        pixels=[
            [7, 6, 7],
            [6, 10, 6],
            [7, 6, 7],
        ],
        name="NTi",
        visible=True,
        collidable=True,
        tags=["NTi", "gOi"],
    ),
    "Nul": Sprite(
        pixels=[
            [3, 3, 3],
            [3, 14, 0],
            [3, 0, 2],
        ],
        name="Nul",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "OFC": Sprite(
        pixels=[
            [12, 12],
            [12, 12],
        ],
        name="OFC",
        visible=True,
        collidable=True,
    ),
    "oif": Sprite(
        pixels=[
            [0, 0, 0],
            [3, 10, 3],
            [3, 3, 3],
        ],
        name="oif",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "OqR": Sprite(
        pixels=[
            [2, 0, 3],
            [0, 8, 3],
            [2, 0, 3],
        ],
        name="OqR",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "OZL": Sprite(
        pixels=[
            [0, 2, 0],
            [2, 12, 2],
            [0, 2, 0],
        ],
        name="OZL",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "PjS": Sprite(
        pixels=[
            [2, 0, 2],
            [0, 14, 0],
            [0, 0, 2],
        ],
        name="PjS",
        visible=True,
        collidable=False,
        tags=["bsT"],
    ),
    "PmE": Sprite(
        pixels=[
            [2, 0, 3],
            [0, 14, 3],
            [3, 3, 3],
        ],
        name="PmE",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "PrU": Sprite(
        pixels=[
            [8, 8],
            [8, 8],
        ],
        name="PrU",
        visible=True,
        collidable=True,
    ),
    "PRx": Sprite(
        pixels=[
            [0, 0, 0],
            [0, -1, 0],
            [0, 0, 0],
        ],
        name="PRx",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "pvc": Sprite(
        pixels=[
            [0, 0, 0],
            [0, 8, 0],
            [0, 0, 0],
        ],
        name="pvc",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "QBc": Sprite(
        pixels=[
            [0, 2, 2],
            [2, 9, 2],
            [0, 0, 2],
        ],
        name="QBc",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "QpB": Sprite(
        pixels=[
            [9, 9],
            [9, 9],
        ],
        name="QpB",
        visible=True,
        collidable=True,
    ),
    "qpe": Sprite(
        pixels=[
            [9, 9],
            [9, 9],
        ],
        name="qpe",
        visible=True,
        collidable=True,
    ),
    "qqM": Sprite(
        pixels=[
            [2, 3, 2],
            [0, 14, 0],
            [2, 0, 2],
        ],
        name="qqM",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "qqX": Sprite(
        pixels=[
            [0, 2, 2],
            [0, 8, 0],
            [2, 2, 0],
        ],
        name="qqX",
        visible=True,
        collidable=True,
    ),
    "RBv": Sprite(
        pixels=[
            [0, 0, 2],
            [0, 14, 0],
            [3, 3, 3],
        ],
        name="RBv",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "REY": Sprite(
        pixels=[
            [10, 10],
            [10, 10],
        ],
        name="REY",
        visible=True,
        collidable=True,
    ),
    "RjR": Sprite(
        pixels=[
            [2, 0, 2],
            [0, 9, 2],
            [0, 2, 0],
        ],
        name="RjR",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "rKF": Sprite(
        pixels=[
            [2, 0, 2],
            [2, 8, 2],
            [2, 2, 2],
        ],
        name="rKF",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "rni": Sprite(
        pixels=[
            [-1, -1, -1, -1, 15, -1, -1, -1, 10, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [10, -1, -1, -1, 14, -1, -1, -1, 15, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [15, -1, -1, -1, 10, -1, -1, -1, 14, -1, -1, -1, 15, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, 15, -1, -1, -1, 10, -1, -1, -1, 14, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, 14, -1, -1, -1, 15, -1, -1, -1, 10, -1, -1, -1, 14],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, 14, -1, -1, -1, 15, -1, -1, -1, 10],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, 10, -1, -1, -1, 14, -1, -1, -1, -1],
        ],
        name="rni",
        visible=True,
        collidable=True,
    ),
    "ROc": Sprite(
        pixels=[
            [3, 0, 2],
            [3, 9, 0],
            [3, 3, 3],
        ],
        name="ROc",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "RZR": Sprite(
        pixels=[
            [2],
        ],
        name="RZR",
        visible=True,
        collidable=True,
    ),
    "seE": Sprite(
        pixels=[
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        ],
        name="seE",
        visible=True,
        collidable=False,
    ),
    "SfD": Sprite(
        pixels=[
            [2, 0, 3],
            [0, 14, 3],
            [2, 0, 3],
        ],
        name="SfD",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "SJP": Sprite(
        pixels=[
            [0, 2, 0],
            [0, 8, 2],
            [2, 0, 2],
        ],
        name="SJP",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "sPz": Sprite(
        pixels=[
            [0, 0, 2],
            [2, 8, 2],
            [2, 2, 2],
        ],
        name="sPz",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "srH": Sprite(
        pixels=[
            [3, 0, 3],
            [0, 11, 2],
            [3, 2, 3],
        ],
        name="srH",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "ssK": Sprite(
        pixels=[
            [3, 3, 3],
            [2, 14, 3],
            [0, 0, 2],
        ],
        name="ssK",
        visible=True,
        collidable=False,
        tags=["bsT"],
    ),
    "sTI": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 9, 0],
            [2, 2, 2],
        ],
        name="sTI",
        visible=True,
        collidable=True,
    ),
    "sxj": Sprite(
        pixels=[
            [2, 0, 2],
            [0, 8, 2],
            [2, 0, 0],
        ],
        name="sxj",
        visible=True,
        collidable=True,
    ),
    "SXM": Sprite(
        pixels=[
            [2, 0, 2],
            [2, 8, 0],
            [0, 0, 2],
        ],
        name="SXM",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "tCT": Sprite(
        pixels=[
            [2, 0, 2],
            [0, 9, 2],
            [2, 2, 2],
        ],
        name="tCT",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "TOK": Sprite(
        pixels=[
            [9, 9, 9, -1, 8, 8, 8, -1, 9, 9, 9],
            [9, 9, 9, -1, 8, 8, 8, -1, 9, 9, 9],
            [9, 9, 9, -1, 8, 8, 8, -1, 9, 9, 9],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [8, 8, 8, -1, -1, -1, -1, -1, 8, 8, 8],
            [8, 8, 8, -1, -1, -1, -1, -1, 8, 8, 8],
            [8, 8, 8, -1, -1, -1, -1, -1, 8, 8, 8],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [9, 9, 9, -1, 8, 8, 8, -1, 9, 9, 9],
            [9, 9, 9, -1, 8, 8, 8, -1, 9, 9, 9],
            [9, 9, 9, -1, 8, 8, 8, -1, 9, 9, 9],
        ],
        name="TOK",
        visible=True,
        collidable=False,
    ),
    "TqS": Sprite(
        pixels=[
            [2, -1, 2],
        ],
        name="TqS",
        visible=True,
        collidable=True,
    ),
    "TqV": Sprite(
        pixels=[
            [0, 2, 2],
            [0, 8, 2],
            [2, 2, 2],
        ],
        name="TqV",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "TuS": Sprite(
        pixels=[
            [3, 3, 3],
            [0, 14, 2],
            [0, 0, 0],
        ],
        name="TuS",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "uaD": Sprite(
        pixels=[
            [3, 0, 3],
            [0, 11, 2],
            [3, 2, 3],
        ],
        name="uaD",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "UaS": Sprite(
        pixels=[
            [2, 2, 0],
            [2, 9, 2],
            [2, 0, 0],
        ],
        name="UaS",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "uCD": Sprite(
        pixels=[
            [6],
        ],
        name="uCD",
        visible=True,
        collidable=True,
    ),
    "uCe": Sprite(
        pixels=[
            [0, 2, 2],
            [2, 12, 2],
            [0, 0, 0],
        ],
        name="uCe",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "uDP": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 9, 2],
            [0, 2, 2],
        ],
        name="uDP",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "uds": Sprite(
        pixels=[
            [2, 0, 2],
            [2, 12, 0],
            [2, 0, 2],
        ],
        name="uds",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "UdT": Sprite(
        pixels=[
            [2, 2, 0],
            [2, 8, 2],
            [0, 0, 2],
        ],
        name="UdT",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "UEq": Sprite(
        pixels=[
            [2, 2, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2, 2, 2],
            [2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2],
            [2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2],
            [2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2],
            [2, 2, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2, 2, 2],
        ],
        name="UEq",
        visible=True,
        collidable=False,
        tags=["Ycb"],
    ),
    "UEt": Sprite(
        pixels=[
            [7, 7, 7],
            [6, 7, 6],
            [6, 6, 6],
        ],
        name="UEt",
        visible=True,
        collidable=True,
    ),
    "uJY": Sprite(
        pixels=[
            [5],
        ],
        name="uJY",
        visible=True,
        collidable=True,
    ),
    "ukF": Sprite(
        pixels=[
            [3, 0, 2],
            [2, 12, 0],
            [2, 2, 0],
        ],
        name="ukF",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "ukY": Sprite(
        pixels=[
            [3, 2, 3],
            [0, 11, 0],
            [3, 2, 3],
        ],
        name="ukY",
        visible=True,
        collidable=False,
        tags=["bsT"],
    ),
    "UmB": Sprite(
        pixels=[
            [6, -1, 6],
        ],
        name="UmB",
        visible=True,
        collidable=True,
    ),
    "uPr": Sprite(
        pixels=[
            [11],
        ],
        name="uPr",
        visible=True,
        collidable=True,
    ),
    "UQj": Sprite(
        pixels=[
            [2, 2, 2],
            [0, 8, 2],
            [2, 0, 2],
        ],
        name="UQj",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "UsM": Sprite(
        pixels=[
            [0],
        ],
        name="UsM",
        visible=True,
        collidable=True,
    ),
    "UTh": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 8, 0],
            [2, 2, 0],
        ],
        name="UTh",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "uvy": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 2, 2],
            [2, 2, 2],
        ],
        name="uvy",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "Uxp": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 8, 2],
            [0, 2, 2],
        ],
        name="Uxp",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "vAD": Sprite(
        pixels=[
            [-1, -1, 6, -1, -1],
            [-1, -1, -1, -1, -1],
            [6, -1, -1, -1, 6],
            [-1, -1, -1, -1, -1],
            [-1, -1, 6, -1, -1],
        ],
        name="vAD",
        visible=True,
        collidable=True,
    ),
    "van": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 2, 2],
            [2, 2, 2],
        ],
        name="van",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "VdJ": Sprite(
        pixels=[
            [2, 2, 2],
            [0, 9, 2],
            [2, 2, 0],
        ],
        name="VdJ",
        visible=True,
        collidable=True,
    ),
    "vFj": Sprite(
        pixels=[
            [2, 0, 2],
            [2, 8, 2],
            [0, 2, 2],
        ],
        name="vFj",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "VHA": Sprite(
        pixels=[
            [11, 11],
            [11, 11],
        ],
        name="VHA",
        visible=True,
        collidable=True,
    ),
    "viw": Sprite(
        pixels=[
            [12, 12],
            [12, 12],
        ],
        name="viw",
        visible=True,
        collidable=True,
    ),
    "vSD": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 8, 0],
            [0, 2, 0],
        ],
        name="vSD",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "Vuk": Sprite(
        pixels=[
            [7, 7, 6],
            [7, 10, 7],
            [7, 7, 7],
        ],
        name="Vuk",
        visible=True,
        collidable=True,
        tags=["NTi", "gOi"],
    ),
    "vxk": Sprite(
        pixels=[
            [8, 8, 8, -1, 9, 9, 9, -1, 9, 9, 9],
            [8, 8, 8, -1, 9, 9, 9, -1, 9, 9, 9],
            [8, 8, 8, -1, 9, 9, 9, -1, 9, 9, 9],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [8, 8, 8, -1, -1, -1, -1, -1, 8, 8, 8],
            [8, 8, 8, -1, -1, -1, -1, -1, 8, 8, 8],
            [8, 8, 8, -1, -1, -1, -1, -1, 8, 8, 8],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [9, 9, 9, -1, 9, 9, 9, -1, 8, 8, 8],
            [9, 9, 9, -1, 9, 9, 9, -1, 8, 8, 8],
            [9, 9, 9, -1, 9, 9, 9, -1, 8, 8, 8],
        ],
        name="vxk",
        visible=True,
        collidable=False,
    ),
    "VxQ": Sprite(
        pixels=[
            [7, 7, 7],
            [7, 10, 7],
            [6, 7, 6],
        ],
        name="VxQ",
        visible=True,
        collidable=True,
        tags=["NTi", "gOi"],
    ),
    "wai": Sprite(
        pixels=[
            [0, 2, 2],
            [2, 8, 3],
            [3, 3, 3],
        ],
        name="wai",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "WbH": Sprite(
        pixels=[
            [0, 2, 0],
            [3, 12, 3],
            [0, 3, 0],
        ],
        name="WbH",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "wCl": Sprite(
        pixels=[
            [9, 9, 9, -1, 8, 8, 8, -1, 9, 9, 9],
            [9, 9, 9, -1, 8, 8, 8, -1, 9, 9, 9],
            [9, 9, 9, -1, 8, 8, 8, -1, 9, 9, 9],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [8, 8, 8, -1, -1, -1, -1, -1, 9, 9, 9],
            [8, 8, 8, -1, -1, -1, -1, -1, 9, 9, 9],
            [8, 8, 8, -1, -1, -1, -1, -1, 9, 9, 9],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [9, 9, 9, -1, 8, 8, 8, -1, 8, 8, 8],
            [9, 9, 9, -1, 8, 8, 8, -1, 8, 8, 8],
            [9, 9, 9, -1, 8, 8, 8, -1, 8, 8, 8],
        ],
        name="wCl",
        visible=True,
        collidable=False,
    ),
    "WDx": Sprite(
        pixels=[
            [2, 2, 2],
            [3, 8, 3],
            [3, 3, 3],
        ],
        name="WDx",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "wmW": Sprite(
        pixels=[
            [0, 2, 2],
            [0, 8, 0],
            [0, 2, 2],
        ],
        name="wmW",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "wmz": Sprite(
        pixels=[
            [3, 0, 0],
            [2, 11, 2],
            [3, 3, 2],
        ],
        name="wmz",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "Wnw": Sprite(
        pixels=[
            [9, 9],
            [9, 9],
            [8, 8],
            [8, 8],
        ],
        name="Wnw",
        visible=True,
        collidable=True,
    ),
    "Wpv": Sprite(
        pixels=[
            [3, 2, 2],
            [0, 11, 0],
            [3, 2, 3],
        ],
        name="Wpv",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "WQe": Sprite(
        pixels=[
            [2, 2, 0],
            [2, 9, 2],
            [0, 0, 0],
        ],
        name="WQe",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "xas": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 12, 2],
            [0, 2, 0],
        ],
        name="xas",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "xeV": Sprite(
        pixels=[
            [6, 6, 6],
            [6, 7, 6],
            [6, 6, 6],
        ],
        name="xeV",
        visible=True,
        collidable=True,
    ),
    "xga": Sprite(
        pixels=[
            [3, 2, 3],
            [0, 11, 0],
            [3, 2, 3],
        ],
        name="xga",
        visible=True,
        collidable=False,
        tags=["bsT"],
    ),
    "XND": Sprite(
        pixels=[
            [6, 7, 6],
            [7, 10, 7],
            [7, 7, 7],
        ],
        name="XND",
        visible=True,
        collidable=True,
        tags=["NTi"],
    ),
    "XWQ": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 12, 2],
            [2, 0, 2],
        ],
        name="XWQ",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "Yid": Sprite(
        pixels=[
            [6, 6, 6],
            [7, 7, 7],
            [6, 6, 6],
        ],
        name="Yid",
        visible=True,
        collidable=True,
    ),
    "yKt": Sprite(
        pixels=[
            [3, 0, 3],
            [2, 11, 3],
            [3, 0, 3],
        ],
        name="yKt",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "yUG": Sprite(
        pixels=[
            [3, 2, 3],
            [0, 14, 0],
            [3, 2, 3],
        ],
        name="yUG",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "Ywn": Sprite(
        pixels=[
            [14, 14],
            [14, 14],
            [15, 15],
            [15, 15],
        ],
        name="Ywn",
        visible=True,
        collidable=True,
    ),
    "ywQ": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 9, 2],
            [2, 2, 2],
        ],
        name="ywQ",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "yZg": Sprite(
        pixels=[
            [2, 0, 2],
            [0, 14, 0],
            [2, 0, 2],
        ],
        name="yZg",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "Zgh": Sprite(
        pixels=[
            [11, 11],
            [11, 11],
        ],
        name="Zgh",
        visible=True,
        collidable=True,
    ),
    "zhI": Sprite(
        pixels=[
            [2, 2, 2],
            [2, 9, 2],
            [2, 2, 2],
        ],
        name="zhI",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "zIu": Sprite(
        pixels=[
            [3, 2, 3],
            [0, 11, 0],
            [3, 2, 3],
        ],
        name="zIu",
        visible=True,
        collidable=False,
        tags=["bsT"],
    ),
    "ZkU": Sprite(
        pixels=[
            [7, 6, 7],
            [7, 10, 7],
            [7, 7, 7],
        ],
        name="ZkU",
        visible=True,
        collidable=True,
        tags=["NTi", "gOi"],
    ),
    "zmT": Sprite(
        pixels=[
            [0, 2, 3],
            [2, 12, 3],
            [3, 3, 3],
        ],
        name="zmT",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
    "zoT": Sprite(
        pixels=[
            [6, 7, 7],
            [7, 10, 7],
            [7, 7, 6],
        ],
        name="zoT",
        visible=True,
        collidable=True,
        tags=["NTi", "gOi"],
    ),
    "zvj": Sprite(
        pixels=[
            [2, 0, 0],
            [2, 8, 2],
            [2, 2, 2],
        ],
        name="zvj",
        visible=True,
        collidable=True,
        tags=["bsT"],
    ),
}

levels = [
    # Lv1
    Level(
        sprites=[
            sprites["QpB"].clone().set_position(30, 0),
            sprites["gFd"].clone().set_position(30, 2),
            sprites["gYF"].clone().set_position(30, 4),
            sprites["Hkx"].clone().set_position(15, 8),
            sprites["Hkx"].clone().set_position(15, 16),
            sprites["Hkx"].clone().set_position(15, 24),
            Sprite(pixels=[[3, 0, 3], [3, 14, 3], [3, 2, 3]], name="card0", visible=True, collidable=True, tags=["bsT"], x=15, y=12),
            Sprite(pixels=[[3, 0, 3], [3, 12, 3], [3, 0, 3]], name="card1", visible=True, collidable=True, tags=["bsT"], x=15, y=20),
        ],
        grid_size=(32, 32),
        data={
            "kCv": 200,
            "cwU": [9, 14, 12],
            "elp": [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        },
        name="Lv1",
    ),
    # hxv
    Level(
        sprites=[
            sprites["EQX"].clone().set_position(14, 19),
            sprites["Hkx"].clone().set_position(10, 7),
            sprites["Hkx"].clone().set_position(14, 7),
            sprites["Hkx"].clone().set_position(18, 7),
            sprites["Hkx"].clone().set_position(10, 11),
            sprites["Hkx"].clone().set_position(18, 11),
            sprites["Hkx"].clone().set_position(10, 15),
            sprites["Hkx"].clone().set_position(14, 15),
            sprites["Hkx"].clone().set_position(18, 15),
            sprites["Hkx"].clone().set_position(18, 19),
            sprites["Hkx"].clone().set_position(14, 23),
            sprites["Hkx"].clone().set_position(10, 23),
            sprites["Hkx"].clone().set_position(10, 19),
            sprites["Hkx"].clone().set_position(18, 23),
            sprites["jGI"].clone().set_position(14, 11),
            sprites["qpe"].clone().set_position(30, 0),
            sprites["viw"].clone().set_position(30, 2),
        ],
        grid_size=(32, 32),
        data={
            "kCv": 32,
            "cwU": [9, 12],
            "elp": [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        },
        name="hxv",
    ),
    # Fmh
    Level(
        sprites=[
            sprites["APy"].clone().set_position(18, 14),
            sprites["dta"].clone().set_position(14, 22),
            sprites["fBi"].clone().set_position(30, 0),
            sprites["Hkx"].clone().set_position(10, 2),
            sprites["Hkx"].clone().set_position(10, 6),
            sprites["Hkx"].clone().set_position(10, 10),
            sprites["Hkx"].clone().set_position(14, 10),
            sprites["Hkx"].clone().set_position(14, 14),
            sprites["Hkx"].clone().set_position(18, 10),
            sprites["Hkx"].clone().set_position(18, 6),
            sprites["Hkx"].clone().set_position(22, 10),
            sprites["Hkx"].clone().set_position(18, 2),
            sprites["Hkx"].clone().set_position(14, 2),
            sprites["Hkx"].clone().set_position(6, 14),
            sprites["Hkx"].clone().set_position(6, 10),
            sprites["Hkx"].clone().set_position(10, 18),
            sprites["Hkx"].clone().set_position(6, 18),
            sprites["Hkx"].clone().set_position(14, 18),
            sprites["Hkx"].clone().set_position(18, 18),
            sprites["Hkx"].clone().set_position(22, 18),
            sprites["Hkx"].clone().set_position(22, 14),
            sprites["Hkx"].clone().set_position(10, 22),
            sprites["Hkx"].clone().set_position(18, 22),
            sprites["Hkx"].clone().set_position(14, 26),
            sprites["Hkx"].clone().set_position(10, 26),
            sprites["Hkx"].clone().set_position(18, 26),
            sprites["KYk"].clone().set_position(14, 6),
            sprites["SXM"].clone().set_position(10, 14),
        ],
        grid_size=(32, 32),
        data={
            "kCv": 96,
            "cwU": [8, 12],
            "elp": [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        },
        name="Fmh",
    ),
    # oea
    Level(
        sprites=[
            sprites["aRa"].clone().set_position(18, 11),
            sprites["gYF"].clone().set_position(30, 4),
            sprites["Hkx"].clone().set_position(10, 7),
            sprites["Hkx"].clone().set_position(14, 11),
            sprites["Hkx"].clone().set_position(14, 15),
            sprites["Hkx"].clone().set_position(22, 11),
            sprites["Hkx"].clone().set_position(22, 15),
            sprites["Hkx"].clone().set_position(18, 7),
            sprites["Hkx"].clone().set_position(14, 7),
            sprites["Hkx"].clone().set_position(6, 11),
            sprites["Hkx"].clone().set_position(10, 15),
            sprites["Hkx"].clone().set_position(18, 15),
            sprites["Hkx"].clone().set_position(6, 15),
            sprites["Hkx"].clone().set_position(6, 7),
            sprites["Hkx"].clone().set_position(22, 7),
            sprites["Hkx"].clone().set_position(10, 19),
            sprites["Hkx"].clone().set_position(18, 19),
            sprites["Hkx"].clone().set_position(10, 23),
            sprites["Hkx"].clone().set_position(14, 23),
            sprites["Hkx"].clone().set_position(18, 23),
            sprites["lMN"].clone().set_position(10, 11),
            sprites["PrU"].clone().set_position(30, 2),
            sprites["QpB"].clone().set_position(30, 0),
            sprites["uCe"].clone().set_position(14, 19),
        ],
        grid_size=(32, 32),
        data={
            "kCv": 96,
            "cwU": [9, 8, 12],
            "elp": [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        },
        name="oea",
    ),
    # INW
    Level(
        sprites=[
            sprites["AQG"].clone().set_position(19, 6),
            sprites["fPj"].clone().set_position(11, 18),
            sprites["Hkx"].clone().set_position(7, 6),
            sprites["Hkx"].clone().set_position(15, 18),
            sprites["Hkx"].clone().set_position(15, 6),
            sprites["Hkx"].clone().set_position(11, 10),
            sprites["Hkx"].clone().set_position(11, 2),
            sprites["Hkx"].clone().set_position(23, 14),
            sprites["Hkx"].clone().set_position(15, 10),
            sprites["Hkx"].clone().set_position(19, 18),
            sprites["Hkx"].clone().set_position(23, 22),
            sprites["Hkx"].clone().set_position(15, 22),
            sprites["Hkx"].clone().set_position(19, 26),
            sprites["Hkx"].clone().set_position(15, 26),
            sprites["Hkx"].clone().set_position(23, 18),
            sprites["Hkx"].clone().set_position(19, 10),
            sprites["Hkx"].clone().set_position(7, 10),
            sprites["Hkx"].clone().set_position(15, 2),
            sprites["Hkx"].clone().set_position(7, 18),
            sprites["Hkx"].clone().set_position(7, 22),
            sprites["Hkx"].clone().set_position(7, 26),
            sprites["Hkx"].clone().set_position(11, 26),
            sprites["Hkx"].clone().set_position(7, 14),
            sprites["Hkx"].clone().set_position(3, 10),
            sprites["Hkx"].clone().set_position(3, 18),
            sprites["Hkx"].clone().set_position(15, 14),
            sprites["Hkx"].clone().set_position(23, 10),
            sprites["Hkx"].clone().set_position(27, 18),
            sprites["Hkx"].clone().set_position(27, 10),
            sprites["IFI"].clone().set_position(3, 14),
            sprites["NTi"].clone().set_position(11, 6),
            sprites["NTi"].clone().set_position(19, 22),
            sprites["NTi"].clone().set_position(11, 14),
            sprites["Nul"].clone().set_position(7, 2),
            sprites["PmE"].clone().set_position(23, 26),
            sprites["qqM"].clone().set_position(11, 22),
            sprites["SfD"].clone().set_position(27, 14),
            sprites["Ywn"].clone().set_position(27, 0),
            sprites["yZg"].clone().set_position(19, 14),
        ],
        grid_size=(32, 32),
        data={
            "kCv": 128,
            "cwU": [14, 15],
            "elp": [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        },
        name="INW",
    ),
    # DFx
    Level(
        sprites=[
            sprites["ASc"].clone().set_position(22, 23),
            sprites["gFd"].clone().set_position(30, 2),
            sprites["kvt"].clone().set_position(10, 15),
            sprites["PjS"].clone().set_position(18, 11),
            sprites["ssK"].clone().set_position(6, 3),
            sprites["Zgh"].clone().set_position(30, 0),
            sprites["ZkU"].clone().set_position(6, 7),
            sprites["ZkU"].clone().set_position(10, 7),
            sprites["ZkU"].clone().set_position(14, 7),
            sprites["ZkU"].clone().set_position(18, 7),
            sprites["ZkU"].clone().set_position(22, 7),
            sprites["ZkU"].clone().set_position(6, 11),
            sprites["ZkU"].clone().set_position(22, 11),
            sprites["ZkU"].clone().set_position(10, 11),
            sprites["ZkU"].clone().set_position(14, 11),
            sprites["ZkU"].clone().set_position(18, 15),
            sprites["ZkU"].clone().set_position(6, 15),
            sprites["ZkU"].clone().set_position(22, 15),
            sprites["ZkU"].clone().set_position(14, 15),
            sprites["ZkU"].clone().set_position(18, 19),
            sprites["ZkU"].clone().set_position(6, 19),
            sprites["ZkU"].clone().set_position(22, 19),
            sprites["ZkU"].clone().set_position(10, 19),
            sprites["ZkU"].clone().set_position(14, 19),
            sprites["ZkU"].clone().set_position(26, 19),
            sprites["ZkU"].clone().set_position(2, 7),
            sprites["ZkU"].clone().set_position(2, 3),
            sprites["ZkU"].clone().set_position(26, 23),
        ],
        grid_size=(32, 32),
        data={
            "kCv": 128,
            "cwU": [11, 14],
            "elp": [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        },
        name="DFx",
    ),
    # Gen7
    Level(
        sprites=[
            sprites["LRU"].clone().set_position(30, 0),
            sprites["Zgh"].clone().set_position(30, 2),
            sprites["Hkx"].clone().set_position(2, 22),
            sprites["Hkx"].clone().set_position(6, 18),
            sprites["Hkx"].clone().set_position(6, 26),
            sprites["Hkx"].clone().set_position(10, 18),
            sprites["Hkx"].clone().set_position(10, 22),
            sprites["Hkx"].clone().set_position(10, 26),
            sprites["Hkx"].clone().set_position(14, 2),
            sprites["Hkx"].clone().set_position(14, 6),
            sprites["Hkx"].clone().set_position(14, 10),
            sprites["Hkx"].clone().set_position(14, 18),
            sprites["Hkx"].clone().set_position(14, 22),
            sprites["Hkx"].clone().set_position(14, 26),
            sprites["Hkx"].clone().set_position(18, 2),
            sprites["Hkx"].clone().set_position(18, 10),
            sprites["Hkx"].clone().set_position(18, 18),
            sprites["Hkx"].clone().set_position(18, 26),
            sprites["Hkx"].clone().set_position(22, 2),
            sprites["Hkx"].clone().set_position(22, 6),
            sprites["Hkx"].clone().set_position(22, 10),
            sprites["Hkx"].clone().set_position(22, 18),
            sprites["Hkx"].clone().set_position(22, 22),
            sprites["Hkx"].clone().set_position(22, 26),
            sprites["Hkx"].clone().set_position(26, 2),
            Sprite(pixels=[[3, 2, 2], [2, 15, 2], [3, 2, 0]], name="card0", visible=True, collidable=True, tags=["bsT"], x=6, y=22),
            Sprite(pixels=[[0, 0, 0], [0, 11, 0], [2, 0, 2]], name="card1", visible=True, collidable=True, tags=["bsT"], x=18, y=6),
            Sprite(pixels=[[2, 2, 2], [2, 15, 2], [0, 2, 2]], name="card2", visible=True, collidable=True, tags=["bsT"], x=18, y=22),
            Sprite(pixels=[[2, 0, 3], [2, 15, 3], [0, 3, 3]], name="card3", visible=True, collidable=True, tags=["bsT"], x=26, y=6),
        ],
        grid_size=(32, 32),
        data={
            "kCv": 96,
            "cwU": [15, 11],
            "elp": [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        },
        name="Gen7",
    ),
]

BACKGROUND_COLOR = 4
PADDING_COLOR = 4


class sve(RenderableUserDisplay):
    def __init__(self, sbb: int, vrr: "Vh17"):
        self.oro = sbb
        self.dzy = sbb
        self.vai = vrr

    def cab(self, shl: int) -> None:
        self.dzy = max(0, min(shl, self.oro))

    def lph(self) -> bool:
        if self.dzy > 0:
            self.dzy -= 1
        return self.dzy > 0

    def dsl(self) -> None:
        self.dzy = self.oro

    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        if self.oro == 0:
            return frame

        slC = self.dzy / self.oro
        GoJ = round(64 * slC)
        for x in range(64):
            frame[63, x] = 12 if x < GoJ else 11

        return frame


class Vh17(ARCBaseGame):
    def __init__(self) -> None:
        ZnK = levels[0].get_data("kCv") if levels else 0
        bUg = ZnK if ZnK else 0
        self.lpw = sve(bUg, self)
        super().__init__("vh17", levels, Camera(0, 0, 16, 16, 4, 4, [self.lpw]), available_actions=[3, 4, 6])

    def olv(self) -> None:
        yTL = self.current_level.get_data("kCv")
        if yTL:
            self.lpw.oro = yTL
            self.lpw.dsl()

    def on_set_level(self, level: Level) -> None:
        self.olv()

        self.zth = None
        self.our = 0
        if self.level_index == 0:
            Uev = self.current_level.get_sprites_by_tag("Ycb")
            if Uev:
                self.zth = Uev[0]

        rKu = self.current_level.grid_size
        self.pdw = rKu[0]  # type: ignore
        self.zbh = rKu[1]  # type: ignore

        self.gig = self.current_level.get_sprites_by_tag("bsT")
        self.fhc = self.current_level.get_sprites_by_tag("Hkx")
        self.mou = self.current_level.get_sprites_by_tag("NTi")

        self.gqb = self.current_level.get_data("cwU")
        if self.gqb is None:
            self.gqb = [9, 8]

        self.irw = self.current_level.get_data("elp")

        if self.irw is None:
            self.irw = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]

        for rmy, zge in enumerate(self.fhc):
            zge.color_remap(zge.pixels[0][0], self.gqb[0])

        for rmy, zge in enumerate(self.mou):
            for jon in range(3):
                for vlo in range(3):
                    if zge.pixels[jon][vlo] != 6:
                        zge.pixels[jon][vlo] = self.gqb[0]

    def step(self) -> None:
        if self.action.id.value == 0:
            self.complete_action()
            return

        if self.our > 0 and self.zth:
            self.our -= 1

            aIT = 0 if self.our % 2 == 1 else 2
            Ytt = self.zth.pixels > -1
            self.zth.pixels[Ytt] = aIT
            if self.our == 0:
                self.complete_action()
            return

        kMO = None
        ATn = False
        Hzf = None

        if self.action.id.value == 6:
            AfP = self.action.data.get("x", 0)
            Ywt = self.action.data.get("y", 0)

            Hzf = self.camera.display_to_grid(AfP, Ywt)
            if Hzf:
                ppb, tut = Hzf

                Wmr = self.current_level.get_sprite_at(ppb, tut, "Hkx")
                if not Wmr:
                    Wmr = self.current_level.get_sprite_at(ppb, tut, "NTi")
                    if Wmr:
                        ATn = True
                if Wmr:
                    self.blr = Wmr
                    kMO = 5

        if kMO is None and Hzf is not None:
            uTB = Hzf and self.current_level.get_sprite_at(Hzf[0], Hzf[1], "bsT")
            if self.level_index == 0 and self.zth and not uTB:
                self.our = 4
                return
            self.complete_action()
            return

        GBS = [
            [(-1, -1), (0, -1), (1, -1)],
            [(-1, 0), (0, 0), (1, 0)],
            [(-1, 1), (0, 1), (1, 1)],
        ]

        if ATn:
            eHl = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
            bBi = self.blr.pixels
            for j in range(3):
                for i in range(3):
                    if bBi[j][i] == 6:
                        eHl[j][i] = 1
        else:
            eHl = self.irw

        if kMO == 5:
            for i in range(3):
                for j in range(3):
                    if eHl[j][i] == 1:
                        ybc, lga = GBS[j][i]
                        cAw = (self.blr.x + (ybc * 4), self.blr.y + (lga * 4))

                        RfH = self.current_level.get_sprite_at(cAw[0], cAw[1], "Hkx")

                        if not RfH:
                            RfH = self.current_level.get_sprite_at(cAw[0], cAw[1], "NTi")
                        if RfH:
                            kNa = self.gqb.index(RfH.pixels[1][1])
                            kNa = (kNa + 1) % len(self.gqb)
                            RfH.color_remap(RfH.pixels[1][1], self.gqb[kNa])

        if self.cgj():
            self.next_level()
            self.complete_action()
            return

        if not self.lpw.lph():
            self.lose()

        self.complete_action()

    def cgj(self) -> bool:
        for etf in self.gig:
            nRq = etf.pixels[1][1]

            HJd = etf.pixels[0][0] == 0
            tx, ty = etf.x - 4, etf.y - 4
            PML = self.current_level.get_sprite_at(tx, ty, "Hkx")
            if not PML:
                PML = self.current_level.get_sprite_at(tx, ty, "NTi")

            if PML:
                pbA = (PML.pixels[1][1] == nRq) if HJd else (PML.pixels[1][1] != nRq)
                if not pbA:
                    return False

            HJd = etf.pixels[0][1] == 0
            tx, ty = etf.x, etf.y - 4
            PML = self.current_level.get_sprite_at(tx, ty, "Hkx")
            if not PML:
                PML = self.current_level.get_sprite_at(tx, ty, "NTi")
            if PML:
                pbA = (PML.pixels[1][1] == nRq) if HJd else (PML.pixels[1][1] != nRq)
                if not pbA:
                    return False

            HJd = etf.pixels[0][2] == 0
            tx, ty = etf.x + 4, etf.y - 4
            PML = self.current_level.get_sprite_at(tx, ty, "Hkx")
            if not PML:
                PML = self.current_level.get_sprite_at(tx, ty, "NTi")
            if PML:
                pbA = (PML.pixels[1][1] == nRq) if HJd else (PML.pixels[1][1] != nRq)
                if not pbA:
                    return False

            HJd = etf.pixels[1][0] == 0
            tx, ty = etf.x - 4, etf.y
            PML = self.current_level.get_sprite_at(tx, ty, "Hkx")
            if not PML:
                PML = self.current_level.get_sprite_at(tx, ty, "NTi")
            if PML:
                pbA = (PML.pixels[1][1] == nRq) if HJd else (PML.pixels[1][1] != nRq)
                if not pbA:
                    return False

            HJd = etf.pixels[1][2] == 0
            tx, ty = etf.x + 4, etf.y
            PML = self.current_level.get_sprite_at(tx, ty, "Hkx")
            if not PML:
                PML = self.current_level.get_sprite_at(tx, ty, "NTi")
            if PML:
                pbA = (PML.pixels[1][1] == nRq) if HJd else (PML.pixels[1][1] != nRq)
                if not pbA:
                    return False

            HJd = etf.pixels[2][0] == 0
            tx, ty = etf.x - 4, etf.y + 4
            PML = self.current_level.get_sprite_at(tx, ty, "Hkx")
            if not PML:
                PML = self.current_level.get_sprite_at(tx, ty, "NTi")
            if PML:
                pbA = (PML.pixels[1][1] == nRq) if HJd else (PML.pixels[1][1] != nRq)
                if not pbA:
                    return False

            HJd = etf.pixels[2][1] == 0
            tx, ty = etf.x, etf.y + 4
            PML = self.current_level.get_sprite_at(tx, ty, "Hkx")
            if not PML:
                PML = self.current_level.get_sprite_at(tx, ty, "NTi")
            if PML:
                pbA = (PML.pixels[1][1] == nRq) if HJd else (PML.pixels[1][1] != nRq)
                if not pbA:
                    return False

            HJd = etf.pixels[2][2] == 0
            tx, ty = etf.x + 4, etf.y + 4
            PML = self.current_level.get_sprite_at(tx, ty, "Hkx")
            if not PML:
                PML = self.current_level.get_sprite_at(tx, ty, "NTi")
            if PML:
                pbA = (PML.pixels[1][1] == nRq) if HJd else (PML.pixels[1][1] != nRq)
                if not pbA:
                    return False
        return True


# -- copy layer: colours, view (mirrored on the diagonal) and the two panels ----------------------------------
# The finished frame is recoloured and then shown mirrored on the diagonal. It is done in the camera, so every
# redraw (each action, Undo, a level jump) shows it. The game itself still reads its own,
# untouched board: get_pixels uses the raw render. Clicks are turned back before the game reads them.
#
# Two panels (the glow-up): the shown board is cut into a left half (x 0-31) and a right half (x 32-63). Only the
# live half takes clicks. ACTION3 makes the left half live, ACTION4 the right (each costs nothing and plays one
# frame); the live half wears a one-pixel yellow frame, the other a maroon one. A click in the dead half is refused:
# the dead frame flashes pink for two frames, nothing changes and no step is spent. Every level starts with the
# right half live. The frames are painted only over background pixels, never over a tile, card or the step bar.
import numpy as _vx_np  # noqa: E402
from arcengine import ActionInput as _VxActionInput, GameAction as _VxGameAction  # noqa: E402

_VX_PALETTE = _vx_np.array([0, 5, 9, 10, 5, 13, 13, 9, 6, 14, 11, 15, 7, 5, 8, 12], dtype=_vx_np.int64)
_VX_BG = 5          # shown colour of the empty board: the only thing a panel frame may be painted over
_VX_LIVE, _VX_DEAD, _VX_REFUSED = 11, 13, 6


def _vx_paint_panels(out, game):
    """Draw the one-pixel frame of each half on the shown frame (out is already turned and recoloured)."""
    live = getattr(game, "_vp_live", 1)
    blink = getattr(game, "_vp_blink", 0) > 0
    for side, x0 in ((0, 0), (1, 32)):
        colour = _VX_LIVE if side == live else (_VX_REFUSED if blink else _VX_DEAD)
        edges = [(x0, y) for y in range(64)] + [(x0 + 31, y) for y in range(64)]
        edges += [(x, 0) for x in range(x0, x0 + 32)] + [(x, 63) for x in range(x0, x0 + 32)]
        for x, y in edges:
            if out[y, x] == _VX_BG:
                out[y, x] = colour
    return out


def _vx_show(frame, game=None):
    a = _vx_np.asarray(frame)
    out = a.copy()
    m = (a >= 0) & (a <= 15)
    out[m] = _VX_PALETTE[a[m].astype(_vx_np.int64)]
    out = _vx_np.ascontiguousarray(out.T).astype(a.dtype)
    if game is not None and out.shape == (64, 64):
        _vx_paint_panels(out, game)
    return out


def _vx_unview(x, y):
    return y, x


_VX_CAMS = {}


def _vx_cam(cam, game=None):
    base = type(cam)
    if getattr(base, "_vx_layer", False):
        cam._vx_game = game
        return cam
    sub = _VX_CAMS.get(base)
    if sub is None:
        def render(self, sprites, _base=base):
            return _vx_show(_base.render(self, sprites), getattr(self, "_vx_game", None))
        sub = type("_VxCam", (base,), {"_vx_layer": True, "render": render})
        _VX_CAMS[base] = sub
    cam.__class__ = sub
    cam._vx_game = game
    return cam


Vh17.camera = property(lambda self: _vx_cam(self._camera, self))
_vx_perform = Vh17.perform_action
_vx_on_set_level = Vh17.on_set_level
_vx_step = Vh17.step


def _vx_on_set_level_panels(self, level):
    _vx_on_set_level(self, level)
    self._vp_live = 1           # every level starts with the right half live
    self._vp_blink = 0
    self._vp_refuse = False


def _vx_step_panels(self):
    aid = self.action.id.value
    if aid in (3, 4):           # choose the live half; costs nothing
        self._vp_live = 0 if aid == 3 else 1
        self.complete_action()
        return
    if getattr(self, "_vp_refuse", False):   # a click in the dead half: flash its frame, change nothing
        if getattr(self, "_vp_blink", 0) == 0:
            self._vp_blink = 3
        self._vp_blink -= 1
        if self._vp_blink == 0:
            self._vp_refuse = False
            self.complete_action()
        return
    _vx_step(self)


def _vx_perform_action(self, action_input, raw=False):
    aid = action_input.id.value if hasattr(action_input.id, "value") else int(action_input.id)
    if aid == 6 and action_input.data and "x" in action_input.data:
        d = dict(action_input.data)
        side = 0 if int(d["x"]) < 32 else 1     # the shown half the click landed in
        if side != getattr(self, "_vp_live", 1):
            self._vp_refuse = True
        d["x"], d["y"] = _vx_unview(int(d["x"]), int(d["y"]))
        action_input = _VxActionInput(id=action_input.id, data=d)
    return _vx_perform(self, action_input, raw)


Vh17.on_set_level = _vx_on_set_level_panels
Vh17.step = _vx_step_panels
Vh17.perform_action = _vx_perform_action
