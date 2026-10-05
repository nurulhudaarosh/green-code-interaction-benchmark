import csv
import sys
import re
from collections import defaultdict
from datetime import datetime


def normalize_text(value):
    value = str(value).strip().casefold()
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_date(value):
    value = str(value).strip()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def detect_duplicates(input_file):
    groups = defaultdict(list)

    with open(input_file, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            record_id = str(row.get("id", "")).strip()
            title = row.get("title")
            description = row.get("description")
            date = row.get("date")

            if not record_id or title is None or description is None or date is None:
                continue

            normalized_date = normalize_date(date)
            if normalized_date is None:
                continue

            key = (
                normalize_text(title),
                normalize_text(description),
                normalized_date
            )

            groups[key].append(record_id)

    duplicate_groups = []

    for ids in groups.values():
        unique_ids = sorted(set(ids))
        if len(unique_ids) >= 2:
            duplicate_groups.append(unique_ids)

    duplicate_groups.sort(key=lambda group: group[0])

    return duplicate_groups


def main():
    if len(sys.argv) != 2:
        return

    input_file = sys.argv[1]
    duplicate_groups = detect_duplicates(input_file)

    for group in duplicate_groups:
        print(",".join(group))


if __name__ == "__main__":
    main()