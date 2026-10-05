import argparse
import json
import sys
from typing import Any, Dict, List, Tuple


def validate_and_filter_record(
    record: Dict[str, Any], min_score: float
) -> Tuple[bool, str]:
    """Validates schema requirements and applies active status + score filtering."""
    # Required field presence check
    required_fields = ["id", "category", "score", "status"]
    for field in required_fields:
        if field not in record:
            return False, "missing_fields"

    # Data type validations
    if not isinstance(record["id"], (int, str)):
        return False, "invalid_id"
    if not isinstance(record["category"], str):
        return False, "invalid_category"
    if not isinstance(record["score"], (int, float)):
        return False, "invalid_score"
    if not isinstance(record["status"], str):
        return False, "invalid_status"

    # Status check
    if record["status"].lower() != "active":
        return False, "inactive"

    # Score threshold check
    if float(record["score"]) < min_score:
        return False, "below_score_threshold"

    return True, "kept"


def process_jsonl(input_path: str, output_path: str, min_score: float) -> None:
    valid_records: List[Dict[str, Any]] = []
    counts = {
        "total": 0,
        "kept": 0,
        "skipped_invalid_json": 0,
        "skipped_missing_fields": 0,
        "skipped_invalid_types": 0,
        "skipped_inactive": 0,
        "skipped_below_score": 0,
    }

    # Open input file or standard input
    in_file = open(input_path, "r", encoding="utf-8") if input_path != "-" else sys.stdin

    try:
        for line in in_file:
            line_str = line.strip()
            if not line_str:
                continue

            counts["total"] += 1

            # Parse JSON
            try:
                record = json.loads(line_str)
            except json.JSONDecodeError:
                counts["skipped_invalid_json"] += 1
                continue

            if not isinstance(record, dict):
                counts["skipped_invalid_types"] += 1
                continue

            # Validate and filter
            is_valid, reason = validate_and_filter_record(record, min_score)

            if is_valid:
                valid_records.append(record)
                counts["kept"] += 1
            else:
                if reason == "missing_fields":
                    counts["skipped_missing_fields"] += 1
                elif reason in ("invalid_id", "invalid_category", "invalid_score", "invalid_status"):
                    counts["skipped_invalid_types"] += 1
                elif reason == "inactive":
                    counts["skipped_inactive"] += 1
                elif reason == "below_score_threshold":
                    counts["skipped_below_score"] += 1
    finally:
        if in_file is not sys.stdin:
            in_file.close()

    # Sort valid records by Category (ascending), Score (descending), ID (ascending)
    valid_records.sort(key=lambda r: (str(r["category"]), -float(r["score"]), str(r["id"])))

    # Output valid records
    out_file = open(output_path, "w", encoding="utf-8") if output_path != "-" else sys.stdout

    try:
        for rec in valid_records:
            out_file.write(json.dumps(rec) + "\n")
    finally:
        if out_file is not sys.stdout:
            out_file.close()

    # Calculate total skipped records
    total_skipped = counts["total"] - counts["kept"]

    # Print summary metrics to stderr
    sys.stderr.write("=== Processing Summary ===\n")
    sys.stderr.write(f"Total processed records : {counts['total']}\n")
    sys.stderr.write(f"Kept records             : {counts['kept']}\n")
    sys.stderr.write(f"Total skipped records    : {total_skipped}\n")
    sys.stderr.write("  - Invalid JSON format  : {}\n".format(counts["skipped_invalid_json"]))
    sys.stderr.write("  - Missing required key : {}\n".format(counts["skipped_missing_fields"]))
    sys.stderr.write("  - Invalid field types  : {}\n".format(counts["skipped_invalid_types"]))
    sys.stderr.write("  - Inactive status      : {}\n".format(counts["skipped_inactive"]))
    sys.stderr.write("  - Score below threshold: {}\n".format(counts["skipped_below_score"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter and sort JSONL records.")
    parser.add_argument(
        "-i", "--input", default="-", help="Input JSONL file path (default: stdin)"
    )
    parser.add_argument(
        "-o", "--output", default="-", help="Output JSONL file path (default: stdout)"
    )
    parser.add_argument(
        "-s", "--min-score", type=float, default=70.0, help="Minimum score threshold (default: 70.0)"
    )

    args = parser.parse_args()
    process_jsonl(args.input, args.output, args.min_score)