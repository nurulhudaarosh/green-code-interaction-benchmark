#!/usr/bin/env python3
"""Delta-energy analysis (RQ1/RQ3).

dE = (E_condition - E_one_shot) / E_one_shot * 100  per task x model.
Positive  -> condition produced less energy-efficient code.
Negative  -> condition produced more energy-efficient code.
"""

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aggregate import load_metrics, PROCESSED  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
CONDITIONS = ["BUG_FIX", "FEATURE_ADDITION", "EDGE_CASE", "FULL_MULTI_TURN"]


def main():
    rows = [r for r in load_metrics()
            if r["status"] == "measured" and str(r["correct"]) == "True"
            and r["energy_j"] not in ("", None)]
    energy = {}
    for r in rows:
        key = (r["category"], r["task_id"], r["model"])
        energy.setdefault(key, {})[r["interaction"]] = float(r["energy_j"])

    deltas = defaultdict(list)
    out_rows = []
    for (cat, tid, model), e in sorted(energy.items()):
        base = e.get("ONE_SHOT")
        if not base:
            continue
        for cond in CONDITIONS:
            if cond in e:
                de = (e[cond] - base) / base * 100
                deltas[cond].append(de)
                out_rows.append({
                    "category": cat, "task_id": tid, "model": model,
                    "condition": cond, "energy_one_shot_j": base,
                    "energy_condition_j": e[cond], "delta_energy_pct": round(de, 2),
                })

    PROCESSED.mkdir(parents=True, exist_ok=True)
    import csv
    with (PROCESSED / "delta_energy.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "category", "task_id", "model", "condition",
            "energy_one_shot_j", "energy_condition_j", "delta_energy_pct"])
        w.writeheader()
        w.writerows(out_rows)

    summary = {
        cond: {
            "n": len(v),
            "mean_pct": round(statistics.mean(v), 2) if v else None,
            "median_pct": round(statistics.median(v), 2) if v else None,
            "tasks_more_efficient_than_one_shot": sum(1 for x in v if x < 0),
        }
        for cond, v in sorted(deltas.items())
    }
    final = REPO / "results" / "final"
    final.mkdir(parents=True, exist_ok=True)
    (final / "energy_summary.json").write_text(
        json.dumps({"n_pairs": len(out_rows), "by_condition": summary}, indent=2),
        encoding="utf-8")

    print(f"delta_energy pairs: {len(out_rows)}")
    for cond, s in summary.items():
        print(f"  {cond:<17} n={s['n']:<4} median dE={s['median_pct']}%")
    print(f"-> results/processed/delta_energy.csv, results/final/energy_summary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
