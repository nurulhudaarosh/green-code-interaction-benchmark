#!/usr/bin/env python3
"""Download member submission folders from shared Google Drive links.

Simple model: each source is a shared Drive *folder*. Download the whole
folder into inbox/<category>/ and keep it on disk. Re-runs use gdown's
resume mode, so already-downloaded files are skipped and only new/changed
files are fetched. The measurement ledger (results/measurement_ledger.jsonl)
is what compares against the previous record and decides what is new, so
nothing needs to be zipped or unzipped here.

Reads config/drive_sources.json. Requires: pip install gdown

Usage:
    python3 scripts/sync_drive.py              # sync all configured sources
    python3 scripts/sync_drive.py --only SR    # one member/category prefix
"""

import argparse
import json
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# gdown makes requests without a timeout; Google throttling can otherwise hang
# the whole pipeline forever. Fail the request instead and retry/move on.
socket.setdefaulttimeout(30)

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "drive_sources.json"
INBOX = REPO / "inbox"


def load_state():
    state = INBOX / ".sync_state.json"
    if state.is_file():
        try:
            return json.loads(state.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def save_state(state):
    INBOX.mkdir(parents=True, exist_ok=True)
    (INBOX / ".sync_state.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8")


def sync_folder(gdown, url: str, dest: Path, attempts: int = 2) -> bool:
    """Download whole folder into dest. resume=True skips existing files."""
    dest.mkdir(parents=True, exist_ok=True)
    for i in range(1, attempts + 1):
        try:
            gdown.download_folder(url, output=str(dest), quiet=True,
                                  use_cookies=False, resume=True)
            return True
        except Exception as e:  # noqa: BLE001 - gdown raises DownloadError
            msg = str(e).splitlines()[0] if str(e) else type(e).__name__
            print(f"  attempt {i}/{attempts} failed: {msg}")
            if i < attempts:
                time.sleep(10 * i)
    # Even on failure, partial files stay on disk and are reused next time.
    return any(p.is_file() for p in dest.rglob("*"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="filter by member/category substring")
    args = ap.parse_args()

    try:
        import gdown
    except ImportError:
        print("ERROR: gdown not installed. Run: pip install gdown", file=sys.stderr)
        return 1

    if not CONFIG.is_file():
        print(f"ERROR: {CONFIG} missing", file=sys.stderr)
        return 1

    sources = json.loads(CONFIG.read_text(encoding="utf-8")).get("sources", [])
    state = load_state()
    INBOX.mkdir(parents=True, exist_ok=True)
    ok_count = fail_count = 0

    for src in sources:
        key = f"{src.get('category')}|{src.get('member')}"
        if args.only and args.only.upper() not in key.upper():
            continue
        link = (src.get("link") or "").strip()
        if not link or "PASTE" in link:
            print(f"skip  {key} (no link configured)")
            continue

        dest = INBOX / src["category"]
        before = sum(1 for p in dest.rglob("*") if p.is_file()) if dest.is_dir() else 0
        print(f"sync  {key} -> inbox/{src['category']}/", flush=True)
        try:
            ok = sync_folder(gdown, link, dest)
        except Exception as e:  # noqa: BLE001 - one source must not stop the rest
            print(f"  ERROR: {type(e).__name__}: {str(e).splitlines()[0]}")
            ok = False
        after = sum(1 for p in dest.rglob("*") if p.is_file()) if dest.is_dir() else 0
        if ok:
            ok_count += 1
            state[key] = {
                "files": after,
                "new_files": after - before,
                "synced_at": datetime.now(timezone.utc).isoformat(),
            }
            print(f"  files on disk: {after} (+{after - before} new)")
        else:
            fail_count += 1
            print(f"  FAILED (files on disk: {after})")

    save_state(state)
    print(f"\nsync done: {ok_count} ok, {fail_count} failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
