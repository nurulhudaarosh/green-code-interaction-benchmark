#!/usr/bin/env python3
"""Green Code benchmark CI/CD pipeline.

One command keeps everything fresh:

    1. SYNC     download/refresh member ZIPs from shared Drive links
                (config/drive_sources.json; unchanged ZIPs skipped)
    2. INGEST   validate + merge ZIPs -> collected/, update dataset/,
                write collected/STATUS.md
    3. HARNESSES auto-generate missing tests/harness/<cat>/<TASK>.py files
                from the dataset reference signatures (self-tested)
    4. MEASURE  take pending units from the ledger (already-measured code
                with the same sha256 is NEVER re-run; error/skipped units
                are retried so new harnesses take effect automatically).
                Writes results/final/problems.{md,csv} for manual fixing.
    5. ANALYZE  rebuild results/processed CSVs, delta-energy tables and
                plots for the paper

So when one member completes one new task, this run measures exactly that
one task and nothing else.

Usage:
    python3 scripts/run_pipeline.py                # one full pass
    python3 scripts/run_pipeline.py --no-sync      # skip Drive download
    python3 scripts/run_pipeline.py --watch 900    # loop every 15 min
    python3 scripts/run_pipeline.py --limit 10     # measure at most N units
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PY = sys.executable
FAIL_LOG = REPO / "results" / "failed.log"
RESILIENT = False


def log_failure(stage, detail):
    """Append a failure record to results/failed.log for later manual fixing.
    Never raises: logging must not stop the pipeline."""
    try:
        FAIL_LOG.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        with FAIL_LOG.open("a", encoding="utf-8") as f:
            f.write(f"[{ts}] STAGE={stage} {detail}\n")
    except OSError as e:
        print(f"WARNING: could not write {FAIL_LOG}: {e}", file=sys.stderr)


def step(name, argv, allow_fail=False, resilient=None, timeout=None):
    print(f"\n{'=' * 60}\n[{name}] {' '.join(str(a) for a in argv)}\n{'=' * 60}",
          flush=True)
    t0 = time.time()
    try:
        # No output capture: the child writes straight to the terminal so
        # you see every download/file/progress line live.
        r = subprocess.run([str(a) for a in argv], cwd=REPO, timeout=timeout)
    except subprocess.TimeoutExpired:
        log_failure(name, f"TIMEOUT after {timeout}s cmd={' '.join(str(a) for a in argv)}")
        print(f"[{name}] TIMEOUT after {timeout}s", file=sys.stderr, flush=True)
        return -1
    dur = time.time() - t0
    if r.returncode != 0:
        log_failure(name, f"rc={r.returncode} cmd={' '.join(str(a) for a in argv)}")
        print(f"[{name}] failed (rc={r.returncode}) in {dur:.1f}s", file=sys.stderr,
              flush=True)
        if not allow_fail and not (RESILIENT if resilient is None else resilient):
            raise SystemExit(r.returncode)
    else:
        print(f"[{name}] done in {dur:.1f}s", flush=True)
    return r.returncode


def pipeline(args):
    if not args.no_sync:
        step("1/5 SYNC", [PY, "scripts/sync_drive.py"], allow_fail=True,
             timeout=3600)
    else:
        print("[1/5 SYNC] skipped (--no-sync)")

    step("2/5 INGEST", [PY, "scripts/ingest_zips.py"], allow_fail=True)

    step("3/5 HARNESSES", [PY, "scripts/gen_harnesses.py"], allow_fail=True)

    queue_file = REPO / "results" / "measurement_queue.jsonl"
    q_argv = [PY, "scripts/measure_progress.py", "queue", "--redo-failed",
              "-o", queue_file]
    if args.limit:
        q_argv += ["--limit", str(args.limit)]
    step("4/5 MEASURE", q_argv)

    units = [json.loads(l) for l in
             queue_file.read_text(encoding="utf-8").splitlines() if l.strip()] \
        if queue_file.is_file() else []
    print(f"\n{len(units)} pending unit(s) to measure")
    done = {"measured": 0, "error": 0, "skipped": 0}
    for i, u in enumerate(units, 1):
        print(f"\n--- [{i}/{len(units)}] {u['category']} {u['task_id']} "
              f"{u['model']} {u['interaction']} ---", flush=True)
        # Stream the unit runner's stdout+stderr live; the final JSON line
        # (printed last by measure_unit.py) carries the result status.
        proc = subprocess.Popen(
            [PY, "runner/measure_unit.py", "--unit", json.dumps(u)],
            cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True)
        last_json = ""
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            if line.strip().startswith("{"):
                last_json = line
        proc.wait()
        parsed = None
        try:
            parsed = json.loads(last_json)
        except json.JSONDecodeError:
            pass
        status = (parsed or {}).get("status", "error")
        done[status if status in done else "error"] += 1
        if status == "error":
            reason = ""
            mpath = (parsed or {}).get("metrics")
            if mpath and (REPO / mpath).is_file():
                try:
                    mj = json.loads((REPO / mpath).read_text(encoding="utf-8"))
                    reason = (mj.get("reason")
                              or ",".join(str(e) for e in mj.get("driver_errors", [])))
                except (OSError, json.JSONDecodeError):
                    pass
            log_failure(
                f"MEASURE {u['category']}/{u['task_id']}/{u['model']}/{u['interaction']}",
                f"reason={reason[:300]}")

    step("5/5 ANALYZE", [PY, "analysis/aggregate.py"], allow_fail=True)
    step("5/5 ANALYZE", [PY, "analysis/energy_analysis.py"], allow_fail=True)
    step("5/5 ANALYZE", [PY, "analysis/interaction_analysis.py"], allow_fail=True)
    step("5/5 ANALYZE", [PY, "analysis/rq_statistics.py"], allow_fail=True)
    step("5/5 ANALYZE", [PY, "analysis/plots.py"], allow_fail=True)
    step("5/5 ANALYZE", [PY, "scripts/code_problems.py"], allow_fail=True)

    subprocess.run([PY, "scripts/measure_progress.py", "status", "--redo-failed"],
                   cwd=REPO)
    return done


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-sync", action="store_true")
    ap.add_argument("--limit", type=int, help="measure at most N pending units this pass")
    ap.add_argument("--watch", type=int, metavar="SECONDS",
                    help="repeat every N seconds (CI/CD mode)")
    ap.add_argument("--resilient", action="store_true",
                    help="log every stage failure to results/failed.log and keep going")
    args = ap.parse_args()
    global RESILIENT
    RESILIENT = args.resilient

    while True:
        done = pipeline(args)
        print(f"\npass done: {done}")
        if not args.watch:
            break
        print(f"sleeping {args.watch}s ...")
        time.sleep(args.watch)
    return 0


if __name__ == "__main__":
    sys.exit(main())
