import os
import re
import sys
import csv
from collections import Counter


def analyze_text_files(root_dir, output_file):
    word_counts = Counter()
    document_frequency = Counter()

    for current_root, dirs, files in os.walk(root_dir):
        dirs.sort()
        files.sort()

        for filename in files:
            if not filename.lower().endswith(".txt"):
                continue

            path = os.path.join(current_root, filename)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except (OSError, UnicodeError):
                continue

            words = re.findall(r"[^\W\d_]+", text, flags=re.UNICODE)
            words = [word.casefold() for word in words]

            if not words:
                continue

            word_counts.update(words)

            for word in set(words):
                document_frequency[word] += 1

    rows = []

    for word in word_counts:
        rows.append([
            word,
            word_counts[word],
            document_frequency[word]
        ])

    rows.sort(key=lambda row: (-row[1], -row[2], row[0]))

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "total_occurrences", "document_frequency"])
        writer.writerows(rows)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyzer.py <input_directory> <output_csv>")
        sys.exit(1)

    analyze_text_files(sys.argv[1], sys.argv[2])