#!/usr/bin/env python3
import argparse
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
SPACES_RE = re.compile(r"[ \t\u00a0]+")
BLANKS_RE = re.compile(r"\n{3,}")

QUOTES = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2026": "...",
}


@dataclass
class FileStat:
    path: str
    encoding: str = ""
    bytes_in: int = 0
    bytes_out: int = 0
    lines_in: int = 0
    lines_out: int = 0
    changed: bool = False
    error: str = ""


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


def read_text(path: Path):
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        encodings = ("utf-16",)
    else:
        encodings = ("utf-8-sig", "cp1252", "latin-1")
    for enc in encodings:
        try:
            return raw.decode(enc), enc, len(raw)
        except UnicodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8-replace", len(raw)


def collect_files(input_dir: Path, output_dir: Path):
    out = output_dir.resolve()
    for root, dirs, files in os.walk(input_dir):
        root_p = Path(root)
        # prune output dir if it lives inside input dir
        dirs[:] = sorted(d for d in dirs if (root_p / d).resolve() != out)
        for name in sorted(files):
            if name.lower().endswith(".txt"):
                yield root_p / name


def run(input_dir: Path, output_dir: Path, verbose: bool = True) -> dict:
    stats = []
    for src in collect_files(input_dir, output_dir):
        rel = src.relative_to(input_dir)
        st = FileStat(path=str(rel))
        try:
            text, enc, size = read_text(src)
            cleaned = normalize(text)
            dst = output_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(cleaned, encoding="utf-8", newline="\n")
            st.encoding = enc
            st.bytes_in = size
            st.bytes_out = len(cleaned.encode("utf-8"))
            st.lines_in = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
            st.lines_out = cleaned.count("\n")
            st.changed = cleaned.encode("utf-8") != src.read_bytes()
        except Exception as e:
            st.error = f"{type(e).__name__}: {e}"
        stats.append(st)
        if verbose:
            if st.error:
                print(f"FAIL  {st.path}  ({st.error})")
            else:
                print(f"OK    {st.path}  {st.bytes_in}B -> {st.bytes_out}B, "
                      f"{st.lines_in}L -> {st.lines_out}L, {st.encoding}"
                      f"{'' if st.changed else ', unchanged'}")

    ok = [s for s in stats if not s.error]
    totals = {
        "files": len(stats),
        "succeeded": len(ok),
        "failed": len(stats) - len(ok),
        "changed": sum(s.changed for s in ok),
        "unchanged": sum(not s.changed for s in ok),
        "bytes_in": sum(s.bytes_in for s in ok),
        "bytes_out": sum(s.bytes_out for s in ok),
        "lines_in": sum(s.lines_in for s in ok),
        "lines_out": sum(s.lines_out for s in ok),
    }
    return {"files": stats, "totals": totals}


def main() -> int:
    ap = argparse.ArgumentParser(description="Recursively normalize .txt files, mirroring structure.")
    ap.add_argument("input_dir", type=Path)
    ap.add_argument("output_dir", type=Path)
    ap.add_argument("-q", "--quiet", action="store_true", help="suppress per-file lines")
    args = ap.parse_args()

    if not args.input_dir.is_dir():
        print(f"Not a directory: {args.input_dir}", file=sys.stderr)
        return 1
    if args.input_dir.resolve() == args.output_dir.resolve():
        print("Output dir must differ from input dir.", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = run(args.input_dir, args.output_dir, verbose=not args.quiet)
    t = result["totals"]

    print("\n--- Totals ---")
    print(f"files:     {t['files']} ({t['succeeded']} ok, {t['failed']} failed)")
    print(f"changed:   {t['changed']}  unchanged: {t['unchanged']}")
    print(f"bytes:     {t['bytes_in']} -> {t['bytes_out']} "
          f"({t['bytes_in'] - t['bytes_out']:+d} saved)")
    print(f"lines:     {t['lines_in']} -> {t['lines_out']}")
    return 0 if t["failed"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())