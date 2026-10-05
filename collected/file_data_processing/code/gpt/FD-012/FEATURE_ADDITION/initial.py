import sys
import re
from pathlib import Path
from collections import Counter


def analyze_texts(root):
    total_frequency = Counter()
    document_frequency = Counter()

    files = sorted(
        path for path in Path(root).rglob("*.txt")
        if path.is_file() and not path.is_symlink()
    )

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue

        words = re.findall(r"[^\W\d_]+", text.casefold())

        if not words:
            continue

        total_frequency.update(words)
        document_frequency.update(set(words))

    ranked = sorted(
        total_frequency,
        key=lambda word: (
            -total_frequency[word],
            -document_frequency[word],
            word
        )
    )

    return [
        {
            "word": word,
            "total_frequency": total_frequency[word],
            "document_frequency": document_frequency[word]
        }
        for word in ranked
    ]


def main():
    if len(sys.argv) != 2:
        print("Usage: python analyzer.py <directory>")
        return

    results = analyze_texts(sys.argv[1])

    for item in results:
        print(
            f"{item['word']}\t"
            f"{item['total_frequency']}\t"
            f"{item['document_frequency']}"
        )


if __name__ == "__main__":
    main()