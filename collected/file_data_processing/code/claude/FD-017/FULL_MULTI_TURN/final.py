"""
event_pivot.py

Validates event records, aggregates counts by (date, region), pivots EVERY
observed event type into its own column, fills absent combinations with 0,
and sorts rows.

Column order is deterministic and independent of record arrival order:
event types are Unicode-normalised, then sorted by a total-order key.

Malformed records (bad date, bad count, missing/blank fields, non-mapping
rows) are skipped and reported in `PivotResult.rejected`; processing never
terminates because of a bad record.
"""

from __future__ import annotations

import csv
import io
import logging
import math
import random
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Mapping

log = logging.getLogger(__name__)

INDEX_COLUMNS = ("date", "region")


class ValidationError(ValueError):
    """Raised internally when a single record fails validation."""


@dataclass(frozen=True)
class Event:
    date: date
    region: str
    event_type: str
    count: int


@dataclass
class PivotResult:
    columns: list[str]                 # ["date", "region", <one per event type>]
    rows: list[list[Any]]              # sorted, zero-filled
    rejected: list[tuple[int, str]]    # (record index, reason) for skipped records

    def to_dicts(self) -> list[dict[str, Any]]:
        return [dict(zip(self.columns, row)) for row in self.rows]

    def to_csv(self) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(self.columns)
        writer.writerows(self.rows)
        return buf.getvalue()

    def to_table(self) -> str:
        """Plain-text aligned table for quick inspection."""
        cells = [self.columns] + [[str(v) for v in r] for r in self.rows]
        widths = [max(len(r[i]) for r in cells) for i in range(len(self.columns))]
        lines = ["  ".join(c.ljust(w) for c, w in zip(r, widths)) for r in cells]
        lines.insert(1, "  ".join("-" * w for w in widths))
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y")


def _parse_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        try:  # ISO timestamps such as 2024-03-05T10:15:00
            return datetime.fromisoformat(text).date()
        except ValueError:
            pass
    raise ValidationError(f"invalid date: {value!r}")


def _parse_count(value: Any) -> int:
    """Accept non-negative whole numbers (int, integral float, numeric string)."""
    bad = ValidationError(f"invalid count: {value!r}")
    if isinstance(value, bool):  # bool is an int subclass; reject explicitly
        raise bad
    if isinstance(value, (int, float)):
        number: float | int = value
    elif isinstance(value, str):
        text = value.strip()
        try:
            number = int(text)
        except ValueError:
            try:
                number = float(text)
            except ValueError:
                raise bad from None
    else:
        raise bad

    if isinstance(number, float):
        if not math.isfinite(number) or not number.is_integer():
            raise bad
        number = int(number)
    if number < 0:
        raise bad
    return number


def _clean_text(value: Any, field: str, *, fold: bool) -> str:
    """Normalise to NFKC and collapse whitespace; optionally casefold."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"missing or invalid {field}: {value!r}")
    text = " ".join(unicodedata.normalize("NFKC", value).split())
    return text.casefold() if fold else text


def validate_record(record: Mapping[str, Any]) -> Event:
    """Validate and normalise one record into an Event (raises ValidationError)."""
    if not isinstance(record, Mapping):
        raise ValidationError(f"record is not a mapping: {record!r}")
    for key in ("date", "region", "event_type"):
        if key not in record:
            raise ValidationError(f"missing field: {key}")
    return Event(
        date=_parse_date(record["date"]),
        region=_clean_text(record["region"], "region", fold=False).title(),
        event_type=_clean_text(record["event_type"], "event_type", fold=True),
        # Absent count means one occurrence; a present-but-malformed one is rejected.
        count=_parse_count(record["count"]) if "count" in record else 1,
    )


# --------------------------------------------------------------------------
# Column ordering
# --------------------------------------------------------------------------

def _type_sort_key(event_type: str) -> tuple[str, str]:
    """Total order: casefolded name first, raw name as an explicit tie-break."""
    return (event_type.casefold(), event_type)


def ordered_type_columns(event_types: Iterable[str]) -> list[tuple[str, str]]:
    """
    Return [(event_type, column_label), ...] in a deterministic order that does
    not depend on the order of `event_types`.

    Labels are assigned while walking the sorted list, so collisions with the
    index columns (or with each other) always resolve the same way: the
    conflicting label is prefixed with "type_" until it is unique.
    """
    used = set(INDEX_COLUMNS)
    result: list[tuple[str, str]] = []
    for et in sorted(set(event_types), key=_type_sort_key):
        label = et
        while label in used:
            label = f"type_{label}"
        used.add(label)
        result.append((et, label))
    return result


# --------------------------------------------------------------------------
# Pivot
# --------------------------------------------------------------------------

def pivot_events(
    records: Iterable[Mapping[str, Any]],
    *,
    descending_dates: bool = False,
) -> PivotResult:
    """
    Build a (date, region) x event_type count table.

    - Every event type observed in a VALID record gets its own column.
      Column order is deterministic and independent of arrival order.
    - Every (date, region) pair that appears gets a row; combinations with no
      events are filled with 0.
    - Invalid records are skipped and listed in `PivotResult.rejected`;
      they never create rows or columns.

    descending_dates: sort newest date first (region still ascending).
    """
    counts: Counter[tuple[date, str, str]] = Counter()
    seen_types: set[str] = set()
    seen_keys: set[tuple[date, str]] = set()
    rejected: list[tuple[int, str]] = []

    for idx, rec in enumerate(records):
        try:
            ev = validate_record(rec)
        except ValidationError as exc:
            rejected.append((idx, str(exc)))
            log.warning("skipping record %d: %s", idx, exc)
            continue

        counts[(ev.date, ev.region, ev.event_type)] += ev.count
        seen_types.add(ev.event_type)
        seen_keys.add((ev.date, ev.region))

    typed_columns = ordered_type_columns(seen_types)

    sign = -1 if descending_dates else 1
    ordered_keys = sorted(seen_keys, key=lambda k: (sign * k[0].toordinal(), k[1]))

    rows = [
        [d.isoformat(), r] + [counts.get((d, r, et), 0) for et, _ in typed_columns]
        for d, r in ordered_keys
    ]
    columns = list(INDEX_COLUMNS) + [label for _, label in typed_columns]
    return PivotResult(columns, rows, rejected)


# --------------------------------------------------------------------------
# Demo
# --------------------------------------------------------------------------

if __name__ == "__main__":
    sample = [
        {"date": "2024-03-01", "region": "north", "event_type": "Login"},
        {"date": "2024-03-01", "region": "North ", "event_type": "login", "count": "3"},
        {"date": "2024-03-01", "region": "south", "event_type": "purchase", "count": 2},
        {"date": "2024/03/02", "region": "south", "event_type": "login"},
        {"date": "03/02/2024", "region": "north", "event_type": "error", "count": 1.0},
        {"date": "2024-03-02", "region": "north", "event_type": "date"},        # name clash
        {"date": "2024-03-02", "region": "north", "event_type": "cafe\u0301"},   # decomposed é
        {"date": "2024-03-02", "region": "north", "event_type": "caf\u00e9"},    # composed é
        {"date": "not-a-date", "region": "east", "event_type": "login"},         # bad date
        {"date": "2024-03-03", "region": "", "event_type": "login"},             # blank region
        "not even a dict",
    ]

    baseline = pivot_events(sample)
    print(baseline.to_table())
    print("\nRejected:")
    for idx, reason in baseline.rejected:
        print(f"  record {idx}: {reason}")

    # Determinism check: shuffled arrival order must give identical columns/rows.
    rng = random.Random(0)
    for _ in range(200):
        shuffled = sample[:]
        rng.shuffle(shuffled)
        again = pivot_events(shuffled)
        assert again.columns == baseline.columns, "column order changed!"
        assert again.rows == baseline.rows, "row content changed!"
    print("\nOK: 200 shuffled orderings produced identical columns and rows.")