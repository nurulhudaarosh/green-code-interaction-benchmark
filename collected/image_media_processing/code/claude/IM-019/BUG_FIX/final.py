"""Cluster visually similar images using average hash + union-find."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from PIL import Image

log = logging.getLogger(__name__)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


def _average_hash(path: Path, hash_size: int) -> int:
    """Return a hash_size*hash_size-bit average hash as an int."""
    with Image.open(path) as img:
        img = img.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())
    mean = sum(pixels) / len(pixels)
    bits = 0
    for p in pixels:
        bits = (bits << 1) | (p > mean)
    return bits


def _hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()  # Python 3.10+


class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path halving
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]


def find_fuzzy_duplicates(
    input_dir: str | os.PathLike,
    hash_size: int = 8,
    max_hamming: int = 5,
) -> list[list[str]]:
    """Group near-duplicate images under ``input_dir`` (recursively).

    Each image is reduced to an average hash (hash_size x hash_size bits).
    Two images are linked if their Hamming distance is <= ``max_hamming``.
    Grouping is transitive: if A~B and B~C, then A, B, C share a cluster
    even when A and C are farther apart than ``max_hamming``.

    Returns a list of clusters (each a sorted list of file paths) containing
    at least two images, sorted by descending size then first path.
    Unreadable files are skipped with a warning.
    """
    if hash_size < 1:
        raise ValueError("hash_size must be >= 1")
    total_bits = hash_size * hash_size
    if not 0 <= max_hamming <= total_bits:
        raise ValueError(
            f"max_hamming must be between 0 and {total_bits} "
            f"(hash_size*hash_size) for hash_size={hash_size}"
        )

    root = Path(input_dir)
    if not root.is_dir():
        raise NotADirectoryError(f"{input_dir!r} is not a directory")

    paths: list[Path] = []
    hashes: list[int] = []
    for dirpath, _, filenames in os.walk(root):
        for name in sorted(filenames):
            p = Path(dirpath) / name
            if p.suffix.lower() not in IMAGE_EXTS:
                continue
            try:
                hashes.append(_average_hash(p, hash_size))
                paths.append(p)
            except Exception as exc:  # corrupt/unsupported image
                log.warning("Skipping %s: %s", p, exc)

    n = len(paths)
    uf = _UnionFind(n)

    # Exact-hash buckets first (cheap), then pairwise comparison of unique hashes.
    by_hash: dict[int, list[int]] = {}
    for i, h in enumerate(hashes):
        by_hash.setdefault(h, []).append(i)
    for idxs in by_hash.values():
        for j in idxs[1:]:
            uf.union(idxs[0], j)

    unique = list(by_hash.items())  # (hash, [indices])
    for a in range(len(unique)):
        ha, ia = unique[a]
        for b in range(a + 1, len(unique)):
            hb, ib = unique[b]
            if _hamming(ha, hb) <= max_hamming:
                uf.union(ia[0], ib[0])

    groups: dict[int, list[str]] = {}
    for i in range(n):
        groups.setdefault(uf.find(i), []).append(str(paths[i]))

    clusters = [sorted(g) for g in groups.values() if len(g) > 1]
    clusters.sort(key=lambda g: (-len(g), g[0]))
    return clusters


if __name__ == "__main__":
    import sys

    for k, cluster in enumerate(find_fuzzy_duplicates(sys.argv[1]), 1):
        print(f"Cluster {k} ({len(cluster)} images)")
        for f in cluster:
            print(f"  {f}")