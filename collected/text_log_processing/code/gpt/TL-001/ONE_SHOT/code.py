import re
from collections import Counter
import heapq


def top_n_words(file_path, n=10):
    """
    Count word frequencies in a large plain-text file and return
    the top-N most frequent words with summary counts.

    Words are:
      - case-insensitive
      - made of letters/digits
      - may contain internal apostrophes
        e.g. don't, user's, rock'n'roll
    """

    # Example word pattern: hello, 123, don't, user's
    word_pattern = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*")

    word_counts = Counter()

    total_words = 0

    # Read line-by-line so even very large files don't need to fit in memory
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            words = word_pattern.findall(line.lower())

            word_counts.update(words)
            total_words += len(words)

    # Get top-N words efficiently
    top_words = heapq.nlargest(
        n,
        word_counts.items(),
        key=lambda item: item[1]
    )

    # Summary
    summary = {
        "total_words": total_words,
        "unique_words": len(word_counts),
        "top_n": n,
        "top_words": top_words
    }

    return summary


# Example usage
if __name__ == "__main__":
    file_path = "input.txt"

    result = top_n_words(file_path, n=10)

    print("Total words:", result["total_words"])
    print("Unique words:", result["unique_words"])
    print("\nTop words:")

    for word, count in result["top_words"]:
        print(f"{word}: {count}")