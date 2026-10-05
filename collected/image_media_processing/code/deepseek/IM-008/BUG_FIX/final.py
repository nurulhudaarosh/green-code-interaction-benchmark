import hashlib
import os
from collections import defaultdict


def find_exact_duplicates(input_dir):
    """
    Walk input_dir recursively and group byte-identical files by SHA-256 checksum.

    The full content of every file is hashed (read in chunks until EOF), so
    files that share a prefix but differ later are NOT grouped together.

    Returns a list of groups (lists of file paths). Only groups with 2+ members
    are returned, and each group is sorted alphabetically.
    """
    groups = defaultdict(list)

    for root, _, filenames in os.walk(input_dir):
        for name in filenames:
            path = os.path.join(root, name)
            if not os.path.isfile(path):
                continue
            try:
                digest = _sha256(path)
            except (OSError, IOError):
                # Skip unreadable files (permissions, broken symlinks, etc.)
                continue
            groups[digest].append(path)

    duplicates = [
        sorted(paths)
        for paths in groups.values()
        if len(paths) >= 2
    ]
    return duplicates


def _sha256(path, chunk_size=1 << 20):
    """Hash the ENTIRE file with SHA-256, streaming in chunks until EOF."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:          # EOF reached — full file hashed
                break
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input_dir>")
        sys.exit(1)

    input_dir = sys.argv[1]
    duplicate_groups = find_exact_duplicates(input_dir)

    if not duplicate_groups:
        print("No exact duplicates found.")
    else:
        for i, group in enumerate(duplicate_groups, start=1):
            print(f"Duplicate group {i} ({len(group)} files):")
            for path in group:
                print(f"  {path}")
            print()