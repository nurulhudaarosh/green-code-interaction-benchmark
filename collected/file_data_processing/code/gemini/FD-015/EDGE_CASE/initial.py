import json
from typing import Dict, List, Any, Tuple


def process_jsonl(
    input_filepath: str, 
    output_filepath: str, 
    min_score: float
) -> Dict[str, int]:
    """
    Validates, filters, sorts, and writes records from a JSONL file.

    Rules:
    - Must be valid JSON with required fields: 'id', 'category', 'score', 'status'
    - 'score' must be numeric
    - Keeps records where status == 'active' and score >= min_score
    - Sorts output by: category (asc), score (desc), id (asc)
    """
    valid_records: List[Dict[str, Any]] = []
    
    skipped_counts = {
        "invalid_json": 0,
        "missing_fields": 0,
        "invalid_score_type": 0,
        "inactive_status": 0,
        "below_score_threshold": 0,
    }

    required_fields = {"id", "category", "score", "status"}

    with open(input_filepath, "r", encoding="utf-8") as infile:
        for line in infile:
            line = line.strip()
            if not line:
                continue

            # 1. Validate JSON structure
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                skipped_counts["invalid_json"] += 1
                continue

            # 2. Validate required schema fields
            if not isinstance(record, dict) or not required_fields.issubset(record.keys()):
                skipped_counts["missing_fields"] += 1
                continue

            # 3. Validate score data type
            score = record.get("score")
            if not isinstance(score, (int, float)) or isinstance(score, bool):
                skipped_counts["invalid_score_type"] += 1
                continue

            # 4. Filter inactive records
            if record.get("status") != "active":
                skipped_counts["inactive_status"] += 1
                continue

            # 5. Filter score threshold
            if score < min_score:
                skipped_counts["below_score_threshold"] += 1
                continue

            valid_records.append(record)

    # Sort key: Category (Ascending), Score (Descending), ID (Ascending)
    def sort_key(rec: Dict[str, Any]) -> Tuple[str, float, Any]:
        return (str(rec["category"]), -float(rec["score"]), rec["id"])

    valid_records.sort(key=sort_key)

    # Write sorted records to output JSONL
    with open(output_filepath, "w", encoding="utf-8") as outfile:
        for record in valid_records:
            outfile.write(json.dumps(record) + "\n")

    return skipped_counts


# Example Usage:
if __name__ == "__main__":
    # Process file with a minimum score threshold of 75.0
    metrics = process_jsonl(
        input_filepath="input_records.jsonl",
        output_filepath="filtered_records.jsonl",
        min_score=75.0
    )
    
    print("Skipped Records Breakdown:")
    for reason, count in metrics.items():
        print(f" - {reason}: {count}")
    print(f" Total Skipped: {sum(metrics.values())}")