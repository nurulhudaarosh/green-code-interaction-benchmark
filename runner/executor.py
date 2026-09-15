#!/usr/bin/env python3
"""Measurement driver — runs INSIDE the sandboxed child process.

Loads the candidate program + task + per-task harness, executes candidate
and reference on generated inputs at each scale, and prints ONE JSON
object on stdout:

    {"status": "ok"|"skipped"|"error", ...metrics/correctness...}

Exit codes: 0 ok, 3 skipped (no harness / contract mismatch), 4 error.

Harness protocol (tests/harness/<category>/<TASK_ID>.py):
    SCALES = ["small", "medium"]           # optional override
    def make_input(scale, rng) -> object   # reproducible workload
    def run(module, inp) -> json-serial    # call candidate/reference API

Both the candidate module and the reference namespace are passed through
the same harness `run()`, so per-task API differences are absorbed there.
"""

import argparse
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


def emit(obj, code):
    print(json.dumps(obj, default=str))
    sys.exit(code)


def _ran_ok(out):
    """The program produced a real result (no exception, no error dict,
    not None). Correctness is judged separately."""
    if out is None:
        return False
    if isinstance(out, dict):
        vals = list(out.values())
        if not vals:
            return False
        v = vals[0]
        if v is None or (isinstance(v, dict) and "__error__" in v):
            return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", required=True)
    ap.add_argument("--task-json", required=True, help="file with the task dict")
    ap.add_argument("--category", required=True)
    a = ap.parse_args()

    task = json.loads(Path(a.task_json).read_text(encoding="utf-8"))
    tid = task["task_id"]

    harness_path = REPO / "tests" / "harness" / a.category / f"{tid}.py"
    if not harness_path.is_file():
        emit({"status": "skipped", "reason": "no_harness", "harness": str(harness_path.relative_to(REPO))}, 3)

    spec = importlib.util.spec_from_file_location("harness", harness_path)
    harness = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(harness)
    except Exception as e:
        emit({"status": "error", "reason": f"harness_import:{e}"}, 4)

    scales = getattr(harness, "SCALES", ["small", "medium"])
    errors = []

    try:
        cand = tester.load_module(a.code)
    except Exception as e:
        emit({"status": "error", "reason": f"candidate_import:{type(e).__name__}: {e}"}, 4)
    try:
        ref_ns = tester.load_reference(task)
    except Exception as e:
        emit({"status": "error", "reason": f"reference_import:{e}"}, 4)

    workdir = Path(tempfile.mkdtemp(prefix="gcb-run-"))
    inputs_rel = f"inputs/{a.category}/{tid}"
    results = {}
    cand_ms = ref_ms = 0.0
    peak_pass = True
    try:
        os.chdir(workdir)
        for scale in scales:
            rng = random.Random(hash(tid) & 0xFFFF)
            try:
                inp = harness.make_input(scale, rng)
            except Exception as e:
                emit({"status": "error", "reason": f"make_input:{e}"}, 4)

            # Auto-input: generated workload is also materialized as plain
            # files (inputs/<cat>/<task>/<scale>/) plus deterministic stdin,
            # so file-/stdin-driven programs run without manual input.
            os.environ.update(inputmod.stage(
                REPO / inputs_rel / scale, workdir, inp))
            sys.stdin = io.StringIO(inputmod.stdin_text(inp))

            t0 = time.perf_counter()
            out_c = tester.safe_call(lambda: harness.run(cand, inp), (), {}, errors)
            cand_ms += (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            out_r = tester.safe_call(lambda: harness.run(ref_ns, inp), (), {}, errors)
            ref_ms += (time.perf_counter() - t0) * 1000

            ran_c = _ran_ok(out_c)
            ran_r = _ran_ok(out_r)
            if out_c is None:
                peak_pass = False
                results[scale] = {"correct": False, "ran": False,
                                  "error": errors[-1] if errors else "returned None"}
            elif not ran_c:
                # entry resolved but the program itself errored/returned None
                peak_pass = False
                results[scale] = {"correct": False, "ran": False,
                                  "error": "program returned None/error"}
            else:
                ok = tester.compare(out_c, out_r)
                peak_pass = peak_pass and ok
                results[scale] = {"correct": ok, "ran": True,
                                  "reference_ran": ran_r}
    finally:
        os.chdir(REPO)
        sys.stdin = sys.__stdin__
        shutil.rmtree(workdir, ignore_errors=True)

    emit({
        "status": "ok",
        "correct": peak_pass,
        "ran": all(v.get("ran") for v in results.values()) and bool(results),
        "reference_ran": all(v.get("reference_ran", True) for v in results.values()),
        "scales": results,
        "candidate_runtime_ms": round(cand_ms, 3),
        "reference_runtime_ms": round(ref_ms, 3),
        "inputs": inputs_rel,
        "errors": errors,
    }, 0)


if __name__ == "__main__":
    main()
