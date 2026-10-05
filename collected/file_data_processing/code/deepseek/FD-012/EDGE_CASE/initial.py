#!/usr/bin/env python3
"""
Offline Python text analyzer.

Recursively reads .txt files, case-folds alphabetic words, counts total
occurrences and document frequency, and ranks words deterministically.

Usage:
    python text_analyzer.py [directory] [--top N] [--min-df N] [--json]

Defaults:
    directory = current directory
    --top 50
    --min-df 1
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


def iter_txt_files(root: Path) -> Iterable[Path]:
    """Yield all .txt files under root, sorted for deterministic order."""
    for path in sorted(root.rglob("*.txt")):
        if path.is_file():
            yield path


def read_text(path: Path) -> str:
    """Read a text file, trying a few encodings before giving up."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            print(f"warning: could not read {path}: {exc}", file=sys.stderr)
            return ""
    print(f"warning: could not decode {path}", file=sys.stderr)
    return ""


def words_in(text: str) -> Iterable[str]:
    """Yield case-folded alphabetic words from text."""
    for match in WORD_RE.finditer(text):
        yield match.group(0).casefold()


def analyze(root: Path, min_df: int = 1):
    """
    Analyze all .txt files under root.

    Returns:
        total_occurrences: Counter[str]
        doc_frequency: Counter[str]
        num_docs: int
    """
    total_occurrences: Counter[str] = Counter()
    doc_frequency: Counter[str] = Counter()
    num_docs = 0

    for path in iter_txt_files(root):
        num_docs += 1
        text = read_text(path)
        seen_in_doc = set()

        for word in words_in(text):
            total_occurrences[word] += 1
            seen_in_doc.add(word)

        for word in seen_in_doc:
            doc_frequency[word] += 1

    if min_df > 1:
        keep = {w for w, df in doc_frequency.items() if df >= min_df}
        total_occurrences = Counter(
            {w: c for w, c in total_occurrences.items() if w in keep}
        )
        doc_frequency = Counter(
            {w: df for w, df in doc_frequency.items() if w in keep}
        )

    return total_occurrences, doc_frequency, num_docs


def rank_words(total_occurrences: Counter, doc_frequency: Counter, top: int):
    """
    Deterministic ranking.

    Primary: total occurrences (descending)
    Secondary: document frequency (descending)
    Tertiary: word (ascending, lexicographic)
    """
    words = sorted(
        total_occurrences.keys(),
        key=lambda w: (-total_occurrences[w], -doc_frequency[w], w),
    )
    if top is not None:
        words = words[:top]
    return words


def print_report(words, total_occurrences, doc_frequency, num_docs, as_json: bool):
    if as_json:
        payload = {
            "num_documents": num_docs,
            "unique_words": len(total_occurrences),
            "words": [
                {
                    "rank": i + 1,
                    "word": w,
                    "occurrences": total_occurrences[w],
                    "document_frequency": doc_frequency[w],
                }
                for i, w in enumerate(words)
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"Documents analyzed : {num_docs}")
    print(f"Unique words       : {len(total_occurrences)}")
    print()
    if not words:
        print("(no words matched the filter)")
        return

    rank_w = max(len("RANK"), len(str(len(words))))
    word_w = max(len("WORD"), max(len(w) for w in words))
    occ_w = max(len("OCC"), max(len(str(total_occurrences[w])) for w in words))
    df_w = max(len("DF"), max(len(str(doc_frequency[w])) for w in words))

    header = (
        f"{'RANK':>{rank_w}}  "
        f"{'WORD':<{word_w}}  "
        f"{'OCC':>{occ_w}}  "
        f"{'DF':>{df_w}}"
    )
    print(header)
    print("-" * len(header))
    for i, w in enumerate(words, start=1):
        print(
            f"{i:>{rank_w}}  "
            f"{w:<{word_w}}  "
            f"{total_occurrences[w]:>{occ_w}}  "
            f"{doc_frequency[w]:>{df_w}}"
        )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Offline recursive .txt word-frequency analyzer."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan recursively (default: current directory).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=50,
        help="Show top N words (default: 50). Use 0 or a negative value for all.",
    )
    parser.add_argument(
        "--min-df",
        type=int,
        default=1,
        help="Only include words appearing in at least N documents (default: 1).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit results as JSON instead of a text table.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    root = Path(args.directory).expanduser()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    total_occurrences, doc_frequency, num_docs = analyze(root, min_df=args.min_df)

    top = None if args.top is None or args.top <= 0 else args.top
    words = rank_words(total_occurrences, doc_frequency, top)

    print_report(words, total_occurrences, doc_frequency, num_docs, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())