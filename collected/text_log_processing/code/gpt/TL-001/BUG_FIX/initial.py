import re
from collections import Counter


def word_frequency(file_path, top_n=10):
    """
    Compute word frequencies from a plain-text file.

    Words are:
      - case-insensitive
      - made of letters/digits
      - may contain internal apostrophes (e.g. don't, user's)

    Returns:
      top_words: list of (word, count)
      summary: dictionary containing total words and unique words
    """

    word_pattern = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*")
    counter = Counter()
    total_words = 0

    # Read line-by-line so the entire file is never loaded into memory.
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            words = word_pattern.findall(line.lower())
            counter.update(words)
            total_words += len(words)

    top_words = counter.most_common(top_n)

    summary = {
        "total_words": total_words,
        "unique_words": len(counter),
    }

    return top_words, summary


# Example usage
if __name__ == "__main__":
    file_path = "input.txt"
    top_n = 10

    top_words, summary = word_frequency(file_path, top_n)

    print("Top words:")
    for word, count in top_words:
        print(f"{word}: {count}")

    print("\nSummary:")
    print(f"Total words: {summary['total_words']}")
    print(f"Unique words: {summary['unique_words']}")