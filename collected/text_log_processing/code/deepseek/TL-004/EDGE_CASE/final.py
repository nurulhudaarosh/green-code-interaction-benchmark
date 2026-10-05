import re
from collections import Counter
from typing import Iterable, List, Tuple, Dict, Optional

DEFAULT_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "have", "had", "he", "her", "his", "i", "in", "is", "it", "its",
    "of", "on", "or", "that", "the", "their", "them", "they", "this", "to",
    "was", "were", "will", "with", "you", "your", "we", "our", "us", "not",
    "no", "so", "if", "then", "than", "do", "does", "did", "doing", "can",
    "could", "should", "would", "may", "might", "must", "am", "been", "being",
}

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9'_]*")


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    return TOKEN_RE.findall(text.lower())


def remove_stopwords(tokens: Iterable[str],
                     stopwords: set = DEFAULT_STOPWORDS) -> List[str]:
    return [t for t in tokens if t not in stopwords and len(t) > 1]


def make_bigrams(tokens: List[str]) -> List[Tuple[str, str]]:
    return list(zip(tokens, tokens[1:]))


def keyword_freq(
    text: Optional[str],
    top_k: int = 20,
    ngrams: Tuple[int, ...] = (1, 2),
    stopwords: Optional[set] = None,
    use_stopwords: bool = True,
) -> Dict[str, List[Tuple[str, int]]]:
    """
    Compute top-k keyword frequencies with robust edge-case handling.

    Edge cases covered:
      * text is None / empty / whitespace-only
      * top_k <= 0  -> returns empty lists
      * top_k larger than vocabulary -> returns all available
      * text contains only stopwords -> unigrams/bigrams empty
      * unicode / non-ASCII text -> handled by regex (letters only kept)
    """
    # ---- normalize inputs ----
    if stopwords is None:
        stopwords = DEFAULT_STOPWORDS

    if top_k is None or top_k < 0:
        top_k = 0

    if not text or not text.strip():
        return {("unigrams" if n == 1 else "bigrams"): []
                for n in ngrams}

    tokens = tokenize(text)

    if use_stopwords:
        tokens = remove_stopwords(tokens, stopwords)

    # If everything was a stopword (or too short), nothing to count.
    if not tokens:
        return {("unigrams" if n == 1 else "bigrams"): []
                for n in ngrams}

    results: Dict[str, List[Tuple[str, int]]] = {}

    for n in ngrams:
        if n == 1:
            counts = Counter(tokens)
            key = "unigrams"
        elif n == 2:
            if len(tokens) < 2:
                # Not enough tokens to form even one bigram.
                results["bigrams"] = []
                continue
            counts = Counter(make_bigrams(tokens))
            counts = Counter({" ".join(k): v for k, v in counts.items()})
            key = "bigrams"
        else:
            raise ValueError(f"Unsupported ngram size: {n}")

        # most_common handles top_k > len(counts) gracefully (returns all).
        if top_k == 0:
            results[key] = []
        else:
            results[key] = counts.most_common(top_k)

    return results