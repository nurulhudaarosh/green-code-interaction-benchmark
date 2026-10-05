import os
import re
from collections import Counter, defaultdict
from pathlib import Path


def analyze_text_files(directory_path: str):
    """Recursively analyzes all .txt files in directory_path.

    Term Frequency (TF): Counts every occurrence of a word across all documents.
    Document Frequency (DF): Counts the number of unique documents containing
    the word (multiple occurrences within the same document contribute 1 to
    DF).

    Returns:
        total_files (int): Total number of .txt files processed.
        ranked_stats (list): List of tuples (word, total_freq, doc_freq) sorted
        deterministically.
    """
    total_tf = Counter()
    doc_freq = defaultdict(set)
    total_files = 0

    # Match alphabetic words
    word_pattern = re.compile(r"[a-zA-Z]+")

    root_dir = Path(directory_path)

    if not root_dir.exists() or not root_dir.is_dir():
        raise ValueError(
            f"Directory path '{directory_path}' does not exist or is not a directory."
        )

    # Recursively traverse directory for .txt files
    for file_path in root_dir.rglob("*.txt"):
        if not file_path.is_file():
            continue

        total_files += 1

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Extract words and case-fold
            words = [
                w.casefold() for w in word_pattern.findall(content)
            ]

            # 1. Add all occurrences to total term frequency
            total_tf.update(words)

            # 2. Add document path to set for unique words in this file (deduplicated per doc)
            unique_words_in_doc = set(words)
            for word in unique_words_in_doc:
                doc_freq[word].add(file_path)

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

    # Compile word stats: (word, total_frequency, document_frequency)
    # len(doc_freq[word]) ensures each document contributes at most 1 to DF
    word_stats = [
        (word, count, len(doc_freq[word])) for word, count in total_tf.items()
    ]

    # Deterministic tie-breaking order:
    # 1. Total Frequency (descending -> -stat[1])
    # 2. Document Frequency (descending -> -stat[2])
    # 3. Alphabetical order (ascending -> stat[0])
    ranked_stats = sorted(word_stats, key=lambda x: (-x[1], -x[2], x[0]))

    return total_files, ranked_stats


def main():
    import sys

    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    print(f"Scanning directory recursively: {os.path.abspath(target_dir)}\n")

    try:
        total_files, results = analyze_text_files(target_dir)

        print(f"Processed {total_files} .txt file(s).")
        print(f"Total unique alphabetic words found: {len(results)}\n")

        if not results:
            print("No text data found.")
            return

        print(f"{'WORD':<20} | {'TOTAL FREQ':<12} | {'DOC FREQ':<10}")
        print("-" * 48)

        for word, tf, df in results[:20]:
            print(f"{word:<20} | {tf:<12} | {df:<10}")

        if len(results) > 20:
            print(f"\n... and {len(results) - 20} more terms.")

    except Exception as err:
        print(f"Error: {err}")


if __name__ == "__main__":
    main()