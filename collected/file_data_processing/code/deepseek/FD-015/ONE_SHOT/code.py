import json
import sys
import argparse
from collections import Counter


def parse_args():
    parser = argparse.ArgumentParser(description="Filter, validate, and sort JSONL records.")
    parser.add_argument("input", help="Path to input JSONL file")
    parser.add_argument("output", help="Path to output JSONL file")
    parser.add_argument("--min-score", type=float, default=0.0,
                        help="Minimum score threshold (inclusive). Default: 0.0")
    parser.add_argument("--active-field", default="active",
                        help="Field name for active flag. Default: 'active'")
    parser.add_argument("--score-field", default="score",
                        help="Field name for score. Default: 'score'")
    parser.add_argument("--category-field", default="category",
                        help="Field name for category. Default: 'category'")
    parser.add_argument("--id-field", default="id",
                        help="Field name for ID. Default: 'id'")
    return parser.parse_args()


def is_valid(record, active_field, score_field, category_field, id_field):
    if not isinstance(record, dict):
        return False, "not a JSON object"
    for field in (active_field, score_field, category_field, id_field):
        if field not in record:
            return False, f"missing field '{field}'"
    if not isinstance(record[active_field], bool):
        return False, f"'{active_field}' is not a boolean"
    if not isinstance(record[score_field], (int, float)) or isinstance(record[score_field], bool):
        return False, f"'{score_field}' is not a number"
    if not isinstance(record[id_field], (str, int)):
        return False, f"'{id_field}' is not a string or int"
    return True, None


def main():
    args = parse_args()
    skip_reasons = Counter()
    kept = []

    with open(args.input, "r", encoding="utf-8") as fin:
        for lineno, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                skip_reasons["blank line"] += 1
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                skip_reasons["invalid JSON"] += 1
                continue

            valid, reason = is_valid(
                record, args.active_field, args.score_field,
                args.category_field, args.id_field
            )
            if not valid:
                skip_reasons[f"invalid record: {reason}"] += 1
                continue

            if not record[args.active_field]:
                skip_reasons["inactive"] += 1
                continue

            if record[args.score_field] < args.min_score:
                skip_reasons["below score threshold"] += 1
                continue

            kept.append(record)

    kept.sort(key=lambda r: (
        str(r[args.category_field]),
        -r[args.score_field],
        str(r[args.id_field]),
    ))

    with open(args.output, "w", encoding="utf-8") as fout:
        for record in kept:
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")

    total_skipped = sum(skip_reasons.values())
    print(f"Kept: {len(kept)}")
    print(f"Skipped: {total_skipped}")
    for reason, count in skip_reasons.most_common():
        print(f"  - {reason}: {count}")


if __name__ == "__main__":
    main()