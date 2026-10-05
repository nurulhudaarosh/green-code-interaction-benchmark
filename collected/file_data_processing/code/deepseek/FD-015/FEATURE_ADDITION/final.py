#!/usr/bin/env python3
"""
JSONL filter: validates records, keeps active records at or above a score threshold,
sorts by (category ASC, score DESC, id ASC), and counts skipped records.
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class Stats:
    total: int = 0
    kept: int = 0
    skipped: int = 0
    reasons: Dict[str, int] = field(default_factory=dict)

    def skip(self, reason: str) -> None:
        self.skipped += 1
        self.reasons[reason] = self.reasons.get(reason, 0) + 1


def is_valid(record: Any) -> Optional[str]:
    """Return None if valid, else a reason string."""
    if not isinstance(record, dict):
        return "not_an_object"

    rid = record.get("id")
    if not isinstance(rid, str) or not rid.strip():
        return "invalid_id"

    category = record.get("category")
    if not isinstance(category, str) or not category.strip():
        return "invalid_category"

    score = record.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return "invalid_score"

    active = record.get("active")
    if not isinstance(active, bool):
        return "invalid_active"

    return None


def filter_records(
    records: Iterable[Any],
    threshold: float,
) -> tuple[List[Dict[str, Any]], Stats]:
    stats = Stats()
    kept: List[Dict[str, Any]] = []

    for record in records:
        stats.total += 1

        reason = is_valid(record)
        if reason is not None:
            stats.skip(reason)
            continue

        if not record["active"]:
            stats.skip("inactive")
            continue

        if record["score"] < threshold:
            stats.skip("below_threshold")
            continue

        kept.append(record)

    # category ASC, score DESC, id ASC
    kept.sort(key=lambda r: (r["category"], -r["score"], r["id"]))
    stats.kept = len(kept)
    return kept, stats


def read_jsonl(path: Optional[str]) -> Iterable[Any]:
    stream = open(path, "r", encoding="utf-8") if path else sys.stdin
    try:
        for line_no, line in enumerate(stream, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                yield {"__parse_error__": f"line {line_no}: {exc}"}
    finally:
        if path:
            stream.close()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Filter, validate, and sort a JSONL file."
    )
    parser.add_argument("input", nargs="?", help="Input JSONL file (default: stdin)")
    parser.add_argument("-o", "--output", help="Output JSONL file (default: stdout)")
    parser.add_argument(
        "-t", "--threshold", type=float, required=True,
        help="Minimum score for a record to be kept",
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Print skip statistics to stderr",
    )
    args = parser.parse_args(argv)

    records = read_jsonl(args.input)
    kept, stats = filter_records(records, args.threshold)

    out = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    try:
        for record in kept:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
    finally:
        if args.output:
            out.close()

    if args.stats:
        print(
            f"total={stats.total} kept={stats.kept} skipped={stats.skipped}",
            file=sys.stderr,
        )
        for reason, count in sorted(stats.reasons.items()):
            print(f"  {reason}: {count}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())