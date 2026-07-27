#!/usr/bin/env python3
"""Shared registry loader and text matcher."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RegistryEntry:
    slug: str
    aliases: tuple[str, ...]


def load_registry(path: Path) -> list[RegistryEntry]:
    entries: list[RegistryEntry] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "|" not in line:
            continue
        slug, alias_blob = line.split("|", 1)
        slug = slug.strip()
        aliases = tuple(a.strip().lower() for a in alias_blob.split(",") if a.strip())
        if slug:
            entries.append(RegistryEntry(slug=slug, aliases=aliases or (slug,)))
    # Longest alias first to prefer specific matches.
    entries.sort(key=lambda e: max(len(a) for a in e.aliases), reverse=True)
    return entries


def _alias_pattern(alias: str) -> re.Pattern[str]:
    escaped = re.escape(alias.lower())
    escaped = escaped.replace(r"\ ", r"\s+")
    if alias.isalnum() or alias.replace(" ", "").isalnum():
        return re.compile(rf"(?<![a-z0-9./_-]){escaped}(?![a-z0-9./_-])", re.I)
    return re.compile(rf"{escaped}", re.I)


def match_registry(text: str, entries: list[RegistryEntry]) -> list[str]:
    hay = (text or "").lower()
    if not hay.strip():
        return []
    found: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        for alias in entry.aliases:
            if _alias_pattern(alias).search(hay):
                if entry.slug not in seen:
                    seen.add(entry.slug)
                    found.append(entry.slug)
                break
    return found


def month_label(month: str) -> str:
    y, m = month.split("-")
    return f"{m}/{y[2:]}"


REDDIT_REPOST = re.compile(
    r"a rising post from r/localllama|don't want to see more\?\s*mods can unlink this subreddit",
    re.I,
)


def is_reddit_repost(text: str) -> bool:
    return bool(REDDIT_REPOST.search(text or ""))

