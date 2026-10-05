import hashlib
import os
from collections import defaultdict


def _sha256(path, chunk_size=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def _iter_files(input_dir, recursive):
    """Yield full paths of regular (non-symlink) files under input_dir."""
    if recursive:
        for root, _, names in os.walk(input_dir):
            for name in names:
                yield os.path.join(root, name)
    else:
        for name in os.listdir(input_dir):
            yield os.path.join(input_dir, name)


def find_exact_duplicates(input_dir, recursive=True):
    """Group byte-identical files in input_dir by SHA-256.

    If recursive is True (default), subdirectories are walked too; otherwise
    only files directly inside input_dir are considered.

    Returns {sha256_hex: [paths relative to input_dir, sorted]} containing
    only groups with 2+ files.
    """
    # Cheap pre-filter: files with a unique size can't have a duplicate,
    # so we skip hashing them entirely.
    by_size = defaultdict(list)
    for path in _iter_files(input_dir, recursive):
        # Only regular files: directories, symlinks, sockets, etc. are skipped.
        try:
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            by_size[os.path.getsize(path)].append(path)
        except OSError:
            continue  # vanished or inaccessible mid-scan

    by_hash = defaultdict(list)
    for paths in by_size.values():
        if len(paths) < 2:
            continue
        for path in paths:
            try:
                digest = _sha256(path)
            except OSError:
                continue  # unreadable file (permissions, vanished mid-scan)
            by_hash[digest].append(os.path.relpath(path, input_dir))

    return {h: sorted(p) for h, p in sorted(by_hash.items()) if len(p) >= 2}