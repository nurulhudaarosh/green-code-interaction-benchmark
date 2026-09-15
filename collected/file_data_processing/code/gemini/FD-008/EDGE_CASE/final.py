import hashlib
import os
import sys
from collections import defaultdict
from pathlib import Path


def is_safe_regular_txt(entry: Path) -> bool:
    """Strictly checks if an entry is a regular file ending in .txt,

    explicitly excluding symlinks (both path and parent directories).
    """
    try:
        # lstat checks the entry itself without following symlinks
        st = entry.lstat()
        if entry.is_symlink():
            return False

        # Must be a regular file
        import stat
        if not stat.S_ISREG(st.st_mode):
            return False

        # Extension check
        return entry.suffix.lower() == ".txt"
    except (OSError, PermissionError):
        return False


def normalize_content(filepath: Path) -> bytes:
    """Safely reads Unicode text with encoding fallback, normalizes unicode,

    case-folds, and collapses whitespace into UTF-8 bytes.
    """
    raw_bytes = None

    # Step 1: Read raw binary safely
    try:
        with open(filepath, "rb") as f:
            raw_bytes = f.read()
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
        return b""

    # Step 2: Decode Unicode handling UTF-8, BOMs, and fallback encodings
    text = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = raw_bytes.decode(encoding)
            break
        except (UnicodeDecodeError, ValueError):
            continue

    if text is None:
        # Fallback to UTF-8 with character replacement if all decoding fails
        text = raw_bytes.decode("utf-8", errors="replace")

    # Step 3: Full Unicode Case-folding + Whitespace normalization
    # split() handles arbitrary Unicode whitespace (spaces, tabs, newlines, non-breaking spaces, etc.)
    normalized_text = " ".join(text.casefold().split())

    return normalized_text.encode("utf-8")


def find_duplicate_txt_files(root_dir: str) -> dict[str, list[str]]:
    """Recursively scans directory tree safely handling deep nesting, symlinks,

    permission errors, and Unicode filenames.
    """
    try:
        root_path = Path(root_dir).resolve(strict=True)
    except (OSError, FileNotFoundError) as e:
        print(f"Error accessing root directory '{root_dir}': {e}", file=sys.stderr)
        return {}

    hash_groups = defaultdict(list)

    # os.walk with followlinks=False prevents symlink loops and traversal into symlinked dirs
    for current_root, dirs, files in os.walk(root_path, followlinks=False):
        # Prune symlinked subdirectories in-place so os.walk never enters them
        dirs[:] = [
            d for d in dirs
            if not os.path.islink(os.path.join(current_root, d))
        ]

        for file_name in files:
            file_path = Path(os.path.join(current_root, file_name))

            if is_safe_regular_txt(file_path):
                normalized_bytes = normalize_content(file_path)

                # Skip completely empty or unreadable files if desired, or hash them
                file_hash = hashlib.sha256(normalized_bytes).hexdigest()

                # Use string conversion of Path for deterministic cross-platform sorting
                hash_groups[file_hash].append(str(file_path))

    # Filter for duplicate groups (count > 1) and sort paths deterministically
    duplicate_groups = {
        h: sorted(paths)
        for h, paths in hash_groups.items()
        if len(paths) > 1
    }

    return duplicate_groups


def report_duplicates(duplicate_groups: dict[str, list[str]]) -> None:
    """Outputs duplicate groups deterministically sorted by hash and path."""
    if not duplicate_groups:
        print("No duplicate text files found.")
        return

    sorted_hashes = sorted(duplicate_groups.keys())
    print(f"Found {len(sorted_hashes)} group(s) of duplicate text files:\n")

    for idx, file_hash in enumerate(sorted_hashes, 1):
        paths = duplicate_groups[file_hash]
        print(f"Group {idx} [SHA-256: {file_hash[:12]}...]")
        for path in paths:
            print(f"  - {path}")
        print()


if __name__ == "__main__":
    # Increase recursion limit just in case deep Path objects/traversals hit system limits
    sys.setrecursionlimit(max(10000, sys.getrecursionlimit()))

    target_directory = sys.argv[1] if len(sys.argv) > 1 else "."
    duplicates = find_duplicate_txt_files(target_directory)
    report_duplicates(duplicates)