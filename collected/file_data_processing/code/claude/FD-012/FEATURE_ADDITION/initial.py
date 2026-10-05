#!/usr/bin/env python3
"""
Offline text analyzer.

Recursively reads .txt files under one or more paths, case-folds alphabetic
words, and reports total occurrences and document frequency for each word.
Ranking is fully deterministic:

    1. total count            (descending)
    2. document frequency     (descending)
    3. word, code point order (ascending)

Usage:
    python text_analyzer.py PATH [PATH ...] [--top N] [--min-count N]
                            [--encoding ENC] [--format table|tsv|json]
                            [--stopwords FILE]
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple

# A "word" is a run of Unicode letters, optionally joined by single internal
# apostrophes (don't, l'homme). Digits and underscores are not letters, so
# they never appear in a word.
_LETTERS = r"[^\W\d_]+"
WORD_RE = re.compile(rf"{_LETTERS}(?:['\u2019]{_LETTERS})*")


def find_txt_files(paths: Iterable[str]) -> List[str]:
    """Return a sorted, de-duplicated list of .txt files (recursive)."""
    found: Set[str] = set()
    for p in paths:
        if os.path.isfile(p):
            if p.lower().endswith(".txt"):
                found.add(os.path.realpath(p))
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p, followlinks=False):
                dirs.sort()
                for name in files:
                    if name.lower().endswith(".txt"):
                        found.add(os.path.realpath(os.path.join(root, name)))
        else:
            print(f"warning: skipping missing path: {p}", file=sys.stderr)
    return sorted(found)


def read_text(path: str, encoding: str) -> Optional[str]:
    """Read a file; fall back to replacement characters on bad bytes."""
    try:
        with open(path, "r", encoding=encoding, errors="replace") as fh:
            return fh.read()
    except OSError as exc:
        print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
        return None


def tokenize(text: str) -> Iterator[str]:
    """Yield case-folded, NFKC-normalized alphabetic words."""
    text = unicodedata.normalize("NFKC", text)
    for match in WORD_RE.finditer(text):
        word = match.group(0).replace("\u2019", "'").casefold()
        yield word


def analyze(
    files: List[str], encoding: str, stopwords: Set[str]
) -> Tuple[Counter, Counter, int]:
    """Return (total_counts, document_frequency, documents_read)."""
    total: Counter = Counter()
    docfreq: Counter = Counter()
    docs_read = 0
    for path in files:
        text = read_text(path, encoding)
        if text is None:
            continue
        docs_read += 1
        words = [w for w in tokenize(text) if w not in stopwords]
        total.update(words)
        docfreq.update(set(words))
    return total, docfreq, docs_read


def rank(total: Counter, docfreq: Counter, min_count: int) -> List[Tuple[str, int, int]]:
    """Deterministic ranking: count desc, doc freq desc, word asc."""
    rows = [(w, c, docfreq[w]) for w, c in total.items() if c >= min_count]
    rows.sort(key=lambda r: (-r[1], -r[2], r[0]))
    return rows


def load_stopwords(path: Optional[str], encoding: str) -> Set[str]:
    if not path:
        return set()
    text = read_text(path, encoding) or ""
    return set(tokenize(text))


def render(rows: List[Tuple[str, int, int]], fmt: str, docs: int) -> str:
    if fmt == "json":
        return json.dumps(
            [
                {"rank": i, "word": w, "count": c, "doc_freq": d}
                for i, (w, c, d) in enumerate(rows, 1)
            ],
            ensure_ascii=False,
            indent=2,
        )
    if fmt == "tsv":
        lines = ["rank\tword\tcount\tdoc_freq"]
        lines += [f"{i}\t{w}\t{c}\t{d}" for i, (w, c, d) in enumerate(rows, 1)]
        return "\n".join(lines)

    width = max([len(w) for w, _, _ in rows] + [4])
    header = f"{'Rank':>5}  {'Word':<{width}}  {'Count':>9}  {'Docs':>6}  {'Doc%':>6}"
    lines = [header, "-" * len(header)]
    for i, (w, c, d) in enumerate(rows, 1):
        pct = (100.0 * d / docs) if docs else 0.0
        lines.append(f"{i:>5}  {w:<{width}}  {c:>9}  {d:>6}  {pct:>5.1f}%")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Offline recursive text analyzer.")
    ap.add_argument("paths", nargs="+", help="files or directories to scan")
    ap.add_argument("--top", type=int, default=0, help="show only top N (0 = all)")
    ap.add_argument("--min-count", type=int, default=1, help="minimum total count")
    ap.add_argument("--encoding", default="utf-8", help="input encoding (default utf-8)")
    ap.add_argument("--format", choices=["table", "tsv", "json"], default="table")
    ap.add_argument("--stopwords", help="file of words to exclude")
    args = ap.parse_args(argv)

    files = find_txt_files(args.paths)
    if not files:
        print("error: no .txt files found", file=sys.stderr)
        return 1

    stop = load_stopwords(args.stopwords, args.encoding)
    total, docfreq, docs = analyze(files, args.encoding, stop)
    rows = rank(total, docfreq, args.min_count)
    if args.top > 0:
        rows = rows[: args.top]

    print(render(rows, args.format, docs))
    print(
        f"\n{docs} document(s), {sum(total.values())} tokens, "
        f"{len(total)} unique words",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())