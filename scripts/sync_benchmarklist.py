#!/usr/bin/env python3
"""Sync open-weight ranks + BenchmarkList links in index.html / locallist.html.

Pulls the Capability Index open-weight table and (optionally) per-model tip
metrics from BenchmarkList, then rewrites rank fields in the local HTML.
Unlinked cards are matched against the public models registry.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
LOCALLIST = ROOT / "locallist.html"

UA = "plmlist-benchmarklist-sync/1.0 (+https://plmlist.com)"
CAPABILITY_URL = "https://benchmarklist.com/capability-index/"
MODELS_URL = "https://benchmarklist.com/api/v1/models.json"
MODEL_PAGE = "https://benchmarklist.com/models/{slug}/"

TIP_METRICS = [
    ("AA Index", ["Artificial Analysis Intelligence Index"], "pts"),
    ("GPQA", ["GPQA Diamond"], "%"),
    ("HLE", ["Humanity's Last Exam", "Humanity’s Last Exam"], "%"),
    ("SWE-bench", ["SWE-bench Verified"], "%"),
    ("AA-LCR", ["AA-LCR"], ""),
    ("Terminal", ["Terminal-Bench 2.1", "Terminal-Bench 2.0", "Terminal-Bench Hard"], "%"),
    ("MMMU-Pro", ["MMMU-Pro"], ""),
    ("SciCode", ["SciCode"], "%"),
    ("LiveCode", ["LiveCodeBench", "LiveCodeBench Pro", "LiveCode"], "%"),
]

# Card title / version hints → canonical BenchmarkList model_id.
# Used when fuzzy matching picks a Closed/API stub or a 404 registry row.
MANUAL_SLUGS = {
    "gemma-4-e2b": "google-gemma-4-e2b-it",
    "gemma-4-26b-a4b": "google-gemma-4-26b-a4b-it",
    "gemma-4-31b": "google-gemma-4-31b-it",
    "gemma-4-12b": "google-gemma-4-12b-it",
    "mistral-small-4-119b": "mistralai-mistral-small-2603",
    "mistral-small-4": "mistralai-mistral-small-2603",
}


@dataclass
class OpenRank:
    rank: int
    name: str
    availability: str


def fetch(url: str, timeout: int = 60) -> str:
    """Fetch URL text. Prefer curl (reliable certs on macOS), fall back to urllib."""
    try:
        proc = subprocess.run(
            [
                "curl",
                "-fsSL",
                "-A",
                UA,
                "--max-time",
                str(timeout),
                url,
            ],
            check=False,
            capture_output=True,
        )
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="replace")
            raise urllib.error.HTTPError(url, proc.returncode, err or "curl failed", hdrs=None, fp=None)
    except FileNotFoundError:
        pass

    ctx = ssl.create_default_context()
    try:
        import certifi  # type: ignore

        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        # Local Python installs sometimes lack a CA bundle; last resort.
        ctx = ssl._create_unverified_context()  # noqa: SLF001

    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


def page_ok(slug: str, cache: dict[str, bool]) -> bool:
    if slug in cache:
        return cache[slug]
    url = MODEL_PAGE.format(slug=slug)
    try:
        proc = subprocess.run(
            ["curl", "-sL", "-A", UA, "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "20", url],
            check=False,
            capture_output=True,
            text=True,
        )
        ok = proc.stdout.strip() == "200"
    except FileNotFoundError:
        try:
            fetch(url, timeout=20)
            ok = True
        except Exception:
            ok = False
    cache[slug] = ok
    return ok


def parse_capability(html: str) -> tuple[dict[str, OpenRank], int]:
    idx = html.find('id="capability-table"')
    if idx < 0:
        raise RuntimeError("capability-table not found")
    sec = html[idx:]
    row_re = re.compile(r"<tr([^>]*)>(.*?)</tr>", re.S)
    link_re = re.compile(r'href="/models/([^"/]+)/?"[^>]*>([^<]+)<')
    cell_re = re.compile(r'data-rank-([a-z]+)="(\d+)"')
    avail_re = re.compile(r'data-filter-availability="([^"]+)"')

    open_map: dict[str, OpenRank] = {}
    for attrs, body in row_re.findall(sec):
        link = link_re.search(body)
        if not link:
            continue
        ranks = dict(cell_re.findall(attrs + body))
        if "open" not in ranks:
            continue
        avail = avail_re.search(attrs)
        open_map[link.group(1)] = OpenRank(
            rank=int(ranks["open"]),
            name=re.sub(r"\s+", " ", link.group(2)).strip(),
            availability=avail.group(1) if avail else "Open",
        )
    if not open_map:
        raise RuntimeError("no open-weight ranks parsed")
    total = max(r.rank for r in open_map.values())
    return open_map, total


_STOP = {
    "it",
    "qat",
    "gguf",
    "instruct",
    "ud",
    "iq1",
    "iq2",
    "iq3",
    "iq4",
    "xs",
    "xxs",
    "xl",
    "mtp",
    "bf16",
    "fp8",
    "uncensored",
    "balanced",
}


def normalize_tokens(text: str) -> list[str]:
    text = text.lower().replace("×", "x")
    text = text.replace("gemma4", "gemma-4").replace("gemma 4", "gemma-4")
    text = re.sub(r"[^a-z0-9.]+", " ", text)
    parts = []
    for p in text.split():
        if not p or p in _STOP:
            continue
        # Drop single-letter junk from quants like IQ1_M → "m"
        if len(p) < 2:
            continue
        parts.append(p)
    return parts


def score_match(query: str, model_id: str, name: str, aliases: list[str]) -> float:
    q = normalize_tokens(query)
    if not q:
        return 0.0
    blob_parts = normalize_tokens(" ".join([model_id, name, *aliases]))
    blob = set(blob_parts)
    if not blob:
        return 0.0

    # All query tokens present
    hit = sum(1 for t in q if t in blob or any(t in b or b in t for b in blob))
    score = hit / len(q)

    # Candidate is a prefix/core of the query (e.g. mistral-small-4 ⊂ mistral-small-4-119b)
    cand = normalize_tokens(model_id.replace("_", "-"))
    if cand and all(t in q or any(t in qt or qt in t for qt in q) for t in cand):
        score = max(score, 0.9)

    # Prefer canonical vendor slugs
    mid = model_id.lower()
    if mid.startswith(("google-", "qwen-", "z-ai-", "minimax-", "mistral-", "deepreinforce-ai-")):
        score += 0.08
    if mid.endswith("-it") and "it" not in q:
        score += 0.03
    # Penalize obvious variants
    for bad in ("nothink", "uncensored", "heretic", "abliterated", "fp8", "draft"):
        if bad in mid:
            score -= 0.25
    # Strong bonus for near-exact id / name containment
    qcompact = re.sub(r"[^a-z0-9]+", "", query.lower())
    idcompact = re.sub(r"[^a-z0-9]+", "", model_id.lower())
    namecompact = re.sub(r"[^a-z0-9]+", "", name.lower())
    if qcompact and (qcompact in idcompact or idcompact in qcompact):
        score += 0.35
    if qcompact and (qcompact in namecompact or namecompact in qcompact):
        score += 0.25
    return score


def manual_slug(query: str) -> str | None:
    q = query.lower().strip()
    if q in MANUAL_SLUGS:
        return MANUAL_SLUGS[q]
    # version strings like Mistral-Small-4-119B-2603-UD-IQ4_XS
    for key, slug in MANUAL_SLUGS.items():
        if key in q:
            return slug
    if "mistral" in q and "small" in q and ("119" in q or "2603" in q or re.search(r"small-4\b", q)):
        return "mistralai-mistral-small-2603"
    if "gemma" in q and "e2b" in q:
        return "google-gemma-4-e2b-it"
    if "gemma" in q and "26b" in q and "a4b" in q:
        return "google-gemma-4-26b-a4b-it"
    return None


def match_model(
    query: str,
    registry: list[dict],
    open_map: dict[str, OpenRank],
    page_cache: dict[str, bool] | None = None,
) -> tuple[str, str] | None:
    """Return (slug, display_name) or None."""
    forced = manual_slug(query)
    if forced:
        if forced in open_map:
            return forced, open_map[forced].name
        for m in registry:
            if m["model_id"] == forced:
                if page_cache is None or page_ok(forced, page_cache) or forced in open_map:
                    return forced, m.get("name") or forced
        if page_cache is None or page_ok(forced, page_cache):
            return forced, forced

    q_tokens = normalize_tokens(query)
    # Distinctive anchors (e.g. ornith, gemma, qwen) must appear in a candidate.
    anchors = [t for t in q_tokens if len(t) >= 4 and not re.fullmatch(r"\d+(\.\d+)?", t)]

    scored: list[tuple[float, str, str]] = []
    for m in registry:
        slug = m["model_id"]
        name = m.get("name") or slug
        aliases = m.get("aliases") or []
        blob = " ".join([slug, name, *aliases]).lower()
        if anchors and not any(a in blob for a in anchors):
            continue
        s = score_match(query, slug, name, aliases)
        if slug in open_map:
            s += 0.35  # strongly prefer open-weight ranked models
            name = open_map[slug].name
        if s >= 0.85:
            scored.append((s, slug, name))
    scored.sort(reverse=True)

    # Prefer any open-ranked candidate in the top set before Closed/API stubs.
    open_first = [x for x in scored[:20] if x[1] in open_map]
    ordered = open_first + [x for x in scored[:20] if x[1] not in open_map]

    for s, slug, name in ordered:
        if page_cache is None:
            return slug, name
        if slug in open_map or page_ok(slug, page_cache):
            return slug, name
    return None


def parse_tip_metrics(model_html: str) -> dict[str, tuple[str, str]]:
    """Map tip label -> (score_text, #rank/total)."""
    # Current BenchmarkList aria-labels look like:
    #   "GPQA Diamond · 84.2% · rank 88 of 448 · 81st percentile"
    # Legacy format (still accepted):
    #   "GPQA Diamond vs X: ... 37.05 (#91/464) vs ..."
    aria = re.findall(r'aria-label="([^"]+)"', model_html)
    found: dict[str, tuple[str, str]] = {}
    for label, names, suffix in TIP_METRICS:
        if label in found:
            continue
        for aria_text in aria:
            for name in names:
                if not (
                    aria_text.startswith(name + " · ")
                    or aria_text.startswith(name + " vs ")
                ):
                    continue

                # New format: Name · SCORE · rank N of T · …
                m_new = re.search(
                    r"·\s*([\d,]+(?:\.\d+)?)\s*(%|pts)?\s*·\s*rank\s+(\d+)\s+of\s+(\d+)",
                    aria_text,
                    flags=re.I,
                )
                if m_new:
                    val = m_new.group(1).replace(",", "")
                    unit = (m_new.group(2) or "").strip()
                    rank = f"#{m_new.group(3)}/{m_new.group(4)}"
                else:
                    # Legacy comparison aria-label
                    m = re.search(
                        r"\b(\d+(?:\.\d+)?)\s*(%|pts)?\s*\(#(\d+)/(\d+)\)",
                        aria_text,
                    )
                    if not m:
                        continue
                    val = m.group(1)
                    unit = m.group(2) or ""
                    rank = f"#{m.group(3)}/{m.group(4)}"

                if suffix == "pts":
                    try:
                        score = f"{float(val):.1f} pts"
                    except ValueError:
                        score = f"{val} pts"
                elif suffix == "%":
                    try:
                        f = float(val)
                        score = f"{f:.0f}%" if f.is_integer() else f"{f:.1f}%"
                    except ValueError:
                        score = f"{val}%"
                else:
                    try:
                        f = float(val)
                        score = f"{f:.0f}" if f.is_integer() else f"{f:.1f}"
                        if unit == "%":
                            pass
                    except ValueError:
                        score = val
                found[label] = (score, rank)
                break
            if label in found:
                break
    return found


def format_score_for_existing(old_score_html: str, new_score: str) -> str:
    """Prefer keeping old unit style when possible."""
    old = re.sub(r"<[^>]+>", "", old_score_html).strip()
    old_has_pts = "pts" in old
    old_has_pct = "%" in old
    num = re.search(r"\d+(?:\.\d+)?", new_score)
    if not num:
        return new_score
    val = num.group(0)
    if old_has_pts or new_score.endswith("pts"):
        try:
            return f"{float(val):.1f} pts"
        except ValueError:
            return f"{val} pts"
    if old_has_pct or new_score.endswith("%"):
        try:
            f = float(val)
            return f"{f:.0f}%" if f.is_integer() else f"{f:.1f}%"
        except ValueError:
            return f"{val}%"
    try:
        f = float(val)
        return f"{f:.0f}" if f.is_integer() else f"{f:.1f}"
    except ValueError:
        return val


def build_tip_list(metrics: dict[str, tuple[str, str]], existing_keys: list[str] | None) -> str:
    keys = existing_keys or [k for k, _, _ in TIP_METRICS if k in metrics]
    rows = []
    for key in keys:
        if key not in metrics:
            continue
        score, rank = metrics[key]
        rows.append(
            f'<div class="tip-row"><span class="tip-k">{escape(key)}</span>'
            f'<span class="tip-v">{escape(score)} <span class="tip-rank">{escape(rank)}</span></span></div>'
        )
    # If nothing matched existing keys, fall back to default order
    if not rows:
        for key, _, _ in TIP_METRICS:
            if key not in metrics:
                continue
            score, rank = metrics[key]
            rows.append(
                f'<div class="tip-row"><span class="tip-k">{escape(key)}</span>'
                f'<span class="tip-v">{escape(score)} <span class="tip-rank">{escape(rank)}</span></span></div>'
            )
    return "".join(rows)


def build_rank_field(
    slug: str,
    display_name: str,
    rank: int,
    total: int,
    tip_metrics: dict[str, tuple[str, str]] | None = None,
    existing_tip_keys: list[str] | None = None,
) -> str:
    url = MODEL_PAGE.format(slug=slug)
    tip_list = build_tip_list(tip_metrics or {}, existing_tip_keys)
    return (
        f'<div class="rf"><span class="rl">rank</span><span class="rv">'
        f'<span class="hovtxt"><span class="rank-n">#{rank}</span>'
        f'<span class="rank-t"> / {total}</span> '
        f'<span class="rank-note">open-weight</span>'
        f'<span class="tip tip-rich">'
        f'<div class="tip-banner"><a class="tip-head" href="{url}" target="_blank" rel="noopener">'
        f"{escape(display_name)} →</a></div>"
        f'<div class="tip-body"><div class="tip-hero">'
        f'<span class="tip-hero-k">open-weight</span>'
        f'<span class="tip-hero-v">#{rank}<span class="tip-hero-t"> / {total}</span></span>'
        f"</div><div class=\"tip-list\">{tip_list}</div></div></span></span> "
        f'<a class="rank-src" href="{url}" target="_blank" rel="noopener">benchmarklist</a>'
        f"</span></div>"
    )


def iter_cards(html: str) -> list[tuple[int, int, str]]:
    cards = []
    for m in re.finditer(r'<div class="setup setup-rich\b', html):
        start = m.start()
        j = start
        depth = 0
        end = None
        while j < len(html):
            no, nc = html.find("<div", j), html.find("</div>", j)
            if nc < 0:
                break
            if no >= 0 and no < nc:
                depth += 1
                j = no + 4
            else:
                depth -= 1
                j = nc + 6
                if depth == 0:
                    end = j
                    break
        if end is None:
            continue
        cards.append((start, end, html[start:end]))
    return cards


def update_existing_rank_field(
    card: str,
    slug: str,
    display_name: str,
    rank: int,
    total: int,
    tip_metrics: dict[str, tuple[str, str]] | None,
) -> str:
    url = MODEL_PAGE.format(slug=slug)

    card = re.sub(r'data-rank="\d+"', f'data-rank="{rank}"', card, count=1)
    card = re.sub(r'(<span class="rank-n">)#\d+(</span>)', rf"\g<1>#{rank}\2", card)
    card = re.sub(r'(<span class="rank-t">) / \d+(</span>)', rf"\g<1> / {total}\2", card)
    card = re.sub(
        r'(<span class="tip-hero-v">)#\d+(<span class="tip-hero-t">) / \d+(</span>)',
        rf"\g<1>#{rank}\2 / {total}\3",
        card,
        count=1,
    )

    # Keep slug/url in sync if redirected/matched
    card = re.sub(
        r'https://benchmarklist\.com/models/[^"/]+/?',
        url,
        card,
    )
    card = re.sub(
        r'(<a class="tip-head"[^>]*>)([^<]*?)( →</a>)',
        rf"\g<1>{escape(display_name)}\3",
        card,
        count=1,
    )

    if tip_metrics:
        def repl_row(match: re.Match[str]) -> str:
            key = match.group(1)
            if key not in tip_metrics:
                return match.group(0)
            score, rnk = tip_metrics[key]
            old_inner = match.group(2)
            score = format_score_for_existing(old_inner, score)
            return (
                f'<div class="tip-row"><span class="tip-k">{key}</span>'
                f'<span class="tip-v">{score} <span class="tip-rank">{rnk}</span></span></div>'
            )

        card = re.sub(
            r'<div class="tip-row"><span class="tip-k">([^<]+)</span><span class="tip-v">(.*?)</span></div>',
            repl_row,
            card,
            flags=re.S,
        )
    return card


def insert_rank_field(card: str, rank_html: str) -> str:
    # Prefer after context; else after version; else before hardware.
    for anchor in (
        r'(<div class="rf"><span class="rl">context</span><span class="rv">.*?</span></div>)',
        r'(<div class="rf"><span class="rl">version</span><span class="rv">.*?</span></div>)',
    ):
        m = re.search(anchor, card, re.S)
        if m:
            i = m.end()
            return card[:i] + rank_html + card[i:]
    m = re.search(r'<div class="rf"><span class="rl">hardware</span>', card)
    if m:
        return card[: m.start()] + rank_html + card[m.start() :]
    return card


def extract_card_name(card: str) -> str:
    m = re.search(r'class="model-name">([^<]+)', card)
    return m.group(1).strip() if m else ""


def extract_slug(card: str) -> str | None:
    m = re.search(r'https://benchmarklist\.com/models/([^"/]+)/?', card)
    return m.group(1) if m else None


def extract_tip_keys(card: str) -> list[str]:
    return re.findall(r'class="tip-k">([^<]+)', card)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="print actions without writing")
    ap.add_argument("--skip-tips", action="store_true", help="only sync open-weight ranks/links")
    ap.add_argument("--sleep", type=float, default=0.15, help="delay between model page fetches")
    args = ap.parse_args()

    print("Fetching capability index…")
    cap_html = fetch(CAPABILITY_URL)
    open_map, total = parse_capability(cap_html)
    print(f"  open-weight models ranked: {len(open_map)} (total denominator {total})")

    print("Fetching models registry…")
    registry = json.loads(fetch(MODELS_URL))["models"]
    print(f"  registry models: {len(registry)}")

    html = INDEX.read_text(encoding="utf-8")
    cards = iter_cards(html)
    print(f"Cards on page: {len(cards)}")

    tip_cache: dict[str, dict[str, tuple[str, str]]] = {}
    page_cache: dict[str, bool] = {}
    actions: list[str] = []
    new_html_parts: list[str] = []
    cursor = 0

    for start, end, card in cards:
        new_html_parts.append(html[cursor:start])
        name = extract_card_name(card)
        slug = extract_slug(card)
        matched_via = "existing" if slug else None
        display = name

        # Prefer manual/open-weight canonical slug over Closed/API stubs.
        forced = manual_slug(name) or manual_slug(
            re.search(r'title="([^"]+)"', card).group(1)
            if re.search(r'title="([^"]+)"', card)
            else ""
        )
        if forced and forced in open_map and slug != forced:
            actions.append(f"WARN  {name}: replacing {slug or '—'} with canonical {forced}")
            slug = forced
            matched_via = "manual"

        if slug and not page_ok(slug, page_cache) and slug not in open_map:
            actions.append(f"WARN  {name}: existing slug {slug} is not a live page; rematching")
            slug = None
            matched_via = None

        if not slug:
            hit = match_model(name, registry, open_map, page_cache)
            if not hit:
                # Also try matching on version title text
                ver = re.search(r'title="([^"]+)"', card)
                if ver:
                    hit = match_model(ver.group(1), registry, open_map, page_cache)
            if hit:
                slug, display = hit
                matched_via = matched_via or "matched"
            else:
                actions.append(f"SKIP  {name}: no BenchmarkList match")
                # Drop any rank rows / orphan tip fragments left by prior runs
                cleaned = card
                for m in reversed(list(re.finditer(r'<div class="rf"><span class="rl">rank</span>', cleaned))):
                    i = m.start()
                    j = i
                    depth = 0
                    while j < len(cleaned):
                        no, nc = cleaned.find("<div", j), cleaned.find("</div>", j)
                        if nc < 0:
                            break
                        if no >= 0 and no < nc:
                            depth += 1
                            j = no + 4
                        else:
                            depth -= 1
                            j = nc + 6
                            if depth == 0:
                                cleaned = cleaned[:i] + cleaned[j:]
                                break
                if '<div class="tip-list">' in cleaned and "tip-rich" not in cleaned:
                    cleaned = re.sub(
                        r'<div class="tip-list">.*?</div>(?:\s*</div></span></span>\s*)?'
                        r'(?:<a class="rank-src"[^>]*>benchmarklist</a></span></div>)?',
                        "",
                        cleaned,
                        count=1,
                        flags=re.S,
                    )
                cleaned = re.sub(r'\s*data-rank="\d+"', "", cleaned, count=1)
                new_html_parts.append(cleaned)
                cursor = end
                continue
        else:
            display = open_map[slug].name if slug in open_map else name

        # If slug missing from open map, try rematch toward an open-ranked model
        if slug not in open_map:
            hit = match_model(name, registry, open_map, page_cache)
            if not hit:
                ver = re.search(r'title="([^"]+)"', card)
                if ver:
                    hit = match_model(ver.group(1), registry, open_map, page_cache)
            if hit and hit[0] in open_map:
                old = slug
                slug, display = hit
                matched_via = f"rematched from {old}"
            elif hit and hit[0] != slug:
                old = slug
                slug, display = hit
                matched_via = f"rematched from {old}"

        tip_metrics = None
        if not args.skip_tips:
            if slug not in tip_cache:
                try:
                    page = fetch(MODEL_PAGE.format(slug=slug))
                    tip_cache[slug] = parse_tip_metrics(page)
                    time.sleep(args.sleep)
                except urllib.error.HTTPError as e:
                    actions.append(f"WARN  {name}: tip fetch HTTP {e.code} for {slug}")
                    tip_cache[slug] = {}
                except Exception as e:  # noqa: BLE001
                    actions.append(f"WARN  {name}: tip fetch failed for {slug}: {e}")
                    tip_cache[slug] = {}
            tip_metrics = tip_cache.get(slug) or None

        old_rank = re.search(r'data-rank="(\d+)"', card)
        old_rank_n = re.search(r'class="rank-n">#(\d+)', card)
        had_rank = bool(old_rank or old_rank_n)
        url = MODEL_PAGE.format(slug=slug)

        if slug in open_map:
            rank = open_map[slug].rank
            display = open_map[slug].name
            if had_rank:
                updated = update_existing_rank_field(
                    card, slug, display, rank, total, tip_metrics
                )
                prev = old_rank.group(1) if old_rank else (old_rank_n.group(1) if old_rank_n else "?")
                if prev != str(rank):
                    actions.append(f"RANK  {name}: #{prev} → #{rank}/{total} ({slug})")
                else:
                    actions.append(f"OK    {name}: #{rank}/{total} ({slug}, {matched_via})")
            else:
                rank_html = build_rank_field(
                    slug,
                    display,
                    rank,
                    total,
                    tip_metrics,
                    existing_tip_keys=None,
                )
                updated = insert_rank_field(card, rank_html)
                if "data-rank=" in updated:
                    updated = re.sub(
                        r'data-rank="[^"]*"', f'data-rank="{rank}"', updated, count=1
                    )
                else:
                    updated = re.sub(
                        r'(<div class="setup setup-rich\b[^>]*?)(>)',
                        rf'\1 data-rank="{rank}"\2',
                        updated,
                        count=1,
                    )
                actions.append(f"LINK  {name}: → {slug} #{rank}/{total}")
        else:
            # Model exists on BenchmarkList but has no open-weight ECI rank.
            # Keep a live link; do not leave a stale open-weight #N/T.
            rank_html = (
                f'<div class="rf"><span class="rl">rank</span><span class="rv">'
                f'<a class="rank-src" href="{url}" target="_blank" rel="noopener">benchmarklist</a>'
                f"</span></div>"
            )
            updated = re.sub(
                r'<div class="rf"><span class="rl">rank</span><span class="rv">.*?'
                r'<a class="rank-src"[^>]*>benchmarklist</a></span></div>',
                rank_html,
                card,
                count=1,
                flags=re.S,
            )
            if updated == card:
                # No prior rank block (or unusual markup) — insert link row.
                if "benchmarklist.com/models/" in card:
                    updated = re.sub(
                        r'https://benchmarklist\.com/models/[^"/]+/?',
                        url,
                        card,
                    )
                updated = insert_rank_field(updated, rank_html) if 'rl">rank</span>' not in updated else updated
            # Drop stale data-rank so filters don't use an obsolete number
            updated = re.sub(r'\s*data-rank="\d+"', "", updated, count=1)
            actions.append(f"LINK  {name}: → {slug} (no open-weight rank)")

        new_html_parts.append(updated)
        cursor = end

    new_html_parts.append(html[cursor:])
    out = "".join(new_html_parts)

    print("\nActions:")
    for line in actions:
        print(" ", line)

    changed = out != html
    if args.dry_run:
        print(f"\nDry run complete ({'changes pending' if changed else 'no HTML changes'}).")
        return 0

    if not changed:
        print("\nNo HTML changes.")
        return 0

    INDEX.write_text(out, encoding="utf-8")
    shutil.copyfile(INDEX, LOCALLIST)
    print(f"\nWrote {INDEX.relative_to(ROOT)} and {LOCALLIST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
