import re
from collections import Counter

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "while", "of", "at", "by", "for",
    "with", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "to", "from", "up", "down", "in", "out", "on",
    "off", "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "can", "will", "just", "should", "now", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had", "do",
    "does", "did", "this", "that", "these", "those", "i", "me", "my", "we",
    "our", "you", "your", "he", "him", "his", "she", "her", "it", "its", "they",
    "them", "their", "what", "which", "who", "whom", "as", "am",
}

TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")


def tokenize(text, lowercase=True):
    """Split text into word tokens. Non-string or empty input yields []."""
    if not isinstance(text, str) or not text.strip():
        return []
    if lowercase:
        text = text.lower()
    return TOKEN_RE.findall(text)


def remove_stopwords(tokens, stopwords=STOPWORDS):
    return [t for t in tokens if t not in stopwords]


def get_ngrams(tokens, n):
    if n < 1 or len(tokens) < n:
        return []
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def _validate_top_k(top_k):
    if isinstance(top_k, bool) or not isinstance(top_k, int):
        raise TypeError(f"top_k must be an int, got {type(top_k).__name__}")
    if top_k < 0:
        raise ValueError("top_k must be >= 0")
    return top_k


def keyword_freq(text, top_k=10, stopwords=STOPWORDS, min_len=2):
    """
    Returns a dict:
        {
            "unigrams": [(word, count), ...],   # at most top_k items
            "bigrams":  [(phrase, count), ...], # at most top_k items
            "status":   "ok" | "empty" | "only_stopwords",
            "total_tokens": int,                # tokens before stopword removal
            "kept_tokens": int,                 # tokens after filtering
        }

    Edge cases:
        - Empty / whitespace-only / None / non-string text -> status "empty".
        - Text with only stopwords (or tokens shorter than min_len)
          -> status "only_stopwords", empty result lists.
        - top_k larger than vocabulary -> returns every item available
          (Counter.most_common slices safely; no padding, no error).
        - top_k == 0 -> empty lists.
        - Negative or non-int top_k -> ValueError / TypeError.
    """
    top_k = _validate_top_k(top_k)

    raw_tokens = tokenize(text)
    result = {
        "unigrams": [],
        "bigrams": [],
        "status": "empty",
        "total_tokens": len(raw_tokens),
        "kept_tokens": 0,
    }
    if not raw_tokens:
        return result

    tokens = [t for t in raw_tokens if len(t) >= min_len]
    tokens = remove_stopwords(tokens, stopwords)
    result["kept_tokens"] = len(tokens)

    if not tokens:
        result["status"] = "only_stopwords"
        return result

    result["status"] = "ok"
    result["unigrams"] = Counter(tokens).most_common(top_k)
    result["bigrams"] = Counter(get_ngrams(tokens, 2)).most_common(top_k)
    return result


def keyword_freq_files(paths, top_k=10, encoding="utf-8", **kwargs):
    """
    Aggregate counts across multiple files.
    Unreadable files are skipped and reported in 'skipped'.
    A corpus with no readable text is reported as 'empty';
    one containing only stopwords as 'only_stopwords'.
    """
    top_k = _validate_top_k(top_k)

    uni, bi = Counter(), Counter()
    total = kept = 0
    skipped = []
    stopwords = kwargs.get("stopwords", STOPWORDS)
    min_len = kwargs.get("min_len", 2)

    for path in paths or []:
        try:
            with open(path, "r", encoding=encoding, errors="replace") as f:
                text = f.read()
        except OSError as e:
            skipped.append((str(path), str(e)))
            continue

        raw = tokenize(text)
        total += len(raw)
        tokens = remove_stopwords([t for t in raw if len(t) >= min_len], stopwords)
        kept += len(tokens)
        uni.update(tokens)
        bi.update(get_ngrams(tokens, 2))  # per-file, so no bigrams span file boundaries

    if total == 0:
        status = "empty"
    elif kept == 0:
        status = "only_stopwords"
    else:
        status = "ok"

    return {
        "unigrams": uni.most_common(top_k),
        "bigrams": bi.most_common(top_k),
        "status": status,
        "total_tokens": total,
        "kept_tokens": kept,
        "skipped": skipped,
    }


if __name__ == "__main__":
    # Empty corpus
    print(keyword_freq("")["status"])                       # empty
    print(keyword_freq(None)["status"])                     # empty

    # Only stopwords
    print(keyword_freq("the and of to a")["status"])        # only_stopwords

    # top_k larger than vocabulary
    r = keyword_freq("quality assurance testing", top_k=100)
    print(r["status"], r["unigrams"], r["bigrams"])
    # ok [('quality', 1), ('assurance', 1), ('testing', 1)]
    #    [('quality assurance', 1), ('assurance testing', 1)]

    # top_k = 0
    print(keyword_freq("quality assurance", top_k=0)["unigrams"])  # []