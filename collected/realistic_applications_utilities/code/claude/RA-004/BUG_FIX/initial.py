#!/usr/bin/env python3
"""
Document Organizer (v2)
-----------------------
Sorts files into category folders (optionally by month), detects duplicates,
supports dry runs, and can undo the last run. Python 3.8+, no dependencies.

Extensions: case-insensitive; compound types (.tar.gz); trailing dots/spaces;
            backup suffixes (report.pdf.bak); fake "extensions" like the .2 in
            "notes v1.2"; extensionless files identified by magic bytes.
Dates:      filename dates (2024-03-15, 20240315, 2024_03_15) are validated as
            real calendar dates; bad ones are ignored. Falls back to mtime, then
            ctime, then an "Undated" folder. Epoch-zero, pre-1980 and
            far-future timestamps are rejected as malformed.

Usage:
  python organizer.py ~/Downloads --dry-run
  python organizer.py ~/Downloads --by-date --dedupe --recursive
  python organizer.py ~/Downloads --undo
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

CATEGORIES = {
    "Documents":     {".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".tex", ".pages"},
    "Spreadsheets":  {".xls", ".xlsx", ".csv", ".ods", ".tsv", ".numbers"},
    "Presentations": {".ppt", ".pptx", ".odp", ".key"},
    "Images":        {".jpg", ".jpeg", ".jpe", ".png", ".gif", ".bmp", ".svg", ".webp", ".heic", ".tif", ".tiff", ".raw"},
    "Videos":        {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm"},
    "Audio":         {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "Archives":      {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".zst",
                      ".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst", ".tgz", ".tbz2", ".txz"},
    "Code":          {".py", ".js", ".ts", ".html", ".htm", ".css", ".java", ".c", ".cpp", ".go",
                      ".rs", ".json", ".xml", ".yml", ".yaml", ".sh", ".sql"},
    "Ebooks":        {".epub", ".mobi", ".azw3"},
    "Installers":    {".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".apk"},
}
EXT_TO_CAT = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}
COMPOUND_EXTS = sorted((e for e in EXT_TO_CAT if e.count(".") > 1), key=len, reverse=True)
STRIP_SUFFIXES = {".bak", ".old", ".orig", ".copy", ".tmp", ".part", ".crdownload"}

# Magic bytes for extensionless files: (offset, signature, category)
MAGIC = [
    (0, b"%PDF-", "Documents"),
    (0, b"\x89PNG\r\n\x1a\n", "Images"),
    (0, b"\xff\xd8\xff", "Images"),
    (0, b"GIF87a", "Images"),
    (0, b"GIF89a", "Images"),
    (0, b"PK\x03\x04", "Archives"),
    (0, b"7z\xbc\xaf\x27\x1c", "Archives"),
    (0, b"Rar!\x1a\x07", "Archives"),
    (0, b"\x1f\x8b", "Archives"),
    (0, b"ID3", "Audio"),
    (0, b"fLaC", "Audio"),
    (4, b"ftyp", "Videos"),
    (0, b"MZ", "Installers"),
]

OTHER, DUPES, UNDATED = "Other", "Duplicates", "Undated"
LOG_NAME = ".organizer_log.json"
RESERVED = set(CATEGORIES) | {OTHER, DUPES}

MIN_YEAR = 1980
DATE_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})[-_.]?(0[1-9]|1[0-2])[-_.]?(0[1-9]|[12]\d|3[01])(?!\d)")


# ---------------------------------------------------------------- extensions
def get_extension(name: str) -> str:
    """Return a normalized, trustworthy extension ('' if none)."""
    name = name.strip().rstrip(". ").lower()
    for _ in range(2):  # peel off up to two backup-style suffixes
        suf = Path(name).suffix
        if suf in STRIP_SUFFIXES and len(name) > len(suf):
            name = name[: -len(suf)]
        else:
            break
    for comp in COMPOUND_EXTS:
        if name.endswith(comp) and len(name) > len(comp):
            return comp
    ext = Path(name).suffix  # '' for '.bashrc' and names with no dot
    body = ext[1:]
    if not body or len(body) > 8 or not body.isalnum() or body.isdigit():
        return ""  # '.2' from 'notes v1.2' or '.2024' is not a real extension
    return ext


def sniff_category(path: Path):
    try:
        with path.open("rb") as f:
            head = f.read(16)
    except OSError:
        return None
    for offset, sig, cat in MAGIC:
        if head[offset: offset + len(sig)] == sig:
            return cat
    return None


def categorize(path: Path) -> str:
    ext = get_extension(path.name)
    if ext in EXT_TO_CAT:
        return EXT_TO_CAT[ext]
    if not ext:
        return sniff_category(path) or OTHER
    return OTHER


# --------------------------------------------------------------------- dates
def valid_date(dt: datetime, now: datetime) -> bool:
    return MIN_YEAR <= dt.year and dt <= now + timedelta(days=1)


def date_from_name(name: str, now: datetime):
    for m in DATE_RE.finditer(name):
        try:
            dt = datetime(int(m[1]), int(m[2]), int(m[3]))  # rejects e.g. Feb 30
        except ValueError:
            continue
        if valid_date(dt, now):
            return dt
    return None


def date_from_stat(path: Path, now: datetime):
    try:
        st = path.stat()
    except OSError:
        return None
    for ts in (st.st_mtime, st.st_ctime):
        try:
            dt = datetime.fromtimestamp(ts)
        except (OverflowError, OSError, ValueError):
            continue  # malformed/out-of-range timestamp
        if valid_date(dt, now):
            return dt
    return None


def date_folder(path: Path, now: datetime):
    """Return (YYYY-MM or 'Undated', source)."""
    dt = date_from_name(path.name, now)
    if dt:
        return dt.strftime("%Y-%m"), "name"
    dt = date_from_stat(path, now)
    if dt:
        return dt.strftime("%Y-%m"), "filesystem"
    return UNDATED, "none"


# ------------------------------------------------------------------- helpers
def file_hash(path: Path, chunk=1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def unique_path(dst: Path, taken: set) -> Path:
    candidate, i = dst, 1
    while candidate.exists() or candidate in taken:
        candidate = dst.with_name(f"{dst.stem}_{i}{dst.suffix}")
        i += 1
    return candidate


def collect_files(root: Path, recursive: bool):
    it = root.rglob("*") if recursive else root.iterdir()
    for p in it:
        if not p.is_file() or p.is_symlink():
            continue
        rel = p.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if rel.parts[0] in RESERVED and len(rel.parts) > 1:
            continue
        yield p


def build_plan(root, recursive, by_date, dedupe):
    now = datetime.now()
    files = sorted(collect_files(root, recursive))
    plan, taken, seen = [], set(), {}
    date_sources = Counter()
    sizes = Counter()
    if dedupe:
        for f in files:
            try:
                sizes[f.stat().st_size] += 1
            except OSError:
                pass

    for f in files:
        try:
            if dedupe and sizes[f.stat().st_size] > 1:
                digest = file_hash(f)
                if digest in seen:
                    dst = unique_path(root / DUPES / f.name, taken)
                    taken.add(dst)
                    plan.append((f, dst, DUPES))
                    continue
                seen[digest] = f

            cat = categorize(f)
            folder = root / cat
            if by_date:
                label, source = date_folder(f, now)
                date_sources[source] += 1
                folder /= label
            dst = folder / f.name
            if dst == f:
                continue
            dst = unique_path(dst, taken)
            taken.add(dst)
            plan.append((f, dst, cat))
        except OSError as e:
            print(f"  ! Skipping {f.name}: {e}", file=sys.stderr)
    return plan, date_sources


# ----------------------------------------------------------------- log / run
def load_log(root: Path) -> list:
    log = root / LOG_NAME
    if log.exists():
        try:
            return json.loads(log.read_text())
        except json.JSONDecodeError:
            pass
    return []


def save_log(root: Path, runs: list):
    (root / LOG_NAME).write_text(json.dumps(runs, indent=2))


def organize(root: Path, args):
    plan, date_sources = build_plan(root, args.recursive, args.by_date, args.dedupe)
    if not plan:
        print("Nothing to organize.")
        return

    tag = "[DRY RUN] " if args.dry_run else ""
    moves = []
    for src, dst, _ in plan:
        print(f"{tag}{src.relative_to(root)}  ->  {dst.relative_to(root)}")
        if args.dry_run:
            continue
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moves.append({"src": str(src), "dst": str(dst)})
        except (OSError, shutil.Error) as e:
            print(f"  ! Failed to move {src.name}: {e}", file=sys.stderr)

    counts = Counter(cat for _, _, cat in plan)
    print(f"\n{tag}Summary ({len(plan)} files):")
    for cat, n in counts.most_common():
        print(f"  {cat:<15}{n}")
    if args.by_date:
        print(f"\nDate sources: {date_sources['name']} from filename, "
              f"{date_sources['filesystem']} from file timestamps, "
              f"{date_sources['none']} undated")

    if moves:
        runs = load_log(root)
        runs.append({"time": datetime.now().isoformat(timespec="seconds"), "moves": moves})
        save_log(root, runs)
        print("\nDone. Run again with --undo to revert.")


def undo(root: Path, dry_run: bool):
    runs = load_log(root)
    if not runs:
        print("No previous run to undo.")
        return
    last = runs[-1]
    print(f"Undoing run from {last['time']} ({len(last['moves'])} files)")
    restored, folders = 0, set()
    for m in reversed(last["moves"]):
        src, dst = Path(m["src"]), Path(m["dst"])
        if not dst.exists():
            print(f"  ! Missing, skipped: {dst.name}", file=sys.stderr)
            continue
        target = unique_path(src, set())
        print(f"{'[DRY RUN] ' if dry_run else ''}{dst.relative_to(root)}  ->  {target.relative_to(root)}")
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst), str(target))
            folders.add(dst.parent)
        restored += 1

    if dry_run:
        return
    for folder in sorted(folders, key=lambda p: len(p.parts), reverse=True):
        for p in [folder, *folder.parents]:
            if p == root:
                break
            try:
                p.rmdir()
            except OSError:
                break
    runs.pop()
    save_log(root, runs)
    print(f"Restored {restored} files.")


def main():
    ap = argparse.ArgumentParser(description="Organize files into category folders.")
    ap.add_argument("folder", type=Path, help="Folder to organize")
    ap.add_argument("-n", "--dry-run", action="store_true", help="Preview without moving anything")
    ap.add_argument("-r", "--recursive", action="store_true", help="Include files in subfolders")
    ap.add_argument("-d", "--by-date", action="store_true",
                    help="Add YYYY-MM subfolders (filename date, else file timestamp, else 'Undated')")
    ap.add_argument("--dedupe", action="store_true", help="Move exact duplicates to a Duplicates folder")
    ap.add_argument("--undo", action="store_true", help="Revert the most recent run")
    args = ap.parse_args()

    root = args.folder.expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"Error: '{root}' is not a directory.")

    if args.undo:
        undo(root, args.dry_run)
    else:
        organize(root, args)


if __name__ == "__main__":
    main()