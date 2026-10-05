import csv
import re
import sys


def normalize_text(value):
    return " ".join(value.strip().casefold().split())


def normalize_email(value):
    return normalize_text(value)


def normalize_phone(value):
    return re.sub(r"\D", "", value)


def surname_initial(value):
    value = normalize_text(value)
    return value[0] if value else ""


def postal_prefix(value):
    value = normalize_text(value)
    return value[:3]


def blocking_key(record):
    return (
        surname_initial(record.get("surname", "")),
        postal_prefix(record.get("postal_code", ""))
    )


def read_csv(filename):
    with open(filename, "r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def match_records(left_records, right_records):
    right_blocks = {}

    for right in right_records:
        key = blocking_key(right)
        right_blocks.setdefault(key, []).append(right)

    matches = []

    for left in left_records:
        key = blocking_key(left)
        candidates = right_blocks.get(key, [])

        left_email = normalize_email(left.get("email", ""))
        left_phone = normalize_phone(left.get("phone", ""))

        best_match = None
        best_type = None
        best_id = None

        for right in candidates:
            right_email = normalize_email(right.get("email", ""))
            right_phone = normalize_phone(right.get("phone", ""))

            match_type = None

            if left_email and right_email and left_email == right_email:
                match_type = "email"
            elif left_phone and right_phone and left_phone == right_phone:
                match_type = "phone"

            if match_type is None:
                continue

            try:
                right_id = int(right.get("id", ""))
            except ValueError:
                right_id = right.get("id", "")

            if best_match is None:
                best_match = right
                best_type = match_type
                best_id = right_id
            elif match_type == "email" and best_type == "phone":
                best_match = right
                best_type = match_type
                best_id = right_id
            elif match_type == best_type and right_id < best_id:
                best_match = right
                best_id = right_id

        if best_match is not None:
            matches.append({
                "left_id": left.get("id", ""),
                "right_id": best_match.get("id", ""),
                "match_type": best_type
            })
        else:
            matches.append({
                "left_id": left.get("id", ""),
                "right_id": "",
                "match_type": ""
            })

    return matches


def write_csv(filename, matches):
    fieldnames = ["left_id", "right_id", "match_type"]

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matches)


def main():
    if len(sys.argv) != 4:
        print("Usage: python matcher.py left.csv right.csv output.csv")
        return

    left_file = sys.argv[1]
    right_file = sys.argv[2]
    output_file = sys.argv[3]

    left_records = read_csv(left_file)
    right_records = read_csv(right_file)

    matches = match_records(left_records, right_records)
    write_csv(output_file, matches)


if __name__ == "__main__":
    main()