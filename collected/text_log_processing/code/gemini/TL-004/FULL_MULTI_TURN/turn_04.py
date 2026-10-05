import math
import re
from collections import Counter
from typing import Dict, Iterable, List, Literal, Optional, Set, Tuple, Union

DEFAULT_STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can't",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from",
    "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
    "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm",
    "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've",
    "were", "weren't", "what", "what's", "when", "when's", "where", "where's",
    "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your",
    "yours", "yourself", "yourselves"
}


def _tokenize(text: Optional[str]) -> List[str]:
    """Cleans hyphenated wraps and tokenizes into lowercase words."""
    if not text or not text.strip():
        return []

    # Rejoin words hyphenated across line breaks (e.g. "lan-\n guage" -> "language")
    clean = re.sub(r"(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)", r"\1\2", text)
    clean = clean.lower()

    return re.findall(r"\b[a-z]+(?:'[a-z]+)?\b", clean)


def _sanitize_top_k(top_k: Optional[int], vocab_size: int) -> int:
    """Clamps top_k safely to the range [0, vocab_size]."""
    if top_k is None or math.isinf(top_k):
        return vocab_size
    if not isinstance(top_k, int) or top_k <= 0 or vocab_size == 0:
        return 0
    return min(top_k, vocab_size)


def analyze_frequencies(
    text: Optional[str],
    mode: Literal["unigram", "bigram", "all"] = "all",
    top_k: Optional[int] = 10,
    stopwords: Optional[Iterable[str]] = None,
    min_length: int = 2,
    bigram_filter: Literal["any", "all", "none"] = "any"
) -> Union[List[Tuple[str, int]], Dict[str, List[Tuple[str, int]]]]:
    """
    Extracts top-k unigrams and/or bigrams. Handles empty inputs, empty vocabularies,
    and oversized/unbounded top_k without raising errors.
    """
    empty_dict: Dict[str, List[Tuple[str, int]]] = {"unigrams": [], "bigrams": []}

    # Early exit on invalid/empty top_k or empty text
    if top_k is not None and top_k <= 0:
        return empty_dict if mode == "all" else []
    if not text or not text.strip():
        return empty_dict if mode == "all" else []

    # Normalize stopwords
    stopword_set = (
        DEFAULT_STOPWORDS
        if stopwords is None
        else {w.strip().lower() for w in stopwords if w and w.strip()}
    )

    tokens = _tokenize(text)
    if not tokens:
        return empty_dict if mode == "all" else []

    length_valid_tokens = [t for t in tokens if len(t) >= min_length]

    # --- Unigram Mode ---
    unigram_results: List[Tuple[str, int]] = []
    if mode in ("unigram", "all"):
        filtered_unigrams = [t for t in length_valid_tokens if t not in stopword_set]
        
        # Empty vocab check: all tokens were filtered out
        if filtered_unigrams:
            counts = Counter(filtered_unigrams)
            k = _sanitize_top_k(top_k, len(counts))
            unigram_results = counts.most_common(k)
        
        if mode == "unigram":
            return unigram_results

    # --- Bigram Mode ---
    bigram_results: List[Tuple[str, int]] = []
    if mode in ("bigram", "all"):
        bigrams: List[str] = []
        
        for i in range(len(length_valid_tokens) - 1):
            w1, w2 = length_valid_tokens[i], length_valid_tokens[i + 1]
            w1_stop, w2_stop = w1 in stopword_set, w2 in stopword_set

            if bigram_filter == "any" and (w1_stop or w2_stop):
                continue
            elif bigram_filter == "all" and (w1_stop and w2_stop):
                continue

            bigrams.append(f"{w1} {w2}")

        # Empty vocab check: no candidate bigrams survived
        if bigrams:
            counts = Counter(bigrams)
            k = _sanitize_top_k(top_k, len(counts))
            bigram_results = counts.most_common(k)

        if mode == "bigram":
            return bigram_results

    return {
        "unigrams": unigram_results,
        "bigrams": bigram_results
    }