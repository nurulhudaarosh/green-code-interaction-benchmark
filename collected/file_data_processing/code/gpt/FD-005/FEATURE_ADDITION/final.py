import csv
import sys
from datetime import datetime


def parse_timestamp(value):
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return value.strip()


def severity_rank(value):
    ranks = {
        "CRITICAL": 4,
        "ERROR": 3,
        "WARNING": 2,
        "WARN": 2,
        "INFO": 1,
        "DEBUG": 0
    }
    return ranks.get(value.strip().upper(), -1)


def main():
    if len(sys.argv) != 3:
        print("Usage: python log_sorter.py input.csv output.csv")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    rows = []

    with open(input_file, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            return

        for sequence, row in enumerate(reader):
            row["_sequence"] = sequence
            rows.append(row)

        fieldnames = reader.fieldnames

    rows.sort(
        key=lambda row: (
            parse_timestamp(row.get("timestamp", "")),
            -severity_rank(row.get("severity", "")),
            row["_sequence"]
        )
    )

    output_fields = fieldnames + ["sequence"]

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=output_fields,
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\n"
        )

        writer.writeheader()

        for row in rows:
            output_row = {field: row.get(field, "") for field in fieldnames}
            output_row["sequence"] = row["_sequence"]
            writer.writerow(output_row)


if __name__ == "__main__":
    main()