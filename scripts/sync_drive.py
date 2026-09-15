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
import hashlib
import json
import os
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
LEDGER = REPO / "results" / "file_ledger.jsonl"
MAX_NEW_PER_PASS = 500  # new files fetched per source per pass; the rest wait


def collected_rel(rel: str) -> str:
    """Normalize an inbox-relative path (may contain /.collection/) to the
    collected-layout path used by unit['rel'] in measurement."""
    return rel.replace("/.collection/", "/", 1) if "/.collection/" in rel else rel


def load_ledger() -> dict:
    if not LEDGER.is_file():
        return {}
    out = {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
            key = r.get("file_id") or (f"rel:{r['rel']}" if r.get("rel") else None)
            if key:
                out[key] = r
        except (json.JSONDecodeError, KeyError):
            pass
    return out


def save_ledger(ledger: dict):
    """Atomically merge `ledger` (key -> entry) into the on-disk file ledger.

    Merge (not blind rewrite) so a concurrent writer — e.g. the measurement
    runner marking a file 'measured' while the downloader adds new files —
    never loses the other side's update. flock serializes writers.
    """
    import fcntl
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    lock_path = LEDGER.parent / ".file_ledger.lock"
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            disk = load_ledger() if LEDGER.is_file() else {}
            disk.update(ledger)
            tmp = LEDGER.with_suffix(".jsonl.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                for r in sorted(disk.values(),
                                key=lambda x: (x.get("rel") or "", x.get("file_id") or "")):
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            tmp.replace(LEDGER)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def record_measured(ledger: dict, rel: str, sha: str = None,
                    task_key: str = None):
    """Mark a unit's file as measured. Seeds the entry when the file was
    downloaded before the ledger existed (file_id unknown)."""
    match = next((e for e in ledger.values()
                  if e.get("rel") == rel and e.get("file_id")), None)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if match:
        match.update({"status": "measured", "measured_at": now,
                      "sha256": sha or match.get("sha256")})
        return
    ident = task_key or rel
    ledger[ident] = {"file_id": None, "rel": rel, "name": Path(rel).name,
                     "status": "measured", "sha256": sha,
                     "downloaded_at": None, "measured_at": now,
                     "fails": 0, "backoff_until": None, "error": None,
                     "task_key": task_key, "source": None}
    save_ledger(ledger)


def can_download(ledger: dict, file_id: str) -> tuple[bool, str]:
    e = ledger.get(file_id)
    if not e:
        return True, "new"
    st = e["status"]
    if st in ("downloaded", "measured", "local", "skipped"):
        return False, "already_" + st
    if st == "failed" and e.get("backoff_until") and \
            time.time() < float(e["backoff_until"]):
        return False, "backoff"
    return True, "retry"


def mark_downloaded(ledger: dict, file_id: str, rel: str, sha: str):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ledger[file_id] = {"file_id": file_id, "rel": rel, "name": Path(rel).name,
                       "status": "downloaded", "sha256": sha,
                       "downloaded_at": now, "measured_at": None,
                       "fails": 0, "backoff_until": None, "error": None,
                       "task_key": None, "source": None}


def mark_failed(ledger: dict, file_id: str, rel: str, error: str):
    e = ledger.get(file_id, {})
    fails = int(e.get("fails", 0)) + 1
    backoff = min(24 * 3600, 900 * (2 ** (fails - 1)))  # 15m, 30m, 1h, 2h, ... 24h cap
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ledger[file_id] = {"file_id": file_id, "rel": rel, "name": Path(rel).name,
                       "status": "failed", "sha256": e.get("sha256"),
                       "downloaded_at": e.get("downloaded_at"),
                       "measured_at": None, "fails": fails,
                       "backoff_until": str(time.time() + backoff),
                       "error": error, "task_key": None, "source": None}


def structure_complete(dest: Path) -> tuple[bool, str]:
    """A synced member folder needs .collection/ AND a non-empty
    dataset/dataset.json somewhere in its tree (kit layout)."""
    if not dest.is_dir():
        return False, "not synced yet"
    roots = [dest] + [p for p in dest.iterdir() if p.is_dir()]
    for r in roots:
        if (r / ".collection").is_dir():
            ds = list(r.glob("dataset/dataset.json")) + list(r.glob("*/dataset/dataset.json"))
            if ds:
                for f in ds:
                    try:
                        if json.loads(f.read_text(encoding="utf-8")).get("tasks"):
                            return True, "ok"
                    except (OSError, json.JSONDecodeError):
                        continue
                return False, f"dataset.json found but empty/invalid: {ds[0]}"
            return False, "dataset/dataset.json missing (sync incomplete?)"
    return False, ".collection/ missing (sync incomplete or wrong link)"


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


def snapshot(dest: Path) -> dict:
    """path -> content hash for every file under dest (used for change log)."""
    out = {}
    if dest.is_dir():
        for p in dest.rglob("*"):
            if p.is_file():
                try:
                    out[str(p.relative_to(dest))] = \
                        hashlib.sha256(p.read_bytes()).hexdigest()[:16]
                except OSError:
                    pass
    return out


def log_change(source: str, new: list, changed: list, removed: list):
    """Append one entry per source with anything that moved this pass.
    Members are expected to only ADD work; CHANGED/REMOVED mean a member
    replaced an existing file — review it and re-apply your local fix in
    collected/ if needed (your collected edits are never overwritten)."""
    rec = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "source": source, "new": new, "changed": changed,
           "removed": removed}
    with open(INBOX / ".sync_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def show_log(n: int) -> int:
    logf = INBOX / ".sync_log.jsonl"
    if not logf.is_file():
        print("no sync log yet")
        return 0
    lines = logf.read_text(encoding="utf-8").strip().splitlines()[-n:]
    for line in lines:
        r = json.loads(line)
        print(f"{r['ts']}  {r['source']}: +{len(r['new'])} new"
              f", ~{len(r['changed'])} changed, -{len(r['removed'])} removed")
        for kind in ("new", "changed", "removed"):
            for f in r[kind][:15]:
                print(f"    {kind[0]} {f}")
            if len(r[kind]) > 15:
                print(f"    ... +{len(r[kind]) - 15} more {kind}")
    return 0


def show_ledger(n: int) -> int:
    ledger = load_ledger()
    if not ledger:
        print("file ledger empty")
        return 0
    from collections import Counter
    cnt = Counter(e["status"] for e in ledger.values())
    print(f"file ledger: {len(ledger)} files tracked")
    for st in ("downloaded", "measured", "failed",
               "already_downloaded", "already_measured"):
        if cnt.get(st):
            print(f"  {st}: {cnt[st]}")
    waiting = [(e["file_id"], e.get("backoff_until"))
               for e in ledger.values()
               if e["status"] == "failed" and e.get("backoff_until")
               and time.time() < float(e["backoff_until"])]
    print(f"  waiting (backoff): {len(waiting)}")
    for e in sorted(ledger.values(), key=lambda x: x.get("rel") or "")[-n:]:
        print(f"  {e['status']:12s} {e['rel']}")
    return 0


def acquire_lock(wait=900):
    """One sync at a time — two gdown processes on the same Drive folder
    trigger Google rate limits and both stall silently. While another sync
    is active we queue up and wait (up to `wait` seconds) instead of failing.
    """
    import fcntl
    lock = open(INBOX / ".sync.lock", "w")
    deadline = time.time() + wait
    while True:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock.write(str(os.getpid()))
            lock.flush()
            return lock
        except OSError:
            if time.time() >= deadline:
                return None
            print(f"  waiting for another sync_drive to finish "
                  f"(up to {wait}s)...", flush=True)
            time.sleep(20)


def sync_folder(gdown, url: str, dest: Path, cookies=None,
                ledger: dict | None = None, source_key: str = None,
                max_new: int = MAX_NEW_PER_PASS) -> bool:
    """Download folder contents into dest WITHOUT re-requesting files
    that are already saved locally. Each Drive file id is recorded in the
    file ledger (results/file_ledger.jsonl). Once a file is downloaded or
    measured it is never requested from Drive again; members only add new
    files, so a failed file is retried later with exponential backoff
    (15m → 30m → 1h → … 24h cap) instead of being hammered every pass.
    """
    if ledger is None:
        ledger = load_ledger()
    dest.mkdir(parents=True, exist_ok=True)
    modes = ([("cookies", cookies)] if cookies else []) + [("anonymous", None)]
    ok = False
    for mode_name, ck in modes:
        kw = dict(output=str(dest), quiet=False, skip_download=True, resume=True)
        if ck:
            kw.update(use_cookies=True, cookies_file=str(ck))
        else:
            kw["use_cookies"] = False
        try:
            print(f"  listing folder via {mode_name}...", flush=True)
            files = gdown.download_folder(url, **kw)
        except Exception as e:  # noqa: BLE001
            msg = str(e).strip() or type(e).__name__
            print(f"  [{mode_name}] list failed: {msg.splitlines()[0]}")
            if "public link" in msg or "403" in msg or "401" in msg:
                print("  hint: Google throttling this mode; the next "
                      "auth mode or a later pass usually works.")
            continue
        if not files:
            print(f"  [{mode_name}] no files listed (empty/access denied)")
            continue
        downloaded = waiting = already = 0
        eligible = []
        for f in files:
            allowed, reason = can_download(ledger, f.id)
            if not allowed:
                if reason == "backoff":
                    waiting += 1
                else:
                    already += 1
                continue
            eligible.append(f)
        for f in eligible[:max_new]:
            local = Path(f.local_path)
            if local.exists() and local.stat().st_size > 0:
                rel = collected_rel(str(local.relative_to(INBOX)))
                sha = hashlib.sha256(local.read_bytes()).hexdigest()[:16]
                mark_downloaded(ledger, f.id, rel, sha)
                downloaded += 1
                continue
            parent = local.parent
            parent.mkdir(parents=True, exist_ok=True)
            for i in range(1, 2):
                try:
                    gdown.download(id=f.id, output=str(parent),
                                   quiet=True, resume=True)
                except Exception as e:  # noqa: BLE001
                    msg = str(e).strip().splitlines()[0]
                    rel = collected_rel(str(local.relative_to(INBOX)))
                    mark_failed(ledger, f.id, rel, msg)
                    print(f"  FAIL {local.relative_to(INBOX)}"
                          f" ({msg[:50]})")
                    time.sleep(3)
                    break
                sha = hashlib.sha256(local.read_bytes()).hexdigest()[:16]
                rel = collected_rel(str(local.relative_to(INBOX)))
                mark_downloaded(ledger, f.id, rel, sha)
                downloaded += 1
                time.sleep(1)  # gap between files
            if len(eligible) > MAX_NEW_PER_PASS:
                break
        still = [e for e in eligible[max_new:]
                  if can_download(ledger, e.id)[0]]
        already += len(still)
        print(f"  done: {downloaded} downloaded, {already} already saved,"
              f" {waiting} waiting (backoff), {len(still)} left for next pass")
        if downloaded > 0 or already > 0:
            ok = True
        if downloaded > 0 or still or waiting:
            save_ledger(ledger)
        # keep trying other auth modes when the structure is still missing
        complete, why = structure_complete(dest)
        if complete or mode_name == "anonymous":
            return ok
        print(f"  [{mode_name}] structure incomplete ({why}) — "
              "cookies may be stale; trying anonymous")
    save_ledger(ledger)
    return ok and any(p.is_file() for p in dest.rglob("*"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="filter by member/category substring")
    ap.add_argument("--log", type=int, nargs="?", const=20, metavar="N",
                    help="show last N change-log entries and exit")
    ap.add_argument("--max-new", type=int, default=MAX_NEW_PER_PASS,
                    help="new files fetched per source per pass (default 500)")
    ap.add_argument("--ledger", type=int, nargs="?", const=20,
                    metavar="N",
                    help="show last N file-ledger entries and per-status counts")
    ap.add_argument("--cookies", default=None,
                    help="Netscape cookies.txt for restricted/throttled "
                         "folders (default: cookies.txt in repo root, if present)")
    args = ap.parse_args()

    if args.log is not None:
        return show_log(args.log)
    if args.ledger is not None:
        return show_ledger(args.ledger)

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
    _lock = acquire_lock()
    if _lock is None:
        print("ERROR: another sync_drive.py is already running "
              f"(see {INBOX / '.sync.lock'}); refusing to race with it.",
              file=sys.stderr)
        return 2
    cookies = None
    if args.cookies:
        cookies = Path(args.cookies)
    else:
        default_ck = REPO / "cookies.txt"
        if default_ck.is_file():
            cookies = default_ck
    if cookies:
        print(f"using cookies: {cookies}")
    else:
        print("anonymous access (no cookies.txt found)")
    ok_count = fail_count = incomplete = 0

    ledger = load_ledger()
    for src in sources:
        key = f"{src.get('category')}|{src.get('member')}"
        if args.only and args.only.upper() not in key.upper():
            continue
        link = (src.get("link") or "").strip()
        if not link or "PASTE" in link:
            print(f"skip  {key} (no link configured)")
            continue

        dest = INBOX / src["category"]
        before = snapshot(dest)
        print(f"sync  {key} -> inbox/{src['category']}/", flush=True)
        try:
            ok = sync_folder(gdown, link, dest, cookies=cookies,
                             ledger=ledger, source_key=key,
                             max_new=args.max_new)
        except Exception as e:  # noqa: BLE001 - one source must not stop the rest
            print(f"  ERROR: {type(e).__name__}: {str(e).splitlines()[0]}")
            ok = False
        after = snapshot(dest)
        new = sorted(set(after) - set(before))
        changed = sorted(k for k in set(before) & set(after)
                         if before[k] != after[k])
        removed = sorted(set(before) - set(after))
        if new or changed or removed:
            log_change(key, new, changed, removed)
        if new:
            for rel in new[:15]:
                print(f"  NEW  {rel}")
            if len(new) > 15:
                print(f"  ... +{len(new) - 15} more new files")
        if changed:
            for rel in changed[:15]:
                print(f"  CHANGED  {rel}  <- member replaced an existing"
                      " file; review + re-apply your local fix in"
                      " collected/ if needed")
        complete, why = structure_complete(dest)
        if ok:
            ok_count += 1
        else:
            fail_count += 1
        state[key] = {
            "files": len(after),
            "new_files": len(new),
            "changed_files": len(changed),
            "complete": complete,
            "note": why,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }
        print(f"  done: {len(new)} new, {len(changed)} changed"
              f", files on disk {len(after)}")
        if complete:
            print(f"  COMPLETE  files on disk: {len(after)}")
        else:
            incomplete += 1
            print(f"  INCOMPLETE ({why}) files: {len(after)}"
                  " — resume-safe, next pass continues")

    save_state(state)
    save_ledger(ledger)
    print(f"\nsync done: {ok_count} ok, {fail_count} download-failed, "
          f"{incomplete} incomplete (will resume next pass)")
    return 0 if not fail_count else 1


if __name__ == "__main__":
    sys.exit(main())
