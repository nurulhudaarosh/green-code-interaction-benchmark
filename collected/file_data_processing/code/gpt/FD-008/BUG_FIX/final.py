import os
import re
import hashlib

def normalize_text(text):
    text = text.casefold()
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def find_duplicates(root):
    hashes = {}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames
            if not os.path.islink(os.path.join(dirpath, d))
        )

        for filename in sorted(filenames):
            path = os.path.join(dirpath, filename)

            if os.path.islink(path):
                continue

            if not filename.lower().endswith(".txt"):
                continue

            if not os.path.isfile(path):
                continue

            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
            except (OSError, UnicodeError):
                continue

            normalized_text = normalize_text(content)
            file_hash = hashlib.sha256(
                normalized_text.encode("utf-8")
            ).hexdigest()

            hashes.setdefault(file_hash, []).append(
                os.path.abspath(path)
            )

    duplicates = [
        sorted(paths)
        for paths in hashes.values()
        if len(paths) > 1
    ]

    duplicates.sort(key=lambda group: group[0])
    return duplicates

def main():
    root = input("Enter directory: ").strip()

    if not os.path.isdir(root):
        print("Invalid directory.")
        return

    groups = find_duplicates(root)

    if not groups:
        print("No duplicate groups found.")
        return

    for number, group in enumerate(groups, 1):
        print(f"Duplicate group {number}:")
        for path in group:
            print(path)
        print()

if __name__ == "__main__":
    main()