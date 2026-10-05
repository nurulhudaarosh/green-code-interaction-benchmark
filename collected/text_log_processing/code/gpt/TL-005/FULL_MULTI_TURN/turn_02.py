from pathlib import Path
import re
import unicodedata


def normalize_text(text: str, lowercase: bool = False) -> str:
    """Normalize Unicode and whitespace while preserving empty input."""
    text = unicodedata.normalize("NFC", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse whitespace only when content exists
    text = re.sub(r"\s+", " ", text).strip()

    if lowercase:
        text = text.lower()

    return text


def normalize_txt_files(input_dir, output_dir, lowercase=False):
    """
    Recursively normalize .txt files and mirror the input directory tree.

    Empty files are handled correctly and remain empty.
    Non-.txt files are ignored.

    Returns processing statistics.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    stats = {
        "files_processed": 0,
        "files_skipped": 0,
        "total_chars_before": 0,
        "total_chars_after": 0,
    }

    if not input_dir.exists() or not input_dir.is_dir():
        return stats

    for src_path in input_dir.rglob("*.txt"):
        if not src_path.is_file():
            continue

        # Preserve the complete directory structure
        relative_path = src_path.relative_to(input_dir)
        dst_path = output_dir / relative_path
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            text = src_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            stats["files_skipped"] += 1
            continue

        # Empty files remain empty
        normalized = normalize_text(text, lowercase=lowercase)

        try:
            dst_path.write_text(normalized, encoding="utf-8")
        except OSError:
            stats["files_skipped"] += 1
            continue

        stats["files_processed"] += 1
        stats["total_chars_before"] += len(text)
        stats["total_chars_after"] += len(normalized)

    return stats