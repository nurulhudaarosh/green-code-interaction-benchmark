import csv
import re
import sys
from collections import defaultdict


def normalize_email(value):
    return value.strip().casefold()


def normalize_phone(value):
    return re.sub(r"\D", "", value)


def blocking_key(record):
    surname = record.get("surname", "").strip().casefold()
    postal = record.get("postal_code", "").strip().casefold()

    surname_initial = surname[:1]
    postal_prefix = postal[:3]

    return surname_initial, postal_prefix


def right_id_key(record):
    value = record.get("id", "")
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def match_customers(left_file, right_file, output_file):
    with open(left_file, "r", encoding="utf-8", newline="") as f:
        left_records = list(csv.DictReader(f))

    with open(right_file, "r", encoding="utf-8", newline="") as f:
        right_records = list(csv.DictReader(f))

    blocks = defaultdict(list)

    for right in right_records:
        blocks[blocking_key(right)].append(right)

    matches = []

    for left in left_records:
        key = blocking_key(left)
        candidates = blocks.get(key, [])

        left_email = normalize_email(left.get("email", ""))
        left_phone = normalize_phone(left.get("phone", ""))

        candidate_matches = []

        for right in candidates:
            right_email = normalize_email(right.get("email", ""))
            right_phone = normalize_phone(right.get("phone", ""))

            email_match = (
                left_email != "" and
                right_email != "" and
                left_email == right_email
            )

            phone_match = (
                left_phone != "" and
                right_phone != "" and
                left_phone == right_phone
            )

            if email_match or phone_match:
                if email_match:
                    match_type = "email"
                    priority = 0
                else:
                    match_type = "phone"
                    priority = 1

                candidate_matches.append(
                    (priority, right_id_key(right), right, match_type)
                )

        if candidate_matches:
            candidate_matches.sort(key=lambda x: (x[0], x[1]))
            _, _, right, match_type = candidate_matches[0]

            matches.append({
                "left_id": left.get("id", ""),
                "right_id": right.get("id", ""),
                "match_type": match_type
            })

    matches.sort(
        key=lambda x: (
            x["left_id"],
            right_id_key(x)
        )
    )

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["left_id", "right_id", "match_type"]
        )
        writer.writeheader()
        writer.writerows(matches)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python matcher.py left.csv right.csv output.csv")
        sys.exit(1)

    match_customers(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3]
    )