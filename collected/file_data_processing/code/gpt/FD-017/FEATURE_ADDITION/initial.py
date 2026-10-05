import csv
import sys
from collections import defaultdict
from datetime import datetime


def main():
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    totals = defaultdict(int)
    event_types = set()

    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required = {"date", "region", "event_type", "count"}
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError("Missing required columns")

        for row in reader:
            date = row["date"].strip()
            region = row["region"].strip()
            event_type = row["event_type"].strip()

            try:
                datetime.strptime(date, "%Y-%m-%d")
                count = int(row["count"])
            except (ValueError, TypeError):
                continue

            if not date or not region or not event_type or count < 0:
                continue

            totals[(date, region, event_type)] += count
            event_types.add(event_type)

    event_types = sorted(event_types)

    rows = []

    groups = sorted({(date, region) for date, region, _ in totals})

    for date, region in groups:
        row = {
            "date": date,
            "region": region
        }

        for event_type in event_types:
            row[event_type] = totals.get((date, region, event_type), 0)

        rows.append(row)

    fieldnames = ["date", "region"] + event_types

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()