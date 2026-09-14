#!/usr/bin/env python3
"""Aggregate ledger + raw result files -> results/processed/metrics.csv.

Run directly or import load_metrics() from other analysis scripts.
"""

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "results" / "measurement_ledger.jsonl"
PROCESSED = REPO / "results" / "processed"

COLUMNS = [
    "category", "task_id", "model", "interaction", "status", "correct",
    "energy_j", "runtime_ms", "peak_memory_mb", "cpu_percent_avg",
    "energy_per_runtime_j_ms", "candidate_runtime_ms", "reference_runtime_ms",
    "note", "measured_at", "code_sha256", "metrics_file",
]


def load_metrics():
    rows = []
    if not LEDGER.is_file():
        return rows
    latest = {}
    order = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        key = (e.get("category"), e.get("task_id"), e.get("model"),
               e.get("interaction"), e.get("file"))
        if key not in latest:
            order.append(key)
        latest[key] = e
    for key in order:
        e = latest[key]
        row = {c: "" for c in COLUMNS}
        row.update({
            "category": e.get("category"), "task_id": e.get("task_id"),
            "model": e.get("model"), "interaction": e.get("interaction"),
            "status": e.get("status"), "note": e.get("note", ""),
            "code_sha256": e.get("sha256", ""),
            "metrics_file": e.get("metrics", ""),
        })
        if e.get("metrics"):
            mf = REPO / e["metrics"]
            if mf.is_file():
                try:
                    m = json.loads(mf.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    m = {}
                met = m.get("metrics") or {}
                row.update({
                    "correct": m.get("correct", ""),
                    "measured_at": m.get("measured_at", ""),
                    "candidate_runtime_ms": m.get("candidate_runtime_ms", ""),
                    "reference_runtime_ms": m.get("reference_runtime_ms", ""),
                    **{k: met.get(k, "") for k in
                       ("energy_j", "runtime_ms", "peak_memory_mb",
                        "cpu_percent_avg", "energy_per_runtime_j_ms")},
                })
        rows.append(row)
    return rows


def main():
    rows = load_metrics()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out = PROCESSED / "metrics.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    n_ok = sum(1 for r in rows if r["status"] == "measured")
    print(f"metrics.csv: {len(rows)} rows ({n_ok} measured) -> {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
