import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict


def normalize_corpus(
    input_dir: str, 
    output_dir: str, 
    lowercase: bool = False
) -> Dict[str, Any]:
    """Recursively process .txt files from input_dir and mirror the full directory

    structure into output_dir.

    Handles:
      - Mirroring all subdirectory structures (including empty dirs)
      - Empty (0-byte) or whitespace-only files safely
      - NFC normalization, whitespace collapsing, and optional lowercasing

    Returns:
      A dictionary summarizing processed file count, total characters in/out,
      and sorted per-file statistics.
    """
    src_root = Path(input_dir).resolve()
    dest_root = Path(output_dir).resolve()

    whitespace_pattern = re.compile(r"\s+")
    per_file_records = []
    total_chars_in = 0
    total_chars_out = 0

    # Ensure the root destination exists even if source is empty
    dest_root.mkdir(parents=True, exist_ok=True)

    # os.walk bottom_up=False guarantees parents are visited first
    for dirpath, dirnames, filenames in os.walk(src_root):
        current_dir = Path(dirpath)
        rel_dir = current_dir.relative_to(src_root)
        dest_dir = dest_root / rel_dir

        # Mirror directories so empty subdirectories are preserved
        dest_dir.mkdir(parents=True, exist_ok=True)

        for filename in filenames:
            if not filename.endswith(".txt"):
                continue

            src_file = current_dir / filename
            dest_file = dest_dir / filename
            rel_file_path = str((rel_dir / filename).as_posix())

            # Read file handling encoding gracefully
            try:
                content = src_file.read_text(encoding="utf-8", errors="replace")
            except Exception:
                content = ""

            in_chars = len(content)
            total_chars_in += in_chars

            # Safe handling for empty or whitespace-only files
            if not content:
                processed = ""
            else:
                # 1. NFC normalization
                normalized = unicodedata.normalize("NFC", content)
                # 2. Collapse sequences of whitespace to a single space & strip ends
                processed = whitespace_pattern.sub(" ", normalized).strip()
                # 3. Optional lowercasing
                if lowercase:
                    processed = processed.lower()

            out_chars = len(processed)
            total_chars_out += out_chars

            # Write out mirrored file
            dest_file.write_text(processed, encoding="utf-8")

            per_file_records.append({
                "rel_path": rel_file_path,
                "chars_in": in_chars,
                "chars_out": out_chars,
            })

    # Sort deterministically by relative path
    per_file_records.sort(key=lambda item: item["rel_path"])

    return {
        "files_processed": len(per_file_records),
        "total_chars_in": total_chars_in,
        "total_chars_out": total_chars_out,
        "per_file": per_file_records,
    }