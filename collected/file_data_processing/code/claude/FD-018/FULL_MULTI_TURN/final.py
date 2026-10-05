#!/usr/bin/env python3
"""
Duplicate-record detector.

Normalizes `title` and `description`, groups records whose normalized
(title, description, date) triple matches exactly, and reports
deterministic duplicate ID groups.

Normalization:
  - title      : case-insensitive, whitespace-insensitive, and also ignores
                 punctuation, HTML tags, and accents.
  - description: case-insensitive; every run of whitespace (spaces, tabs,
                 newlines, NBSP, zero-width characters) collapses to a single
                 space and leading/trailing whitespace is trimmed.
                 Punctuation (and everything else) is NOT altered, so
                 "Final numbers, Q3." != "Final numbers Q3".
  - date       : normalized to ISO YYYY-MM-DD when parseable.

Guarantees:
  - Singleton groups (only one distinct ID) are omitted.
  - IDs inside every duplicate group are sorted (numeric-aware natural
    order, so "2" < "10"), each listed once.
  - Groups are sorted by smallest ID, then by group key.
  - JSON output uses sorted keys and fixed formatting.

Usage:
    python dedupe.py records.json
    python dedupe.py records.csv
    python dedupe.py            # runs built-in demo
Input fields: id, title, description, date
"""

from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

_WS_RE = re.compile(r"\s+", re.UNICODE)
_PUNCT_RE = re.compile(r"[^\w\s]|_", re.UNICODE)
_TAG_RE = re.compile(r"<[^>]+>")
_NUM_RE = re.compile(r"(\d+)")
_INVISIBLE_RE = re.compile("[\u200b\u200c\u200d\u2060\ufeff\u00ad]")

_DATE_FORMATS = (
    "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d",
    "%m/%d/%Y", "%d-%m-%Y", "%d.%m.%Y",
    "%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y",
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
)


def collapse_whitespace(text: str) -> str:
    """Collapse every run of whitespace into one space and trim the ends."""
    return _WS_RE.sub(" ", text).strip()


def normalize_title(value: Any) -> str:
    """Case-, whitespace-, punctuation-, accent-insensitive normal form."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = _INVISIBLE_RE.sub("", text)
    text = _TAG_RE.sub(" ", text)
    text = text.casefold()
    text = "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )
    text = _PUNCT_RE.sub(" ", text)
    return collapse_whitespace(text)


def normalize_description(value: Any) -> str:
    """Case-insensitive; collapses repeated whitespace and trims surrounding
    whitespace. Punctuation, tags, and accents are left untouched."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))  # NBSP etc. -> space
    text = _INVISIBLE_RE.sub("", text)
    text = text.casefold()
    return collapse_whitespace(text)


def normalize_date(value: Any) -> str:
    """Return ISO date (YYYY-MM-DD). Unparseable values fall back to
    normalized text so they still group deterministically."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    raw = collapse_whitespace(
        _INVISIBLE_RE.sub("", unicodedata.normalize("NFKC", str(value)))
    )
    if not raw:
        return ""
    for candidate in (raw, raw.title() if raw.isupper() or raw.islower() else raw):
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(candidate, fmt).date().isoformat()
            except ValueError:
                continue
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return normalize_title(raw)


def natural_key(value: Any) -> tuple:
    """Sort key: numeric chunks compare numerically, text chunks lexically."""
    parts = _NUM_RE.split(str(value))
    key = []
    for i, part in enumerate(parts):
        if i % 2:
            key.append((0, int(part), ""))
        elif part:
            key.append((1, 0, part))
    return (tuple(key), str(value))


def make_key(record: dict) -> tuple[str, str, str]:
    return (
        normalize_title(record.get("title")),
        normalize_description(record.get("description")),
        normalize_date(record.get("date")),
    )


def find_duplicates(
    records: Iterable[dict],
    *,
    skip_empty: bool = True,
) -> list[dict]:
    """Group records by normalized (title, description, date).

    Returns only groups with 2+ distinct IDs (singletons omitted), each as
    {"group", "key", "ids", "count"} with "ids" sorted naturally.
    If skip_empty is True, records whose title AND description are both
    empty are ignored.
    """
    buckets: dict[tuple[str, str, str], set] = defaultdict(set)
    for idx, rec in enumerate(records):
        rec_id = collapse_whitespace(str(rec.get("id", "") or ""))
        if not rec_id:
            rec_id = f"row-{idx}"  # deterministic fallback by input position
        key = make_key(rec)
        if skip_empty and not key[0] and not key[1]:
            continue
        buckets[key].add(rec_id)

    groups = []
    for key, ids in buckets.items():
        if len(ids) < 2:  # omit singleton groups
            continue
        sorted_ids = sorted(ids, key=natural_key)  # sort IDs in every group
        groups.append({
            "key": {"title": key[0], "description": key[1], "date": key[2]},
            "ids": sorted_ids,
            "count": len(sorted_ids),
        })

    groups.sort(key=lambda g: (
        natural_key(g["ids"][0]),
        g["key"]["title"], g["key"]["description"], g["key"]["date"],
    ))
    for n, g in enumerate(groups, 1):
        g["group"] = n
    return groups


def load_records(path: str) -> list[dict]:
    p = Path(path)
    if p.suffix.lower() == ".csv":
        with p.open(newline="", encoding="utf-8-sig") as fh:
            return list(csv.DictReader(fh))
    with p.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        data = data.get("records", [])
    return data


def format_report(groups: list[dict], total: int) -> str:
    dup_ids = sum(g["count"] for g in groups)
    lines = [
        f"Records scanned : {total}",
        f"Duplicate groups: {len(groups)}",
        f"Records in dupes: {dup_ids}",
        "",
    ]
    for g in groups:
        k = g["key"]
        lines.append(f"Group {g['group']}: {', '.join(g['ids'])}")
        lines.append(f"  title      : {k['title']}")
        lines.append(f"  description: {k['description']}")
        lines.append(f"  date       : {k['date']}")
    return "\n".join(lines)


DEMO = [
    {"id": "10", "title": "  quarterly report  ", "description": "   FINAL   NUMBERS,   q3.  ", "date": "MARCH  1,  2024"},
    {"id": "2",  "title": "QUARTERLY   REPORT",   "description": "final\tnumbers,\n q3.",       "date": "03/01/2024"},
    {"id": "1",  "title": "Quarterly Report",     "description": "Final numbers, Q3.",          "date": "2024-03-01"},
    {"id": "3",  "title": "Quarterly Report",     "description": "Final numbers Q3",            "date": "2024-03-01"},  # punctuation differs -> not a duplicate
    {"id": "5",  "title": "CAFE\u00a0MENU",       "description": "spring    items!",            "date": "2024-04-01"},
    {"id": "4",  "title": "Café Menu",            "description": "  Spring items!  ",           "date": "2024-04-01"},
    {"id": "6",  "title": "Unique",               "description": "Only one",                    "date": "2024-05-01"},  # singleton
]


def main(argv: list[str]) -> int:
    records = load_records(argv[1]) if len(argv) > 1 else DEMO
    groups = find_duplicates(records)
    print(format_report(groups, len(records)))
    print("\nJSON:")
    print(json.dumps(groups, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))