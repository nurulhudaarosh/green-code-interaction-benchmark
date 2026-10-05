"""
event_pivot.py

Validate event records, then pivot them into one row per (date, region)
with one count column per event type. Standard library only.

Malformed records (bad dates, bad counts, missing fields, non-mappings, ...)
are skipped and reported in `PivotResult.errors`; they never stop processing.
Pass strict=True to get the old fail-fast behavior instead.
"""

from __future__ import annotations

import csv
import io
import math
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Mapping, Sequence


class RecordValidationError(ValueError):
    """Raised only in strict mode when one or more records are invalid."""

    def __init__(self, errors: Sequence[str]):
        self.errors = list(errors)
        super().__init__(
            f"{len(self.errors)} invalid record(s):\n" + "\n".join(self.errors)
        )


@dataclass(frozen=True)
class PivotResult:
    columns: list[str]               # ["date", "region", <event types...>]
    rows: list[dict[str, Any]]       # sorted, zero-filled
    errors: list[str]                # one message per skipped record
    processed: int = 0               # records that were counted

    @property
    def skipped(self) -> int:
        return len(self.errors)

    def to_csv(self) -> str:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=self.columns, lineterminator="\n")
        writer.writeheader()
        for row in self.rows:
            writer.writerow({**row, "date": row["date"].isoformat()})
        return buf.getvalue()


def _parse_date(value: Any) -> date:
    if isinstance(value, datetime):          # check before date: datetime is a date
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        try:
            return date.fromisoformat(text)
        except ValueError:
            pass
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except ValueError:
            raise ValueError(f"invalid date: {value!r}") from None
    raise TypeError(f"date must be a string or date, got {type(value).__name__}")


def _parse_count(value: Any) -> int:
    """Return a non-negative whole number, or raise ValueError/TypeError."""
    if isinstance(value, bool):              # bool is an int subclass; reject it
        raise TypeError("count must be a number, got bool")
    if isinstance(value, int):
        number = value
    elif isinstance(value, float):
        if not math.isfinite(value) or not value.is_integer():
            raise ValueError(f"count must be a whole number, got {value}")
        number = int(value)
    elif isinstance(value, str):
        try:
            number = int(value.strip())
        except ValueError:
            raise ValueError(f"invalid count: {value!r}") from None
    else:
        raise TypeError(f"count must be a number, got {type(value).__name__}")
    if number < 0:
        raise ValueError(f"count must be non-negative, got {number}")
    return number


def _clean_text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string, got {type(value).__name__}")
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValueError(f"{field} must not be empty")
    return cleaned


def validate_record(record: Mapping[str, Any]) -> tuple[date, str, str, int]:
    """
    Return (date, region, event_type, count) normalized.

    'count' is optional and defaults to 1. Raises ValueError/TypeError
    when the record is malformed.
    """
    if not isinstance(record, Mapping):
        raise TypeError("record must be a mapping")
    missing = [k for k in ("date", "region", "event_type") if k not in record]
    if missing:
        raise ValueError(f"missing field(s): {', '.join(missing)}")

    d = _parse_date(record["date"])
    region = _clean_text(record["region"], "region")
    event_type = _clean_text(record["event_type"], "event_type").lower()
    count = _parse_count(record["count"]) if "count" in record else 1
    return d, region, event_type, count


def pivot_events(
    records: Iterable[Any],
    *,
    strict: bool = False,
    event_types: Sequence[str] | None = None,
) -> PivotResult:
    """
    Pivot event records into counts by (date, region) x event_type.

    Args:
        records: iterable of mappings with keys 'date', 'region',
                 'event_type' and an optional 'count' (default 1).
        strict: False (default) skips malformed records and reports them in
                `errors`; True raises RecordValidationError after scanning
                all records.
        event_types: optional fixed column list (normalized to lowercase).
                     If omitted, columns are the sorted distinct event types
                     seen. Types outside a fixed list are skipped as invalid.

    Returns:
        PivotResult with deterministic columns and rows sorted by (date, region).
    """
    allowed = None
    if event_types is not None:
        allowed = sorted({e.strip().lower() for e in event_types if e and e.strip()})

    counts: Counter[tuple[date, str, str]] = Counter()
    keys: set[tuple[date, str]] = set()
    seen_types: set[str] = set()
    errors: list[str] = []
    processed = 0

    for idx, record in enumerate(records):
        try:
            d, region, etype, count = validate_record(record)
            if allowed is not None and etype not in allowed:
                raise ValueError(f"unknown event_type '{etype}'")
        except (ValueError, TypeError, OverflowError) as exc:
            errors.append(f"record {idx}: {exc}")
            continue                          # skip, keep going

        counts[(d, region, etype)] += count
        keys.add((d, region))
        seen_types.add(etype)
        processed += 1

    if errors and strict:
        raise RecordValidationError(errors)

    type_columns = allowed if allowed is not None else sorted(seen_types)
    columns = ["date", "region", *type_columns]

    rows = []
    for d, region in sorted(keys):            # date ascending, then region
        row: dict[str, Any] = {"date": d, "region": region}
        for etype in type_columns:
            row[etype] = counts.get((d, region, etype), 0)   # zero-fill
        rows.append(row)

    return PivotResult(columns=columns, rows=rows, errors=errors, processed=processed)


if __name__ == "__main__":
    sample = [
        {"date": "2024-03-02", "region": "West", "event_type": "Click"},
        {"date": "2024-03-01", "region": "East", "event_type": "view", "count": "3"},
        {"date": "2024-03-01", "region": "East", "event_type": "VIEW", "count": 2},
        {"date": "2024-03-01", "region": "West", "event_type": "purchase"},
        {"date": "2024-03-02", "region": "West", "event_type": "click", "count": 2},
        {"date": "not-a-date", "region": "East", "event_type": "view"},          # bad date
        {"date": "2024-03-01", "region": "East", "event_type": "view", "count": "abc"},
        {"date": "2024-03-01", "region": "East", "event_type": "view", "count": -1},
        {"date": "2024-03-01", "region": "East", "event_type": "view", "count": 2.5},
        {"date": "2024-03-01", "region": "East", "event_type": "view", "count": True},
        {"date": "2024-03-02", "region": "  ", "event_type": "view"},            # bad region
        "oops",                                                                  # not a mapping
        {"date": "2024-02-30", "region": "East", "event_type": "view"},          # impossible date
    ]

    result = pivot_events(sample)             # lenient by default
    print(result.to_csv())
    print(f"processed={result.processed} skipped={result.skipped}")
    for err in result.errors:
        print("skipped ->", err)