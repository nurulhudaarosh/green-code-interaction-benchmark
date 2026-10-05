import csv
import sys
import re
from collections import defaultdict


def normalize(text):
    text = text.strip().casefold()
    text = re.sub(r"\s+", " ", text)
    return text


def find_duplicates(input_file):
    groups = defaultdict(list)

    with open(input_file, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            record_id = row["id"]
            title = normalize(row["title"])
            description = normalize(row["description"])
            date = row["date"].strip()

            key = (title, description, date)
            groups[key].append(record_id)

    duplicate_groups = []

    for ids in groups.values():
        if len(ids) > 1:
            duplicate_groups.append(sorted(ids))

    duplicate_groups.sort()

    return duplicate_groups


def main():
    if len(sys.argv) != 2:
        print("Usage: python duplicate_detector.py input.csv")
        return

    for ids in find_duplicates(sys.argv[1]):
        print(",".join(ids))


if __name__ == "__main__":
    main()