#!/usr/bin/env python3
"""Word frequency analyzer: stopword filtering, top-k unigrams and/or bigrams."""

import argparse
import heapq
import re
import sys
from collections import Counter

STOPWORDS = frozenset("""
a about above after again against all am an and any are aren't as at be because
been before being below between both but by can can't cannot could couldn't did
didn't do does doesn't doing don't down during each few for from further had
hadn't has hasn't have haven't having he he'd he'll he's her here here's hers
herself him himself his how how's i i'd i'll i'm i've if in into is isn't it
it's its itself let's me more most mustn't my myself no nor not of off on once
only or other ought our ours ourselves out over own same shan't she she'd
she'll she's should shouldn't so some such than that that's the their theirs
them themselves then there there's these they they'd they'll they're they've
this those through to too under until up very was wasn't we we'd we'll we're
we've were weren't what what's when when's where where's which while who who's
whom why why's with won't would wouldn't you you'd you'll you're you've your
yours yourself yourselves also just will shall may might must us
""".split())

TOKEN_RE = re.compile(r"[a-z]+(?:'[a-z]+|-[a-z]+)*")


def normalize(s: str) -> str:
    return s.casefold().replace("\u2019", "'").replace("\u2018", "'")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(normalize(text))


def _keep(word, stop, min_len):
    return len(word) >= min_len and word not in stop


def _top_k(counts: Counter, k: int) -> list[tuple[str, int]]:
    """Top-k by count desc, then alphabetical. Safe for empty counters,
    k <= 0 (returns []), and k larger than the vocabulary (returns all)."""
    if not counts or k is None or k <= 0:
        return []
    key = lambda kv: (-kv[1], kv[0])
    if k >= len(counts):
        return sorted(counts.items(), key=key)
    return heapq.nsmallest(k, counts.items(), key=key)


def top_unigrams(tokens, k=10, stop=STOPWORDS, min_len=2):
    return _top_k(Counter(w for w in tokens if _keep(w, stop, min_len)), k)


def top_bigrams(tokens, k=10, stop=STOPWORDS, min_len=2, filter_bigrams=True):
    if filter_bigrams:
        pairs = ((a, b) for a, b in zip(tokens, tokens[1:])
                 if _keep(a, stop, min_len) and _keep(b, stop, min_len))
    else:
        pairs = zip(tokens, tokens[1:])
    return _top_k(Counter(f"{a} {b}" for a, b in pairs), k)


def positive_int(value: str) -> int:
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return n


def print_table(label, rows, k):
    shown = len(rows)
    if shown == 0:
        print(f"\nTop {k} {label}\n  (none after filtering)")
        return
    note = f" (only {shown} available)" if shown < k else ""
    print(f"\nTop {min(k, shown)} {label}{note}")
    for rank, (item, n) in enumerate(rows, 1):
        print(f"{rank:>3}. {item:<28} {n}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("file", nargs="?", help="input file (default: stdin)")
    p.add_argument("-m", "--mode", choices=["unigram", "bigram", "both"],
                   default="both")
    p.add_argument("-k", type=positive_int, default=10, help="top-k size")
    p.add_argument("--min-len", type=positive_int, default=2)
    p.add_argument("--no-stopwords", action="store_true")
    p.add_argument("--extra-stop", nargs="*", default=[])
    p.add_argument("--keep-stop-bigrams", action="store_true")
    args = p.parse_args()

    try:
        if args.file:
            with open(args.file, encoding="utf-8-sig", errors="replace") as f:
                text = f.read()
        else:
            text = sys.stdin.read()
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    tokens = tokenize(text)
    if not tokens:
        print("No words found in input.", file=sys.stderr)
        return 0

    stop = frozenset() if args.no_stopwords else (
        STOPWORDS | {normalize(w) for w in args.extra_stop}
    )

    if args.mode in ("unigram", "both"):
        print_table("unigrams",
                    top_unigrams(tokens, args.k, stop, args.min_len), args.k)
    if args.mode in ("bigram", "both"):
        print_table("bigrams",
                    top_bigrams(tokens, args.k, stop, args.min_len,
                                filter_bigrams=not args.keep_stop_bigrams),
                    args.k)
    return 0


if __name__ == "__main__":
    sys.exit(main())