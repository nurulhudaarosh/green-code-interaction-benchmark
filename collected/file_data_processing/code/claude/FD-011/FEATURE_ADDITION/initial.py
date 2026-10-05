#!/usr/bin/env python3
"""
Sensor time-series gap filler.

- Sorts readings per sensor by timestamp
- Fills missing *interior* hourly timestamps via linear interpolation
  (no extrapolation before the first / after the last reading)
- Marks inserted rows with `interpolated = True`
- Writes deterministic output (stable ordering, fixed formatting)

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
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Tuple

HOUR = timedelta(hours=1)
TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

Reading = Tuple[datetime, float]
Row = Tuple[str, datetime, float, bool]


def parse_timestamp(raw: str) -> datetime:
    """Parse an ISO-8601 timestamp; naive values are treated as UTC."""
    raw = raw.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_timestamp(dt: datetime) -> str:
    return dt.strftime(TS_FORMAT)


def format_value(value: float) -> str:
    """Fixed, locale-independent float formatting (deterministic)."""
    if value == 0:
        value = 0.0  # normalise -0.0
    return f"{value:.6f}"


def read_readings(path: str) -> Dict[str, List[Reading]]:
    by_sensor: Dict[str, List[Reading]] = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"sensor_id", "timestamp", "value"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required column(s): {sorted(missing)}")
        for lineno, rec in enumerate(reader, start=2):
            sensor = rec["sensor_id"].strip()
            raw_val = (rec["value"] or "").strip()
            if not sensor:
                raise ValueError(f"Line {lineno}: empty sensor_id")
            try:
                ts = parse_timestamp(rec["timestamp"])
            except ValueError as exc:
                raise ValueError(f"Line {lineno}: bad timestamp: {exc}") from exc
            if raw_val == "":
                continue  # blank reading treated as missing
            try:
                val = float(raw_val)
            except ValueError as exc:
                raise ValueError(f"Line {lineno}: bad value {raw_val!r}") from exc
            if not math.isfinite(val):
                continue  # NaN / inf treated as missing
            by_sensor[sensor].append((ts, val))
    return by_sensor


def dedupe_sorted(readings: List[Reading]) -> List[Reading]:
    """
    Sort by timestamp and collapse duplicate timestamps deterministically:
    duplicates are averaged (order-independent since values are sorted first).
    """
    readings = sorted(readings, key=lambda r: (r[0], r[1]))
    out: List[Reading] = []
    i = 0
    while i < len(readings):
        j = i
        vals = []
        while j < len(readings) and readings[j][0] == readings[i][0]:
            vals.append(readings[j][1])
            j += 1
        out.append((readings[i][0], math.fsum(vals) / len(vals)))
        i = j
    return out


def fill_sensor(sensor: str, readings: List[Reading]) -> List[Row]:
    """
    Return original + interpolated rows for one sensor, in timestamp order.
    Only whole-hour steps between consecutive readings are filled; if a
    reading is off the hourly grid, gaps are stepped from the earlier reading.
    """
    readings = dedupe_sorted(readings)
    rows: List[Row] = []
    for idx, (ts, val) in enumerate(readings):
        rows.append((sensor, ts, val, False))
        if idx + 1 == len(readings):
            break
        next_ts, next_val = readings[idx + 1]
        total = next_ts - ts
        cursor = ts + HOUR
        while cursor < next_ts:
            frac = (cursor - ts) / total  # timedelta / timedelta -> float
            interp = val + (next_val - val) * frac
            rows.append((sensor, cursor, interp, True))
            cursor += HOUR
    return rows


def process(by_sensor: Dict[str, List[Reading]]) -> Iterable[Row]:
    for sensor in sorted(by_sensor):  # deterministic sensor ordering
        yield from fill_sensor(sensor, by_sensor[sensor])


def write_rows(path: str, rows: Iterable[Row]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["sensor_id", "timestamp", "value", "interpolated"])
        for sensor, ts, val, inserted in rows:
            writer.writerow(
                [sensor, format_timestamp(ts), format_value(val), "true" if inserted else "false"]
            )


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fill missing interior hourly sensor readings.")
    parser.add_argument("input", help="Input CSV (sensor_id,timestamp,value)")
    parser.add_argument("output", help="Output CSV path")
    args = parser.parse_args(argv)

    try:
        data = read_readings(args.input)
        write_rows(args.output, process(data))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())