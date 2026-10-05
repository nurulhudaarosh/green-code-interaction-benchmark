import os
import hashlib
from collections import defaultdict


def find_exact_duplicates(input_dir):
    """
    Find byte-identical files in input_dir using full-file SHA-256 hashes.

    Returns:
        A list of duplicate groups, where each group contains 2+ file paths
        sorted alphabetically.
    """
    hashes = defaultdict(list)

    for root, _, files in os.walk(input_dir):
        for filename in files:
            path = os.path.join(root, filename)

            sha256 = hashlib.sha256()

            # Hash the ENTIRE file, not just the first part.
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    sha256.update(chunk)

            hashes[sha256.hexdigest()].append(path)

    # Keep only groups containing actual duplicates.
    duplicates = [
        sorted(paths)
        for paths in hashes.values()
        if len(paths) >= 2
    ]

    # Optional: deterministic ordering of duplicate groups.
    duplicates.sort(key=lambda group: group[0])

    return duplicates