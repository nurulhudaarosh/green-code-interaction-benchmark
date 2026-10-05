import sys
import re
from pathlib import Path
from collections import Counter, defaultdict


def analyze_texts(root_directory):
    total_frequency = Counter()
    document_frequency = defaultdict(int)

    root = Path(root_directory)

    for file_path in sorted(root.rglob("*.txt")):
        if not file_path.is_file():
            continue

        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue

        words = re.findall(r"[^\W\d_]+", text.casefold())

        if not words:
            continue

        total_frequency.update(words)

        for word in set(words):
            document_frequency[word] += 1

    words = sorted(
        total_frequency.keys(),
        key=lambda word: (
            -document_frequency[word],
            -total_frequency[word],
            word
        )
    )

    return [
        (word, total_frequency[word], document_frequency[word])
        for word in words
    ]


def main():
    if len(sys.argv) != 2:
        print("Usage: python analyzer.py <directory>")
        return

    results = analyze_texts(sys.argv[1])

    print("word,total_frequency,document_frequency")

    for word, total, document in results:
        print(f"{word},{total},{document}")


if __name__ == "__main__":
    main()