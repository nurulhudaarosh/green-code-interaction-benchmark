#!/usr/bin/env python3
"""Offline duplicate .txt file finder.

Recursively scans a directory for regular .txt files (symlinks and other
extensions ignored), normalizes content by case-folding and collapsing all
whitespace runs to a single space, hashes the normalized bytes with SHA-256,
and reports deterministic duplicate groups.

Usage:
    python dup_txt_finder.py <directory> [--json]
"""

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from collections import defaultdict

WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Case-fold and collapse all whitespace runs into a single space."""
    return WHITESPACE_RE.sub(" ", text.casefold()).strip()


def is_regular_txt(path: str) -> bool:
    """Return True only for regular files ending in .txt (not symlinks)."""
    if not path.lower().endswith(".txt"):
        return False
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(st.st_mode):
        return False
    return stat.S_ISREG(st.st_mode)


def hash_file(path: str) -> str:
    """Read, normalize, and SHA-256 hash a text file's content."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        content = fh.read()
    normalized = normalize_text(content)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_duplicates(root: str) -> dict:
    """Walk root and return {hash: [paths...]} for hashes with >1 file."""
    groups = defaultdict(list)

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Skip symlinked directories to stay offline/safe and deterministic.
        dirnames[:] = sorted(
            d for d in dirnames
            if not os.path.islink(os.path.join(dirpath, d))
        )
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            if not is_regular_txt(full):
                continue
            try:
                digest = hash_file(full)
            except OSError as exc:
                print(f"warning: cannot read {full}: {exc}", file=sys.stderr)
                continue
            groups[digest].append(os.path.abspath(full))

    return {
        digest: sorted(paths)
        for digest, paths in groups.items()
        if len(paths) > 1
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find duplicate .txt files by normalized content hash."
    )
    parser.add_argument("directory", help="Root directory to scan recursively.")
    parser.add_argument(
        "--json", action="store_true", help="Output results as JSON."
    )
    args = parser.parse_args()

    root = args.directory
    if not os.path.isdir(root):
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    duplicates = find_duplicates(root)

    if args.json:
        print(json.dumps(duplicates, indent=2, sort_keys=True))
        return 0

    if not duplicates:
        print("No duplicate .txt files found.")
        return 0

    ordered = sorted(duplicates.items(), key=lambda kv: kv[1][0])
    total_groups = len(ordered)
    total_files = sum(len(v) for _, v in ordered)

    print(f"Found {total_groups} duplicate group(s) "
          f"covering {total_files} file(s).\n")

    for idx, (digest, paths) in enumerate(ordered, start=1):
        print(f"Group {idx} (sha256:{digest}):")
        for p in paths:
            print(f"  {p}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())