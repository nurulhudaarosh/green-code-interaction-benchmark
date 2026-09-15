import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence


def normalize_content(content: str) -> str:
    """Case-fold and normalize all whitespace (collapses runs of whitespace to a single space)."""
    return re.sub(r"\s+", " ", content.casefold()).strip()


def compute_normalized_hash(file_path: Path) -> str:
    """Read a .txt file, normalize its text content, and return its SHA-256 hex digest."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    normalized_text = normalize_content(text)
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def find_duplicate_txt_files(root_dir: str | Path) -> List[List[Path]]:
    """Recursively search root_dir for regular .txt files and group duplicates.

    Ignores symlinks, non-.txt extensions, and directories.
    Returns a deterministically sorted list of duplicate groups (paths sorted within groups).
    """
    root = Path(root_dir).resolve()
    hash_groups: Dict[str, List[Path]] = defaultdict(list)

    # Collect and sort paths up front for deterministic traversal order
    all_paths = sorted(root.rglob("*"))

    for path in all_paths:
        # Strict check: must be a regular file (not a symlink), with exact .txt extension
        if path.is_file() and not path.is_symlink() and path.suffix.lower() == ".txt":
            try:
                content_hash = compute_normalized_hash(path)
                hash_groups[content_hash].append(path)
            except (PermissionError, OSError):
                # Skip files that cannot be accessed or read
                continue

    # Filter out non-duplicates (groups with size > 1) and sort deterministically
    duplicates = [
        sorted(paths) for paths in hash_groups.values() if len(paths) > 1
    ]

    # Sort groups by the path string of their first element for stable output ordering
    return sorted(duplicates, key=lambda group: group[0])


def report_duplicates(duplicate_groups: List[List[Path]]) -> None:
    """Print the formatted list of duplicate groups."""
    if not duplicate_groups:
        print("No duplicate .txt files found.")
        return

    print(f"Found {len(duplicate_groups)} duplicate group(s):\n")
    for group_idx, group in enumerate(duplicate_groups, start=1):
        print(f"Group {group_idx}:")
        for file_path in group:
            print(f"  - {file_path}")
        print()


if __name__ == "__main__":
    import sys

    target_directory = sys.argv[1] if len(sys.argv) > 1 else "."
    results = find_duplicate_txt_files(target_directory)
    report_duplicates(results)