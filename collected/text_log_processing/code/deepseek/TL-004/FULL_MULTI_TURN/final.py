import re
from collections import Counter
from typing import List, Tuple, Set, Optional, Iterable


# ----------------------------------------------------------------------
# Built-in stopword list (common English stopwords) — all lowercase.
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
# Small helpers
# ----------------------------------------------------------------------
def _coerce_top_k(top_k: Optional[int]) -> int:
    """
    Normalize top_k to a non-negative int.

    - None              -> 0
    - non-int / bool    -> 0   (bool is int subclass; treat as invalid)
    - float             -> int(truncated), clamped at 0
    - negative / NaN    -> 0
    - huge values       -> left as-is; slicing handles overflow safely
    """
    if top_k is None:
        return 0
    if isinstance(top_k, bool):
        return 0
    if isinstance(top_k, int):
        return max(top_k, 0)
    if isinstance(top_k, float):
        if top_k != top_k:          # NaN check
            return 0
        if top_k == float("inf"):
            return 2**31 - 1
        return max(int(top_k), 0)
    return 0


def _normalize_stopwords(stopwords: Optional[Iterable[str]]) -> Set[str]:
    """
    Return a lowercase set of stopwords. Always safe to call — never None.

    - None               -> empty set (caller decides whether to use defaults)
    - non-string entries -> skipped
    - mixed case         -> lowercased
    - empty strings      -> skipped
    """
    if not stopwords:
        return set()
    out = set()
    for word in stopwords:
        if isinstance(word, str) and word:
            out.add(word.lower())
    return out


# ----------------------------------------------------------------------
# Text loading
# ----------------------------------------------------------------------
def load_text(source: Optional[str] = None, path: Optional[str] = None) -> str:
    """Load text from string or file; return "" on any failure."""
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
    """Turn raw text into a flat list of word tokens. Safe on None/empty."""
    if not text or not isinstance(text, str):
        return []

    if lowercase:
        text = text.lower()

    if strip_punct:
        text = re.sub(r"[^\w']", " ", text, flags=re.UNICODE)

    tokens = []
    for tok in text.split():
        tok = tok.strip("'")
        if tok:
            tokens.append(tok)
    return tokens


# ----------------------------------------------------------------------
# Filtering
# ----------------------------------------------------------------------
def _filter_tokens(
    tokens: Iterable[str],
    stopwords: Set[str],
    filter_stopwords: bool,
    min_word_length: int,
) -> List[str]:
    """Apply stopword + length filters. Stopwords are lowercase-matched."""
    stops = stopwords if filter_stopwords else set()
    if min_word_length < 0:
        min_word_length = 0

    out = []
    for tok in tokens:
        if len(tok) < min_word_length:
            continue
        if filter_stopwords and tok.lower() in stops:
            continue
        out.append(tok)
    return out


# ----------------------------------------------------------------------
# Unigram frequency
# ----------------------------------------------------------------------
def word_frequency(
    text: str,
    stopwords: Optional[Set[str]] = None,
    top_k: int = 10,
    filter_stopwords: bool = True,
    min_word_length: int = 1,
) -> Tuple[List[Tuple[str, int]], int]:
    """
    Top-k unigrams after case-insensitive stopword filtering.

    Edge cases handled:
        * text is None / "" / whitespace-only      -> ([], 0)
        * stopwords is None                        -> DEFAULT_STOPWORDS
        * stopwords has mixed case / non-strings   -> normalized
        * top_k is None / negative / float / huge  -> coerced, then sliced
        * top_k > vocab size                       -> returns full vocab
        * empty vocabulary after filtering         -> ([], 0)
    """
    # Normalize stopwords; None means "use defaults".
    if stopwords is None:
        stops = set(DEFAULT_STOPWORDS)
    else:
        stops = _normalize_stopwords(stopwords)

    k = _coerce_top_k(top_k)

    # Empty input short-circuit — avoids touching Counter entirely.
    if not text:
        return [], 0

    tokens = tokenize(text)
    filtered = _filter_tokens(tokens, stops, filter_stopwords, min_word_length)

    # Empty vocabulary after filtering — top_k may be huge, but we must
    # return [] with unique=0 rather than trying to slice nothing.
    if not filtered:
        return [], 0

    counter = Counter(filtered)
    sorted_items = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return sorted_items[:k], len(counter)          # slicing never raises


# ----------------------------------------------------------------------
# Bigram frequency
# ----------------------------------------------------------------------
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
    Top-k bigrams after stopword filtering.

    Edge cases handled:
        * text is None / "" / whitespace-only      -> ([], 0)
        * fewer than 2 tokens after filtering      -> ([], 0)
        * top_k oversized                          -> returns all bigrams
        * cross_line=False                         -> no pairs cross newlines
    """
    if stopwords is None:
        stops = set(DEFAULT_STOPWORDS)
    else:
        stops = _normalize_stopwords(stopwords)

    k = _coerce_top_k(top_k)

    if not text:
        return [], 0

    if cross_line:
        flat = re.sub(r"\s+", " ", text)
        tokens = tokenize(flat)
    else:
        tokens = []
        for line in text.splitlines():
            tokens.extend(tokenize(line))

    filtered = _filter_tokens(tokens, stops, filter_stopwords, min_word_length)

    # Empty vocab, or only one token → no bigrams possible.
    if len(filtered) < 2:
        return [], 0

    bigrams = list(zip(filtered, filtered[1:]))
    counter = Counter(bigrams)
    sorted_items = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return sorted_items[:k], len(counter)


# ----------------------------------------------------------------------
# Pretty printers
# ----------------------------------------------------------------------
def print_unigrams(
    results: List[Tuple[str, int]],
    total_unique: int = 0,
    requested_k: Optional[int] = None,
) -> None:
    if not results:
        note = ""
        if requested_k is not None and requested_k > 0:
            note = "  (empty vocabulary — nothing to rank)"
        print(f"  (no words found after filtering){note}")
        return

    ww = max(max(len(w) for w, _ in results), 6)
    cw = max(max(len(str(c)) for _, c in results), 5)

    print(f"  {'Rank':<5} {'Word':<{ww}} {'Count':>{cw}}")
    print(f"  {'-'*5} {'-'*ww} {'-'*cw}")
    for rank, (word, count) in enumerate(results, start=1):
        print(f"  {rank:<5} {word:<{ww}} {count:>{cw}}")

    if total_unique:
        shown = len(results)
        if requested_k is not None and requested_k > total_unique:
            print(f"\n  (unique words after filtering: {total_unique}; "
                  f"requested top_k={requested_k} → returning all {shown})")
        else:
            print(f"\n  (unique words after filtering: {total_unique})")


def print_bigrams(
    results: List[Tuple[Tuple[str, str], int]],
    total_unique: int = 0,
    requested_k: Optional[int] = None,
) -> None:
    if not results:
        print("  (no bigrams found after filtering)")
        return

    labels = [f"{a} {b}" for (a, b), _ in results]
    lw = max(max(len(s) for s in labels), 14)
    cw = max(max(len(str(c)) for _, c in results), 5)

    print(f"  {'Rank':<5} {'Bigram':<{lw}} {'Count':>{cw}}")
    print(f"  {'-'*5} {'-'*lw} {'-'*cw}")
    for rank, ((a, b), count) in enumerate(results, start=1):
        print(f"  {rank:<5} {f'{a} {b}':<{lw}} {count:>{cw}}")

    if total_unique:
        shown = len(results)
        if requested_k is not None and requested_k > total_unique:
            print(f"\n  (unique bigrams: {total_unique}; "
                  f"requested top_k={requested_k} → returning all {shown})")
        else:
            print(f"\n  (unique bigrams: {total_unique})")


# ----------------------------------------------------------------------
# Self-tests
# ----------------------------------------------------------------------
def _run_tests() -> None:
    print("=" * 72)
    print("EDGE-CASE HARDENING — empty vocab + oversized top_k")
    print("=" * 72)

    # --- Case A: empty vocab from empty input ---------------------------
    print("\n📌 A. Empty input → empty vocab, any top_k")
    print("-" * 72)
    for label, payload in [
        ("empty string", ""),
        ("None",         None),
        ("whitespace",   "   \n\t  "),
        ("punct-only",   "!!! ??? ,,, ..."),
    ]:
        for k in [0, 1, 10, 10**9, -5, None]:
            r, u = word_frequency(payload, top_k=k)              # type: ignore[arg-type]
            b, ub = bigram_frequency(payload, top_k=k)           # type: ignore[arg-type]
            assert r == [] and u == 0, f"unigram fail: {label}, k={k} -> {r}, {u}"
            assert b == [] and ub == 0, f"bigram fail: {label}, k={k} -> {b}, {ub}"
        print(f"  {label:<14} -> all top_k values returned ([], 0)  ✅")

    # --- Case B: all tokens filtered out → empty vocab ------------------
    print("\n📌 B. All tokens removed by stopwords → empty vocab")
    print("-" * 72)
    all_stops = "the and or but if then so for nor yet"
    for k in [0, 3, 10**9]:
        r, u = word_frequency(all_stops, top_k=k)
        b, ub = bigram_frequency(all_stops, top_k=k)
        assert r == [] and u == 0
        assert b == [] and ub == 0
    print(f"  input={all_stops!r}")
    print(f"  -> every top_k returned ([], 0)  ✅")

    # --- Case C: oversized top_k on tiny vocab --------------------------
    print("\n📌 C. Oversized top_k on small vocab (should return full vocab)")
    print("-" * 72)
    tiny = "alpha beta gamma alpha"
    for k in [5, 50, 10**6, 10**9]:
        r, u = word_frequency(tiny, top_k=k)
        assert u == 3, f"unique should be 3, got {u}"
        assert len(r) == 3, f"expected 3 results, got {len(r)}"
        # Sorted by (-count, word): alpha(2), beta(1), gamma(1)
        assert [w for w, _ in r] == ["alpha", "beta", "gamma"]
    print(f"  input={tiny!r}")
    print(f"  top_k ∈ {{5, 50, 1e6, 1e9}} -> always 3 results  ✅")

    # --- Case D: oversized top_k on bigrams -----------------------------
    print("\n📌 D. Oversized top_k on bigrams")
    print("-" * 72)
    txt = "one two three four five"
    for k in [100, 10**9]:
        b, ub = bigram_frequency(txt, top_k=k)
        assert ub == 4, f"expected 4 unique bigrams, got {ub}"
        assert len(b) == 4
    print(f"  input={txt!r}")
    print(f"  top_k ∈ {{100, 1e9}} -> always 4 bigrams  ✅")

    # --- Case E: top_k = 0 ----------------------------------------------
    print("\n📌 E. top_k = 0 → empty results, vocab size still reported")
    print("-" * 72)
    r, u = word_frequency("alpha beta gamma alpha", top_k=0)
    b, ub = bigram_frequency("one two three four", top_k=0)
    assert r == [] and u == 3, f"got r={r}, u={u}"
    assert b == [] and ub == 3, f"got b={b}, ub={ub}"
    print(f"  unigram: results={r}, unique={u}  ✅")
    print(f"  bigram:  results={b}, unique={ub}  ✅")

    # --- Case F: invalid top_k types ------------------------------------
    print("\n📌 F. Invalid top_k types are coerced safely")
    print("-" * 72)
    for k in [None, -3, 3.7, float("nan"), float("inf"), "10", True]:
        r, u = word_frequency("alpha beta gamma alpha", top_k=k)   # type: ignore[arg-type]
        print(f"  top_k={str(k):<10} -> results={len(r)}, unique={u}")
    print("  (no crash; non-int / negative / NaN → 0, inf → huge, float→truncated)  ✅")

    # --- Case G: empty vocab + non-empty stopwords ----------------------
    print("\n📌 G. Empty vocab with explicit (non-default) stopwords")
    print("-" * 72)
    text = "the and or"
    r, u = word_frequency(text, stopwords={"THE", "and", "OR"}, top_k=10**9)
    assert r == [] and u == 0
    print(f"  text={text!r}, stopwords={{'THE','and','OR'}}")
    print(f"  -> ([], 0)  ✅  (case-insensitive stopword matching)")

    # --- Case H: realistic oversized request ----------------------------
    print("\n📌 H. Realistic text, top_k larger than vocab")
    print("-" * 72)
    text = (
        "the quick brown fox jumps over the lazy dog "
        "the quick fox runs"
    )
    r, u = word_frequency(text, top_k=1000)
    print_unigrams(r, u, requested_k=1000)

    print("\n" + "=" * 72)
    print("All edge-case tests passed. ✅")
    print("=" * 72)


if __name__ == "__main__":
    _run_tests()