from pathlib import Path
from datetime import datetime
import shutil


DOCUMENT_TYPES = {
    ".pdf": "PDF",
    ".doc": "Documents",
    ".docx": "Documents",
    ".txt": "Documents",
    ".rtf": "Documents",
    ".odt": "Documents",
    ".xls": "Spreadsheets",
    ".xlsx": "Spreadsheets",
    ".csv": "Spreadsheets",
    ".ods": "Spreadsheets",
    ".ppt": "Presentations",
    ".pptx": "Presentations",
    ".odp": "Presentations",
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".bmp": "Images",
    ".svg": "Images",
    ".webp": "Images",
}


def normalize_extension(filename):
    """Return a valid lowercase extension, or None."""
    if not isinstance(filename, str):
        return None

    filename = filename.strip()

    if not filename or filename.endswith("."):
        return None

    suffix = Path(filename).suffix.lower()

    if not suffix or suffix == ".":
        return None

    extension = suffix[1:]

    if not extension.isalnum():
        return None

    return suffix


def parse_date(date_value):
    """Parse supported date formats and return None for malformed dates."""
    if not isinstance(date_value, str):
        return None

    value = date_value.strip()

    if not value:
        return None

    formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
    )

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    return None


def get_category(filename):
    """Return the document category based on its extension."""
    extension = normalize_extension(filename)

    if extension is None:
        return "Unknown"

    return DOCUMENT_TYPES.get(extension, "Other")


def get_size_bucket(file_size):
    """
    Classify files by size.

    Small:       < 1 MB
    Medium:      1 MB - < 10 MB
    Large:       10 MB - < 100 MB
    Very Large:  100 MB+
    """
    if not isinstance(file_size, (int, float)) or file_size < 0:
        return "Unknown"

    megabytes = file_size / (1024 * 1024)

    if megabytes < 1:
        return "Small"
    if megabytes < 10:
        return "Medium"
    if megabytes < 100:
        return "Large"
    return "Very Large"


def get_unique_destination(destination):
    """Return a non-conflicting destination path."""
    if not destination.exists():
        return destination

    counter = 1

    while True:
        candidate = (
            destination.parent
            / f"{destination.stem}_{counter}{destination.suffix}"
        )

        if not candidate.exists():
            return candidate

        counter += 1


def organize_documents(
    source_directory,
    destination_directory=None,
    file_dates=None,
    dry_run=False,
):
    """
    Organize files by category and size bucket.

    Result structure:
        Category/
            Size Bucket/
                filename

    Example:
        PDF/Small/report.pdf
        Documents/Medium/notes.docx
        Images/Large/photo.png
    """
    source = Path(source_directory)

    destination = (
        Path(destination_directory)
        if destination_directory
        else source
    )

    file_dates = file_dates or {}

    result = {
        "moved": 0,
        "skipped": 0,
        "errors": 0,
        "invalid_dates": 0,
        "categories": {},
        "size_buckets": {},
        "details": [],
    }

    if not source.exists():
        result["errors"] += 1
        result["details"].append(
            f"Source directory does not exist: {source}"
        )
        return result

    if not source.is_dir():
        result["errors"] += 1
        result["details"].append(
            f"Source path is not a directory: {source}"
        )
        return result

    try:
        files = list(source.iterdir())
    except OSError as exc:
        result["errors"] += 1
        result["details"].append(
            f"Unable to read directory: {exc}"
        )
        return result

    for file_path in files:
        if not file_path.is_file():
            continue

        if file_path.name.startswith("."):
            result["skipped"] += 1
            result["details"].append(
                f"Skipped hidden file: {file_path.name}"
            )
            continue

        category = get_category(file_path.name)

        # Validate optional date metadata without crashing.
        if file_path.name in file_dates:
            raw_date = file_dates[file_path.name]

            if parse_date(raw_date) is None:
                result["invalid_dates"] += 1
                result["details"].append(
                    f"Malformed date ignored for "
                    f"{file_path.name}: {raw_date!r}"
                )

        try:
            file_size = file_path.stat().st_size
        except OSError as exc:
            result["errors"] += 1
            result["details"].append(
                f"Could not determine size of "
                f"{file_path.name}: {exc}"
            )
            continue

        size_bucket = get_size_bucket(file_size)

        category_directory = (
            destination / category / size_bucket
        )

        target = category_directory / file_path.name
        target = get_unique_destination(target)

        try:
            if file_path.resolve() == target.resolve():
                result["skipped"] += 1
                result["details"].append(
                    f"Already organized: {file_path.name}"
                )
                continue

            if dry_run:
                result["moved"] += 1
                result["details"].append(
                    f"Would move: {file_path.name} -> "
                    f"{category}/{size_bucket}/{target.name}"
                )
            else:
                category_directory.mkdir(
                    parents=True,
                    exist_ok=True
                )

                shutil.move(
                    str(file_path),
                    str(target)
                )

                result["moved"] += 1
                result["details"].append(
                    f"Moved: {file_path.name} -> "
                    f"{category}/{size_bucket}/{target.name}"
                )

            result["categories"][category] = (
                result["categories"].get(category, 0) + 1
            )

            result["size_buckets"][size_bucket] = (
                result["size_buckets"].get(size_bucket, 0) + 1
            )

        except (OSError, shutil.Error) as exc:
            result["errors"] += 1
            result["details"].append(
                f"Error processing {file_path.name}: {exc}"
            )

    return result


def print_summary(result):
    """Print a readable organization summary."""
    print("\nDocument Organizer Summary")
    print("=" * 40)
    print(f"Moved:          {result['moved']}")
    print(f"Skipped:        {result['skipped']}")
    print(f"Errors:         {result['errors']}")
    print(f"Invalid dates:  {result['invalid_dates']}")

    if result["categories"]:
        print("\nFiles by category:")
        for category, count in sorted(
            result["categories"].items()
        ):
            print(f"  {category}: {count}")

    if result["size_buckets"]:
        print("\nFiles by size bucket:")
        for bucket, count in sorted(
            result["size_buckets"].items()
        ):
            print(f"  {bucket}: {count}")

    if result["details"]:
        print("\nDetails:")
        for detail in result["details"]:
            print(f"  - {detail}")


if __name__ == "__main__":
    source_directory = "documents"

    # Optional date metadata.
    file_dates = {
        "report.PDF": "2026-09-15",
        "notes.docx": "15/09/2026",
        "old.txt": "not-a-date",
        "broken.pdf": "2026-99-99",
    }

    # True = preview changes without moving files.
    # False = actually organize the files.
    dry_run = False

    result = organize_documents(
        source_directory=source_directory,
        file_dates=file_dates,
        dry_run=dry_run,
    )

    print_summary(result)