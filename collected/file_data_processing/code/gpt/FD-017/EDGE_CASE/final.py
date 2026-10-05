import csv
import sys
from collections import defaultdict
from datetime import datetime


def event_pivot(input_file, output_file):
    totals = defaultdict(int)
    event_types = set()

    with open(input_file, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        required = {"date", "region", "event_type", "count"}

        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("Missing required columns")

        for row in reader:
            try:
                date = datetime.strptime(
                    row["date"].strip(), "%Y-%m-%d"
                ).date()

                region = row["region"].strip()
                event_type = row["event_type"].strip()
                count = int(row["count"])

                if not region or not event_type or count < 0:
                    continue

                totals[(date, region, event_type)] += count
                event_types.add(event_type)

            except (ValueError, TypeError, AttributeError):
                continue

    # Sort event types alphabetically for deterministic column order
    event_types = sorted(event_types)

    grouped = defaultdict(dict)

    for (date, region, event_type), count in totals.items():
        grouped[(date, region)][event_type] = count

    output_rows = []

    for (date, region), values in grouped.items():
        row = {
            "date": date.isoformat(),
            "region": region
        }

        for event_type in event_types:
            row[event_type] = values.get(event_type, 0)

        output_rows.append(row)

    output_rows.sort(key=lambda row: (row["date"], row["region"]))

    fieldnames = ["date", "region"] + event_types

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python event_pivot.py input.csv output.csv")
        sys.exit(1)

    event_pivot(sys.argv[1], sys.argv[2])