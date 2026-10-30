# vz11: single-file ARC-AGI-3 game. Glow-up of vz01 (Claude Opus 5.5 Medium, 15-Oct-2026):
# new generated levels, clean colours, a splash and a win animation, and one twist every level needs.
# The screen is shown quarter turn clockwise. Rule code below: ARC Prize Foundation, MIT licence (notice follows).
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

from typing import Any, Dict, List, Optional, Set, Tuple

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
    "bodekplurlf16": Sprite(
        pixels=[
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        name="bodekplurlf16",
        visible=True,
        collidable=True,
    ),
    "bodekplurlf20": Sprite(
        pixels=[
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        name="bodekplurlf20",
        visible=True,
        collidable=True,
    ),
    "bodekplurlf32": Sprite(
        pixels=[
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        name="bodekplurlf32",
        visible=True,
        collidable=True,
    ),
    "liolfvkveqg": Sprite(
        pixels=[
            [6],
        ],
        name="liolfvkveqg",
        visible=True,
        collidable=True,
        tags=["liolfvkveqg"],
    ),
    "plzwjbfyfli-3": Sprite(
        pixels=[
            [8, 8, 8],
        ],
        name="plzwjbfyfli-3",
        visible=True,
        collidable=True,
        tags=["plzwjbfyfli", "sys_click"],
    ),
    "plzwjbfyfli-4": Sprite(
        pixels=[
            [8, 8, 8, 8],
        ],
        name="plzwjbfyfli-4",
        visible=True,
        collidable=True,
        tags=["plzwjbfyfli", "sys_click"],
    ),
    "plzwjbfyfli-4h": Sprite(
        pixels=[
            [8],
            [8],
            [8],
            [8],
        ],
        name="plzwjbfyfli-4h",
        visible=True,
        collidable=True,
        tags=["plzwjbfyfli", "sys_click"],
    ),
    "plzwjbfyfli-5": Sprite(
        pixels=[
            [8, 8, 8, 8, 8],
        ],
        name="plzwjbfyfli-5",
        visible=True,
        collidable=True,
        tags=["plzwjbfyfli", "sys_click"],
    ),
    "plzwjbfyfli-5-sowlljgtjvn": Sprite(
        pixels=[
            [8, 8, 4, 8, 8],
        ],
        name="plzwjbfyfli-5-sowlljgtjvn",
        visible=True,
        collidable=True,
        tags=["plzwjbfyfli", "sowlljgtjvn", "sys_click"],
    ),
    "plzwjbfyfli-6": Sprite(
        pixels=[
            [8, 8, 8, 8, 8, 8],
        ],
        name="plzwjbfyfli-6",
        visible=True,
        collidable=True,
        tags=["plzwjbfyfli", "sys_click"],
    ),
    "plzwjbfyfli-7": Sprite(
        pixels=[
            [8, 8, 8, 8, 8, 8, 8],
        ],
        name="plzwjbfyfli-7",
        visible=True,
        collidable=True,
        tags=["plzwjbfyfli"],
    ),
    "plzwjbfyfli-7-sowlljgtjvn": Sprite(
        pixels=[
            [8, 8, 8, 4, 8, 8, 8],
        ],
        name="plzwjbfyfli-7-sowlljgtjvn",
        visible=True,
        collidable=True,
        tags=["plzwjbfyfli", "sowlljgtjvn"],
    ),
    "plzwjbfyfli-8": Sprite(
        pixels=[
            [8, 8, 8, 8, 8, 8, 8, 8],
        ],
        name="plzwjbfyfli-8",
        visible=True,
        collidable=True,
        tags=["plzwjbfyfli", "sys_click"],
    ),
    "repwkzbkhxl": Sprite(
        pixels=[
            [11, -1, 11],
            [11, 11, 11],
        ],
        name="repwkzbkhxl",
        visible=True,
        collidable=True,
        tags=["repwkzbkhxl"],
    ),
    "sowlljgtjvn": Sprite(
        pixels=[
            [4],
        ],
        name="sowlljgtjvn",
        visible=True,
        collidable=True,
        tags=["sowlljgtjvn"],
    ),
    "tuvkdkhdokr-lexuhyxqrsm": Sprite(
        pixels=[
            [-1, 15],
            [15, 15],
        ],
        name="tuvkdkhdokr-lexuhyxqrsm",
        visible=True,
        collidable=True,
        tags=["tuvkdkhdokr", "sys_click"],
    ),
    "tuvkdkhdokr-riwynidseun": Sprite(
        pixels=[
            [15, -1],
            [15, 15],
        ],
        name="tuvkdkhdokr-riwynidseun",
        visible=True,
        collidable=True,
        tags=["tuvkdkhdokr", "sys_click"],
    ),
    "waoewejnqzc": Sprite(
        pixels=[
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        name="waoewejnqzc",
        visible=True,
        collidable=True,
        tags=["waoewejnqzc"],
    ),
}
_VZ_SPECS = [{'size': 16, 'rotation': 0, 'steps': 160, 'side': False, 'sources': [[3, 1]], 'bars': [['plzwjbfyfli-3', 3, 4]], 'cups': [[2, 13, 0], [6, 13, 0]], 'twist': {'kind': 'current', 'drift': 1, 'w': 10, 'h': 3, 'x': 3, 'y': 4}, 'gentle': True}, {'size': 16, 'rotation': 0, 'steps': 44, 'side': False, 'sources': [[9, 1]], 'bars': [['plzwjbfyfli-6', 1, 8], ['plzwjbfyfli-4', 3, 4]], 'cups': [[1, 13, 0], [5, 13, 0], [11, 13, 0]], 'twist': {'kind': 'current', 'drift': -1, 'w': 9, 'h': 2, 'x': 3, 'y': 7}}, {'size': 16, 'rotation': 0, 'steps': 38, 'side': False, 'sources': [[9, 1]], 'bars': [['plzwjbfyfli-6', 4, 6], ['plzwjbfyfli-5', 6, 7]], 'cups': [[1, 13, 0], [5, 13, 0]], 'twist': {'kind': 'current', 'drift': -1, 'w': 10, 'h': 3, 'x': 3, 'y': 5}}, {'size': 20, 'rotation': 0, 'steps': 38, 'side': False, 'sources': [[9, 1]], 'bars': [['plzwjbfyfli-4', 16, 9], ['plzwjbfyfli-5-sowlljgtjvn', 13, 14]], 'cups': [[10, 17, 0], [15, 17, 0]], 'twist': {'kind': 'current', 'drift': 1, 'w': 8, 'h': 3, 'x': 9, 'y': 10}}, {'size': 20, 'rotation': 0, 'steps': 52, 'side': False, 'sources': [[8, 1]], 'bars': [['plzwjbfyfli-8', 1, 4], ['plzwjbfyfli-8', 12, 11]], 'cups': [[2, 17, 0], [11, 17, 0], [16, 17, 0]], 'twist': {'kind': 'current', 'drift': 1, 'w': 13, 'h': 2, 'x': 5, 'y': 4}}, {'size': 16, 'rotation': 0, 'steps': 46, 'side': False, 'sources': [[2, 1], [11, 1]], 'bars': [['plzwjbfyfli-5', 1, 5], ['plzwjbfyfli-3', 11, 7], ['plzwjbfyfli-5', 0, 8]], 'cups': [[1, 13, 0], [6, 13, 0], [10, 13, 0], [13, 13, 0]], 'twist': {'kind': 'current', 'drift': 1, 'w': 9, 'h': 2, 'x': 3, 'y': 4}}, {'size': 16, 'rotation': 0, 'steps': 66, 'side': False, 'sources': [[4, 1], [12, 1]], 'bars': [['plzwjbfyfli-6', 2, 3], ['plzwjbfyfli-3', 5, 4], ['plzwjbfyfli-4', 4, 6], ['plzwjbfyfli-3', 11, 4]], 'cups': [[2, 13, 0], [8, 13, 0], [12, 13, 0]], 'twist': {'kind': 'current', 'drift': -1, 'w': 6, 'h': 4, 'x': 9, 'y': 5}}]


def _vz_twist_sprite(t, size):
    """The twist drawn as a picture (never words). current: a field whose stripes lean the way it pushes.
    rings: two identical hollow squares, each around the cell paint drops into."""
    if t["kind"] == "current":
        w, h, d = t["w"], t["h"], t["drift"]
        px = [[3 if (i - d * j) % 3 == 0 else 2 for i in range(w)] for j in range(h)]
        return [Sprite(pixels=px, name="vzcurrent", x=t["x"], y=t["y"], layer=-5, collidable=False,
                       tags=["vzcurrent"])]
    ring = [[2, 2, 2], [2, -1, 2], [2, 2, 2]]
    return [Sprite(pixels=ring, name="vzring", x=x - 1, y=y - 1, layer=-5, collidable=False, tags=["vzring"])
            for x, y in t["cells"]]


def _vz_level(s):
    """One level from its generated spec (the level generator's format plus "twist"), with the game's own sprites."""
    size = s["size"]
    out = [sprites["bodekplurlf%d" % size].clone().set_position(-1, -1)]
    for x, y in s["sources"]:
        out.append(sprites["liolfvkveqg"].clone().set_position(x, y))
    for name, x, y in s["bars"]:
        if not name.startswith("tuvkdkhdokr"):
            out.append(sprites[name].clone().set_position(x, y))
    for c in s["cups"]:
        out.append(sprites["repwkzbkhxl"].clone().set_position(c[0], c[1]).set_rotation(c[2] if len(c) > 2 else 0))
    for x, y in s["sources"]:
        out.append(sprites["sowlljgtjvn"].clone().set_position(x, y - 1))
    for name, x, y in s["bars"]:
        if name.startswith("tuvkdkhdokr"):
            out.append(sprites[name].clone().set_position(x, y))
    out.append(sprites["waoewejnqzc"].clone().set_position(0, size - 1))
    if s.get("side"):
        out.append(sprites["waoewejnqzc"].clone().set_position(size - 1, 0).set_rotation(90))
        out.append(sprites["waoewejnqzc"].clone().set_position(0, 0).set_rotation(90))
    data = {"steps": s["steps"], "dojfslwbg": s["rotation"], "vzgentle": bool(s.get("gentle"))}
    t = s.get("twist")
    if t:
        out += _vz_twist_sprite(t, size)
        data["vztwist"] = t
    return Level(sprites=out, grid_size=(size, size), data=data)


levels = [_vz_level(s) for s in _VZ_SPECS]

BACKGROUND_COLOR = 12
PADDING_COLOR = 1


class sklgkadoxw(RenderableUserDisplay):
    """."""

    def __init__(self, vwbodnowge: int = 0):
        self.vwbodnowge = vwbodnowge
        self.current_steps = vwbodnowge
        super().__init__()

    def fymfsbgqso(self, pfhpxrnpci: int) -> None:
        self.current_steps = max(0, min(pfhpxrnpci, self.vwbodnowge))

    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        if self.vwbodnowge == 0:
            return frame
        ouoessvdbk = self.current_steps / self.vwbodnowge
        zzmgpljlhw = round(64 * ouoessvdbk)
        for x in range(64):
            if x < zzmgpljlhw:
                frame[0, x] = 14
            else:
                frame[0, x] = 0
        return frame


class ntashmkaxf(RenderableUserDisplay):
    """."""

    def __init__(self, dojfslwbg: int = 0):
        self._k = dojfslwbg // 90 % 4

    def set_rotation(self, dojfslwbg: int) -> None:
        self._k = dojfslwbg // 90 % 4

    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        if self._k == 0:
            return frame
        return np.rot90(frame, k=self._k).copy()


class Vz11(ARCBaseGame):
    """."""

    mfkgvxzkbj = {
        1: {
            GameAction.ACTION1: GameAction.ACTION4,
            GameAction.ACTION2: GameAction.ACTION3,
            GameAction.ACTION3: GameAction.ACTION1,
            GameAction.ACTION4: GameAction.ACTION2,
        },
        2: {
            GameAction.ACTION1: GameAction.ACTION2,
            GameAction.ACTION2: GameAction.ACTION1,
            GameAction.ACTION3: GameAction.ACTION4,
            GameAction.ACTION4: GameAction.ACTION3,
        },
        3: {
            GameAction.ACTION1: GameAction.ACTION3,
            GameAction.ACTION2: GameAction.ACTION4,
            GameAction.ACTION3: GameAction.ACTION2,
            GameAction.ACTION4: GameAction.ACTION1,
        },
    }
    othselxnik = {
        1: {
            GameAction.ACTION1: GameAction.ACTION3,
            GameAction.ACTION2: GameAction.ACTION4,
            GameAction.ACTION3: GameAction.ACTION2,
            GameAction.ACTION4: GameAction.ACTION1,
        },
        2: {
            GameAction.ACTION1: GameAction.ACTION2,
            GameAction.ACTION2: GameAction.ACTION1,
            GameAction.ACTION3: GameAction.ACTION4,
            GameAction.ACTION4: GameAction.ACTION3,
        },
        3: {
            GameAction.ACTION1: GameAction.ACTION4,
            GameAction.ACTION2: GameAction.ACTION3,
            GameAction.ACTION3: GameAction.ACTION1,
            GameAction.ACTION4: GameAction.ACTION2,
        },
    }
    dkvpswzsjg: str
    vsoxmtrhqt: Optional[Sprite]
    hmxltcipkc: List[Tuple[Sprite, int, int]]
    xpcxocsmmq: List[Sprite]
    kfdcqkodyy: bool
    lybfalkrdl: bool
    cevwbinfgl: Set[Sprite]
    onoqwewztl: Set[Sprite]
    trhynadhiz: int
    lijmqzmgnw: sklgkadoxw
    avangppqui: bool

    def __init__(self) -> None:
        self.dkvpswzsjg = "change"
        self.vsoxmtrhqt = None
        self.hmxltcipkc = []
        self.xpcxocsmmq = []
        self.kfdcqkodyy = False
        self.lybfalkrdl = False
        self.cevwbinfgl = set()
        self.onoqwewztl = set()
        self.trhynadhiz = 0
        self.lijmqzmgnw = sklgkadoxw(vwbodnowge=0)
        self.avangppqui = False
        self.yqejjfwwh = False
        self.zlhbnhpcq = 0
        self._vz_win = 0
        self.lyremoheq = 0
        self.fahhoimkk = 0
        self.jinpztikz = ntashmkaxf(0)
        zgzbkvrwm = Camera(
            background=BACKGROUND_COLOR,
            letter_box=PADDING_COLOR,
            interfaces=[self.lijmqzmgnw, self.jinpztikz],
        )
        super().__init__(
            game_id="vz11",
            levels=levels,
            camera=zgzbkvrwm,
            available_actions=[1, 2, 3, 4, 5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self.dkvpswzsjg = "change"
        self.vsoxmtrhqt = None
        self.hmxltcipkc = []
        self.xpcxocsmmq = []
        self.kfdcqkodyy = False
        self.lybfalkrdl = False
        self.cevwbinfgl = set()
        self.onoqwewztl = set()
        self.avangppqui = False
        self.yqejjfwwh = False
        self.lyremoheq = 0
        for s in level.get_sprites_by_tag("plzwjbfyfli"):
            s.pixels[(s.pixels >= 0) & (s.pixels != 4)] = 8
        for s in level.get_sprites():
            if s.name == "repwkzbkhxl":
                s.pixels[s.pixels >= 0] = 11
        for s in level.get_sprites_by_tag("waoewejnqzc"):
            s.pixels[s.pixels >= 0] = 1
        pfhpxrnpci = level.get_data("steps") or 50
        self.zlhbnhpcq = pfhpxrnpci
        self.lijmqzmgnw.vwbodnowge = pfhpxrnpci
        self.lijmqzmgnw.fymfsbgqso(pfhpxrnpci)
        uhbgnthefe = self.gsvsxaspkc()
        if uhbgnthefe:
            self.mmzrajuxwp(uhbgnthefe)
        dojfslwbg = level.get_data("dojfslwbg") or 0
        self.fahhoimkk = dojfslwbg // 90 % 4
        self.jinpztikz.set_rotation(dojfslwbg)


    # ── vz glow-up: the twist, the splash and the win animation ──────────────────────────────────────────────
    def _vz_flow(self, p, dx, dy):
        """The current: paint falling inside the field moves one cell sideways per row; it falls straight again
        once it leaves the field."""
        t = self.current_level.get_data("vztwist")
        if not t or t["kind"] != "current" or dy != 1:
            return dx, dy
        inside = t["x"] <= p.x < t["x"] + t["w"] and t["y"] <= p.y < t["y"] + t["h"]
        if inside and dx == 0:
            return t["drift"], 1
        if not inside and dx != 0:
            return 0, 1
        return dx, dy

    def _vz_drop(self, x, y):
        """A new drop of paint. Twin rings: a drop landing in one ring's middle comes out of the other's."""
        t = self.current_level.get_data("vztwist")
        if t and t["kind"] == "rings":
            (ax, ay), (bx, by) = t["cells"]
            if (x, y) == (ax, ay) and self.current_level.get_sprite_at(bx, by) is None:
                x, y = bx, by
            elif (x, y) == (bx, by) and self.current_level.get_sprite_at(ax, ay) is None:
                x, y = ax, ay
        return sprites["liolfvkveqg"].clone().set_position(x, y)

    def _vz_spark(self, x, y, colour):
        s = Sprite(pixels=[[colour]], name="vzspark", x=x, y=y, layer=3, collidable=False, tags=["vzspark"])
        self.current_level.add_sprite(s)
        self.xpcxocsmmq.append(s)   # cleared with the paint after a failed spill

    def _vz_splash(self, cup):
        """A visible answer: a filled cup throws two drops up and out."""
        if cup.rotation == 0:
            self._vz_spark(cup.x - 1, cup.y - 1, 10)
            self._vz_spark(cup.x + 3, cup.y - 1, 10)

    def _vz_celebrate(self):
        """The win: the paint and the full cups flash and sparks rise from every cup, then the next level.
        True while frames are left to play."""
        i = self._vz_win
        if i >= 8:
            self._vz_win = 0
            return False
        self._vz_win = i + 1
        for p in self.xpcxocsmmq:
            if "liolfvkveqg" in p.tags:
                p.pixels[p.pixels >= 0] = 7 if i % 2 == 0 else 6
        for c in self.mxdlffpzkc():
            c.pixels[c.pixels >= 0] = 7 if i % 2 == 0 else 13
            if c.rotation == 0 and c.y - 1 - i >= 1:
                self._vz_spark(c.x + 1, c.y - 1 - i, 7)
        return True

    def fbrwmvzsym(self) -> List[Sprite]:
        return [s for s in self.current_level.get_sprites_by_tag("plzwjbfyfli")] + [s for s in self.current_level.get_sprites_by_tag("tuvkdkhdokr")]

    def qbsoyazkhk(self) -> List[Sprite]:
        return [s for s in self.current_level.get_sprites_by_tag("liolfvkveqg")]

    def mxdlffpzkc(self) -> List[Sprite]:
        return [s for s in self.current_level.get_sprites_by_tag("repwkzbkhxl")]

    def vgpoqzieha(self) -> List[Sprite]:
        return [s for s in self.current_level.get_sprites_by_tag("waoewejnqzc")]

    def gsvsxaspkc(self) -> Optional[Sprite]:
        bewcnjlccv = self.fbrwmvzsym()
        if not bewcnjlccv:
            return None
        return min(bewcnjlccv, key=lambda vcnqlwquvy: vcnqlwquvy.x**2 + vcnqlwquvy.y**2)

    def husluhmboo(self, hualjkqrro: Sprite, x: int, y: int) -> bool:
        """."""
        ozlpegmuiw = hualjkqrro.width
        thjmlectxc = hualjkqrro.height
        if y < 3:
            return False
        for ifavaamret in self.mxdlffpzkc():
            rx, ry = (ifavaamret.x, ifavaamret.y)
            fykwwtgsjv = ifavaamret.width
            zgqksrdiou = ifavaamret.height
            if x < rx + fykwwtgsjv + 1 and x + ozlpegmuiw > rx - 1 and (y < ry + zgqksrdiou + 1) and (y + thjmlectxc > ry - 1):
                return False
        return True

    def oioatzlrlu(self, ukutpdlsfq: Sprite, tkwwsinjpi: Sprite) -> bool:
        ax1, ay1, ax2, ay2 = (
            ukutpdlsfq.x,
            ukutpdlsfq.y,
            ukutpdlsfq.x + ukutpdlsfq.width,
            ukutpdlsfq.y + ukutpdlsfq.height,
        )
        bx1, by1, bx2, by2 = (
            tkwwsinjpi.x,
            tkwwsinjpi.y,
            tkwwsinjpi.x + tkwwsinjpi.width,
            tkwwsinjpi.y + tkwwsinjpi.height,
        )
        return ax1 < bx2 and ax2 > bx1 and (ay1 < by2) and (ay2 > by1)

    def mmzrajuxwp(self, hualjkqrro: Sprite) -> None:
        if self.vsoxmtrhqt is not None:
            self.ntuflwihof()
        self.vsoxmtrhqt = hualjkqrro
        if hualjkqrro is not None:
            hualjkqrro.pixels[(hualjkqrro.pixels >= 0) & (hualjkqrro.pixels != 4)] = 9
            hualjkqrro.set_layer(1)
        self.avangppqui = True

    def ntuflwihof(self) -> None:
        if self.vsoxmtrhqt is not None:
            nogozwphuv = 15 if "tuvkdkhdokr" in self.vsoxmtrhqt.tags else 8
            self.vsoxmtrhqt.pixels[(self.vsoxmtrhqt.pixels >= 0) & (self.vsoxmtrhqt.pixels != 4)] = nogozwphuv
            self.vsoxmtrhqt.set_layer(0)
        self.vsoxmtrhqt = None

    def vdwhttyyfq(self) -> None:
        self.dkvpswzsjg = "spill"
        self.ntuflwihof()
        self.hmxltcipkc = [(lpaiwmascx, 0, 1) for lpaiwmascx in self.qbsoyazkhk()]
        self.xpcxocsmmq = []
        self.kfdcqkodyy = False
        self.lybfalkrdl = False
        self.cevwbinfgl = set()
        self.onoqwewztl = set()
        for lwigswghhd in self.current_level.get_sprites_by_tag("sowlljgtjvn"):
            px, py = (lwigswghhd.x, lwigswghhd.y)
            cuftbajfn = lwigswghhd.pixels
            for y in range(cuftbajfn.shape[0]):
                for x in range(cuftbajfn.shape[1]):
                    if int(cuftbajfn[y, x]) == 4:
                        qxatjlxbsr, mdktzafzgr = (px + x, py + y)
                        lxmalbxucn = self.current_level.get_sprite_at(qxatjlxbsr, mdktzafzgr + 1)
                        ingqkycxdt = lxmalbxucn and "liolfvkveqg" in getattr(lxmalbxucn, "tags", [])
                        if not ingqkycxdt and self.current_level.get_sprite_at(qxatjlxbsr, mdktzafzgr + 1) is None:
                            yfwryonwmf = self._vz_drop(qxatjlxbsr, mdktzafzgr + 1)
                            self.current_level.add_sprite(yfwryonwmf)
                            self.hmxltcipkc.append((yfwryonwmf, 0, 1))
                            self.xpcxocsmmq.append(yfwryonwmf)

    def lpqbikobah(self) -> None:
        for s in self.xpcxocsmmq:
            self.current_level.remove_sprite(s)
        self.xpcxocsmmq = []
        for s in self.mxdlffpzkc():
            s.pixels[s.pixels >= 0] = 11
        for s in self.vgpoqzieha():
            s.pixels[s.pixels >= 0] = 1
        self.cevwbinfgl = set()
        self.onoqwewztl = set()
        self.dkvpswzsjg = "change"
        self.kfdcqkodyy = False
        self.lybfalkrdl = False
        self.hmxltcipkc = []
        self.lyremoheq += 1
        uhbgnthefe = self.gsvsxaspkc()
        if uhbgnthefe:
            self.mmzrajuxwp(uhbgnthefe)

    def step(self) -> None:
        action_id, action_data = self.krehtwyvlu()
        if self.dkvpswzsjg == "change":
            if action_id != GameAction.RESET:
                self.ytqycovhld(1)
            if action_id == GameAction.ACTION6:
                tkqedciqx = action_data.get("x", 0)
                dqkivrvrc = action_data.get("y", 0)
                zvlpmllzzi = self.camera.display_to_grid(tkqedciqx, dqkivrvrc)
                if zvlpmllzzi:
                    qxatjlxbsr, mdktzafzgr = zvlpmllzzi
                    cbfkqeecgo: Optional[Sprite] = None
                    for vcnqlwquvy in self.fbrwmvzsym():
                        if vcnqlwquvy.x <= qxatjlxbsr < vcnqlwquvy.x + vcnqlwquvy.width and vcnqlwquvy.y <= mdktzafzgr < vcnqlwquvy.y + vcnqlwquvy.height:
                            cbfkqeecgo = vcnqlwquvy
                            break
                    if cbfkqeecgo:
                        self.mmzrajuxwp(cbfkqeecgo)
                        self.yqejjfwwh = True
                        self.complete_action()
                        return
            if self.vsoxmtrhqt is not None:
                zmgbkzxvf, wcrkcuoyr = (0, 0)
                if action_id == GameAction.ACTION1:
                    wcrkcuoyr = -1
                elif action_id == GameAction.ACTION2:
                    wcrkcuoyr = 1
                elif action_id == GameAction.ACTION3:
                    zmgbkzxvf = -1
                elif action_id == GameAction.ACTION4:
                    zmgbkzxvf = 1
                if zmgbkzxvf != 0 or wcrkcuoyr != 0:
                    ssgevmwqov = self.vsoxmtrhqt.x + zmgbkzxvf
                    jppwwnrrfn = self.vsoxmtrhqt.y + wcrkcuoyr
                    if self.husluhmboo(self.vsoxmtrhqt, ssgevmwqov, jppwwnrrfn):
                        collisions = self.try_move_sprite(self.vsoxmtrhqt, zmgbkzxvf, wcrkcuoyr)
                        if len(collisions) > 0 and all(["plzwjbfyfli" in c.tags or "tuvkdkhdokr" in c.tags for c in collisions]):
                            self.vsoxmtrhqt.move(zmgbkzxvf, wcrkcuoyr)
                    self.yqejjfwwh = False
                    self.complete_action()
                    self.avangppqui = False
                    return
            if action_id == GameAction.ACTION5:
                if self.lyremoheq >= 4 and not self.current_level.get_data("vzgentle"):
                    self.lose()
                    self.complete_action()
                    return
                self.vdwhttyyfq()
                self.avangppqui = False
                self.yqejjfwwh = False
                return
            self.complete_action()
            return
        elif self.dkvpswzsjg == "spill":
            if self.lybfalkrdl:
                nldokazwta = self.mxdlffpzkc()
                zmkiirynyo = all((r in self.cevwbinfgl for r in nldokazwta))
                if self.kfdcqkodyy or not zmkiirynyo:
                    if self.trhynadhiz < 6:
                        for qyutcrxkne in self.onoqwewztl:
                            qyutcrxkne.pixels[qyutcrxkne.pixels >= 0] = 14 if self.trhynadhiz % 2 == 1 else 1
                        if self.trhynadhiz < 5:
                            for ifavaamret in self.mxdlffpzkc():
                                if ifavaamret not in self.cevwbinfgl:
                                    ifavaamret.pixels[ifavaamret.pixels >= 0] = 0 if self.trhynadhiz % 2 == 0 else 11
                        self.trhynadhiz += 1
                    else:
                        self.lpqbikobah()
                        if self.zlhbnhpcq <= 0:
                            self.lose()
                        self.complete_action()
                else:
                    if self._vz_celebrate():
                        return
                    self.complete_action()
                    self.next_level()
                return
            hhrqsxbmic: List[Tuple[Sprite, int, int]] = []
            for lpaiwmascx, zmgbkzxvf, wcrkcuoyr in self.hmxltcipkc:
                zmgbkzxvf, wcrkcuoyr = self._vz_flow(lpaiwmascx, zmgbkzxvf, wcrkcuoyr)
                tayzpnizn, lxrpmtrmq = (lpaiwmascx.x, lpaiwmascx.y)
                obzjtntha, unvkukvdu = (-1, 1) if wcrkcuoyr != 0 else (0, 0)
                vwwcczstp, kghcadhlp = (-1, 1) if wcrkcuoyr == 0 else (0, 0)
                qkwtogjpyx = [(obzjtntha, vwwcczstp), (unvkukvdu, kghcadhlp)]
                lxmalbxucn = self.current_level.get_sprite_at(tayzpnizn + zmgbkzxvf, lxrpmtrmq + wcrkcuoyr)
                if lxmalbxucn is None:
                    yfwryonwmf = self._vz_drop(tayzpnizn + zmgbkzxvf, lxrpmtrmq + wcrkcuoyr)
                    self.current_level.add_sprite(yfwryonwmf)
                    hhrqsxbmic.append((yfwryonwmf, zmgbkzxvf, wcrkcuoyr))
                    self.xpcxocsmmq.append(yfwryonwmf)
                    continue
                if "liolfvkveqg" in lxmalbxucn.tags:
                    hhrqsxbmic.append((lxmalbxucn, zmgbkzxvf, wcrkcuoyr))
                if "plzwjbfyfli" in lxmalbxucn.tags:
                    for oizjapxnvj, zrgzlvcvcr in qkwtogjpyx:
                        if self.current_level.get_sprite_at(tayzpnizn + oizjapxnvj, lxrpmtrmq + zrgzlvcvcr) is None:
                            yfwryonwmf = self._vz_drop(tayzpnizn + oizjapxnvj, lxrpmtrmq + zrgzlvcvcr)
                            self.current_level.add_sprite(yfwryonwmf)
                            hhrqsxbmic.append((yfwryonwmf, zmgbkzxvf, wcrkcuoyr))
                            self.xpcxocsmmq.append(yfwryonwmf)
                    continue
                if "repwkzbkhxl" in lxmalbxucn.tags:
                    owyqnbmyij = self.current_level.get_sprite_at(tayzpnizn + obzjtntha, lxrpmtrmq + vwwcczstp)
                    faksfmaezd = self.current_level.get_sprite_at(tayzpnizn + unvkukvdu, lxrpmtrmq + kghcadhlp)
                    if owyqnbmyij is lxmalbxucn and faksfmaezd is lxmalbxucn:
                        lxmalbxucn.pixels[lxmalbxucn.pixels >= 0] = 13
                        self.cevwbinfgl.add(lxmalbxucn)
                        self._vz_splash(lxmalbxucn)
                        continue
                    else:
                        for oizjapxnvj, zrgzlvcvcr in qkwtogjpyx:
                            if self.current_level.get_sprite_at(tayzpnizn + oizjapxnvj, lxrpmtrmq + zrgzlvcvcr) is None:
                                yfwryonwmf = self._vz_drop(tayzpnizn + oizjapxnvj, lxrpmtrmq + zrgzlvcvcr)
                                self.current_level.add_sprite(yfwryonwmf)
                                hhrqsxbmic.append((yfwryonwmf, zmgbkzxvf, wcrkcuoyr))
                                self.xpcxocsmmq.append(yfwryonwmf)
                        continue
                if "tuvkdkhdokr" in lxmalbxucn.tags:
                    owyqnbmyij = self.current_level.get_sprite_at(tayzpnizn + obzjtntha, lxrpmtrmq + vwwcczstp)
                    faksfmaezd = self.current_level.get_sprite_at(tayzpnizn + unvkukvdu, lxrpmtrmq + kghcadhlp)
                    if owyqnbmyij is lxmalbxucn and faksfmaezd is None:
                        nizmgdznmn = wcrkcuoyr
                        yevagjsmfn = -zmgbkzxvf
                        yfwryonwmf = self._vz_drop(tayzpnizn + nizmgdznmn, lxrpmtrmq + yevagjsmfn)
                        self.current_level.add_sprite(yfwryonwmf)
                        hhrqsxbmic.append((yfwryonwmf, nizmgdznmn, yevagjsmfn))
                        self.xpcxocsmmq.append(yfwryonwmf)
                    if faksfmaezd is lxmalbxucn and owyqnbmyij is None:
                        nizmgdznmn = -wcrkcuoyr
                        yevagjsmfn = zmgbkzxvf
                        yfwryonwmf = self._vz_drop(tayzpnizn + nizmgdznmn, lxrpmtrmq + yevagjsmfn)
                        self.current_level.add_sprite(yfwryonwmf)
                        hhrqsxbmic.append((yfwryonwmf, nizmgdznmn, yevagjsmfn))
                        self.xpcxocsmmq.append(yfwryonwmf)
                    else:
                        for oizjapxnvj, zrgzlvcvcr in qkwtogjpyx:
                            if self.current_level.get_sprite_at(tayzpnizn + oizjapxnvj, lxrpmtrmq + zrgzlvcvcr) is None:
                                yfwryonwmf = self._vz_drop(tayzpnizn + oizjapxnvj, lxrpmtrmq + zrgzlvcvcr)
                                self.current_level.add_sprite(yfwryonwmf)
                                hhrqsxbmic.append((yfwryonwmf, zmgbkzxvf, wcrkcuoyr))
                                self.xpcxocsmmq.append(yfwryonwmf)
                        continue
                if "waoewejnqzc" in lxmalbxucn.tags:
                    lxmalbxucn.pixels[lxmalbxucn.pixels >= 0] = 14
                    self.onoqwewztl.add(lxmalbxucn)
                    self.kfdcqkodyy = True
                    continue
            self.hmxltcipkc = hhrqsxbmic
            if not self.hmxltcipkc:
                self.lybfalkrdl = True
                self.trhynadhiz = 0
            return

    def ojydygjkdb(self, hyutemwrji: int, shkslvxwqs: int) -> Tuple[int, int]:
        """."""
        k = self.fahhoimkk
        if k == 0:
            return (hyutemwrji, shkslvxwqs)
        if k == 1:
            return (63 - shkslvxwqs, hyutemwrji)
        if k == 2:
            return (63 - hyutemwrji, 63 - shkslvxwqs)
        return (shkslvxwqs, 63 - hyutemwrji)

    def rqlmciubuz(self, qxatjlxbsr: int, mdktzafzgr: int) -> Tuple[int, int]:
        """."""
        k = self.fahhoimkk
        if k == 0:
            return (qxatjlxbsr, mdktzafzgr)
        if k == 1:
            return (mdktzafzgr, 63 - qxatjlxbsr)
        if k == 2:
            return (63 - qxatjlxbsr, 63 - mdktzafzgr)
        return (63 - mdktzafzgr, qxatjlxbsr)

    def krehtwyvlu(self) -> Tuple[GameAction, Dict[str, Any]]:
        """."""
        k = self.fahhoimkk
        hwpdaniibf = self.action.id
        data = self.action.data
        if k == 0:
            return (hwpdaniibf, data)
        if hwpdaniibf in self.mfkgvxzkbj.get(k, {}):
            return (self.mfkgvxzkbj[k][hwpdaniibf], data)
        if hwpdaniibf == GameAction.ACTION6:
            hyutemwrji = data.get("x", 0)
            shkslvxwqs = data.get("y", 0)
            qxatjlxbsr, mdktzafzgr = self.ojydygjkdb(hyutemwrji, shkslvxwqs)
            return (hwpdaniibf, {"x": qxatjlxbsr, "y": mdktzafzgr})
        return (hwpdaniibf, data)

    def ytqycovhld(self, uarpgqegqg: int) -> None:
        """."""
        self.zlhbnhpcq = max(0, self.zlhbnhpcq - uarpgqegqg)
        self.lijmqzmgnw.fymfsbgqso(self.zlhbnhpcq)
        if self.zlhbnhpcq <= 0:
            self.lose()
            self.complete_action()
            return

    def _get_hidden_state(self) -> np.ndarray:
        """."""
        itxxbwovcy = np.zeros((4, 4), dtype=np.int16)
        itxxbwovcy[0, 0] = self.lijmqzmgnw.current_steps
        return itxxbwovcy

    def _get_valid_actions(self) -> list[ActionInput]:
        """."""
        k = self.fahhoimkk
        if self.yqejjfwwh:
            ytfzukjyoe = [ActionInput(id=GameAction.from_id(ukutpdlsfq)) for ukutpdlsfq in [1, 2, 3, 4, 5] if ukutpdlsfq in self._available_actions]
        else:
            ytfzukjyoe = super()._get_valid_actions()
        if k == 0:
            return ytfzukjyoe
        rehehlgmbg: list[ActionInput] = []
        for action in ytfzukjyoe:
            if action.id in self.othselxnik.get(k, {}):
                rehehlgmbg.append(ActionInput(id=self.othselxnik[k][action.id], data=action.data))
            elif action.id == GameAction.ACTION6:
                qxatjlxbsr = action.data.get("x", 0)
                mdktzafzgr = action.data.get("y", 0)
                hyutemwrji, shkslvxwqs = self.rqlmciubuz(qxatjlxbsr, mdktzafzgr)
                rehehlgmbg.append(ActionInput(id=action.id, data={"x": hyutemwrji, "y": shkslvxwqs}))
            else:
                rehehlgmbg.append(action)
        return rehehlgmbg


# -- copy layer: colours and view (quarter turn clockwise) ----------------------------------------------------
# The finished frame is recoloured and then shown quarter turn clockwise. It is done in the camera, so every
# redraw (each action, Undo, a level jump) shows it. The game itself still reads its own,
# untouched board: get_pixels uses the raw render. Input is turned back before the game reads it.
import numpy as _vx_np  # noqa: E402
from arcengine import ActionInput as _VxActionInput, GameAction as _VxGameAction  # noqa: E402

_VX_PALETTE = _vx_np.array([8, 13, 10, 0, 0, 5, 11, 0, 14, 6, 0, 12, 9, 11, 7, 15], dtype=_vx_np.int64)
_VX_ARROW = {1: 3, 2: 4, 3: 2, 4: 1}


def _vx_show(frame):
    a = _vx_np.asarray(frame)
    out = a.copy()
    m = (a >= 0) & (a <= 15)
    out[m] = _VX_PALETTE[a[m].astype(_vx_np.int64)]
    return _vx_np.ascontiguousarray(_vx_np.rot90(out, k=-1)).astype(a.dtype)


def _vx_unview(x, y):
    return y, 63 - x


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


Vz11.camera = property(lambda self: _vx_cam(self._camera))
_vx_perform = Vz11.perform_action


def _vx_perform_action(self, action_input, raw=False):
    aid = action_input.id.value if hasattr(action_input.id, "value") else int(action_input.id)
    if aid in _VX_ARROW:
        action_input = _VxActionInput(id=_VxGameAction.from_id(_VX_ARROW[aid]), data=action_input.data)
    elif aid == 6 and action_input.data and "x" in action_input.data:
        d = dict(action_input.data)
        d["x"], d["y"] = _vx_unview(int(d["x"]), int(d["y"]))
        action_input = _VxActionInput(id=action_input.id, data=d)
    return _vx_perform(self, action_input, raw)


Vz11.perform_action = _vx_perform_action
