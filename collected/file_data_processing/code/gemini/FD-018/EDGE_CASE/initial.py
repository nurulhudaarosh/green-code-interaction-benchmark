import re
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any, Tuple

def normalize_text(text: str) -> str:
    """Normalizes text by lowercasing, stripping special characters, and removing redundant spaces."""
    if not text:
        return ""
    # Lowercase and replace punctuation/special characters with a single space
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple whitespaces into a single space
    return re.sub(r"\s+", " ", text).strip()

def normalize_date(date_val: Any) -> str:
    """Normalizes date values into an ISO YYYY-MM-DD string format."""
    if not date_val:
        return ""
    if isinstance(date_val, datetime):
        return date_val.strftime("%Y-%m-%d")
    
    date_str = str(date_val).strip()
    # Support common date formats
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    # Return raw trimmed string if it doesn't match standard patterns
    return date_str

def detect_duplicates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Groups records by exact match of normalized title, description, and date.
    Returns a deterministic report of duplicate ID groups.
    """
    groups = defaultdict(list)
    
    for rec in records:
        rec_id = rec.get("id")
        norm_title = normalize_text(rec.get("title", ""))
        norm_desc = normalize_text(rec.get("description", ""))
        norm_dt = normalize_date(rec.get("date", ""))
        
        # Composite signature for grouping
        signature = (norm_title, norm_desc, norm_dt)
        groups[signature].append(rec_id)
    
    duplicates_report = []
    
    # Process groups deterministically sorted by signature
    for signature in sorted(groups.keys()):
        ids = groups[signature]
        if len(ids) > 1:
            sorted_ids = sorted(ids)  # Deterministic sorting of IDs
            duplicates_report.append({
                "canonical_id": sorted_ids[0],
                "duplicate_ids": sorted_ids[1:],
                "all_group_ids": sorted_ids,
                "group_size": len(sorted_ids),
                "matched_signature": {
                    "normalized_title": signature[0],
                    "normalized_description": signature[1],
                    "normalized_date": signature[2]
                }
            })
            
    return duplicates_report


# --- Example Usage ---
if __name__ == "__main__":
    dataset = [
        {"id": 101, "title": " Acme Corp. Meeting! ", "description": "Discuss Q3 goals.", "date": "2026-10-05"},
        {"id": 102, "title": "acme corp meeting", "description": "discuss q3 goals", "date": "10/05/2026"},
        {"id": 103, "title": "Acme Corp. Meeting", "description": "Discuss Q3 goals", "date": "2026-10-05"},
        {"id": 104, "title": "Different Title", "description": "Discuss Q3 goals", "date": "2026-10-05"},
        {"id": 105, "title": "Acme Corp. Meeting!", "description": "Discuss Q3 goals.", "date": "2026-10-06"},
    ]

    report = detect_duplicates(dataset)
    import json
    print(json.dumps(report, indent=2))