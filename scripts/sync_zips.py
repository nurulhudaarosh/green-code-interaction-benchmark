#!/usr/bin/env python3
"""Ingest member submission ZIPs from zip_src/ — a fast local alternative
to the (throttled) Google Drive sync.

Tracking works exactly like the Drive file ledger, but per ZIP:
  - each ZIP is identified by (name, sha256) in results/zip_ledger.jsonl
  - a ZIP whose content was already extracted is NEVER extracted again
  - a member updating their submission produces a new sha256 -> the new
    ZIP gets extracted (merged on top; local manual fixes in collected/
    are still never overwritten by ingest)
  - extracted files land in inbox/<category>/ exactly like Drive sync, so
    the same ingest -> harness -> measure steps run afterwards, and the
    Drive downloader sees them on disk and never fetches them

The category is detected from the task-id prefixes inside the ZIP (e.g.
IM-007 -> image_media_processing), so the ZIP file name does not matter.

Usage:
    python3 scripts/sync_zips.py             # extract new ZIPs
    python3 scripts/sync_zips.py --dry-run   # only report what would happen
    python3 scripts/sync_zips.py --force     # re-extract even known ZIPs
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from ingest_zips import CATEGORY_BY_CODE  # noqa: E402

ZIP_SRC = REPO / "zip_src"
LEDGER = REPO / "results" / "zip_ledger.jsonl"
INBOX = REPO / "inbox"

TASK_PREFIX = re.compile(r"^([A-Z]{2})-\d+$")
_hash_cache = {}  # name -> (size, mtime, sha256)


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def zip_sha(path: Path) -> str:
    st = path.stat()
    cached = _hash_cache.get(path.name)
    if cached and cached[0] == st.st_size and cached[1] == st.st_mtime:
        return cached[2]
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    sha = h.hexdigest()
    _hash_cache[path.name] = (st.st_size, st.st_mtime, sha)
    return sha


def load_ledger() -> dict:
    done = {}
    if LEDGER.is_file():
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                done[(e["zip"], e["sha256"])] = e
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def append_ledger(entry: dict):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def member_dest(rel_inside: str, category: str) -> Path | None:
    """Map a zip-internal path to its inbox/<category>/ destination.

    Layout inside a member zip:
        Green-Code-Collection/.collection/code/<model>/<TASK>/<INT>/<f>.py
        Green-Code-Collection/.collection/raw/...
        Green-Code-Collection/.collection/logs/...
        Green-Code-Collection/.collection/state.json
        Green-Code-Collection/dataset/dataset.json
    """
    parts = [p for p in rel_inside.split("/") if p not in ("", ".")]
    if not parts or any(p in ("..", "__MACOSX") for p in parts):
        return None
    if ".collection" in parts:
        i = parts.index(".collection")
        rest = parts[i + 1:]
        if not rest:
            return INBOX / category / ".collection"
        return INBOX / category / ".collection" / Path(*rest)
    if len(parts) >= 2 and parts[-2] == "dataset" and parts[-1] == "dataset.json":
        return INBOX / category / "dataset" / "dataset.json"
    if parts[-1] in ("member_collection.ipynb",):
        return INBOX / category / parts[-1]
    return None


def detect_category(zf: zipfile.ZipFile) -> tuple[str | None, dict]:
    """Category from task-id prefixes in code paths + small stats."""
    counts = {}
    n_code = 0
    for info in zf.infolist():
        if info.is_dir():
            continue
        parts = [p for p in info.filename.split("/") if p]
        if ".collection" not in parts:
            continue
        i = parts.index(".collection")
        # .collection/code/<model>/<TASK>/<INT>/<file>.py
        if len(parts) >= i + 5 and parts[i + 1] == "code":
            n_code += 1
            m = TASK_PREFIX.match(parts[i + 3])
            if m:
                code = m.group(1)
                counts[code] = counts.get(code, 0) + 1
    if not counts:
        return None, {"code_files": n_code}
    best = max(counts, key=counts.get)
    return CATEGORY_BY_CODE.get(best), {"code_files": n_code, "prefixes": counts}


def extract_zip(zf: zipfile.ZipFile, category: str) -> int:
    """Extract member files into inbox/<category>/ (overwrite allowed)."""
    n = 0
    for info in zf.infolist():
        if info.is_dir():
            continue
        dest = member_dest(info.filename, category)
        if dest is None:
            continue
        if not str(dest.resolve()).startswith(str(INBOX.resolve())):
            continue  # path traversal guard
        dest.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info) as src, dest.open("wb") as out:
            while True:
                chunk = src.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
        n += 1
    return n


def dataset_tasks_of(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        tasks = data.get("tasks") if isinstance(data, dict) else data
        return tasks if tasks else None
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def normalize_dataset_inplace(path: Path) -> bool:
    """Normalize known generator quirks in a dataset file:
    - reference_solution.python_implementation -> also exposed as .code
    Returns True if the file was rewritten."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    tasks = data.get("tasks") if isinstance(data, dict) else data
    if not tasks:
        return False
    changed = False
    for t in tasks:
        rs = t.get("reference_solution")
        if isinstance(rs, dict) and not rs.get("code") \
                and rs.get("python_implementation"):
            rs["code"] = rs["python_implementation"]
            changed = True
    if changed:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    return changed


def ensure_frozen_dataset(category: str) -> str:
    """Make sure dataset/<category>/dataset.json is valid.

    Uses the zip-extracted inbox copy when the local one is missing;
    repairs it if corrupt; NEVER replaces an already-valid local dataset.
    Returns 'frozen' | 'kept' | 'repaired' | 'missing'.
    """
    local = REPO / "dataset" / category / "dataset.json"
    inbox_ds = INBOX / category / "dataset" / "dataset.json"
    if dataset_tasks_of(local):
        if normalize_dataset_inplace(local):
            return "normalized"
        return "kept"
    if not inbox_ds.is_file():
        return "missing"
    if dataset_tasks_of(inbox_ds):
        src = inbox_ds
    else:
        r = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "repair_dataset.py"),
             str(inbox_ds), "-o", str(inbox_ds)],
            capture_output=True, text=True, timeout=600, cwd=REPO)
        if r.returncode != 0 or not dataset_tasks_of(inbox_ds):
            return "repair-failed"
        src = inbox_ds
    normalize_dataset_inplace(src)
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_bytes(src.read_bytes())
    return "frozen" if src is inbox_ds else "repaired"


def process_new_zips(dry_run=False, force=False) -> dict:
    """Extract every not-yet-seen ZIP from zip_src/.

    Returns {category: files_extracted} for the ZIPs processed this call.
    """
    if not ZIP_SRC.is_dir():
        return {}
    ledger = load_ledger()
    touched = {}
    for zp in sorted(ZIP_SRC.glob("*.zip")):
        try:
            sha = zip_sha(zp)
        except OSError as e:
            print(f"  {zp.name}: unreadable ({e})")
            continue
        if not force and (zp.name, sha) in ledger:
            continue
        try:
            with zipfile.ZipFile(zp) as zf:
                category, stats = detect_category(zf)
                if category is None:
                    print(f"  {zp.name}: cannot detect category "
                          f"({stats}) — skipped")
                    continue
                if dry_run:
                    print(f"  WOULD EXTRACT {zp.name} -> inbox/{category}/ "
                          f"({stats.get('code_files', 0)} code files)")
                    continue
                n = extract_zip(zf, category)
        except zipfile.BadZipFile as e:
            print(f"  {zp.name}: BAD ZIP ({e})")
            continue
        ds_state = ensure_frozen_dataset(category)
        append_ledger({"zip": zp.name, "sha256": sha,
                       "size": zp.stat().st_size, "category": category,
                       "files": n, "dataset": ds_state,
                       "extracted_at": now_iso()})
        print(f"  EXTRACTED {zp.name} -> inbox/{category}/ "
              f"({n} files, dataset={ds_state})")
        touched[category] = touched.get(category, 0) + n
    return touched


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="re-extract ZIPs already in the ledger")
    args = ap.parse_args()
    print(f"zip source: {ZIP_SRC}")
    touched = process_new_zips(dry_run=args.dry_run, force=args.force)
    if not args.dry_run:
        for cat, n in sorted(touched.items()):
            print(f"-> inbox/{cat}/: {n} new file(s)")
        if not touched:
            print("no new ZIPs (already tracked in results/zip_ledger.jsonl)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
