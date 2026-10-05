import csv
import sys
from collections import defaultdict
from datetime import datetime


def main():
    if len(sys.argv) != 3:
        print("Usage: python event_pivot.py input.csv output.csv")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    totals = defaultdict(int)
    event_types = set()

    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required = {"date", "region", "event_type"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            print("Error: CSV must contain date, region, and event_type columns.")
            return

        for row in reader:
            date = row.get("date", "").strip()
            region = row.get("region", "").strip()
            event_type = row.get("event_type", "").strip()

            if not date or not region or not event_type:
                continue

            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                continue

            totals[(date, region, event_type)] += 1
            event_types.add(event_type)

    event_types = sorted(event_types)

    rows = sorted(
        {(date, region) for date, region, _ in totals},
        key=lambda x: (x[0], x[1])
    )

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["date", "region"] + event_types
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for date, region in rows:
            output = {
                "date": date,
                "region": region
            }

            for event_type in event_types:
                output[event_type] = totals.get(
                    (date, region, event_type), 0
                )

            writer.writerow(output)


if __name__ == "__main__":
    main()