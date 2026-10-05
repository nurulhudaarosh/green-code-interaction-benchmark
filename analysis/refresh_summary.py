#!/usr/bin/env python3
"""Refresh stale aggregates in results/final/complexity_summary.json.

code_metrics.py (the original author of that file) is NOT rerun because it
would overwrite the ledger-synced dynamic columns in code_metrics.csv.
Instead this script recomputes, from the clean synced complexity_metrics.csv:
  - n_programs / n_parseable / n_measured
  - all correlations (Spearman + Pearson, scipy)
"""

import csv
import json
from pathlib import Path
from scipy.stats import spearmanr, pearsonr

REPO = Path(__file__).resolve().parent.parent
FINAL = REPO / "results" / "final"

PAIRS = ["sloc", "cyclomatic", "complexity_rank", "max_loop_depth",
         "runtime_s", "energy_pkg_j"]


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main():
    rows = list(csv.DictReader(open(FINAL / "complexity_metrics.csv")))
    ok = [r for r in rows if r["status"] == "ok" and f(r["energy_pkg_j"]) is not None]
    s = json.loads((FINAL / "complexity_summary.json").read_text())
    s["n_programs"] = len(rows)
    s["n_parseable"] = sum(1 for r in rows if r["parse_ok"] == "1")
    s["n_measured"] = len(ok)
    defs = [("sloc_vs_energy", "sloc", "energy_pkg_j"),
            ("cyclomatic_vs_energy", "cyclomatic", "energy_pkg_j"),
            ("complexity_rank_vs_energy", "complexity_rank", "energy_pkg_j"),
            ("loop_depth_vs_energy", "max_loop_depth", "energy_pkg_j"),
            ("cyclomatic_vs_runtime", "cyclomatic", "runtime_s"),
            ("sloc_vs_runtime", "sloc", "runtime_s"),
            ("runtime_vs_energy", "runtime_s", "energy_pkg_j")]
    for name, a, b in defs:
        xy = [(f(r[a]), f(r[b])) for r in ok
              if f(r[a]) is not None and f(r[b]) is not None]
        x, y = zip(*xy)
        s["correlations"][name] = {"n": len(xy),
                                   "spearman_rho": round(float(spearmanr(x, y).statistic), 4),
                                   "pearson_r": round(float(pearsonr(x, y).statistic), 4)}
    (FINAL / "complexity_summary.json").write_text(json.dumps(s, indent=1))
    print("[summary] n =", s["n_programs"], s["n_parseable"], s["n_measured"],
          "| rho(E,t) =", s["correlations"]["runtime_vs_energy"])


if __name__ == "__main__":
    main()
