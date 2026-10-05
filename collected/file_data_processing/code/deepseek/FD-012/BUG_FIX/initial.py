#!/usr/bin/env python3
"""
Offline Text Analyzer
- Recursively reads .txt files from a directory
- Case-folds alphabetic words
- Counts total occurrences and document frequency
- Ranks words deterministically
"""

import os
import re
import sys
import argparse
from collections import defaultdict

# Match sequences of alphabetic characters (Unicode-aware), case-folded later
WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


def find_txt_files(root):
    """Recursively yield paths to .txt files under root, sorted for determinism."""
    collected = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            if name.lower().endswith(".txt"):
                collected.append(os.path.join(dirpath, name))
    # Sort full paths for deterministic traversal order
    collected.sort()
    return collected


def analyze_file(path, total_counts, doc_freq):
    """Process a single file: update total_counts and doc_freq."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as e:
        print(f"warning: could not read {path}: {e}", file=sys.stderr)
        return False

    words = WORD_RE.findall(text)
    if not words:
        return True

    # Case-fold every word for canonical form
    folded = [w.casefold() for w in words]

    # Total occurrences
    for w in folded:
        total_counts[w] += 1

    # Document frequency: each unique word counted once per document
    for w in set(folded):
        doc_freq[w] += 1

    return True


def rank_words(total_counts, doc_freq, top_n=None):
    """
    Deterministic ranking:
    Primary: total occurrences (desc)
    Secondary: document frequency (desc)
    Tertiary: word lexicographically (asc)
    """
    words = sorted(
        total_counts.keys(),
        key=lambda w: (-total_counts[w], -doc_freq[w], w),
    )
    if top_n is not None:
        words = words[:top_n]
    return words


def main():
    parser = argparse.ArgumentParser(
        description="Offline recursive .txt word analyzer."
    )
    parser.add_argument("directory", help="Root directory to scan recursively")
    parser.add_argument(
        "-n", "--top", type=int, default=None,
        help="Show only the top N words (default: all)"
    )
    parser.add_argument(
        "--min-count", type=int, default=1,
        help="Only report words with at least this many total occurrences"
    )
    parser.add_argument(
        "--min-docs", type=int, default=1,
        help="Only report words appearing in at least this many documents"
    )
    parser.add_argument(
        "--csv", action="store_true",
        help="Output as CSV instead of aligned table"
    )
    args = parser.parse_args()

    root = args.directory
    if not os.path.isdir(root):
        print(f"error: {root} is not a directory", file=sys.stderr)
        sys.exit(1)

    files = find_txt_files(root)
    if not files:
        print(f"no .txt files found under {root}", file=sys.stderr)
        sys.exit(0)

    total_counts = defaultdict(int)
    doc_freq = defaultdict(int)
    files_read = 0

    for path in files:
        if analyze_file(path, total_counts, doc_freq):
            files_read += 1

    # Filter by thresholds
    filtered = {
        w: c for w, c in total_counts.items()
        if c >= args.min_count and doc_freq[w] >= args.min_docs
    }

    ranked = rank_words(filtered, doc_freq, top_n=args.top)

    # Output
    if args.csv:
        print("word,total_occurrences,document_frequency")
        for w in ranked:
            # Escape quotes/commas minimally for CSV safety
            safe = w
            if any(ch in safe for ch in ',"'):
                safe = '"' + safe.replace('"', '""') + '"'
            print(f"{safe},{total_counts[w]},{doc_freq[w]}")
    else:
        if not ranked:
            print("no words matched the given thresholds.")
            return
        word_width = max(len(w) for w in ranked)
        word_width = max(word_width, len("word"))
        header = f"{'word':<{word_width}}  {'total':>10}  {'docs':>10}"
        print(header)
        print("-" * len(header))
        for w in ranked:
            print(f"{w:<{word_width}}  {total_counts[w]:>10}  {doc_freq[w]:>10}")

    # Summary to stderr so stdout stays clean for piping
    print(
        f"\n[summary] files scanned: {len(files)}, "
        f"files read: {files_read}, "
        f"unique words: {len(total_counts)}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()