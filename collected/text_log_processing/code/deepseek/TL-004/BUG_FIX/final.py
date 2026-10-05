import re
from collections import Counter
from pathlib import Path


def keyword_freq(paths, stopwords=None, top_k=10, include_bigrams=False):
    """
    Tokenize text files, filter stopwords, count unigrams (and optionally bigrams),
    and return the top-k most frequent keywords.

    Fixes:
      - Case-insensitive stopword filtering (tokens are lowercased before comparison).
      - Empty / unreadable files are handled gracefully (no crash).
      - Bigrams span across line boundaries (continuity is per-file, not per-line).

    Args:
        paths (str | Path | list): File path(s) or directory(ies) to process.
        stopwords (iterable): Words to filter out (case-insensitive).
        top_k (int): Number of top keywords to return.
        include_bigrams (bool): If True, also count and include bigrams.

    Returns:
        list[tuple[str, int]]: Top-k (keyword, count) pairs sorted by frequency.
    """
    # Case-insensitive stopword set
    stopwords = {w.lower() for w in (stopwords or []) if w}

    # Normalize input to a list of file paths
    if isinstance(paths, (str, Path)):
        paths = [paths]

    files = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files.extend(f for f in p.rglob("*") if f.is_file())
        elif p.is_file():
            files.append(p)

    token_re = re.compile(r"[a-zA-Z']+")
    counter = Counter()

    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeError):
            continue

        # Skip empty / whitespace-only files early
        if not text.strip():
            continue

        # Lowercase, then tokenize; stopword filter is now case-insensitive
        tokens = [
            t for t in token_re.findall(text.lower())
            if t and t not in stopwords
        ]

        if not tokens:
            continue

        counter.update(tokens)

        if include_bigrams and len(tokens) > 1:
            # Continuity is maintained across newlines because we tokenized
            # the whole file at once rather than line-by-line.
            bigrams = (
                f"{tokens[i]} {tokens[i + 1]}"
                for i in range(len(tokens) - 1)
            )
            counter.update(bigrams)

    return counter.most_common(top_k)