import hashlib
import os
from collections import defaultdict


def find_exact_duplicates(input_dir):
    """
    Find byte-identical files in input_dir by SHA-256 checksum.

    Returns a list of groups, where each group is a sorted list of
    file paths that share the same content. Only groups with 2+ members
    are returned. Groups are sorted by their first member.
    """
    hashes = defaultdict(list)

    for root, _, files in os.walk(input_dir):
        for name in files:
            path = os.path.join(root, name)
            if not os.path.isfile(path):
                continue
            try:
                digest = _sha256(path)
            except OSError:
                continue
            hashes[digest].append(path)

    groups = [
        sorted(paths)
        for paths in hashes.values()
        if len(paths) >= 2
    ]
    groups.sort()
    return groups


def _sha256(path, chunk_size=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()