#!/usr/bin/env python3
"""
Time-series utility: per-sensor sorting, hourly gap filling via linear
interpolation, marking of inserted rows, and deterministic output.

Input CSV columns:  sensor_id, timestamp, value
Output CSV columns: sensor_id, timestamp, value, interpolated

Behavior:
  * Rows are grouped by sensor_id and sorted by timestamp.
  * Only *interior* gaps are filled (between the first and last reading of
    each sensor); no extrapolation occurs before the first or after the last.
  * Missing hourly timestamps are inserted with linearly interpolated values.
  * Inserted rows have interpolated=1; original rows have interpolated=0.
  * Output is deterministic: sensors sorted lexicographically, timestamps
    ascending, fixed float formatting, UTC ISO-8601 timestamps, LF line endings.

Timestamps are normalized to UTC. Naive timestamps are assumed to be UTC.
Timestamps are treated as points on an hourly grid anchored at each gap's
left endpoint (so off-grid readings, e.g. 10:30, produce fills at 11:30, ...).
Duplicate (sensor, timestamp) readings are collapsed by averaging.
"""

import argparse
import csv
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Tuple

HOUR = timedelta(hours=1)
TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
VALUE_PRECISION = 6

Row = Tuple[str, datetime, float, int]  # sensor, ts, value, interpolated flag


def parse_timestamp(text: str) -> datetime:
    """Parse an ISO-8601 timestamp into an aware UTC datetime."""
    s = text.strip()
    if s.endswith(("Z", "z")):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_value(v: float) -> str:
    """Fixed-precision, locale-independent formatting (avoids '-0.000000')."""
    s = f"{v:.{VALUE_PRECISION}f}"
    if float(s) == 0.0:
        s = f"{0.0:.{VALUE_PRECISION}f}"
    return s


def read_readings(rows: Iterable[Dict[str, str]]) -> Dict[str, Dict[datetime, List[float]]]:
    """Group raw readings by sensor and timestamp. Skips blank/non-finite values."""
    grouped: Dict[str, Dict[datetime, List[float]]] = defaultdict(lambda: defaultdict(list))
    for lineno, row in enumerate(rows, start=2):
        sensor = (row.get("sensor_id") or "").strip()
        ts_text = (row.get("timestamp") or "").strip()
        val_text = (row.get("value") or "").strip()
        if not sensor or not ts_text:
            raise ValueError(f"Line {lineno}: missing sensor_id or timestamp")
        if val_text == "":
            continue  # missing measurement: treated as an absent reading
        try:
            value = float(val_text)
        except ValueError:
            raise ValueError(f"Line {lineno}: invalid value {val_text!r}") from None
        if not math.isfinite(value):
            continue
        try:
            ts = parse_timestamp(ts_text)
        except ValueError:
            raise ValueError(f"Line {lineno}: invalid timestamp {ts_text!r}") from None
        grouped[sensor][ts].append(value)
    return grouped


def fill_sensor(sensor: str, readings: Dict[datetime, List[float]]) -> List[Row]:
    """Sort one sensor's readings and fill interior hourly gaps linearly."""
    points = sorted((ts, sum(vs) / len(vs)) for ts, vs in readings.items())
    out: List[Row] = []
    for i, (ts, val) in enumerate(points):
        out.append((sensor, ts, val, 0))
        if i + 1 == len(points):
            break
        next_ts, next_val = points[i + 1]
        span = (next_ts - ts) / HOUR  # gap length in hours (may be fractional)
        k = 1
        while ts + k * HOUR < next_ts:
            fill_ts = ts + k * HOUR
            frac = (fill_ts - ts) / (next_ts - ts)
            fill_val = val + (next_val - val) * frac
            out.append((sensor, fill_ts, fill_val, 1))
            k += 1
    return out


def process(rows: Iterable[Dict[str, str]]) -> List[Row]:
    grouped = read_readings(rows)
    result: List[Row] = []
    for sensor in sorted(grouped):
        result.extend(fill_sensor(sensor, grouped[sensor]))
    return result


def write_rows(rows: List[Row], out) -> None:
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["sensor_id", "timestamp", "value", "interpolated"])
    for sensor, ts, val, flag in rows:
        writer.writerow([sensor, ts.strftime(TS_FORMAT), format_value(val), flag])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("input", help="input CSV path, or '-' for stdin")
    parser.add_argument("output", help="output CSV path, or '-' for stdout")
    args = parser.parse_args(argv)

    try:
        if args.input == "-":
            result = process(csv.DictReader(sys.stdin))
        else:
            with open(args.input, newline="", encoding="utf-8") as f:
                result = process(csv.DictReader(f))
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.output == "-":
        write_rows(result, sys.stdout)
    else:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            write_rows(result, f)
    return 0


if __name__ == "__main__":
    sys.exit(main())