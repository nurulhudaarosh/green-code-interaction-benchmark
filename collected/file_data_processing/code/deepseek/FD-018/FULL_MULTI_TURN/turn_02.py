"""
Duplicate-record detector.

Normalization rules (deliberately conservative):
  - Case differences are ignored (casefold).
  - Any run of whitespace (spaces, tabs, newlines, NBSP, etc.) is
    collapsed to a single space and stripped from both ends.
  - Punctuation, accents, and everything else are preserved, so
    "Hello, World!" and "Hello World" are NOT considered duplicates.

Records are grouped by exact normalized (title, description) match.
Reports are fully deterministic:
  - Groups are ordered by (normalized_title, normalized_description).
  - IDs within a group are ordered by (date, record_id).
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

# Collapse any Unicode whitespace run (including NBSP, tabs, newlines).
_WHITESPACE_RE = re.compile(r"\s+", flags=re.UNICODE)


def normalize_text(value: Any) -> str:
    """Normalize for case-insensitive, whitespace-insensitive matching.

    Steps:
      1. Coerce to string (None -> "").
      2. Unicode NFKC normalization (folds NBSP -> space, etc.).
      3. Casefold (locale-independent, handles ß -> ss, etc.).
      4. Collapse whitespace runs to a single space, then strip.

    Punctuation and accents are intentionally preserved.
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.casefold()
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Record:
    record_id: str
    title: str
    description: str
    date: str = ""  # ISO-8601 string preferred; used only for ordering

    @property
    def norm_title(self) -> str:
        return normalize_text(self.title)

    @property
    def norm_description(self) -> str:
        return normalize_text(self.description)

    @property
    def key(self) -> tuple[str, str]:
        return (self.norm_title, self.norm_description)


@dataclass
class DuplicateGroup:
    norm_title: str
    norm_description: str
    entries: list[Record] = field(default_factory=list)

    @property
    def record_ids(self) -> list[str]:
        return [r.record_id for r in self.entries]

    def as_dict(self) -> dict[str, Any]:
        return {
            "normalized_title": self.norm_title,
            "normalized_description": self.norm_description,
            "count": len(self.entries),
            "record_ids": self.record_ids,
            "entries": [
                {
                    "record_id": r.record_id,
                    "date": r.date,
                    "title": r.title,
                    "description": r.description,
                }
                for r in self.entries
            ],
        }


# ---------------------------------------------------------------------------
# Date handling (for deterministic ordering within a group)
# ---------------------------------------------------------------------------

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S%z",
)


def parse_date_sortkey(value: Any) -> tuple[int, str]:
    """Return a sort key that never mixes types.

    (0, iso)  -> successfully parsed date
    (1, raw)  -> present but unparsed
    (2, "")   -> missing
    """
    if value is None or value == "":
        return (2, "")
    text = str(value).strip()
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return (0, dt.isoformat())
    except ValueError:
        pass
    for fmt in _DATE_FORMATS:
        try:
            return (0, datetime.strptime(text, fmt).isoformat())
        except ValueError:
            continue
    return (1, text)


# ---------------------------------------------------------------------------
# Core detector
# ---------------------------------------------------------------------------

def find_duplicate_groups(
    records: Iterable[Record],
    *,
    min_group_size: int = 2,
    include_singletons: bool = False,
) -> list[DuplicateGroup]:
    """Group records by exact normalized (title, description) match."""
    buckets: dict[tuple[str, str], list[Record]] = defaultdict(list)
    for rec in records:
        buckets[rec.key].append(rec)

    threshold = 1 if include_singletons else max(min_group_size, 1)

    groups: list[DuplicateGroup] = []
    for key in sorted(buckets.keys()):
        entries = buckets[key]
        if len(entries) < threshold:
            continue
        entries_sorted = sorted(
            entries,
            key=lambda r: (parse_date_sortkey(r.date), r.record_id),
        )
        groups.append(
            DuplicateGroup(
                norm_title=key[0],
                norm_description=key[1],
                entries=entries_sorted,
            )
        )

    groups.sort(key=lambda g: (g.norm_title, g.norm_description))
    return groups


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_records_from_json(path: str | Path) -> list[Record]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("records", [])
    return [_coerce_record(item) for item in data]


def load_records_from_csv(
    path: str | Path,
    *,
    id_field: str = "id",
    title_field: str = "title",
    description_field: str = "description",
    date_field: str = "date",
) -> list[Record]:
    records: list[Record] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            records.append(
                Record(
                    record_id=str(row.get(id_field, "")),
                    title=row.get(title_field, "") or "",
                    description=row.get(description_field, "") or "",
                    date=row.get(date_field, "") or "",
                )
            )
    return records


def _coerce_record(item: dict[str, Any]) -> Record:
    return Record(
        record_id=str(item.get("id") or item.get("record_id") or ""),
        title=str(item.get("title") or ""),
        description=str(item.get("description") or ""),
        date=str(item.get("date") or ""),
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def format_report(
    groups: Sequence[DuplicateGroup],
    *,
    total_records: int | None = None,
    as_json: bool = False,
) -> str:
    if as_json:
        return json.dumps(
            {
                "total_records": total_records,
                "duplicate_group_count": len(groups),
                "duplicate_record_count": sum(len(g.entries) for g in groups),
                "groups": [g.as_dict() for g in groups],
            },
            indent=2,
            ensure_ascii=False,
        )

    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("DUPLICATE RECORD REPORT")
    lines.append("=" * 72)
    if total_records is not None:
        lines.append(f"Total records scanned : {total_records}")
    lines.append(f"Duplicate groups      : {len(groups)}")
    lines.append(
        f"Duplicate records     : {sum(len(g.entries) for g in groups)}"
    )
    lines.append("")

    if not groups:
        lines.append("No duplicate groups found.")
        return "\n".join(lines)

    for idx, group in enumerate(groups, start=1):
        lines.append(f"[Group {idx}] {len(group.entries)} records")
        lines.append(f"  Title (norm)      : {group.norm_title!r}")
        lines.append(f"  Description (norm): {group.norm_description!r}")
        lines.append("  Records (by date):")
        for rec in group.entries:
            lines.append(
                f"    - id={rec.record_id!r}  date={rec.date!r}  "
                f"title={rec.title!r}"
            )
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def detect_duplicates(
    records: Iterable[Record],
    *,
    min_group_size: int = 2,
    include_singletons: bool = False,
) -> list[DuplicateGroup]:
    return find_duplicate_groups(
        records,
        min_group_size=min_group_size,
        include_singletons=include_singletons,
    )


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample = [
        Record("A1", "Hello World", "First post.", "2024-01-01"),
        Record("A2", "hello world", "first post.", "2024-01-02"),
        Record("A3", "HELLO    world", "  FIRST   post.  ", "2024-01-03"),
        # Punctuation is preserved -> distinct group from A*
        Record("A4", "Hello, World!", "First post.", "2024-01-04"),
        Record("B1", "Unique title", "Unique description", "2024-02-01"),
        # Accents preserved; case + whitespace folded
        Record("C1", "Café Münster", "Über story", "2024-03-01"),
        Record("C2", "café   münster", "ÜBER story", "2024-03-02"),
        # Empty / whitespace-only collapse to the same empty key
        Record("D1", "", "", "2024-04-01"),
        Record("D2", "   ", "\t\n", "2024-04-02"),
    ]

    groups = detect_duplicates(sample)
    print(format_report(groups, total_records=len(sample)))
    print("-" * 72)
    print("JSON view:")
    print(format_report(groups, total_records=len(sample), as_json=True))