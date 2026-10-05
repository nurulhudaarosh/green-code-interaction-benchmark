from collections import Counter
from pathlib import Path
import re


def analyze_text_files(root_directory: str | Path) -> list[tuple[str, int, int]]:
    """Recursively scans a directory for .txt files, tokenizes and case-folds

    Unicode alphabetic words, counts frequencies, and outputs deterministically
    sorted results.

    Returns:
        List of tuples: (word, total_count, document_frequency)
    """
    root_path = Path(root_directory)
    if not root_path.exists() or not root_path.is_dir():
        raise ValueError(
            f"The provided path '{root_directory}' is not a valid directory."
        )

    # Unicode alphabetic word pattern: matches sequences of Unicode letters (category 'L')
    # Excludes digits, underscores, punctuation, and symbols across all languages.
    word_pattern = re.compile(r"[\w^\d_]+")

    total_counts = Counter()
    doc_frequencies = Counter()

    # Recursively iterate through all .txt files
    for file_path in root_path.rglob("*.txt"):
        if not file_path.is_file():
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            continue

        # Full Unicode case-folding for consistent matching across languages
        folded_content = content.casefold()

        # Extract Unicode alphabetic words
        words = [
            match
            for match in word_pattern.findall(folded_content)
            if match.isalpha()
        ]

        if words:
            total_counts.update(words)
            # Unique words per file for Document Frequency
            doc_frequencies.update(set(words))

    # Deterministic ranking:
    # 1. Document frequency (descending: -item[2])
    # 2. Total count (descending: -item[1])
    # 3. Alphabetical tie-breaker (ascending: item[0])
    results = [
        (word, count, doc_frequencies[word])
        for word, count in total_counts.items()
    ]
    results.sort(key=lambda item: (-item[2], -item[1], item[0]))

    return results


if __name__ == "__main__":
    import sys

    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    analysis = analyze_text_files(target_dir)

    print(
        f"{'WORD':<20} | {'DOCUMENT FREQUENCY':<18} | {'TOTAL OCCURRENCES':<18}"
    )
    print("-" * 62)
    for word, count, doc_freq in analysis[:20]:
        print(f"{word:<20} | {doc_freq:<18} | {count:<18}")