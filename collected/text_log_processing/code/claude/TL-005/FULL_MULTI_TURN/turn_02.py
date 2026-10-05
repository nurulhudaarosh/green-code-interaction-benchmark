#!/usr/bin/env python3
"""Text normalizer for .txt files: whitespace + unicode cleanup."""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

PUNCT_MAP = {
    "\u2018": "'", "\u2019": "'", "\u201A": "'", "\u201B": "'",
    "\u201C": '"', "\u201D": '"', "\u201E": '"', "\u201F": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u2010": "-", "\u2011": "-",
    "\u2026": "...",
    "\u2022": "*",
}
ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad"), None)
SPACES = re.compile(r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000\t\f\v]")
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def normalize(text: str, ascii_punct: bool = False, form: str = "NFC") -> str:
    text = unicodedata.normalize(form, text)
    text = text.translate(ZERO_WIDTH)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u2028", "\n").replace("\u2029", "\n\n")
    text = CONTROL.sub("", text)
    if ascii_punct:
        text = text.translate(str.maketrans(PUNCT_MAP))
    text = SPACES.sub(" ", text)
    text = re.sub(r" {2,}", " ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text + "\n" if text else ""  # empty/whitespace-only stays empty


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    if not raw:
        return ""
    for enc in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def collect(paths, out_dir):
    """Yield (source, relative_path) pairs; relative path is relative to the input root."""
    skip_root = out_dir.resolve() if out_dir else None
    for p in map(Path, paths):
        if p.is_dir():
            for f in sorted(p.rglob("*.txt")):
                if f.name.endswith(".clean.txt"):
                    continue
                if skip_root and skip_root in f.resolve().parents:
                    continue
                yield f, f.relative_to(p)
        elif p.is_file():
            yield p, Path(p.name)
        else:
            print(f"skip {p}: not found", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="Normalize .txt files")
    ap.add_argument("paths", nargs="+", help="files or directories")
    ap.add_argument("-i", "--in-place", action="store_true", help="overwrite originals")
    ap.add_argument("-o", "--out-dir", help="mirror results here (default: <name>.clean.txt beside source)")
    ap.add_argument("--ascii", action="store_true", help="convert smart quotes/dashes to ASCII")
    ap.add_argument("--form", default="NFC", choices=["NFC", "NFD", "NFKC", "NFKD"])
    args = ap.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else None
    seen = set()

    for src, rel in collect(args.paths, out_dir):
        if args.in_place:
            dest = src
        elif out_dir:
            dest = out_dir / rel
        else:
            dest = src.with_name(src.stem + ".clean.txt")

        key = dest.resolve()
        if key in seen:
            print(f"skip {src}: output collision at {dest}", file=sys.stderr)
            continue
        seen.add(key)

        try:
            cleaned = normalize(read_text(src), args.ascii, args.form)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(cleaned, encoding="utf-8", newline="\n")
        except OSError as e:
            print(f"skip {src}: {e}", file=sys.stderr)
            continue
        print(f"{src} -> {dest}")


if __name__ == "__main__":
    main()