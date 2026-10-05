#!/usr/bin/env python3
"""Sync code_metrics.csv dynamic columns from the authoritative ledger.

code_metrics.csv carried stale energy values for 23 units (e.g. identical
0.5312 J fills for RA ONE_SHOT rows). The append-only ledger
results/energy_runs.jsonl (latest ok record per unit) is authoritative.
This script overwrites energy_pkg_j/energy_core_j/runtime_s/peak_mem_mb and
re-derives power_w/energy_per_sloc/energy_per_kb_input in place (with a
.bak of the original).
"""

import csv
import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CM = REPO / "results" / "final" / "code_metrics.csv"
LEDGER = REPO / "results" / "energy_runs.jsonl"


def main():
    led = {}
    for line in LEDGER.read_text().splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("status") != "ok":
            continue
        led[(r["category"], r["task_id"], r["model"], r["condition"])] = r
    shutil.copy(CM, str(CM) + ".bak")
    rows = list(csv.DictReader(open(CM, encoding="utf-8")))
    n_sync = 0
    for r in rows:
        if r["status"] != "ok":
            continue
        k = (r["category"], r["task_id"], r["model"], r["condition"])
        L = led.get(k)
        if not L:
            continue
        r["energy_pkg_j"] = L["energy_pkg_j"]
        r["energy_core_j"] = L.get("energy_core_j", "")
        r["runtime_s"] = L["runtime_s"]
        r["peak_mem_mb"] = L.get("peak_mem_mb", "")
        try:
            e, t = float(L["energy_pkg_j"]), float(L["runtime_s"])
            r["power_w"] = round(e / t, 4) if t > 0 else ""
            r["energy_per_sloc"] = round(e / float(r["sloc"]), 6) if r.get("sloc") else ""
            ib = float(r["input_bytes"]) if r.get("input_bytes") else 0
            r["energy_per_kb_input"] = round(e / (ib / 1024), 6) if ib else ""
        except (TypeError, ValueError, ZeroDivisionError):
            pass
        n_sync += 1
    with open(CM, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"[sync] {n_sync} ok units synced from ledger")


if __name__ == "__main__":
    main()
