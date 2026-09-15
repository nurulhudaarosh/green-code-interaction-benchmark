import os
import re
import hashlib
from collections import defaultdict

def normalize_text(text):
    return re.sub(r"\s+", " ", text.casefold()).strip()

def find_duplicates(root_folder):
    groups = defaultdict(list)

    for current_root, dirs, files in os.walk(root_folder):
        dirs[:] = [
            d for d in dirs
            if not os.path.islink(os.path.join(current_root, d))
        ]

        for filename in files:
            path = os.path.join(current_root, filename)

            if not filename.lower().endswith(".txt"):
                continue

            if os.path.islink(path) or not os.path.isfile(path):
                continue

            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
            except (OSError, UnicodeError):
                continue

            normalized = normalize_text(content)
            file_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

            groups[file_hash].append(os.path.abspath(path))

    duplicates = [
        sorted(paths)
        for paths in groups.values()
        if len(paths) > 1
    ]

    duplicates.sort(key=lambda group: group[0])
    return duplicates

if __name__ == "__main__":
    root_folder = input("Enter folder path: ").strip()

    duplicate_groups = find_duplicates(root_folder)

    if not duplicate_groups:
        print("No duplicate text files found.")
    else:
        for index, group in enumerate(duplicate_groups, 1):
            print(f"Duplicate group {index}:")
            for path in group:
                print(path)
            print()