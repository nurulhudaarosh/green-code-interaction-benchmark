import hashlib
import os
from collections import defaultdict


def normalize_content(text: str) -> str:
    # Case-fold + collapse any run of whitespace (incl. Unicode whitespace) to a single space.
    return " ".join(text.split()).casefold()


def hash_file(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except (OSError, IOError):
        return None
    normalized = normalize_content(content)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_duplicate_txt_files(root: str) -> list[list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)

    # os.walk is iterative -> safe for arbitrarily deep trees, no recursion limit.
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Prune symlinked directories so we never traverse outside the tree.
        dirnames[:] = [
            d for d in dirnames
            if not os.path.islink(os.path.join(dirpath, d))
        ]

        for name in filenames:
            # Only regular .txt files (case-insensitive extension).
            if not name.lower().endswith(".txt"):
                continue
            full_path = os.path.join(dirpath, name)
            # Skip symlinks and anything that isn't a regular file.
            if os.path.islink(full_path):
                continue
            if not os.path.isfile(full_path):
                continue
            digest = hash_file(full_path)
            if digest is None:
                continue
            groups[digest].append(full_path)

    # Keep only groups with >= 2 files; sort paths and groups deterministically.
    duplicates = [
        sorted(paths)
        for paths in groups.values()
        if len(paths) >= 2
    ]
    duplicates.sort(key=lambda paths: paths[0])
    return duplicates


if __name__ == "__main__":
    import sys

    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    result = find_duplicate_txt_files(root_dir)

    if not result:
        print("No duplicate .txt files found.")
    else:
        for i, group in enumerate(result, 1):
            print(f"Duplicate group {i}:")
            for path in group:
                print(f"  {path}")
            print()