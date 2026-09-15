from pathlib import Path
import hashlib
import sys

def normalize_text(path: Path) -> str:
    """Read a text file, case-fold, and normalize whitespace."""
    content = path.read_text(encoding="utf-8", errors="ignore")
    content = content.casefold()
    return " ".join(content.split())

def find_duplicate_txt_files(root_dir: str | Path) -> dict[str, list[str]]:
    """
    Recursively inspect regular .txt files, ignoring symlinks and non-.txt files.
    Returns a deterministic dictionary mapping SHA-256 hashes to sorted lists
    of duplicate file paths (only for hashes with >1 file).
    """
    root = Path(root_dir).resolve()
    hash_map: dict[str, list[str]] = {}

    # Recursively find regular files with a .txt extension, ignoring symlinks
    txt_files = [
        p for p in root.rglob("*.txt")
        if p.is_file() and not p.is_symlink()
    ]

    # Process files in deterministic (sorted) order
    for file_path in sorted(txt_files):
        try:
            normalized_content = normalize_text(file_path)
            content_hash = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
            
            if content_hash not in hash_map:
                hash_map[content_hash] = []
            hash_map[content_hash].append(str(file_path))
        except Exception as e:
            print(f"Skipping file due to read error '{file_path}': {e}", file=sys.stderr)

    # Filter to groups with duplicates and sort groups by hash for deterministic output
    duplicates = {
        h: hash_map[h]
        for h in sorted(hash_map.keys())
        if len(hash_map[h]) > 1
    }

    return duplicates

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Find duplicate .txt files based on normalized content.")
    parser.add_argument("directory", nargs="?", default=".", help="Root directory to search (default: current directory)")
    args = parser.parse_args()

    results = find_duplicate_txt_files(args.directory)

    if not results:
        print("No duplicate .txt files found.")
    else:
        print(f"Found {len(results)} group(s) of duplicates:\n")
        for group_idx, (file_hash, file_paths) in enumerate(results.items(), start=1):
            print(f"Group {group_idx} [SHA-256: {file_hash}]:")
            for path in file_paths:
                print(f"  - {path}")
            print()