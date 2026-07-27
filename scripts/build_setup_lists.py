#!/usr/bin/env python3
"""Build hardware benchmark setup lists with expanded detection tiers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from paths import DATA, DISCORD_DATA, DISCORD_MONTHLY
from registry_match import is_reddit_repost, match_registry
from setup_detect import (
    assign_tier,
    extract_tps,
    extract_ttft_ms,
    format_speed,
    infer_model,
    is_complete_setup,
    load_hw_entries,
    load_model_entries,
    load_qt_entries,
    match_hardware,
    summarize_hardware,
    summarize_quant,
)

MONTHLY = DISCORD_MONTHLY
PARSED = DISCORD_DATA / "model-mentions-full-parsed.json"
OUT = DATA / "hardware-setups.json"
LEGACY_OUT = DATA / "setup-lists.json"

TIER_RANK = {
    "full": 6,
    "hw_speed_model": 5,
    "hw_speed_benchmark": 4,
    "hw_speed": 3,
    "inferred_model": 2,
    "inferred": 1,
}

TIER_DESC = {
    "full": "Tagged in all 4 categories: model + hardware + quantization + speed",
    "hw_speed_model": "Tagged hardware + speed + model (quant may be missing)",
    "hw_speed_benchmark": "Tagged hardware + speed with numeric tok/s or TTFT in message",
    "hw_speed": "Tagged hardware + speed only",
    "inferred_model": "Full-scan: registry hardware + numeric speed + model signal",
    "inferred": "Full-scan: registry hardware + numeric tok/s or TTFT",
}


def load_category_index() -> dict[str, dict[str, dict]]:
    index: dict[str, dict[str, dict]] = {}
    for name in ("hardware", "speed", "quantization", "model-mentions"):
        index[name] = {}
        for path in sorted((DISCORD_DATA / name).glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            month = doc["meta"]["month"]
            for msg in doc.get("messages", []):
                index[name][msg["id"]] = {**msg, "month": month}
    return index


def load_parsed_tags() -> dict[str, str]:
    if not PARSED.exists():
        return {}
    doc = json.loads(PARSED.read_text(encoding="utf-8"))
    return {m["id"]: m.get("tag", "") for m in doc.get("messages", []) if m.get("tag")}


def build_row(
    msg: dict,
    month: str,
    cats: dict[str, dict[str, dict]],
    parsed_tags: dict[str, str],
    hw_entries,
    qt_entries,
    model_entries,
) -> dict | None:
    mid = msg["id"]
    content = msg.get("content") or ""
    if is_reddit_repost(content):
        return None

    in_hw = mid in cats["hardware"]
    in_sp = mid in cats["speed"]
    in_qt = mid in cats["quantization"]
    in_mm = mid in cats["model-mentions"]

    hw_ex = cats["hardware"].get(mid, {}).get("extracted", "")
    sp_ex = cats["speed"].get(mid, {}).get("extracted", "")
    qt_ex = cats["quantization"].get(mid, {}).get("extracted", "")
    mm_ex = cats["model-mentions"].get(mid, {}).get("extracted", "")

    tps = extract_tps(content)
    ttft_ms = extract_ttft_ms(content)
    hw_slugs, specific_hw = match_hardware(content, hw_entries)
    qt_slugs = match_registry(content, qt_entries)

    model = parsed_tags.get(mid) or mm_ex
    if not model:
        model = infer_model(content, model_entries)
    tier = assign_tier(
        in_hw=in_hw,
        in_sp=in_sp,
        in_qt=in_qt,
        in_mm=in_mm,
        specific_hw=specific_hw,
        tps=tps,
        ttft_ms=ttft_ms,
        model=model,
    )
    if not tier:
        return None

    return {
        "id": mid,
        "month": month,
        "timestamp": msg.get("timestamp", cats["hardware"].get(mid, {}).get("timestamp", "")),
        "tier": tier,
        # Canvas / manual-review columns
        "model": model or mm_ex,
        "hardware": summarize_hardware(hw_ex, specific_hw),
        "quantization": summarize_quant(qt_ex, qt_slugs),
        "speed": format_speed(tps, ttft_ms, sp_ex),
        "message": content,
        # Structured specs (parsed from message + registry)
        "specs": {
            "model": model or mm_ex,
            "hardware": summarize_hardware(hw_ex, specific_hw),
            "hardware_slugs": hw_slugs,
            "hardware_slugs_specific": specific_hw,
            "quantization": summarize_quant(qt_ex, qt_slugs),
            "quant_slugs": qt_slugs,
            "speed": format_speed(tps, ttft_ms, sp_ex),
            "tps_values": tps,
            "ttft_ms_values": ttft_ms,
        },
        # Raw LLM classifier extractions (when tagged)
        "extracted": {
            "model": mm_ex,
            "hardware": hw_ex,
            "quantization": qt_ex,
            "speed": sp_ex,
        },
        "tagged": {
            "hardware": in_hw,
            "speed": in_sp,
            "quantization": in_qt,
            "model": in_mm,
        },
    }


def main() -> None:
    cats = load_category_index()
    parsed_tags = load_parsed_tags()
    hw_entries = load_hw_entries()
    qt_entries = load_qt_entries()
    model_entries = load_model_entries()

    by_id: dict[str, dict] = {}
    for path in sorted(MONTHLY.glob("202*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        month = doc["meta"]["month"]
        for msg in doc.get("messages", []):
            row = build_row(msg, month, cats, parsed_tags, hw_entries, qt_entries, model_entries)
            if not row:
                continue
            prev = by_id.get(row["id"])
            if not prev or TIER_RANK[row["tier"]] > TIER_RANK[prev["tier"]]:
                by_id[row["id"]] = row

    detected = sorted(by_id.values(), key=lambda r: (r["month"], r["id"]))
    setups = [row for row in detected if is_complete_setup(row)]
    excluded = len(detected) - len(setups)
    tier_counts: dict[str, int] = {}
    for row in setups:
        tier_counts[row["tier"]] = tier_counts.get(row["tier"], 0) + 1

    out_doc = {
        "meta": {
            "description": "Hardware benchmark setups for manual review. Requires resolved model and speed (parsed tok/s, TTFT, or numeric speed text).",
            "purpose": "manual_review",
            "requirements": {
                "model": "Non-empty resolved model (parsed tag, classifier extraction, or registry match)",
                "speed": "Parsed tok/s or TTFT, or speed text containing a numeric value",
            },
            "detected_count": len(detected),
            "excluded_incomplete": excluded,
            "detection": {
                "full": TIER_DESC["full"],
                "hw_speed_model": TIER_DESC["hw_speed_model"],
                "hw_speed_benchmark": TIER_DESC["hw_speed_benchmark"],
                "hw_speed": TIER_DESC["hw_speed"],
                "inferred_model": TIER_DESC["inferred_model"],
                "inferred": TIER_DESC["inferred"],
            },
            "row_fields": {
                "model": "Resolved model (parsed tag, classifier extracted, or inferred from message)",
                "hardware": "Display hardware string (classifier extracted or registry slugs)",
                "quantization": "Display quant string (classifier extracted or registry slugs)",
                "speed": "Display speed string (classifier extracted + parsed tok/s and TTFT)",
                "message": "Full original Discord message",
                "specs": "Structured parsed values: slugs, tps_values, ttft_ms_values",
                "extracted": "Raw LLM classifier extracted strings per category",
                "tier": "Detection confidence tier",
                "tagged": "Which classifier categories tagged this message id",
            },
            "message_count": len(setups),
            "by_tier": tier_counts,
            "built_at": datetime.now(timezone.utc).isoformat(),
        },
        "setups": setups,
    }

    OUT.write_text(json.dumps(out_doc, indent=2), encoding="utf-8")
    LEGACY_OUT.write_text(json.dumps(out_doc, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(setups)} setups, excluded {excluded} incomplete)")
    print(f"Wrote {LEGACY_OUT} (legacy alias)")
    print(json.dumps(tier_counts, indent=2))


if __name__ == "__main__":
    main()
