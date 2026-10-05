import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Always removed (zero-width space, word joiner, BOM, soft hyphen, bidi marks)
_ALWAYS_STRIP = dict.fromkeys(map(ord, "\u200b\u2060\ufeff\u00ad\u200e\u200f\u202a\u202b\u202c\u202d\u202e"))
# ZWNJ/ZWJ: meaningful in Bengali/Persian/Indic, so kept by default
_JOINERS = dict.fromkeys(map(ord, "\u200c\u200d"))

_HSPACE = re.compile(r"[^\S\n]+")   # any whitespace except newline
_MULTI_NL = re.compile(r"\n{3,}")


@dataclass
class Stats:
    files_seen: int = 0
    files_written: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    chars_in: int = 0
    chars_out: int = 0
    bytes_in: int = 0
    bytes_out: int = 0
    failures: list = field(default_factory=list)


def normalize_text(text, lowercase=False, form="NFC", keep_joiners=True, collapse_blank_lines=True):
    text = unicodedata.normalize(form, text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.translate(_ALWAYS_STRIP)
    if not keep_joiners:
        text = text.translate(_JOINERS)
    # Map exotic spaces (NBSP, thin space, ideographic space, tabs...) to a plain space,
    # drop other control chars except newline
    text = "".join(
        " " if (c != "\n" and c.isspace())
        else ("" if unicodedata.category(c) in ("Cc", "Cf") and c not in "\n\u200c\u200d" else c)
        for c in text
    )
    text = _HSPACE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    if collapse_blank_lines:
        text = _MULTI_NL.sub("\n\n", text)
    text = text.strip()
    if lowercase:
        text = text.casefold()
    return text + "\n" if text else ""


def normalize_corpus(src, dst, lowercase=False, form="NFC", keep_joiners=True,
                     exts=(".txt",), encoding="utf-8", overwrite=True, skip_empty=False):
    src, dst = Path(src).resolve(), Path(dst).resolve()
    if not src.is_dir():
        raise NotADirectoryError(src)
    if dst == src or src in dst.parents:
        raise ValueError("dst must not be inside src")

    exts = tuple(e.lower() for e in exts) if exts else None
    stats = Stats()

    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        if path.is_dir():
            (dst / rel).mkdir(parents=True, exist_ok=True)  # mirror empty dirs too
            continue
        if exts and path.suffix.lower() not in exts:
            continue

        stats.files_seen += 1
        out = dst / rel
        if out.exists() and not overwrite:
            stats.files_skipped += 1
            continue

        try:
            raw = path.read_bytes()
            text = raw.decode(encoding)
            clean = normalize_text(text, lowercase, form, keep_joiners)
            if skip_empty and not clean:
                stats.files_skipped += 1
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            data = clean.encode("utf-8")
            out.write_bytes(data)
        except Exception as e:
            stats.files_failed += 1
            stats.failures.append({"file": str(rel), "error": f"{type(e).__name__}: {e}"})
            continue

        stats.files_written += 1
        stats.chars_in += len(text)
        stats.chars_out += len(clean)
        stats.bytes_in += len(raw)
        stats.bytes_out += len(data)

    return stats


def print_report(s: Stats):
    removed = s.chars_in - s.chars_out
    pct = (removed / s.chars_in * 100) if s.chars_in else 0.0
    print("=" * 44)
    print("Normalization report")
    print("=" * 44)
    print(f"Files seen     : {s.files_seen}")
    print(f"Files written  : {s.files_written}")
    print(f"Files skipped  : {s.files_skipped}")
    print(f"Files failed   : {s.files_failed}")
    print(f"Chars in/out   : {s.chars_in:,} -> {s.chars_out:,} ({removed:,} removed, {pct:.2f}%)")
    print(f"Bytes in/out   : {s.bytes_in:,} -> {s.bytes_out:,}")
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
    p.add_argument("--no-overwrite", action="store_true")
    p.add_argument("--skip-empty", action="store_true")
    p.add_argument("--json", metavar="PATH", help="also write stats as JSON")
    a = p.parse_args()

    stats = normalize_corpus(a.src, a.dst, a.lowercase, a.form, not a.strip_joiners,
                             a.ext, a.encoding, not a.no_overwrite, a.skip_empty)
    print_report(stats)
    if a.json:
        Path(a.json).write_text(json.dumps(asdict(stats), indent=2, ensure_ascii=False), encoding="utf-8")
    sys.exit(1 if stats.files_failed else 0)


if __name__ == "__main__":
    main()