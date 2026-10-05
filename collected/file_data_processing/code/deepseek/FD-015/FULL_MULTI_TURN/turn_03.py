import json
import argparse
from typing import Any, Dict, Iterable, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter, validate, and sort JSONL records."
    )
    parser.add_argument("input", help="Path to input JSONL file")
    parser.add_argument("output", help="Path to output JSONL file")
    parser.add_argument(
        "--score-threshold",
        type=float,
        required=True,
        help="Minimum score required for a record to be kept",
    )
    return parser.parse_args()


def validate_record(record: Any) -> Tuple[bool, Optional[str]]:
    """Return (is_valid, reason_if_invalid)."""
    if not isinstance(record, dict):
        return False, "record is not a JSON object"

    required = ("id", "category", "score", "active")
    for field in required:
        if field not in record:
            return False, f"missing field: {field}"

    if not isinstance(record["id"], (str, int)) or isinstance(record["id"], bool):
        return False, "id must be a string or integer"

    if not isinstance(record["category"], str) or not record["category"]:
        return False, "category must be a non-empty string"

    score = record["score"]
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return False, "score must be a number"

    if not isinstance(record["active"], bool):
        return False, "active must be a boolean"

    return True, None


def iter_jsonl(path: str) -> Iterable[Tuple[int, Optional[Dict[str, Any]], Optional[str]]]:
    """Yield (line_number, record_or_None, error_or_None)."""
    with open(path, "r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                yield line_no, None, "empty line"
                continue
            try:
                yield line_no, json.loads(line), None
            except json.JSONDecodeError as exc:
                yield line_no, None, f"invalid JSON: {exc.msg}"


def sort_key(record: Dict[str, Any]) -> Tuple[str, float, str]:
    """Category ascending, score descending, ID ascending."""
    return (
        record["category"],              # ascending
        -float(record["score"]),         # descending
        str(record["id"]),               # ascending
    )


def main() -> None:
    args = parse_args()

    kept: List[Dict[str, Any]] = []
    skipped = 0
    skipped_reasons: Dict[str, int] = {}

    def bump(reason: str) -> None:
        nonlocal skipped
        skipped += 1
        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1

    for line_no, record, error in iter_jsonl(args.input):
        if error is not None:
            bump(f"malformed/parse error: {error}")
            continue

        valid, reason = validate_record(record)
        if not valid:
            bump(f"incomplete/invalid: {reason}")
            continue

        if not record["active"]:
            bump("inactive")
            continue

        if float(record["score"]) < args.score_threshold:
            bump("below score threshold")
            continue

        kept.append(record)

    # Sort retained records: category ASC, score DESC, ID ASC
    kept.sort(key=sort_key)

    with open(args.output, "w", encoding="utf-8") as f:
        for record in kept:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Kept: {len(kept)}")
    print(f"Skipped: {skipped}")
    for reason, count in sorted(skipped_reasons.items()):
        print(f"  - {reason}: {count}")


if __name__ == "__main__":
    main()