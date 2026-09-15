import re
from collections import Counter

def word_frequency(file_path, top_n=10):
    """
    Compute word frequencies from a plain-text file.

    Words are:
      - case-insensitive
      - made of letters/digits
      - may contain internal apostrophes, e.g. "don't", "user's"
    """

    # Matches words like:
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

    # Top-N most frequent words
    top_words = counter.most_common(top_n)

    return {
        "top_words": top_words,
        "unique_words": len(counter),
        "total_words": total_words,
    }


# Example usage
result = word_frequency("large_file.txt", top_n=10)

print("Top words:")
for word, count in result["top_words"]:
    print(f"{word}: {count}")

print("\nSummary:")
print("Total words:", result["total_words"])
print("Unique words:", result["unique_words"])