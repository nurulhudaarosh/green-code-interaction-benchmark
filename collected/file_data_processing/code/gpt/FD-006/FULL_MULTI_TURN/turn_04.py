import csv
import re
import sys


def normalize_email(email):
    return email.strip().lower()


def normalize_phone(phone):
    return re.sub(r"\D", "", phone)


def completeness(record):
    return sum(1 for value in record.values() if value.strip())


def normalize_customers(input_file, output_file):
    groups = {}

    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for row_number, row in enumerate(reader):
            row["email"] = normalize_email(row.get("email", ""))
            row["phone"] = normalize_phone(row.get("phone", ""))

            score = completeness(row)

            if row["email"] not in groups:
                groups[row["email"]] = (score, row_number, row)
            else:
                old_score, old_row_number, _ = groups[row["email"]]

                if score > old_score or (
                    score == old_score and row_number < old_row_number
                ):
                    groups[row["email"]] = (score, row_number, row)

    records = [
        item[2]
        for item in sorted(
            groups.values(),
            key=lambda item: item[2]["email"]
        )
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python normalizer.py input.csv output.csv")
        sys.exit(1)

    normalize_customers(sys.argv[1], sys.argv[2])