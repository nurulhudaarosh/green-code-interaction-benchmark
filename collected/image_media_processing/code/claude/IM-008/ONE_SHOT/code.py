import hashlib
import os
from collections import defaultdict
from pathlib import Path


def find_exact_duplicates(input_dir, chunk_size=1024 * 1024):
    """Group byte-identical files under input_dir by SHA-256 checksum.

    Returns {sha256_hexdigest: [sorted file paths]} containing only groups
    with 2+ members. Paths are strings.
    """
    # Pass 1: bucket by size. A file with a unique size can't have a duplicate,
    # so it never needs to be hashed.
    by_size = defaultdict(list)
    for root, _dirs, files in os.walk(input_dir):
        for name in files:
            path = Path(root) / name
            if path.is_symlink() or not path.is_file():
                continue
            try:
                by_size[path.stat().st_size].append(path)
            except OSError:
                continue

    # Pass 2: hash only files that share a size with at least one other file.
    by_hash = defaultdict(list)
    for paths in by_size.values():
        if len(paths) < 2:
            continue
        for path in paths:
            h = hashlib.sha256()
            try:
                with open(path, "rb") as f:
                    while chunk := f.read(chunk_size):
                        h.update(chunk)
            except OSError:
                continue  # unreadable or vanished mid-scan
            by_hash[h.hexdigest()].append(str(path))

    return {d: sorted(p) for d, p in by_hash.items() if len(p) >= 2}