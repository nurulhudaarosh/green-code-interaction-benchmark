import csv
import sys
from datetime import datetime, timedelta


def parse_timestamp(value):
    return datetime.fromisoformat(value.strip())


def interpolate(start_value, end_value, ratio):
    return start_value + (end_value - start_value) * ratio


def process_readings(input_file, output_file):
    readings = {}

    with open(input_file, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            sensor = row["sensor"]
            timestamp = parse_timestamp(row["timestamp"])
            value = float(row["value"])

            readings.setdefault(sensor, []).append(
                (timestamp, value, False)
            )

    result = []

    for sensor in sorted(readings):
        data = sorted(readings[sensor], key=lambda x: x[0])

        if not data:
            continue

        filled = []

        for i in range(len(data) - 1):
            current_time, current_value, _ = data[i]
            next_time, next_value, _ = data[i + 1]

            filled.append((current_time, current_value, False))

            difference = next_time - current_time
            hours = int(difference.total_seconds() // 3600)

            if hours > 1 and difference == timedelta(hours=hours):
                for step in range(1, hours):
                    new_time = current_time + timedelta(hours=step)
                    ratio = step / hours
                    new_value = interpolate(
                        current_value,
                        next_value,
                        ratio
                    )

                    filled.append((new_time, new_value, True))

        filled.append(data[-1])

        for timestamp, value, inserted in filled:
            result.append({
                "sensor": sensor,
                "timestamp": timestamp.isoformat(),
                "value": value,
                "inserted": inserted
            })

    result.sort(
        key=lambda row: (
            row["sensor"],
            row["timestamp"]
        )
    )

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["sensor", "timestamp", "value", "inserted"]
        )

        writer.writeheader()

        for row in result:
            writer.writerow({
                "sensor": row["sensor"],
                "timestamp": row["timestamp"],
                "value": f"{row['value']:.6f}",
                "inserted": str(row["inserted"]).lower()
            })


def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py input.csv output.csv")
        sys.exit(1)

    process_readings(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()