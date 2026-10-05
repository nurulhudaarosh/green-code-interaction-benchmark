import csv
import re
import sys
import unicodedata
from collections import defaultdict


def normalize_text(value):
    value = unicodedata.normalize("NFKC", value or "")
    value = value.strip().casefold()
    return value


def normalize_email(value):
    return normalize_text(value)


def normalize_phone(value):
    return re.sub(r"\D", "", value or "")


def surname_initial(value):
    value = normalize_text(value)
    letters = re.findall(r"[^\W\d_]", value, flags=re.UNICODE)
    return letters[0] if letters else ""


def postal_prefix(value):
    value = normalize_text(value)
    return re.sub(r"\s+", "", value)[:3]


def record_blocks(record):
    blocks = set()

    initial = surname_initial(record.get("surname", ""))
    if initial:
        blocks.add("s:" + initial)

    prefix = postal_prefix(record.get("postal_code", ""))
    if prefix:
        blocks.add("p:" + prefix)

    return blocks


def load_records(path):
    records = []

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for index, row in enumerate(reader):
            row["_row"] = index
            row["_email"] = normalize_email(row.get("email", ""))
            row["_phone"] = normalize_phone(row.get("phone", ""))
            records.append(row)

    return records


def find_matches(records):
    blocks = defaultdict(set)

    for index, record in enumerate(records):
        for block in record_blocks(record):
            blocks[block].add(index)

    email_map = defaultdict(set)
    phone_map = defaultdict(set)

    for index, record in enumerate(records):
        if record["_email"]:
            email_map[record["_email"]].add(index)

        if record["_phone"]:
            phone_map[record["_phone"]].add(index)

    matches = set()

    for index, record in enumerate(records):
        candidates = set()

        for block in record_blocks(record):
            candidates.update(blocks[block])

        for candidate in candidates:
            if candidate == index:
                continue

            other = records[candidate]

            email_match = (
                record["_email"]
                and other["_email"]
                and record["_email"] == other["_email"]
            )

            phone_match = (
                record["_phone"]
                and other["_phone"]
                and record["_phone"] == other["_phone"]
            )

            if email_match or phone_match:
                pair = tuple(sorted((index, candidate)))
                matches.add(pair)

    return sorted(matches)


def write_matches(path, records, matches):
    fieldnames = [
        "record1_row",
        "record2_row",
        "match_type"
    ]

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for first, second in matches:
            a = records[first]
            b = records[second]

            types = []

            if (
                a["_email"]
                and b["_email"]
                and a["_email"] == b["_email"]
            ):
                types.append("email")

            if (
                a["_phone"]
                and b["_phone"]
                and a["_phone"] == b["_phone"]
            ):
                types.append("phone")

            writer.writerow({
                "record1_row": first,
                "record2_row": second,
                "match_type": "+".join(types)
            })


def main():
    if len(sys.argv) != 3:
        print("Usage: python matcher.py input.csv output.csv")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    records = load_records(input_path)
    matches = find_matches(records)
    write_matches(output_path, records, matches)

    print(f"Records processed: {len(records)}")
    print(f"Matches found: {len(matches)}")


if __name__ == "__main__":
    main()