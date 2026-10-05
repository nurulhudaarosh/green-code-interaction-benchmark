import re
from collections import Counter
from typing import List, Tuple


def unigram_frequency(
    text: str,
    k: int = 10,
    lowercase: bool = True,
    strip_punctuation: bool = True,
) -> Tuple[List[Tuple[str, int]], int]:
    """
    Analyze unigram (single-word) frequencies in a text.

    Args:
        text: Input text to analyze.
        k: Number of top words to return.
        lowercase: Whether to normalize case before counting.
        strip_punctuation: Whether to remove punctuation from tokens.

    Returns:
        A tuple (top_k, total_tokens) where:
            - top_k is a list of (word, count) tuples sorted by count desc.
            - total_tokens is the total number of tokens processed.
    """
    if k <= 0:
        raise ValueError("k must be a positive integer")

    # Normalize case if requested
    if lowercase:
        text = text.lower()

    # Tokenize: split on non-alphanumeric characters (handles punctuation)
    if strip_punctuation:
        tokens = re.findall(r"\b\w+\b", text, flags=re.UNICODE)
    else:
        tokens = text.split()

    # Count frequencies
    counts = Counter(tokens)
    total_tokens = sum(counts.values())

    # top-k by count (ties broken alphabetically for determinism)
    top_k = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]

    return top_k, total_tokens


# ---------------------------------------------------------------------------
# Example usage / demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample = """
    The quick brown fox jumps over the lazy dog.
    The dog barks, and the fox runs away. The fox is quick!
    """

    top_words, total = unigram_frequency(sample, k=5)
    print(f"Total tokens: {total}")
    print("Top 5 words:")
    for word, count in top_words:
        print(f"  {word:<8} {count}")