import json
from typing import Any, Dict, List


def process_jsonl(
    input_path: str, output_path: str, min_score: float
) -> Dict[str, int]:
    """Reads a JSONL file, validates records, filters for active items with

    score >= min_score, sorts the remaining records by category, score (desc),
    and ID, and writes them to an output JSONL file. Skipped records (malformed,
    incomplete, inactive, or below score threshold) are categorized and counted.
    """
    valid_records: List[Dict[str, Any]] = []
    skipped_counts = {
        "malformed_json": 0,
        "malformed_record": 0,
        "incomplete_fields": 0,
        "inactive": 0,
        "below_threshold": 0,
    }

    required_fields = ("id", "category", "score", "is_active")

    with open(input_path, "r", encoding="utf-8") as infile:
        for line in infile:
            line = line.strip()
            if not line:
                continue

            # 1. Parse JSON format (Handle malformed JSON syntax)
            try:
                record = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                skipped_counts["malformed_json"] += 1
                continue

            # 2. Structure Check (Handle malformed record type)
            if not isinstance(record, dict):
                skipped_counts["malformed_record"] += 1
                continue

            # 3. Completeness Check (Handle missing fields or None/null values)
            missing_or_none = [
                field
                for field in required_fields
                if field not in record or record[field] is None
            ]
            if missing_or_none:
                skipped_counts["incomplete_fields"] += 1
                continue

            # 4. Type Validation (Handle wrong field data types)
            if (
                not isinstance(record["is_active"], bool)
                or not isinstance(record["score"], (int, float))
                or not isinstance(record["category"], str)
            ):
                skipped_counts["malformed_record"] += 1
                continue

            # 5. Filter Conditions (Active status and Score threshold)
            if not record["is_active"]:
                skipped_counts["inactive"] += 1
                continue

            if record["score"] < min_score:
                skipped_counts["below_threshold"] += 1
                continue

            valid_records.append(record)

    # 6. Sorting: Category (A-Z), Score (High to Low), ID (A-Z)
    valid_records.sort(key=lambda x: (x["category"], -x["score"], str(x["id"])))

    # 7. Write filtered and sorted records to output JSONL
    with open(output_path, "w", encoding="utf-8") as outfile:
        for record in valid_records:
            outfile.write(json.dumps(record) + "\n")

    # 8. Return summary metrics
    return {
        "kept": len(valid_records),
        "total_skipped": sum(skipped_counts.values()),
        **skipped_counts,
    }


# Example Usage
if __name__ == "__main__":
    input_file = "input.jsonl"
    output_file = "filtered_output.jsonl"
    score_threshold = 75.0

    stats = process_jsonl(input_file, output_file, min_score=score_threshold)

    print("Processing Complete Summary:")
    print(f"  Records Kept        : {stats['kept']}")
    print(f"  Total Skipped       : {stats['total_skipped']}")
    print(f"    - Malformed JSON  : {stats['malformed_json']}")
    print(f"    - Malformed Type  : {stats['malformed_record']}")
    print(f"    - Incomplete      : {stats['incomplete_fields']}")
    print(f"    - Inactive        : {stats['inactive']}")
    print(f"    - Below Threshold : {stats['below_threshold']}")