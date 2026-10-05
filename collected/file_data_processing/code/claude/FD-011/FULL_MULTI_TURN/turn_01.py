#!/usr/bin/env python3
"""
Time-series utility: per-sensor sorting, hourly gap filling via linear
interpolation, inserted-row marking, and deterministic CSV output.

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


@dataclass(frozen=True)
class Reading:
    sensor: str
    ts: datetime  # timezone-aware, UTC
    value: Optional[float]
    inserted: bool = False


def parse_timestamp(raw: str) -> datetime:
    """Parse an ISO-8601 timestamp; naive values are treated as UTC."""
    s = raw.strip()
    if s.endswith("Z") or s.endswith("z"):
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


def interpolate_sensor(readings: List[Reading]) -> List[Reading]:
    """
    Given one sensor's readings, sort by time, collapse duplicate timestamps
    (last occurrence in input order wins), and insert hourly rows between
    consecutive readings that have valid values. Only interior gaps are
    filled; nothing is extrapolated before the first or after the last row.
    Gaps adjacent to an unreadable (None) value are left unfilled.
    """
    # Stable sort keeps input order among equal timestamps; the dict then
    # keeps the last one seen for each timestamp.
    ordered = sorted(readings, key=lambda r: r.ts)
    dedup: Dict[datetime, Reading] = {}
    for r in ordered:
        dedup[r.ts] = r
    rows = [dedup[t] for t in sorted(dedup)]

    out: List[Reading] = []
    for i, cur in enumerate(rows):
        out.append(cur)
        if i + 1 == len(rows):
            break
        nxt = rows[i + 1]
        gap = nxt.ts - cur.ts
        if gap <= HOUR or cur.value is None or nxt.value is None:
            continue

        total_seconds = gap.total_seconds()
        t = cur.ts + HOUR
        while t < nxt.ts:
            frac = (t - cur.ts).total_seconds() / total_seconds
            val = cur.value + (nxt.value - cur.value) * frac
            out.append(Reading(cur.sensor, t, val, inserted=True))
            t += HOUR
    return out


def process(readings: Iterable[Reading]) -> List[Reading]:
    by_sensor: Dict[str, List[Reading]] = {}
    for r in readings:
        by_sensor.setdefault(r.sensor, []).append(r)

    result: List[Reading] = []
    for sensor in sorted(by_sensor):
        result.extend(interpolate_sensor(by_sensor[sensor]))
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
            readings.append(
                Reading(sensor, ts, parse_value(row[value_col] or ""))
            )
    return readings, skipped


def write_csv(
    path: str, rows: List[Reading],
    sensor_col: str, time_col: str, value_col: str,
) -> None:
    # newline="" + explicit "\n" terminator => identical bytes on all platforms.
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow([sensor_col, time_col, value_col, "inserted"])
        for r in rows:
            writer.writerow([
                r.sensor,
                format_timestamp(r.ts),
                format_value(r.value),
                "true" if r.inserted else "false",
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

    write_csv(args.output, process(readings),
              args.sensor_col, args.time_col, args.value_col)
    return 0


if __name__ == "__main__":
    sys.exit(main())