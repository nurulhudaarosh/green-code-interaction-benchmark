import hashlib
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


def normalize_and_hash(filepath: Path) -> str:
    """Reads file, case-folds text, collapses all whitespace, and returns SHA-256 hash."""
    hasher = hashlib.sha256()

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Case-fold and normalize all repeated whitespace (spaces, tabs, newlines) to single spaces
    normalized_content = re.sub(r"\s+", " ", content.casefold()).strip()

    hasher.update(normalized_content.encode("utf-8"))
    return hasher.hexdigest()


def find_duplicate_text_files(root_dir: str) -> dict[str, list[str]]:
    """Recursively scans directory for .txt files and groups identical normalized contents."""
    hashes = defaultdict(list)

    for root, _, files in os.walk(root_dir):
        for filename in sorted(files):
            # Strictly filter for .txt extensions
            if not filename.lower().endswith(".txt"):
                continue

            file_path = Path(root) / filename

            # Skip symlinks and non-regular files
            if file_path.is_symlink() or not file_path.is_file():
                continue

            try:
                digest = normalize_and_hash(file_path)
                hashes[digest].append(str(file_path.resolve()))
            except (PermissionError, OSError) as e:
                print(f"Skipping unreadable file {file_path}: {e}", file=sys.stderr)

    # Return deterministic duplicate groups sorted by hash and paths
    return {
        digest: sorted(paths)
        for digest, paths in sorted(hashes.items())
        if len(paths) > 1
    }


if __name__ == "__main__":
    target_directory = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"Scanning directory: {os.path.abspath(target_directory)}\n")

    duplicate_groups = find_duplicate_text_files(target_directory)

    if not duplicate_groups:
        print("No duplicate text files found.")
    else:
        print(f"Found {len(duplicate_groups)} duplicate group(s):\n")
        for i, (digest, paths) in enumerate(duplicate_groups.items(), start=1):
            print(f"Group {i} (SHA-256: {digest[:12]}...):")
            for path in paths:
                print(f"  - {path}")
            print()