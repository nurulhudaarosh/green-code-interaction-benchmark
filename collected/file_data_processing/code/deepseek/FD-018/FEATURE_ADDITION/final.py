import re
import unicodedata
from collections import defaultdict
from datetime import datetime


def normalize_text(text):
    """Normalize text: lowercase, strip accents, remove punctuation/extra spaces."""
    if text is None:
        return ""
    text = str(text)
    # Unicode normalize and strip accents
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Lowercase
    text = text.lower()
    # Replace non-alphanumeric with space
    text = re.sub(r"[^a-z0-9]+", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_date(value):
    """Normalize a date to YYYY-MM-DD string; return '' if unparseable."""
    if value is None or value == "":
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    s = str(value).strip()
    fmts = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    )
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    m = re.match(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        y, mo, d = m.groups()
        try:
            return datetime(int(y), int(mo), int(d)).strftime("%Y-%m-%d")
        except ValueError:
            return ""
    return ""


def _sort_key_id(x):
    """Deterministic sort key for IDs of mixed types."""
    return (type(x).__name__, str(x))


def detect_duplicates(records):
    """
    Detect duplicate records by exact normalized (title, description, date) match.

    records: iterable of dicts with keys 'id', 'title', 'description', 'date'.

    Returns a list of groups, each group is a dict:
        {
            'key': (norm_title, norm_description, norm_date),
            'ids': [sorted ids],   # sorted deterministically
            'count': N,            # N >= 2
        }
    Singleton groups are omitted. Groups are ordered deterministically by key.
    """
    groups = defaultdict(list)

    for rec in records:
        rid = rec.get("id")
        key = (
            normalize_text(rec.get("title")),
            normalize_text(rec.get("description")),
            normalize_date(rec.get("date")),
        )
        groups[key].append(rid)

    duplicates = []
    for key, ids in groups.items():
        if len(ids) < 2:
            # Omit singleton (non-duplicate) groups
            continue
        sorted_ids = sorted(ids, key=_sort_key_id)
        duplicates.append(
            {
                "key": key,
                "ids": sorted_ids,
                "count": len(sorted_ids),
            }
        )

    # Deterministic ordering of groups by the normalized key tuple
    duplicates.sort(key=lambda g: g["key"])
    return duplicates


def report_duplicates(records):
    """Return a deterministic human-readable report string."""
    groups = detect_duplicates(records)
    lines = []
    lines.append(f"Duplicate groups found: {len(groups)}")
    lines.append("-" * 60)
    for i, g in enumerate(groups, 1):
        title, desc, date = g["key"]
        lines.append(f"Group {i} (count={g['count']})")
        lines.append(f"  date        : {date or '<none>'}")
        lines.append(f"  title       : {title or '<empty>'}")
        lines.append(f"  description : {desc or '<empty>'}")
        lines.append(f"  ids         : {', '.join(str(x) for x in g['ids'])}")
        lines.append("-" * 60)
    return "\n".join(lines)


if __name__ == "__main__":
    sample = [
        {"id": 10, "title": "Hello, World!", "description": "First post.", "date": "2024-01-01"},
        {"id": 2,  "title": "hello world",  "description": "First   post.", "date": "01/01/2024"},
        {"id": 3,  "title": "Héllo Wörld",  "description": "First post!",   "date": "2024/01/01"},
        {"id": 4,  "title": "Different",    "description": "Another.",      "date": "2024-02-02"},
        {"id": 5,  "title": "Different",    "description": "Another.",      "date": "2024-02-02"},
        {"id": 6,  "title": "Unique",       "description": "No dup.",       "date": "2024-03-03"},
    ]
    print(report_duplicates(sample))