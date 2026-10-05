import argparse
import collections
import os
import re
from typing import Dict, List, Tuple


def analyze_text_directory(
    root_dir: str, top_n: int = 20, encoding: str = "utf-8"
) -> Tuple[
    List[Tuple[str, int, int]], Dict[str, int], Dict[str, int], int, int
]:
    """Recursively processes .txt files in root_dir.

    Returns:
        ranked_words: List of tuples (word, total_count, doc_frequency)
        word_counts: Dict mapping word to total occurrence count
        doc_counts: Dict mapping word to document frequency count
        total_files: Number of .txt files processed
        total_words: Total count of alphabetic word occurrences found
    """
    word_counts = collections.Counter()
    doc_counts = collections.Counter()
    total_files = 0
    total_words = 0

    # Pattern matches sequences of alphabetic characters
    word_pattern = re.compile(r"[a-zA-Z]+")

    for current_root, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(".txt"):
                file_path = os.path.join(current_root, filename)
                total_files += 1

                try:
                    with open(
                        file_path, "r", encoding=encoding, errors="ignore"
                    ) as f:
                        content = f.read()
                except Exception as e:
                    print(f"Warning: Could not read file {file_path}: {e}")
                    continue

                # Case-fold and extract alphabetic words
                words = [
                    match.group(0).casefold()
                    for match in word_pattern.finditer(content)
                ]

                total_words += len(words)
                word_counts.update(words)

                # Set of unique words in the current document for document frequency
                unique_words = set(words)
                doc_counts.update(unique_words)

    # Deterministic Ranking Order:
    # 1. Primary sort: Document Frequency (descending)
    # 2. Secondary sort: Total Frequency (descending)
    # 3. Tertiary sort: Word lexicographically (ascending)
    ranked_words = sorted(
        [
            (word, word_counts[word], doc_counts[word])
            for word in word_counts
        ],
        key=lambda item: (-item[2], -item[1], item[0]),
    )

    if top_n > 0:
        ranked_words = ranked_words[:top_n]

    return ranked_words, word_counts, doc_counts, total_files, total_words


def print_report(
    ranked_words: List[Tuple[str, int, int]],
    total_files: int,
    total_words: int,
    unique_words: int,
) -> None:
    """Formats and prints summary report."""
    print("=" * 60)
    print("TEXT ANALYSIS REPORT")
    print("=" * 60)
    print(f"Total .txt files processed : {total_files}")
    print(f"Total alphabetic words     : {total_words}")
    print(f"Total unique words         : {unique_words}")
    print("-" * 60)
    print(f"{'Rank':<6}{'Word':<20}{'Doc Frequency':<15}{'Total Count':<15}")
    print("-" * 60)

    for rank, (word, count, doc_freq) in enumerate(ranked_words, start=1):
        print(f"{rank:<6}{word:<20}{doc_freq:<15}{count:<15}")

    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Recursively analyze text files in a directory."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory)",
    )
    parser.add_argument(
        "-n",
        "--top",
        type=int,
        default=20,
        help="Number of top words to display (default: 20)",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist.")
    else:
        ranked, word_counts, doc_counts, total_files, total_words = (
            analyze_text_directory(args.directory, top_n=args.top)
        )
        print_report(
            ranked,
            total_files=total_files,
            total_words=total_words,
            unique_words=len(word_counts),
        )