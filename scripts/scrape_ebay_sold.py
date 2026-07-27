#!/usr/bin/env python3
"""Scrape recent eBay sold prices for hardware items on locallist setups.

eBay now gates Sold Items behind sign-in / bot checks. This script uses a
persistent Chrome profile under .ebay-profile/ so you can log in once:

  python3 scripts/scrape_ebay_sold.py --login
  python3 scripts/scrape_ebay_sold.py
  python3 scripts/scrape_ebay_sold.py --query "AMD BC-250"

Writes: data/ebay-prices.json
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SETUPS = DATA / "hardware-setups.json"
LIKED = (
    ROOT / "canvases" / "hardware-setups-review.canvas.data.json"
)
OUT = DATA / "ebay-prices.json"
PROFILE = ROOT / ".ebay-profile"

SKIP_ITEMS = {
    "gbe",
    "gbE".lower(),
    "ram",
    "ddr4",
    "ddr5",
    "ssd",
    "nvme",
    "pcie",
    "cpu",
    "gpu",
    "igpu",
}


def parse_price(text: str) -> float | None:
    if not text:
        return None
    # Prefer the first hard price; ignore ranges' high end for "to"
    cleaned = text.replace(",", "")
    # "$123.45" or "US $123.45" or "$100.00 to $200.00"
    nums = re.findall(r"\$\s*(\d+(?:\.\d+)?)", cleaned)
    if not nums:
        return None
    return float(nums[0])


def split_hardware_items(hardware: str) -> list[str]:
    raw = hardware or ""
    parts = re.split(r"\s*(?:,|/|\+|&| and )\s*", raw)
    items: list[str] = []
    for part in parts:
        part = re.sub(r"\s+", " ", part).strip(" .;")
        if len(part) < 3:
            continue
        # Drop bare capacity / generic tokens
        low = part.lower()
        if low in SKIP_ITEMS:
            continue
        if re.fullmatch(r"\d+\s*gb", low):
            continue
        if part not in items:
            items.append(part)
    return items


def collect_queries(limit: int | None = None) -> list[str]:
    liked_ids: set[str] = set()
    if LIKED.exists():
        doc = json.loads(LIKED.read_text(encoding="utf-8"))
        liked_ids = {mid for mid, on in doc.get("liked", {}).items() if on}

    setups = json.loads(SETUPS.read_text(encoding="utf-8")).get("setups", [])
    if liked_ids:
        setups = [r for r in setups if r.get("id") in liked_ids]

    seen: list[str] = []
    for row in setups:
        for item in split_hardware_items(row.get("hardware") or ""):
            if item not in seen:
                seen.append(item)
    if limit:
        seen = seen[:limit]
    return seen


def summarize(prices: list[float]) -> dict:
    vals = sorted(prices)
    return {
        "count": len(vals),
        "min": round(vals[0], 2),
        "median": round(statistics.median(vals), 2),
        "max": round(vals[-1], 2),
        "recent": [round(v, 2) for v in vals[:8]],
    }


def scrape_query(page, query: str, max_items: int = 20) -> dict:
    url = (
        "https://www.ebay.com/sch/i.html?"
        + f"_nkw={query.replace(' ', '+')}&_ipg=60"
    )
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)

    # Prefer Sold Items when available (may redirect to sign-in).
    sold_clicked = False
    for sel in ("text=Sold Items", "text=Sold items"):
        loc = page.locator(sel).first
        if loc.count() == 0:
            continue
        try:
            loc.click(timeout=4000)
            sold_clicked = True
            page.wait_for_timeout(3500)
            break
        except PlaywrightTimeout:
            continue

    title = page.title()
    current = page.url
    if "signin.ebay.com" in current or "Sign in" in title:
        return {
            "query": query,
            "ok": False,
            "error": "sign_in_required",
            "url": current,
            "mode": "sold" if sold_clicked else "active",
            "items": [],
        }
    if "Security Measure" in title:
        return {
            "query": query,
            "ok": False,
            "error": "security_measure",
            "url": current,
            "mode": "sold" if sold_clicked else "active",
            "items": [],
        }

    mode = "sold" if ("LH_Sold=1" in current or sold_clicked) else "active"
    cards = page.locator("li.s-item").all()
    items: list[dict] = []
    for card in cards:
        if len(items) >= max_items:
            break
        try:
            t = card.locator(".s-item__title").inner_text(timeout=800).strip()
            p = card.locator(".s-item__price").inner_text(timeout=800).strip()
        except Exception:
            continue
        if not t or t.lower().startswith("shop on ebay"):
            continue
        price = parse_price(p)
        if price is None:
            continue
        href = None
        try:
            href = card.locator("a.s-item__link").get_attribute("href")
        except Exception:
            pass
        items.append({"title": t, "price_text": p, "price": price, "url": href})

    prices = [i["price"] for i in items]
    result = {
        "query": query,
        "ok": bool(prices),
        "error": None if prices else "no_prices_parsed",
        "url": current,
        "mode": mode,
        "items": items,
        "stats": summarize(prices) if prices else None,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }
    return result


def run_login(wait_seconds: int) -> None:
    PROFILE.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE),
            headless=False,
            channel="chrome",
            viewport={"width": 1400, "height": 1000},
            locale="en-US",
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(
            "https://www.ebay.com/signin/",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        print(
            f"Log into eBay in the opened Chrome window. "
            f"Waiting up to {wait_seconds}s…"
        )
        page.wait_for_timeout(wait_seconds * 1000)
        # Smoke: can we open sold search without bouncing to sign-in?
        page.goto(
            "https://www.ebay.com/sch/i.html?_nkw=RTX+4090&LH_Sold=1&LH_Complete=1",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(3000)
        print("After login check title:", page.title())
        print("URL:", page.url)
        context.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--login", action="store_true", help="Open Chrome to sign into eBay")
    ap.add_argument("--login-wait", type=int, default=120, help="Seconds to wait while logging in")
    ap.add_argument("--query", action="append", default=[], help="Only scrape this query (repeatable)")
    ap.add_argument("--limit", type=int, default=0, help="Max unique hardware queries from setups")
    ap.add_argument("--delay", type=float, default=2.5, help="Delay between queries")
    ap.add_argument("--headed", action="store_true", default=True, help="Show browser (default on)")
    ap.add_argument("--headless", action="store_true", help="Run headless (usually blocked by eBay)")
    args = ap.parse_args()

    if args.login:
        run_login(args.login_wait)
        return

    queries = args.query or collect_queries(limit=args.limit or None)
    if not queries:
        raise SystemExit("No hardware queries found")

    PROFILE.mkdir(parents=True, exist_ok=True)
    existing = {}
    if OUT.exists():
        existing = json.loads(OUT.read_text(encoding="utf-8"))

    results = existing.get("items", {})
    meta_errors: list[str] = []

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE),
            headless=bool(args.headless),
            channel="chrome",
            viewport={"width": 1400, "height": 1000},
            locale="en-US",
        )
        page = context.pages[0] if context.pages else context.new_page()

        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] {query}")
            try:
                row = scrape_query(page, query)
            except Exception as e:
                row = {
                    "query": query,
                    "ok": False,
                    "error": f"exception:{type(e).__name__}:{e}",
                    "items": [],
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }
            results[query] = row
            if row.get("ok"):
                stats = row["stats"]
                print(
                    f"  {row['mode']}: n={stats['count']} "
                    f"median=${stats['median']:.0f} "
                    f"range=${stats['min']:.0f}–${stats['max']:.0f}"
                )
            else:
                print(f"  FAIL: {row.get('error')}")
                meta_errors.append(f"{query}:{row.get('error')}")
            # Persist incrementally
            OUT.write_text(
                json.dumps(
                    {
                        "meta": {
                            "built_at": datetime.now(timezone.utc).isoformat(),
                            "query_count": len(results),
                            "errors": meta_errors[-20:],
                            "note": (
                                "Sold comps usually require an eBay login in "
                                ".ebay-profile (run with --login first)."
                            ),
                        },
                        "items": results,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            if i < len(queries):
                time.sleep(args.delay)

        context.close()

    ok = sum(1 for v in results.values() if v.get("ok"))
    print(f"Wrote {OUT} ({ok}/{len(results)} ok)")


if __name__ == "__main__":
    main()
