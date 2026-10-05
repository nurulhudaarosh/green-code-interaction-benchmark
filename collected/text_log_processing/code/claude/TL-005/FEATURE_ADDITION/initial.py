#!/usr/bin/env python3
import argparse
import re
import sys
import unicodedata
from pathlib import Path

CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
SPACES_RE = re.compile(r"[ \t\u00a0]+")
BLANKS_RE = re.compile(r"\n{3,}")

QUOTES = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2026": "...",
}


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = unicodedata.normalize("NFKC", text)
    text = ZERO_WIDTH_RE.sub("", text)
    text = CONTROL_RE.sub("", text)
    for k, v in QUOTES.items():
        text = text.replace(k, v)
    text = SPACES_RE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = BLANKS_RE.sub("\n\n", text)
    return text.strip() + "\n"


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser(description="Normalize .txt files in a directory (non-recursive).")
    ap.add_argument("input_dir", type=Path)
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()

    if not args.input_dir.is_dir():
        print(f"Not a directory: {args.input_dir}", file=sys.stderr)
        return 1
    if args.input_dir.resolve() == args.output_dir.resolve():
        print("Output dir must differ from input dir.", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for f in sorted(args.input_dir.glob("*.txt")):
        if not f.is_file():
            continue
        cleaned = normalize(read_text(f))
        (args.output_dir / f.name).write_text(cleaned, encoding="utf-8", newline="\n")
        count += 1
        print(f"cleaned: {f.name}")

    print(f"Done. {count} file(s) -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())