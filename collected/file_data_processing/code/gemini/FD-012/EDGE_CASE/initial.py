import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path


def analyze_text_files(directory_path: str):
    """Recursively processes .txt files in a directory to analyze word frequencies.

    - Case-folds words to lower case.
    - Extracts purely alphabetic words.
    - Counts total occurrences and document frequency per word.
    - Orders results deterministically:
        1. Total occurrences (descending)
        2. Document frequency (descending)
        3. Word (alphabetical ascending)
    """
    root_dir = Path(directory_path)

    if not root_dir.exists() or not root_dir.is_dir():
        print(f"Error: Directory '{directory_path}' does not exist or is not a directory.")
        return

    total_counts = Counter()
    doc_counts = Counter()
    processed_files = 0

    # Pattern matching purely alphabetic words
    word_pattern = re.compile(r"\b[a-zA-Z]+\b")

    for file_path in root_dir.rglob("*.txt"):
        try:
            # Fallback handling for common text encodings
            content = None
            for encoding in ("utf-8", "latin-1", "cp1252"):
                try:
                    content = file_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                print(f"Skipping unreadable file: {file_path}")
                continue

            # Extract and case-fold words
            words = word_pattern.findall(content.lower())

            # Update total frequency count across all files
            total_counts.update(words)

            # Update document frequency (unique words in current file)
            doc_counts.update(set(words))

            processed_files += 1

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    if processed_files == 0:
        print(f"No valid .txt files found in '{directory_path}'.")
        return

    # Deterministic Sorting:
    # Key 1: Total occurrences (-total_counts[word] for descending)
    # Key 2: Document frequency (-doc_counts[word] for descending)
    # Key 3: Word string (word for ascending alphabetical order)
    unique_words = sorted(
        total_counts.keys(),
        key=lambda w: (-total_counts[w], -doc_counts[w], w)
    )

    # Print Summary & Results Table
    print(f"Processed {processed_files} file(s).\n")
    print(f"{'Rank':<6} {'Word':<20} {'Total Count':<12} {'Doc Frequency':<12}")
    print("-" * 52)

    for rank, word in enumerate(unique_words, start=1):
        print(
            f"{rank:<6} {word:<20} {total_counts[word]:<12} {doc_counts[word]:<12}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Recursively analyze text files and rank word frequencies."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Path to directory containing .txt files (default: current directory)"
    )
    args = parser.parse_args()

    analyze_text_files(args.directory)