import csv
import sys
import re
from collections import defaultdict


def normalize(text):
    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text.casefold()


def main():
    groups = defaultdict(list)

    reader = csv.DictReader(sys.stdin)

    for row in reader:
        record_id = row.get("id", "").strip()
        date = row.get("date", "").strip()
        title = normalize(row.get("title", ""))
        description = normalize(row.get("description", ""))

        key = (date, title, description)
        groups[key].append(record_id)

    duplicate_groups = []

    for ids in groups.values():
        if len(ids) > 1:
            duplicate_groups.append(sorted(ids))

    duplicate_groups.sort(key=lambda ids: ids)

    writer = csv.writer(sys.stdout)
    writer.writerow(["duplicate_ids"])

    for ids in duplicate_groups:
        writer.writerow([" ".join(ids)])


if __name__ == "__main__":
    main()