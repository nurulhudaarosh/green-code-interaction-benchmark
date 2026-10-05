#!/usr/bin/env python3
"""
Time-series utility: per-sensor chronological sorting, hourly gap filling via
linear interpolation, filled-row marking, and deterministic CSV output.

Rules
-----
* Input rows may arrive in any order. Each sensor's readings are sorted by UTC
  time BEFORE any gap detection happens.
* Every missing interior hour is inserted, including runs of many consecutive
  missing hours. Inserted rows get status "filled"; original rows "original".
* Values are linearly interpolated between the nearest valid readings on either
  side of each missing hour, so a run of N missing hours gets N evenly spaced
  values on the straight line between its two anchors.
* No extrapolation: nothing is inserted before a sensor's first valid
  observation or after its last valid observation.
* Blank/invalid readings that already exist are kept as-is (never overwritten).

Usage:
    python fill_sensor_gaps.py input.csv output.csv \
        [--sensor-col sensor_id] [--time-col timestamp] [--value-col value]
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Tuple

HOUR = timedelta(hours=1)
STATUS_COL = "status"
STATUS_ORIGINAL = "original"
STATUS_FILLED = "filled"


@dataclass(frozen=True)
class Reading:
    sensor: str
    ts: datetime  # timezone-aware, UTC
    value: Optional[float]
    filled: bool = False


def parse_timestamp(raw: str) -> datetime:
    """Parse an ISO-8601 timestamp; naive values are treated as UTC."""
    s = raw.strip()
    if s.endswith(("Z", "z")):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_value(raw: str) -> Optional[float]:
    """Return a finite float, or None for blank/NaN/non-finite values."""
    s = raw.strip()
    if not s:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def format_value(v: Optional[float]) -> str:
    # repr() gives the shortest round-trip representation: deterministic.
    return "" if v is None else repr(float(v))


def sort_and_dedupe(readings: List[Reading]) -> List[Reading]:
    """
    Order one sensor's readings chronologically and collapse duplicate
    timestamps. The sort is stable, so among equal timestamps the original
    input order is preserved and the LAST occurrence wins.
    """
    ordered = sorted(readings, key=lambda r: r.ts)
    latest: Dict[datetime, Reading] = {}
    for r in ordered:
        latest[r.ts] = r
    return [latest[t] for t in sorted(latest)]


def fill_gaps(rows: List[Reading]) -> List[Reading]:
    """
    `rows` MUST already be chronologically sorted and de-duplicated.

    Between every pair of consecutive rows more than one hour apart, insert a
    row at each missing hourly step (previous_ts + k hours, k = 1, 2, ...)
    while the step is still before the next row. That handles any number of
    consecutive missing hours.

    Each inserted value is interpolated on the straight line between the
    nearest valid reading at/before the gap and the nearest valid reading
    at/after it. Gaps are only filled when timestamps lie strictly inside the
    span [first valid observation, last valid observation]; anything before
    the first valid reading or after the last valid reading is left empty.
    """
    valid_idx = [i for i, r in enumerate(rows) if r.value is not None]
    if len(valid_idx) < 2:
        return list(rows)  # nothing to interpolate between

    first_valid_ts = rows[valid_idx[0]].ts
    last_valid_ts = rows[valid_idx[-1]].ts

    n = len(rows)

    # prev_valid[i]: index of nearest valid row at or before i (or -1)
    prev_valid = [-1] * n
    last = -1
    for i, r in enumerate(rows):
        if r.value is not None:
            last = i
        prev_valid[i] = last

    # next_valid[i]: index of nearest valid row at or after i (or -1)
    next_valid = [-1] * n
    nxt_idx = -1
    for i in range(n - 1, -1, -1):
        if rows[i].value is not None:
            nxt_idx = i
        next_valid[i] = nxt_idx

    out: List[Reading] = []
    for i in range(n - 1):
        cur, nxt = rows[i], rows[i + 1]
        out.append(cur)

        if nxt.ts - cur.ts <= HOUR:
            continue  # no missing hour between these two rows

        lo, hi = prev_valid[i], next_valid[i + 1]
        if lo == -1 or hi == -1:
            continue  # no valid anchor on one side: would be extrapolation

        a, b = rows[lo], rows[hi]
        span = b.ts - a.ts  # > 0 because timestamps are unique and sorted

        t = cur.ts + HOUR
        while t < nxt.ts:
            # Defensive bound check: never fill outside the valid span.
            if first_valid_ts < t < last_valid_ts:
                frac = (t - a.ts) / span  # timedelta / timedelta -> float
                val = a.value + (b.value - a.value) * frac
                out.append(Reading(cur.sensor, t, val, filled=True))
            t += HOUR

    out.append(rows[-1])
    return out


def process(readings: Iterable[Reading]) -> List[Reading]:
    """Group by sensor (sorted by id), sort each group by time, then fill gaps."""
    by_sensor: Dict[str, List[Reading]] = {}
    for r in readings:
        by_sensor.setdefault(r.sensor, []).append(r)

    result: List[Reading] = []
    for sensor in sorted(by_sensor):
        chronological = sort_and_dedupe(by_sensor[sensor])  # sort FIRST
        result.extend(fill_gaps(chronological))             # then detect gaps
    return result


def read_csv(
    path: str, sensor_col: str, time_col: str, value_col: str
) -> Tuple[List[Reading], List[str]]:
    readings: List[Reading] = []
    skipped: List[str] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [
            c for c in (sensor_col, time_col, value_col)
            if c not in (reader.fieldnames or [])
        ]
        if missing:
            raise ValueError(f"Missing required column(s): {', '.join(missing)}")
        for lineno, row in enumerate(reader, start=2):
            try:
                sensor = (row[sensor_col] or "").strip()
                if not sensor:
                    raise ValueError("empty sensor id")
                ts = parse_timestamp(row[time_col] or "")
            except (ValueError, TypeError) as exc:
                skipped.append(f"line {lineno}: {exc}")
                continue
            readings.append(Reading(sensor, ts, parse_value(row[value_col] or "")))
    return readings, skipped


def write_csv(
    path: str, rows: List[Reading],
    sensor_col: str, time_col: str, value_col: str,
) -> None:
    # newline="" + explicit "\n" terminator => identical bytes on all platforms.
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow([sensor_col, time_col, value_col, STATUS_COL])
        for r in rows:
            writer.writerow([
                r.sensor,
                format_timestamp(r.ts),
                format_value(r.value),
                STATUS_FILLED if r.filled else STATUS_ORIGINAL,
            ])


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--sensor-col", default="sensor_id")
    p.add_argument("--time-col", default="timestamp")
    p.add_argument("--value-col", default="value")
    args = p.parse_args(argv)

    try:
        readings, skipped = read_csv(
            args.input, args.sensor_col, args.time_col, args.value_col
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for msg in skipped:
        print(f"warning: skipped {msg}", file=sys.stderr)

    try:
        write_csv(args.output, process(readings),
                  args.sensor_col, args.time_col, args.value_col)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())