#!/usr/bin/env python3
"""Aggregate energy_runs.jsonl into per-unit metrics, paired comparisons,
statistical tests. Writes results/final/energy_report.{json,csv}."""
import json
import math
from pathlib import Path

from scipy import stats

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "results" / "energy_runs.jsonl"
FINAL = REPO / "results" / "final"
FINAL.mkdir(parents=True, exist_ok=True)

CONDS = ["ONE_SHOT", "BUG_FIX", "FEATURE_ADDITION", "EDGE_CASE", "FULL_MULTI_TURN"]


def load():
    units = {}
    for line in LEDGER.read_text().splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("status") != "ok":
            continue
        key = (r["category"], r["task_id"], r["model"], r["condition"])
        # keep latest measurement per key
        units[key] = {"energy_j": r["energy_pkg_j"], "runtime_s": r["runtime_s"],
                      "mem_mb": r.get("peak_mem_mb"), "file": r["file"],
                      "condition": r["condition"], "model": r["model"],
                      "category": r["category"], "task_id": r["task_id"]}
    return units


def med(vals):
    v = sorted(vals)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def mean(vals):
    return sum(vals) / len(vals) if vals else None


def main():
    units = load()
    # ---- per-unit CSV
    with (FINAL / "energy_report.csv").open("w") as f:
        f.write("category,task_id,model,condition,energy_j,runtime_s,mem_mb\n")
        for (cat, tid, model, cond), m in sorted(units.items()):
            f.write(f"{cat},{tid},{model},{cond},{m['energy_j']},"
                    f"{m['runtime_s']},{m['mem_mb']}\n")

    # ---- paired comparisons C0 vs each condition
    pairs = {}   # cond -> list of (key, E_C0, E_CX)
    for cond in CONDS[1:]:
        plist = []
        for key, m in units.items():
            if cond == m["condition"]:
                c0 = (key[0], key[1], key[2], "ONE_SHOT")
                if c0 in units and units[c0]["energy_j"] > 0:
                    plist.append((key, units[c0]["energy_j"], m["energy_j"]))
        pairs[cond] = plist

    report = {"n_units": len(units),
              "n_paired": {c: len(v) for c, v in pairs.items()},
              "overall": {},
              "delta": {}, "wilcoxon": {}, "by_model": {}, "by_category": {}}

    for cond in CONDS:
        vals = [m["energy_j"] for m in units.values() if m["condition"] == cond]
        if vals:
            report["overall"][cond] = {
                "n": len(vals), "mean_j": round(mean(vals), 4),
                "median_j": round(med(vals), 4),
                "mean_runtime_s": round(mean([m["runtime_s"] for m in units.values()
                                              if m["condition"] == cond]), 4)}

    for cond, plist in pairs.items():
        if len(plist) < 5:
            continue
        deltas = [(b - a) / a * 100 for _, a, b in plist]
        report["delta"][cond] = {
            "mean_pct": round(mean(deltas), 2),
            "median_pct": round(med(deltas), 2),
            "n_increase": sum(1 for d in deltas if d > 0),
            "n_decrease": sum(1 for d in deltas if d < 0)}
        try:
            w = stats.wilcoxon([a for _, a, _ in plist], [b for _, _, b in plist])
            report["wilcoxon"][cond] = {"statistic": round(float(w.statistic), 1),
                                        "p_value": round(float(w.pvalue), 4)}
        except ValueError:
            report["wilcoxon"][cond] = {"p_value": None}

    # ---- by model (mean energy + C0-vs-C4 delta)
    models = sorted({k[2] for k in units})
    for model in models:
        e_by_cond = {}
        for cond in CONDS:
            vals = [m["energy_j"] for k, m in units.items()
                    if k[2] == model and m["condition"] == cond]
            if vals:
                e_by_cond[cond] = round(mean(vals), 4)
        d4 = []
        for (cat, tid, mdl, cond), m in units.items():
            if mdl == model and cond == "FULL_MULTI_TURN":
                c0 = (cat, tid, mdl, "ONE_SHOT")
                if c0 in units and units[c0]["energy_j"] > 0:
                    d4.append((m["energy_j"] - units[c0]["energy_j"])
                              / units[c0]["energy_j"] * 100)
        report["by_model"][model] = {
            "mean_energy_by_cond": e_by_cond,
            "mean_delta_vs_oneshot_pct": round(mean(d4), 2) if d4 else None,
            "n_paired_c4": len(d4)}

    # ---- by category
    cats = sorted({k[0] for k in units})
    for cat in cats:
        d4 = []
        for (c, tid, mdl, cond), m in units.items():
            if c == cat and cond == "FULL_MULTI_TURN":
                c0 = (c, tid, mdl, "ONE_SHOT")
                if c0 in units and units[c0]["energy_j"] > 0:
                    d4.append((m["energy_j"] - units[c0]["energy_j"])
                              / units[c0]["energy_j"] * 100)
        report["by_category"][cat] = {
            "n_units": sum(1 for k in units if k[0] == cat),
            "mean_delta_vs_oneshot_pct": round(mean(d4), 2) if d4 else None,
            "n_paired_c4": len(d4)}

    (FINAL / "energy_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2)[:1200])


if __name__ == "__main__":
    main()
