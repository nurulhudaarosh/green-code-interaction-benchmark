#!/usr/bin/env python3
"""
Offline Python text analyzer.

Recursively reads .txt files, case-folds Unicode alphabetic words,
counts total occurrences and document frequency, and ranks words
deterministically.

Consistency guarantees:
  * Tokenization uses Unicode-aware alphabetic matching (str.isalpha),
    so letters like é, ñ, ü, ø, æ, ß, α, ж, 漢, ひ, 한 are treated as
    word characters. Digits, underscores, and punctuation are separators.
  * Case folding uses str.casefold(), the Unicode-correct case fold.
    Both the tokenizer and the counter operate on the folded form, so
    "Straße", "STRASSE", and "strasse" collapse to the same key.
  * A single canonical function (fold_and_tokenize) is the ONLY place
    folding/tokenization logic lives, so counts and DF cannot diverge.

Usage:
    python text_analyzer.py [directory] [--top N] [--min-df N] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator

# ---------------------------------------------------------------------------
# Tokenization + case folding
# ---------------------------------------------------------------------------

def _is_word_char(ch: str) -> bool:
    """
    A character is a word character if it is alphabetic in the Unicode
    sense. This keeps letters from every script and excludes digits,
    underscores, and all punctuation/symbols.
    """
    return ch.isalpha()


def fold_and_tokenize(text: str) -> Iterator[str]:
    """
    Yield case-folded Unicode alphabetic tokens from text.

    The tokenizer scans the ORIGINAL text (so isalpha is applied to the
    real code points), then folds each token with str.casefold().

    Folding at the token level (rather than folding the whole document
    first) avoids casefold expansions such as 'ß' -> 'ss' or 'İ' -> 'i̇'
    creating or destroying word boundaries unexpectedly. Every consumer
    of tokens goes through this function, so counts and document
    frequency always see identical keys.
    """
    buf: list[str] = []
    for ch in text:
        if _is_word_char(ch):
            buf.append(ch)
        elif buf:
            yield "".join(buf).casefold()
            buf.clear()
    if buf:
        yield "".join(buf).casefold()


def normalize_key(word: str) -> str:
    """
    Canonicalize a folded token for stable counting and deterministic
    ordering. NFC normalization keeps combining sequences (e.g. 'e' +
    U+0301) and precomposed forms ('é') in a single canonical form.
    """
    return unicodedata.normalize("NFC", word)


# ---------------------------------------------------------------------------
# File discovery + reading
# ---------------------------------------------------------------------------

def iter_txt_files(root: Path) -> Iterable[Path]:
    """Yield all .txt files under root, sorted for deterministic order."""
    for path in sorted(root.rglob("*.txt")):
        if path.is_file():
            yield path


def read_text(path: Path) -> str:
    """Read a text file, trying a few encodings before giving up."""
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            print(f"warning: could not read {path}: {exc}", file=sys.stderr)
            return ""
    print(f"warning: could not decode {path}", file=sys.stderr)
    return ""


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze(root: Path, min_df: int = 1):
    """
    Analyze all .txt files under root.

    Returns:
        total_occurrences: Counter[str]   (folded, NFC-normalized token -> count)
        doc_frequency:     Counter[str]   (folded, NFC-normalized token -> #docs)
        num_docs:          int
    """
    total_occurrences: Counter[str] = Counter()
    doc_frequency: Counter[str] = Counter()
    num_docs = 0

    for path in iter_txt_files(root):
        num_docs += 1
        text = read_text(path)
        seen_in_doc: set[str] = set()

        for raw_token in fold_and_tokenize(text):
            token = normalize_key(raw_token)
            if not token:
                continue
            total_occurrences[token] += 1
            seen_in_doc.add(token)

        for token in seen_in_doc:
            doc_frequency[token] += 1

    if min_df > 1:
        keep = {w for w, df in doc_frequency.items() if df >= min_df}
        total_occurrences = Counter(
            {w: c for w, c in total_occurrences.items() if w in keep}
        )
        doc_frequency = Counter(
            {w: df for w, df in doc_frequency.items() if w in keep}
        )

    return total_occurrences, doc_frequency, num_docs


# ---------------------------------------------------------------------------
# Ranking + reporting
# ---------------------------------------------------------------------------

def rank_words(
    total_occurrences: Counter[str],
    doc_frequency: Counter[str],
    top: int | None,
) -> list[str]:
    """
    Deterministic ranking.

    Primary:   total occurrences (descending)
    Secondary: document frequency (descending)
    Tertiary:  folded, NFC-normalized word (ascending, Unicode code point order)
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
        # ensure_ascii=False keeps Unicode words readable in the JSON output.
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"Documents analyzed : {num_docs}")
    print(f"Unique words       : {len(total_occurrences)}")
    print()
    if not words:
        print("(no words matched the filter)")
        return

    # Width calculation uses display width to keep columns aligned for
    # CJK and other wide scripts.
    def dwidth(s: str) -> int:
        return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)

    rank_w = max(dwidth("RANK"), len(str(len(words))))
    word_w = max(dwidth("WORD"), max(dwidth(w) for w in words))
    occ_w = max(dwidth("OCC"), max(dwidth(str(total_occurrences[w])) for w in words))
    df_w = max(dwidth("DF"), max(dwidth(str(doc_frequency[w])) for w in words))

    def pad_right(s: str, width: int) -> str:
        return s + " " * (width - dwidth(s))

    def pad_left(s: str, width: int) -> str:
        return " " * (width - dwidth(s)) + s

    header = (
        f"{pad_left('RANK', rank_w)}  "
        f"{pad_right('WORD', word_w)}  "
        f"{pad_left('OCC', occ_w)}  "
        f"{pad_left('DF', df_w)}"
    )
    print(header)
    print("-" * dwidth(header))
    for i, w in enumerate(words, start=1):
        print(
            f"{pad_left(str(i), rank_w)}  "
            f"{pad_right(w, word_w)}  "
            f"{pad_left(str(total_occurrences[w]), occ_w)}  "
            f"{pad_left(str(doc_frequency[w]), df_w)}"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

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