import hashlib

from collections import defaultdict
from pathlib import Path


def find_exact_duplicates(input_dir: str | Path) -> list[list[str]]:
    """Finds exact byte-identical duplicate files in a directory.

    Groups files by SHA-256 checksum, filtering out unique files and returning
    only groups with 2 or more duplicate members sorted alphabetically.
    """
    root = Path(input_dir)
    if not root.is_dir():
        raise ValueError(f"Directory not found: {input_dir}")

    # Step 1: Fast initial grouping by file size
    size_groups = defaultdict(list)
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            try:
                size_groups[path.stat().st_size].append(path)
            except OSError:
                continue

    # Step 2: Hash only files that share the exact same size
    hash_groups = defaultdict(list)
    for size, paths in size_groups.items():
        if len(paths) < 2:
            continue  # Skip unique file sizes

        for path in paths:
            try:
                hasher = hashlib.sha256()
                with open(path, "rb") as f:
                    while chunk := f.read(65536):  # 64 KB chunks
                        hasher.update(chunk)
                hash_groups[hasher.hexdigest()].append(str(path))
            except OSError:
                continue

    # Step 3: Extract and sort groups containing 2+ members
    duplicates = [
        sorted(members)
        for members in hash_groups.values()
        if len(members) >= 2
    ]

    return sorted(duplicates)