import os
import hashlib
from collections import defaultdict

def normalize_text(text):
    return " ".join(text.casefold().split())

def find_duplicate_text_files(root_dir):
    groups = defaultdict(list)

    for root, dirs, files in os.walk(root_dir, followlinks=False):
        dirs[:] = [
            d for d in dirs
            if not os.path.islink(os.path.join(root, d))
        ]

        for filename in files:
            path = os.path.join(root, filename)

            if not filename.casefold().endswith(".txt"):
                continue

            if os.path.islink(path) or not os.path.isfile(path):
                continue

            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
            except (OSError, UnicodeError):
                continue

            normalized = normalize_text(content)
            file_hash = hashlib.sha256(
                normalized.encode("utf-8")
            ).hexdigest()

            groups[file_hash].append(os.path.abspath(path))

    duplicates = []

    for file_hash, paths in groups.items():
        if len(paths) > 1:
            paths.sort()
            duplicates.append((file_hash, paths))

    duplicates.sort(key=lambda group: group[1][0])

    return duplicates

def main():
    root_dir = "."

    duplicates = find_duplicate_text_files(root_dir)

    for index, (file_hash, paths) in enumerate(duplicates, 1):
        print(f"Group {index}:")
        print(f"SHA-256: {file_hash}")
        for path in paths:
            print(path)
        print()

if __name__ == "__main__":
    main()