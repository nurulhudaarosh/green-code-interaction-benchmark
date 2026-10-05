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
                    "value": value,
                    "filled": "false"
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

        if len(timestamps) == 1:
            output_rows.append(
                {
                    "sensor": sensor,
                    "timestamp": timestamps[0].isoformat(),
                    "value": format(by_time[timestamps[0]]["value"], ".15g"),
                    "filled": "false"
                }
            )
            continue

        for i in range(len(timestamps) - 1):
            start_time = timestamps[i]
            end_time = timestamps[i + 1]

            start_value = by_time[start_time]["value"]
            end_value = by_time[end_time]["value"]

            output_rows.append(
                {
                    "sensor": sensor,
                    "timestamp": start_time.isoformat(),
                    "value": format(start_value, ".15g"),
                    "filled": "false"
                }
            )

            gap = end_time - start_time

            if gap.total_seconds() > 3600 and gap.total_seconds() % 3600 == 0:
                total_hours = int(gap.total_seconds() // 3600)

                for hour in range(1, total_hours):
                    new_time = start_time + timedelta(hours=hour)
                    ratio = hour / total_hours
                    new_value = interpolate(
                        start_value,
                        end_value,
                        ratio
                    )

                    output_rows.append(
                        {
                            "sensor": sensor,
                            "timestamp": new_time.isoformat(),
                            "value": format(new_value, ".15g"),
                            "filled": "true"
                        }
                    )

        last_time = timestamps[-1]

        output_rows.append(
            {
                "sensor": sensor,
                "timestamp": last_time.isoformat(),
                "value": format(by_time[last_time]["value"], ".15g"),
                "filled": "false"
            }
        )

    output_rows.sort(
        key=lambda r: (
            r["sensor"],
            parse_timestamp(r["timestamp"])
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