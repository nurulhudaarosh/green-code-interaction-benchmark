import csv
import sys
from datetime import datetime
from collections import defaultdict


def main():
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    totals = defaultdict(int)
    event_types = set()

    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required = {"date", "region", "event_type"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("Input must contain date, region, and event_type columns.")

        for row in reader:
            date_text = row["date"].strip()
            region = row["region"].strip()
            event_type = row["event_type"].strip()

            if not date_text or not region or not event_type:
                continue

            try:
                date = datetime.strptime(date_text, "%Y-%m-%d").date()
            except ValueError:
                continue

            totals[(date, region, event_type)] += 1
            event_types.add(event_type)

    event_types = sorted(event_types)

    rows = []

    keys = sorted(
        {(date, region) for date, region, event_type in totals},
        key=lambda x: (x[0], x[1])
    )

    for date, region in keys:
        row = {
            "date": date.isoformat(),
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