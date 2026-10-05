#!/usr/bin/env python3
"""
Per-sensor hourly time-series gap filler.

- Sorts readings per sensor by timestamp
- Fills missing *interior* hourly timestamps via linear interpolation
  (no extrapolation before the first or after the last reading)
- Marks inserted rows with `interpolated=True`
- Deterministic output: sorted by (sensor_id, timestamp), fixed float format,
  fixed column order, LF line endings

Input CSV columns : sensor_id, timestamp, value
Output CSV columns: sensor_id, timestamp, value, interpolated

Usage:
    python fill_gaps.py input.csv output.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Tuple

HOUR = timedelta(hours=1)
OUTPUT_COLUMNS = ("sensor_id", "timestamp", "value", "interpolated")


@dataclass(frozen=True)
class Reading:
    sensor_id: str
    timestamp: datetime  # timezone-aware, UTC
    value: float
    interpolated: bool = False


def parse_timestamp(text: str) -> datetime:
    """Parse ISO-8601; naive values are treated as UTC. Result is UTC."""
    text = text.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def format_value(v: float) -> str:
    # repr-based shortest round-trip formatting is deterministic across runs
    return repr(float(v))


def normalize(readings: Iterable[Reading]) -> Dict[str, List[Reading]]:
    """Group by sensor, sort by timestamp, collapse duplicate timestamps.

    Duplicates at the same (sensor, timestamp) are averaged, so the result
    does not depend on input order.
    """
    grouped: Dict[str, Dict[datetime, List[float]]] = defaultdict(lambda: defaultdict(list))
    for r in readings:
        grouped[r.sensor_id][r.timestamp].append(r.value)

    result: Dict[str, List[Reading]] = {}
    for sensor_id in sorted(grouped):
        rows = []
        for ts in sorted(grouped[sensor_id]):
            vals = sorted(grouped[sensor_id][ts])  # sorted => order-independent sum
            rows.append(Reading(sensor_id, ts, math.fsum(vals) / len(vals)))
        result[sensor_id] = rows
    return result


def interpolate_sensor(rows: List[Reading]) -> List[Reading]:
    """Fill missing interior hourly timestamps for one sorted sensor series."""
    if not rows:
        return []

    out: List[Reading] = [rows[0]]
    for prev, curr in zip(rows, rows[1:]):
        gap = curr.timestamp - prev.timestamp
        # Only fill when the gap is a whole number of hours > 1.
        # Off-grid gaps (e.g. 90 min) are left untouched rather than guessed.
        if gap > HOUR and gap % HOUR == timedelta(0):
            steps = int(gap / HOUR)
            dv = curr.value - prev.value
            for k in range(1, steps):
                frac = k / steps
                out.append(
                    Reading(
                        prev.sensor_id,
                        prev.timestamp + k * HOUR,
                        prev.value + dv * frac,
                        interpolated=True,
                    )
                )
        out.append(curr)
    return out


def fill_gaps(readings: Iterable[Reading]) -> List[Reading]:
    """Full pipeline: normalize, interpolate per sensor, emit in stable order."""
    by_sensor = normalize(readings)
    result: List[Reading] = []
    for sensor_id in sorted(by_sensor):
        result.extend(interpolate_sensor(by_sensor[sensor_id]))
    return result


def read_csv(path: str) -> List[Reading]:
    readings: List[Reading] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = {"sensor_id", "timestamp", "value"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Input CSV missing columns: {sorted(missing)}")
        for lineno, row in enumerate(reader, start=2):
            raw = (row["value"] or "").strip()
            if raw == "":
                continue  # blank reading: treated as a gap
            try:
                value = float(raw)
                ts = parse_timestamp(row["timestamp"])
            except ValueError as exc:
                raise ValueError(f"Line {lineno}: {exc}") from exc
            if not math.isfinite(value):
                continue  # NaN/inf treated as a gap
            readings.append(Reading(row["sensor_id"].strip(), ts, value))
    return readings


def write_csv(path: str, rows: Iterable[Reading]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(OUTPUT_COLUMNS)
        for r in rows:
            writer.writerow(
                (
                    r.sensor_id,
                    format_timestamp(r.timestamp),
                    format_value(r.value),
                    "true" if r.interpolated else "false",
                )
            )


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="Input CSV path")
    parser.add_argument("output", help="Output CSV path")
    args = parser.parse_args(argv)

    try:
        filled = fill_gaps(read_csv(args.input))
        write_csv(args.output, filled)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())