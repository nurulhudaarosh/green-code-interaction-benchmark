import re
from collections import Counter
from pathlib import Path

_TOKEN_RE = re.compile(r"\w+(?:'\w+)?", re.UNICODE)


def keyword_freq(paths, stopwords=None, top_k=10, include_bigrams=False):
    if isinstance(paths, (str, Path)):
        paths = [paths]
    if isinstance(stopwords, str):
        stopwords = [stopwords]
    stop = {w.casefold() for w in (stopwords or [])}
    counts = Counter()

    for p in paths:
        try:
            text = Path(p).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not text.strip():
            continue

        prev = None  # carries across lines, resets per file
        for tok in _TOKEN_RE.findall(text.casefold()):
            if tok in stop:
                prev = None
                continue
            counts[tok] += 1
            if include_bigrams and prev is not None:
                counts[f"{prev} {tok}"] += 1
            prev = tok

    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]