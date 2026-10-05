from pathlib import Path
import re
import unicodedata


def normalize_text(text: str, lowercase: bool = False) -> str:
    """Normalize Unicode and whitespace, with optional lowercasing."""
    text = unicodedata.normalize("NFC", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    if lowercase:
        text = text.lower()

    return text


def normalize_txt_files(input_dir, output_dir, lowercase=False):
    """
    Recursively normalize .txt files while mirroring the directory tree.

    Handles:
      - Empty input directories
      - Directories containing no .txt files
      - Non-.txt files
      - Empty .txt files
      - Invalid UTF-8 files
      - Nested directories

    Returns a detailed statistics report.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    stats = {
        "input_dir_exists": input_dir.exists(),
        "files_found": 0,
        "files_processed": 0,
        "files_skipped": 0,
        "non_txt_files": 0,
        "empty_files": 0,
        "chars_before": 0,
        "chars_after": 0,
        "chars_removed": 0,
        "lowercase": lowercase,
        "file_stats": [],
    }

    # Gracefully handle missing or invalid input directory
    if not input_dir.exists() or not input_dir.is_dir():
        return stats

    # Walk everything so non-.txt files can be counted,
    # while only .txt files are processed.
    for src_path in input_dir.rglob("*"):
        if not src_path.is_file():
            continue

        if src_path.suffix.lower() != ".txt":
            stats["non_txt_files"] += 1
            continue

        stats["files_found"] += 1

        relative_path = src_path.relative_to(input_dir)
        dst_path = output_dir / relative_path

        try:
            text = src_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            stats["files_skipped"] += 1
            stats["file_stats"].append({
                "file": str(relative_path),
                "status": "skipped",
                "error": str(exc),
            })
            continue

        is_empty = not bool(text)

        if is_empty:
            stats["empty_files"] += 1

        normalized = normalize_text(text, lowercase=lowercase)

        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            dst_path.write_text(normalized, encoding="utf-8")
        except OSError as exc:
            stats["files_skipped"] += 1
            stats["file_stats"].append({
                "file": str(relative_path),
                "status": "skipped",
                "error": str(exc),
            })
            continue

        before = len(text)
        after = len(normalized)

        stats["files_processed"] += 1
        stats["chars_before"] += before
        stats["chars_after"] += after
        stats["chars_removed"] += before - after

        stats["file_stats"].append({
            "file": str(relative_path),
            "status": "processed",
            "empty": is_empty,
            "chars_before": before,
            "chars_after": after,
            "chars_removed": before - after,
        })

    return stats