#!/usr/bin/env python3
"""
Offline duplicate .txt file finder.

Recursively scans a directory for regular .txt files (symlinks and other
extensions are ignored), normalizes their content (case-fold + whitespace
normalize), hashes the normalized content with SHA-256, and reports
deterministic duplicate groups.
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

WHITESPACE_RE = re.compile(r"\s+")


def normalize_content(text: str) -> str:
    """Case-fold and collapse/trim whitespace for stable comparison."""
    text = text.casefold()
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip()


def hash_file(path: Path) -> str | None:
    """Read, normalize, and SHA-256 hash a file's content. Returns None on read failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        print(f"warning: could not read {path}: {e}", file=sys.stderr)
        return None

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("latin-1")
        except UnicodeDecodeError as e:
            print(f"warning: could not decode {path}: {e}", file=sys.stderr)
            return None

    normalized = normalize_content(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_txt_files(root: Path):
    """Yield regular .txt files under root, recursively, skipping symlinks."""
    for path in sorted(root.rglob("*.txt")):
        # Skip symlinks (files, dirs, or broken links) entirely.
        if path.is_symlink():
            continue
        # Only regular files with a .txt extension (case-sensitive match on suffix).
        if not path.is_file():
            continue
        if path.suffix != ".txt":
            continue
        yield path


def find_duplicates(root: Path) -> dict[str, list[Path]]:
    """Return mapping of content-hash -> sorted list of duplicate file paths (groups of size >= 2)."""
    hash_to_paths: dict[str, list[Path]] = {}

    for path in find_txt_files(root):
        digest = hash_file(path)
        if digest is None:
            continue
        hash_to_paths.setdefault(digest, []).append(path)

    duplicates = {
        digest: sorted(paths)
        for digest, paths in hash_to_paths.items()
        if len(paths) > 1
    }
    return duplicates


def report(duplicates: dict[str, list[Path]]) -> None:
    if not duplicates:
        print("No duplicate .txt files found.")
        return

    # Deterministic ordering: sort groups by hash string.
    for i, digest in enumerate(sorted(duplicates.keys()), start=1):
        paths = duplicates[digest]
        print(f"Group {i} (sha256={digest}):")
        for p in paths:
            print(f"  {p}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find duplicate .txt files by normalized content hash."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory)",
    )
    args = parser.parse_args()

    root = Path(args.directory).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 1

    duplicates = find_duplicates(root)
    report(duplicates)
    return 0


if __name__ == "__main__":
    sys.exit(main())