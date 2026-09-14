#!/usr/bin/env python3
"""Paper-ready plots -> results/final/plots/*.png.

Empty datasets are handled gracefully (prints a note, no files).
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "final" / "plots"
CONDITIONS = ["ONE_SHOT", "BUG_FIX", "FEATURE_ADDITION", "EDGE_CASE", "FULL_MULTI_TURN"]


def main():
    delta_file = REPO / "results" / "processed" / "delta_energy.csv"
    metrics_file = REPO / "results" / "processed" / "metrics.csv"
    if not metrics_file.is_file():
        print("no metrics.csv yet — nothing to plot")
        return 0

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import statistics

    OUT.mkdir(parents=True, exist_ok=True)
    plotted = []

    if delta_file.is_file():
        with delta_file.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        by_cond = defaultdict(list)
        by_model = defaultdict(lambda: defaultdict(list))
        for r in rows:
            de = float(r["delta_energy_pct"])
            by_cond[r["condition"]].append(de)
            by_model[r["model"]][r["condition"]].append(de)

        conds = [c for c in CONDITIONS[1:] if by_cond.get(c)]
        if conds:
            fig, ax = plt.subplots(figsize=(8, 5))
            data = [by_cond[c] for c in conds]
            ax.boxplot(data, labels=[c.replace("_", "-\n") for c in conds],
                       showfliers=False)
            ax.axhline(0, color="grey", lw=1)
            ax.set_ylabel("ΔE vs one-shot (%)")
            ax.set_title("Final-code energy change by interaction style")
            fig.tight_layout()
            fig.savefig(OUT / "delta_energy_boxplot.png", dpi=150)
            plotted.append("delta_energy_boxplot.png")

            models = sorted(by_model)
            width = 0.8 / max(len(conds), 1)
            fig, ax = plt.subplots(figsize=(9, 5))
            for i, c in enumerate(conds):
                medians = [
                    statistics.median(by_model[m][c]) if by_model[m].get(c) else 0
                    for m in models
                ]
                ax.bar([j + i * width for j in range(len(models))], medians,
                       width, label=c)
            ax.set_xticks(range(len(models)), models)
            ax.axhline(0, color="grey", lw=1)
            ax.set_ylabel("median ΔE (%)")
            ax.set_title("Interaction effect per model (RQ2)")
            ax.legend(fontsize=8)
            fig.tight_layout()
            fig.savefig(OUT / "delta_energy_by_model.png", dpi=150)
            plotted.append("delta_energy_by_model.png")

    with metrics_file.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f)
                if r["status"] == "measured" and r["energy_j"] and r["runtime_ms"]]
    if rows:
        fig, ax = plt.subplots(figsize=(6, 5))
        colors = {c: f"C{i}" for i, c in enumerate(CONDITIONS)}
        for r in rows:
            ax.scatter(float(r["runtime_ms"]), float(r["energy_j"]),
                       s=25, color=colors.get(r["interaction"], "k"),
                       alpha=0.7)
        handles = [plt.Line2D([], [], marker="o", ls="", color=colors[c],
                              label=c) for c in CONDITIONS if c in colors]
        ax.legend(handles=handles, fontsize=8)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("runtime (ms)")
        ax.set_ylabel("energy (J)")
        ax.set_title("Energy vs runtime (RQ4)")
        fig.tight_layout()
        fig.savefig(OUT / "energy_vs_runtime.png", dpi=150)
        plotted.append("energy_vs_runtime.png")

    print(f"plotted: {plotted if plotted else 'nothing (insufficient data)'}"
          f" -> results/final/plots/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
