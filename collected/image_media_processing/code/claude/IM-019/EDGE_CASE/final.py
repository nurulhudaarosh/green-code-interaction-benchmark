"""Find near-duplicate images using average hashing and union-find clustering."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


def _average_hash(path: Path, hash_size: int) -> int:
    """Return a hash_size*hash_size-bit average hash of the image as an int."""
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        img = img.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())
    mean = sum(pixels) / len(pixels)
    bits = 0
    for p in pixels:
        bits = (bits << 1) | (1 if p > mean else 0)
    return bits


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path halving
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def find_fuzzy_duplicates(
    input_dir: str | Path,
    hash_size: int = 8,
    max_hamming: int = 5,
) -> list[list[Path]]:
    """Cluster visually similar images in ``input_dir`` (searched recursively).

    Each image gets an average hash (grayscale, downscaled to
    ``hash_size`` x ``hash_size``, thresholded at the mean). Two images are
    linked if their hashes differ in at most ``max_hamming`` bits. Links are
    transitive: if A~B and B~C, then A, B and C land in one cluster even if
    A and C are further apart than ``max_hamming``.

    Returns a list of clusters, each a sorted list of paths with at least two
    members. Clusters are sorted by size (largest first), then by first path.
    Unreadable images are skipped with a warning.
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
            hashes.append(_average_hash(p, hash_size))
            paths.append(p)
        except Exception as exc:  # corrupt or unsupported image
            logger.warning("Skipping %s: %s", p, exc)

    n = len(paths)
    if n < 2:
        # Zero or one valid image: nothing to compare, so no clusters.
        return []

    uf = _UnionFind(n)
    for i in range(n):
        for j in range(i + 1, n):
            if _hamming(hashes[i], hashes[j]) <= max_hamming:
                uf.union(i, j)

    groups: dict[int, list[Path]] = {}
    for i, p in enumerate(paths):
        groups.setdefault(uf.find(i), []).append(p)

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