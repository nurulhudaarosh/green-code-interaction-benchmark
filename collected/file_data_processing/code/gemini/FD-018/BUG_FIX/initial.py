import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple


def normalize_text(text: str) -> str:
    """Normalizes text by converting to lowercase, removing accents/diacritics,

    stripping special characters, and collapsing whitespace.
    """
    if not text:
        return ""
    # Normalize unicode (decompose accented characters)
    text = unicodedata.normalize("NFKD", text)
    # Strip diacritics / accents
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Convert to lowercase
    text = text.lower()
    # Remove non-alphanumeric characters (keep basic spaces)
    text = re.sub(r"[^\w\s]", "", text)
    # Collapse multiple whitespaces into a single space
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_date(date_str: str) -> str:
    """Parses various date formats and normalizes into standard ISO format (YYYY-MM-DD)."""
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return date_str.strip()  # Fallback to trimmed string if unparseable


def detect_duplicates(records: List[Dict[str, str]]) -> Dict[str, List[Dict]]:
    """Groups records by exact normalized title, description, and date.

    Returns deterministic duplicate groups containing more than one record.
    """
    grouped_records = defaultdict(list)

    for record in records:
        norm_title = normalize_text(record.get("title", ""))
        norm_desc = normalize_text(record.get("description", ""))
        norm_date = parse_date(str(record.get("date", "")))

        # Composite key ensuring deterministic matching
        group_key = (norm_title, norm_desc, norm_date)

        grouped_records[group_key].append(
            {
                "id": record.get("id"),
                "original_record": record,
            }
        )

    # Filter down to groups with duplicates (> 1 record) and sort deterministically
    duplicate_groups = {}
    for key, group in grouped_records.items():
        if len(group) > 1:
            # Sort IDs deterministically
            sorted_group = sorted(
                group, key=lambda x: str(x["id"]) if x["id"] is not None else ""
            )
            canonical_id = f"DUP-GROUP-{sorted_group[0]['id']}"
            duplicate_groups[canonical_id] = {
                "matched_key": {
                    "normalized_title": key[0],
                    "normalized_description": key[1],
                    "normalized_date": key[2],
                },
                "duplicate_ids": [item["id"] for item in sorted_group],
                "records": [item["original_record"] for item in sorted_group],
            }

    return duplicate_groups


# --- Example Usage & Validation ---
if __name__ == "__main__":
    sample_records = [
        {
            "id": 101,
            "title": "  Widget Pro 2000! ",
            "description": "High quality gadget.",
            "date": "2026-03-15",
        },
        {
            "id": 102,
            "title": "widget pro 2000",
            "description": "High-quality gadget",
            "date": "03/15/2026",
        },
        {
            "id": 103,
            "title": "Wídget Prô 2000",
            "description": "high quality gadget",
            "date": "2026-03-15",
        },
        {
            "id": 104,
            "title": "Widget Pro 2000",
            "description": "Different description.",
            "date": "2026-03-15",
        },
        {
            "id": 105,
            "title": "Another Item",
            "description": "Unique description",
            "date": "2026-04-01",
        },
    ]

    duplicates = detect_duplicates(sample_records)

    import json

    print(json.dumps(duplicates, indent=2))