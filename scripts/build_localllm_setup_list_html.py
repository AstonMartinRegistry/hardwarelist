#!/usr/bin/env python3
"""Build localllmsetuplist.html from liked hardware-setups-review canvas picks."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from paths import DATA, OUTPUT, liked_canvas_data

LIKED = liked_canvas_data()
SETUPS = DATA / "hardware-setups.json"
OUT = OUTPUT / "localllmsetuplist.html"

COLS = 3


def extract_pp_ts(text: str, tps_values: list[float]) -> tuple[str, str]:
    hay = text or ""
    pp_vals: list[str] = []
    ts_vals: list[str] = []

    for pat in (
        r"(\d+(?:\.\d+)?)\s*(?:tok/s|t/s|tokens/sec|tok/sec|tps)\s*pp\b",
        r"(\d+(?:\.\d+)?)\s*pp/s\b",
        r"(?:~|about)?\s*(\d+(?:\.\d+)?)\s*(?:tok/s|t/s)\s*pp\b",
        r"(\d+(?:\.\d+)?)\s*pp\s*(?:@|tok/s|t/s|tokens/sec|tok/sec)?",
        r"pp\s*TPS[^0-9]{0,20}(\d+(?:\.\d+)?)\s*tok/s",
        r"(\d+(?:\.\d+)?)\s*tok/s\s+pp\s+TPS",
    ):
        for m in re.finditer(pat, hay, re.I):
            pp_vals.append(m.group(1))

    for pat in (
        r"(\d+(?:\.\d+)?)\s*(?:tok/s|t/s|tokens/sec|tok/sec|tps)\s*(?:tg|gen|decode|generation)\b",
        r"(?:tg|gen|decode|generation)\s*(\d+(?:\.\d+)?)\s*(?:tok/s|t/s|tokens/sec|tok/sec|tps)?",
        r"(\d+(?:\.\d+)?)\s*(?:tok/s|t/s|tokens/sec|tok/sec|tps)\b",
    ):
        for m in re.finditer(pat, hay, re.I):
            start = m.start()
            ctx = hay[max(0, start - 24) : m.end() + 12].lower()
            if re.search(r"\bpp\b", ctx) and "tg" not in ctx and "gen" not in ctx and "decode" not in ctx:
                continue
            ts_vals.append(m.group(1))

    if tps_values and not ts_vals:
        reasonable = [v for v in tps_values if 0.1 <= v <= 500]
        pick = min(reasonable) if reasonable else min(tps_values)
        ts_vals.append(f"{pick:g}")

    pp = ", ".join(dict.fromkeys(pp_vals))
    ts = ", ".join(dict.fromkeys(ts_vals))
    return pp, ts


def leftover_message(row: dict, pp: str, ts: str) -> str:
    """Keep the original message intact (do not punch holes for extracted fields)."""
    del pp, ts  # kept in signature for call-site compatibility
    msg = (row.get("message") or "").strip()
    return msg or "—"


def render_box(row: dict) -> str:
    specs = row.get("specs") or {}
    hay = f"{row.get('speed') or ''}\n{row.get('message') or ''}"
    pp, ts = extract_pp_ts(hay, specs.get("tps_values") or [])
    extra = leftover_message(row, pp, ts)
    fields = [
        ("hardware", row.get("hardware") or "—"),
        ("model", row.get("model") or "—"),
        ("quant", row.get("quantization") or "—"),
        ("speed", row.get("speed") or "—"),
        ("pp", pp or "—"),
        ("ts", ts or "—"),
        ("additional info", extra),
    ]
    lines = []
    for label, value in fields:
        lines.append(f"<b>{html.escape(label)}:</b> {html.escape(str(value))}<br>")
    return (
        "<fieldset>\n"
        f"<legend>{html.escape(row.get('id', ''))}</legend>\n"
        + "".join(lines)
        + "</fieldset>"
    )


def build_html(rows: list[dict]) -> str:
    parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        '<meta charset="utf-8">',
        "<title>localllmsetuplist</title>",
        "</head>",
        "<body>",
        "<h1>localllmsetuplist</h1>",
        '<table border="1" cellpadding="8" cellspacing="0">',
    ]
    for i in range(0, len(rows), COLS):
        chunk = rows[i : i + COLS]
        parts.append("<tr>")
        for row in chunk:
            parts.append(f"<td valign=\"top\">{render_box(row)}</td>")
        for _ in range(COLS - len(chunk)):
            parts.append("<td></td>")
        parts.append("</tr>")
    parts.extend(["</table>", "</body>", "</html>"])
    return "\n".join(parts) + "\n"


def main() -> None:
    liked_doc = json.loads(LIKED.read_text(encoding="utf-8"))
    liked_ids = [mid for mid, on in liked_doc.get("liked", {}).items() if on]
    by_id = {r["id"]: r for r in json.loads(SETUPS.read_text(encoding="utf-8"))["setups"]}
    rows = [by_id[mid] for mid in liked_ids if mid in by_id]
    rows.sort(key=lambda r: (r.get("month", ""), r.get("id", "")), reverse=True)
    OUT.write_text(build_html(rows), encoding="utf-8")
    print(f"Wrote {OUT} ({len(rows)} setups from {len(liked_ids)} liked ids)")


if __name__ == "__main__":
    main()
