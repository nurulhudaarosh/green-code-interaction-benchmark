import re
from collections import Counter
from collections.abc import Iterable
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9]+")


def keyword_freq(
    paths: Iterable[str],
    stopwords: Iterable[str] = (),
    top_k: int = 20,
    include_bigrams: bool = False,
) -> dict[str, Any]:
    """Calculate frequency of unigrams (and optionally bigrams) across text files.

    Args:
        paths: Iterable of file paths to process.
        stopwords: Words to ignore (case-insensitive).
        top_k: Number of top results to return.
        include_bigrams: If True, counts adjacent word pairs across lines/chunks.

    Returns:
        A dict containing:
            - 'results': List of (term, count) tuples sorted by count desc, term asc.
            - 'total_tokens': Total count of valid unigrams evaluated.
    """
    stop_set = {w.lower() for w in stopwords}
    counts = Counter()
    total_tokens = 0

    for path in paths:
        prev_token = None

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                # Tokenize streaming per line
                tokens = TOKEN_RE.findall(line.lower())

                for token in tokens:
                    if token in stop_set:
                        # Stopwords reset bigram adjacency
                        prev_token = None
                        continue

                    # Unigram counting
                    counts[token] += 1
                    total_tokens += 1

                    # Bigram counting across lines
                    if include_bigrams:
                        if prev_token is not None:
                            counts[f"{prev_token} {token}"] += 1
                        prev_token = token

    # Sort primarily by count (descending), secondarily by term (lexicographical asc)
    sorted_items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    return {
        "results": sorted_items[:top_k],
        "total_tokens": total_tokens,
    }