#!/usr/bin/env python3
"""Run the full measurement for one queue unit: correctness + energy +
runtime + memory + CPU. Writes results/raw/<category>/<unit>.json and a
ledger line via scripts/measure_progress.py.

Usage (usually called by scripts/run_pipeline.py):
    python3 runner/measure_unit.py --unit '{"category":..., "task_id":..., ...}'
"""

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from sync_drive import load_ledger, save_ledger, record_measured  # noqa: E402

from measurement.rapl import RaplEnergy  # noqa: E402
from measurement.system import machine_info  # noqa: E402
from runner.sandbox import run_capped  # noqa: E402

CFG = json.loads((REPO / "config" / "experiment.json").read_text())
EXEC = CFG.get("execution", {})
TIMEOUT = EXEC.get("timeout_seconds", 300)
WARMUP = EXEC.get("warmup_runs", 1)
RUNS = EXEC.get("measured_runs", 5)


def median(vals):
    vals = [v for v in vals if v is not None]
    return round(statistics.median(vals), 6) if vals else None


def dataset_task(category, task_id):
    ds = REPO / "dataset" / category / "dataset.json"
    try:
        data = json.loads(ds.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    tasks = data.get("tasks") if isinstance(data, dict) else data
    for t in tasks or []:
        if str(t.get("task_id")) == str(task_id):
            return t
    return None


def driver_cmd(code, task_file, category):
    return [sys.executable, str(REPO / "runner" / "executor.py"),
            "--code", str(code), "--task-json", str(task_file),
            "--category", category]


def log(msg):
    print(msg, flush=True)


def measure_unit(unit):
    category, tid = unit["category"], unit["task_id"]
    code = REPO / unit["rel"]
    task = dataset_task(category, tid)
    label = f"{tid}/{unit['model']}/{unit['interaction']}"
    result = {
        "unit": {k: unit[k] for k in ("category", "task_id", "model", "interaction", "file")},
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "code_sha256": unit["sha256"],
        "environment": machine_info(),
        "config": {"warmup_runs": WARMUP, "measured_runs": RUNS, "timeout_s": TIMEOUT},
    }
    if task is None:
        return "error", result | {"status": "error", "reason": "task_not_in_dataset"}

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(task, f)
        task_file = Path(f.name)

    final_out = None
    driver_status = None
    try:
        for i in range(WARMUP):
            stdout, stderr, _, _ = run_capped(driver_cmd(code, task_file, category), TIMEOUT)
        energy, wall, peak, cpu_avg = [], [], [], []
        for _ in range(RUNS):
            with RaplEnergy() as rapl:
                stdout, stderr, res, timed_out = run_capped(
                    driver_cmd(code, task_file, category), TIMEOUT
                )
            e = rapl.stop()
            if timed_out:
                return "error", result | {
                    "status": "error", "reason": "timeout", "driver_stderr": stderr[-2000:]
                }
            energy.append(e["energy_j"])
            wall.append(res["wall_ms"])
            peak.append(res["peak_memory_mb"])
            cpu_avg.append(res["cpu_percent_avg"])
            final_out = stdout
            driver_status = res["returncode"]
    finally:
        task_file.unlink(missing_ok=True)

    payload = None
    if final_out:
        for line in reversed(final_out.strip().splitlines()):
            if line.startswith("{"):
                payload = json.loads(line)
                break

    if payload is None:
        return "error", result | {
            "status": "error", "reason": f"no_driver_output (rc={driver_status})",
            "driver_stderr": (stderr or "")[-2000:],
        }
    if payload.get("status") == "skipped":
        return "skipped", result | {"status": "skipped", "reason": payload.get("reason")}
    if payload.get("status") == "error":
        return "error", result | {"status": "error", "reason": payload.get("reason")}

    metrics = {
        "energy_j": median(energy),
        "runtime_ms": median(wall),
        "peak_memory_mb": median(peak),
        "cpu_percent_avg": median(cpu_avg),
        "energy_per_runtime_j_ms": (
            round(median(energy) / median(wall), 6)
            if median(energy) and median(wall) else None
        ),
    }
    # Energy-first: a program that RAN on the workload is measured even
    # when its output differs from the reference; `correct` records the
    # correctness verdict separately for analysis-time filtering.
    ran = bool(payload.get("ran"))
    status = "measured" if ran else "error"
    out = result | {
        "status": status,
        "correct": payload.get("correct"),
        "ran": ran,
        "inputs": payload.get("inputs"),
        "scales": payload.get("scales"),
        "candidate_runtime_ms": payload.get("candidate_runtime_ms"),
        "reference_runtime_ms": payload.get("reference_runtime_ms"),
        "metrics": metrics,
        "driver_errors": payload.get("errors", []),
    }
    if not ran:
        out["reason"] = "program_did_not_run (entry missing or errored)"
    return status, out


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--unit", help="JSON of one queue unit")
    g.add_argument("--unit-file", help="path to JSON file of one queue unit")
    a = ap.parse_args()
    unit = json.loads(a.unit or Path(a.unit_file).read_text(encoding="utf-8"))

    status, out = measure_unit(unit)

    raw_dir = REPO / "results" / "raw" / unit["category"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    name = f"{unit['task_id']}__{unit['model']}__{unit['interaction']}.json"
    metrics_path = raw_dir / name
    metrics_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "measure_progress.py"),
         "record", unit["rel"], "--status", status,
         "--metrics", str(metrics_path.relative_to(REPO)),
         "--note", str(out.get("reason", "")), "--if-changed"],
        check=True,
    )
    ledger = load_ledger()
    task_key = f"{unit['category']}|{unit['model']}|" \
        f"{unit['interaction']}|{unit['task_id']}"
    record_measured(ledger, unit["rel"], sha=unit.get("sha256"),
                    task_key=task_key)
    save_ledger(ledger)
    print(json.dumps({"status": status, "unit": unit["rel"],
                      "metrics": str(metrics_path)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
