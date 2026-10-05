import re
from typing import Dict, List, Any


def normalize_text(text: str) -> str:
    """Normalizes text by lowercasing, removing punctuation, and stripping extra whitespace."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def find_duplicate_records(records: List[Dict[str, Any]]) -> List[List[Any]]:
    """Groups duplicate records based on normalized title, description, and date.

    Omits singleton groups, sorts IDs within every duplicate group, and returns
    a deterministically ordered list of duplicate ID groups.
    """
    groups: Dict[tuple, List[Any]] = {}

    for record in records:
        rec_id = record.get("id")
        title = normalize_text(str(record.get("title", "")))
        description = normalize_text(str(record.get("description", "")))
        date = str(record.get("date", "")).strip()

        key = (title, description, date)
        groups.setdefault(key, []).append(rec_id)

    # Filter out singleton groups (> 1 record required) and sort IDs within each group
    duplicate_groups = [
        sorted(rec_ids) for rec_ids in groups.values() if len(rec_ids) > 1
    ]

    # Deterministic sorting of output groups: largest group first, then by primary ID
    duplicate_groups.sort(key=lambda group: (-len(group), group[0]))

    return duplicate_groups


# Verification
if __name__ == "__main__":
    sample_records = [
        {
            "id": 201,
            "title": "  Python   Tutorial! ",
            "description": "Learn python fast.",
            "date": "2026-10-05",
        },
        {
            "id": 102,
            "title": "python tutorial",
            "description": "Learn python fast",
            "date": "2026-10-05",
        },
        {
            "id": 303,
            "title": "Unique Record",
            "description": "No matches",
            "date": "2026-10-05",
        },  # Singleton (Omitted)
        {
            "id": 50,
            "title": "Data Science Guide",
            "description": "Intro to ML & AI.",
            "date": "2026-09-01",
        },
        {
            "id": 12,
            "title": "Data Science Guide",
            "description": "Intro to ML & AI.",
            "date": "2026-09-01",
        },
        {
            "id": 88,
            "title": "Data Science Guide...",
            "description": "Intro to ML and AI",
            "date": "2026-09-01",
        },
    ]

    result = find_duplicate_records(sample_records)
    print("Duplicate Groups:", result)