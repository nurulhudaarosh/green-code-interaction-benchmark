from datetime import datetime


def get_extension(filename):
    """Return the lowercase file extension, or an empty string if missing/invalid."""
    if not isinstance(filename, str):
        return ""

    filename = filename.strip()
    if not filename or "." not in filename:
        return ""

    name, extension = filename.rsplit(".", 1)

    if not name.strip() or not extension.strip():
        return ""

    return extension.strip().lower()


def parse_document(record):
    """
    Parse a document record in the format:
    name|date|size

    Returns None for malformed records.
    """
    if not isinstance(record, str) or not record.strip():
        return None

    parts = record.split("|")

    if len(parts) != 3:
        return None

    name = parts[0].strip()
    date_text = parts[1].strip()
    size_text = parts[2].strip()

    # Empty document names are invalid.
    if not name:
        return None

    # Validate date.
    try:
        date = datetime.strptime(date_text, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

    # Validate size.
    try:
        size = float(size_text)
    except (ValueError, TypeError):
        return None

    if size < 0:
        return None

    extension = get_extension(name)

    return {
        "name": name,
        "date": date,
        "size": size,
        "extension": extension,
    }


def classify_size(size):
    """
    Classify file size using exact boundary handling:

    < 1 MB       -> small
    1 MB–10 MB   -> medium
    > 10 MB      -> large

    Exact boundaries belong to the lower bucket where applicable.
    """
    if size < 1:
        return "small"
    elif size <= 10:
        return "medium"
    else:
        return "large"


def organize_documents(records):
    """
    Organize valid document records by extension and size bucket.

    Handles:
    - missing extensions
    - malformed separators
    - empty names
    - malformed dates
    - invalid/negative sizes
    - exact size boundaries
    - empty/whitespace-only records
    """
    organized = {
        "no_extension": [],
        "extensions": {},
        "size_buckets": {
            "small": [],
            "medium": [],
            "large": [],
        },
    }

    if not isinstance(records, list):
        return organized

    for record in records:
        document = parse_document(record)

        if document is None:
            continue

        name = document["name"]
        extension = document["extension"]
        size = document["size"]

        # Organize by extension.
        if not extension:
            organized["no_extension"].append(name)
        else:
            if extension not in organized["extensions"]:
                organized["extensions"][extension] = []
            organized["extensions"][extension].append(name)

        # Organize by exact size boundaries.
        bucket = classify_size(size)
        organized["size_buckets"][bucket].append(name)

    return organized


if __name__ == "__main__":
    records = [
        "report.pdf|2026-01-10|0.5",
        "presentation.pptx|2026-02-15|1",
        "research.docx|2026-03-01|10",
        "largefile.pdf|2026-03-20|10.01",
        "README|2026-04-01|2",
        " .pdf|2026-04-02|3",
        "report.pdf|2026/04/03|4",
        "bad|record|extra|field",
        "notes.txt|2026-05-01|0",
        "   |2026-05-01|2",
        "archive.|2026-05-02|5",
    ]

    result = organize_documents(records)

    print(result)