from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Sequence

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"


def parse_timestamp(value: str) -> datetime:
    return datetime.strptime(value.strip(), TIMESTAMP_FORMAT)


def format_timestamp(value: datetime) -> str:
    return value.strftime(TIMESTAMP_FORMAT)


def read_readings(path: str | Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with open(path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "sensor_id": str(row["sensor_id"]).strip(),
                    "timestamp": parse_timestamp(str(row["timestamp"])),
                    "value": float(row["value"]),
                    "filled": False,
                }
            )
    return rows


def sort_readings(
    readings: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    return sorted(readings, key=lambda r: (str(r["sensor_id"]), r["timestamp"]))


def interpolate_sensor(
    readings: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    if not readings:
        return []

    ordered = sorted(readings, key=lambda r: r["timestamp"])
    filled: list[dict[str, object]] = [ordered[0]]

    for previous, current in zip(ordered, ordered[1:]):
        prev_ts: datetime = previous["timestamp"]
        curr_ts: datetime = current["timestamp"]
        prev_val: float = previous["value"]
        curr_val: float = current["value"]

        gap = curr_ts - prev_ts
        total_hours = gap.total_seconds() / 3600.0
        if total_hours > 1:
            missing_hours = int(total_hours) - 1
            if total_hours.is_integer():
                step_count = int(total_hours)
            else:
                step_count = missing_hours + 1

            for step in range(1, step_count):
                ratio = step / step_count
                filled.append(
                    {
                        "sensor_id": current["sensor_id"],
                        "timestamp": prev_ts + timedelta(hours=step),
                        "value": prev_val + (curr_val - prev_val) * ratio,
                        "filled": True,
                    }
                )
        filled.append(current)

    return filled


def fill_missing_hourly(
    readings: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in readings:
        grouped.setdefault(str(row["sensor_id"]), []).append(row)

    result: list[dict[str, object]] = []
    for sensor_id in sorted(grouped):
        result.extend(interpolate_sensor(grouped[sensor_id]))
    return result


def write_readings(
    readings: Iterable[dict[str, object]],
    path: str | Path,
    fieldnames: Sequence[str] = ("sensor_id", "timestamp", "value", "filled"),
) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in readings:
            writer.writerow(
                {
                    "sensor_id": row["sensor_id"],
                    "timestamp": format_timestamp(row["timestamp"]),
                    "value": f"{float(row['value']):.6f}",
                    "filled": "true" if row["filled"] else "false",
                }
            )


def process(
    input_path: str | Path, output_path: str | Path
) -> list[dict[str, object]]:
    readings = read_readings(input_path)
    sorted_rows = sort_readings(readings)
    filled_rows = fill_missing_hourly(sorted_rows)
    write_readings(filled_rows, output_path)
    return filled_rows


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Hourly sensor interpolation utility")
    parser.add_argument("input", help="Input CSV with sensor_id,timestamp,value")
    parser.add_argument("output", help="Output CSV path")
    args = parser.parse_args()

    process(args.input, args.output)