from datetime import datetime
from pathlib import Path


def classify_size(size):
    # Boundaries:
    # < 1 KB       -> small
    # 1 KB to <1MB -> medium
    # >= 1 MB      -> large
    if size < 1024:
        return "small"
    elif size < 1024 * 1024:
        return "medium"
    else:
        return "large"


def organize_documents(documents):
    organized = {}

    for document in documents:
        if not isinstance(document, dict):
            continue

        name = document.get("name")
        size = document.get("size")
        modified = document.get("modified")

        # Handle empty, whitespace-only, and non-string names.
        if not isinstance(name, str):
            continue

        name = name.strip()
        if not name:
            continue

        # Handle invalid and boundary size values.
        if isinstance(size, bool):
            continue

        try:
            size = int(size)
        except (TypeError, ValueError):
            continue

        if size < 0:
            continue

        # Handle missing and malformed dates.
        if not isinstance(modified, str):
            continue

        modified = modified.strip()
        if not modified:
            continue

        try:
            modified_date = datetime.strptime(modified, "%Y-%m-%d")
        except ValueError:
            continue

        if modified_date.strftime("%Y-%m-%d") != modified:
            continue

        # Handle filenames with no extension, hidden names,
        # and normal extensions.
        suffix = Path(name).suffix.lower()

        if suffix and suffix != ".":
            extension = suffix[1:]
        else:
            extension = "no_extension"

        document_info = {
            "name": name,
            "size": size,
            "size_category": classify_size(size),
            "modified": modified
        }

        organized.setdefault(extension, []).append(document_info)

    # Deterministic ordering by filename.
    for extension in organized:
        organized[extension].sort(
            key=lambda item: item["name"].lower()
        )

    return organized


if __name__ == "__main__":
    documents = [
        {"name": "empty.txt", "size": 0, "modified": "2026-10-01"},
        {"name": "boundary-small.txt", "size": 1023, "modified": "2026-10-01"},
        {"name": "boundary-medium.txt", "size": 1024, "modified": "2026-10-01"},
        {
            "name": "boundary-large.txt",
            "size": 1024 * 1024,
            "modified": "2026-10-01"
        },
        {"name": " report.pdf ", "size": 2048, "modified": "2026-10-02"},
        {"name": "README", "size": 500, "modified": "2026-10-03"},
        {"name": "   ", "size": 100, "modified": "2026-10-01"},
        {"name": ".config", "size": 100, "modified": "2026-10-04"},
    ]

    result = organize_documents(documents)

    for extension, files in result.items():
        print(f"{extension}:")
        for file in files:
            print(f"  {file}")