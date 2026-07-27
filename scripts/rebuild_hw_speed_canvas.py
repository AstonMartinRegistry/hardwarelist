#!/usr/bin/env python3
"""Rebuild hw-speed-setups.canvas.tsx embedded data from rollup JSON."""

from __future__ import annotations

import json
import re
from pathlib import Path

from paths import DATA, DISCORD_DATA, hw_speed_canvas

HW = DATA / "hardware-by-slug.json"
HW_MSG = DATA / "hardware-messages-by-slug.json"
SPEED = DISCORD_DATA / "speed-metrics.json"
SETUPS = DATA / "hardware-setups.json"
CANVAS = hw_speed_canvas()

GENERIC = {"vram", "ram", "cpu", "gpu", "igpu", "nvidia", "amd"}
TOP_N = 14


def build_hw_data(doc: dict) -> dict:
    slugs = doc["slugs"]
    totals = dict(zip(slugs, doc["slugTotals"]))
    matrix = doc["matrix"]
    specific = [s for s in slugs if s not in GENERIC]
    specific.sort(key=lambda s: (-totals[s], s))
    top = specific[:TOP_N]
    idx = {s: slugs.index(s) for s in top}
    return {
        "months": doc["months"],
        "monthLabels": doc["monthLabels"],
        "slugs": top,
        "slugTotals": [totals[s] for s in top],
        "matrix": [matrix[idx[s]] for s in top],
        "meta": {
            "messages": doc["meta"]["message_count"],
            "mapped": doc["meta"]["mapped_messages"],
            "slugs_total": doc["meta"]["unique_slugs"],
        },
    }


def build_hw_msg_data(hw_doc: dict, msg_doc: dict, top_slugs: list[str]) -> dict:
    slugs_data = msg_doc.get("slugs", {})
    rows: list[dict] = []
    for slug in top_slugs:
        entry = slugs_data.get(slug, {})
        for sample in entry.get("samples", [])[:6]:
            msg = sample.get("message", "")
            rows.append(
                {
                    "slug": slug,
                    "month": sample.get("month", ""),
                    "extracted": sample.get("extracted", ""),
                    "message": msg[:280] + ("…" if len(msg) > 280 else ""),
                }
            )
    return {"rows": rows[:48]}


def build_speed_data(doc: dict) -> dict:
    return {
        "months": doc["months"],
        "monthLabels": doc["monthLabels"],
        "tpsMedian": doc["series"]["tps_median"],
        "tpsCount": doc["series"]["tps_count"],
        "ttftMedianMs": doc["series"]["ttft_median_ms"],
        "ttftCount": doc["series"]["ttft_count"],
        "meta": {
            "messages": doc["meta"]["message_count"],
            "with_metrics": doc["meta"]["messages_with_metrics"],
            "tps_values": doc["meta"]["total_tps_values"],
            "ttft_values": doc["meta"]["total_ttft_values"],
            "overall_tps_median": doc["overall"]["tps"]["median"] if doc["overall"]["tps"] else 0,
        },
    }


def build_setup_data(doc: dict) -> dict:
    rank = {
        "full": 6,
        "hw_speed_model": 5,
        "hw_speed_benchmark": 4,
        "hw_speed": 3,
        "inferred_model": 2,
        "inferred": 1,
    }
    setups = []
    for row in doc["setups"]:
        msg = row.get("message") or row.get("content_preview") or ""
        setups.append(
            {
                "month": row["month"],
                "tier": row.get("tier", "full"),
                "model": row["model"],
                "hardware": row["hardware"],
                "quantization": row["quantization"],
                "speed": row["speed"],
                "message": msg,
                "_rank": rank.get(row.get("tier", "full"), 0),
            }
        )
    setups.sort(key=lambda r: (r["month"], r["_rank"]), reverse=True)
    for row in setups:
        row.pop("_rank", None)
    return {
        "count": doc["meta"]["message_count"],
        "by_tier": doc["meta"].get("by_tier", {}),
        "setups": [{k: v for k, v in row.items() if k != "_rank"} for row in setups[:120]],
    }


def patch_block(text: str, name: str, data: dict) -> str:
    payload = json.dumps(data, indent=2)
    pattern = rf"const {name} = \{{[\s\S]*?\}} as const;"
    match = re.search(pattern, text)
    if not match:
        raise SystemExit(f"Could not patch {name} in canvas")
    replacement = f"const {name} = {payload} as const;"
    return text[: match.start()] + replacement + text[match.end() :]


def main() -> None:
    hw_doc = json.loads(HW.read_text(encoding="utf-8"))
    msg_doc = json.loads(HW_MSG.read_text(encoding="utf-8"))
    speed_doc = json.loads(SPEED.read_text(encoding="utf-8"))
    setup_doc = json.loads(SETUPS.read_text(encoding="utf-8"))

    if not CANVAS.exists():
        raise SystemExit(f"Canvas not found: {CANVAS}")

    hw_data = build_hw_data(hw_doc)
    text = CANVAS.read_text(encoding="utf-8")
    text = patch_block(text, "HW_DATA", hw_data)
    text = patch_block(text, "HW_MSG_DATA", build_hw_msg_data(hw_doc, msg_doc, hw_data["slugs"]))
    text = patch_block(text, "SPEED_DATA", build_speed_data(speed_doc))
    text = patch_block(text, "SETUP_DATA", build_setup_data(setup_doc))
    CANVAS.write_text(text, encoding="utf-8")
    print(f"Updated {CANVAS}")


if __name__ == "__main__":
    main()
