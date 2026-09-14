#!/usr/bin/env python3
"""Interaction-style comparison (RQ2/RQ3): per-model and per-category
breakdowns of energy/runtime metrics across interaction conditions."""

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aggregate import load_metrics, PROCESSED  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
METRICS = ["energy_j", "runtime_ms", "peak_memory_mb", "cpu_percent_avg"]


def main():
    rows = [r for r in load_metrics()
            if r["status"] == "measured" and str(r["correct"]) == "True"]
    if not rows:
        print("no measured rows yet")
        return 0

    agg = defaultdict(lambda: defaultdict(list))
    for r in rows:
        for m in METRICS:
            v = r[m]
            if v not in ("", None):
                agg[(r["model"], r["interaction"])][m].append(float(v))

    out = []
    for (model, interaction), mm in sorted(agg.items()):
        row = {"model": model, "interaction": interaction}
        for m in METRICS:
            vals = mm.get(m, [])
            row[f"{m}_median"] = round(statistics.median(vals), 4) if vals else None
            row[f"{m}_n"] = len(vals)
        out.append(row)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    cols = ["model", "interaction"] + [f"{m}_{s}" for m in METRICS for s in
                                       ("median", "n")]
    with (PROCESSED / "interaction_breakdown.csv").open("w", newline="",
                                                        encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    print(f"interaction_breakdown.csv: {len(out)} model x interaction cells")
    print("-> results/processed/interaction_breakdown.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
