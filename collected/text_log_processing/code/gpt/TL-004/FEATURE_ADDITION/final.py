import re
from collections import Counter


def unigram_freq(path, top_k=20, include_bigrams=False):
    unigram_counts = Counter()
    bigram_counts = Counter()
    total_tokens = 0
    previous_word = None

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            words = re.findall(r"[a-z0-9]+", line.lower())

            for word in words:
                unigram_counts[word] += 1
                total_tokens += 1

                if include_bigrams and previous_word is not None:
                    bigram_counts[(previous_word, word)] += 1

                previous_word = word

    top_words = sorted(
        unigram_counts.items(),
        key=lambda x: (-x[1], x[0])
    )[:top_k]

    result = {
        "top_k": top_words,
        "total_tokens": total_tokens
    }

    if include_bigrams:
        top_bigrams = sorted(
            bigram_counts.items(),
            key=lambda x: (-x[1], x[0])
        )[:top_k]

        result["top_bigrams"] = top_bigrams

    return result