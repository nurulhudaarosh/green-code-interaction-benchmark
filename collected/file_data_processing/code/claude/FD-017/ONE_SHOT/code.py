#!/usr/bin/env python3
"""
event_pivot.py - validate event records and pivot them into a
(date, region) x event_type count table.

Input record shape (dicts):
    {"date": "2026-10-01" | date | datetime,
     "region": "EMEA",
     "event_type": "Page View",
     "count": 3}            # optional, defaults to 1

Output rows (list of dicts), sorted by date then region:
    {"date": "2026-10-01", "region": "EMEA",
     "click": 4, "page_view": 7, "purchase": 0, "total": 11}

Determinism guarantees:
  * event-type columns are normalized (lowercase, non-alphanumerics -> "_")
    and sorted alphabetically, independent of input order
  * rows are sorted by (date, region); output never depends on dict/set order
  * every (date, region) row contains every event-type column (missing = 0)
"""

from __future__ import annotations

import csv
import io
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Iterable

TOTAL_COL = "total"
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


class ValidationError(ValueError):
    """Raised in strict mode; carries every problem found, not just the first."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        shown = "\n  ".join(errors[:20])
        more = f"\n  ... and {len(errors) - 20} more" if len(errors) > 20 else ""
        super().__init__(f"{len(errors)} invalid record(s):\n  {shown}{more}")


@dataclass
class PivotResult:
    columns: list[str]                       # full ordered header
    event_columns: list[str]                 # normalized event-type columns
    rows: list[dict[str, Any]]               # sorted, zero-filled
    rejected: list[tuple[int, str]] = field(default_factory=list)  # (index, reason)

    def to_csv(self) -> str:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=self.columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(self.rows)
        return buf.getvalue()


# --------------------------------------------------------------------------
# Validation / normalization
# --------------------------------------------------------------------------
def normalize_event_type(raw: str) -> str:
    """'Page View' / 'page-view ' / 'PAGE_VIEW' -> 'page_view'."""
    return _NON_ALNUM.sub("_", raw.strip().lower()).strip("_")


def _parse_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        try:
            # Handles "2026-10-01" and "2026-10-01T12:30:00" (and offsets on 3.11+)
            return datetime.fromisoformat(text).date()
        except ValueError:
            pass
    raise ValueError(f"unparseable date: {value!r}")


def _validate(record: Any) -> tuple[date, str, str, int]:
    """Return (date, region, event_col, count) or raise ValueError."""
    if not isinstance(record, dict):
        raise ValueError(f"record must be a dict, got {type(record).__name__}")

    missing = [k for k in ("date", "region", "event_type") if record.get(k) in (None, "")]
    if missing:
        raise ValueError(f"missing required field(s): {', '.join(missing)}")

    d = _parse_date(record["date"])

    region = record["region"]
    if not isinstance(region, str) or not region.strip():
        raise ValueError(f"invalid region: {region!r}")
    region = region.strip().upper()

    etype = record["event_type"]
    if not isinstance(etype, str):
        raise ValueError(f"invalid event_type: {etype!r}")
    col = normalize_event_type(etype)
    if not col:
        raise ValueError(f"event_type has no usable characters: {etype!r}")
    if col in ("date", "region", TOTAL_COL):
        raise ValueError(f"event_type {etype!r} collides with a reserved column name")

    count = record.get("count", 1)
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError(f"count must be a positive integer, got {count!r}")

    return d, region, col, count


# --------------------------------------------------------------------------
# Pivot
# --------------------------------------------------------------------------
def build_pivot(
    records: Iterable[Any],
    *,
    strict: bool = True,
    event_columns: Iterable[str] | None = None,
) -> PivotResult:
    """
    Validate, aggregate, and pivot records.

    strict=True   -> raise ValidationError listing every bad record.
    strict=False  -> skip bad records and report them in `rejected`.
    event_columns -> optional fixed column set (normalized names) so the schema
                     stays stable across runs even when some types are absent.
    """
    counts: dict[tuple[date, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    seen_types: set[str] = set()
    rejected: list[tuple[int, str]] = []

    for idx, rec in enumerate(records):
        try:
            d, region, col, n = _validate(rec)
        except ValueError as exc:
            rejected.append((idx, str(exc)))
            continue
        counts[(d, region)][col] += n
        seen_types.add(col)

    if strict and rejected:
        raise ValidationError([f"record #{i}: {msg}" for i, msg in rejected])

    fixed = {normalize_event_type(c) for c in event_columns} if event_columns else set()
    ev_cols = sorted(seen_types | fixed)
    columns = ["date", "region", *ev_cols, TOTAL_COL]

    rows: list[dict[str, Any]] = []
    for (d, region) in sorted(counts):               # date asc, then region asc
        cell = counts[(d, region)]
        row: dict[str, Any] = {"date": d.isoformat(), "region": region}
        for col in ev_cols:
            row[col] = cell.get(col, 0)              # fill missing with zero
        row[TOTAL_COL] = sum(row[c] for c in ev_cols)
        rows.append(row)

    return PivotResult(columns=columns, event_columns=ev_cols, rows=rows, rejected=rejected)


# --------------------------------------------------------------------------
# Demo / CLI-free entry point
# --------------------------------------------------------------------------
if __name__ == "__main__":
    sample = [
        {"date": "2026-10-02", "region": "apac", "event_type": "Purchase"},
        {"date": "2026-10-01", "region": "EMEA", "event_type": "Page View"},
        {"date": "2026-10-01", "region": "emea ", "event_type": "page-view", "count": 2},
        {"date": datetime(2026, 10, 1, 14, 30), "region": "AMER", "event_type": "Click"},
        {"date": "2026-10-02", "region": "EMEA", "event_type": "Click", "count": 4},
        # invalid records (skipped in lenient mode):
        {"date": "not-a-date", "region": "EMEA", "event_type": "Click"},
        {"date": "2026-10-03", "region": "", "event_type": "Click"},
        {"date": "2026-10-03", "region": "AMER", "event_type": "Click", "count": 0},
    ]

    try:
        build_pivot(sample, strict=True)
    except ValidationError as err:
        print("Strict mode failed as expected:\n", err, "\n", file=sys.stderr)

    result = build_pivot(sample, strict=False)
    print(result.to_csv())
    for idx, reason in result.rejected:
        print(f"rejected #{idx}: {reason}", file=sys.stderr)