#!/usr/bin/env python3
"""
JSONL filter: validates records, keeps active records with score >= threshold,
sorts by category (asc), score (desc), id (asc), and counts every skipped record.

Expected record schema (one JSON object per line):
    {"id": <str|int>, "category": <str>, "score": <number>, "active": <bool>}

Skip categories:
    incomplete  - a required field is missing, null, or an empty string
    malformed   - invalid JSON, not a JSON object, or a field of the wrong type/value
    inactive    - valid record with active == false
    below_threshold - valid, active record with score < threshold
Blank lines are ignored but reported separately.

Usage:
    python jsonl_filter.py input.jsonl --threshold 50 -o output.jsonl
    cat input.jsonl | python jsonl_filter.py - -t 50
"""

from __future__ import annotations

import argparse
import contextlib
import json
import math
import sys
from collections import Counter
from typing import Any, Iterable, Iterator, TextIO

REQUIRED_FIELDS = ("id", "category", "score", "active")


class Malformed(Exception):
    """Record is present but structurally wrong (bad JSON, wrong type, bad value)."""


class Incomplete(Exception):
    """Record is missing a required field, or the field is null/empty."""


def validate_record(record: Any) -> dict:
    """Return the record if valid; raise Incomplete or Malformed otherwise."""
    if not isinstance(record, dict):
        raise Malformed("not_a_json_object")

    # Completeness first: missing, null, or empty-string fields.
    for field in REQUIRED_FIELDS:
        if field not in record:
            raise Incomplete(f"missing_{field}")
        value = record[field]
        if value is None or (isinstance(value, str) and not value.strip()):
            raise Incomplete(f"empty_{field}")

    # Then types and values.
    rid = record["id"]
    if isinstance(rid, bool) or not isinstance(rid, (str, int)):
        raise Malformed("bad_id_type")

    if not isinstance(record["category"], str):
        raise Malformed("bad_category_type")

    score = record["score"]
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise Malformed("bad_score_type")
    if isinstance(score, float) and not math.isfinite(score):
        raise Malformed("non_finite_score")

    if not isinstance(record["active"], bool):
        raise Malformed("bad_active_type")

    return record


def parse_lines(lines: Iterable[str], stats: Counter) -> Iterator[dict]:
    """Yield valid records; count and report everything else."""
    for line_no, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            stats["blank_lines"] += 1
            continue

        try:
            raw = json.loads(line)
        except (json.JSONDecodeError, RecursionError):
            stats["malformed"] += 1
            stats["reason:invalid_json"] += 1
            print(f"line {line_no}: skipped (malformed: invalid_json)", file=sys.stderr)
            continue

        try:
            yield validate_record(raw)
        except Incomplete as exc:
            stats["incomplete"] += 1
            stats[f"reason:{exc}"] += 1
            print(f"line {line_no}: skipped (incomplete: {exc})", file=sys.stderr)
        except Malformed as exc:
            stats["malformed"] += 1
            stats[f"reason:{exc}"] += 1
            print(f"line {line_no}: skipped (malformed: {exc})", file=sys.stderr)


def sort_key(record: dict) -> tuple:
    """Category asc, score desc, id asc. Int and str IDs compare without type errors."""
    rid = record["id"]
    id_key = (0, rid, "") if isinstance(rid, int) else (1, 0, rid)
    return (record["category"], -record["score"], id_key)


def filter_records(lines: Iterable[str], threshold: float) -> tuple[list[dict], Counter]:
    """Return (sorted kept records, stats)."""
    stats: Counter = Counter()
    kept: list[dict] = []

    for record in parse_lines(lines, stats):
        if not record["active"]:
            stats["inactive"] += 1
        elif record["score"] < threshold:
            stats["below_threshold"] += 1
        else:
            kept.append(record)

    kept.sort(key=sort_key)
    stats["kept"] = len(kept)
    return kept, stats


def write_records(records: Iterable[dict], out: TextIO) -> None:
    for rec in records:
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")


def print_summary(stats: Counter) -> None:
    skipped = (stats["malformed"] + stats["incomplete"]
               + stats["inactive"] + stats["below_threshold"])
    p = lambda text: print(text, file=sys.stderr)

    p("--- Summary ---")
    p(f"Kept:              {stats['kept']}")
    p(f"Skipped (total):   {skipped}")
    p(f"  malformed:       {stats['malformed']}")
    p(f"  incomplete:      {stats['incomplete']}")
    p(f"  inactive:        {stats['inactive']}")
    p(f"  below threshold: {stats['below_threshold']}")
    p(f"Blank lines (ignored): {stats['blank_lines']}")

    reasons = sorted(k for k in stats if k.startswith("reason:"))
    if reasons:
        p("Skip reasons:")
        for key in reasons:
            p(f"  {key[7:]:<22}{stats[key]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Filter and sort JSONL records.")
    parser.add_argument("input", help="Input JSONL file, or '-' for stdin")
    parser.add_argument("-t", "--threshold", type=float, required=True,
                        help="Minimum score (inclusive) for a record to be kept")
    parser.add_argument("-o", "--output", default="-",
                        help="Output JSONL file, or '-' for stdout (default)")
    args = parser.parse_args()

    try:
        source = (contextlib.nullcontext(sys.stdin) if args.input == "-"
                  else open(args.input, "r", encoding="utf-8", errors="replace"))
        with source as in_f:
            kept, stats = filter_records(in_f, args.threshold)
    except OSError as exc:
        print(f"Error reading input: {exc}", file=sys.stderr)
        return 1

    try:
        if args.output == "-":
            write_records(kept, sys.stdout)
        else:
            with open(args.output, "w", encoding="utf-8") as out_f:
                write_records(kept, out_f)
    except OSError as exc:
        print(f"Error writing output: {exc}", file=sys.stderr)
        return 1

    print_summary(stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())