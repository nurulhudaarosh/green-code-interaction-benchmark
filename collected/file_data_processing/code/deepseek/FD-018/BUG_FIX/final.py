"""
Duplicate-record detector.

Reads records from a JSON file (or a Python list), normalizes the
`title` and `description` fields, groups records whose normalized
(title, description) pairs match exactly, and reports deterministic
duplicate ID groups.

Normalization rules (minimal, per requirement):
  - Unicode NFKC normalization
  - Casefold (case-insensitive matching)
  - Collapse all whitespace runs (spaces, tabs, newlines) to a single space
  - Strip leading/trailing whitespace

Deliberately NOT removed: punctuation. "Hello, world!" and "hello world"
will NOT match under these rules because the comma differs.

Determinism:
  - Records are sorted by (date, id) before grouping.
  - Groups are reported sorted by the earliest (date, id) in the group.
  - IDs within a group are sorted.

Usage:
    python duplicate_detector.py records.json
    python duplicate_detector.py records.json --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Iterable, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Collapse any run of Unicode whitespace into a single ASCII space.
_WHITESPACE_RE = re.compile(r"\s+", re.UNICODE)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Record:
    id: str
    title: str
    description: str
    date: Optional[str] = None  # ISO-8601 date string, e.g. "2024-01-31"

    def normalized_key(self) -> tuple[str, str]:
        return (normalize_text(self.title), normalize_text(self.description))

    def sort_key(self) -> tuple[str, str]:
        # Missing dates sort last; otherwise ISO date strings sort lexically.
        return (self.date or "9999-12-31", self.id)


@dataclass
class DuplicateGroup:
    key: tuple[str, str]
    ids: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)

    @property
    def earliest_date(self) -> Optional[str]:
        present = [d for d in self.dates if d]
        return min(present) if present else None

    @property
    def count(self) -> int:
        return len(self.ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "normalized_title": self.key[0],
            "normalized_description": self.key[1],
            "ids": self.ids,
            "dates": self.dates,
            "earliest_date": self.earliest_date,
            "count": self.count,
        }


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_text(value: Any) -> str:
    """Normalize a text field for duplicate detection.

    Only case and whitespace differences are erased. Punctuation is kept.
    """
    if value is None:
        return ""
    text = str(value)
    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Parsing / loading
# ---------------------------------------------------------------------------

def parse_record(raw: dict[str, Any], index: int) -> Record:
    if not isinstance(raw, dict):
        raise ValueError(f"Record at index {index} is not a JSON object")

    rid = raw.get("id")
    if rid is None:
        raise ValueError(f"Record at index {index} is missing 'id'")
    rid = str(rid)

    title = raw.get("title", "")
    description = raw.get("description", "")
    date_value = raw.get("date")

    return Record(
        id=rid,
        title=title if title is not None else "",
        description=description if description is not None else "",
        date=_normalize_date(date_value),
    )


def _normalize_date(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return text  # leave as-is; sorting still works lexically


def load_records(path: str) -> list[Record]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    if isinstance(data, dict) and "records" in data:
        data = data["records"]

    if not isinstance(data, list):
        raise ValueError(
            "Input JSON must be a list of records or an object with a 'records' list"
        )

    return [parse_record(item, i) for i, item in enumerate(data)]


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

def find_duplicate_groups(records: Iterable[Record]) -> list[DuplicateGroup]:
    buckets: dict[tuple[str, str], list[Record]] = defaultdict(list)
    for rec in records:
        buckets[rec.normalized_key()].append(rec)

    groups: list[DuplicateGroup] = []
    for key, members in buckets.items():
        if len(members) < 2:
            continue
        members_sorted = sorted(members, key=lambda r: r.sort_key())
        group = DuplicateGroup(
            key=key,
            ids=[m.id for m in members_sorted],
            dates=[m.date or "" for m in members_sorted],
        )
        groups.append(group)

    # Deterministic ordering of groups: by earliest date, then first id.
    groups.sort(
        key=lambda g: (g.earliest_date or "9999-12-31", g.ids[0] if g.ids else "")
    )
    return groups


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def format_text_report(groups: list[DuplicateGroup], total_records: int) -> str:
    lines: list[str] = []
    lines.append(f"Scanned {total_records} record(s).")
    lines.append(f"Found {len(groups)} duplicate group(s).")
    lines.append("")

    for idx, group in enumerate(groups, start=1):
        lines.append(f"Group {idx}: {group.count} record(s)")
        lines.append(f"  Earliest date          : {group.earliest_date or '(none)'}")
        lines.append(f"  Normalized title       : {group.key[0]!r}")
        lines.append(f"  Normalized description : {group.key[1]!r}")
        lines.append(f"  IDs (sorted)           : {', '.join(group.ids)}")
        lines.append(
            f"  Dates                  : "
            f"{', '.join(d or '(none)' for d in group.dates)}"
        )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect duplicate records by normalized title+description."
    )
    parser.add_argument("input", help="Path to JSON file with records")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    try:
        records = load_records(args.input)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    groups = find_duplicate_groups(records)

    if args.json:
        payload = {
            "total_records": len(records),
            "duplicate_group_count": len(groups),
            "groups": [g.to_dict() for g in groups],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        sys.stdout.write(format_text_report(groups, len(records)))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())