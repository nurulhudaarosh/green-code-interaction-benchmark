import os
import hashlib
from collections import defaultdict


def find_exact_duplicates(input_dir):
    """Group byte-identical files using their full SHA-256 checksum."""
    groups = defaultdict(list)

    for filename in os.listdir(input_dir):
        filepath = os.path.join(input_dir, filename)

        if os.path.isfile(filepath):
            sha256 = hashlib.sha256()

            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)

            groups[sha256.hexdigest()].append(filename)

    return [
        sorted(files)
        for files in groups.values()
        if len(files) >= 2
    ]