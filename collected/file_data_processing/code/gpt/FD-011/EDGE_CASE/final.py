import csv
import sys
from datetime import datetime, timedelta


def parse_timestamp(value):
    return datetime.fromisoformat(value.strip())


def interpolate(v1, v2, ratio):
    return v1 + (v2 - v1) * ratio


def process(input_file, output_file):
    readings = {}

    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            sensor = row["sensor"].strip()
            timestamp = parse_timestamp(row["timestamp"])
            value = float(row["value"])

            readings.setdefault(sensor, []).append(
                {
                    "timestamp": timestamp,
                    "value": value
                }
            )

    output_rows = []

    for sensor in sorted(readings):
        rows = sorted(
            readings[sensor],
            key=lambda r: r["timestamp"]
        )

        by_time = {}

        for row in rows:
            by_time[row["timestamp"]] = row

        timestamps = sorted(by_time)

        for i, current_time in enumerate(timestamps):
            current_value = by_time[current_time]["value"]

            output_rows.append(
                {
                    "sensor": sensor,
                    "timestamp": current_time.isoformat(),
                    "value": format(current_value, ".15g"),
                    "filled": "false"
                }
            )

            if i == len(timestamps) - 1:
                continue

            next_time = timestamps[i + 1]
            next_value = by_time[next_time]["value"]

            gap_seconds = (next_time - current_time).total_seconds()

            if gap_seconds <= 3600 or gap_seconds % 3600 != 0:
                continue

            missing_hours = int(gap_seconds // 3600) - 1
            total_hours = missing_hours + 1

            for hour in range(1, missing_hours + 1):
                filled_time = current_time + timedelta(hours=hour)
                ratio = hour / total_hours
                filled_value = interpolate(
                    current_value,
                    next_value,
                    ratio
                )

                output_rows.append(
                    {
                        "sensor": sensor,
                        "timestamp": filled_time.isoformat(),
                        "value": format(filled_value, ".15g"),
                        "filled": "true"
                    }
                )

    output_rows.sort(
        key=lambda row: (
            row["sensor"],
            parse_timestamp(row["timestamp"])
        )
    )

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["sensor", "timestamp", "value", "filled"]
        )
        writer.writeheader()
        writer.writerows(output_rows)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(1)

    process(sys.argv[1], sys.argv[2])