from pathlib import Path
import re
import unicodedata


def normalize_text(text: str, lowercase: bool = False) -> str:
    """Normalize Unicode and whitespace in text."""
    # Unicode normalization
    text = unicodedata.normalize("NFC", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse all whitespace (spaces, tabs, newlines) to single spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Optional lowercase
    if lowercase:
        text = text.lower()

    return text


def normalize_txt_files(input_dir, output_dir, lowercase=False):
    """
    Normalize all .txt files in input_dir and write them to output_dir.

    Returns basic processing statistics.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "files_processed": 0,
        "files_skipped": 0,
        "total_chars_before": 0,
        "total_chars_after": 0,
    }

    for path in input_dir.glob("*.txt"):
        if not path.is_file():
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            stats["files_skipped"] += 1
            continue

        normalized = normalize_text(text, lowercase=lowercase)

        output_path = output_dir / path.name
        output_path.write_text(normalized, encoding="utf-8")

        stats["files_processed"] += 1
        stats["total_chars_before"] += len(text)
        stats["total_chars_after"] += len(normalized)

    return stats