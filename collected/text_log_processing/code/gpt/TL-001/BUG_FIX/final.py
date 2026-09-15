import re
from collections import Counter


def word_frequency(file_path, top_n):
    word_counts = Counter()
    total_words = 0

    # Process the file line by line
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            # Match words with optional internal apostrophes
            words = re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*", line.lower())

            word_counts.update(words)
            total_words += len(words)

    # Get top-N most frequent words
    top_words = word_counts.most_common(top_n)

    # Summary counts
    summary = {
        "total_words": total_words,
        "unique_words": len(word_counts)
    }

    return top_words, summary


# Example
top_words, summary = word_frequency("input.txt", 10)

print("Top 10 words:")
for word, count in top_words:
    print(f"{word}: {count}")

print("\nSummary:")
print("Total words:", summary["total_words"])
print("Unique words:", summary["unique_words"])