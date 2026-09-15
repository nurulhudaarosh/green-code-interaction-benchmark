import csv
import sys


def severity_rank(severity):
    ranks = {
        "CRITICAL": 4,
        "ERROR": 3,
        "WARNING": 2,
        "INFO": 1,
        "DEBUG": 0
    }
    return ranks.get(severity.upper(), -1)


def main():
    if len(sys.argv) != 3:
        print("Usage: python log_sorter.py input.csv output.csv")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    rows = []

    with open(input_file, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for sequence, row in enumerate(reader):
            row["_sequence"] = sequence
            rows.append(row)

    rows.sort(
        key=lambda row: (
            row.get("timestamp", ""),
            -severity_rank(row.get("severity", "")),
            row["_sequence"]
        )
    )

    fieldnames = [field for field in rows[0].keys() if field != "_sequence"] if rows else []

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()

        for row in rows:
            output_row = {field: row.get(field, "") for field in fieldnames}
            writer.writerow(output_row)


if __name__ == "__main__":
    main()