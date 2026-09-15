import hashlib
import os
import sys
from collections import defaultdict
from pathlib import Path


def normalize_content(filepath: Path) -> bytes:
    """Reads a text file, decodes it, normalizes whitespace and case,

    and returns UTF-8 encoded bytes ready for hashing.
    """
    try:
        # Read text, handling broad encoding possibilities smoothly
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception as e:
        print(
            f"Warning: Could not read file {filepath}: {e}", file=sys.stderr
        )
        return b""

    # Case-fold for robust unicode case-insensitive matching
    text = text.casefold()

    # Normalize whitespace: collapse internal runs of whitespace to a single space
    # and strip leading/trailing whitespace
    normalized_text = " ".join(text.split())

    return normalized_text.encode("utf-8")


def find_duplicate_txt_files(root_dir: str) -> dict[str, list[str]]:
    """Recursively scans root_dir for regular .txt files, ignoring symlinks,

    and groups identical files by SHA-256 hash of normalized content.
    """
    root_path = Path(root_dir).resolve()
    hash_groups = defaultdict(list)

    if not root_path.exists() or not root_path.is_dir():
        print(
            f"Error: Directory '{root_dir}' does not exist or is not a directory.",
            file=sys.stderr,
        )
        return {}

    # Traverse directory tree
    for entry in root_path.rglob("*.txt"):
        try:
            # Strictly ignore symbolic links (both files and directories)
            if entry.is_symlink():
                continue

            # Must be a regular file ending in .txt
            if entry.is_file() and entry.suffix.lower() == ".txt":
                normalized_bytes = normalize_content(entry)

                # Compute SHA-256 hash
                file_hash = hashlib.sha256(normalized_bytes).hexdigest()

                # Record POSIX-style path string for deterministic sorting
                hash_groups[file_hash].append(str(entry))

        except (PermissionError, OSError) as e:
            print(f"Warning: Skipping {entry} due to error: {e}", file=sys.stderr)
            continue

    # Filter to only groups with duplicates (count > 1)
    duplicate_groups = {
        h: sorted(paths)
        for h, paths in hash_groups.items()
        if len(paths) > 1 and h != hashlib.sha256(b"").hexdigest()
    }

    return duplicate_groups


def report_duplicates(duplicate_groups: dict[str, list[str]]) -> None:
    """Prints deterministic report of duplicate groups."""
    if not duplicate_groups:
        print("No duplicate text files found.")
        return

    # Sort groups by hash for deterministic output order
    sorted_hashes = sorted(duplicate_groups.keys())

    print(f"Found {len(sorted_hashes)} group(s) of duplicate text files:\n")

    for idx, file_hash in enumerate(sorted_hashes, 1):
        paths = duplicate_groups[file_hash]
        print(f"Group {idx} [SHA-256: {file_hash[:12]}...]")
        for path in paths:
            print(f"  - {path}")
        print()


if __name__ == "__main__":
    target_directory = sys.argv[1] if len(sys.argv) > 1 else "."
    duplicates = find_duplicate_txt_files(target_directory)
    report_duplicates(duplicates)