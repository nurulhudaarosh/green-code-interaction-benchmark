from datetime import datetime
from pathlib import Path


def classify_size(size):
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

        if not isinstance(name, str) or not name.strip():
            continue
        name = name.strip()

        if isinstance(size, bool):
            continue
        try:
            size = int(size)
        except (TypeError, ValueError):
            continue

        if size < 0:
            continue

        if not isinstance(modified, str) or not modified.strip():
            continue

        modified = modified.strip()

        try:
            modified_date = datetime.strptime(modified, "%Y-%m-%d")
        except ValueError:
            continue

        if modified_date.strftime("%Y-%m-%d") != modified:
            continue

        extension = Path(name).suffix.lower()
        extension = extension[1:] if extension else "no_extension"

        document_info = {
            "name": name,
            "size": size,
            "size_category": classify_size(size),
            "modified": modified
        }

        organized.setdefault(extension, []).append(document_info)

    for extension in organized:
        organized[extension].sort(key=lambda item: item["name"].lower())

    return organized


if __name__ == "__main__":
    documents = [
        {"name": "report.pdf", "size": 1500, "modified": "2026-10-01"},
        {"name": "notes.txt", "size": 800, "modified": "2026-09-28"},
        {"name": "photo.jpg", "size": 2400, "modified": "2026-09-30"},
        {"name": "large.zip", "size": 2 * 1024 * 1024, "modified": "2026-10-02"},
    ]

    result = organize_documents(documents)

    for extension, files in result.items():
        print(f"{extension}:")
        for file in files:
            print(f"  {file}")