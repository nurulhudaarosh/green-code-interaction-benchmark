"""Find near-duplicate images using average hashing + union-find clustering."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

log = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


class UnionFind:
    """Disjoint-set with path compression and union by rank."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # path compression
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def average_hash(path: Path, hash_size: int = 8) -> int:
    """Return a hash_size*hash_size-bit average hash of the image as an int."""
    with Image.open(path) as img:
        img = img.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())
    mean = sum(pixels) / len(pixels)
    value = 0
    for p in pixels:
        value = (value << 1) | (1 if p > mean else 0)
    return value


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def find_fuzzy_duplicates(
    input_dir: str | Path,
    hash_size: int = 8,
    max_hamming: int = 5,
) -> list[list[Path]]:
    """Cluster near-duplicate images in `input_dir` (searched recursively).

    Two images are linked if the Hamming distance between their average hashes
    is <= max_hamming. Grouping is transitive: if A~B and B~C, then A, B, C
    share a cluster even if A and C are farther apart than max_hamming.

    Returns a list of clusters (each a sorted list of Paths) containing at least
    two images. Clusters are ordered by size (largest first), then by first path.
    Unreadable files are skipped with a warning.
    """
    if hash_size < 1:
        raise ValueError("hash_size must be >= 1")
    if max_hamming < 0:
        raise ValueError("max_hamming must be >= 0")

    root = Path(input_dir)
    if not root.is_dir():
        raise NotADirectoryError(f"{root} is not a directory")

    paths: list[Path] = []
    hashes: list[int] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        try:
            hashes.append(average_hash(p, hash_size))
            paths.append(p)
        except Exception as exc:  # corrupt/unsupported image
            log.warning("Skipping %s: %s", p, exc)

    n = len(paths)
    uf = UnionFind(n)
    for i in range(n):
        hi = hashes[i]
        for j in range(i + 1, n):
            if hamming(hi, hashes[j]) <= max_hamming:
                uf.union(i, j)

    groups: dict[int, list[Path]] = {}
    for idx, p in enumerate(paths):
        groups.setdefault(uf.find(idx), []).append(p)

    clusters = [sorted(g) for g in groups.values() if len(g) > 1]
    clusters.sort(key=lambda g: (-len(g), g[0]))
    return clusters


if __name__ == "__main__":
    import sys

    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    for k, cluster in enumerate(find_fuzzy_duplicates(directory), 1):
        print(f"Cluster {k} ({len(cluster)} images):")
        for path in cluster:
            print(f"  {path}")