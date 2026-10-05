import re
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any

def normalize_title(text: str) -> str:
    """Normalizes title by lowercasing, stripping special characters, and collapsing whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def normalize_description(text: str) -> str:
    """Normalizes description by trimming surrounding spaces and collapsing repeated whitespace while preserving punctuation."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def normalize_date(date_val: Any) -> str:
    """Normalizes date values into an ISO YYYY-MM-DD string format."""
    if not date_val:
        return ""
    if isinstance(date_val, datetime):
        return date_val.strftime("%Y-%m-%d")
    
    date_str = str(date_val).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return date_str

def detect_duplicates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Groups records by exact match of normalized title, description (punctuation intact), and date.
    Returns a deterministic report of duplicate ID groups.
    """
    groups = defaultdict(list)
    
    for rec in records:
        rec_id = rec.get("id")
        norm_title = normalize_title(rec.get("title", ""))
        norm_desc = normalize_description(rec.get("description", ""))
        norm_dt = normalize_date(rec.get("date", ""))
        
        signature = (norm_title, norm_desc, norm_dt)
        groups[signature].append(rec_id)
    
    duplicates_report = []
    
    for signature in sorted(groups.keys()):
        ids = groups[signature]
        if len(ids) > 1:
            sorted_ids = sorted(ids)
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
        # Match group 1 (Punctuation in description preserved)
        {"id": 101, "title": " Acme Corp. Meeting! ", "description": "  Discuss   Q3 goals!  \n  ", "date": "2026-10-05"},
        {"id": 102, "title": "acme corp meeting", "description": "Discuss Q3 goals!", "date": "10/05/2026"},
        # Distinct due to punctuation differences in description
        {"id": 103, "title": "Acme Corp. Meeting", "description": "Discuss Q3 goals.", "date": "2026-10-05"},
    ]

    report = detect_duplicates(dataset)
    import json
    print(json.dumps(report, indent=2))