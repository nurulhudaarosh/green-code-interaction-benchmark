import argparse
import json
import os
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Always removed (zero-width space, word joiner, BOM, soft hyphen, bidi marks)
_ALWAYS_STRIP = dict.fromkeys(map(ord, "\u200b\u2060\ufeff\u00ad\u200e\u200f\u202a\u202b\u202c\u202d\u202e"))
# ZWNJ/ZWJ: meaningful in Bengali/Persian/Indic, so kept by default
_JOINERS = dict.fromkeys(map(ord, "\u200c\u200d"))

_HSPACE = re.compile(r"[^\S\n]+")
_MULTI_NL = re.compile(r"\n{3,}")


@dataclass
class Stats:
    files_seen: int = 0        # matched extension filter
    files_written: int = 0     # new or content actually changed
    files_unchanged: int = 0   # output already identical (idempotent re-run)
    files_skipped: int = 0     # --no-overwrite / --skip-empty
    files_failed: int = 0
    files_ignored: int = 0     # non-matching ext (not copied) or symlinks
    files_copied: int = 0      # non-matching ext copied verbatim (--copy-others)
    dirs_mirrored: int = 0
    chars_in: int = 0
    chars_out: int = 0
    bytes_in: int = 0
    bytes_out: int = 0
    failures: list = field(default_factory=list)


def _clean_char(c):
    if c == "\n" or c in "\u200c\u200d":
        return c
    if c.isspace():
        return " "
    if unicodedata.category(c) in ("Cc", "Cf"):
        return ""
    return c


def normalize_text(text, lowercase=False, form="NFC", keep_joiners=True, collapse_blank_lines=True):
    text = unicodedata.normalize(form, text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.translate(_ALWAYS_STRIP)
    if not keep_joiners:
        text = text.translate(_JOINERS)
    if lowercase:
        text = text.casefold()
    # Re-normalize after casefold/removals so a second pass is a no-op (idempotence)
    text = unicodedata.normalize(form, text)
    text = "".join(map(_clean_char, text))
    text = _HSPACE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    if collapse_blank_lines:
        text = _MULTI_NL.sub("\n\n", text)
    text = text.strip()
    return text + "\n" if text else ""


def _same_bytes(path, data):
    try:
        return path.is_file() and path.stat().st_size == len(data) and path.read_bytes() == data
    except OSError:
        return False


def normalize_corpus(src, dst, lowercase=False, form="NFC", keep_joiners=True,
                     exts=(".txt",), encoding="utf-8", errors="strict",
                     overwrite=True, skip_empty=False, copy_others=False, mirror_dirs=True):
    src, dst = Path(src).resolve(), Path(dst).resolve()
    if not src.is_dir():
        raise NotADirectoryError(f"src is not a directory: {src}")
    if dst.exists() and not dst.is_dir():
        raise NotADirectoryError(f"dst exists and is not a directory: {dst}")
    if dst == src or src in dst.parents or dst in src.parents:
        raise ValueError("src and dst must not contain each other")

    exts = tuple(("." + e.lstrip(".")).lower() for e in exts) if exts else None
    enc = "utf-8-sig" if encoding.lower().replace("_", "-") in ("utf-8", "utf8") else encoding
    stats = Stats()
    dirs = []

    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        out = dst / rel

        if path.is_symlink():
            stats.files_ignored += 1
            continue
        if path.is_dir():
            dirs.append(rel)
            continue
        if not path.is_file():  # sockets, fifos, etc.
            stats.files_ignored += 1
            continue

        # Non-matching files mixed in
        if exts and path.suffix.lower() not in exts:
            if not copy_others:
                stats.files_ignored += 1
                continue
            try:
                if out.exists() and not overwrite:
                    stats.files_skipped += 1
                elif _same_bytes(out, path.read_bytes()):
                    stats.files_unchanged += 1
                else:
                    out.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, out)
                    stats.files_copied += 1
            except Exception as e:
                stats.files_failed += 1
                stats.failures.append({"file": str(rel), "error": f"{type(e).__name__}: {e}"})
            continue

        stats.files_seen += 1
        if out.exists() and not overwrite:
            stats.files_skipped += 1
            continue

        try:
            raw = path.read_bytes()
            text = raw.decode(enc, errors)
            clean = normalize_text(text, lowercase, form, keep_joiners)
            if skip_empty and not clean:
                stats.files_skipped += 1
                continue
            data = clean.encode("utf-8")
            if _same_bytes(out, data):
                stats.files_unchanged += 1
            else:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(data)
                stats.files_written += 1
        except Exception as e:
            stats.files_failed += 1
            stats.failures.append({"file": str(rel), "error": f"{type(e).__name__}: {e}"})
            continue

        stats.chars_in += len(text)
        stats.chars_out += len(clean)
        stats.bytes_in += len(raw)
        stats.bytes_out += len(data)

    # Mirror every source directory, including empty ones
    if mirror_dirs:
        dst.mkdir(parents=True, exist_ok=True)
        for rel in dirs:
            d = dst / rel
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                stats.dirs_mirrored += 1

    return stats


def print_report(s: Stats):
    removed = s.chars_in - s.chars_out
    pct = (removed / s.chars_in * 100) if s.chars_in else 0.0
    print("=" * 44)
    print("Normalization report")
    print("=" * 44)
    print(f"Files matched   : {s.files_seen}")
    print(f"  written       : {s.files_written}")
    print(f"  unchanged     : {s.files_unchanged}")
    print(f"  skipped       : {s.files_skipped}")
    print(f"  failed        : {s.files_failed}")
    print(f"Other files     : {s.files_ignored} ignored, {s.files_copied} copied")
    print(f"Dirs mirrored   : {s.dirs_mirrored}")
    print(f"Chars in/out    : {s.chars_in:,} -> {s.chars_out:,} ({removed:,} removed, {pct:.2f}%)")
    print(f"Bytes in/out    : {s.bytes_in:,} -> {s.bytes_out:,}")
    for f in s.failures:
        print(f"  ! {f['file']}: {f['error']}")


def main():
    p = argparse.ArgumentParser(description="Normalize a text corpus, mirroring the directory tree.")
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--lowercase", action="store_true")
    p.add_argument("--form", default="NFC", choices=["NFC", "NFD", "NFKC", "NFKD"])
    p.add_argument("--strip-joiners", action="store_true", help="remove ZWJ/ZWNJ (not recommended for Bengali)")
    p.add_argument("--ext", nargs="*", default=[".txt"], help="extensions to process; empty = all files")
    p.add_argument("--encoding", default="utf-8")
    p.add_argument("--errors", default="strict", choices=["strict", "replace", "ignore"])
    p.add_argument("--no-overwrite", action="store_true")
    p.add_argument("--skip-empty", action="store_true")
    p.add_argument("--copy-others", action="store_true", help="copy non-matching files verbatim")
    p.add_argument("--no-empty-dirs", action="store_true", help="only create dirs that receive files")
    p.add_argument("--json", metavar="PATH", help="also write stats as JSON")
    a = p.parse_args()

    try:
        stats = normalize_corpus(
            a.src, a.dst, a.lowercase, a.form, not a.strip_joiners, a.ext, a.encoding, a.errors,
            not a.no_overwrite, a.skip_empty, a.copy_others, not a.no_empty_dirs,
        )
    except (NotADirectoryError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)

    if stats.files_seen == 0:
        print("warning: no files matched the extension filter", file=sys.stderr)
    print_report(stats)
    if a.json:
        Path(a.json).write_text(json.dumps(asdict(stats), indent=2, ensure_ascii=False), encoding="utf-8")
    sys.exit(1 if stats.files_failed else 0)


if __name__ == "__main__":
    main()