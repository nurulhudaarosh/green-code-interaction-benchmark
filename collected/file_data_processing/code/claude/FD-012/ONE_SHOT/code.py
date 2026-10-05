#!/usr/bin/env python3
"""
Offline text analyzer.

Recursively reads .txt files under one or more paths, case-folds alphabetic
words, counts total occurrences and document frequency (number of files each
word appears in), and prints a deterministic ranking.

Ranking order (all ties broken deterministically):
    1. total count            (descending)
    2. document frequency     (descending)
    3. word                   (ascending, by code point)

Usage:
    python text_analyzer.py PATH [PATH ...] [-n TOP] [--min-count N]
                            [--encoding ENC] [--format {table,tsv,json}]
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from typing import Dict, Iterable, List, Tuple

# A "word" is a maximal run of Unicode letters, optionally joined by internal
# apostrophes (e.g. "don't", "o'clock"). Digits and underscores are excluded.
# [^\W\d_] matches any Unicode letter.
WORD_RE = re.compile(r"[^\W\d_]+(?:['\u2019][^\W\d_]+)*")


def find_txt_files(paths: Iterable[str]) -> List[str]:
    """Recursively collect .txt files (case-insensitive extension), sorted and de-duplicated."""
    found = set()
    for p in paths:
        if os.path.isfile(p):
            if p.lower().endswith(".txt"):
                found.add(os.path.realpath(p))
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p, followlinks=False):
                dirs.sort()
                for name in sorted(files):
                    if name.lower().endswith(".txt"):
                        found.add(os.path.realpath(os.path.join(root, name)))
        else:
            print(f"warning: skipping missing path: {p}", file=sys.stderr)
    return sorted(found)


def read_text(path: str, encoding: str) -> str:
    """Read a file; undecodable bytes are replaced so results stay deterministic."""
    with open(path, "r", encoding=encoding, errors="replace", newline=None) as fh:
        return fh.read()


def tokenize(text: str) -> List[str]:
    """Normalize, extract alphabetic words, and case-fold them."""
    text = unicodedata.normalize("NFKC", text)
    words = []
    for m in WORD_RE.finditer(text):
        w = m.group(0).replace("\u2019", "'").casefold()
        words.append(w)
    return words


def analyze(files: List[str], encoding: str) -> Tuple[Dict[str, int], Dict[str, int], int]:
    """Return (total_counts, doc_freq, files_processed)."""
    total: Counter = Counter()
    docfreq: Counter = Counter()
    processed = 0
    for path in files:
        try:
            text = read_text(path, encoding)
        except OSError as exc:
            print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
            continue
        words = tokenize(text)
        processed += 1
        total.update(words)
        docfreq.update(set(words))
    return total, docfreq, processed


def rank(total: Dict[str, int], docfreq: Dict[str, int], min_count: int) -> List[Tuple[str, int, int]]:
    rows = [(w, c, docfreq[w]) for w, c in total.items() if c >= min_count]
    rows.sort(key=lambda r: (-r[1], -r[2], r[0]))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Offline word frequency analyzer for .txt files.")
    ap.add_argument("paths", nargs="+", help="files or directories to scan recursively")
    ap.add_argument("-n", "--top", type=int, default=50, help="number of words to show (0 = all; default 50)")
    ap.add_argument("--min-count", type=int, default=1, help="minimum total occurrences to include")
    ap.add_argument("--encoding", default="utf-8", help="input encoding (default utf-8)")
    ap.add_argument("--format", choices=["table", "tsv", "json"], default="table", help="output format")
    args = ap.parse_args(argv)

    if args.top < 0 or args.min_count < 1:
        ap.error("--top must be >= 0 and --min-count must be >= 1")

    files = find_txt_files(args.paths)
    if not files:
        print("error: no .txt files found", file=sys.stderr)
        return 1

    total, docfreq, processed = analyze(files, args.encoding)
    rows = rank(total, docfreq, args.min_count)
    shown = rows if args.top == 0 else rows[: args.top]

    if args.format == "json":
        out = {
            "files_processed": processed,
            "total_words": sum(total.values()),
            "unique_words": len(total),
            "ranking": [
                {"rank": i, "word": w, "count": c, "doc_freq": d}
                for i, (w, c, d) in enumerate(shown, 1)
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    elif args.format == "tsv":
        print("rank\tword\tcount\tdoc_freq")
        for i, (w, c, d) in enumerate(shown, 1):
            print(f"{i}\t{w}\t{c}\t{d}")
    else:
        print(f"Files processed: {processed}")
        print(f"Total words:     {sum(total.values())}")
        print(f"Unique words:    {len(total)}")
        print()
        width = max([len(w) for w, _, _ in shown] + [4])
        print(f"{'Rank':>5}  {'Word':<{width}}  {'Count':>8}  {'DocFreq':>8}")
        print(f"{'-' * 5}  {'-' * width}  {'-' * 8}  {'-' * 8}")
        for i, (w, c, d) in enumerate(shown, 1):
            print(f"{i:>5}  {w:<{width}}  {c:>8}  {d:>8}")

    return 0


if __name__ == "__main__":
    sys.exit(main())