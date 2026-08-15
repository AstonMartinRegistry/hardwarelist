#!/usr/bin/env python3
"""Sync BenchmarkList open-weight ranks into public.setups (Supabase).

The site renders cards from the DB via GET /api/setups — ranks must live there,
not in static HTML.

  python3 scripts/sync_ranks_to_setups.py
  python3 scripts/sync_ranks_to_setups.py --skip-tips
  python3 scripts/sync_ranks_to_setups.py --dry-run

Requires .env: NEXT_PUBLIC_SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sync_benchmarklist import (  # noqa: E402
    CAPABILITY_URL,
    MODEL_PAGE,
    MODELS_URL,
    MANUAL_SLUGS,
    build_rank_field,
    fetch,
    match_model,
    manual_slug,
    parse_capability,
    parse_tip_metrics,
)


def load_env() -> None:
    for name in (".env", ".env.local"):
        path = ROOT / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            t = line.strip()
            if not t or t.startswith("#") or "=" not in t:
                continue
            k, v = t.split("=", 1)
            k, v = k.strip(), v.strip()
            if (v.startswith('"') and v.endswith('"')) or (
                v.startswith("'") and v.endswith("'")
            ):
                v = v[1:-1]
            os.environ.setdefault(k, v)


def supabase_config() -> tuple[str, str]:
    url = (
        os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
        or os.environ.get("SUPABASE_URL")
        or ""
    ).rstrip("/")
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_ANON_KEY")
        or ""
    )
    if not url or not key:
        raise SystemExit("Missing NEXT_PUBLIC_SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY")
    return url, key


def sb_request(
    method: str, path: str, *, body: object | None = None, prefer: str = ""
) -> object:
    url, key = supabase_config()
    full = f"{url}/rest/v1/{path}"
    cmd = [
        "curl",
        "-fsSL",
        "-X",
        method,
        "-H",
        f"apikey: {key}",
        "-H",
        f"Authorization: Bearer {key}",
        "-H",
        "Content-Type: application/json",
        "-H",
        "Accept: application/json",
    ]
    if prefer:
        cmd.extend(["-H", f"Prefer: {prefer}"])
    if body is not None:
        cmd.extend(["-d", json.dumps(body)])
    cmd.append(full)
    proc = subprocess.run(cmd, check=False, capture_output=True)
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase {method} {path} failed: {err or proc.returncode}")
    text = proc.stdout.decode("utf-8", errors="replace")
    return json.loads(text) if text else None


def fetch_setups() -> list[dict]:
    rows = sb_request(
        "GET",
        "setups?select=id,model,version_label,rank,payload&order=model.asc&limit=500",
    )
    return list(rows or [])


def patch_setup(row_id: str, patch: dict) -> None:
    sb_request(
        "PATCH",
        f"setups?id=eq.{row_id}",
        body=patch,
        prefer="return=minimal",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-tips", action="store_true")
    ap.add_argument("--sleep", type=float, default=0.15)
    args = ap.parse_args()

    load_env()

    # Prefer Qwen3.8 when it appears on BenchmarkList
    MANUAL_SLUGS.setdefault("qwen3.8-27b", "qwen-qwen3.8-27b")
    MANUAL_SLUGS.setdefault("qwen3.8", "qwen-qwen3.8-27b")

    print("Fetching capability index…")
    open_map, total = parse_capability(fetch(CAPABILITY_URL))
    print(f"  open-weight models ranked: {len(open_map)} (denom {total})")

    print("Fetching models registry…")
    registry = json.loads(fetch(MODELS_URL))["models"]
    print(f"  registry models: {len(registry)}")

    setups = fetch_setups()
    print(f"Setups in DB: {len(setups)}")

    # Match once per distinct model name
    tip_cache: dict[str, dict] = {}
    page_cache: dict[str, bool] = {}
    model_match: dict[str, tuple[str | None, int | None, str | None]] = {}
    actions: list[str] = []

    unique_models = sorted({str(s.get("model") or "") for s in setups if s.get("model")})
    for name in unique_models:
        forced = manual_slug(name)
        slug = None
        display = name
        if forced and forced in open_map:
            slug, display = forced, open_map[forced].name
        else:
            hit = match_model(name, registry, open_map, page_cache)
            if hit:
                slug, display = hit

        if not slug:
            actions.append(f"SKIP  {name}: no BenchmarkList match")
            model_match[name] = (None, None, None)
            continue

        tip_html = None
        rank = open_map[slug].rank if slug in open_map else None
        if slug in open_map:
            display = open_map[slug].name

        if not args.skip_tips and slug in open_map:
            if slug not in tip_cache:
                try:
                    tip_cache[slug] = parse_tip_metrics(
                        fetch(MODEL_PAGE.format(slug=slug))
                    )
                    time.sleep(args.sleep)
                except Exception as e:  # noqa: BLE001
                    actions.append(f"WARN  {name}: tip fetch failed ({e})")
                    tip_cache[slug] = {}
            metrics = tip_cache.get(slug) or {}
            tip_html = build_rank_field(
                slug, display, int(rank), total, metrics or None, None
            )

        if rank is not None:
            actions.append(f"RANK  {name}: #{rank}/{total} ({slug})")
        else:
            actions.append(f"LINK  {name}: {slug} (no open-weight rank)")
        model_match[name] = (slug, rank, tip_html)

    updated = 0
    for row in setups:
        name = str(row.get("model") or "")
        slug, rank, tip_html = model_match.get(name, (None, None, None))
        payload = dict(row.get("payload") or {})
        if slug:
            payload["benchmarklist_slug"] = slug
            payload["benchmarklist_total"] = total
        if tip_html:
            payload["tip_html"] = tip_html
        elif rank is None and "tip_html" in payload:
            # keep old tip unless we explicitly cleared rank
            pass

        patch: dict = {"payload": payload, "updated_at": _now()}
        if rank is not None:
            patch["rank"] = rank
        elif row.get("rank") is not None and slug and slug not in open_map:
            patch["rank"] = None

        prev = row.get("rank")
        if prev == patch.get("rank", prev) and payload == (row.get("payload") or {}):
            continue

        actions.append(
            f"WRITE {name} id={row['id'][:8]}… rank {prev} → {patch.get('rank', prev)}"
        )
        if not args.dry_run:
            patch_setup(row["id"], patch)
        updated += 1

    print("\nActions:")
    for line in actions:
        print(" ", line)
    print(f"\n{'Would update' if args.dry_run else 'Updated'} {updated} setup row(s).")
    return 0


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
