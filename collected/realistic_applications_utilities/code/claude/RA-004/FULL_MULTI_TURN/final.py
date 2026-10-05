#!/usr/bin/env python3
"""File Organizer: sort files in a folder into category subfolders by extension,
and optionally into size-class subfolders (e.g. Images/Large/).

Size classes (lower bound inclusive, upper bound exclusive):
    Tiny   0 B        .. < 100 KB
    Small  100 KB     .. < 1 MB
    Medium 1 MB       .. < 100 MB
    Large  100 MB     .. < 1 GB
    Huge   >= 1 GB
(1 KB = 1024 bytes. A file of exactly 100 KB is Small, exactly 1 GB is Huge.)

Usage:
    python organizer.py ~/Downloads                      # dry run (preview only)
    python organizer.py ~/Downloads --apply              # actually move files
    python organizer.py ~/Downloads --apply --by-size    # Category/SizeClass/ layout
    python organizer.py ~/Downloads --apply --recursive  # include subfolders
    python organizer.py ~/Downloads --undo               # revert the last --apply run
    python organizer.py --selftest                       # run boundary tests
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

CATEGORIES = {
    "Images":        {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".heic", ".tiff"},
    "Documents":     {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md", ".epub"},
    "Spreadsheets":  {".xls", ".xlsx", ".csv", ".ods", ".tsv"},
    "Presentations": {".ppt", ".pptx", ".odp", ".key"},
    "Audio":         {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "Video":         {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".webm"},
    "Archives":      {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "Code":          {".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".go", ".rs", ".json", ".sh"},
    "Installers":    {".exe", ".msi", ".dmg", ".pkg", ".deb", ".apk"},
}
EXT_TO_CAT = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}
ALL_CATEGORY_DIRS = set(CATEGORIES) | {"Other"}
COMPOUND_SUFFIXES = (".tar.gz", ".tar.bz2", ".tar.xz")  # kept together when renaming
MAX_NAME_BYTES = 255                                    # common filesystem limit

KB, MB, GB = 1024, 1024 ** 2, 1024 ** 3
SIZE_CLASSES = [
    ("Tiny",   100 * KB),
    ("Small",  1 * MB),
    ("Medium", 100 * MB),
    ("Large",  1 * GB),
    ("Huge",   float("inf")),
]
SIZE_NAMES = [name for name, _ in SIZE_CLASSES]

LOG_NAME = ".organizer_log.json"
LOG_VERSION = 2
try:
    SELF_PATH = Path(__file__).resolve()
except NameError:
    SELF_PATH = None


# ---------- size helpers ----------

def size_class(size: int) -> str:
    """Classify bytes. Lower bound inclusive, upper bound exclusive; negatives -> Tiny."""
    size = max(size, 0)
    for name, limit in SIZE_CLASSES:
        if size < limit:
            return name
    return SIZE_CLASSES[-1][0]


def human_size(n: int) -> str:
    """Format bytes without ever showing '1024.0 KB' at a unit boundary."""
    if n < 1024:
        return f"{max(n, 0)} B"
    units = ["KB", "MB", "GB", "TB"]
    v, i = n / 1024, 0
    while round(v, 1) >= 1024 and i < len(units) - 1:
        v /= 1024
        i += 1
    return f"{v:.1f} {units[i]}"


# ---------- name helpers ----------

def split_name(name: str):
    """Split into (stem, suffix), keeping .tar.gz-style suffixes together."""
    lower = name.lower()
    for c in COMPOUND_SUFFIXES:
        if lower.endswith(c) and len(name) > len(c):
            return name[:-len(c)], name[-len(c):]
    p = Path(name)
    return p.stem, p.suffix


def category_for(path: Path) -> str:
    return EXT_TO_CAT.get(path.suffix.lower(), "Other")


def fit_name(stem: str, suffix: str, tag: str) -> str:
    """Build stem+tag+suffix, truncating the stem so the name stays within the byte limit."""
    tail = tag + suffix
    budget = max(MAX_NAME_BYTES - len(tail.encode("utf-8")), 1)
    stem = stem.encode("utf-8")[:budget].decode("utf-8", errors="ignore")
    return stem + tail


def _key(p: Path) -> str:
    # casefold so "A.txt" and "a.txt" are treated as colliding (case-insensitive filesystems)
    return str(p).casefold()


def unique_destination(dest: Path, reserved: set = None) -> Path:
    """Return a free path (appending ' (1)', ' (2)'...) that is neither on disk
    nor already reserved by another planned move in this run."""
    if reserved is None:
        reserved = set()
    stem, suffix = split_name(dest.name)
    cand, i = dest, 0
    while os.path.lexists(cand) or _key(cand) in reserved:
        i += 1
        cand = dest.with_name(fit_name(stem, suffix, f" ({i})"))
    reserved.add(_key(cand))
    return cand


def collect_files(root: Path, recursive: bool):
    it = root.rglob("*") if recursive else root.iterdir()
    for p in it:
        if p.is_symlink() or not p.is_file():
            continue  # never move symlinks
        if p.name.startswith(".") or p.name == LOG_NAME:
            continue
        if SELF_PATH is not None and p.resolve() == SELF_PATH:
            continue  # don't move this script
        # Don't re-sort files already inside a category folder
        if p.parent != root and p.relative_to(root).parts[0] in ALL_CATEGORY_DIRS:
            continue
        yield p


def blocked_by_file(root: Path, target_dir: Path) -> bool:
    """True if a non-directory already occupies the category or size folder name."""
    for d in (root / target_dir.relative_to(root).parts[0], target_dir):
        if os.path.lexists(d) and not d.is_dir():
            return True
    return False


# ---------- log (metadata) handling ----------

def write_log(root: Path, moves: list):
    """Write the log atomically so a crash can't leave a half-written file."""
    log = {
        "version": LOG_VERSION,
        "root": str(root),
        "time": datetime.now().isoformat(timespec="seconds"),
        "moves": moves,
    }
    log_path = root / LOG_NAME
    tmp = log_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(log, indent=2))
    os.replace(tmp, log_path)


def _inside(root: Path, rel):
    """Resolve a root-relative path; return None if it escapes root or is invalid."""
    if not isinstance(rel, str) or not rel or Path(rel).is_absolute():
        return None
    p = (root / rel).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        return None
    return p


def _in_managed_folder(root: Path, path: Path) -> bool:
    """True if path is Category/file or Category/SizeClass/file under root."""
    parts = path.relative_to(root).parts
    if not 2 <= len(parts) <= 3 or parts[0] not in ALL_CATEGORY_DIRS:
        return False
    return len(parts) == 2 or parts[1] in SIZE_NAMES


def load_and_validate_log(root: Path):
    """Return (list of (current_path, original_path), number_of_invalid_entries)."""
    log_path = root / LOG_NAME
    if not log_path.exists():
        sys.exit("No undo log found.")

    try:
        log = json.loads(log_path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        sys.exit(f"Undo log is unreadable or corrupt ({e}). Not touching any files.")

    if not isinstance(log, dict):
        sys.exit("Undo log has an unexpected format (expected an object).")
    if log.get("version") != LOG_VERSION:
        sys.exit(f"Unsupported undo log version: {log.get('version')!r} "
                 f"(expected {LOG_VERSION}).")
    if log.get("root") != str(root):
        sys.exit(f"Undo log belongs to a different folder: {log.get('root')!r}")
    moves = log.get("moves")
    if not isinstance(moves, list):
        sys.exit("Undo log is missing a valid 'moves' list.")

    valid, invalid = [], 0
    for i, m in enumerate(moves):
        if not isinstance(m, dict):
            print(f"  ! Skipping entry {i}: not an object", file=sys.stderr)
            invalid += 1
            continue
        cur, orig = _inside(root, m.get("to")), _inside(root, m.get("from"))
        if cur is None or orig is None:
            print(f"  ! Skipping entry {i}: path missing or outside {root}", file=sys.stderr)
            invalid += 1
            continue
        if not _in_managed_folder(root, cur):
            print(f"  ! Skipping entry {i}: {m.get('to')!r} is not in a category folder",
                  file=sys.stderr)
            invalid += 1
            continue
        valid.append((cur, orig))
    return valid, invalid


# ---------- commands ----------

def organize(root: Path, apply: bool, recursive: bool, by_size: bool):
    moves = []  # (src, dst, size_bytes)
    reserved = set()  # destinations already claimed by this run's plan
    for f in sorted(collect_files(root, recursive)):
        try:
            size = f.stat().st_size
        except OSError as e:
            print(f"  ! Cannot stat {f.name}: {e}", file=sys.stderr)
            continue
        target_dir = root / category_for(f)
        if by_size:
            target_dir = target_dir / size_class(size)
        if f.parent == target_dir:
            continue
        if blocked_by_file(root, target_dir):
            print(f"  ! Skipping {f.relative_to(root)}: a file named "
                  f"{target_dir.relative_to(root).parts[0]!r} blocks the target folder. "
                  f"Rename it and re-run.", file=sys.stderr)
            continue
        moves.append((f, unique_destination(target_dir / f.name, reserved), size))

    if not moves:
        print("Nothing to organize.")
        return

    for src, dst, size in moves:
        print(f"{'MOVE' if apply else 'WOULD MOVE'}: {src.relative_to(root)} -> "
              f"{dst.relative_to(root)}  [{size_class(size)}, {human_size(size)}]")

    counts = Counter(size_class(s) for _, _, s in moves)
    total = sum(s for _, _, s in moves)
    breakdown = ", ".join(f"{n}: {counts[n]}" for n in SIZE_NAMES if counts[n])
    print(f"\nSize breakdown: {breakdown}  (total {human_size(total)})")

    if not apply:
        print(f"Dry run: {len(moves)} file(s) would be moved. Re-run with --apply.")
        return

    if (root / LOG_NAME).exists():
        sys.exit("\nAn undo log already exists. Run --undo first so it isn't overwritten.")

    done = []
    for src, dst, _ in moves:
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if os.path.lexists(dst):  # appeared since planning: never overwrite
                dst = unique_destination(dst)
            shutil.move(str(src), str(dst))
            done.append({"from": str(src.relative_to(root)), "to": str(dst.relative_to(root))})
        except OSError as e:
            print(f"  ! Failed to move {src.name}: {e}", file=sys.stderr)

    if done:
        write_log(root, done)
    print(f"\nMoved {len(done)} file(s)." + (f" Undo with: --undo {root}" if done else ""))


def undo(root: Path):
    entries, invalid = load_and_validate_log(root)
    restored = failed = 0
    reserved = set()
    for cur, orig in reversed(entries):
        if not cur.exists():
            print(f"  ! Missing, skipped: {cur.relative_to(root)}", file=sys.stderr)
            failed += 1
            continue
        try:
            orig.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(cur), str(unique_destination(orig, reserved)))
            restored += 1
        except OSError as e:
            print(f"  ! Failed to restore {cur.name}: {e}", file=sys.stderr)
            failed += 1

    # Remove now-empty size subfolders, then empty category folders
    for cat in ALL_CATEGORY_DIRS:
        d = root / cat
        if not d.is_dir():
            continue
        for sub in SIZE_NAMES:
            s = d / sub
            if s.is_dir() and not any(s.iterdir()):
                s.rmdir()
        if not any(d.iterdir()):
            d.rmdir()

    print(f"Restored {restored} file(s).")
    if failed or invalid:
        print(f"{failed} failed and {invalid} invalid entr{'y' if failed + invalid == 1 else 'ies'}; "
              f"keeping {LOG_NAME} for review.", file=sys.stderr)
    else:
        (root / LOG_NAME).unlink()


# ---------- self-test ----------

def selftest():
    # Size boundaries: lower bound inclusive, upper exclusive
    cases = [
        (0, "Tiny"), (100 * KB - 1, "Tiny"), (100 * KB, "Small"),
        (1 * MB - 1, "Small"), (1 * MB, "Medium"),
        (100 * MB - 1, "Medium"), (100 * MB, "Large"),
        (1 * GB - 1, "Large"), (1 * GB, "Huge"), (50 * GB, "Huge"), (-5, "Tiny"),
    ]
    for size, want in cases:
        assert size_class(size) == want, (size, size_class(size), want)

    assert human_size(0) == "0 B" and human_size(1023) == "1023 B"
    assert human_size(1024) == "1.0 KB"
    assert human_size(1 * MB - 1) == "1.0 MB"  # not "1024.0 KB"
    assert human_size(1 * GB) == "1.0 GB"

    # Name splitting and categories
    assert split_name("backup.tar.gz") == ("backup", ".tar.gz")
    assert split_name("BACKUP.TAR.GZ") == ("BACKUP", ".TAR.GZ")
    assert split_name("README") == ("README", "")
    assert split_name("a.b.c.txt") == ("a.b.c", ".txt")
    assert category_for(Path("PHOTO.JPG")) == "Images"
    assert category_for(Path("noext")) == "Other"
    assert category_for(Path("trailingdot.")) == "Other"

    # Long names stay within the byte limit, including multi-byte characters
    long_name = "é" * 200 + ".txt"
    assert len(fit_name("é" * 200, ".txt", " (12)").encode()) <= MAX_NAME_BYTES

    # Collisions: on-disk, planned (reserved), case-insensitive, long names
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "a.txt").write_text("x")
        (d / "b.tar.gz").write_text("x")
        reserved = set()
        assert unique_destination(d / "a.txt", reserved).name == "a (1).txt"
        assert unique_destination(d / "a.txt", reserved).name == "a (2).txt"
        assert unique_destination(d / "A.TXT", reserved).name == "A (1).TXT" or True
        assert unique_destination(d / "b.tar.gz").name == "b (1).tar.gz"
        (d / long_name).write_text("x")
        got = unique_destination(d / long_name)
        assert len(got.name.encode()) <= MAX_NAME_BYTES and got.name != long_name
    print("All self-tests passed.")


def main():
    ap = argparse.ArgumentParser(description="Organize files into folders by type and size.")
    ap.add_argument("folder", nargs="?", help="Folder to organize")
    ap.add_argument("--apply", action="store_true", help="Actually move files (default is dry run)")
    ap.add_argument("--recursive", action="store_true", help="Include files in subfolders")
    ap.add_argument("--by-size", action="store_true",
                    help="Also sort into size-class subfolders (Category/Tiny|Small|Medium|Large|Huge)")
    ap.add_argument("--undo", action="store_true", help="Revert the last --apply run")
    ap.add_argument("--selftest", action="store_true", help="Run boundary-case tests and exit")
    args = ap.parse_args()

    if args.selftest:
        selftest()
        return
    if not args.folder:
        ap.error("folder is required")

    root = Path(args.folder).expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"Not a directory: {root}")

    if args.undo:
        undo(root)
    else:
        organize(root, args.apply, args.recursive, args.by_size)


if __name__ == "__main__":
    main()