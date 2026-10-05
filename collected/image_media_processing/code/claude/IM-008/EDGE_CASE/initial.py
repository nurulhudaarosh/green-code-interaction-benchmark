import hashlib
import os
from collections import defaultdict


def find_exact_duplicates(input_dir):
    """Return {sha256_hex: [sorted paths]} for byte-identical files (2+ per group)."""

    def sha256_of(path, chunk_size=1 << 20):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()

    # Cheap pre-filter: files with a unique size can't have a duplicate.
    by_size = defaultdict(list)
    for root, _, files in os.walk(input_dir):
        for name in files:
            path = os.path.join(root, name)
            if os.path.islink(path):
                continue
            try:
                by_size[os.path.getsize(path)].append(path)
            except OSError:
                continue

    by_hash = defaultdict(list)
    for paths in by_size.values():
        if len(paths) < 2:
            continue
        for path in paths:
            try:
                by_hash[sha256_of(path)].append(path)
            except OSError:
                continue  # unreadable file (permissions, deleted mid-scan)

    return {h: sorted(p) for h, p in by_hash.items() if len(p) >= 2}