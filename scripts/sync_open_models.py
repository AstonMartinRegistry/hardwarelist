#!/usr/bin/env python3
"""Snapshot BenchmarkList open-source models into data/open-models.json.

  python3 scripts/sync_open_models.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "open-models.json"
UA = "plmlist-open-models/1.0 (+https://plmlist.com)"
DIRECTORY = "https://benchmarklist.com/api/v1/model-directory.json"

# Collapse near-duplicate developer labels.
PROVIDER_ALIASES = {
    "nous research": "Nous",
    "bytedance seed": "ByteDance",
    "bytedance": "ByteDance",
    "mistral ai": "Mistral",
    "moonshot ai": "Moonshot",
    "z.ai": "Z.ai",
    "lg ai research": "LG",
    "thinking machines lab": "Thinking Machines",
    "allen ai": "Allen AI",
    "meituan longcat": "Meituan",
    "rednote hilab": "RedNote",
    "nex-agi": "Nex-AGI",
    "nvidia": "NVIDIA",
    "ibm": "IBM",
    "openai": "OpenAI",
}


def fetch(url: str) -> str:
    proc = subprocess.run(
        ["curl", "-fsSL", "-A", UA, "--max-time", "60", url],
        check=False,
        capture_output=True,
    )
    if proc.returncode != 0 or not proc.stdout:
        err = proc.stderr.decode("utf-8", errors="replace")
        raise SystemExit(f"fetch failed: {url}\n{err}")
    return proc.stdout.decode("utf-8", errors="replace")


def provider_name(raw: str) -> str:
    label = (raw or "").strip() or "Other"
    alias = PROVIDER_ALIASES.get(label.lower())
    return alias or label


def load_rows() -> list[dict]:
    rows: list[dict] = []
    page = 1
    while True:
        url = (
            f"{DIRECTORY}?source=open_source&min-benchmarks=1"
            f"&page={page}&sort=6&direction=desc"
        )
        data = json.loads(fetch(url))
        batch = data.get("rows") or []
        rows.extend(batch)
        pages = int(data.get("total_pages") or 1)
        print(f"  page {page}/{pages} (+{len(batch)})")
        if page >= pages or not batch:
            break
        page += 1
    return rows


def main() -> int:
    print("Fetching BenchmarkList open-source directory…")
    rows = load_rows()
    groups: dict[str, list[dict]] = defaultdict(list)
    seen: set[str] = set()
    for r in rows:
        mid = r.get("i") or r.get("id")
        if not mid or mid in seen:
            continue
        seen.add(mid)
        name = (r.get("n") or r.get("name") or mid).strip()
        groups[provider_name(r.get("d") or r.get("developer") or "")].append(
            {"id": mid, "name": name}
        )

    providers = []
    for name, models in groups.items():
        models.sort(key=lambda m: m["name"].lower())
        providers.append({"name": name, "models": models})
    providers.sort(key=lambda p: (-len(p["models"]), p["name"].lower()))

    payload = {
        "source": "benchmarklist",
        "count": sum(len(p["models"]) for p in providers),
        "providers": providers,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({payload['count']} models, {len(providers)} providers)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
