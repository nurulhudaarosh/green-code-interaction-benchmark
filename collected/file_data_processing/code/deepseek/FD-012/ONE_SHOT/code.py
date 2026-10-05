#!/usr/bin/env python3
"""
Offline recursive .txt analyzer.

Features:
  - Recursively scans a directory for *.txt files.
  - Tokenizes alphabetic words, case-folds them (str.casefold).
  - Counts total occurrences and document frequency per word.
  - Ranks deterministically: by total desc, then doc-freq desc, then word asc.

Only standard library is used. No network access.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Iterator, List, Tuple

_TOKEN_SPLIT = re.compile(r"[^\w']+", flags=re.UNICODE)


def iter_txt_files(root: str) -> Iterator[str]:
    """Yield paths of all .txt files under root, recursively, sorted."""
    if os.path.isfile(root):
        if root.lower().endswith(".txt"):
            yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            if name.lower().endswith(".txt"):
                yield os.path.join(dirpath, name)


def tokenize(text: str) -> Iterator[str]:
    """
    Yield case-folded alphabetic tokens.

    A token is a maximal run of alphabetic characters. Apostrophes are
    removed before the alphabetic check so contractions remain single
    tokens. Numbers are ignored entirely.
    """
    for raw in _TOKEN_SPLIT.split(text):
        if not raw:
            continue
        candidate = raw.replace("'", "").replace("\u2019", "")
        if candidate and candidate.isalpha():
            yield candidate.casefold()


@dataclass(frozen=True)
class WordStats:
    word: str
    total_count: int
    doc_freq: int


def analyze(root: str) -> Tuple[List[WordStats], int]:
    """Analyze all .txt files under root; return (sorted stats, doc count)."""
    total_counter: Counter[str] = Counter()
    doc_counter: Counter[str] = Counter()
    doc_count = 0

    for path in iter_txt_files(root):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            print(f"[warn] skipping {path}: {exc}", file=sys.stderr)
            continue

        doc_count += 1
        seen_in_doc: set[str] = set()
        for token in tokenize(text):
            total_counter[token] += 1
            if token not in seen_in_doc:
                seen_in_doc.add(token)
                doc_counter[token] += 1

    stats = [
        WordStats(word=w, total_count=c, doc_freq=doc_counter[w])
        for w, c in total_counter.items()
    ]
    stats.sort(key=lambda s: (-s.total_count, -s.doc_freq, s.word))
    return stats, doc_count


def format_report(stats: List[WordStats], doc_count: int, top: int, min_count: int) -> str:
    lines = []
    lines.append(f"Documents analyzed : {doc_count}")
    lines.append(f"Unique words       : {len(stats)}")
    lines.append("")
    lines.append(f"{'rank':>4}  {'total':>7}  {'docs':>6}  word")
    lines.append("-" * 40)

    rank = 0
    shown = 0
    for s in stats:
        if s.total_count < min_count:
            break
        rank += 1
        if shown >= top:
            break
        shown += 1
        lines.append(f"{rank:>4}  {s.total_count:>7}  {s.doc_freq:>6}  {s.word}")

    if shown == 0:
        lines.append("(no words matched the criteria)")

    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recursively analyze .txt files: case-folded word counts + doc frequency."
    )
    parser.add_argument("directory", help="Root directory (or single .txt file) to scan.")
    parser.add_argument("--top", type=int, default=50,
                        help="Number of top words to display (default: 50).")
    parser.add_argument("--min-count", type=int, default=1,
                        help="Ignore words with total count below this (default: 1).")
    parser.add_argument("--json", metavar="PATH",
                        help="Write full results to a JSON file.")
    args = parser.parse_args(argv)

    if not os.path.exists(args.directory):
        print(f"error: path not found: {args.directory}", file=sys.stderr)
        return 2

    stats, doc_count = analyze(args.directory)
    print(format_report(stats, doc_count, args.top, args.min_count))

    if args.json:
        payload = {
            "root": os.path.abspath(args.directory),
            "documents": doc_count,
            "unique_words": len(stats),
            "words": [asdict(s) for s in stats],
        }
        try:
            with open(args.json, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
            print(f"\nJSON written to {args.json}", file=sys.stderr)
        except OSError as exc:
            print(f"[warn] could not write JSON: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())