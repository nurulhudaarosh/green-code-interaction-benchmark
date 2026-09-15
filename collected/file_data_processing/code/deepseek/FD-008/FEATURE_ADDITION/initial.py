#!/usr/bin/env python3
"""
Offline duplicate .txt file finder.

- Recursively scans a directory
- Only considers regular .txt files (ignores symlinks and other extensions)
- Case-folds and whitespace-normalizes content
- Hashes normalized content with SHA-256
- Reports deterministic duplicate groups
"""

import argparse
import hashlib
import os
import sys
from collections import defaultdict


def normalize_content(text: str) -> str:
    """Case-fold and collapse all whitespace to single spaces."""
    return " ".join(text.split()).casefold()


def hash_normalized_file(path: str) -> str | None:
    """Read a text file, normalize content, return SHA-256 hex digest."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except (OSError, IOError) as e:
        print(f"warning: could not read {path}: {e}", file=sys.stderr)
        return None

    normalized = normalize_content(content)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_duplicates(root: str) -> dict[str, list[str]]:
    """Walk root and group .txt files by hash of normalized content."""
    groups: dict[str, list[str]] = defaultdict(list)

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Sort for deterministic traversal
        dirnames.sort()
        filenames.sort()

        for name in filenames:
            if not name.lower().endswith(".txt"):
                continue

            full_path = os.path.join(dirpath, name)

            # Skip symlinks (to files or dirs)
            if os.path.islink(full_path):
                continue

            # Only regular files
            if not os.path.isfile(full_path):
                continue

            digest = hash_normalized_file(full_path)
            if digest is not None:
                groups[digest].append(os.path.abspath(full_path))

    # Keep only groups with more than one file
    return {h: sorted(paths) for h, paths in groups.items() if len(paths) > 1}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find duplicate .txt files by normalized content."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory)",
    )
    args = parser.parse_args()

    root = os.path.abspath(args.directory)
    if not os.path.isdir(root):
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 1

    duplicates = find_duplicates(root)

    if not duplicates:
        print("No duplicate .txt files found.")
        return 0

    # Deterministic output order: sort groups by their first file path
    ordered = sorted(duplicates.values(), key=lambda paths: paths[0])

    total_groups = len(ordered)
    total_files = sum(len(g) for g in ordered)
    print(f"Found {total_groups} duplicate group(s) covering {total_files} file(s):\n")

    for i, paths in enumerate(ordered, start=1):
        print(f"Group {i}:")
        for p in paths:
            print(f"  {p}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())