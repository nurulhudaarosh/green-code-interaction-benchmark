#!/usr/bin/env python3
"""
Offline recursive text analyzer.

- Recursively scans a directory for .txt files.
- Tokenizes each file into Unicode alphabetic words, case-folded.
- Counts:
    * total occurrences across all files
    * document frequency (number of files in which the word appears;
      repeated occurrences within a single file count only once)
- Ranks words deterministically by:
    1. document frequency (descending)
    2. total occurrences (descending)
    3. word (ascending, lexicographic on the case-folded form)

Usage:
    python analyzer.py <directory> [--top N] [--min-count N] [--json]

No third-party dependencies.

Tokenization / case-folding notes
---------------------------------
The goal is a *consistent* notion of "word" across all scripts and cases.

1. We treat the Unicode property "Alphabetic" (PropList / DerivedCoreProperties)
   as the definition of a word character. Python's `re` does not expose
   `\p{Alphabetic}` directly, but `str.isalpha()` is defined via that property
   for the characters Python knows about, and we can iterate codepoints
   manually for full control.

2. We case-fold with `str.casefold()`, which is the Unicode-recommended
   caseless comparison operation. It is more aggressive than `.lower()`:
   e.g. 'ß' -> 'ss', 'İ' -> 'i̇', 'Σ' -> 'σ' at word end. This makes
   "STRASSE", "straße", and "Strasse" all collapse to "strasse".

3. Case folding can expand a single character into multiple characters
   (e.g. 'ß' -> 'ss', 'ﬀ' -> 'ff'). Those expansions are letters, so the
   folded form remains a valid word.

4. Case folding can also *introduce* characters that are not themselves
   alphabetic in the source (rare). We filter post-fold: the folded form
   must consist entirely of alphabetic characters. This guarantees the
   counting keys are always case-folded alphabetic strings, so mixed-case
   and Unicode inputs are handled consistently.

5. Diacritics: we do NOT strip them by default. "café" and "cafe" are
   different words. This is deliberate — stripping diacritics would merge
   distinct words in many languages (French "cote"/"côte", Turkish
   "sık"/"sik", etc.). If you want NFD + combining-mark removal, pass
   `--strip-diacritics`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

def _is_word_char(ch: str) -> bool:
    """
    True if `ch` counts as a word character for tokenization.

    Uses Unicode general category:
      - L*  = letters (Lu, Ll, Lt, Lm, Lo)
      - Nl  = letter numbers (e.g. Roman numerals like Ⅻ)
      - Mn, Mc, Me = combining marks, so that e.g. Devanagari and Arabic
                     vocalization stay attached to their base letter.

    We intentionally EXCLUDE digits (Nd) so that "abc123" splits into
    "abc" and "123", and "123" is dropped entirely.
    """
    cat = unicodedata.category(ch)
    return (
        cat.startswith("L")
        or cat == "Nl"
        or cat in ("Mn", "Mc", "Me")
    )


def _normalize(ch: str, strip_diacritics: bool) -> str:
    """
    Apply NFC normalization to a single character, optionally stripping
    combining marks (NFD decomposition with marks removed).
    """
    if strip_diacritics:
        decomposed = unicodedata.normalize("NFD", ch)
        return "".join(
            c for c in decomposed
            if unicodedata.category(c) not in ("Mn", "Mc", "Me")
        )
    return unicodedata.normalize("NFC", ch)


def tokenize(text: str, *, strip_diacritics: bool = False) -> Iterator[str]:
    """
    Yield case-folded Unicode alphabetic words from `text`.

    Steps per word:
      1. Split on non-word characters (see `_is_word_char`).
      2. Normalize each character (NFC, or NFD+strip marks).
      3. Case-fold the whole word with str.casefold().
      4. Re-verify the folded form is entirely word characters; drop if not.
    """
    buffer: list[str] = []

    def flush() -> Iterator[str]:
        if not buffer:
            return
        raw = "".join(buffer)
        buffer.clear()

        # Normalize first, then case-fold. Folding after normalization is
        # the Unicode-recommended order and avoids surprises with combining
        # sequences.
        if strip_diacritics:
            raw = "".join(
                _normalize(c, True) for c in raw
            )
        else:
            raw = unicodedata.normalize("NFC", raw)

        folded = raw.casefold()

        # Post-fold validation: every character of the folded form must be
        # a word character (letter / letter-number / combining mark). This
        # drops pathological cases where case folding produces non-letters.
        if not folded:
            return
        if not all(_is_word_char(c) for c in folded):
            return

        yield folded

    for ch in text:
        if _is_word_char(ch):
            buffer.append(ch)
        else:
            yield from flush()
    yield from flush()


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class WordStats:
    word: str
    total: int = 0
    doc_freq: int = 0

    def as_dict(self) -> dict:
        return {
            "word": self.word,
            "total": self.total,
            "doc_freq": self.doc_freq,
        }


@dataclass
class AnalysisResult:
    files_scanned: int = 0
    files_skipped: int = 0
    total_tokens: int = 0
    unique_words: int = 0
    words: list[WordStats] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "files_scanned": self.files_scanned,
            "files_skipped": self.files_skipped,
            "total_tokens": self.total_tokens,
            "unique_words": self.unique_words,
            "words": [w.as_dict() for w in self.words],
        }


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def find_txt_files(root: Path) -> Iterator[Path]:
    """
    Recursively yield .txt files under `root`.

    - Does not follow symlink loops (os.walk default behavior).
    - Sorted for deterministic traversal order.
    - Case-insensitive extension match (".TXT" is included).
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            if name.lower().endswith(".txt"):
                yield Path(dirpath) / name


def read_text(path: Path) -> str | None:
    """
    Read a text file with a cascade of encodings.

    Returns None if the file cannot be decoded or read.
    """
    encodings = ("utf-8", "utf-8-sig", "utf-16", "latin-1")
    try:
        raw = path.read_bytes()
    except OSError:
        return None

    for enc in encodings:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return None


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def analyze(root: Path, *, strip_diacritics: bool = False) -> AnalysisResult:
    """
    Walk `root`, tokenize every .txt file, and aggregate statistics.

    For each file:
      - Every token occurrence increments `totals[word]`.
      - Each distinct word in the file increments `doc_freq[word]` exactly
        once, regardless of how many times it appears in that file.
    """
    totals: Counter[str] = Counter()
    doc_freq: Counter[str] = Counter()

    result = AnalysisResult()

    for path in find_txt_files(root):
        text = read_text(path)
        if text is None:
            result.files_skipped += 1
            continue

        result.files_scanned += 1

        # Single pass: collect occurrences AND the set of distinct words
        # in this file.
        seen_in_doc: set[str] = set()
        for token in tokenize(text, strip_diacritics=strip_diacritics):
            totals[token] += 1
            result.total_tokens += 1
            seen_in_doc.add(token)

        # Document frequency: each distinct word of this file counts once.
        for token in seen_in_doc:
            doc_freq[token] += 1

    # Deterministic ranking:
    #   1. document frequency, descending
    #   2. total occurrences, descending
    #   3. word, ascending (lexicographic on the case-folded form)
    ordered = sorted(
        totals.keys(),
        key=lambda w: (-doc_freq[w], -totals[w], w),
    )

    result.unique_words = len(ordered)
    result.words = [
        WordStats(word=w, total=totals[w], doc_freq=doc_freq[w])
        for w in ordered
    ]
    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def format_report(result: AnalysisResult, top: int | None, min_count: int) -> str:
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("Text Analysis Report")
    lines.append("=" * 72)
    lines.append(f"Files scanned : {result.files_scanned}")
    lines.append(f"Files skipped : {result.files_skipped} (unreadable/undecodable)")
    lines.append(f"Total tokens  : {result.total_tokens}")
    lines.append(f"Unique words  : {result.unique_words}")
    lines.append("-" * 72)
    lines.append(f"{'RANK':>4}  {'WORD':<30}  {'DOC_FREQ':>10}  {'TOTAL':>10}")
    lines.append("-" * 72)

    shown = 0
    for rank, w in enumerate(result.words, start=1):
        if w.total < min_count:
            continue
        if top is not None and shown >= top:
            break
        display = w.word if len(w.word) <= 30 else w.word[:27] + "..."
        lines.append(f"{rank:>4}  {display:<30}  {w.doc_freq:>10}  {w.total:>10}")
        shown += 1

    if shown == 0:
        lines.append("(no words matched the filters)")

    lines.append("-" * 72)
    lines.append(f"Displayed: {shown} word(s)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline recursive .txt word analyzer.",
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Root directory to scan recursively for .txt files.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="Show only the top N words (default: all).",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=1,
        metavar="N",
        help="Only include words with at least N total occurrences (default: 1).",
    )
    parser.add_argument(
        "--strip-diacritics",
        action="store_true",
        help=(
            "Remove combining marks (NFD + strip Mn/Mc/Me) before case folding. "
            "Merges 'café' and 'cafe'. Off by default."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable table.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root: Path = args.directory
    if not root.exists():
        print(f"error: path does not exist: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    result = analyze(root, strip_diacritics=args.strip_diacritics)

    if args.json:
        payload = result.as_dict()
        if args.min_count > 1:
            payload["words"] = [
                w for w in payload["words"] if w["total"] >= args.min_count
            ]
        if args.top is not None:
            payload["words"] = payload["words"][: args.top]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_report(result, top=args.top, min_count=args.min_count))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())