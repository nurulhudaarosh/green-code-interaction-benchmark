#!/usr/bin/env python3
"""Worker: run a candidate program and its task reference through the per-task
harness at several input scales, timing each, and print ONE JSON line.

Mirrors runner/executor.py (in-process harness API) but records per-scale
runtime instead of correctness, so a log-log growth exponent can be fitted.

Usage:
    python3 analysis/scale_worker.py <category> <task_id> <prog.py> [scales...]
prints {"task":..., "scales":{"small":{"ms":..,"size":..}, ...}, "slope":..}
"""
import importlib.util
import io
import json
import os
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from runner import inputs as inputmod  # noqa: E402
from runner import tester  # noqa: E402

REPS = int(os.environ.get("GCB_SCALE_REPS", "3"))
BUDGET_MS = float(os.environ.get("GCB_SCALE_BUDGET_MS", "4000"))


def load_harness(category, tid):
    p = REPO / "tests" / "harness" / category / f"{tid}.py"
    spec = importlib.util.spec_from_file_location("harness", p)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    return h


def jsonable(o):
    try:
        json.dumps(o, default=str)
        return True
    except (TypeError, ValueError):
        return False


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def timed_reps(fn, reps=REPS):
    """Median wall time over up to `reps` calls, stopping early once the
    accumulated time exceeds BUDGET_MS (slow inputs need only one sample)."""
    times = []
    out = None
    err = None
    for _ in range(reps):
        t0 = time.perf_counter()
        try:
            out = fn()
            err = None
        except Exception as e:  # noqa: BLE001
            out, err = None, f"{type(e).__name__}: {e}"
        times.append((time.perf_counter() - t0) * 1000.0)
        if sum(times) > BUDGET_MS:
            break
    return median(times), out, err


def main():
    cat, tid, prog = sys.argv[1], sys.argv[2], sys.argv[3]
    scales = sys.argv[4:] or ["small", "medium", "large"]
    task = None
    ds = REPO / "dataset" / cat / "dataset.json"
    for t in json.loads(ds.read_text()).get("tasks", []):
        if str(t.get("task_id")) == str(tid):
            task = t
            break
    out = {"category": cat, "task_id": tid, "program": prog, "scales": {}}
    if task is None:
        out["error"] = "task_not_in_dataset"
        print(json.dumps(out))
        return
    try:
        harness = load_harness(cat, tid)
    except Exception as e:  # noqa: BLE001
        out["error"] = f"harness:{e}"
        print(json.dumps(out))
        return
    try:
        ref_ns = tester.load_reference(task)
    except Exception as e:  # noqa: BLE001
        out["error"] = f"reference_import:{e}"
        print(json.dumps(out))
        return

    cand = None
    ref_only = prog == "--reference"
    if not ref_only:
        try:
            cand = tester.load_module(prog)
        except Exception as e:  # noqa: BLE001
            out["error"] = f"candidate_import:{type(e).__name__}: {e}"
            print(json.dumps(out))
            return

    workdir = Path(tempfile.mkdtemp(prefix="gcb-scale-"))
    try:
        os.chdir(workdir)
        for scale in scales:
            rng = random.Random(hash(tid) & 0xFFFF)
            try:
                inp = harness.make_input(scale, rng)
            except Exception as e:  # noqa: BLE001
                out["scales"][scale] = {"error": f"make_input:{e}"}
                continue
            size = len(json.dumps(inp, default=str))
            os.environ.update(inputmod.stage(REPO / "inputs" / cat / tid / scale,
                                             workdir, inp))
            sys.stdin = io.StringIO(inputmod.stdin_text(inp))
            if ref_only:
                c_ms, c_err = None, None
            else:
                c_ms, c_out, c_err = timed_reps(lambda: harness.run(cand, inp))
            r_ms, r_out, r_err = timed_reps(lambda: harness.run(ref_ns, inp))
            entry = {"size_bytes": size, "cand_ms": (round(c_ms, 4) if c_ms is not None else None),
                     "ref_ms": round(r_ms, 4),
                     "cand_ok": c_err is None, "ref_ok": r_err is None}
            if c_err:
                entry["cand_error"] = c_err
            if r_err:
                entry["ref_error"] = r_err
            out["scales"][scale] = entry
            if (not entry["cand_ok"]) or (not entry["ref_ok"]) \
                    or max(c_ms or 0, r_ms or 0) > BUDGET_MS:
                out["budget_exceeded_at"] = scale
                break
    finally:
        os.chdir(REPO)
        sys.stdin = sys.__stdin__
        shutil.rmtree(workdir, ignore_errors=True)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
