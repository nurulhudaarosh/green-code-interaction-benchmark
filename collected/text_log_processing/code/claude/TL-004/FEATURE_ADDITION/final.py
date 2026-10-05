import re
from collections import Counter

_TOKEN_RE = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*", re.UNICODE)


def tokenize(text, lowercase=True):
    if lowercase:
        text = text.lower()
    return _TOKEN_RE.findall(text)


def _top_k(counter, k):
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[: max(k, 0)]


def unigram_analyzer(text, k=10, lowercase=True, stopwords=None, include_bigrams=False):
    """
    Default (include_bigrams=False): returns (top_k_unigrams, total_tokens).
    include_bigrams=True: returns (top_k_unigrams, total_tokens, top_k_bigrams),
    where bigrams are ((w1, w2), count) over adjacent tokens after stopword removal.
    """
    tokens = tokenize(text, lowercase)
    if stopwords:
        tokens = [t for t in tokens if t not in stopwords]

    top_unigrams = _top_k(Counter(tokens), k)
    total = len(tokens)

    if not include_bigrams:
        return top_unigrams, total

    bigram_counts = Counter(zip(tokens, tokens[1:]))
    return top_unigrams, total, _top_k(bigram_counts, k)


if __name__ == "__main__":
    sample = "The cat sat on the mat. The dog didn't sit; the cat did."

    print(unigram_analyzer(sample, k=3))
    # ([('the', 4), ('cat', 2), ("didn't", 1)], 13)

    uni, total, bi = unigram_analyzer(sample, k=3, include_bigrams=True)
    print(bi)
    # [(('the', 'cat'), 2), (('cat', 'did'), 1), (('cat', 'sat'), 1)]