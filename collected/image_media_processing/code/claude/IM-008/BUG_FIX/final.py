import hashlib
import os
import sys
import tempfile
from collections import defaultdict


def find_exact_duplicates(input_dir, chunk_size=1 << 20):
    """Return {sha256_hex: [sorted paths]} for groups of 2+ byte-identical files.

    The full contents of every candidate file are hashed (in chunks, until EOF).
    """
    # Pass 1: bucket by size, since files with different sizes can't be identical
    by_size = defaultdict(list)
    for root, _, names in os.walk(input_dir):
        for name in names:
            path = os.path.join(root, name)
            if os.path.islink(path):
                continue
            try:
                by_size[os.path.getsize(path)].append(path)
            except OSError:
                continue

    # Pass 2: hash only files that share a size with at least one other file
    by_hash = defaultdict(list)
    for paths in by_size.values():
        if len(paths) < 2:
            continue
        for path in paths:
            digest = hashlib.sha256()
            try:
                with open(path, "rb") as f:
                    while chunk := f.read(chunk_size):
                        digest.update(chunk)
            except OSError:
                continue
            by_hash[digest.hexdigest()].append(path)

    return {h: sorted(p) for h, p in by_hash.items() if len(p) >= 2}


def _test_shared_header_not_duplicates():
    with tempfile.TemporaryDirectory() as d:
        header = b"H" * 4096
        for name, tail in [("a.bin", b"one"), ("b.bin", b"two"), ("c.bin", b"one")]:
            with open(os.path.join(d, name), "wb") as f:
                f.write(header + tail)
        groups = list(find_exact_duplicates(d).values())
        assert groups == [[os.path.join(d, "a.bin"), os.path.join(d, "c.bin")]]


def _test_multi_chunk_files():
    # Small chunk_size forces multiple reads; difference sits in the last byte
    with tempfile.TemporaryDirectory() as d:
        for name, tail in [("x", b"A"), ("y", b"B")]:
            with open(os.path.join(d, name), "wb") as f:
                f.write(b"Z" * 10_000 + tail)
        assert find_exact_duplicates(d, chunk_size=64) == {}


if __name__ == "__main__":
    if len(sys.argv) == 2:
        for h, paths in find_exact_duplicates(sys.argv[1]).items():
            print(h)
            for p in paths:
                print("  ", p)
    else:
        _test_shared_header_not_duplicates()
        _test_multi_chunk_files()
        print("All tests passed. Usage: python find_duplicates.py <dir>")