#!/usr/bin/env python3
"""Rebuild hardware-setups-review.canvas.tsx embedded data from hardware-setups.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

from paths import DATA, review_canvas

SETUPS = DATA / "hardware-setups.json"
CANVAS = review_canvas()

TIER_RANK = {
    "full": 6,
    "hw_speed_model": 5,
    "hw_speed_benchmark": 4,
    "hw_speed": 3,
    "inferred_model": 2,
    "inferred": 1,
}


def build_review_data(doc: dict) -> dict:
    rows: list[dict] = []
    for row in doc["setups"]:
        specs = row.get("specs") or {}
        rows.append(
            {
                "id": row["id"],
                "month": row["month"],
                "timestamp": row.get("timestamp", ""),
                "tier": row.get("tier", "full"),
                "model": row.get("model", ""),
                "hardware": row.get("hardware", ""),
                "quantization": row.get("quantization", ""),
                "speed": row.get("speed", ""),
                "message": row.get("message") or row.get("content_preview") or "",
                "tps": specs.get("tps_values") or [],
                "ttft_ms": specs.get("ttft_ms_values") or [],
                "_rank": TIER_RANK.get(row.get("tier", "full"), 0),
            }
        )
    rows.sort(key=lambda r: (r["month"], r["_rank"]), reverse=True)
    for row in rows:
        row.pop("_rank", None)
    return {
        "count": doc["meta"]["message_count"],
        "by_tier": doc["meta"].get("by_tier", {}),
        "setups": rows,
    }


def patch_block(text: str, name: str, data: dict) -> str:
    payload = json.dumps(data, indent=2)
    pattern = rf"const {name} = \{{[\s\S]*?\}}(?: as const)?;"
    match = re.search(pattern, text)
    if not match:
        raise SystemExit(f"Could not patch {name} in canvas")
    replacement = f"const {name} = {payload};"
    return text[: match.start()] + replacement + text[match.end() :]


def main() -> None:
    if not CANVAS.exists():
        raise SystemExit(f"Canvas not found: {CANVAS}")
    doc = json.loads(SETUPS.read_text(encoding="utf-8"))
    data = build_review_data(doc)
    text = CANVAS.read_text(encoding="utf-8")
    text = patch_block(text, "SETUP_REVIEW_DATA", data)
    CANVAS.write_text(text, encoding="utf-8")
    print(f"Updated {CANVAS} ({data['count']} setups)")


if __name__ == "__main__":
    main()
