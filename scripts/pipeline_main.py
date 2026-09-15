#!/usr/bin/env python3
"""Green Code benchmark pipeline v2 — split into small, never-repeating
steps, driven by two concurrent worker threads.

  STEP 0 (fast, once per category)  DATASETS
      Every category's task definitions are fetched from Drive into
      dataset/<category>/dataset.json exactly once and then FROZEN —
      never fetched or changed again. A corrupt-at-source dataset is
      repaired with scripts/repair_dataset.py.

  THREAD 1  DOWNLOADER (producer)
      LIST      cached Drive folder listing; refreshed at most every
                --list-ttl seconds, only while something is still missing
      PATTERN   expected code files derived from the FROZEN local dataset
                (max 25 tasks per category); for categories whose dataset
                has not arrived yet, a generic code-layout pattern is used
      DOWNLOAD  only files that are expected AND missing from the file
                ledger. A downloaded file is NEVER requested from Drive
                again (ledger marks it downloaded/measured; failed
                downloads back off 15m -> 30m -> ... -> 24h). Expected
                files that are not in Drive yet are simply skipped.
      INGEST    inbox -> collected/ for that category (partial member
                submissions are fine; local manual fixes are preserved)
      HARNESSES auto-generate missing harnesses
      -> signals the runner thread

  THREAD 2  RUNNER (consumer)
      QUEUE     units in collected/ whose final program has no
                measurement-ledger entry (or whose sha256 changed = manual
                fix, or whose error backoff expired). A measured unit is
      MEASURE   run once per unit: warmup + N measured runs with RAPL,
                recorded in the append-only measurement ledger. Measured
                code never touches any Drive step again.
      PROBLEMS  results/pipeline_state.json + problems.{csv,md} are
                rebuilt from the LATEST state — a problem that got fixed
                disappears from the report.

Everything is crash-safe: all progress lives in append-only ledgers or
atomic JSON files, so killing and restarting the pipeline never repeats a
step. Use scripts/run_pipeline.sh to keep it alive across hangs.

Usage:
    python3 scripts/pipeline_main.py                 # run forever
    python3 scripts/pipeline_main.py --one-cycle     # one downloader cycle, no runner
    python3 scripts/pipeline_main.py --limit 5       # stop after N measured units
    python3 scripts/pipeline_main.py --no-downloader # measure what is already local
"""

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import threading
import time
import traceback
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# gdown requests without a timeout can hang the pipeline forever
socket.setdefaulttimeout(30)

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from sync_drive import (  # noqa: E402
    LEDGER as FILE_LEDGER,
    collected_rel,
    load_ledger as load_file_ledger,
    save_ledger,
)
from measure_progress import scan_units  # noqa: E402
import ingest_zips  # noqa: E402

INBOX = REPO / "inbox"
RESULTS = REPO / "results"
LISTINGS = RESULTS / "drive_listings.json"
STATE = RESULTS / "pipeline_state.json"
MEAS_LEDGER = RESULTS / "measurement_ledger.jsonl"
PROBLEMS_MD = RESULTS / "final" / "problems.md"

CFG = json.loads((REPO / "config" / "experiment.json").read_text(encoding="utf-8"))
MAX_TASKS = int(CFG.get("max_tasks_per_category", 25))
EXEC = CFG.get("execution", {})
WARMUP = int(EXEC.get("warmup_runs", 1))
RUNS = int(EXEC.get("measured_runs", 5))
TIMEOUT_S = int(EXEC.get("timeout_seconds", 300))
UNIT_TIMEOUT = (WARMUP + RUNS) * (TIMEOUT_S + 90) + 600
ERROR_BACKOFF = [900, 3600, 14400]     # 15m, 1h, 4h between error retries
MAX_CONSEC_ERRORS = 3                  # after this: manual fix required
GAP_BETWEEN_DOWNLOADS = 1.0
MODELS = CFG.get("models", ["gpt", "claude", "gemini", "deepseek"])

HEARTBEATS = {"downloader": 0.0, "runner": 0.0}
STOP = threading.Event()
NEW_WORK = threading.Event()
PRINT_LOCK = threading.Lock()
MEASURED_COUNT = [0]


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    with PRINT_LOCK:
        print(f"[{ts}] {msg}", flush=True)


def hb(name):
    HEARTBEATS[name] = time.time()


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# frozen datasets
# --------------------------------------------------------------------------

def load_dataset_tasks(category):
    p = REPO / "dataset" / category / "dataset.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        tasks = data.get("tasks") if isinstance(data, dict) else data
        return tasks if tasks else None
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def dataset_valid(category):
    return bool(load_dataset_tasks(category))


# --------------------------------------------------------------------------
# expected-file pattern (derived from the frozen local dataset)
# --------------------------------------------------------------------------

def expected_code_rels(category, listing=None):
    """Relative paths (collected-style: <cat>/code/...) that should exist.

    Strict pattern from the frozen dataset when available; otherwise a
    generic code-layout pattern taken from the Drive listing so files can
    be pre-fetched while the member's dataset has not arrived yet.
    """
    tasks = load_dataset_tasks(category)
    out = set()
    if tasks:
        for task in tasks[:MAX_TASKS]:
            for model in MODELS:
                for rel in ingest_zips.expected_code_files(task, model):
                    out.add(f"{category}/{rel}")
        return out
    if listing:
        for f in listing:
            rel = f["rel"]
            parts = rel.split("/")
            # <cat>/code/<model>/<TASK>/<INT>/<file>.py
            if (len(parts) == 6 and parts[1] == "code" and parts[2] in MODELS
                    and parts[5].endswith(".py")):
                out.add(rel)
    return out


# --------------------------------------------------------------------------
# Drive access (isolated in scripts/drive_helper.py with hard timeouts)
# --------------------------------------------------------------------------

HELPER = REPO / "scripts" / "drive_helper.py"
LIST_TIMEOUT = 280     # hard cap for one folder listing
GET_TIMEOUT = 180      # hard cap for one file download


def _helper(args, timeout):
    try:
        r = subprocess.run([sys.executable, str(HELPER)] + args,
                           capture_output=True, text=True, timeout=timeout,
                           cwd=REPO)
    except subprocess.TimeoutExpired:
        return None, f"helper timeout after {timeout}s"
    for line in reversed((r.stdout or "").strip().splitlines()):
        if line.startswith("{"):
            try:
                return json.loads(line), None
            except json.JSONDecodeError:
                continue
    return None, f"helper rc={r.returncode}: {(r.stderr or '')[:150]}"


def list_source(url, dest):
    """One listing request via the helper. Returns (files, error);
    files: [{id, rel, path, name}] (rel = collected-style, path = true)."""
    data, err = _helper(["list", url, str(dest)], LIST_TIMEOUT)
    if err:
        return None, err
    if not data.get("ok"):
        return None, (data.get("error") or "listing failed")[:200]
    out = []
    for f in data.get("files", []):
        p = Path(f["path"])
        try:
            path = str(p.relative_to(INBOX))
        except ValueError:
            continue
        out.append({"id": f["id"], "rel": collected_rel(path),
                    "path": path, "name": p.name})
    return out, None


def fetch_file(file_id, parent_dir):
    """Download one file by id via the helper. Returns (ok, error)."""
    data, err = _helper(["get", file_id, str(parent_dir)], GET_TIMEOUT)
    if err:
        return False, err
    if not data.get("ok"):
        return False, (data.get("error") or "download failed")[:200]
    return True, None


def load_listings():
    try:
        return json.loads(LISTINGS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_listings(data):
    RESULTS.mkdir(parents=True, exist_ok=True)
    tmp = LISTINGS.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    tmp.replace(LISTINGS)


def refresh_listing(sources, category, force=False, ttl=300):
    """Return (files, error) using the cache; refresh when stale."""
    cache = load_listings()
    ent = cache.get(category)
    if not force and ent and not ent.get("error"):
        age = time.time() - datetime.fromisoformat(ent["listed_at"]).timestamp()
        if age < ttl:
            return ent["files"], None
    src = sources.get(category)
    if src is None:
        return None, "no source configured"
    files, err = list_source(src["link"], INBOX / category)
    cache[category] = {"listed_at": now_iso(), "files": files or [],
                       "error": err}
    save_listings(cache)
    return cache[category]["files"], err


# --------------------------------------------------------------------------
# file ledger helpers (the "never request again" record)
# --------------------------------------------------------------------------

def seed_disk_files(ledger, category, expected):
    """Files already on disk but absent from the ledger get seeded as
    downloaded (file_id unknown) so they are never fetched from Drive."""
    seeded = 0
    for rel in expected:
        entry = next((e for e in ledger.values() if e.get("rel") == rel), None)
        if entry:
            continue
        local = local_path_of(rel)
        if not local.is_file() or local.stat().st_size == 0:
            continue
        sha = hashlib.sha256(local.read_bytes()).hexdigest()[:16]
        ledger[f"rel:{rel}"] = {
            "file_id": None, "rel": rel, "name": local.name,
            "status": "downloaded", "sha256": sha,
            "downloaded_at": now_iso(), "measured_at": None,
            "fails": 0, "backoff_until": None, "error": None,
            "task_key": None, "source": "disk-seed",
        }
        seeded += 1
    return seeded


def local_path_of(rel):
    """collected-style rel -> actual path under inbox/."""
    return INBOX / rel.replace("/code/", "/.collection/code/", 1) \
        if "/code/" in rel else INBOX / rel


def download_pass(category, sources, max_new, list_ttl):
    """Download expected-but-unrecorded files that exist in Drive.

    Returns number of new files downloaded. Never re-requests a file the
    ledger already knows (downloaded/measured/local/skipped), honors the
    failed-backoff, and skips expected files that are not in the listing.
    A category whose expected set is fully recorded never lists Drive
    again.
    """
    # seed + pre-check WITHOUT any listing: files already on disk (e.g.
    # from a zip_src ZIP) are recorded first so Drive is never asked
    # about them at all
    ledger = load_file_ledger()
    expected = expected_code_rels(category)
    if not expected:
        return 0
    seeded = seed_disk_files(ledger, category, expected)
    if seeded:
        save_ledger(ledger)
        log(f"DOWN {category}: seeded {seeded} on-disk file(s) into the ledger")
    if dataset_valid(category):
        done = {e.get("rel") for e in ledger.values()
                if e.get("status") in ("downloaded", "measured", "local", "skipped")}
        if expected <= done:
            return 0  # category complete — no Drive request at all

    listing, err = refresh_listing(sources, category, ttl=list_ttl)
    if err:
        log(f"DOWN {category}: listing failed: {err}")
        return 0
    by_rel_listing = {f["rel"]: f for f in listing}
    if not dataset_valid(category):
        # no frozen dataset yet: use the generic code-layout pattern from
        # the listing so member files can still be pre-fetched
        for rel in expected_code_rels(category, listing):
            expected.add(rel)

    # small extras that are always wanted: member progress state + the
    # dataset itself while the local one is still missing
    extras = set()
    st = f"{category}/state.json"
    if st in by_rel_listing and not any(e.get("rel") == st for e in ledger.values()):
        extras.add(st)
    if not dataset_valid(category):
        ds = f"{category}/dataset/dataset.json"
        if ds in by_rel_listing and not any(
                e.get("rel") == ds for e in ledger.values()):
            extras.add(ds)

    want = sorted((expected | extras) & set(by_rel_listing))
    downloaded = skipped_known = waiting = 0
    for rel in want:
        if STOP.is_set():
            break
        f = by_rel_listing[rel]
        fid = f["id"]
        entry = ledger.get(fid) or next(
            (e for e in ledger.values() if e.get("rel") == rel), None)
        if entry:
            stt = entry.get("status")
            if stt in ("downloaded", "measured", "local", "skipped"):
                skipped_known += 1
                continue
            if stt == "failed":
                bu = entry.get("backoff_until")
                if bu and time.time() < float(bu):
                    waiting += 1
                    continue
        local = INBOX / f["path"]
        if local.is_file() and local.stat().st_size > 0:
            sha = hashlib.sha256(local.read_bytes()).hexdigest()[:16]
            ledger[fid] = {"file_id": fid, "rel": rel, "name": local.name,
                           "status": "downloaded", "sha256": sha,
                           "downloaded_at": now_iso(), "measured_at": None,
                           "fails": 0, "backoff_until": None, "error": None,
                           "task_key": None, "source": category}
            downloaded += 1
            continue
        local.parent.mkdir(parents=True, exist_ok=True)
        ok, derr = fetch_file(fid, local.parent)
        try:
            if not ok:
                raise RuntimeError(derr or "download failed")
            if not local.is_file() or local.stat().st_size == 0:
                raise RuntimeError("download produced no file")
            sha = hashlib.sha256(local.read_bytes()).hexdigest()[:16]
            ledger[fid] = {"file_id": fid, "rel": rel, "name": local.name,
                           "status": "downloaded", "sha256": sha,
                           "downloaded_at": now_iso(), "measured_at": None,
                           "fails": 0, "backoff_until": None, "error": None,
                           "task_key": None, "source": category}
            downloaded += 1
            log(f"DOWN {category}: {rel}")
        except Exception as e:  # noqa: BLE001
            msg = (str(e).strip().splitlines() or [type(e).__name__])[0][:200]
            fails = int((entry or {}).get("fails", 0)) + 1
            backoff = min(24 * 3600, 900 * (2 ** (fails - 1)))
            ledger[fid] = {"file_id": fid, "rel": rel, "name": f["name"],
                           "status": "failed", "sha256": None,
                           "downloaded_at": None, "measured_at": None,
                           "fails": fails,
                           "backoff_until": str(time.time() + backoff),
                           "error": msg, "task_key": None, "source": category}
            log(f"DOWN {category}: FAIL {rel} ({msg[:80]}) backoff {backoff}s")
            time.sleep(3)
        save_ledger(ledger)
        if downloaded >= max_new:
            break
        time.sleep(GAP_BETWEEN_DOWNLOADS)
    if downloaded or waiting:
        log(f"DOWN {category}: +{downloaded} new, {skipped_known} already had,"
            f" {waiting} backoff")
    return downloaded


# --------------------------------------------------------------------------
# step 0: frozen datasets
# --------------------------------------------------------------------------

def bootstrap_datasets(sources):
    """Fast step: make sure every category has a valid frozen local dataset.

    A category whose Drive folder has no dataset yet (or a corrupt one)
    keeps waiting; the downloader retries it every cycle.
    """
    log("STEP 0: checking frozen datasets ...")
    for category, src in sorted(sources.items()):
        if dataset_valid(category):
            continue
        files, err = refresh_listing(sources, category, force=True)
        if err:
            log(f"  {category}: listing failed ({err}) — will retry")
            continue
        cand = [f for f in files if f["rel"] == f"{category}/dataset/dataset.json"]
        if not cand:
            log(f"  {category}: no dataset/dataset.json in Drive folder yet — waiting")
            continue
        f = cand[0]
        dest = INBOX / category / "dataset" / "dataset.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        ok, derr = fetch_file(f["id"], dest.parent)
        try:
            if not ok:
                raise RuntimeError(derr or "download failed")
            data = json.loads(dest.read_text(encoding="utf-8"))
            tasks = data.get("tasks") if isinstance(data, dict) else data
            if not tasks:
                raise ValueError("dataset has no tasks")
        except Exception as e:  # noqa: BLE001
            log(f"  {category}: dataset download/parse failed ({e}) — "
                "trying repair")
            if not repair_and_freeze(category, dest):
                log(f"  {category}: dataset still unusable — waiting")
            continue
        freeze_dataset(category, dest)
        log(f"  {category}: dataset frozen ({len(tasks)} tasks)")
    for category in sources:
        if dataset_valid(category):
            n = len(load_dataset_tasks(category))
            log(f"  {category}: OK ({n} tasks)")


def repair_and_freeze(category, src_path):
    try:
        r = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "repair_dataset.py"),
             str(src_path), "-o", str(src_path)],
            capture_output=True, text=True, timeout=300, cwd=REPO)
        ok = r.returncode == 0 and dataset_valid_from(src_path)
        if ok:
            freeze_dataset(category, src_path)
            log(f"  {category}: repaired dataset frozen")
        return ok
    except Exception as e:  # noqa: BLE001
        log(f"  {category}: repair crashed: {e}")
        return False


def dataset_valid_from(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        tasks = data.get("tasks") if isinstance(data, dict) else data
        return bool(tasks)
    except Exception:  # noqa: BLE001
        return False


def freeze_dataset(category, src_path):
    from sync_zips import normalize_dataset_inplace
    normalize_dataset_inplace(Path(src_path))
    dest_dir = REPO / "dataset" / category
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / "dataset.json").write_bytes(Path(src_path).read_bytes())


# --------------------------------------------------------------------------
# ingest + harnesses (subprocess steps)
# --------------------------------------------------------------------------

def run_step(argv, timeout=1800):
    try:
        r = subprocess.run([str(a) for a in argv], cwd=REPO,
                           capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {timeout}s"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def ingest_and_harness(category):
    ok, out = run_step([sys.executable, "scripts/ingest_zips.py",
                        str(INBOX / category)], timeout=1800)
    if not ok:
        log(f"INGEST {category}: FAILED\n{out.strip()[-800:]}")
        return False
    new = [l for l in out.splitlines() if "KEPT" in l or "local modification" in l]
    if new:
        log(f"INGEST {category}: kept local fixes: {len(new)} note(s)")
    # harnesses for any task that still lacks one
    ok2, out2 = run_step([sys.executable, "scripts/gen_harnesses.py", category],
                         timeout=3600)
    if not ok2:
        log(f"HARNESS {category}: FAILED\n{out2.strip()[-500:]}")
    wrote = [l for l in out2.splitlines() if "written=" in l]
    if wrote:
        log(f"HARNESS {category}: {wrote[0].strip()}")
    return True


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------

def load_meas_ledger_latest():
    latest, fails = {}, defaultdict(int)
    if MEAS_LEDGER.is_file():
        for line in MEAS_LEDGER.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = (e.get("category"), e.get("task_id"), e.get("model"),
                   e.get("interaction"), e.get("file"))
            if e.get("status") in ("error", "skipped"):
                fails[key] = fails[key] + 1 if key in latest else 1
            else:
                fails[key] = 0
            latest[key] = e
    return latest, fails


def pending_units():
    units = scan_units()
    latest, fails = load_meas_ledger_latest()
    out = []
    for u in units:
        key = (u["category"], u["task_id"], u["model"],
               u["interaction"], u["file"])
        if key not in latest:
            out.append(u)
            continue
        e = latest[key]
        if e.get("sha256") != u["sha256"]:
            out.append(u)      # code changed (manual fix) -> measure now
            continue
        if e.get("status") in ("error", "skipped"):
            n = fails.get(key, 0)
            if n >= MAX_CONSEC_ERRORS:
                continue       # needs a manual fix; problem report tells which
            backoff = ERROR_BACKOFF[min(n - 1, len(ERROR_BACKOFF) - 1)]
            try:
                last_ts = datetime.fromisoformat(e["ts"]).timestamp()
            except (KeyError, ValueError):
                last_ts = 0
            if time.time() - last_ts >= backoff:
                out.append(u)
    out.sort(key=lambda x: (x["category"], x["model"], x["task_id"],
                            x["interaction"]))
    return out


def record_unit_error(unit, note):
    subprocess.run([sys.executable, "scripts/measure_progress.py", "record",
                    unit["rel"], "--status", "error", "--note", note],
                   cwd=REPO, capture_output=True, text=True)


def measure_one(unit):
    label = (f"{unit['category']}/{unit['task_id']}/{unit['model']}"
             f"/{unit['interaction']}")
    log(f"MEASURE {label} starting")
    t0 = time.time()
    proc = None
    try:
        proc = subprocess.Popen(
            [sys.executable, "runner/measure_unit.py", "--unit",
             json.dumps(unit)], cwd=REPO, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True)
        last = {"line": ""}

        def pump():
            for line in proc.stdout:
                hb("runner")
                with PRINT_LOCK:
                    sys.stdout.write(f"    {line}")
                    sys.stdout.flush()
                if line.strip().startswith("{"):
                    last["line"] = line

        th = threading.Thread(target=pump, daemon=True)
        th.start()
        rc = proc.wait(timeout=UNIT_TIMEOUT)
        th.join(timeout=10)
        status = "error"
        try:
            status = json.loads(last["line"]).get("status", "error")
        except (json.JSONDecodeError, TypeError):
            record_unit_error(unit, f"no_verdict (measure_unit rc={rc})")
        log(f"MEASURE {label} -> {status} in {time.time() - t0:.0f}s")
        return status
    except subprocess.TimeoutExpired:
        if proc:
            proc.kill()
        record_unit_error(unit, "measure_unit_timeout (hard kill)")
        log(f"MEASURE {label} -> TIMEOUT (killed after {UNIT_TIMEOUT}s)")
        return "error"


def rebuild_problem_state():
    """Single source of truth for CURRENT problems. Anything that got fixed
    disappears from here automatically (latest ledger state wins)."""
    state = {"updated_at": now_iso(), "unit_errors": {}, "download_errors": {},
             "dataset_problems": {}, "stats": {}}
    latest, fails = load_meas_ledger_latest()
    for key, e in latest.items():
        if e.get("status") not in ("error", "skipped"):
            continue
        k = "|".join(str(x) for x in key)
        state["unit_errors"][k] = {
            "reason": (e.get("note") or "")[:300],
            "attempts": fails.get(key, 0),
            "needs_manual_fix": fails.get(key, 0) >= MAX_CONSEC_ERRORS,
            "last_ts": e.get("ts"),
        }
    for entry in load_file_ledger().values():
        if entry.get("status") == "failed":
            state["download_errors"][entry.get("rel") or "?"] = {
                "error": (entry.get("error") or "")[:200],
                "fails": entry.get("fails", 0),
                "backoff_until": entry.get("backoff_until"),
            }
    try:
        sources = load_sources()
        for cat in sources:
            if not dataset_valid(cat):
                state["dataset_problems"][cat] = (
                    "no valid local dataset yet (Drive folder has none / "
                    "corrupt; will keep checking)")
    except Exception:  # noqa: BLE001
        pass
    units = scan_units()
    latest_all, _ = load_meas_ledger_latest()
    done = sum(1 for u in units
               if latest_all.get((u["category"], u["task_id"], u["model"],
                                  u["interaction"], u["file"]), {})
               .get("status") == "measured")
    state["stats"] = {"units_local": len(units), "units_measured": done,
                      "units_pending": len(pending_units()),
                      "measured_this_run": MEASURED_COUNT[0],
                      "parked_needs_manual_fix": len(RUNNER_PARKED)}
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE)


def regen_problems_report():
    run_step([sys.executable, "scripts/code_problems.py"], timeout=300)


def u_key(u):
    return (u["category"], u["task_id"], u["model"], u["interaction"], u["file"])


RUNNER_PARKED = {}   # unit_key -> first_error_ts (needs manual fix)
RUNNER_COOLDOWN = {}  # unit_key -> (retry_not_before_ts, attempts)


def runner_loop(limit=None):
    log("RUNNER thread started")
    since_report = 0
    while not STOP.is_set():
        try:
            hb("runner")
            now = time.time()
            units = [u for u in pending_units()
                     if u_key(u) not in RUNNER_PARKED
                     and RUNNER_COOLDOWN.get(u_key(u), (0,))[0] <= now]
            if not units:
                NEW_WORK.wait(timeout=60)
                NEW_WORK.clear()
                continue
            if limit is not None and MEASURED_COUNT[0] >= limit:
                log(f"RUNNER: --limit {limit} reached; stopping")
                return
            u = units[0]
            status = measure_one(u)
            MEASURED_COUNT[0] += 1
            since_report += 1
            k = u_key(u)
            if status == "error":
                _, att = RUNNER_COOLDOWN.get(k, (0, 0))
                att += 1
                if att >= MAX_CONSEC_ERRORS:
                    RUNNER_PARKED[k] = now_iso()
                    RUNNER_COOLDOWN.pop(k, None)
                    log(f"RUNNER: {k} failed {att}x — parked until manual "
                        f"fix (see results/final/problems.md)")
                else:
                    backoff = ERROR_BACKOFF[min(att - 1,
                                               len(ERROR_BACKOFF) - 1)]
                    RUNNER_COOLDOWN[k] = (now + backoff, att)
            else:
                RUNNER_COOLDOWN.pop(k, None)
            rebuild_problem_state()
            if since_report >= 5 or status == "error":
                regen_problems_report()
                since_report = 0
        except Exception:  # noqa: BLE001
            log(f"RUNNER: cycle crashed\n{traceback.format_exc()[-600:]}")
            STOP.wait(30)
    log("RUNNER thread stopped")


# --------------------------------------------------------------------------
# downloader
# --------------------------------------------------------------------------

def load_sources():
    cfg = json.loads((REPO / "config" / "drive_sources.json")
                     .read_text(encoding="utf-8"))
    return {s["category"]: s for s in cfg.get("sources", []) if s.get("link")}


def downloader_cycle(sources, max_new, list_ttl):
    did_work = False
    # 1) local ZIPs first (fast, no network) ----------------------------
    try:
        from sync_zips import process_new_zips
        hb("downloader")
        touched = process_new_zips()
        for category, n in sorted(touched.items()):
            log(f"ZIP {category}: {n} new file(s) extracted from zip_src/")
            if dataset_valid(category):
                if ingest_and_harness(category):
                    did_work = True
                    NEW_WORK.set()
    except Exception:  # noqa: BLE001
        log(f"ZIP step crashed\n{traceback.format_exc()[-600:]}")
    # 2) Drive fallback for anything the ZIPs do not cover ---------------
    for category, src in sorted(sources.items()):
        if STOP.is_set():
            break
        hb("downloader")
        try:
            n_new = download_pass(category, sources, max_new, list_ttl)
        except Exception:  # noqa: BLE001
            log(f"DOWN {category}: cycle crashed\n{traceback.format_exc()[-600:]}")
            continue
        if n_new > 0 and dataset_valid(category):
            if ingest_and_harness(category):
                did_work = True
                NEW_WORK.set()
        elif n_new == 0 and dataset_valid(category):
            # nothing new from Drive, but first-run ingest may still be pending
            coll = REPO / "collected" / category
            if not (coll / "ingest_report.json").is_file():
                if ingest_and_harness(category):
                    did_work = True
                    NEW_WORK.set()
    return did_work


def downloader_loop(max_new, list_ttl, idle=60, one_cycle=False):
    log("DOWNLOADER thread started")
    sources = load_sources()
    try:
        bootstrap_datasets(sources)
    except Exception:  # noqa: BLE001
        log(f"DOWNLOADER: bootstrap crashed\n{traceback.format_exc()[-600:]}")
    while not STOP.is_set():
        hb("downloader")
        try:
            did = downloader_cycle(sources, max_new, list_ttl)
        except Exception:  # noqa: BLE001
            log(f"DOWNLOADER: cycle crashed\n{traceback.format_exc()[-600:]}")
            did = False
        if one_cycle:
            return
        STOP.wait(10 if did else idle)
    log("DOWNLOADER thread stopped")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def status_line():
    sources = load_sources()
    ds = {c: ("ok" if dataset_valid(c) else "WAITING")
          for c in sorted(sources)}
    latest, _ = load_meas_ledger_latest()
    units = scan_units()
    measured = sum(1 for u in units
                   if latest.get((u["category"], u["task_id"], u["model"],
                                  u["interaction"], u["file"]), {})
                   .get("status") == "measured")
    pend = len(pending_units())
    log(f"STATE datasets={ds} | local units={len(units)} measured={measured} "
        f"| pending={pend} | measured_this_run={MEASURED_COUNT[0]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list-ttl", type=int, default=300,
                    help="seconds between Drive listings per source (default 300)")
    ap.add_argument("--max-new", type=int, default=200,
                    help="max new file downloads per source per cycle")
    ap.add_argument("--idle", type=int, default=60,
                    help="downloader sleep when idle")
    ap.add_argument("--limit", type=int,
                    help="stop after N measured units this run")
    ap.add_argument("--one-cycle", action="store_true",
                    help="one downloader cycle + dataset bootstrap, no runner")
    ap.add_argument("--no-downloader", action="store_true")
    ap.add_argument("--no-runner", action="store_true")
    args = ap.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    log("=" * 62)
    log("pipeline v2 starting "
        f"(pid={os.getpid()} list_ttl={args.list_ttl}s "
        f"unit_timeout={UNIT_TIMEOUT}s)")
    log("=" * 62)

    threads = []
    if not args.no_downloader:
        threads.append(threading.Thread(
            target=downloader_loop, daemon=True,
            args=(args.max_new, args.list_ttl, args.idle, args.one_cycle),
            name="downloader"))
    if not (args.no_runner or args.one_cycle):
        threads.append(threading.Thread(
            target=runner_loop, daemon=True, args=(args.limit,),
            name="runner"))
    for t in threads:
        t.start()

    if args.one_cycle:
        for t in threads:
            t.join()
        rebuild_problem_state()
        status_line()
        return 0

    stall_logged = 0
    try:
        while any(t.is_alive() for t in threads):
            time.sleep(60)
            now = time.time()
            for name, ts in HEARTBEATS.items():
                if ts and now - ts > 1800:
                    if stall_logged < 5:
                        log(f"WARNING: {name} thread stale for "
                            f"{(now - ts) / 60:.0f} min (may be stuck — "
                            "restart the pipeline if this persists)")
                        stall_logged += 1
            status_line()
            if args.limit is not None and MEASURED_COUNT[0] >= args.limit:
                log(f"--limit {args.limit} reached; shutting down")
                break
    except KeyboardInterrupt:
        log("interrupted — shutting down (safe: all progress is in ledgers)")
    STOP.set()
    NEW_WORK.set()
    time.sleep(2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
