import hashlib
import os
from collections import defaultdict


def find_exact_duplicates(input_dir):
    """
    Walk input_dir recursively and group byte-identical files by SHA-256 checksum.

    Returns a list of groups (lists of file paths), each group containing
    paths to files with identical content. Only groups with 2+ members are
    returned, and each group is sorted alphabetically.
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
                # Skip files we can't read (permissions, broken symlinks, etc.)
                continue
            groups[digest].append(path)

    duplicates = [
        sorted(paths)
        for paths in groups.values()
        if len(paths) >= 2
    ]
    return duplicates


def _sha256(path, chunk_size=1 << 20):
    """Compute the SHA-256 hex digest of a file, reading in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()