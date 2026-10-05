#!/usr/bin/env python3
"""
JSONL filter: validates records, keeps active ones with score >= threshold
(inclusive), excludes inactive ones, sorts by category (asc), score (desc),
id (asc), and reports how many records were skipped and why.

Expected record shape (one JSON object per line):
    {"id": 1, "category": "books", "score": 87.5, "active": true}

Usage:
    python filter_jsonl.py input.jsonl --threshold 50 -o output.jsonl
    cat input.jsonl | python filter_jsonl.py --threshold 50
"""

import argparse
import json
import math
import sys
from collections import Counter
from typing import Iterable, Optional, Tuple


def is_number(value) -> bool:
    """True for real, finite numbers (bool is excluded since it subclasses int)."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate(record) -> Tuple[bool, Optional[str]]:
    """Return (is_valid, error_reason)."""
    if not isinstance(record, dict):
        return False, "not_an_object"

    for field in ("id", "category", "score", "active"):
        if field not in record:
            return False, f"missing_{field}"

    rec_id = record["id"]
    if isinstance(rec_id, bool) or not isinstance(rec_id, (int, str)):
        return False, "invalid_id"
    if isinstance(rec_id, str) and not rec_id.strip():
        return False, "invalid_id"

    category = record["category"]
    if not isinstance(category, str) or not category.strip():
        return False, "invalid_category"

    if not is_number(record["score"]):
        return False, "invalid_score"

    if not isinstance(record["active"], bool):
        return False, "invalid_active"

    return True, None


def id_sort_key(rec_id):
    """Sort numeric IDs before string IDs so mixed types never raise TypeError."""
    if isinstance(rec_id, int):
        return (0, rec_id, "")
    return (1, 0, rec_id)


def sort_key(record):
    return (record["category"], -record["score"], id_sort_key(record["id"]))


def process(lines: Iterable[str], threshold: float):
    """Parse, validate, and filter lines. Returns (kept_records, skip_counts)."""
    kept = []
    skipped = Counter()

    for line in lines:
        line = line.strip()
        if not line:
            continue  # blank lines are ignored, not counted as skipped

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            skipped["invalid_json"] += 1
            continue

        valid, reason = validate(record)
        if not valid:
            skipped[reason] += 1
            continue

        # Inactive records are always excluded
        if not record["active"]:
            skipped["inactive"] += 1
            continue

        # Strict "<": a score exactly equal to the threshold is retained
        if record["score"] < threshold:
            skipped["below_threshold"] += 1
            continue

        kept.append(record)

    kept.sort(key=sort_key)
    return kept, skipped


def main():
    parser = argparse.ArgumentParser(description="Filter and sort JSONL records.")
    parser.add_argument(
        "input", nargs="?", default="-",
        help="Input JSONL file (default: stdin)",
    )
    parser.add_argument(
        "-o", "--output", default="-",
        help="Output JSONL file (default: stdout)",
    )
    parser.add_argument(
        "-t", "--threshold", type=float, required=True,
        help="Minimum score (inclusive) for a record to be kept",
    )
    args = parser.parse_args()

    if math.isnan(args.threshold):
        parser.error("threshold must be a real number")

    # Read
    if args.input == "-":
        kept, skipped = process(sys.stdin, args.threshold)
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            kept, skipped = process(f, args.threshold)

    # Write
    out = sys.stdout if args.output == "-" else open(args.output, "w", encoding="utf-8")
    try:
        for record in kept:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
    finally:
        if out is not sys.stdout:
            out.close()

    # Summary goes to stderr so it never pollutes JSONL on stdout
    total_skipped = sum(skipped.values())
    print(f"Kept:    {len(kept)}", file=sys.stderr)
    print(f"Skipped: {total_skipped}", file=sys.stderr)
    for reason, count in sorted(skipped.items()):
        print(f"  - {reason}: {count}", file=sys.stderr)


if __name__ == "__main__":
    main()