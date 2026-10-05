import csv
import sys
from datetime import datetime, timedelta


def parse_timestamp(value):
    return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))


def interpolate(start_value, end_value, steps):
    return start_value + (end_value - start_value) / steps


def process(input_file, output_file):
    rows = []

    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            sensor = row["sensor"].strip()
            timestamp = parse_timestamp(row["timestamp"])
            value = float(row["value"])

            rows.append({
                "sensor": sensor,
                "timestamp": timestamp,
                "value": value,
                "filled": row.get("filled", "0").strip()
            })

    sensors = {}

    for row in rows:
        sensors.setdefault(row["sensor"], []).append(row)

    output_rows = []

    for sensor in sorted(sensors):
        readings = sorted(
            sensors[sensor],
            key=lambda x: x["timestamp"]
        )

        for i in range(len(readings) - 1):
            current = readings[i]
            next_row = readings[i + 1]

            output_rows.append({
                "sensor": sensor,
                "timestamp": current["timestamp"],
                "value": current["value"],
                "filled": current["filled"]
            })

            gap = next_row["timestamp"] - current["timestamp"]

            if gap.total_seconds() > 3600:
                hours = int(gap.total_seconds() // 3600)

                for step in range(1, hours):
                    timestamp = current["timestamp"] + timedelta(hours=step)
                    value = interpolate(
                        current["value"],
                        next_row["value"],
                        hours
                    )

                    output_rows.append({
                        "sensor": sensor,
                        "timestamp": timestamp,
                        "value": value,
                        "filled": "1"
                    })

        if readings:
            last = readings[-1]

            output_rows.append({
                "sensor": sensor,
                "timestamp": last["timestamp"],
                "value": last["value"],
                "filled": last["filled"]
            })

    output_rows.sort(
        key=lambda x: (x["sensor"], x["timestamp"])
    )

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sensor", "timestamp", "value", "filled"])

        for row in output_rows:
            timestamp = row["timestamp"].isoformat()
            writer.writerow([
                row["sensor"],
                timestamp,
                f"{row['value']:.10f}".rstrip("0").rstrip("."),
                row["filled"]
            ])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python utility.py input.csv output.csv")
        sys.exit(1)

    process(sys.argv[1], sys.argv[2])