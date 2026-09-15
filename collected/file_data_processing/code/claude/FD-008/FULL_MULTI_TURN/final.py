#!/usr/bin/env python3
"""Offline duplicate .txt file finder.

Recursively scans a directory for regular .txt files. Symlinks (both files
and directories) are ignored/not followed, non-.txt files are skipped,
Unicode content is decoded safely, and deep or problematic trees (broken
symlinks, permission errors, unreadable files) are handled without crashing.
Reports deterministic duplicate groups (only groups with 2+ files, sorted).
"""

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path
from collections import defaultdict

WHITESPACE_RE = re.compile(r'\s+')


def normalize_content(text: str) -> str:
    """Case-fold and collapse/trim whitespace for stable comparison."""
    text = text.casefold()
    text = WHITESPACE_RE.sub(' ', text)
    return text.strip()


def hash_file(path: Path) -> str | None:
    """Read, normalize, and SHA-256 hash a file's contents.

    Returns the hex digest, or None if the file could not be read/decoded.
    """
    try:
        raw = path.read_bytes()
    except OSError as e:
        print(f"Skipping unreadable file {path}: {e}", file=sys.stderr)
        return None

    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                text = raw.decode('latin-1')
            except UnicodeDecodeError as e:
                print(f"Skipping undecodable file {path}: {e}", file=sys.stderr)
                return None

    normalized = normalize_content(text)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def _on_walk_error(err: OSError) -> None:
    print(f"Skipping unreadable directory: {err}", file=sys.stderr)


def find_txt_files(root: Path):
    """Yield regular .txt files under root, recursively.

    - Does not follow symlinked directories (avoids symlink loops / deep nesting issues).
    - Skips symlinked files.
    - Skips non-.txt files.
    - Tolerates permission errors and broken entries during traversal.
    """
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False, onerror=_on_walk_error):
        # Defensively drop any symlinked subdirectories from traversal
        # (os.walk with followlinks=False already won't descend into them,
        # but be explicit and safe against odd filesystem states).
        dirnames[:] = [
            d for d in dirnames
            if not os.path.islink(os.path.join(dirpath, d))
        ]

        for name in filenames:
            if not name.endswith('.txt'):
                continue

            full_path = Path(dirpath) / name

            try:
                if full_path.is_symlink():
                    continue
                if not full_path.is_file():
                    continue
            except OSError as e:
                print(f"Skipping inaccessible path {full_path}: {e}", file=sys.stderr)
                continue

            yield full_path


def find_duplicates(root: Path) -> dict[str, list[Path]]:
    """Group files under root by normalized-content SHA-256 hash.

    Only groups with 2+ files are kept; paths within each group are sorted.
    """
    groups: dict[str, list[Path]] = defaultdict(list)

    for path in find_txt_files(root):
        digest = hash_file(path)
        if digest is None:
            continue
        groups[digest].append(path)

    duplicates = {
        digest: sorted(paths, key=lambda p: str(p))
        for digest, paths in groups.items()
        if len(paths) >= 2
    }
    return duplicates


def report_duplicates(duplicates: dict[str, list[Path]]) -> None:
    if not duplicates:
        print("No duplicate .txt files found.")
        return

    # Deterministic group ordering by hash.
    for i, digest in enumerate(sorted(duplicates.keys()), start=1):
        paths = duplicates[digest]
        print(f"Group {i} (sha256={digest}):")
        for p in paths:
            print(f"  {p}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Find duplicate .txt files by normalized content hash."
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Root directory to scan recursively.",
    )
    args = parser.parse_args()

    root = args.directory
    if not root.is_dir():
        print(f"Error: {root} is not a directory.", file=sys.stderr)
        sys.exit(1)

    duplicates = find_duplicates(root)
    report_duplicates(duplicates)


if __name__ == "__main__":
    main()