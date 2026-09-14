#!/usr/bin/env python3
"""Statistical tests for RQ1 (one-shot vs each condition) when enough
samples exist. Non-parametric (energy data is skewed). Writes
results/final/statistical_tests.json.

Requires scipy; skipped gracefully if unavailable or data too small.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from energy_analysis import CONDITIONS  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
MIN_N = 5


def main():
    delta_file = REPO / "results" / "processed" / "delta_energy.csv"
    if not delta_file.is_file():
        print("run energy_analysis.py first")
        return 0
    import csv
    groups = defaultdict(list)
    with delta_file.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            groups[r["condition"]].append(float(r["delta_energy_pct"]))

    results = {"tests": {}}
    try:
        from scipy import stats
    except ImportError:
        print("scipy not installed — recording raw medians only")
        stats = None

    for cond, vals in sorted(groups.items()):
        entry = {"n": len(vals),
                 "median_delta_energy_pct": sorted(vals)[len(vals) // 2] if vals else None}
        if stats and len(vals) >= MIN_N:
            # H0: median delta == 0 (condition == one-shot)
            try:
                stat, p = stats.wilcoxon(vals)
                entry["wilcoxon_p_vs_one_shot"] = round(float(p), 5)
            except ValueError:
                pass
            try:
                stat, p = stats.mannwhitneyu(
                    vals, [0.0], alternative="two-sided")
                entry["mannwhitney_p_vs_zero"] = round(float(p), 5)
            except ValueError:
                pass
        elif len(vals) < MIN_N:
            entry["note"] = f"needs >= {MIN_N} pairs for tests"
        results["tests"][cond] = entry

    # RQ2: does the effect vary across models? Kruskal-Wallis per condition.
    all_rows = []
    with delta_file.open(encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))
    if stats:
        by_cond_model = defaultdict(lambda: defaultdict(list))
        for r in all_rows:
            by_cond_model[r["condition"]][r["model"]].append(
                float(r["delta_energy_pct"]))
        rq2 = {}
        for cond, models in sorted(by_cond_model.items()):
            samples = [v for v in models.values() if len(v) >= MIN_N]
            if len(samples) >= 2:
                stat, p = stats.kruskal(*samples)
                rq2[cond] = {"models": len(samples), "kruskal_p": round(float(p), 5)}
        results["rq2_effect_varies_across_models"] = rq2

    final = REPO / "results" / "final"
    final.mkdir(parents=True, exist_ok=True)
    (final / "statistical_tests.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
