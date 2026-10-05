import re
import heapq
from collections import Counter
from typing import List, Tuple, Optional, Union


def unigram_frequency(
    text: str,
    k: int = 10,
    lowercase: bool = True,
    strip_punctuation: bool = True,
    include_bigrams: bool = False,
) -> Union[
    Tuple[List[Tuple[str, int]], int],
    Tuple[List[Tuple[str, int]], int, List[Tuple[Tuple[str, str], int]], int],
]:
    """
    Analyze unigram (and optionally bigram) frequencies in a text.

    Args:
        text: Input text to analyze.
        k: Number of top items to return (applies to both unigrams and bigrams).
        lowercase: Whether to normalize case before counting.
        strip_punctuation: Whether to remove punctuation from tokens.
        include_bigrams: If True, also compute and return top-k bigrams.

    Returns:
        If include_bigrams is False:
            (top_k_unigrams, total_unigram_tokens)
        If include_bigrams is True:
            (top_k_unigrams, total_unigram_tokens,
             top_k_bigrams, total_bigram_tokens)
    """
    if k <= 0:
        raise ValueError("k must be a positive integer")

    # --- Tokenize (identical to before) ---
    if lowercase:
        text = text.lower()

    if strip_punctuation:
        tokens = re.findall(r"\b\w+\b", text, flags=re.UNICODE)
    else:
        tokens = text.split()

    # --- Unigrams (unchanged behavior) ---
    unigram_counts = Counter(tokens)
    total_tokens = sum(unigram_counts.values())
    top_unigrams = sorted(unigram_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]

    if not include_bigrams:
        return top_unigrams, total_tokens

    # --- Bigrams ---
    bigrams = list(zip(tokens, tokens[1:]))
    bigram_counts = Counter(bigrams)
    total_bigrams = sum(bigram_counts.values())

    # Sort by count desc, then lexicographically by the (w1, w2) tuple
    top_bigrams = sorted(
        bigram_counts.items(),
        key=lambda kv: (-kv[1], kv[0][0], kv[0][1]),
    )[:k]

    return top_unigrams, total_tokens, top_bigrams, total_bigrams


# ---------------------------------------------------------------------------
# Example usage / demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample = """
    The quick brown fox jumps over the lazy dog.
    The dog barks, and the fox runs away. The fox is quick!
    """

    # Unigram-only call: identical output to before
    top_words, total = unigram_frequency(sample, k=5)
    print(f"Total tokens: {total}")
    print("Top 5 words:")
    for word, count in top_words:
        print(f"  {word:<8} {count}")

    print()

    # With bigrams
    top_words, total, top_bigrams, total_bigrams = unigram_frequency(
        sample, k=5, include_bigrams=True
    )
    print(f"Total tokens: {total}, total bigrams: {total_bigrams}")
    print("Top 5 bigrams:")
    for (w1, w2), count in top_bigrams:
        print(f"  {w1} {w2:<10} {count}")