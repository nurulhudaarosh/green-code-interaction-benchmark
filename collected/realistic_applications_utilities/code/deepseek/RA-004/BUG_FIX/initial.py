"""
Complete Document Organizer
----------------------------
A fully functional document organizer that:
- Scans a source folder for files
- Categorizes them by type (Documents, Images, Videos, Audio, Archives, Code, etc.)
- Moves (or copies) them into organized subfolders
- Handles duplicate filenames safely
- Supports dry-run mode
- Logs all actions
- Can undo the last organization (via manifest file)

FIXES IN THIS VERSION:
1. Extension handling:
   - Files with no extension now go to "Others" (previously worked, but now
     explicit).
   - Files with trailing dots (e.g. "report.") are handled safely.
   - Case-insensitive extension matching (already worked, reinforced).
   - Multi-part extensions like ".tar.gz" are now recognized as a single
     "Archives" category instead of only ".gz".
   - Hidden files (dotfiles like ".bashrc") are correctly treated as having
     no extension and placed in "Others".
   - Extension is trimmed of surrounding whitespace before matching.

2. Malformed-date handling:
   - The manifest now includes a timestamp for each operation.
   - `load_manifest` validates the structure and date fields, discarding
     malformed entries instead of crashing.
   - A new helper `parse_timestamp` safely parses ISO timestamps and
     returns None on failure.
   - Undo operations now skip entries with malformed timestamps but still
     attempt to restore the file path (with a warning).
   - Backwards compatible with old manifests that lack a timestamp field.

Usage:
    python document_organizer.py /path/to/folder [--copy] [--dry-run] [--undo]

Example:
    python document_organizer.py ~/Downloads
    python document_organizer.py ~/Downloads --copy
    python document_organizer.py ~/Downloads --dry-run
    python document_organizer.py ~/Downloads --undo
"""

import os
import sys
import shutil
import argparse
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict


# ---------- Category definitions ----------
CATEGORIES = {
    "Documents": [
        ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt",
        ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".md"
    ],
    "Images": [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
        ".webp", ".tiff", ".ico", ".heic"
    ],
    "Videos": [
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
        ".webm", ".m4v", ".mpg", ".mpeg"
    ],
    "Audio": [
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma",
        ".m4a", ".opus"
    ],
    "Archives": [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso",
        # Multi-part archive extensions (longest-first matching):
        ".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst"
    ],
    "Code": [
        ".py", ".js", ".ts", ".java", ".c", ".cpp", ".cs", ".rb",
        ".go", ".rs", ".php", ".html", ".css", ".scss", ".json",
        ".xml", ".yml", ".yaml", ".sh", ".bat", ".sql"
    ],
    "Executables": [
        ".exe", ".msi", ".app", ".deb", ".rpm", ".apk", ".dmg"
    ],
    "Fonts": [
        ".ttf", ".otf", ".woff", ".woff2", ".eot"
    ],
    "Ebooks": [
        ".epub", ".mobi", ".azw", ".azw3", ".fb2"
    ],
}

# Multi-part extensions to check first (longest match wins).
MULTIPART_EXTENSIONS = sorted(
    [ext for ext in CATEGORIES["Archives"] if ext.count(".") > 1],
    key=len,
    reverse=True,
)

MANIFEST_NAME = ".organizer_manifest.json"


# ---------- Helpers: extension handling ----------
def get_extension(filename: str) -> str:
    """
    Extract a normalized (lowercase) extension from a filename.

    Handles:
      - Multi-part extensions like ".tar.gz" (returns ".tar.gz")
      - Trailing dots like "report." (returns "")
      - Hidden dotfiles like ".bashrc" (returns "")
      - Case-insensitivity ("FILE.PDF" -> ".pdf")
      - Surrounding whitespace ("file.pdf " -> ".pdf")
    """
    if not filename:
        return ""

    # Strip whitespace so "file.pdf " doesn't fall through.
    name = filename.strip()

    # A file starting with "." and containing no other "." is a dotfile
    # with no extension (e.g. ".bashrc", ".gitignore").
    if name.startswith(".") and name.count(".") == 1:
        return ""

    # If there's no dot at all, no extension.
    if "." not in name:
        return ""

    # If name ends with "." (e.g. "report."), treat as no extension.
    if name.endswith("."):
        return ""

    # Check multi-part extensions first (longest match).
    lower_name = name.lower()
    for ext in MULTIPART_EXTENSIONS:
        if lower_name.endswith(ext):
            return ext

    # Fall back to the last dot.
    ext = "." + name.rsplit(".", 1)[-1]
    return ext.lower()


def get_category(filename_or_ext: str) -> str:
    """
    Return the category name for a given filename or extension.
    Accepts either a full filename or a bare extension.
    """
    # If the input looks like an extension (starts with "." and has no
    # path separators), use it directly. Otherwise extract from filename.
    if filename_or_ext.startswith(".") and "/" not in filename_or_ext \
            and "\\" not in filename_or_ext:
        ext = filename_or_ext.lower()
    else:
        ext = get_extension(filename_or_ext)

    if not ext:
        return "Others"

    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return "Others"


# ---------- Helpers: malformed-date handling ----------
def parse_timestamp(value) -> datetime | None:
    """
    Safely parse an ISO-8601 timestamp string.
    Returns a datetime, or None if the value is malformed/missing.
    """
    if not value or not isinstance(value, str):
        return None
    try:
        # Support "Z" suffix (UTC) just in case.
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except (ValueError, TypeError):
        return None


def is_valid_manifest_entry(entry) -> bool:
    """
    Validate a manifest entry. Accepts either:
      - a plain string (legacy format: just the destination path)
      - a dict with 'dest' and optional 'timestamp'
    Malformed entries are rejected.
    """
    if isinstance(entry, str):
        return bool(entry.strip())
    if isinstance(entry, dict):
        dest = entry.get("dest")
        return isinstance(dest, str) and bool(dest.strip())
    return False


# ---------- Helpers: file/dir utilities ----------
def unique_destination(dest_path: Path) -> Path:
    """If a file already exists at dest_path, append (1), (2), ... until unique."""
    if not dest_path.exists():
        return dest_path
    stem = dest_path.stem
    suffix = dest_path.suffix
    parent = dest_path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def load_manifest(folder: Path) -> dict:
    """
    Load the manifest file if it exists.
    Malformed JSON or malformed entries are handled gracefully:
      - Returns {} on unreadable/invalid JSON.
      - Filters out entries that don't validate.
      - Reports malformed-date entries but keeps them (they'll still be
        undoable, just without a timestamp).
    """
    manifest_path = folder / MANIFEST_NAME
    if not manifest_path.exists():
        return {}

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log(f"Warning: could not read manifest ({e}). Starting fresh.")
        return {}

    if not isinstance(raw, dict):
        log("Warning: manifest has unexpected structure. Ignoring.")
        return {}

    cleaned = {}
    for original, entry in raw.items():
        if not isinstance(original, str) or not original.strip():
            log(f"Warning: skipping manifest entry with bad key: {original!r}")
            continue

        if not is_valid_manifest_entry(entry):
            log(f"Warning: skipping malformed manifest entry for {original!r}")
            continue

        # Normalize to dict form.
        if isinstance(entry, str):
            cleaned[original] = {"dest": entry, "timestamp": None}
        else:
            ts = entry.get("timestamp")
            parsed = parse_timestamp(ts)
            if ts is not None and parsed is None:
                log(f"Warning: malformed timestamp for {original!r}: {ts!r}")
            cleaned[original] = {
                "dest": entry["dest"],
                "timestamp": parsed.isoformat() if parsed else None,
            }

    return cleaned


def save_manifest(folder: Path, manifest: dict) -> None:
    """Save the manifest file."""
    manifest_path = folder / MANIFEST_NAME
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def log(message: str) -> None:
    """Print a timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


# ---------- Core operations ----------
def scan_files(source: Path):
    """Yield all files directly inside source (non-recursive), excluding the manifest."""
    for entry in source.iterdir():
        if entry.is_file() and entry.name != MANIFEST_NAME:
            yield entry


def organize(source: Path, copy: bool = False, dry_run: bool = False) -> dict:
    """
    Organize files in `source` into category subfolders.
    Returns a manifest dict mapping original_path -> {dest, timestamp}.
    """
    if not source.exists() or not source.is_dir():
        raise NotADirectoryError(f"Not a valid directory: {source}")

    moved = {}
    stats = defaultdict(int)

    files = list(scan_files(source))
    if not files:
        log("No files found to organize.")
        return moved

    log(f"Found {len(files)} file(s) in '{source}'")
    log(f"Mode: {'COPY' if copy else 'MOVE'}{' (DRY RUN)' if dry_run else ''}")
    log("-" * 50)

    for file_path in files:
        category = get_category(file_path.name)
        target_dir = source / category

        if not dry_run:
            target_dir.mkdir(exist_ok=True)

        dest_path = unique_destination(target_dir / file_path.name)

        try:
            if dry_run:
                log(f"[DRY] {file_path.name}  ->  {category}/")
            else:
                if copy:
                    shutil.copy2(file_path, dest_path)
                else:
                    shutil.move(str(file_path), str(dest_path))
                log(f"{file_path.name}  ->  {category}/{dest_path.name}")
                moved[str(file_path)] = {
                    "dest": str(dest_path),
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                }
            stats[category] += 1
        except (OSError, shutil.Error) as e:
            log(f"ERROR moving '{file_path.name}': {e}")

    log("-" * 50)
    log("Summary:")
    for cat, count in sorted(stats.items()):
        log(f"  {cat:<15} {count} file(s)")

    return moved


def undo(source: Path) -> None:
    """
    Undo the last organization using the manifest file.
    Handles malformed entries gracefully: bad timestamps are reported but the
    restore is still attempted; bad destination paths are skipped.
    """
    manifest = load_manifest(source)
    if not manifest:
        log("No valid manifest entries found. Nothing to undo.")
        return

    log(f"Undoing {len(manifest)} operation(s)...")
    errors = 0
    skipped = 0

    for original, entry in manifest.items():
        current = entry.get("dest")
        ts = parse_timestamp(entry.get("timestamp"))

        if not isinstance(current, str) or not current.strip():
            log(f"SKIP (malformed dest): {original!r}")
            skipped += 1
            continue

        original_path = Path(original)
        current_path = Path(current)

        if ts is None:
            log(f"Note: missing/malformed timestamp for '{current_path.name}' "
                f"(proceeding anyway)")
        else:
            log(f"  (from {ts.strftime('%Y-%m-%d %H:%M:%S')})")

        if not current_path.exists():
            log(f"SKIP (missing): {current_path}")
            skipped += 1
            continue

        if original_path.exists():
            log(f"SKIP (target exists): {original_path}")
            errors += 1
            continue

        try:
            original_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(current_path), str(original_path))
            log(f"Restored: {current_path.name}  ->  {original_path.parent.name}/")
        except (OSError, shutil.Error) as e:
            log(f"ERROR restoring '{current_path.name}': {e}")
            errors += 1

    # Clean up empty category folders
    for folder in source.iterdir():
        if folder.is_dir() and (folder.name in CATEGORIES or folder.name == "Others"):
            try:
                if not any(folder.iterdir()):
                    folder.rmdir()
                    log(f"Removed empty folder: {folder.name}/")
            except OSError:
                pass

    manifest_path = source / MANIFEST_NAME
    if manifest_path.exists():
        manifest_path.unlink()

    if errors == 0 and skipped == 0:
        log("Undo complete.")
    else:
        log(f"Undo complete with {errors} error(s) and {skipped} skipped.")


# ---------- Self-test for the fixed helpers ----------
def _self_test() -> None:
    """Quick sanity checks for extension and timestamp handling."""
    cases = [
        ("report.pdf", ".pdf", "Documents"),
        ("REPORT.PDF", ".pdf", "Documents"),
        ("archive.tar.gz", ".tar.gz", "Archives"),
        ("backup.tar.bz2", ".tar.bz2", "Archives"),
        ("data.tar", ".tar", "Archives"),
        ("no_extension", "", "Others"),
        ("trailingdot.", "", "Others"),
        (".bashrc", "", "Others"),
        (".gitignore", "", "Others"),
        ("file.pdf ", ".pdf", "Documents"),
        ("my.file.name.PNG", ".png", "Images"),
    ]
    for name, expected_ext, expected_cat in cases:
        ext = get_extension(name)
        cat = get_category(name)
        assert ext == expected_ext, f"{name!r}: ext {ext!r} != {expected_ext!r}"
        assert cat == expected_cat, f"{name!r}: cat {cat!r} != {expected_cat!r}"

    # Timestamp parsing
    assert parse_timestamp("2024-01-15T10:30:00") is not None
    assert parse_timestamp("2024-01-15T10:30:00Z") is not None
    assert parse_timestamp("not-a-date") is None
    assert parse_timestamp("") is None
    assert parse_timestamp(None) is None
    assert parse_timestamp(12345) is None

    # Manifest entry validation
    assert is_valid_manifest_entry("path/to/file")
    assert is_valid_manifest_entry({"dest": "path/to/file", "timestamp": "x"})
    assert is_valid_manifest_entry({"dest": "path/to/file"})
    assert not is_valid_manifest_entry({"dest": ""})
    assert not is_valid_manifest_entry({})
    assert not is_valid_manifest_entry(123)
    assert not is_valid_manifest_entry(None)

    print("Self-test passed.")


# ---------- CLI ----------
def main():
    parser = argparse.ArgumentParser(
        description="Organize files in a folder by category.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python document_organizer.py ~/Downloads\n"
               "  python document_organizer.py ~/Downloads --copy\n"
               "  python document_organizer.py ~/Downloads --dry-run\n"
               "  python document_organizer.py ~/Downloads --undo\n"
    )
    parser.add_argument("folder", nargs="?", help="Folder to organize")
    parser.add_argument("--copy", action="store_true",
                        help="Copy files instead of moving them")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview actions without changing anything")
    parser.add_argument("--undo", action="store_true",
                        help="Undo the last organization using the manifest")
    parser.add_argument("--self-test", action="store_true",
                        help="Run internal tests for extension/date handling")

    args = parser.parse_args()

    if args.self_test:
        _self_test()
        return

    if not args.folder:
        parser.error("the following arguments are required: folder")

    source = Path(args.folder).expanduser().resolve()

    try:
        if args.undo:
            undo(source)
        else:
            moved = organize(source, copy=args.copy, dry_run=args.dry_run)
            if moved and not args.dry_run:
                save_manifest(source, moved)
                log(f"Manifest saved: {MANIFEST_NAME}")
    except NotADirectoryError as e:
        log(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        log("Interrupted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()