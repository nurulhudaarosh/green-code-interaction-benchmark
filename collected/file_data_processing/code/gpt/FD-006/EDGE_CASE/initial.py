import csv
import re
import sys


def normalize_email(email):
    return email.strip().lower()


def normalize_phone(phone):
    return re.sub(r"\D", "", phone)


def completeness(record):
    return sum(bool(value.strip()) for value in record.values())


def main():
    if len(sys.argv) != 3:
        print("Usage: python normalizer.py input.csv output.csv")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        if not fieldnames or "email" not in fieldnames or "phone" not in fieldnames:
            raise ValueError("CSV must contain email and phone columns")

        groups = {}

        for row_number, row in enumerate(reader):
            row["email"] = normalize_email(row["email"])
            row["phone"] = normalize_phone(row["phone"])

            key = row["email"]
            score = completeness(row)

            if key not in groups or score > groups[key][0]:
                groups[key] = (score, row_number, row)

        records = [value[2] for value in groups.values()]
        records.sort(key=lambda row: row["email"])

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    main()