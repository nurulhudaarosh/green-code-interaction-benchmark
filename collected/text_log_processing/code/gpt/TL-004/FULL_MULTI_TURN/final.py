import re
from collections import Counter


def word_frequency(text, stopwords=(), top_k=10, include_bigrams=False):
    tokens = re.findall(r"[a-z0-9]+", text.lower())

    # Case-insensitive stopword filtering
    stopwords = {word.lower() for word in stopwords}
    tokens = [word for word in tokens if word not in stopwords]

    # Handle negative top_k safely
    k = max(0, top_k)

    # Unigrams
    unigram_counts = Counter(tokens)
    top_unigrams = sorted(
        unigram_counts.items(),
        key=lambda x: (-x[1], x[0])
    )[:k]

    result = {
        "total_tokens": len(tokens),
        "top_unigrams": top_unigrams
    }

    # Optional bigrams
    if include_bigrams:
        bigram_counts = Counter(zip(tokens, tokens[1:]))

        top_bigrams = sorted(
            bigram_counts.items(),
            key=lambda x: (-x[1], x[0])
        )[:k]

        result["top_bigrams"] = top_bigrams

    return result