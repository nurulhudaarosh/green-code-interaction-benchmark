import argparse
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

# Mapping of folder names to associated file extensions
CATEGORY_MAPPING: Dict[str, set] = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff"},
    "Documents": {
        ".pdf",
        ".docx",
        ".doc",
        ".txt",
        ".rtf",
        ".odt",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".csv",
    },
    "Audio": {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm"},
    "Archives": {".zip", ".tar", ".gz", ".7z", ".rar", ".bz2"},
    "Code_Scripts": {
        ".py",
        ".js",
        ".html",
        ".css",
        ".java",
        ".cpp",
        ".c",
        ".json",
        ".xml",
        ".sh",
    },
    "Executables": {".exe", ".msi", ".dmg", ".pkg", ".deb"},
}


def validate_file_metadata(
    file_path: Path, min_size_bytes: int = 0, max_age_days: Optional[int] = None
) -> Tuple[bool, str]:
    """Validates file integrity and metadata attributes.

    Returns:
        Tuple[bool, str]: (is_valid, reason)
    """
    try:
        # 1. Existence and Symlink / File Type Checks
        if not file_path.exists():
            return False, "File does not exist"

        if file_path.is_symlink():
            return False, "Skipped symbolic link"

        if not file_path.is_file():
            return False, "Not a regular file"

        # 2. Extract Stat Metadata
        stat_info = file_path.stat()

        # 3. Size Validation (Catches zero-byte / corrupt or incomplete files)
        if stat_info.st_size < min_size_bytes:
            return False, f"File size ({stat_info.st_size} B) below minimum threshold ({min_size_bytes} B)"

        # 4. Access Permissions Validation
        if not file_path.is_readable():
            return False, "File is not readable (Permission Denied)"

        # 5. Modified Date / Age Validation (Optional filter)
        if max_age_days is not None:
            mtime = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            file_age_days = (now - mtime).days
            if file_age_days > max_age_days:
                return False, f"File age ({file_age_days} days) exceeds maximum allowed ({max_age_days} days)"

        return True, "Valid"

    except PermissionError:
        return False, "Permission denied accessing file metadata"
    except OSError as e:
        return False, f"OS error retrieving metadata: {e}"


def get_category(file_extension: str) -> str:
    """Returns the matching category folder name for a given file extension."""
    ext = file_extension.lower()
    for category, extensions in CATEGORY_MAPPING.items():
        if ext in extensions:
            return category
    return "Others"


def resolve_duplicate_path(destination_path: Path) -> Path:
    """Handles naming collisions by appending a counter before the extension."""
    if not destination_path.exists():
        return destination_path

    stem = destination_path.stem
    suffix = destination_path.suffix
    parent = destination_path.parent
    counter = 1

    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def organize_directory(
    target_dir: Path,
    dry_run: bool = False,
    min_size_bytes: int = 0,
    max_age_days: Optional[int] = None,
) -> None:
    """Scans, validates metadata, and organizes files in target_dir into category subfolders."""
    if not target_dir.exists() or not target_dir.is_dir():
        logging.error(
            f"The provided path does not exist or is not a directory: {target_dir}"
        )
        return

    logging.info(
        f"Starting file organization for: {target_dir.resolve()}"
        + (" (DRY RUN)" if dry_run else "")
    )

    moved_count = 0
    skipped_count = 0
    invalid_count = 0

    # Iterate through items in the target directory (non-recursive)
    for item in target_dir.iterdir():
        # Skip directories
        if item.is_dir():
            continue

        # Skip hidden system files (e.g., .DS_Store, .gitignore)
        if item.name.startswith("."):
            skipped_count += 1
            continue

        # Validate File Metadata before taking any actions
        is_valid, validation_reason = validate_file_metadata(
            item, min_size_bytes=min_size_bytes, max_age_days=max_age_days
        )
        if not is_valid:
            logging.warning(f"Skipping '{item.name}': {validation_reason}")
            invalid_count += 1
            continue

        category = get_category(item.suffix)
        category_folder = target_dir / category
        destination = resolve_duplicate_path(category_folder / item.name)

        if dry_run:
            logging.info(
                f"[DRY RUN] Would move: '{item.name}' -> '{category}/{destination.name}'"
            )
        else:
            try:
                category_folder.mkdir(exist_ok=True)
                shutil.move(str(item), str(destination))
                logging.info(
                    f"Moved: '{item.name}' -> '{category}/{destination.name}'"
                )
            except Exception as e:
                logging.error(f"Failed to move '{item.name}': {e}")
                continue

        moved_count += 1

    summary_prefix = "[DRY RUN] Summary" if dry_run else "Summary"
    logging.info(
        f"{summary_prefix}: {moved_count} file(s) processed, "
        f"{invalid_count} failed metadata validation, "
        f"{skipped_count} hidden/system file(s) skipped."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Organize files with robust metadata validation into categorical subfolders."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to target directory (defaults to current working directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without actually moving any files.",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=0,
        help="Minimum file size in bytes (default: 0, ignores 0-byte check if set to 0).",
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=None,
        help="Maximum file age in days based on last modification time.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    target_path = Path(args.path)
    organize_directory(
        target_path,
        dry_run=args.dry_run,
        min_size_bytes=args.min_size,
        max_age_days=args.max_age,
    )


if __name__ == "__main__":
    main()