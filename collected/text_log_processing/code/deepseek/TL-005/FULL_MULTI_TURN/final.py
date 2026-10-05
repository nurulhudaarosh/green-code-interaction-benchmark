#!/usr/bin/env python3
"""
Text normalizer for .txt files with whitespace/Unicode cleanup,
lowercasing, and a structured stats report.

Gracefully handles empty directories, non-txt files, symlinks,
and unreadable paths.

Usage:
    python normalize_text.py input.txt --stats
    python normalize_text.py src/ --outdir clean/ --lowercase --stats
    python normalize_text.py src/ --include-ext md rst --outdir clean/
    python normalize_text.py emptydir/            # reports "no files", exit 3
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


# --- Configuration -----------------------------------------------------------

CHAR_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'", "\u201A": "'", "\u201B": "'",
    "\u201C": '"', "\u201D": '"', "\u201E": '"', "\u201F": '"',
    "\u2013": "-", "\u2014": "-", "\u2015": "-",
    "\u2026": "...",
    "\u00A0": " ", "\u2007": " ", "\u202F": " ",
    "\u200B": "",  "\u200C": "",  "\u200D": "",  "\uFEFF": "",
    "\u00AD": "",
}

STRIP_CATEGORIES = {"Cc", "Cf", "Co", "Cs"}
KEEP_CONTROL = {"\n", "\r", "\t"}

DEFAULT_EXTS = ("txt",)

# Exit codes
EXIT_OK = 0
EXIT_PARTIAL = 1
EXIT_USAGE = 2
EXIT_NOTHING = 3


# --- Stats containers --------------------------------------------------------

@dataclass
class NormalizeStats:
    replacements: Counter = field(default_factory=Counter)
    stripped: Counter = field(default_factory=Counter)
    collapsed_space_runs: int = 0
    collapsed_blank_line_runs: int = 0
    tabs_converted: int = 0
    line_endings_normalized: int = 0
    case_folded_chars: int = 0


@dataclass
class FileReport:
    src: Path
    dst: Path
    encoding_in: str
    chars_in: int
    chars_out: int
    bytes_in: int
    bytes_out: int
    stats: NormalizeStats

    @property
    def char_delta(self) -> int:
        return self.chars_out - self.chars_in

    @property
    def byte_delta(self) -> int:
        return self.bytes_out - self.bytes_in


@dataclass
class SkipReport:
    """A path we deliberately did not process, with a machine-readable reason."""
    path: Path
    reason: str   # e.g. "not_a_file", "empty_dir", "wrong_ext", "symlink_loop", ...

    def describe(self) -> str:
        if self.reason == "wrong_ext":
            ext = self.path.suffix or "(no extension)"
            return f"{self.path}: skipped (extension {ext} not in include list)"
        if self.reason == "empty_dir":
            return f"{self.path}: skipped (directory contains no matching files)"
        if self.reason == "not_a_file":
            return f"{self.path}: skipped (not a regular file)"
        if self.reason == "broken_symlink":
            return f"{self.path}: skipped (broken symlink)"
        if self.reason == "unreadable":
            return f"{self.path}: skipped (permission denied)"
        return f"{self.path}: skipped ({self.reason})"


# --- Core normalization ------------------------------------------------------

def normalize_unicode(
    text: str,
    form: str = "NFC",
    stats: NormalizeStats | None = None,
) -> str:
    if not text:
        return text
    text = unicodedata.normalize(form, text)
    out = []
    for ch in text:
        if ch in KEEP_CONTROL:
            out.append(ch)
            continue
        cat = unicodedata.category(ch)
        if cat in STRIP_CATEGORIES:
            if stats is not None:
                stats.stripped[f"U+{ord(ch):04X}"] += 1
            continue
        if ch in CHAR_REPLACEMENTS:
            if stats is not None:
                stats.replacements[f"U+{ord(ch):04X}"] += 1
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
    stats: NormalizeStats | None = None,
) -> str:
    if not text or not text.strip():
        return ""

    before = text
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if stats is not None and text != before:
        stats.line_endings_normalized += (
            before.count("\r\n") + before.count("\r")
        )

    if tabs_to_spaces:
        n_tabs = text.count("\t")
        if n_tabs:
            if stats is not None:
                stats.tabs_converted += n_tabs
            text = text.replace("\t", " " * tabs_to_spaces)

    if strip_lines:
        text = "\n".join(line.rstrip() for line in text.split("\n"))

    if collapse_spaces:
        new_text, n = re.subn(r"[ \f\v]{2,}", " ", text)
        if stats is not None:
            stats.collapsed_space_runs += n
        text = new_text

    if collapse_blank_lines:
        new_text, n = re.subn(r"\n{3,}", "\n\n", text)
        if stats is not None:
            stats.collapsed_blank_line_runs += n
        text = new_text

    stripped = text.strip()
    return stripped + "\n" if stripped else ""


def apply_case(text: str, mode: str, stats: NormalizeStats | None = None) -> str:
    if mode == "none" or not text:
        return text
    folded = text.casefold() if mode == "casefold" else text.lower()
    if stats is not None:
        stats.case_folded_chars += sum(
            1 for a, b in zip(text, folded) if a != b
        ) + abs(len(text) - len(folded))
    return folded


def normalize_text(
    text: str,
    *,
    unicode_form: str = "NFC",
    case_mode: str = "none",
    stats: NormalizeStats | None = None,
    **whitespace_opts,
) -> str:
    text = normalize_unicode(text, form=unicode_form, stats=stats)
    text = normalize_whitespace(text, stats=stats, **whitespace_opts)
    text = apply_case(text, case_mode, stats=stats)
    return text


# --- File I/O ----------------------------------------------------------------

def detect_encoding(path: Path) -> str:
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
    dst: Path,
    *,
    encoding: str | None = None,
    **opts,
) -> FileReport:
    enc = encoding or detect_encoding(src)
    original = src.read_text(encoding=enc)

    stats = NormalizeStats()
    normalized = normalize_text(original, stats=stats, **opts)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(normalized, encoding="utf-8", newline="\n")

    return FileReport(
        src=src,
        dst=dst,
        encoding_in=enc,
        chars_in=len(original),
        chars_out=len(normalized),
        bytes_in=len(original.encode("utf-8")),
        bytes_out=len(normalized.encode("utf-8")),
        stats=stats,
    )


# --- Input expansion ---------------------------------------------------------

def _classify_file(p: Path, exts: set[str]) -> SkipReport | None:
    """Return None if the file is fine, else a SkipReport."""
    if p.is_symlink() and not p.exists():
        return SkipReport(p, "broken_symlink")
    if not p.exists():
        return SkipReport(p, "not_a_file")
    if not p.is_file():
        return SkipReport(p, "not_a_file")
    if p.suffix.lower().lstrip(".") not in exts:
        return SkipReport(p, "wrong_ext")
    if not os.access(p, os.R_OK):
        return SkipReport(p, "unreadable")
    return None


def collect_inputs(
    paths: list[Path],
    *,
    exts: set[str],
    recursive: bool = True,
    follow_symlinks: bool = False,
) -> tuple[list[Path], list[SkipReport]]:
    """
    Expand inputs to a sorted, deduped list of files, plus skip reports.

    Empty directories produce an explicit SkipReport instead of being
    silently dropped. Non-matching files inside directories are ignored
    (they're noise); non-matching files passed *explicitly* are reported.
    """
    files: list[Path] = []
    skips: list[SkipReport] = []
    seen: set[Path] = set()

    def add(f: Path) -> None:
        key = f.resolve() if follow_symlinks else f
        if key in seen:
            return
        seen.add(key)
        files.append(f)

    for p in paths:
        if not p.exists() and not p.is_symlink():
            skips.append(SkipReport(p, "not_a_file"))
            continue

        if p.is_symlink() and not p.exists():
            skips.append(SkipReport(p, "broken_symlink"))
            continue

        if p.is_dir():
            pattern = "**/*" if recursive else "*"
            found_any = False
            for child in sorted(p.glob(pattern)):
                if not child.is_file():
                    continue
                if child.suffix.lower().lstrip(".") not in exts:
                    continue
                cls = _classify_file(child, exts)
                if cls is not None:
                    skips.append(cls)
                    continue
                add(child)
                found_any = True
            if not found_any:
                skips.append(SkipReport(p, "empty_dir"))
        else:
            # Explicitly-named file: report if wrong extension or unreadable.
            cls = _classify_file(p, exts)
            if cls is not None:
                skips.append(cls)
                continue
            add(p)

    return files, skips


# --- Destination mapping -----------------------------------------------------

def _common_parts(files: list[Path]) -> int:
    parents = [f.resolve().parent.parts for f in files]
    n = min(len(p) for p in parents)
    i = 0
    while i < n and all(p[i] == parents[0][i] for p in parents):
        i += 1
    return i


def _common_root(files: list[Path]) -> Path:
    if not files:
        return Path(".")
    parts = Path(files[0]).resolve().parent.parts[:_common_parts(files)]
    return Path(*parts) if parts else Path(".")


def plan_destinations(
    files: list[Path],
    *,
    outdir: Path | None,
    output: Path | None,
    in_place: bool,
) -> list[tuple[Path, Path]]:
    if output is not None:
        if len(files) != 1:
            raise ValueError("-o/--output requires exactly one input file")
        return [(files[0], output)]

    if in_place:
        return [(f, f) for f in files]

    if outdir is not None:
        root = _common_root(files)
        pairs: list[tuple[Path, Path]] = []
        for f in files:
            try:
                rel = f.resolve().relative_to(root.resolve())
            except ValueError:
                rel = Path(f.name)
            pairs.append((f, outdir / rel))
        return pairs

    return [(f, f.with_name(f"{f.stem}.normalized{f.suffix}")) for f in files]


# --- Stats report ------------------------------------------------------------

def _human_delta(n: int) -> str:
    return f"+{n}" if n >= 0 else str(n)


def format_report(
    reports: list[FileReport],
    skips: list[SkipReport],
    *,
    case_mode: str,
    unicode_form: str,
    elapsed_s: float | None = None,
) -> str:
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("NORMALIZATION REPORT")
    lines.append("=" * 72)
    lines.append(f"Files processed : {len(reports)}")
    lines.append(f"Files skipped   : {len(skips)}")
    lines.append(f"Unicode form    : {unicode_form}")
    lines.append(f"Case mode       : {case_mode}")
    if elapsed_s is not None:
        lines.append(f"Elapsed         : {elapsed_s:.3f}s")
    lines.append("")

    if reports:
        lines.append("-" * 72)
        lines.append(f"{'FILE':<40} {'CHARS':>12} {'BYTES':>12}")
        lines.append("-" * 72)
        for r in reports:
            name = str(r.src)
            if len(name) > 39:
                name = "…" + name[-38:]
            chars = f"{r.chars_in}->{r.chars_out} ({_human_delta(r.char_delta)})"
            bytes_ = f"{r.bytes_in}->{r.bytes_out} ({_human_delta(r.byte_delta)})"
            lines.append(f"{name:<40} {chars:>12} {bytes_:>12}")
        lines.append("-" * 72)
        lines.append("")

        t_chars_in = sum(r.chars_in for r in reports)
        t_chars_out = sum(r.chars_out for r in reports)
        t_bytes_in = sum(r.bytes_in for r in reports)
        t_bytes_out = sum(r.bytes_out for r in reports)
        lines.append("TOTALS")
        lines.append(f"  chars : {t_chars_in} -> {t_chars_out} "
                     f"({_human_delta(t_chars_out - t_chars_in)})")
        lines.append(f"  bytes : {t_bytes_in} -> {t_bytes_out} "
                     f"({_human_delta(t_bytes_out - t_bytes_in)})")
        lines.append("")

        agg = NormalizeStats()
        for r in reports:
            agg.replacements.update(r.stats.replacements)
            agg.stripped.update(r.stats.stripped)
            agg.collapsed_space_runs += r.stats.collapsed_space_runs
            agg.collapsed_blank_line_runs += r.stats.collapsed_blank_line_runs
            agg.tabs_converted += r.stats.tabs_converted
            agg.line_endings_normalized += r.stats.line_endings_normalized
            agg.case_folded_chars += r.stats.case_folded_chars

        lines.append("TRANSFORMATIONS")
        lines.append(f"  line endings normalized      : {agg.line_endings_normalized}")
        lines.append(f"  tabs expanded                : {agg.tabs_converted}")
        lines.append(f"  space runs collapsed         : {agg.collapsed_space_runs}")
        lines.append(f"  blank-line runs collapsed    : {agg.collapsed_blank_line_runs}")
        lines.append(f"  characters case-folded       : {agg.case_folded_chars}")

        if agg.replacements:
            lines.append("  character replacements       :")
            for cp, n in agg.replacements.most_common():
                try:
                    disp = repr(chr(int(cp[2:], 16)))
                except Exception:
                    disp = "?"
                lines.append(f"      {cp} {disp:<8} x{n}")

        if agg.stripped:
            lines.append("  characters stripped          :")
            for cp, n in agg.stripped.most_common():
                lines.append(f"      {cp:<8} x{n}")

    if skips:
        lines.append("")
        lines.append("SKIPPED")
        # Group by reason for a compact view
        by_reason: dict[str, list[SkipReport]] = {}
        for s in skips:
            by_reason.setdefault(s.reason, []).append(s)
        for reason in sorted(by_reason):
            lines.append(f"  {reason} ({len(by_reason[reason])}):")
            for s in by_reason[reason]:
                # SkipReport.describe() prefixes the path; just show the path.
                lines.append(f"      {s.path}")

    lines.append("=" * 72)
    return "\n".join(lines) + "\n"


# --- CLI ---------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Normalize .txt files: Unicode + whitespace cleanup.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("files", nargs="+", type=Path,
                   help="Input file(s) or directories")
    p.add_argument("-o", "--output", type=Path,
                   help="Output file (exactly one input)")
    p.add_argument("-d", "--outdir", type=Path,
                   help="Output directory (mirrors input tree)")
    p.add_argument("-i", "--in-place", action="store_true",
                   help="Overwrite input files")
    p.add_argument("-e", "--encoding", help="Force input encoding")
    p.add_argument("--form", default="NFC", choices=["NFC", "NFD", "NFKC", "NFKD"],
                   help="Unicode normalization form")
    p.add_argument("--include-ext", nargs="+", default=list(DEFAULT_EXTS),
                   metavar="EXT",
                   help="Extensions to process (without dots)")
    p.add_argument("--no-recursive", action="store_true",
                   help="Don't descend into subdirectories")
    p.add_argument("--follow-symlinks", action="store_true",
                   help="Dereference symlinks when scanning directories")

    case_group = p.add_mutually_exclusive_group()
    case_group.add_argument("--lowercase", action="store_true",
                            help="Lowercase output (str.lower)")
    case_group.add_argument("--casefold", action="store_true",
                            help="Casefold output (Unicode-aware)")

    p.add_argument("--keep-spaces", action="store_true")
    p.add_argument("--keep-blank-lines", action="store_true")
    p.add_argument("--tabs", type=int, default=4, help="Spaces per tab (0 disables)")

    p.add_argument("--stats", action="store_true",
                   help="Print a stats report after processing")
    p.add_argument("--stats-only", action="store_true",
                   help="Print only the stats report")
    p.add_argument("--stats-file", type=Path,
                   help="Also write the stats report to this file")
    p.add_argument("--quiet", action="store_true",
                   help="Suppress per-file progress lines")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.output and args.outdir:
        print("error: -o/--output and -d/--outdir are mutually exclusive",
              file=sys.stderr)
        return EXIT_USAGE
    if args.output and args.in_place:
        print("error: -o/--output and -i/--in-place are mutually exclusive",
              file=sys.stderr)
        return EXIT_USAGE

    exts = {e.lower().lstrip(".") for e in args.include_ext}

    files, skips = collect_inputs(
        args.files,
        exts=exts,
        recursive=not args.no_recursive,
        follow_symlinks=args.follow_symlinks,
    )

    # Graceful "nothing to do" path: no crash, no partial writes.
    if not files:
        if skips:
            print("warning: no matching files found:", file=sys.stderr)
            for s in skips:
                print(f"  {s.describe()}", file=sys.stderr)
        else:
            print("error: no input files matched", file=sys.stderr)
        return EXIT_NOTHING

    try:
        pairs = plan_destinations(
            files, outdir=args.outdir, output=args.output, in_place=args.in_place,
        )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_USAGE

    case_mode = "casefold" if args.casefold else ("lower" if args.lowercase else "none")

    opts = dict(
        unicode_form=args.form,
        case_mode=case_mode,
        collapse_spaces=not args.keep_spaces,
        collapse_blank_lines=not args.keep_blank_lines,
        tabs_to_spaces=args.tabs,
    )

    t0 = time.perf_counter()
    reports: list[FileReport] = []
    errors = 0
    show_progress = not (args.quiet or args.stats_only)

    for src, dst in pairs:
        try:
            rep = process_file(src, dst, encoding=args.encoding, **opts)
        except PermissionError:
            skips.append(SkipReport(src, "unreadable"))
            errors += 1
            if show_progress:
                print(f"skip: {src} (permission denied)", file=sys.stderr)
            continue
        except OSError as e:
            errors += 1
            if show_progress:
                print(f"error: {src}: {e}", file=sys.stderr)
            continue
        except Exception as e:
            errors += 1
            print(f"error processing {src}: {e}", file=sys.stderr)
            continue

        reports.append(rep)
        if show_progress:
            msg = f"normalized: {rep.src} -> {rep.dst}"
            if args.stats:
                msg += (f"  [enc={rep.encoding_in} "
                        f"chars {rep.chars_in}->{rep.chars_out} "
                        f"bytes {rep.bytes_in}->{rep.bytes_out}]")
            print(msg)

    elapsed = time.perf_counter() - t0

    if (args.stats or args.stats_only or args.stats_file) and (reports or skips):
        report = format_report(
            reports, skips,
            case_mode=case_mode,
            unicode_form=args.form,
            elapsed_s=elapsed,
        )
        sys.stdout.write(report)
        if args.stats_file:
            args.stats_file.parent.mkdir(parents=True, exist_ok=True)
            args.stats_file.write_text(report, encoding="utf-8")
            if not args.stats_only:
                print(f"stats written: {args.stats_file}")

    if not show_progress and skips and not (args.stats or args.stats_only):
        # If progress is suppressed but we still skipped things, warn once.
        print(f"note: {len(skips)} input(s) skipped "
              f"(use --stats to see details)", file=sys.stderr)

    if errors:
        return EXIT_PARTIAL
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())