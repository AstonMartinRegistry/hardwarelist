#!/usr/bin/env python3
"""Detect hardware benchmark setups from Discord messages."""

from __future__ import annotations

import re
from pathlib import Path

from registry_match import load_registry, match_registry

ROOT = Path(__file__).resolve().parent.parent
HW_REG = ROOT / "hardware_registry.txt"
QT_REG = ROOT / "quantization_registry.txt"
MODEL_REG = ROOT / "model_registry.txt"

GENERIC_SPEED = {
    "tps",
    "t/s",
    "tok/s",
    "speed",
    "faster",
    "slow",
    "tokens per second",
    "token generation speed",
    "good speed",
}

GENERIC_HW = {"vram", "ram", "cpu", "gpu", "igpu", "nvidia", "amd"}

TPS_PATTERNS = [
    re.compile(
        r"(?P<val>\d+(?:\.\d+)?)\s*(?:\+|±|~)?\s*"
        r"(?:tok(?:en)?s?/?s|t/s|tps|tk/s|tok/sec|tokens/sec|tokens\s*per\s*second|ts)\b",
        re.I,
    ),
    re.compile(
        r"\b(?:tok(?:en)?s?/?s|t/s|tps|tk/s|tokens/sec|tokens\s*per\s*second|ts)\s*"
        r"(?:of|at|around|about|~|is|was)?\s*(?P<val>\d+(?:\.\d+)?)",
        re.I,
    ),
    re.compile(r"(?P<val>\d+(?:\.\d+)?)\s*t/s\b", re.I),
    re.compile(r"(?P<val>\d+(?:\.\d+)?)(?:t/s|tk/s|tok/s)\b", re.I),
    re.compile(r"(?P<val>\d+(?:\.\d+)?)\s*tks\b", re.I),
    re.compile(r"(?P<val>\d+(?:\.\d+)?)\s*tks?/s\b", re.I),
]

TTFT_PATTERNS = [
    re.compile(
        r"(?:ttft|time\s*to\s*first\s*token|first\s*token\s*latency|prefill\s*latency|tpot)"
        r"[^0-9]{0,24}(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>ms|milliseconds?|s|sec|seconds?)\b",
        re.I,
    ),
    re.compile(
        r"(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>ms|milliseconds?|s|sec|seconds?)\s*"
        r"(?:ttft|to\s*first\s*token|first\s*token|tpot)",
        re.I,
    ),
    re.compile(r"sub[- ]?(?P<val>\d+(?:\.\d+)?)\s*ms\s*(?:latency|ttft|ttft)?", re.I),
    re.compile(r"mean\s+ttft\s*\(ms\):\s*(?P<val>\d+(?:\.\d+)?)", re.I),
    re.compile(r"median\s+ttft\s*\(ms\):\s*(?P<val>\d+(?:\.\d+)?)", re.I),
]

MODEL_PATTERNS: list[tuple[re.Pattern[str], str | callable]] = [
    (re.compile(r"qwen3\.6[- ]?(\d+)\s*b", re.I), lambda m: f"qwen3.6-{m.group(1)}b"),
    (re.compile(r"qwen3\.5[- ]?(\d+)\s*b", re.I), lambda m: f"qwen3.5-{m.group(1)}b"),
    (re.compile(r"qwen3[- ]?coder", re.I), "qwen3-coder"),
    (re.compile(r"qwen3[- ]?(\d+)\s*b", re.I), lambda m: f"qwen3-{m.group(1)}b"),
    (re.compile(r"gpt[- ]?oss[- ]?120", re.I), "gpt-oss-120b"),
    (re.compile(r"gpt[- ]?oss[- ]?20", re.I), "gpt-oss-20b"),
    (re.compile(r"gemma\s*4", re.I), "gemma4"),
    (re.compile(r"glm[- ]?5(?:\.\d+)?", re.I), "glm-5"),
    (re.compile(r"glm[- ]?4", re.I), "glm-4"),
    (re.compile(r"deepseek[- ]?v4", re.I), "deepseek-v4"),
    (re.compile(r"deepseek", re.I), "deepseek"),
    (re.compile(r"minimax[- ]?m?\d", re.I), "minimax"),
    (re.compile(r"kimi[- ]?k2", re.I), "kimi-k2"),
    (re.compile(r"llama[- ]?3", re.I), "llama-3"),
    (re.compile(r"devstral", re.I), "devstral"),
    (re.compile(r"mistral", re.I), "mistral"),
]


def to_ms(value: float, unit: str) -> float:
    u = (unit or "ms").lower()
    if u.startswith("ms") or u.startswith("milli"):
        return value
    return value * 1000.0


def extract_tps(text: str) -> list[float]:
    values: list[float] = []
    for pat in TPS_PATTERNS:
        for m in pat.finditer(text or ""):
            val = float(m.group("val"))
            if 0.1 <= val <= 50000:
                values.append(val)
    return values


def extract_ttft_ms(text: str) -> list[float]:
    values: list[float] = []
    for pat in TTFT_PATTERNS:
        for m in pat.finditer(text or ""):
            val = float(m.group("val"))
            unit = m.groupdict().get("unit") or "ms"
            ms = to_ms(val, unit)
            if 1 <= ms <= 600_000:
                values.append(ms)
    return values


def load_model_entries():
    return load_registry(MODEL_REG)


def infer_model(text: str, model_entries=None) -> str:
    for pat, out in MODEL_PATTERNS:
        m = pat.search(text or "")
        if not m:
            continue
        return out(m) if callable(out) else out
    entries = model_entries if model_entries is not None else load_model_entries()
    slugs = match_registry(text or "", entries)
    if slugs:
        return slugs[0]
    return ""


def has_setup_model(model: str) -> bool:
    return bool((model or "").strip())


def has_setup_speed(*, speed: str, tps: list[float], ttft_ms: list[float]) -> bool:
    if tps or ttft_ms:
        return True
    s = (speed or "").strip().lower()
    if not s or s in GENERIC_SPEED:
        return False
    return bool(re.search(r"\d", s))


def is_complete_setup(row: dict) -> bool:
    specs = row.get("specs") or {}
    model = row.get("model") or specs.get("model") or ""
    speed = row.get("speed") or specs.get("speed") or ""
    return has_setup_model(model) and has_setup_speed(
        speed=speed,
        tps=specs.get("tps_values") or [],
        ttft_ms=specs.get("ttft_ms_values") or [],
    )


def format_speed(tps: list[float], ttft_ms: list[float], extracted: str = "") -> str:
    parts: list[str] = []
    if extracted and extracted.strip().lower() not in {"tps", "t/s", "tok/s", "speed", "faster", "slow"}:
        parts.append(extracted.strip())
    if tps:
        parts.append(", ".join(f"{v:g} tok/s" for v in tps[:4]))
    if ttft_ms:
        parts.append(", ".join(f"{v:g}ms TTFT" for v in ttft_ms[:3]))
    return " · ".join(parts)


def load_hw_entries():
    return load_registry(HW_REG)


def load_qt_entries():
    return load_registry(QT_REG)


def match_hardware(text: str, entries) -> tuple[list[str], list[str]]:
    slugs = match_registry(text, entries)
    specific = [s for s in slugs if s not in GENERIC_HW]
    return slugs, specific


def summarize_hardware(extracted: str, specific_slugs: list[str]) -> str:
    if extracted and extracted.strip().lower() not in {"gpu", "gpus", "vram", "ram", "cpu"}:
        return extracted.strip()
    if specific_slugs:
        return ", ".join(specific_slugs[:4])
    return extracted.strip() if extracted else ""


def summarize_quant(extracted: str, quant_slugs: list[str]) -> str:
    if extracted and extracted.strip().lower() not in {"quant", "quantization", "quants"}:
        return extracted.strip()
    if quant_slugs:
        return ", ".join(quant_slugs[:3])
    return extracted.strip() if extracted else ""


def assign_tier(
    *,
    in_hw: bool,
    in_sp: bool,
    in_qt: bool,
    in_mm: bool,
    specific_hw: list[str],
    tps: list[float],
    ttft_ms: list[float],
    model: str,
) -> str | None:
    has_numeric = bool(tps or ttft_ms)
    has_model = bool(model)

    if in_hw and in_sp and in_qt and in_mm:
        return "full"
    if in_hw and in_sp and in_mm:
        return "hw_speed_model"
    if in_hw and in_sp and has_numeric:
        return "hw_speed_benchmark"
    if in_hw and in_sp:
        return "hw_speed"
    if specific_hw and has_numeric and (has_model or in_mm):
        return "inferred_model"
    if specific_hw and has_numeric:
        return "inferred"
    return None
