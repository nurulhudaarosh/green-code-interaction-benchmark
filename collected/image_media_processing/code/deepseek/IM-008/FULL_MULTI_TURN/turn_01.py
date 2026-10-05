import hashlib
import os
from collections import defaultdict


def find_exact_duplicates(input_dir):
    """
    Find byte-identical files in input_dir by SHA-256 checksum.

    Returns a list of groups (each group is a sorted list of file paths)
    where every group contains 2 or more files with identical content.
    """
    hashes = defaultdict(list)

    for root, _, files in os.walk(input_dir):
        for name in files:
            path = os.path.join(root, name)
            if not os.path.isfile(path):
                continue
            try:
                h = hashlib.sha256()
                with open(path, "rb") as f:
                    for chunk in iter(lambda: f.read(1024 * 1024), b""):
                        h.update(chunk)
                hashes[h.hexdigest()].append(path)
            except (OSError, PermissionError):
                # Skip files we can't read
                continue

    groups = [sorted(paths) for paths in hashes.values() if len(paths) >= 2]
    return groups