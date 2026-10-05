import hashlib
from pathlib import Path

def find_exact_duplicates(input_dir):
    groups = {}

    for path in Path(input_dir).rglob("*"):
        if path.is_file():
            sha256 = hashlib.sha256()

            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    sha256.update(chunk)

            groups.setdefault(sha256.hexdigest(), []).append(str(path))

    # Keep only groups with 2+ identical files and sort each group alphabetically
    return [sorted(files) for files in groups.values() if len(files) >= 2]