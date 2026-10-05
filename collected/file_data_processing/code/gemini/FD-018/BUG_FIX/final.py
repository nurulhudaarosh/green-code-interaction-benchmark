import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple


def normalize_text(text: str) -> str:
    """Normalizes text by stripping accents/diacritics, converting to lower case,

    removing punctuation, and collapsing all repeated whitespace.
    """
    if not text:
        return ""
    # Decompose unicode accents and strip diacritics
    text = "".join(
        c
        for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )
    # Convert case to lower
    text = text.lower()
    # Strip non-alphanumeric characters except basic spaces
    text = re.sub(r"[^\w\s]", "", text)
    # Collapse repeating whitespace characters (spaces, tabs, newlines) into a single space
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_date(date_str: str) -> str:
    """Normalizes various date formats into standard ISO format (YYYY-MM-DD)."""
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return date_str.strip()


def detect_duplicates(records: List[Dict[str, str]]) -> Dict[str, List[Dict]]:
    """Groups records by exact normalized title, description, and date.

    Ignores case differences and repeated whitespace. Returns deterministic duplicate groups.
    """
    grouped_records = defaultdict(list)

    for record in records:
        norm_title = normalize_text(record.get("title", ""))
        norm_desc = normalize_text(record.get("description", ""))
        norm_date = parse_date(str(record.get("date", "")))

        # Composite key for exact normalized match
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
            "id": 201,
            "title": "SUPREME   GADGET   2000",
            "description": "High   quality\t\ndevice.",
            "date": "2026-03-15",
        },
        {
            "id": 202,
            "title": "supreme gadget 2000",
            "description": "high quality device.",
            "date": "2026-03-15",
        },
        {
            "id": 203,
            "title": "SuPrEmE   GaDgEt  2000",
            "description": "HIGH    QUALITY    DEVICE.",
            "date": "03/15/2026",
        },
        {
            "id": 204,
            "title": "Supreme Gadget 2000",
            "description": "Different description entirely",
            "date": "2026-03-15",
        },
    ]

    duplicates = detect_duplicates(sample_records)

    import json

    print(json.dumps(duplicates, indent=2))