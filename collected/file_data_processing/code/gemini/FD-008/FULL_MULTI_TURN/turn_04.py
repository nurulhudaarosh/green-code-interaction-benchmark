import hashlib
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


def get_normalized_hash(filepath: Path) -> str | None:
    """Reads file safely with UTF-8 decoding, normalizes whitespace and case, and hashes with SHA-256."""
    try:
        # Prevent opening special devices/pipes, though regular file check precedes this
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Full Unicode case-folding & whitespace collapsing across all line breaks/tabs
        normalized_content = re.sub(r"\s+", " ", content.casefold()).strip()
        return hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
    except (PermissionError, OSError, UnicodeError) as e:
        print(f"Skipping unreadable file {filepath}: {e}", file=sys.stderr)
        return None


def find_duplicate_text_files(root_dir: str) -> dict[str, list[str]]:
    """Recursively scans deep directory structures safely, reporting sorted duplicate groups (>= 2 files)."""
    hashes = defaultdict(list)
    resolved_root = os.path.abspath(root_dir)

    # os.walk handles deep nesting safely without recursion depth limits.
    # followlinks=False ensures symlinked directories are never traversed.
    for root, dirs, files in os.walk(resolved_root, followlinks=False):
        # Sort in-place to ensure deterministic traversal order
        dirs.sort()
        for filename in sorted(files):
            # Strict file extension filtering
            if not filename.lower().endswith(".txt"):
                continue

            file_path = Path(root) / filename

            try:
                # Exclude symlinks (both file symlinks and symlinked dirs/junctions)
                # and non-regular files (pipes, sockets, block devices)
                if file_path.is_symlink() or not file_path.is_file():
                    continue

                digest = get_normalized_hash(file_path)
                if digest:
                    # Store fully resolved canonical path
                    hashes[digest].append(str(file_path.resolve()))
            except (PermissionError, OSError) as e:
                print(f"Skipping path error on {file_path}: {e}", file=sys.stderr)

    # Filter strictly for duplicate groups (>= 2 files) and sort deterministically
    deterministic_duplicates = {}
    for digest in sorted(hashes.keys()):
        paths = hashes[digest]
        if len(paths) >= 2:
            deterministic_duplicates[digest] = sorted(set(paths))

    return deterministic_duplicates


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