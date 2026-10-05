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
LOG_NAME = ".organizer_log.json"


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
    skip_dirs = set(CATEGORIES) | {"Other"}
    it = root.rglob("*") if recursive else root.iterdir()
    for p in it:
        if not p.is_file() or p.name.startswith(".") or p.name == LOG_NAME:
            continue
        # Don't re-sort files already inside a category folder
        if p.parent != root and p.relative_to(root).parts[0] in skip_dirs:
            continue
        yield p


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

    done = []
    for src, dst in moves:
        try:
            dst.parent.mkdir(exist_ok=True)
            shutil.move(str(src), str(dst))
            done.append({"from": str(src), "to": str(dst)})
        except OSError as e:
            print(f"  ! Failed to move {src.name}: {e}", file=sys.stderr)

    log = {"time": datetime.now().isoformat(timespec="seconds"), "moves": done}
    (root / LOG_NAME).write_text(json.dumps(log, indent=2))
    print(f"\nMoved {len(done)} file(s). Undo with: --undo {root}")


def undo(root: Path):
    log_path = root / LOG_NAME
    if not log_path.exists():
        sys.exit("No undo log found.")
    log = json.loads(log_path.read_text())
    restored = 0
    for m in reversed(log["moves"]):
        src, dst = Path(m["to"]), Path(m["from"])
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(unique_destination(dst)))
            restored += 1
    # Remove now-empty category folders
    for cat in list(CATEGORIES) + ["Other"]:
        d = root / cat
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    log_path.unlink()
    print(f"Restored {restored} file(s).")


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