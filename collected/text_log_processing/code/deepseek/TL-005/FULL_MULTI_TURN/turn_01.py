#!/usr/bin/env python3
"""
Text normalizer for .txt files with whitespace and Unicode cleanup.

Usage:
    python normalize_text.py input.txt
    python normalize_text.py input.txt -o output.txt
    python normalize_text.py *.txt --in-place
    python normalize_text.py input.txt --stats
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path


# --- Configuration -----------------------------------------------------------

# Smart quotes / dashes / ellipsis → ASCII equivalents
CHAR_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'", "\u201A": "'", "\u201B": "'",  # single quotes
    "\u201C": '"', "\u201D": '"', "\u201E": '"', "\u201F": '"',  # double quotes
    "\u2013": "-", "\u2014": "-", "\u2015": "-",                 # dashes
    "\u2026": "...",                                             # ellipsis
    "\u00A0": " ", "\u2007": " ", "\u202F": " ",                 # nbsp variants
    "\u200B": "",  "\u200C": "",  "\u200D": "",  "\uFEFF": "",   # zero-width
    "\u00AD": "",                                                # soft hyphen
}

# Unicode categories to strip entirely
STRIP_CATEGORIES = {"Cc", "Cf", "Co", "Cs"}  # control, format, private, surrogate
KEEP_CONTROL = {"\n", "\r", "\t"}


# --- Core normalization ------------------------------------------------------

def normalize_unicode(text: str, form: str = "NFC") -> str:
    """Normalize Unicode (NFC/NFD/NFKC/NFKD) and strip problematic chars."""
    text = unicodedata.normalize(form, text)

    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch in KEEP_CONTROL:
            out.append(ch)
        elif cat in STRIP_CATEGORIES:
            continue
        elif ch in CHAR_REPLACEMENTS:
            out.append(CHAR_REPLACEMENTS[ch])
        else:
            out.append(ch)
    return "".join(out)


def normalize_whitespace(
    text: str,
    *,
    collapse_spaces: bool = True,
    strip_lines: bool = True,
    collapse_blank_lines: bool = True,
    tabs_to_spaces: int = 4,
) -> str:
    """Clean up whitespace without destroying paragraph structure."""
    # Normalize line endings to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if tabs_to_spaces:
        text = text.replace("\t", " " * tabs_to_spaces)

    if strip_lines:
        text = "\n".join(line.rstrip() for line in text.split("\n"))

    if collapse_spaces:
        # Collapse runs of spaces, but not newlines
        text = re.sub(r"[ \f\v]+", " ", text)

    if collapse_blank_lines:
        # 2+ newlines → exactly 2 (preserve paragraph breaks)
        text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip() + "\n"


def normalize_text(
    text: str,
    *,
    unicode_form: str = "NFC",
    lowercase: bool = False,
    **whitespace_opts,
) -> str:
    """Full normalization pipeline."""
    text = normalize_unicode(text, form=unicode_form)
    text = normalize_whitespace(text, **whitespace_opts)
    if lowercase:
        text = text.lower()
    return text


# --- File I/O ----------------------------------------------------------------

def detect_encoding(path: Path) -> str:
    """Try UTF-8, fall back to utf-8-sig, then latin-1."""
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "utf-16"):
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def process_file(
    src: Path,
    dst: Path | None = None,
    *,
    in_place: bool = False,
    encoding: str | None = None,
    **opts,
) -> dict:
    """Read, normalize, and write a text file. Returns stats."""
    enc = encoding or detect_encoding(src)
    original = src.read_text(encoding=enc)
    normalized = normalize_text(original, **opts)

    target = src if in_place else (dst or src.with_name(f"{src.stem}.normalized{src.suffix}"))
    target.write_text(normalized, encoding="utf-8", newline="\n")

    return {
        "file": str(src),
        "output": str(target),
        "encoding_in": enc,
        "bytes_in": len(original.encode("utf-8")),
        "bytes_out": len(normalized.encode("utf-8")),
        "chars_in": len(original),
        "chars_out": len(normalized),
    }


# --- CLI ---------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Normalize .txt files: Unicode + whitespace cleanup.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("files", nargs="+", type=Path, help="Input .txt file(s)")
    p.add_argument("-o", "--output", type=Path, help="Output file (single input only)")
    p.add_argument("-i", "--in-place", action="store_true", help="Overwrite input files")
    p.add_argument("-e", "--encoding", help="Force input encoding (default: autodetect)")
    p.add_argument("--form", default="NFC", choices=["NFC", "NFD", "NFKC", "NFKD"],
                   help="Unicode normalization form")
    p.add_argument("--lowercase", action="store_true", help="Lowercase output")
    p.add_argument("--keep-spaces", action="store_true", help="Don't collapse runs of spaces")
    p.add_argument("--keep-blank-lines", action="store_true",
                   help="Don't collapse multiple blank lines")
    p.add_argument("--tabs", type=int, default=4, help="Spaces per tab (0 to disable)")
    p.add_argument("--stats", action="store_true", help="Print before/after stats")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.output and len(args.files) > 1:
        print("error: -o/--output only works with a single input file", file=sys.stderr)
        return 2

    opts = dict(
        unicode_form=args.form,
        lowercase=args.lowercase,
        collapse_spaces=not args.keep_spaces,
        collapse_blank_lines=not args.keep_blank_lines,
        tabs_to_spaces=args.tabs,
    )

    exit_code = 0
    for src in args.files:
        if not src.is_file():
            print(f"skip: {src} (not a file)", file=sys.stderr)
            exit_code = 1
            continue
        try:
            stats = process_file(
                src,
                dst=args.output,
                in_place=args.in_place,
                encoding=args.encoding,
                **opts,
            )
        except Exception as e:
            print(f"error processing {src}: {e}", file=sys.stderr)
            exit_code = 1
            continue

        msg = f"normalized: {stats['file']} -> {stats['output']}"
        if args.stats:
            msg += (f"  [enc={stats['encoding_in']} "
                    f"chars {stats['chars_in']}->{stats['chars_out']} "
                    f"bytes {stats['bytes_in']}->{stats['bytes_out']}]")
        print(msg)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())