#!/usr/bin/env python3
"""
Duplicate-record detector.

Normalizes `title` and `description`, groups records whose normalized
(title, description, date) triple matches exactly, and reports
deterministic duplicate ID groups (only groups with 2+ records).

Determinism guarantees:
  - IDs inside each group are sorted (natural/numeric-aware order).
  - Groups are sorted by their first (smallest) ID, then by group key.
  - JSON output uses sorted keys; no reliance on dict/set iteration order.

Usage:
    python dedupe.py records.json
    python dedupe.py records.csv --format json
    python dedupe.py            # runs the built-in demo

Input formats (by file extension):
    .json : list of objects, each with id, title, description, date
    .csv  : header row with id,title,description,date
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------

_WS_RE = re.compile(r"\s+")
# Remove punctuation/symbols (Unicode categories P* and S*), keep letters/digits.
_PUNCT_CATEGORIES = ("P", "S")


def normalize_text(value: Any) -> str:
    """
    Canonical form of free text:
      1. None -> ""
      2. Unicode NFKC (folds compatibility forms, e.g. full-width chars, ligatures)
      3. casefold (stronger than lower(); handles e.g. German ß)
      4. strip accents (NFD, drop combining marks)
      5. punctuation/symbols -> space
      6. collapse whitespace and trim
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = "".join(
        " " if unicodedata.category(ch)[0] in _PUNCT_CATEGORIES else ch
        for ch in text
    )
    return _WS_RE.sub(" ", text).strip()


_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y.%m.%d",
    "%Y%m%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d %b %Y",
    "%d %B %Y",
)


def normalize_date(value: Any) -> str:
    """
    Canonical form of a date: ISO `YYYY-MM-DD`.
    Accepts date/datetime objects or strings in a few common formats.
    Time-of-day is intentionally ignored (grouping is by calendar date).
    Unparseable / missing values fall back to normalized text so they
    still group deterministically with identical raw values.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    s = str(value).strip()
    # ISO datetime such as 2024-03-05T10:20:30Z -> keep only the date part
    iso_head = re.match(r"^(\d{4}-\d{2}-\d{2})(?:[T ].*)?$", s)
    if iso_head:
        try:
            return datetime.strptime(iso_head.group(1), "%Y-%m-%d").date().isoformat()
        except ValueError:
            pass
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return "raw:" + normalize_text(s)


# --------------------------------------------------------------------------
# Deterministic ordering helpers
# --------------------------------------------------------------------------

_NUM_SPLIT_RE = re.compile(r"(\d+)")


def natural_key(value: Any) -> Tuple:
    """
    Natural sort key so 'a2' < 'a10' and 2 < 10, with a type-stable tuple
    structure (avoids int/str comparison errors).
    Each chunk -> (0, int) for digit runs, (1, str) for text.
    The original string is appended as a final tie-breaker.
    """
    s = str(value)
    parts = []
    for chunk in _NUM_SPLIT_RE.split(s):
        if chunk == "":
            continue
        parts.append((0, int(chunk), "") if chunk.isdigit() else (1, 0, chunk))
    return (tuple(parts), s)


# --------------------------------------------------------------------------
# Core detection
# --------------------------------------------------------------------------

GroupKey = Tuple[str, str, str]  # (norm_title, norm_description, norm_date)


def build_key(record: Dict[str, Any]) -> GroupKey:
    return (
        normalize_text(record.get("title")),
        normalize_text(record.get("description")),
        normalize_date(record.get("date")),
    )


def find_duplicate_groups(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Returns a deterministically ordered list of duplicate groups:
        [{"key": {...}, "ids": [...], "count": n}, ...]
    Only groups with at least two distinct record IDs are reported.
    Records lacking an `id` raise ValueError (cannot be reported reliably).
    """
    buckets: Dict[GroupKey, set] = defaultdict(set)

    for idx, rec in enumerate(records):
        if "id" not in rec or rec["id"] is None or str(rec["id"]).strip() == "":
            raise ValueError(f"Record at position {idx} has no 'id': {rec!r}")
        buckets[build_key(rec)].add(str(rec["id"]).strip())

    groups = []
    for key, id_set in buckets.items():
        if len(id_set) < 2:
            continue
        ids = sorted(id_set, key=natural_key)
        groups.append(
            {
                "key": {
                    "title": key[0],
                    "description": key[1],
                    "date": key[2],
                },
                "ids": ids,
                "count": len(ids),
            }
        )

    # Deterministic group order: by first ID (natural), then by full key.
    groups.sort(
        key=lambda g: (
            natural_key(g["ids"][0]),
            g["key"]["title"],
            g["key"]["description"],
            g["key"]["date"],
        )
    )
    for n, g in enumerate(groups, start=1):
        g["group_id"] = f"DUP-{n:04d}"
    return groups


# --------------------------------------------------------------------------
# I/O
# --------------------------------------------------------------------------

def load_records(path: str) -> List[Dict[str, Any]]:
    lower = path.lower()
    if lower.endswith(".json"):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            raise ValueError("JSON input must be a list of record objects.")
        return data
    if lower.endswith(".csv"):
        with open(path, "r", encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    raise ValueError("Unsupported input type; use .json or .csv")


def render_text(groups: List[Dict[str, Any]], total_records: int) -> str:
    if not groups:
        return f"No duplicates found among {total_records} record(s)."
    dup_records = sum(g["count"] for g in groups)
    lines = [
        f"Scanned {total_records} record(s): "
        f"{len(groups)} duplicate group(s), {dup_records} record(s) involved.",
        "",
    ]
    for g in groups:
        k = g["key"]
        lines.append(f"{g['group_id']}  ids={', '.join(g['ids'])}")
        lines.append(f"    title       : {k['title']!r}")
        lines.append(f"    description : {k['description']!r}")
        lines.append(f"    date        : {k['date']!r}")
    return "\n".join(lines)


def render_json(groups: List[Dict[str, Any]], total_records: int) -> str:
    payload = {
        "total_records": total_records,
        "duplicate_group_count": len(groups),
        "groups": groups,
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)


# --------------------------------------------------------------------------
# Demo + CLI
# --------------------------------------------------------------------------

DEMO_RECORDS = [
    {"id": "A10", "title": "Quarterly  Report!", "description": "Revenue summary for Q1.", "date": "2024-03-05"},
    {"id": "A2",  "title": "quarterly report",   "description": "Revenue Summary for Q1",  "date": "03/05/2024"},
    {"id": "A3",  "title": "Quarterly Report",   "description": "Revenue summary for Q1.", "date": "2024-03-06"},
    {"id": "B1",  "title": "Café Menu",          "description": "Spring   specials",        "date": "2024-04-01T09:30:00Z"},
    {"id": "B7",  "title": "CAFE MENU",          "description": "spring specials",          "date": "2024-04-01"},
    {"id": "B9",  "title": "Cafe-Menu",          "description": "Spring specials!",         "date": "April 1, 2024"},
    {"id": "C1",  "title": "Unique item",        "description": "Nothing like it",          "date": "2024-01-01"},
    {"id": "A2",  "title": "Quarterly Report",   "description": "Revenue summary for Q1",   "date": "2024-03-05"},  # repeated ID, ignored
]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Detect duplicate records.")
    parser.add_argument("input", nargs="?", help="Path to .json or .csv (omit for demo)")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        records = load_records(args.input) if args.input else DEMO_RECORDS
        groups = find_duplicate_groups(records)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out = (render_json if args.format == "json" else render_text)(groups, len(records))
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())