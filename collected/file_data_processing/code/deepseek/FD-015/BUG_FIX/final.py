import json
import sys
from collections import Counter

def filter_jsonl(input_path, output_path, score_threshold):
    kept = []
    skipped_counts = Counter()

    with open(input_path, "r", encoding="utf-8") as infile:
        for line_num, line in enumerate(infile, start=1):
            line = line.strip()
            if not line:
                skipped_counts["blank_line"] += 1
                continue

            # Malformed JSON
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                skipped_counts["invalid_json"] += 1
                continue

            # Must be a JSON object
            if not isinstance(record, dict):
                skipped_counts["not_an_object"] += 1
                continue

            # Incomplete records: missing any required field
            required = ("id", "category", "score", "active")
            if any(field not in record for field in required):
                skipped_counts["missing_fields"] += 1
                continue

            # Validate field types
            if not isinstance(record["id"], (str, int)) or isinstance(record["id"], bool):
                skipped_counts["invalid_id"] += 1
                continue

            if not isinstance(record["category"], str):
                skipped_counts["invalid_category"] += 1
                continue

            if not isinstance(record["score"], (int, float)) or isinstance(record["score"], bool):
                skipped_counts["invalid_score"] += 1
                continue

            if not isinstance(record["active"], bool):
                skipped_counts["invalid_active"] += 1
                continue

            # Keep only active records at/above the threshold
            if not record["active"]:
                skipped_counts["inactive"] += 1
                continue

            if record["score"] < score_threshold:
                skipped_counts["below_threshold"] += 1
                continue

            kept.append(record)

    # Sort by category (asc), then score (desc), then id (asc)
    kept.sort(key=lambda r: (r["category"], -r["score"], str(r["id"])))

    with open(output_path, "w", encoding="utf-8") as outfile:
        for record in kept:
            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")

    return kept, skipped_counts


def main():
    if len(sys.argv) != 4:
        print("Usage: python filter_jsonl.py <input.jsonl> <output.jsonl> <score_threshold>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        score_threshold = float(sys.argv[3])
    except ValueError:
        print("Error: score_threshold must be a number.")
        sys.exit(1)

    kept, skipped = filter_jsonl(input_path, output_path, score_threshold)

    total_skipped = sum(skipped.values())
    print(f"Kept records:    {len(kept)}")
    print(f"Skipped records: {total_skipped}")
    for reason, count in sorted(skipped.items()):
        print(f"  - {reason}: {count}")
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()