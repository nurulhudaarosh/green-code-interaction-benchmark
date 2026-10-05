import hashlib
from collections import defaultdict
from pathlib import Path


def find_exact_duplicates(input_dir, recursive=False):
    """Return {sha256_hex: [sorted file paths]} for byte-identical files.

    Only groups with 2+ files are included.

    If recursive is True, subdirectories are searched too, and files are
    reported as paths relative to input_dir. Otherwise only files directly
    inside input_dir are considered, reported as input_dir/name.
    """
    root = Path(input_dir)
    candidates = root.rglob("*") if recursive else root.iterdir()
    groups = defaultdict(list)

    for path in candidates:
        if path.is_symlink() or not path.is_file():
            continue
        try:
            digest = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):  # 1 MiB chunks
                    digest.update(chunk)
        except OSError:
            continue  # unreadable file (permissions, race with deletion, etc.)

        reported = path.relative_to(root) if recursive else path
        groups[digest.hexdigest()].append(str(reported))

    return {h: sorted(paths) for h, paths in groups.items() if len(paths) > 1}