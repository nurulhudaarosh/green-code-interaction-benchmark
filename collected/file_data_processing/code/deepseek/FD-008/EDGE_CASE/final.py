import hashlib
import os
import re
import sys
import unicodedata
from collections import defaultdict

# Cap file size to avoid blowing up memory on huge non-text files that
# happen to be named .txt. Adjust as needed.
MAX_FILE_BYTES = 64 * 1024 * 1024  # 64 MiB


def normalize_text(text: str) -> str:
    """
    Normalize text for duplicate comparison:
      - Unicode NFKC normalization (canonical-ish, collapses compatibility forms)
      - Case-fold (Unicode-aware)
      - Collapse all Unicode whitespace runs to a single ASCII space, then strip
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()
    # \s in Python's re matches Unicode whitespace by default for str patterns.
    text = re.sub(r"\s+", " ", text).strip()
    return text


def content_hash(path: str) -> str:
    """Read a text file safely and return SHA-256 hex digest of normalized content."""
    with open(path, "rb") as fb:
        data = fb.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(
            f"File too large (> {MAX_FILE_BYTES} bytes): {path}"
        )

    # Decode defensively: BOM handling + invalid byte replacement.
    if data.startswith(b"\xef\xbb\xbf"):          # UTF-8 BOM
        text = data[3:].decode("utf-8", errors="replace")
    elif data.startswith(b"\xff\xfe\x00\x00"):    # UTF-32 LE BOM
        text = data[4:].decode("utf-32-le", errors="replace")
    elif data.startswith(b"\x00\x00\xfe\xff"):    # UTF-32 BE BOM
        text = data[4:].decode("utf-32-be", errors="replace")
    elif data.startswith(b"\xff\xfe"):            # UTF-16 LE BOM
        text = data[2:].decode("utf-16-le", errors="replace")
    elif data.startswith(b"\xfe\xff"):            # UTF-16 BE BOM
        text = data[2:].decode("utf-16-be", errors="replace")
    else:
        text = data.decode("utf-8", errors="replace")

    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _safe_stat(path: str):
    """Return os.stat_result without following symlinks, or None on error."""
    try:
        return os.stat(path, follow_symlinks=False)
    except OSError:
        return None


def find_duplicates(root: str) -> dict:
    """
    Recursively inspect regular .txt files under `root`.

    Safety properties:
      - Never follows symlinks (neither file nor directory symlinks).
      - Skips anything that is not a regular file (after lstat).
      - Skips hardlinked directories / weird special files.
      - Handles Unicode filenames and Unicode content.
      - Ignores non-.txt extensions (case-insensitive).
      - Handles deep nesting via os.walk + iterative pruning (no recursion).
      - Catches per-file errors so one bad file can't abort the scan.
    """
    groups = defaultdict(list)

    # os.walk is iterative, so deep nesting won't blow the Python stack.
    # followlinks=False prevents descending into symlinked dirs.
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Prune symlinked directories and any non-directory entries that
        # somehow appear (defensive; os.walk usually filters these).
        pruned = []
        for d in dirnames:
            full_d = os.path.join(dirpath, d)
            st = _safe_stat(full_d)
            if st is None:
                continue
            # Skip symlinks (os.path.islink is redundant with lstat mode,
            # but keeps intent explicit) and non-directories.
            if os.path.islink(full_d):
                continue
            if not os.path.isdir(full_d):
                continue
            pruned.append(d)
        dirnames[:] = pruned

        for name in filenames:
            # Case-insensitive .txt check on the basename.
            if not name.lower().endswith(".txt"):
                continue

            full = os.path.join(dirpath, name)
            st = _safe_stat(full)
            if st is None:
                continue

            # Skip symlinks explicitly.
            if os.path.islink(full):
                continue
            # Only regular files (skip fifos, sockets, devices, etc.).
            if not os.path.isfile(full):
                continue

            try:
                digest = content_hash(full)
            except (OSError, ValueError) as e:
                print(f"Warning: skipping {full!r}: {e}", file=sys.stderr)
                continue

            groups[digest].append(full)

    # Keep only true duplicate groups, with deterministically sorted members.
    result = {}
    for h, paths in groups.items():
        if len(paths) > 1:
            result[h] = sorted(paths, key=lambda p: (p.casefold(), p))
    return result


def main():
    if len(sys.argv) != 2:
        print("Usage: python dup_txt_finder.py <directory>", file=sys.stderr)
        sys.exit(1)

    root = sys.argv[1]
    if not os.path.isdir(root):
        print(f"Error: {root} is not a directory", file=sys.stderr)
        sys.exit(1)

    duplicates = find_duplicates(root)

    if not duplicates:
        print("No duplicate .txt files found.")
        return

    # Deterministic ordering of groups: by their canonical (first) path.
    ordered = sorted(
        duplicates.values(),
        key=lambda paths: (paths[0].casefold(), paths[0]),
    )

    for i, paths in enumerate(ordered, 1):
        print(f"Duplicate group {i}:")
        for p in paths:
            print(f"  {p}")
        print()


if __name__ == "__main__":
    main()