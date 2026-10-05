from pathlib import Path
from typing import Dict, List, Set, Tuple, Union, overload
from PIL import Image

class UnionFind:
    """Disjoint Set Union (DSU) structure with path compression and rank optimization."""

    def __init__(self):
        self.parent: Dict[Path, Path] = {}
        self.rank: Dict[Path, int] = {}

    def add(self, item: Path) -> None:
        if item not in self.parent:
            self.parent[item] = item
            self.rank[item] = 0

    def find(self, item: Path) -> Path:
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])  # Path compression
        return self.parent[item]

    def union(self, item1: Path, item2: Path) -> None:
        root1 = self.find(item1)
        root2 = self.find(item2)

        if root1 != root2:
            # Union by rank
            if self.rank[root1] < self.rank[root2]:
                root1, root2 = root2, root1
            self.parent[root2] = root1
            if self.rank[root1] == self.rank[root2]:
                self.rank[root1] += 1


def compute_average_hash(image_path: Path, hash_size: int = 8) -> int:
    """Computes average hash (aHash) as an integer bitmask."""
    with Image.open(image_path) as img:
        img = img.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())

    avg = sum(pixels) / len(pixels)

    hash_val = 0
    for pixel in pixels:
        hash_val = (hash_val << 1) | (1 if pixel >= avg else 0)

    return hash_val


def hamming_distance(hash1: int, hash2: int) -> int:
    """Computes bitwise Hamming distance between two integer hashes."""
    return bin(hash1 ^ hash2).count("1")


# Overload type signatures for precise IDE autocomplete
@overload
def find_fuzzy_duplicates(
    input_dir: str | Path,
    hash_size: int = 8,
    max_hamming: int = 5,
    valid_extensions: Set[str] = ...,
    return_hashes: Literal[False] = False,
) -> List[List[Path]]: ...

@overload
def find_fuzzy_duplicates(
    input_dir: str | Path,
    hash_size: int = 8,
    max_hamming: int = 5,
    valid_extensions: Set[str] = ...,
    return_hashes: Literal[True] = True,
) -> Tuple[List[List[Path]], Dict[Path, int]]: ...


def find_fuzzy_duplicates(
    input_dir: str | Path,
    hash_size: int = 8,
    max_hamming: int = 5,
    valid_extensions: Set[str] = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"},
    return_hashes: bool = False,
) -> Union[List[List[Path]], Tuple[List[List[Path]], Dict[Path, int]]]:
    """
    Finds fuzzy duplicate images using Average Hash and groups them transitively.

    Parameters:
      input_dir: Directory containing images to scan.
      hash_size: Dimensions for aHash resizing (default 8 yields 64-bit hash).
      max_hamming: Maximum Hamming distance to consider images as duplicates.
      valid_extensions: Set of allowed image extensions.
      return_hashes: If True, returns tuple of (clusters, hash_map).

    Returns:
      Either a list of clusters or a tuple of (clusters, hash_map).
    """
    directory = Path(input_dir)
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"Invalid directory path: {input_dir}")

    hashes: Dict[Path, int] = {}
    uf = UnionFind()

    # Step 1: Discover images and compute hashes
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in valid_extensions:
            try:
                hashes[path] = compute_average_hash(path, hash_size=hash_size)
                uf.add(path)
            except Exception as e:
                print(f"Skipping corrupt or unreadable image {path}: {e}")

    paths = list(hashes.keys())

    # Step 2: Compare pairs and merge components in Union-Find
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            p1, p2 = paths[i], paths[j]
            if hamming_distance(hashes[p1], hashes[p2]) <= max_hamming:
                uf.union(p1, p2)

    # Step 3: Aggregate paths by root parent
    clusters: Dict[Path, List[Path]] = {}
    for path in paths:
        root = uf.find(path)
        clusters.setdefault(root, []).append(path)

    duplicate_groups = [group for group in clusters.values() if len(group) > 1]

    if return_hashes:
        return duplicate_groups, hashes
    return duplicate_groups