import re
from collections import Counter

def word_frequency(file_path, top_n):
    word_pattern = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*")
    counts = Counter()
    total_words = 0

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            words = word_pattern.findall(line.lower())
            counts.update(words)
            total_words += len(words)

    return {
        "top_words": counts.most_common(top_n),
        "total_words": total_words,
        "unique_words": len(counts)
    }