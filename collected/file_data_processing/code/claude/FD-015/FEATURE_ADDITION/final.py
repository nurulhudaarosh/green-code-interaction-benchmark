#!/usr/bin/env python3
"""
JSONL filter: validates records, keeps active ones at or above a score
threshold, sorts them by category (asc), score (desc), id (asc), and
reports how many records were skipped.

Expected record shape:
    {"id": <int|str>, "category": <str>, "score": <number>, "active": <bool>}

Usage:
    python filter_jsonl.py input.jsonl --threshold 50 -o output.jsonl
    cat input.jsonl | python filter_jsonl.py - --threshold 50
"""

import argparse
import json
import sys
from collections import Counter
from typing import Any, Iterable, Optional

REQUIRED_FIELDS = ("id", "category", "score", "active")


def validate(record: Any) -> Optional[str]:
    """Return None if the record is valid, otherwise a short reason string."""
    if not isinstance(record, dict):
        return "not_an_object"

    for field in REQUIRED_FIELDS:
        if field not in record:
            return f"missing_{field}"

    rec_id = record["id"]
    if isinstance(rec_id, bool) or not isinstance(rec_id, (int, str)):
        return "invalid_id"
    if isinstance(rec_id, str) and not rec_id.strip():
        return "invalid_id"

    category = record["category"]
    if not isinstance(category, str) or not category.strip():
        return "invalid_category"

    score = record["score"]
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return "invalid_score"
    if score != score or score in (float("inf"), float("-inf")):  # NaN / inf
        return "invalid_score"

    if not isinstance(record["active"], bool):
        return "invalid_active"

    return None


def sort_key(record: dict) -> tuple:
    """
    Sort key: category ascending, score descending, ID ascending.

    Numeric IDs sort before string IDs so mixed types never raise a
    TypeError during comparison.
    """
    rec_id = record["id"]
    id_key = (0, rec_id, "") if isinstance(rec_id, int) else (1, 0, rec_id)
    return (record["category"], -record["score"], id_key)


def filter_records(lines: Iterable[str], threshold: float):
    """Return (sorted_kept_records, skipped_counter)."""
    kept = []
    skipped = Counter()

    for line in lines:
        line = line.strip()
        if not line:
            continue  # blank lines are ignored, not counted

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            skipped["malformed_json"] += 1
            continue

        reason = validate(record)
        if reason:
            skipped[reason] += 1
            continue

        if not record["active"]:
            skipped["inactive"] += 1
            continue

        if record["score"] < threshold:
            skipped["below_threshold"] += 1
            continue

        kept.append(record)

    kept.sort(key=sort_key)
    return kept, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Filter and sort JSONL records.")
    parser.add_argument("input", help="Input JSONL file, or '-' for stdin")
    parser.add_argument(
        "-t", "--threshold", type=float, required=True,
        help="Minimum score (inclusive) for a record to be kept",
    )
    parser.add_argument(
        "-o", "--output", default="-",
        help="Output JSONL file (default: stdout)",
    )
    args = parser.parse_args()

    if args.input == "-":
        kept, skipped = filter_records(sys.stdin, args.threshold)
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            kept, skipped = filter_records(f, args.threshold)

    out = sys.stdout if args.output == "-" else open(args.output, "w", encoding="utf-8")
    try:
        for rec in kept:
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
    finally:
        if out is not sys.stdout:
            out.close()

    # Summary goes to stderr so stdout stays clean JSONL
    print(f"Kept: {len(kept)}", file=sys.stderr)
    print(f"Skipped: {sum(skipped.values())}", file=sys.stderr)
    for reason, count in sorted(skipped.items()):
        print(f"  {reason}: {count}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())