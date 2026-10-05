import os
import re
from collections import Counter
from typing import List, Tuple, Set, Dict, Optional, Union

DEFAULT_STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can't",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from",
    "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
    "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers",
    "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll",
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its",
    "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't",
    "so", "some", "such", "than", "that", "that's", "the", "their", "theirs",
    "them", "themselves", "then", "there", "there's", "these", "they",
    "they'd", "they'll", "they're", "they've", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "wasn't", "we",
    "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's",
    "when", "when's", "where", "where's", "which", "while", "who", "who's",
    "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves"
}

def keyword_freq(
    source: Union[str, os.PathLike],
    top_k: int = 5,
    stopwords: Optional[Set[str]] = None,
    min_word_length: int = 2,
    is_file_path: bool = False,
    encoding: str = "utf-8"
) -> Dict[str, List[Tuple[str, int]]]:
    """
    Extracts top-k unigrams and bigrams by frequency with robust edge case handling.

    Args:
        source: Text string or file path containing text to analyze.
        top_k: Number of highest frequency items to return. If <= 0, returns empty lists.
        stopwords: Set of lowercase stop words (defaults to DEFAULT_STOPWORDS).
        min_word_length: Minimum character length for a token to be kept.
        is_file_path: If True, reads text from `source` as a filepath.
        encoding: File encoding used when `is_file_path` is True.

    Returns:
        Dict containing top-k 'unigrams' and 'bigrams' as (term, count) tuples.
    """
    empty_result: Dict[str, List[Tuple[str, int]]] = {"unigrams": [], "bigrams": []}

    # Guard: Invalid or zero top_k
    if top_k <= 0:
        return empty_result

    # 1. Input source reading & empty checks
    if is_file_path:
        if not os.path.exists(source) or os.path.getsize(source) == 0:
            return empty_result
        try:
            with open(source, "r", encoding=encoding, errors="replace") as f:
                raw_text = f.read()
        except (OSError, UnicodeDecodeError):
            return empty_result
    else:
        raw_text = source

    if not raw_text or not raw_text.strip():
        return empty_result

    # 2. Setup stop words (case-insensitive set)
    active_stopwords = (
        {w.lower() for w in stopwords}
        if stopwords is not None
        else DEFAULT_STOPWORDS
    )

    # 3. Tokenization
    tokens = re.findall(r"\b[a-zA-Z0-9']+\b", raw_text.lower())
    if not tokens:
        return empty_result

    # 4. Stopword and length filtering
    filtered_tokens = [
        tok for tok in tokens
        if tok not in active_stopwords and len(tok) >= min_word_length
    ]

    # Edge Case: Corpus contained only stopwords / short noise
    if not filtered_tokens:
        return empty_result

    # 5. Unigram extraction (most_common(k) safely handles k > vocab size)
    unigram_counts = Counter(filtered_tokens)
    top_unigrams = unigram_counts.most_common(top_k)

    # 6. Bigram extraction (requires at least 2 remaining valid tokens)
    if len(filtered_tokens) < 2:
        top_bigrams: List[Tuple[str, int]] = []
    else:
        bigrams = [
            f"{filtered_tokens[i]} {filtered_tokens[i + 1]}"
            for i in range(len(filtered_tokens) - 1)
        ]
        bigram_counts = Counter(bigrams)
        top_bigrams = bigram_counts.most_common(top_k)

    return {
        "unigrams": top_unigrams,
        "bigrams": top_bigrams,
    }