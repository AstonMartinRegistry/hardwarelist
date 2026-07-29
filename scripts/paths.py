"""Shared paths for the hardwarelist project.

Project-owned data lives here. Upstream Discord classification inputs are read
from the sibling discorddata repo (override with DISCORDDATA_ROOT).
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTPUT = ROOT / "public"
CANVASES = ROOT / "canvases"

DISCORD_ROOT = Path(
    os.environ.get(
        "DISCORDDATA_ROOT",
        str(ROOT.parent / "discorddata"),
    )
)
DISCORD_DATA = DISCORD_ROOT / "jsonstrimmed/localllmbymonth/data"
DISCORD_MONTHLY = DISCORD_ROOT / "jsonstrimmed/localllmbymonth"

# Prefer in-repo canvases; fall back to Cursor project canvases after open.
CURSOR_CANVASES = (
    Path.home()
    / ".cursor/projects/Users-danielk-Desktop-projects-hardwarelist/canvases"
)


def liked_canvas_data() -> Path:
    candidates = (
        CANVASES / "hardware-setups-review.canvas.data.json",
        CURSOR_CANVASES / "hardware-setups-review.canvas.data.json",
    )
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def review_canvas() -> Path:
    candidates = (
        CANVASES / "hardware-setups-review.canvas.tsx",
        CURSOR_CANVASES / "hardware-setups-review.canvas.tsx",
    )
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def hw_speed_canvas() -> Path:
    candidates = (
        CANVASES / "hw-speed-setups.canvas.tsx",
        CURSOR_CANVASES / "hw-speed-setups.canvas.tsx",
    )
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]
