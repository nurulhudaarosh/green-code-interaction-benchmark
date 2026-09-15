#!/usr/bin/env python3
"""Re-run every unit that is not `ok` in results/energy_runs.jsonl, capture
the real error with the adaptive invocation logic, classify it, and write
results/final/energy_failures.csv (plus a printed summary).

Usage: python3 scripts/energy_failures.py [--workers N]
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import measure_energy as me  # noqa: E402

LEDGER = REPO / "results" / "energy_runs.jsonl"
OUT_CSV = REPO / "results" / "final" / "energy_failures.csv"
TIMEOUT = 20


def latest_failing():
    last = {}
    for line in LEDGER.read_text().splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        last[(r["category"], r["task_id"], r["model"], r["condition"])] = r
    return {k: r for k, r in last.items() if r.get("status") != "ok"}


def classify(outcome, last_rc, err):
    if outcome == "timeout":
        return "TIMEOUT", "killed after %ds" % TIMEOUT
    if "SyntaxError" in err or "IndentationError" in err:
        return "NOT_PYTHON", "model prose / truncated file, not valid Python"
    if "AssertionError" in err or "FAILED (fail" in err:
        return "WRONG_OUTPUT", "embedded self-tests fail (logic bug)"
    if ("NameError" in err or "ValueError" in err or "KeyError" in err
            or "TypeError" in err or "EOFError" in err
            or "OperationalError" in err or "IndexError" in err):
        line = [l for l in err.strip().splitlines() if l.strip()]
        return "RUNTIME_BUG", (line[-1][:110] if line else "runtime error")
    if "ModuleNotFoundError" in err:
        m = re.search(r"No module named '([^']+)'", err)
        return "MISSING_DEP", f"needs module {m.group(1) if m else '?'}"
    if "arguments are required" in err or "unrecognized arguments" in err:
        line = [l for l in err.strip().splitlines() if l.strip()]
        return "CLI_ARGS", (line[-1][:110] if line else "argument error")
    if ("FileNotFoundError" in err or "NotADirectoryError" in err
            or "No such file" in err):
        line = [l for l in err.strip().splitlines() if l.strip()]
        return "MISSING_FILE", (line[-1][:110] if line else "missing file")
    if not err.strip():
        return f"SILENT_RC{last_rc}", "no message (schema mismatch / no-op)"
    line = [l for l in err.strip().splitlines() if l.strip()]
    return "OTHER", (line[-1][:110] if line else "")


def run_one(key):
    cat, task_id, model, cond = key
    rel = f"{cat}/code/{model}/{task_id}/{cond}/" \
          f"{'code.py' if cond == 'ONE_SHOT' else 'final.py'}"
    prog = REPO / "collected" / rel
    if not prog.is_file():
        return key, {"outcome": "no_program", "rel": rel}
    prog_text = prog.read_text(encoding="utf-8", errors="replace")
    tid_dir = me.INPUTS / cat / task_id
    with tempfile.TemporaryDirectory(prefix="gcb-fail-") as td:
        work = Path(td)
        if tid_dir.is_dir():
            for f in tid_dir.iterdir():
                if f.is_file():
                    shutil.copy2(f, work / f.name)
                elif f.is_dir():
                    shutil.copytree(f, work / f.name)
        shutil.copy2(prog, work / "prog.py")
        me.ensure_input_dirs(work, cat, prog_text)
        me.serve_aliases(work, prog_text)

        last = None
        for stdin_name, args in me.invocations(task_id, cat, model, work, prog_text):
            rc, _, _ = me.run_once(work, stdin_name, args, timeout=TIMEOUT)
            last = (stdin_name, args, rc)
            if rc == 0:
                return key, {"outcome": "runs_ok", "rel": rel,
                             "invocation": {"stdin": stdin_name, "args": args}}
            if rc == 124:
                return key, {"outcome": "timeout", "rel": rel}
        stdin_name, args, rc = last or (None, [], None)
        sf = work / stdin_name if stdin_name else None
        stdin = open(sf, "rb") if (sf and sf.is_file()) else subprocess.DEVNULL
        try:
            p = subprocess.run([sys.executable, "prog.py", *args], cwd=work,
                               stdin=stdin, stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE, timeout=TIMEOUT)
            err = p.stderr.decode("utf-8", "replace")
            rc = p.returncode
        except subprocess.TimeoutExpired:
            err, rc = "", 124
        finally:
            if sf and sf.is_file():
                stdin.close()
        return key, {"outcome": "timeout" if rc == 124 else "failed",
                     "rel": rel, "last_rc": rc, "err": err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    fails = latest_failing()
    print(f"re-running {len(fails)} non-ok units with {a.workers} workers...",
          flush=True)
    results = {}
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(run_one, k): k for k in fails}
        for fut in as_completed(futs):
            key, res = fut.result()
            results[key] = res
    rows, transient = [], 0
    for key, res in sorted(results.items()):
        cat, task_id, model, cond = key
        if res["outcome"] == "runs_ok":
            transient += 1
            continue
        reason, detail = classify(res["outcome"], res.get("last_rc"),
                                  res.get("err", ""))
        rows.append({"category": cat, "task_id": task_id, "model": model,
                     "condition": cond, "file": res.get("rel", ""),
                     "reason": reason, "detail": detail})
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["category", "task_id", "model",
                                          "condition", "file", "reason", "detail"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nstill failing: {len(rows)}  (transient now-runnable: {transient})")
    for k, n in Counter(r["reason"] for r in rows).most_common():
        print(f"  {n:4d}  {k}")
    print("\nby category x reason:")
    grid = defaultdict(Counter)
    for r in rows:
        grid[r["category"]][r["reason"]] += 1
    for c in sorted(grid):
        print("  ", c, dict(grid[c]))
    print(f"\nwrote {OUT_CSV}")


if __name__ == "__main__":
    main()
