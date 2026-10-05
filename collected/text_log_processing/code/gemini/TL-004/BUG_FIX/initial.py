from collections import Counter
from pathlib import Path
import re
from typing import Iterable, List, Sequence, Tuple, Union


def keyword_freq(
    paths: Sequence[Union[str, Path]],
    stopwords: Iterable[str],
    top_k: int = 10,
    include_bigrams: bool = False,
) -> List[Tuple[str, int]]:
    """Tokenizes text files, removes stopwords, counts unigrams (and optionally bigrams),

    and returns the top-k most frequent terms.

    Args:
        paths: Sequence of file paths to process.
        stopwords: Collection of words to exclude.
        top_k: Number of top results to return.
        include_bigrams: Whether to include adjacent word pairs.

    Returns:
        List of (term, frequency) tuples sorted by count descending.
    """
    stop_set = {word.lower() for word in stopwords}
    word_pattern = re.compile(r"\b[a-zA-Z0-9]+(?:'[a-zA-Z0-9]+)?\b")
    counts = Counter()

    for path in paths:
        path_obj = Path(path)
        if not path_obj.is_file():
            continue

        try:
            text = path_obj.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Extract tokens and normalize case
        tokens = [
            token.lower()
            for token in word_pattern.findall(text)
            if token.lower() not in stop_set
        ]

        # 1. Unigrams
        counts.update(tokens)

        # 2. Bigrams (constructed from consecutive filtered tokens)
        if include_bigrams and len(tokens) >= 2:
            bigrams = (f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1))
            counts.update(bigrams)

    return counts.most_common(top_k)