#!/usr/bin/env python3
"""
Offline text analyzer.

Recursively reads .txt files under one or more paths, case-folds alphabetic
words, counts total occurrences and document frequency, and ranks words
deterministically.

Ranking order (all ties broken deterministically):
  1. total occurrences        (descending)
  2. document frequency       (descending)
  3. word                     (ascending, by Unicode code point of the case-folded form)

Usage:
    python text_analyzer.py PATH [PATH ...] [--top N] [--min-count N]
                            [--encoding ENC] [--format table|tsv|json]
                            [--output FILE]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator

# Characters allowed inside a word besides letters: apostrophes and hyphens
# are kept only when surrounded by letters (e.g. "don't", "well-known").
_APOSTROPHES = {"'", "\u2019"}
_HYPHENS = {"-", "\u2010"}
_INNER = _APOSTROPHES | _HYPHENS


def normalize_word(word: str) -> str:
    """Case-fold and NFKC-normalize; unify curly apostrophes and hyphens."""
    word = unicodedata.normalize("NFKC", word).casefold()
    for a in _APOSTROPHES:
        word = word.replace(a, "'")
    for h in _HYPHENS:
        word = word.replace(h, "-")
    return word


def tokenize(text: str) -> Iterator[str]:
    """
    Yield case-folded alphabetic words.

    A word is a maximal run of alphabetic characters, optionally joined by a
    single inner apostrophe or hyphen that sits between two letters.
    Digits, underscores, and other symbols act as separators.
    """
    buf: list[str] = []
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]
        if ch.isalpha():
            buf.append(ch)
        elif (
            ch in _INNER
            and buf
            and i + 1 < n
            and text[i + 1].isalpha()
        ):
            buf.append(ch)
        else:
            if buf:
                yield normalize_word("".join(buf))
                buf.clear()
        i += 1
    if buf:
        yield normalize_word("".join(buf))


def find_txt_files(paths: Iterable[str]) -> list[Path]:
    """Recursively collect .txt files (case-insensitive extension), sorted and de-duplicated."""
    found: dict[str, Path] = {}
    for raw in paths:
        p = Path(raw)
        if p.is_file():
            if p.suffix.lower() == ".txt":
                found[os.path.realpath(p)] = p
        elif p.is_dir():
            for root, dirs, files in os.walk(p, followlinks=False):
                dirs.sort()
                for name in sorted(files):
                    if name.lower().endswith(".txt"):
                        fp = Path(root) / name
                        found[os.path.realpath(fp)] = fp
        else:
            print(f"warning: path not found: {raw}", file=sys.stderr)
    return sorted(found.values(), key=lambda x: os.path.realpath(x))


def read_text(path: Path, encoding: str) -> str | None:
    """Read a file; fall back to replacement decoding if strict decoding fails."""
    try:
        with open(path, "r", encoding=encoding, errors="strict", newline=None) as f:
            return f.read()
    except UnicodeDecodeError:
        print(f"warning: {path}: not valid {encoding}; decoding with replacement", file=sys.stderr)
        try:
            with open(path, "r", encoding=encoding, errors="replace", newline=None) as f:
                return f.read()
        except OSError as e:
            print(f"warning: cannot read {path}: {e}", file=sys.stderr)
    except OSError as e:
        print(f"warning: cannot read {path}: {e}", file=sys.stderr)
    return None


def analyze(files: Iterable[Path], encoding: str = "utf-8-sig"):
    """Return (total_counts, doc_freq, docs_read)."""
    total: Counter[str] = Counter()
    docfreq: Counter[str] = Counter()
    docs = 0
    for path in files:
        text = read_text(path, encoding)
        if text is None:
            continue
        docs += 1
        words = Counter(tokenize(text))
        total.update(words)
        docfreq.update(words.keys())  # each word once per document
    return total, docfreq, docs


def rank(total: Counter, docfreq: Counter, min_count: int = 1):
    """Deterministic ranking: count desc, doc freq desc, word asc."""
    rows = [(w, c, docfreq[w]) for w, c in total.items() if c >= min_count]
    rows.sort(key=lambda r: (-r[1], -r[2], r[0]))
    return rows


def render(rows, docs: int, fmt: str) -> str:
    if fmt == "json":
        payload = {
            "documents": docs,
            "words": [
                {"rank": i, "word": w, "total": c, "document_frequency": d}
                for i, (w, c, d) in enumerate(rows, 1)
            ],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)

    if fmt == "tsv":
        lines = ["rank\tword\ttotal\tdocument_frequency"]
        lines += [f"{i}\t{w}\t{c}\t{d}" for i, (w, c, d) in enumerate(rows, 1)]
        return "\n".join(lines)

    # table
    header = ("Rank", "Word", "Total", "Docs")
    body = [(str(i), w, str(c), str(d)) for i, (w, c, d) in enumerate(rows, 1)]
    widths = [len(h) for h in header]
    for row in body:
        for j, cell in enumerate(row):
            widths[j] = max(widths[j], len(cell))
    fmt_row = lambda r: (
        f"{r[0]:>{widths[0]}}  {r[1]:<{widths[1]}}  {r[2]:>{widths[2]}}  {r[3]:>{widths[3]}}"
    )
    out = [fmt_row(header), "  ".join("-" * w for w in widths)]
    out += [fmt_row(r) for r in body]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Offline text analyzer for .txt files.")
    ap.add_argument("paths", nargs="+", help="files or directories to scan recursively")
    ap.add_argument("--top", type=int, default=0, help="show only the top N words (0 = all)")
    ap.add_argument("--min-count", type=int, default=1, help="minimum total occurrences (default 1)")
    ap.add_argument("--encoding", default="utf-8-sig", help="file encoding (default utf-8-sig)")
    ap.add_argument("--format", choices=("table", "tsv", "json"), default="table")
    ap.add_argument("--output", help="write results to this file instead of stdout")
    args = ap.parse_args(argv)

    if args.top < 0 or args.min_count < 1:
        ap.error("--top must be >= 0 and --min-count must be >= 1")

    files = find_txt_files(args.paths)
    if not files:
        print("error: no .txt files found", file=sys.stderr)
        return 1

    total, docfreq, docs = analyze(files, args.encoding)
    rows = rank(total, docfreq, args.min_count)
    if args.top:
        rows = rows[: args.top]

    result = render(rows, docs, args.format)
    summary = (
        f"# documents: {docs}  unique words: {len(total)}  "
        f"total words: {sum(total.values())}"
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="\n") as f:
            f.write(result + "\n")
        print(summary, file=sys.stderr)
    else:
        if args.format == "table":
            print(summary)
        sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
        print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())