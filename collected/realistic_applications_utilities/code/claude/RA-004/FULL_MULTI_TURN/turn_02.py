#!/usr/bin/env python3
"""File Organizer: sort files in a folder into category subfolders by extension.

Usage:
    python organizer.py ~/Downloads                      # dry run (preview only)
    python organizer.py ~/Downloads --apply              # actually move files
    python organizer.py ~/Downloads --apply --recursive  # include subfolders
    python organizer.py ~/Downloads --undo               # revert the last --apply run
"""
import argparse
import json
import os
import shutil
import sys
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
LOG_NAME = ".organizer_log.json"
LOG_VERSION = 2


def category_for(path: Path) -> str:
    return EXT_TO_CAT.get(path.suffix.lower(), "Other")


def unique_destination(dest: Path) -> Path:
    """Append (1), (2), ... if a file with the same name already exists."""
    if not dest.exists():
        return dest
    i = 1
    while True:
        candidate = dest.with_name(f"{dest.stem} ({i}){dest.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def collect_files(root: Path, recursive: bool):
    it = root.rglob("*") if recursive else root.iterdir()
    for p in it:
        if not p.is_file() or p.name.startswith(".") or p.name == LOG_NAME:
            continue
        # Don't re-sort files already inside a category folder
        if p.parent != root and p.relative_to(root).parts[0] in ALL_CATEGORY_DIRS:
            continue
        yield p


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


def load_and_validate_log(root: Path):
    """Return (list of (current_path, original_path), number_of_invalid_entries).
    Exits with a clear message if the log is unusable as a whole."""
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
        # A moved file must sit directly inside a category folder
        if cur.parent.parent != root or cur.parent.name not in ALL_CATEGORY_DIRS:
            print(f"  ! Skipping entry {i}: {m.get('to')!r} is not in a category folder",
                  file=sys.stderr)
            invalid += 1
            continue
        valid.append((cur, orig))
    return valid, invalid


# ---------- commands ----------

def organize(root: Path, apply: bool, recursive: bool):
    moves = []
    for f in collect_files(root, recursive):
        target_dir = root / category_for(f)
        if f.parent == target_dir:
            continue
        moves.append((f, unique_destination(target_dir / f.name)))

    if not moves:
        print("Nothing to organize.")
        return

    for src, dst in moves:
        print(f"{'MOVE' if apply else 'WOULD MOVE'}: {src.relative_to(root)} -> {dst.relative_to(root)}")

    if not apply:
        print(f"\nDry run: {len(moves)} file(s) would be moved. Re-run with --apply.")
        return

    if (root / LOG_NAME).exists():
        sys.exit("\nAn undo log already exists. Run --undo first so it isn't overwritten.")

    done = []
    for src, dst in moves:
        try:
            dst.parent.mkdir(exist_ok=True)
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
    for cur, orig in reversed(entries):
        if not cur.exists():
            print(f"  ! Missing, skipped: {cur.relative_to(root)}", file=sys.stderr)
            failed += 1
            continue
        try:
            orig.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(cur), str(unique_destination(orig)))
            restored += 1
        except OSError as e:
            print(f"  ! Failed to restore {cur.name}: {e}", file=sys.stderr)
            failed += 1

    # Remove now-empty category folders
    for cat in ALL_CATEGORY_DIRS:
        d = root / cat
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()

    print(f"Restored {restored} file(s).")
    if failed or invalid:
        print(f"{failed} failed and {invalid} invalid entr{'y' if failed + invalid == 1 else 'ies'}; "
              f"keeping {LOG_NAME} for review.", file=sys.stderr)
    else:
        (root / LOG_NAME).unlink()


def main():
    ap = argparse.ArgumentParser(description="Organize files into folders by type.")
    ap.add_argument("folder", help="Folder to organize")
    ap.add_argument("--apply", action="store_true", help="Actually move files (default is dry run)")
    ap.add_argument("--recursive", action="store_true", help="Include files in subfolders")
    ap.add_argument("--undo", action="store_true", help="Revert the last --apply run")
    args = ap.parse_args()

    root = Path(args.folder).expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"Not a directory: {root}")

    if args.undo:
        undo(root)
    else:
        organize(root, args.apply, args.recursive)


if __name__ == "__main__":
    main()