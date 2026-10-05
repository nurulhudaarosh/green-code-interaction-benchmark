#!/usr/bin/env python3
"""
Duplicate-record detector.

Normalizes title and description, groups records whose normalized
(title, description, date) match exactly, and reports deterministic
duplicate ID groups.

Determinism guarantees:
  - IDs inside each group are sorted (numeric-aware).
  - Groups are sorted by their first (smallest) ID, then by key.
  - Output JSON uses sorted keys; no reliance on dict/set iteration order.
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
from typing import Any, Iterable

# ----------------------------------------------------------------------
# Normalization
# ----------------------------------------------------------------------

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%Y%m%d",
)


def normalize_text(value: Any) -> str:
    """Unicode-normalize, casefold, strip punctuation, collapse whitespace."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.casefold()
    text = _PUNCT_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def normalize_date(value: Any) -> str:
    """Return an ISO date string (YYYY-MM-DD), or '' if missing.

    Unparseable dates fall back to normalized text so that identical
    unparseable values still match each other deterministically.
    """
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    raw = str(value).strip()
    if not raw:
        return ""

    # Keep only the date portion of ISO timestamps (e.g. 2024-05-01T10:00:00Z).
    iso_head = raw[:10]
    try:
        return datetime.strptime(iso_head, "%Y-%m-%d").date().isoformat()
    except ValueError:
        pass

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return "raw:" + normalize_text(raw)


# ----------------------------------------------------------------------
# Detection
# ----------------------------------------------------------------------

def _id_sort_key(record_id: Any) -> tuple:
    """Numeric-aware, type-safe sort key so ordering is stable."""
    s = str(record_id)
    parts = re.split(r"(\d+)", s)
    return tuple(
        (0, int(p), "") if p.isdigit() else (1, 0, p) for p in parts if p != ""
    ) + ((2, 0, s),)


def make_key(record: dict, id_field: str, title_field: str,
             desc_field: str, date_field: str) -> tuple[str, str, str]:
    return (
        normalize_text(record.get(title_field)),
        normalize_text(record.get(desc_field)),
        normalize_date(record.get(date_field)),
    )


def find_duplicates(
    records: Iterable[dict],
    id_field: str = "id",
    title_field: str = "title",
    desc_field: str = "description",
    date_field: str = "date",
    skip_empty: bool = True,
) -> list[dict]:
    """Return deterministic duplicate groups.

    Each group: {"group": n, "key": {...}, "ids": [...], "count": k}
    Only groups with 2+ distinct IDs are reported.
    """
    buckets: dict[tuple[str, str, str], list[Any]] = defaultdict(list)

    for rec in records:
        if id_field not in rec or rec[id_field] in (None, ""):
            continue
        key = make_key(rec, id_field, title_field, desc_field, date_field)
        if skip_empty and key[0] == "" and key[1] == "":
            continue  # nothing meaningful to compare
        buckets[key].append(rec[id_field])

    groups = []
    for key, ids in buckets.items():
        unique_ids = sorted(set(ids), key=_id_sort_key)
        if len(unique_ids) > 1:
            groups.append((key, unique_ids))

    # Deterministic group ordering: by first ID, then by the key itself.
    groups.sort(key=lambda g: (_id_sort_key(g[1][0]), g[0]))

    return [
        {
            "group": i,
            "key": {"title": k[0], "description": k[1], "date": k[2]},
            "ids": ids,
            "count": len(ids),
        }
        for i, (k, ids) in enumerate(groups, start=1)
    ]


# ----------------------------------------------------------------------
# I/O
# ----------------------------------------------------------------------

def load_records(path: str) -> list[dict]:
    if path.lower().endswith(".json"):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            raise ValueError("JSON input must be a list of objects.")
        return data
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def format_report(groups: list[dict]) -> str:
    if not groups:
        return "No duplicate records found."
    lines = [f"Found {len(groups)} duplicate group(s):", ""]
    for g in groups:
        lines.append(f"Group {g['group']} ({g['count']} records): "
                     f"{', '.join(map(str, g['ids']))}")
        lines.append(f"  title:       {g['key']['title']!r}")
        lines.append(f"  description: {g['key']['description']!r}")
        lines.append(f"  date:        {g['key']['date']!r}")
        lines.append("")
    return "\n".join(lines).rstrip()


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Detect duplicate records.")
    p.add_argument("input", nargs="?", help="CSV or JSON file (omit to run demo)")
    p.add_argument("--id-field", default="id")
    p.add_argument("--title-field", default="title")
    p.add_argument("--desc-field", default="description")
    p.add_argument("--date-field", default="date")
    p.add_argument("--json", action="store_true", help="Emit JSON report")
    p.add_argument("--keep-empty", action="store_true",
                   help="Also compare records with empty title and description")
    args = p.parse_args(argv)

    if args.input:
        records = load_records(args.input)
    else:
        records = [
            {"id": 10, "title": "Quarterly Report!", "description": "Q3  results ",
             "date": "2024-10-01"},
            {"id": 2,  "title": "quarterly report",  "description": "q3 results",
             "date": "10/01/2024"},
            {"id": 7,  "title": "Quarterly Report",  "description": "Q3 results",
             "date": "2024-10-02"},  # different date -> not a duplicate
            {"id": 3,  "title": "Café Menu",  "description": "Spring edition",
             "date": "2024-03-01"},
            {"id": 12, "title": "CAFÉ  MENU", "description": "spring edition.",
             "date": "2024-03-01T09:30:00Z"},
            {"id": 99, "title": "Unique", "description": "Only one", "date": "2024-01-01"},
        ]

    groups = find_duplicates(
        records,
        id_field=args.id_field,
        title_field=args.title_field,
        desc_field=args.desc_field,
        date_field=args.date_field,
        skip_empty=not args.keep_empty,
    )

    if args.json:
        print(json.dumps(groups, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(format_report(groups))
    return 0


if __name__ == "__main__":
    sys.exit(main())