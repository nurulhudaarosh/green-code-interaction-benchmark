import re
import unicodedata
from collections import defaultdict
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Tuple


def normalize_text(value: Any) -> str:
    """
    Normalize a title or description:
    - None -> ""
    - Unicode NFKC normalization
    - lowercase
    - collapse all whitespace to single spaces
    - strip leading/trailing whitespace
    - remove common punctuation for more robust matching
    """
    if value is None:
        return ""
    text = str(value)
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    # Replace punctuation with space so "hello, world" == "hello world"
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_date(value: Any) -> str:
    """
    Normalize a date-like value to an ISO date string (YYYY-MM-DD).
    Accepts date, datetime, or common string formats.
    Returns "" if the value cannot be parsed.
    """
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()
    if not text:
        return ""

    # Try ISO first
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass

    # Try a few common formats
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue

    return ""


def detect_duplicates(
    records: Iterable[Dict[str, Any]],
    id_key: str = "id",
    title_key: str = "title",
    description_key: str = "description",
    date_key: str = "date",
) -> Dict[Tuple[str, str, str], List[Any]]:
    """
    Group records by (normalized_title, normalized_description, normalized_date).
    Only groups with more than one record are considered duplicates.

    Returns a dict mapping the normalized key tuple to the list of record IDs
    in deterministic (sorted) order.
    """
    groups: Dict[Tuple[str, str, str], List[Any]] = defaultdict(list)

    for record in records:
        if not isinstance(record, dict):
            continue
        key = (
            normalize_text(record.get(title_key)),
            normalize_text(record.get(description_key)),
            parse_date(record.get(date_key)),
        )
        groups[key].append(record.get(id_key))

    duplicates: Dict[Tuple[str, str, str], List[Any]] = {}
    for key, ids in groups.items():
        if len(ids) > 1:
            # Deterministic ordering: sort by string representation, then original type
            duplicates[key] = sorted(ids, key=lambda x: (str(x), type(x).__name__))

    # Sort the outer dict by key for deterministic output
    return dict(sorted(duplicates.items(), key=lambda kv: kv[0]))


def format_report(
    duplicates: Dict[Tuple[str, str, str], List[Any]],
) -> str:
    """Produce a deterministic human-readable report."""
    if not duplicates:
        return "No duplicate records found."

    lines: List[str] = []
    for idx, ((title, description, date_str), ids) in enumerate(duplicates.items(), start=1):
        lines.append(f"Duplicate Group #{idx}")
        lines.append(f"  Title (normalized):       {title!r}")
        lines.append(f"  Description (normalized): {description!r}")
        lines.append(f"  Date:                     {date_str!r}")
        lines.append(f"  Duplicate IDs ({len(ids)}): {ids}")
        lines.append("")
    return "\n".join(lines).rstrip()


if __name__ == "__main__":
    sample_records = [
        {"id": 1, "title": "Hello, World!", "description": "First  post", "date": "2024-01-15"},
        {"id": 2, "title": "hello world", "description": "first post", "date": "2024-01-15"},
        {"id": 3, "title": "HELLO   WORLD", "description": "First post", "date": "2024/01/15"},
        {"id": 4, "title": "Unique", "description": "Something else", "date": "2024-02-01"},
        {"id": 5, "title": "Unique", "description": "Something else", "date": "2024-02-02"},
        {"id": 6, "title": None, "description": None, "date": None},
        {"id": 7, "title": "", "description": "", "date": ""},
    ]

    duplicates = detect_duplicates(sample_records)
    print(format_report(duplicates))