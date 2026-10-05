import hashlib
from collections import defaultdict
from pathlib import Path


def find_exact_duplicates(
    input_dir: str | Path, recursive: bool = True
) -> list[list[str]]:
    """Finds exact byte-identical duplicate files in a directory.

    Args:
        input_dir: The root directory to search.
        recursive: If True, recursively walks subdirectories. If False, checks
          only top-level files. Defaults to True.

    Returns:
        A list of duplicate file groups (each with 2+ files), where each group
        contains file paths relative to `input_dir`, sorted alphabetically.
    """
    root = Path(input_dir)
    if not root.is_dir():
        raise ValueError(f"Directory not found: {input_dir}")

    # Step 1: Collect files based on the recursive flag
    entries = root.rglob("*") if recursive else root.glob("*")

    # Step 2: Group candidate files by size
    size_groups = defaultdict(list)
    for path in entries:
        if path.is_file() and not path.is_symlink():
            try:
                size_groups[path.stat().st_size].append(path)
            except OSError:
                continue

    # Step 3: Hash only files that share the exact same size
    hash_groups = defaultdict(list)
    for paths in size_groups.values():
        if len(paths) < 2:
            continue

        for path in paths:
            try:
                hasher = hashlib.sha256()
                with open(path, "rb") as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)

                # Store relative path string
                rel_path = str(path.relative_to(root))
                hash_groups[hasher.hexdigest()].append(rel_path)
            except OSError:
                continue

    # Step 4: Extract and sort groups with 2+ members
    duplicates = [
        sorted(members)
        for members in hash_groups.values()
        if len(members) >= 2
    ]

    return sorted(duplicates)