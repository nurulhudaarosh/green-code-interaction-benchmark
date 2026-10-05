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
    return value[:1] if value else ""


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


def right_id_key(record):
    value = record.get("id", "")
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


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
        best_priority = None

        for right in candidates:
            right_email = normalize_email(right.get("email", ""))
            right_phone = normalize_phone(right.get("phone", ""))

            if left_email and right_email and left_email == right_email:
                priority = 0
                match_type = "email"
            elif left_phone and right_phone and left_phone == right_phone:
                priority = 1
                match_type = "phone"
            else:
                continue

            candidate_priority = (priority, right_id_key(right))

            if best_match is None or candidate_priority < best_priority:
                best_match = right
                best_priority = candidate_priority
                best_type = match_type

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

    left_records = read_csv(sys.argv[1])
    right_records = read_csv(sys.argv[2])

    matches = match_records(left_records, right_records)
    write_csv(sys.argv[3], matches)


if __name__ == "__main__":
    main()