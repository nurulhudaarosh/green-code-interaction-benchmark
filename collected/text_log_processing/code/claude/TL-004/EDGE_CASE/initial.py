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
    """Split text into word tokens (letters/digits, optional inner apostrophe)."""
    if lowercase:
        text = text.lower()
    return TOKEN_RE.findall(text)


def remove_stopwords(tokens, stopwords=STOPWORDS):
    return [t for t in tokens if t not in stopwords]


def get_ngrams(tokens, n):
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def keyword_freq(text, k=10, stopwords=STOPWORDS, min_len=2):
    """
    Returns a dict with top-k unigrams and bigrams.

    Unigrams: stopwords and short tokens removed.
    Bigrams: built from the filtered token stream, so they skip stopwords
             (e.g. "quality assurance testing" -> "quality assurance",
             "assurance testing").
    """
    tokens = [t for t in tokenize(text) if len(t) >= min_len]
    tokens = remove_stopwords(tokens, stopwords)

    unigrams = Counter(tokens)
    bigrams = Counter(get_ngrams(tokens, 2))

    return {
        "unigrams": unigrams.most_common(k),
        "bigrams": bigrams.most_common(k),
    }


if __name__ == "__main__":
    sample = """
    Software quality assurance is the process of ensuring software quality.
    Quality assurance engineers write test cases, run automated tests, and
    report bugs. Good test automation improves software quality.
    """
    result = keyword_freq(sample, k=5)

    print("Top unigrams:")
    for word, count in result["unigrams"]:
        print(f"  {word}: {count}")

    print("Top bigrams:")
    for phrase, count in result["bigrams"]:
        print(f"  {phrase}: {count}")