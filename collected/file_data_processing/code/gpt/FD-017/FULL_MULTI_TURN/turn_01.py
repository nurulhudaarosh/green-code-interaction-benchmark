import csv
import sys
from datetime import datetime
from collections import defaultdict


def main():
    if len(sys.argv) != 3:
        print("Usage: python event_pivot.py input.csv output.csv")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    totals = defaultdict(int)
    event_types = set()

    try:
        with open(input_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            required = {"date", "region", "event_type", "count"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                return

            for row in reader:
                date_text = row.get("date", "").strip()
                region = row.get("region", "").strip()
                event_type = row.get("event_type", "").strip()
                count_text = row.get("count", "").strip()

                if not date_text or not region or not event_type or not count_text:
                    continue

                try:
                    date_value = datetime.strptime(
                        date_text, "%Y-%m-%d"
                    ).date()
                    count = int(count_text)
                except (ValueError, TypeError):
                    continue

                if count < 0:
                    continue

                key = (date_value, region, event_type)
                totals[key] += count
                event_types.add(event_type)

    except (OSError, UnicodeError):
        return

    event_columns = sorted(event_types)

    rows = set()
    for date_value, region, event_type in totals:
        rows.add((date_value, region))

    sorted_rows = sorted(rows, key=lambda x: (x[0], x[1]))

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["date", "region"] + event_columns
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for date_value, region in sorted_rows:
            output_row = {
                "date": date_value.isoformat(),
                "region": region
            }

            for event_type in event_columns:
                output_row[event_type] = totals.get(
                    (date_value, region, event_type), 0
                )

            writer.writerow(output_row)


if __name__ == "__main__":
    main()