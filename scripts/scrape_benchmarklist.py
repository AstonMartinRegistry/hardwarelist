#!/usr/bin/env python3
"""Scrape curated stats from benchmarklist.com model pages.

Prefers visible "rank N of M" text (matches the site UI) over LD+JSON ranks.
Writes data/benchmarklist-stats.json keyed by slug.
"""

from __future__ import annotations

import json
import re
import subprocess
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "benchmarklist-stats.json"

SLUGS = [
    "qwen-qwen3.6-27b",
    "qwen-qwen3.6-35b-a3b",
    "qwen-qwen3.5-27b",
    "qwen-qwen3.5-9b",
    "qwen-qwen3.5-0.8b",
    "qwen-qwen3.5-35b-a3b",
    "qwen-qwen3.5-122b-a10b",
    "qwen-qwen3.5-397b-a17b",
    "qwen-qwen3-coder",
    "qwen-qwen3-coder-next",
    "z-ai-glm-4.5",
    "z-ai-glm-4.7",
    "z-ai-glm-5.2",
    "minimax-minimax-m2.5",
    "google-gemma-4-31b-it",
    "google-gemma-4-26b-a4b-it",
    "google-gemma-4-12b-it",
    "mistral-small-4",
]

PRICING = {
    "qwen-qwen3.6-27b": (0.285, 2.4),
    "qwen-qwen3.6-35b-a3b": (0.14, 1.0),
    "qwen-qwen3.5-27b": (0.195, 1.56),
    "qwen-qwen3.5-9b": (0.1, 0.15),
    "qwen-qwen3.5-35b-a3b": (0.14, 1.0),
    "qwen-qwen3.5-122b-a10b": (0.26, 2.08),
    "qwen-qwen3.5-397b-a17b": (0.385, 2.45),
    "qwen-qwen3-coder": (0.22, 1.8),
    "qwen-qwen3-coder-next": (0.22, 1.8),
    "z-ai-glm-4.5": (0.6, 2.2),
    "z-ai-glm-4.7": (0.4, 1.75),
    "z-ai-glm-5.2": (0.94, 3.0),
    "minimax-minimax-m2.5": (0.12, 0.48),
    "google-gemma-4-31b-it": (0.12, 0.35),
    "google-gemma-4-26b-a4b-it": (0.06, 0.33),
}

# page name -> display label
CURATED = [
    ("Artificial Analysis Intelligence Index", "AA Intelligence Index"),
    ("GPQA Diamond", "GPQA Diamond"),
    ("Humanity's Last Exam", "Humanity's Last Exam"),
    ("SWE-bench Verified", "SWE-bench Verified"),
    ("AA-LCR", "AA-LCR (long context)"),
    ("Terminal-Bench 2.1", "Terminal-Bench 2.1"),
    ("MMMU-Pro", "MMMU-Pro"),
    ("SciCode", "SciCode"),
    ("LiveCodeBench", "LiveCodeBench"),
    ("Artificial Analysis Openness Index", "Openness Index"),
]


def fetch(slug: str) -> str:
    url = f"https://benchmarklist.com/models/{slug}/"
    res = subprocess.run(
        ["curl", "-sS", "-A", "Mozilla/5.0", url],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or f"curl exit {res.returncode}")
    return res.stdout


def flatten(html_text: str) -> str:
    text = unescape(html_text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


def parse_open_weight(flat: str) -> dict:
    ow: dict = {}
    m = re.search(r"(?:Global )?open-weight rank #(\d+)\s*/\s*(\d+)", flat, re.I)
    if not m:
        # Newer pages: "Global vs open weights #88 vs 154"
        m = re.search(r"Global vs open weights #(\d+)\s*vs\s*(\d+)", flat, re.I)
    if m:
        ow["rank"] = int(m.group(1))
        ow["total"] = int(m.group(2))
    m = re.search(
        r"vs open-weight models\s+(\d+) shared benchmarks\s*·\s*(\d+) ranked pairs\s+"
        r"Relative #(\d+)/(\d+)\s*·\s*\d+ ranked pairs\s*·\s*(\d+)W\s*/\s*(\d+)L\s+"
        r"Median ([-−]?[0-9.]+)",
        flat,
        re.I,
    )
    if m:
        ow["shared_benchmarks"] = int(m.group(1))
        ow["peer_pairs"] = int(m.group(2))
        ow["relative_rank"] = int(m.group(3))
        ow["relative_total"] = int(m.group(4))
        ow["peer_wins"] = int(m.group(5))
        ow["peer_losses"] = int(m.group(6))
        ow["peer_median_pctile"] = m.group(7).replace("−", "-")
    return ow


def parse_ldjson(html_text: str) -> tuple[str | None, int | None, dict[str, dict]]:
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html_text, re.S
    )
    name = None
    count = None
    datasets: dict[str, dict] = {}

    def walk(o):
        nonlocal name, count
        if isinstance(o, dict):
            if o.get("@type") == "SoftwareApplication" and o.get("name"):
                name = o.get("name")
                for p in o.get("additionalProperty", []) or []:
                    if p.get("name") in ("Benchmark scores", "Benchmarks covered"):
                        count = p.get("value")
            if o.get("@type") == "Dataset" and o.get("name"):
                ap = o.get("additionalProperty") or []
                headline = ap[0] if ap else {}
                if headline and headline.get("name") != "Rank":
                    datasets[o["name"]] = {
                        "metric": headline.get("name"),
                        "value": headline.get("value"),
                        "unit": headline.get("unitText", ""),
                    }
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for b in blocks:
        try:
            walk(json.loads(b))
        except Exception:
            continue
    return name, count, datasets


def parse_visible_rank(flat: str, page_name: str) -> tuple[int, int] | None:
    # Apostrophe-flexible match for Humanity's Last Exam etc.
    pat = re.escape(page_name).replace(r"\'", r"['’]")
    m = re.search(
        pat + r"\s*·\s*[^·]+?\s*·\s*rank\s+(\d+)\s+of\s+(\d+)",
        flat,
        re.I,
    )
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(pat + r".{0,100}?rank\s+(\d+)\s+of\s+(\d+)", flat, re.I)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def parse_page(html_text: str) -> dict:
    flat = flatten(html_text)
    name, count, datasets = parse_ldjson(html_text)
    stats = []
    for page_name, label in CURATED:
        d = datasets.get(page_name)
        ranks = parse_visible_rank(flat, page_name)
        if not d and not ranks:
            continue
        row = {
            "label": label,
            "metric": (d or {}).get("metric") or "Score",
            "value": (d or {}).get("value"),
            "unit": (d or {}).get("unit") or "",
        }
        if ranks:
            row["rank"], row["total"] = ranks
        elif d:
            # fallback only if UI rank missing
            pass
        stats.append(row)
    # Hardcoded HLE fallback if entity mangling skipped the match but LD+JSON exists
    if not any(s["label"] == "Humanity's Last Exam" for s in stats):
        d = datasets.get("Humanity's Last Exam")
        ranks = parse_visible_rank(flat, "Humanity&#39;s Last Exam") or parse_visible_rank(
            flat, "Humanity's Last Exam"
        )
        if d or ranks:
            row = {
                "label": "Humanity's Last Exam",
                "metric": (d or {}).get("metric") or "Accuracy",
                "value": (d or {}).get("value"),
                "unit": (d or {}).get("unit") or "fraction",
            }
            if ranks:
                row["rank"], row["total"] = ranks
            stats.insert(2, row)

    return {
        "name": name,
        "benchmark_count": count,
        "open_weight": parse_open_weight(flat),
        "stats": stats,
    }


def main() -> None:
    existing: dict = {}
    if OUT.exists():
        existing = json.loads(OUT.read_text(encoding="utf-8"))
    out: dict[str, dict] = dict(existing)
    for slug in SLUGS:
        try:
            page = fetch(slug)
            parsed = parse_page(page)
        except Exception as e:  # noqa: BLE001
            print(f"! {slug}: {e}")
            parsed = existing.get(slug) or {
                "name": None,
                "benchmark_count": None,
                "stats": [],
            }
        pin, pout = PRICING.get(slug, (None, None))
        parsed["price_in"] = pin
        parsed["price_out"] = pout
        out[slug] = parsed
        ow = parsed.get("open_weight") or {}
        ow_txt = (
            f"OSS #{ow['rank']}/{ow['total']}" if ow.get("rank") else "OSS rank n/a"
        )
        print(
            f"{slug}: {parsed.get('name')} · {ow_txt} · "
            f"{len(parsed.get('stats') or [])} stats"
        )
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
