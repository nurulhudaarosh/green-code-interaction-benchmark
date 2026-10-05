import sys
import json


def main():
    if len(sys.argv) != 3:
        print("Usage: python filter.py input.jsonl threshold")
        return

    input_file = sys.argv[1]

    try:
        threshold = float(sys.argv[2])
    except ValueError:
        print("Invalid threshold")
        return

    valid_records = []
    skipped = 0

    try:
        with open(input_file, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    skipped += 1
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    skipped += 1
                    continue

                if not isinstance(record, dict):
                    skipped += 1
                    continue

                if not all(key in record for key in ("id", "category", "score", "status")):
                    skipped += 1
                    continue

                if not isinstance(record["category"], str):
                    skipped += 1
                    continue

                if not isinstance(record["status"], str):
                    skipped += 1
                    continue

                try:
                    score = float(record["score"])
                except (ValueError, TypeError):
                    skipped += 1
                    continue

                if record["status"].casefold() != "active":
                    skipped += 1
                    continue

                if score < threshold:
                    skipped += 1
                    continue

                record["score"] = score
                valid_records.append(record)

    except OSError as e:
        print(f"Error reading file: {e}")
        return

    valid_records.sort(
        key=lambda r: (
            r["category"].casefold(),
            -r["score"],
            str(r["id"])
        )
    )

    for record in valid_records:
        print(json.dumps(record, ensure_ascii=False, separators=(",", ":")))

    print(json.dumps({"skipped": skipped}, separators=(",", ":")))


if __name__ == "__main__":
    main()