#!/usr/bin/env python3
"""Roll up hardware mentions by canonical registry slug and month."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from paths import DATA, ROOT
from registry_match import is_reddit_repost, load_registry, match_registry, month_label

HARDWARE_DIR = DATA / "hardware"
REGISTRY = ROOT / "hardware_registry.txt"
OUT = DATA / "hardware-by-slug.json"
OUT_PARSED = DATA / "hardware-parsed.json"
OUT_BY_SLUG = DATA / "hardware-messages-by-slug.json"
SAMPLE_PER_SLUG = 12

GENERIC_SLUGS = {"vram", "ram", "cpu", "gpu", "igpu", "nvidia", "amd"}


def load_messages() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(HARDWARE_DIR.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        month = doc["meta"]["month"]
        for msg in doc.get("messages", []):
            rows.append(
                {
                    "id": msg["id"],
                    "month": month,
                    "timestamp": msg.get("timestamp", ""),
                    "content": msg.get("content", ""),
                    "extracted": msg.get("extracted", ""),
                    "why": msg.get("why", ""),
                }
            )
    return rows


def main() -> None:
    entries = load_registry(REGISTRY)
    messages = load_messages()
    months = sorted({m["month"] for m in messages})
    month_idx = {m: i for i, m in enumerate(months)}

    slug_totals: Counter[str] = Counter()
    slug_monthly: dict[str, list[int]] = defaultdict(lambda: [0] * len(months))
    slug_messages: dict[str, list[dict]] = defaultdict(list)
    parsed_rows: list[dict] = []
    unmapped = 0

    for msg in messages:
        if is_reddit_repost(f"{msg['content']} {msg['extracted']}"):
            continue
        text = f"{msg['content']} {msg['extracted']}"
        slugs = match_registry(text, entries)
        if not slugs:
            unmapped += 1
            continue
        row = {
            "id": msg["id"],
            "month": msg["month"],
            "timestamp": msg["timestamp"],
            "extracted": msg["extracted"],
            "message": msg["content"],
            "slugs": slugs,
            "specific_slugs": [s for s in slugs if s not in GENERIC_SLUGS],
        }
        parsed_rows.append(row)
        for slug in slugs:
            slug_totals[slug] += 1
            slug_monthly[slug][month_idx[msg["month"]]] += 1
            if len(slug_messages[slug]) < SAMPLE_PER_SLUG:
                slug_messages[slug].append(
                    {
                        "id": msg["id"],
                        "month": msg["month"],
                        "extracted": msg["extracted"],
                        "message": msg["content"],
                    }
                )

    specific = [(s, slug_totals[s]) for s in slug_totals if s not in GENERIC_SLUGS]
    specific.sort(key=lambda x: (-x[1], x[0]))
    generic = [(s, slug_totals[s]) for s in slug_totals if s in GENERIC_SLUGS]
    generic.sort(key=lambda x: (-x[1], x[0]))

    slug_order = [s for s, _ in specific] + [s for s, _ in generic]
    matrix = [[slug_monthly[s][i] for i in range(len(months))] for s in slug_order]

    out_doc = {
        "meta": {
            "source": str(HARDWARE_DIR),
            "registry": str(REGISTRY),
            "message_count": len(messages),
            "mapped_messages": len(parsed_rows),
            "unmapped_messages": unmapped,
            "unique_slugs": len(slug_totals),
            "match_method": "Registry alias regex on message content + LLM extracted field (longest alias wins per slug)",
            "built_at": datetime.now(timezone.utc).isoformat(),
        },
        "months": months,
        "monthLabels": [month_label(m) for m in months],
        "slugs": slug_order,
        "slugTotals": [slug_totals[s] for s in slug_order],
        "matrix": matrix,
        "specific_top": [{"slug": s, "total": c} for s, c in specific[:30]],
        "generic_top": [{"slug": s, "total": c} for s, c in generic],
    }

    parsed_doc = {
        "meta": {
            "source": str(HARDWARE_DIR),
            "registry": str(REGISTRY),
            "rows": len(parsed_rows),
            "match_method": "Each row: scan full message + extracted against hardware_registry.txt aliases",
            "built_at": datetime.now(timezone.utc).isoformat(),
        },
        "messages": parsed_rows,
    }

    by_slug_doc = {
        "meta": {
            "description": "Sample messages per hardware slug (first N chronologically per slug file order)",
            "sample_per_slug": SAMPLE_PER_SLUG,
            "built_at": datetime.now(timezone.utc).isoformat(),
        },
        "slugs": {
            slug: {
                "total": slug_totals[slug],
                "samples": slug_messages[slug],
            }
            for slug in slug_order
        },
    }

    OUT.write_text(json.dumps(out_doc, indent=2), encoding="utf-8")
    OUT_PARSED.write_text(json.dumps(parsed_doc, indent=2), encoding="utf-8")
    OUT_BY_SLUG.write_text(json.dumps(by_slug_doc, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(slug_order)} slugs, {len(parsed_rows)} mapped msgs)")
    print(f"Wrote {OUT_PARSED}")
    print(f"Wrote {OUT_BY_SLUG}")
    print(json.dumps({"top_specific": specific[:10], "unmapped": unmapped}, indent=2))


if __name__ == "__main__":
    main()
