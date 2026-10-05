import csv
import re
import sys
import unicodedata
from collections import defaultdict


def normalize_text(value):
    value = unicodedata.normalize("NFKC", value or "")
    return " ".join(value.strip().casefold().split())


def normalize_email(value):
    return normalize_text(value)


def normalize_phone(value):
    return re.sub(r"\D", "", value or "")


def get_surname(name):
    parts = normalize_text(name).split()
    return parts[-1] if parts else ""


def get_blocking_key(record):
    surname = get_surname(record.get("name", ""))
    postal = normalize_text(record.get("postal_code", ""))

    surname_initial = surname[0] if surname else ""
    postal_prefix = re.match(r"\d+", postal)

    if not surname_initial or not postal_prefix:
        return None

    return surname_initial + "|" + postal_prefix.group(0)


def read_records(filename):
    records = []

    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row_number, row in enumerate(reader):
            row["_row_number"] = row_number
            row["_email"] = normalize_email(row.get("email", ""))
            row["_phone"] = normalize_phone(row.get("phone", ""))
            row["_block"] = get_blocking_key(row)
            records.append(row)

    return records


def build_right_indexes(right_records):
    block_index = defaultdict(list)
    email_index = defaultdict(list)
    phone_index = defaultdict(list)

    for record in right_records:
        if record["_block"]:
            block_index[record["_block"]].append(record)

        if record["_email"]:
            email_index[record["_email"]].append(record)

        if record["_phone"]:
            phone_index[record["_phone"]].append(record)

    return block_index, email_index, phone_index


def match_records(left_records, right_records):
    block_index, email_index, phone_index = build_right_indexes(right_records)
    matches = []

    for left in left_records:
        candidates = {}

        # Blocking is performed first.
        if left["_block"]:
            for right in block_index.get(left["_block"], []):
                candidates[right["_row_number"]] = right

        # Exact email/phone indexes can add candidates without
        # scanning every right-side record.
        if left["_email"]:
            for right in email_index.get(left["_email"], []):
                candidates[right["_row_number"]] = right

        if left["_phone"]:
            for right in phone_index.get(left["_phone"], []):
                candidates[right["_row_number"]] = right

        for right in candidates.values():
            email_match = (
                bool(left["_email"])
                and bool(right["_email"])
                and left["_email"] == right["_email"]
            )

            phone_match = (
                bool(left["_phone"])
                and bool(right["_phone"])
                and left["_phone"] == right["_phone"]
            )

            block_match = (
                bool(left["_block"])
                and left["_block"] == right["_block"]
            )

            if email_match or phone_match:
                match_type = "exact_email_or_phone"
            elif block_match:
                match_type = "same_block"
            else:
                continue

            matches.append({
                "left_record": left["_row_number"],
                "right_record": right["_row_number"],
                "match_type": match_type,
                "email_match": str(email_match).lower(),
                "phone_match": str(phone_match).lower(),
                "blocking_key": left["_block"] or ""
            })

    return sorted(
        matches,
        key=lambda x: (
            x["left_record"],
            x["right_record"],
            x["match_type"]
        )
    )


def write_matches(filename, matches):
    fieldnames = [
        "left_record",
        "right_record",
        "match_type",
        "email_match",
        "phone_match",
        "blocking_key"
    ]

    with open(filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matches)


def main():
    if len(sys.argv) != 4:
        print("Usage: python matcher.py left.csv right.csv output.csv")
        sys.exit(1)

    left_file = sys.argv[1]
    right_file = sys.argv[2]
    output_file = sys.argv[3]

    left_records = read_records(left_file)
    right_records = read_records(right_file)

    matches = match_records(left_records, right_records)
    write_matches(output_file, matches)

    print(f"Left records: {len(left_records)}")
    print(f"Right records: {len(right_records)}")
    print(f"Matches: {len(matches)}")
    print(f"Results written to {output_file}")


if __name__ == "__main__":
    main()