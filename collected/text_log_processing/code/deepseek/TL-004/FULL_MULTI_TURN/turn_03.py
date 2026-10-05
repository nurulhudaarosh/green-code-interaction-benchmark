import re
from collections import Counter
from typing import List, Tuple, Set, Optional, Iterable


# ----------------------------------------------------------------------
# Built-in stopword list (common English stopwords)
# NOTE: All entries are lowercase. Matching is done case-insensitively.
# ----------------------------------------------------------------------
DEFAULT_STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can't",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from",
    "further", "had", "hadn't", "has", "hasn't", "have", "haven't",
    "having", "he", "he'd", "he'll", "he's", "her", "here", "here's",
    "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most",
    "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on",
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves",
    "out", "over", "own", "same", "shan't", "she", "she'd", "she'll",
    "she's", "should", "shouldn't", "so", "some", "such", "than",
    "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasn't", "we", "we'd",
    "we'll", "we're", "we've", "were", "weren't", "what", "what's",
    "when", "when's", "where", "where's", "which", "while", "who",
    "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your",
    "yours", "yourself", "yourselves",
}


# ----------------------------------------------------------------------
# Text loading (safe against empty files / missing paths)
# ----------------------------------------------------------------------
def load_text(source: Optional[str] = None, path: Optional[str] = None) -> str:
    """
    Load text from a string or file path, returning "" on failure.

    - If `source` is provided, it is returned as-is (after None -> "").
    - If `path` is provided, the file is read with UTF-8 encoding.
      Any IOError / UnicodeDecodeError returns "" instead of crashing.
    """
    if source is not None:
        return source if isinstance(source, str) else ""

    if path:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                return fh.read()
        except (OSError, UnicodeError) as exc:
            print(f"  ⚠️  Could not read '{path}': {exc}")
            return ""

    return ""


# ----------------------------------------------------------------------
# Tokenization
# ----------------------------------------------------------------------
def tokenize(
    text: str,
    *,
    lowercase: bool = True,
    strip_punct: bool = True,
) -> List[str]:
    """
    Convert raw text into a flat list of word tokens.

    - `lowercase=True`  → case-insensitive matching (fixes case-sensitivity bugs).
    - `strip_punct=True` → removes everything except letters, digits, and
      apostrophes (so "don't" survives as a token but "hello," becomes "hello").

    Returns [] for empty or None input — callers never crash on empty files.
    """
    if not text:
        return []

    if lowercase:
        text = text.lower()

    if strip_punct:
        # Keep letters (any Unicode script), digits, and apostrophes.
        # Everything else becomes whitespace.
        text = re.sub(r"[^\w']", " ", text, flags=re.UNICODE)

    # Split on whitespace and strip stray apostrophes from token edges.
    tokens = []
    for tok in text.split():
        tok = tok.strip("'")
        if tok:
            tokens.append(tok)
    return tokens


# ----------------------------------------------------------------------
# Core frequency functions
# ----------------------------------------------------------------------
def _filter_tokens(
    tokens: Iterable[str],
    stopwords: Set[str],
    filter_stopwords: bool,
    min_word_length: int,
) -> List[str]:
    """Apply stopword and length filters. Stopwords are compared lowercased."""
    if filter_stopwords and stopwords:
        # Defensive: ensure stopwords are lowercase so matching is always
        # case-insensitive, even if the user passed mixed-case entries.
        stops = {s.lower() for s in stopwords if s}
    else:
        stops = set()

    out = []
    for tok in tokens:
        if len(tok) < min_word_length:
            continue
        if filter_stopwords and tok.lower() in stops:
            continue
        out.append(tok)
    return out


def word_frequency(
    text: str,
    stopwords: Optional[Set[str]] = None,
    top_k: int = 10,
    filter_stopwords: bool = True,
    min_word_length: int = 1,
) -> Tuple[List[Tuple[str, int]], int]:
    """
    Top-k unigrams after case-insensitive stopword filtering.

    Returns:
        (results, total_unique)
        results      -> list of (word, count) sorted by (-count, word)
        total_unique -> number of distinct words that survived filtering
    """
    if stopwords is None:
        stopwords = DEFAULT_STOPWORDS

    if top_k < 0:
        top_k = 0

    tokens = tokenize(text)                       # case-folded, punct-stripped
    filtered = _filter_tokens(tokens, stopwords, filter_stopwords, min_word_length)

    counter = Counter(filtered)
    sorted_items = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return sorted_items[:top_k], len(counter)


def bigram_frequency(
    text: str,
    stopwords: Optional[Set[str]] = None,
    top_k: int = 10,
    filter_stopwords: bool = True,
    min_word_length: int = 1,
    *,
    cross_line: bool = True,
) -> Tuple[List[Tuple[Tuple[str, str], int]], int]:
    """
    Top-k bigrams (word pairs) after stopword filtering.

    Bigrams are formed from the *filtered* token stream, so pairs never
    contain a stopword. When `cross_line=True`, pairs span newlines and
    blank lines — i.e. "line1 word" + "line2 word" is a valid bigram.

    Args:
        text:             Raw input text (can be empty).
        stopwords:        Stopword set (case-insensitive). None → default.
        top_k:            How many bigrams to return.
        filter_stopwords: Toggle stopword removal.
        min_word_length:  Drop short tokens before pairing.
        cross_line:       If False, bigrams never span paragraph breaks.

    Returns:
        (results, total_unique)
        results -> list of ((w1, w2), count) sorted by (-count, (w1, w2)).
    """
    if stopwords is None:
        stopwords = DEFAULT_STOPWORDS

    if top_k < 0:
        top_k = 0

    if not text:
        return [], 0

    # --- Build the token stream ---
    if cross_line:
        # Flatten everything: newlines become spaces, so bigrams cross lines.
        flat = re.sub(r"\s+", " ", text)
        tokens = tokenize(flat)
    else:
        # Preserve line boundaries; concatenate per-line bigrams.
        tokens = []
        for line in text.splitlines():
            tokens.extend(tokenize(line))

    filtered = _filter_tokens(tokens, stopwords, filter_stopwords, min_word_length)

    # Need at least 2 tokens for any bigram
    if len(filtered) < 2:
        return [], 0

    bigrams = list(zip(filtered, filtered[1:]))
    counter = Counter(bigrams)
    sorted_items = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return sorted_items[:top_k], len(counter)


# ----------------------------------------------------------------------
# Pretty printers
# ----------------------------------------------------------------------
def print_unigrams(results: List[Tuple[str, int]], total_unique: int = 0) -> None:
    if not results:
        print("  (no words found after filtering)")
        return

    max_word_len = max((len(w) for w, _ in results), default=4)
    max_count_len = max((len(str(c)) for _, c in results), default=5)
    ww = max(max_word_len, 6)
    cw = max(max_count_len, 5)

    print(f"  {'Rank':<5} {'Word':<{ww}} {'Count':>{cw}}")
    print(f"  {'-'*5} {'-'*ww} {'-'*cw}")
    for rank, (word, count) in enumerate(results, start=1):
        print(f"  {rank:<5} {word:<{ww}} {count:>{cw}}")
    if total_unique:
        print(f"\n  (unique words after filtering: {total_unique})")


def print_bigrams(results: List[Tuple[Tuple[str, str], int]], total_unique: int = 0) -> None:
    if not results:
        print("  (no bigrams found after filtering)")
        return

    labels = [f"{a} {b}" for (a, b), _ in results]
    max_label_len = max(len(s) for s in labels)
    max_count_len = max(len(str(c)) for _, c in results)
    lw = max(max_label_len, 14)
    cw = max(max_count_len, 5)

    print(f"  {'Rank':<5} {'Bigram':<{lw}} {'Count':>{cw}}")
    print(f"  {'-'*5} {'-'*lw} {'-'*cw}")
    for rank, ((a, b), count) in enumerate(results, start=1):
        label = f"{a} {b}"
        print(f"  {rank:<5} {label:<{lw}} {count:>{cw}}")
    if total_unique:
        print(f"\n  (unique bigrams after filtering: {total_unique})")


# ----------------------------------------------------------------------
# Demo / self-test
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("WORD FREQUENCY ANALYZER — hardened version")
    print("=" * 70)

    # --- Test 1: case-sensitivity fix -----------------------------------
    print("\n📌 Test 1: Case-insensitivity (The / the / THE all merge)")
    print("-" * 70)
    mixed = "The THE the Apple apple APPLE banana Banana."
    res, uniq = word_frequency(mixed, top_k=10)
    print_unigrams(res, uniq)

    # --- Test 2: empty input (no crash) --------------------------------
    print("\n📌 Test 2: Empty / None input (should not crash)")
    print("-" * 70)
    for label, payload in [("empty string", ""), ("None", None), ("whitespace", "   \n\t  ")]:
        try:
            r, u = word_frequency(payload)                       # type: ignore[arg-type]
            b, ub = bigram_frequency(payload)                    # type: ignore[arg-type]
            print(f"  {label:<14} -> unigrams={len(r)}, bigrams={len(b)}  ✅")
        except Exception as exc:
            print(f"  {label:<14} -> CRASH: {exc}  ❌")

    # --- Test 3: empty file (no crash) ---------------------------------
    print("\n📌 Test 3: Empty file (should not crash)")
    print("-" * 70)
    import tempfile, os
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        empty_path = fh.name
    try:
        text = load_text(path=empty_path)
        r, u = word_frequency(text)
        print(f"  empty file     -> unigrams={len(r)}, unique={u}  ✅")
    finally:
        os.unlink(empty_path)

    # --- Test 4: cross-line bigrams ------------------------------------
    print("\n📌 Test 4: Cross-line bigrams (line breaks should NOT block pairs)")
    print("-" * 70)
    multiline = (
        "the quick brown fox\n"
        "jumps over the lazy dog\n"
        "the fox sleeps"
    )
    print("  Input:")
    for line in multiline.splitlines():
        print(f"    | {line}")

    bg_cross, uniq_cross = bigram_frequency(multiline, top_k=6, cross_line=True)
    print("\n  cross_line=True (bigrams span newlines):")
    print_bigrams(bg_cross, uniq_cross)

    bg_no_cross, uniq_no_cross = bigram_frequency(multiline, top_k=6, cross_line=False)
    print("\n  cross_line=False (bigrams stay within lines):")
    print_bigrams(bg_no_cross, uniq_no_cross)

    # --- Test 5: custom stopwords case-insensitivity -------------------
    print("\n📌 Test 5: Custom stopwords passed in MIXED case still work")
    print("-" * 70)
    txt = "Fox fox FOX Dog dog DOG Cat cat."
    custom = {"FoX", "DOG"}                       # intentionally mixed case
    r, u = word_frequency(txt, stopwords=custom, top_k=10)
    print("  stopwords = {'FoX', 'DOG'}  →  only 'cat' should survive:")
    print_unigrams(r, u)

    # --- Test 6: bigram with stopword filtering ------------------------
    print("\n📌 Test 6: Bigrams after stopword filtering")
    print("-" * 70)
    text6 = "The quick brown fox jumps over the lazy dog. The quick fox runs."
    bg, ub = bigram_frequency(text6, top_k=5)
    print("  Input:", text6)
    print()
    print_bigrams(bg, ub)

    print("\n" + "=" * 70)
    print("All tests completed without crashing. ✅")
    print("=" * 70)