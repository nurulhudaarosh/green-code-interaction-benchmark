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
      - top_n: list of (word, count)
      - total_words: total number of words
      - unique_words: number of distinct words
    """

    # Matches words such as:
    # hello
    # hello123
    # don't
    # user's
    word_pattern = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*")

    counter = Counter()
    total_words = 0

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            words = word_pattern.findall(line.lower())

            counter.update(words)
            total_words += len(words)

    unique_words = len(counter)
    top_words = counter.most_common(top_n)

    return top_words, total_words, unique_words


# Example usage
file_path = "input.txt"
top_words, total_words, unique_words = word_frequency(file_path, top_n=10)

print("Top words:")
for word, count in top_words:
    print(f"{word}: {count}")

print("\nSummary:")
print(f"Total words: {total_words}")
print(f"Unique words: {unique_words}")