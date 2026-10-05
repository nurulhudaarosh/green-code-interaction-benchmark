#!/usr/bin/env python3
"""Regenerate the paired-delta plots from the authoritative joined corpus.

Root cause fixed: results/processed/delta_energy.csv holds a single stale
row (gpt/BUG_FIX), so analysis/plots.py rendered degenerate single-bar
figures (delta_energy_by_model.png, delta_energy_boxplot.png). This script
recomputes paired within-(task, model) energy deltas from
results/final/complexity_metrics.csv (1485 rows, 1309 measured) and
overwrites those two PNGs in place, keeping filenames stable for the
paper sources.
"""
import csv
import statistics as st
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JOINED = REPO / "results" / "final" / "complexity_metrics.csv"
OUT = REPO / "results" / "final" / "plots"
CONDS = ["BUG_FIX", "FEATURE_ADDITION", "EDGE_CASE", "FULL_MULTI_TURN"]
MODELS = ["gpt", "claude", "gemini", "deepseek"]
SHORT = {"BUG_FIX": "C1\nBUG_FIX", "FEATURE_ADDITION": "C2\nFEATURE",
         "EDGE_CASE": "C3\nEDGE", "FULL_MULTI_TURN": "C4\nFULL"}


def paired_deltas():
    """{(model, cond): [delta_pct]} paired within (category, task, model)."""
    from clean_filter import excluded as _excluded
    excl = _excluded()
    base = defaultdict(dict)  # (cat, task, model) -> {cond: energy}
    with JOINED.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if "|".join((r["category"], r["task_id"], r["model"],
                         r["condition"])) in excl:
                continue
            try:
                e = float(r["energy_pkg_j"])
            except (TypeError, ValueError):
                continue
            base[(r["category"], r["task_id"], r["model"])][r["condition"]] = e
    out = defaultdict(list)
    for (_, _, model), d in base.items():
        e0 = d.get("ONE_SHOT")
        if not e0:
            continue
        for c in CONDS:
            if c in d:
                out[(model, c)].append(100.0 * (d[c] - e0) / e0)
    return out


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    deltas = paired_deltas()
    n = sum(len(v) for v in deltas.values())
    print(f"[fix-plots] paired deltas: {n} pairs "
          f"({{(m,c): n}} = "
          + str({k: len(v) for k, v in sorted(deltas.items())}) + ")")

    # 1) grouped bars: median dE per model x condition (the paper's Fig. 5)
    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(MODELS))
    width = 0.8 / len(CONDS)
    for i, c in enumerate(CONDS):
        meds = [st.median(deltas[(m, c)]) if deltas[(m, c)] else 0.0
                for m in MODELS]
        ax.bar([j + (i - 1.5) * width for j in x], meds, width, label=c)
    ax.set_xticks(list(x), MODELS)
    ax.axhline(0, color="grey", lw=1)
    ax.set_ylabel("median ΔE vs one-shot (%)")
    ax.set_title("Interaction effect per model (RQ2)")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(OUT / "delta_energy_by_model.png", dpi=150)
    plt.close(fig)

    # 2) boxplot of paired dE per condition (same root cause, same fix)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot([[d for m in MODELS for d in deltas[(m, c)]] for c in CONDS],
               tick_labels=[SHORT[c] for c in CONDS], showfliers=False)
    ax.axhline(0, color="grey", lw=1)
    ax.set_ylabel("ΔE vs one-shot (%)")
    ax.set_title("Final-code energy change by interaction style")
    fig.tight_layout()
    fig.savefig(OUT / "delta_energy_boxplot.png", dpi=150)
    plt.close(fig)
    print("[fix-plots] overwrote delta_energy_by_model.png + "
          "delta_energy_boxplot.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
