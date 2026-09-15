from collections import defaultdict
import hashlib
import os
from pathlib import Path


def normalize_content(content: str) -> str:
    """Case-folds and normalizes whitespace in the text content."""
    return " ".join(content.casefold().split())


def find_duplicate_txt_files(root_dir: str | Path) -> dict[str, list[str]]:
    """Recursively finds duplicate regular .txt files based on normalized SHA-256 hash.

    Ignores symlinks and non-.txt extensions.
    Returns deterministic, sorted duplicate groups.
    """
    hashes = defaultdict(list)
    root_path = Path(root_dir).resolve()

    # Collect and sort paths to guarantee deterministic traversal order
    all_paths = sorted(root_path.rglob("*.txt"))

    for path in all_paths:
        # Strict filter: regular file, non-symlink, strictly ending in .txt
        if not path.is_file() or path.is_symlink() or path.suffix.lower() != ".txt":
            continue

        try:
            # Read text with basic UTF-8 handling and fallback replacement
            content = path.read_text(encoding="utf-8", errors="replace")
            normalized = normalize_content(content)
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

            hashes[digest].append(str(path))
        except (PermissionError, OSError):
            continue

    # Filter for duplicate groups (hash with > 1 file) and sort deterministically
    duplicates = {
        digest: sorted(paths)
        for digest, paths in sorted(hashes.items())
        if len(paths) > 1
    }

    return duplicates


if __name__ == "__main__":
    import sys

    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    dup_groups = find_duplicate_txt_files(target_dir)

    if not dup_groups:
        print("No duplicate .txt files found.")
    else:
        print(f"Found {len(dup_groups)} duplicate group(s):\n")
        for idx, (digest, files) in enumerate(dup_groups.items(), start=1):
            print(f"Group {idx} [SHA-256: {digest[:12]}...]:")
            for filepath in files:
                print(f"  - {filepath}")
            print()