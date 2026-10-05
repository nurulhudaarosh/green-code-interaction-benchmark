import json
import argparse
from collections import Counter


def validate_record(record):
    """Return (is_valid, reason). A record must be a dict with required fields."""
    if not isinstance(record, dict):
        return False, "not_a_dict"
    required = ("id", "category", "score", "active")
    for field in required:
        if field not in record:
            return False, f"missing_{field}"
    if not isinstance(record["id"], (str, int)):
        return False, "bad_id"
    if not isinstance(record["category"], str):
        return False, "bad_category"
    if not isinstance(record["score"], (int, float)) or isinstance(record["score"], bool):
        return False, "bad_score"
    if not isinstance(record["active"], bool):
        return False, "bad_active"
    return True, None


def filter_jsonl(input_path, output_path, threshold):
    kept = []
    skipped = Counter()

    with open(input_path, "r", encoding="utf-8") as infile:
        for line_num, line in enumerate(infile, 1):
            line = line.strip()
            if not line:
                skipped["blank_line"] += 1
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                skipped["invalid_json"] += 1
                continue

            valid, reason = validate_record(record)
            if not valid:
                skipped[f"invalid:{reason}"] += 1
                continue

            if not record["active"]:
                skipped["inactive"] += 1
                continue

            if record["score"] < threshold:
                skipped["below_threshold"] += 1
                continue

            kept.append(record)

    # Sort by category (asc), score (desc), id (asc)
    kept.sort(key=lambda r: (r["category"], -r["score"], str(r["id"])))

    with open(output_path, "w", encoding="utf-8") as outfile:
        for record in kept:
            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")

    total_skipped = sum(skipped.values())
    print(f"Kept: {len(kept)}")
    print(f"Skipped: {total_skipped}")
    for reason, count in sorted(skipped.items()):
        print(f"  {reason}: {count}")

    return kept, skipped


def main():
    parser = argparse.ArgumentParser(description="Filter JSONL records.")
    parser.add_argument("input", help="Input JSONL file")
    parser.add_argument("output", help="Output JSONL file")
    parser.add_argument(
        "--threshold", "-t", type=float, required=True,
        help="Minimum score for active records to be kept",
    )
    args = parser.parse_args()

    filter_jsonl(args.input, args.output, args.threshold)


if __name__ == "__main__":
    main()