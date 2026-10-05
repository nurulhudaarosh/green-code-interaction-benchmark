#!/usr/bin/env python3
"""Merge static code metrics + empirical scaling + energy into paper tables.

Reads:
  results/final/code_metrics.csv
  results/final/scaling.csv                (optional / partial)
Writes:
  results/final/complexity_metrics.json    (all tables the paper cites)
  results/final/complexity_metrics.csv     (joined per-program table)
  results/final/plots/metrics_*.png
"""
import csv
import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FINAL = REPO / "results" / "final"
PLOTS = FINAL / "plots"
CONDS = ["ONE_SHOT", "BUG_FIX", "FEATURE_ADDITION", "EDGE_CASE", "FULL_MULTI_TURN"]

DELTA_FIELDS = ["sloc", "cyclomatic", "complexity_rank", "functions",
                "max_loop_depth", "energy_pkg_j", "runtime_s", "peak_mem_mb",
                "power_w", "cand_slope_ml"]


def fnum(x):
    try:
        if x in ("", None):
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def load_csv(path):
    if not Path(path).is_file():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def median(vals):
    vals = [v for v in vals if v is not None]
    return round(st.median(vals), 4) if vals else None


def mean(vals):
    vals = [v for v in vals if v is not None]
    return round(st.mean(vals), 4) if vals else None


def pct(vals, pred):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return round(100 * sum(1 for v in vals if pred(v)) / len(vals), 1)


def summarize_group(rows, key_fields):
    g = defaultdict(list)
    for r in rows:
        g[tuple(r[k] for k in key_fields)].append(r)
    out = {}
    for k, sub in sorted(g.items()):
        parsed = [r for r in sub if r.get("parse_ok") == "1"]
        slope = [fnum(r.get("cand_slope_ml")) for r in parsed]
        out["|".join(k)] = {
            "n": len(sub),
            "n_measured": sum(1 for r in sub if r.get("status") == "ok"),
            "n_slope": len([s for s in slope if s is not None]),
            "median_sloc": median([fnum(r.get("sloc")) for r in parsed]),
            "median_functions": median([fnum(r.get("functions")) for r in parsed]),
            "median_loops": median([fnum(r.get("loops")) for r in parsed]),
            "median_cyclomatic": median([fnum(r.get("cyclomatic")) for r in parsed]),
            "median_max_loop_depth": median([fnum(r.get("max_loop_depth")) for r in parsed]),
            "median_complexity_rank": median([fnum(r.get("complexity_rank")) for r in parsed]),
            "pct_quadratic_plus": pct([fnum(r.get("complexity_rank")) for r in parsed],
                                      lambda v: v >= 2),
            "pct_recursive": pct([fnum(r.get("recursion")) for r in parsed], lambda v: v >= 1),
            "median_energy_j": median([fnum(r.get("energy_pkg_j")) for r in sub]),
            "median_runtime_s": median([fnum(r.get("runtime_s")) for r in sub]),
            "median_peak_mem_mb": median([fnum(r.get("peak_mem_mb")) for r in sub]),
            "median_power_w": median([fnum(r.get("power_w")) for r in sub]),
            "median_slope": median(slope),
            "pct_superlinear": pct(slope, lambda v: v >= 1.5),
        }
    return out


def paired_deltas(rows):
    """Within (category, task, model): value(condition) - value(ONE_SHOT)."""
    # index by unit then condition
    units = defaultdict(dict)
    for r in rows:
        units[(r["category"], r["task_id"], r["model"])][r["condition"]] = r
    deltas = {}
    for field in DELTA_FIELDS:
        per_cond = {}
        for c in CONDS[1:]:
            diffs = []
            for conds in units.values():
                if c in conds and "ONE_SHOT" in conds:
                    a = fnum(conds[c].get(field))
                    b = fnum(conds["ONE_SHOT"].get(field))
                    if a is not None and b is not None:
                        diffs.append(a - b)
            per_cond[c] = {"n_paired": len(diffs),
                           "mean_delta": round(st.mean(diffs), 4) if diffs else None,
                           "median_delta": median(diffs),
                           "pct_increase": (round(100 * sum(1 for d in diffs if d > 0) / len(diffs), 1)
                                             if diffs else None)}
        deltas[field] = per_cond
    return deltas


def static_empirical_agreement(rows):
    """Compare estimated complexity class to the empirical slope bucket."""
    pairs = []
    for r in rows:
        s = fnum(r.get("cand_slope_ml"))
        rank = fnum(r.get("complexity_rank"))
        if s is None or rank is None or rank < 0 or not _reliable(r):
            continue
        pairs.append((rank, s))
    if len(pairs) < 10:
        return None
    rx = [p[0] for p in pairs]
    ry = [p[1] for p in pairs]
    try:
        from scipy.stats import spearmanr
        rho = float(spearmanr(rx, ry).statistic)
    except Exception:
        rho = None
    # classify estimator as superlinear if rank>=2; empirical if slope>=1.5
    tp = sum(1 for r, s in pairs if r >= 2 and s >= 1.5)
    fp = sum(1 for r, s in pairs if r >= 2 and s < 1.5)
    fn = sum(1 for r, s in pairs if r < 2 and s >= 1.5)
    tn = sum(1 for r, s in pairs if r < 2 and s < 1.5)
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn) if tp + fn else None
    return {"n": len(pairs), "spearman_rank_vs_slope": round(rho, 4) if rho is not None else None,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(prec, 3) if prec else None,
            "recall": round(rec, 3) if rec else None}


def declared_agreement(rows):
    sub = [r for r in rows if r.get("complexity_compliant") not in ("", None)
           and r.get("parse_ok") == "1"]
    if not sub:
        return None
    return {"n": len(sub),
            "compliant_rate": round(100 * sum(int(r["complexity_compliant"]) for r in sub) / len(sub), 1)}


def _reliable(r, min_large_ms=5.0):
    """A scaling slope is trustworthy only when the large-scale run is well
    above process/call overhead."""
    large = fnum(r.get("cand_ms_large"))
    return large is not None and large >= min_large_ms


def write_scaling_summary(rows):
    """Rebuild results/final/scaling_summary.json from the joined rows
    (works even if the probe was stopped before writing its own summary)."""
    sl = []
    refs_by_task = {}
    by_cond = defaultdict(list)
    by_model = defaultdict(list)
    by_cat = defaultdict(list)
    for r in rows:
        s = fnum(r.get("cand_slope_ml"))
        if s is not None and _reliable(r):
            sl.append(s)
            by_cond[r["condition"]].append(s)
            by_model[r["model"]].append(s)
            by_cat[r["category"]].append(s)
        rs = fnum(r.get("ref_slope"))
        if rs is not None:
            refs_by_task.setdefault((r["category"], r["task_id"]), rs)
    refs = list(refs_by_task.values())

    def summ(d):
        return {k: {"n": len(v), "median_slope": median(v),
                    "pct_superlinear": pct(v, lambda x: x >= 1.5)}
                for k, v in sorted(d.items())}

    out = {
        "n_programs": len(rows),
        "n_slopes": len(sl),
        "n_reference_tasks": len(refs),
        "median_cand_slope_ml": median(sl),
        "median_reference_slope": median(refs),
        "by_condition": summ(by_cond),
        "by_model": summ(by_model),
        "by_category": summ(by_cat),
    }
    (FINAL / "scaling_summary.json").write_text(json.dumps(out, indent=2),
                                                encoding="utf-8")
    return out


def make_plots(rows, summary):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return
    PLOTS.mkdir(parents=True, exist_ok=True)

    # 1. complexity class distribution by condition
    classes = ["O(1)", "O(n)", "O(n log n)", "O(n^2)", "O(n^2 log n)",
               "O(n^3)", "O(n^4)", "O(2^n)", "O(recursive)", "unparseable"]
    fig, ax = plt.subplots(figsize=(9, 5))
    width = 0.16
    import numpy as np
    xs = np.arange(len(classes))
    for i, c in enumerate(CONDS):
        sub = [r for r in rows if r["condition"] == c]
        tot = max(1, len(sub))
        vals = [100 * sum(1 for r in sub if r["estimated_complexity"] == cl) / tot
                for cl in classes]
        ax.bar(xs + (i - 2) * width, vals, width, label=c)
    ax.set_xticks(xs)
    ax.set_xticklabels(classes, rotation=45, ha="right")
    ax.set_ylabel("% of programs")
    ax.set_title("Estimated time-complexity class by interaction condition")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(PLOTS / "metrics_complexity_by_condition.png", dpi=150)
    plt.close(fig)

    # 2. SLOC boxplot by condition
    fig, ax = plt.subplots(figsize=(7, 5))
    data = [[fnum(r.get("sloc")) for r in rows if r["condition"] == c
             and r.get("parse_ok") == "1"] for c in CONDS]
    ax.boxplot([d for d in data], tick_labels=CONDS, showfliers=False)
    ax.set_ylabel("SLOC")
    ax.set_title("Source lines of code by interaction condition")
    fig.tight_layout()
    fig.savefig(PLOTS / "metrics_sloc_by_condition.png", dpi=150)
    plt.close(fig)

    # 3. empirical slope histogram by condition
    fig, ax = plt.subplots(figsize=(8, 5))
    for c in CONDS:
        vals = [fnum(r.get("cand_slope_ml")) for r in rows
                if r["condition"] == c and fnum(r.get("cand_slope_ml")) is not None]
        if vals:
            ax.hist(vals, bins=30, range=(-0.5, 4), alpha=0.4, label=c)
    ax.axvline(1, color="k", ls="--", lw=1)
    ax.axvline(2, color="r", ls="--", lw=1)
    ax.set_xlabel("empirical growth exponent (log-log slope)")
    ax.set_ylabel("count")
    ax.set_title("Empirical runtime growth exponent by condition")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(PLOTS / "metrics_slope_hist.png", dpi=150)
    plt.close(fig)

    # 4. runtime vs energy (log-log)
    fig, ax = plt.subplots(figsize=(6, 5))
    xs = [fnum(r.get("runtime_s")) for r in rows if r.get("status") == "ok"]
    ys = [fnum(r.get("energy_pkg_j")) for r in rows if r.get("status") == "ok"]
    pts = [(x, y) for x, y in zip(xs, ys) if x and y]
    if pts:
        ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=4, alpha=0.3)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("runtime (s)"); ax.set_ylabel("package energy (J)")
    ax.set_title("Runtime vs energy per program")
    fig.tight_layout()
    fig.savefig(PLOTS / "metrics_runtime_vs_energy.png", dpi=150)
    plt.close(fig)

    # 5. energy by condition boxplot
    fig, ax = plt.subplots(figsize=(7, 5))
    data = [[fnum(r.get("energy_pkg_j")) for r in rows if r["condition"] == c
             and r.get("status") == "ok"] for c in CONDS]
    ax.boxplot([d for d in data], tick_labels=CONDS, showfliers=False)
    ax.set_ylabel("package energy (J)")
    ax.set_title("Energy by interaction condition")
    fig.tight_layout()
    fig.savefig(PLOTS / "metrics_energy_by_condition.png", dpi=150)
    plt.close(fig)


def main():
    rows = load_csv(FINAL / "code_metrics.csv")
    try:
        from clean_filter import excluded as _excluded
        _ex = _excluded()
        rows = [r for r in rows if "|".join(
            (r["category"], r["task_id"], r["model"], r["condition"])) not in _ex]
    except Exception:
        pass
    scaling = load_csv(FINAL / "scaling.csv")
    smap = {r["program"].replace("collected/", "", 1): r for r in scaling}
    smap.update({r["program"]: r for r in scaling})
    for r in rows:
        key = r["file"]
        s = smap.get(key) or smap.get(key.replace("collected/", "", 1))
        if s:
            for f in ("cand_slope", "cand_slope_ml", "ref_slope",
                      "cand_ms_small", "cand_ms_medium", "cand_ms_large"):
                r[f] = s.get(f, "")
            r["cand_ok_all"] = s.get("cand_ok_all", "")
    out = {
        "n_programs": len(rows),
        "by_condition": summarize_group(rows, ["condition"]) and
        {c: v for c, v in summarize_group(rows, ["condition"]).items()},
        "by_model": summarize_group(rows, ["model"]),
        "by_category": summarize_group(rows, ["category"]),
        "by_condition_category": summarize_group(rows, ["condition", "category"]),
        "paired_deltas_vs_one_shot": paired_deltas(rows),
        "complexity_distribution": dict(Counter(
            r["estimated_complexity"] for r in rows if r.get("parse_ok") == "1").most_common()),
        "static_vs_empirical": static_empirical_agreement(rows),
        "declared_target_agreement": declared_agreement(rows),
    }
    (FINAL / "complexity_metrics.json").write_text(json.dumps(out, indent=2),
                                                   encoding="utf-8")
    ssum = write_scaling_summary(rows)
    out["scaling"] = ssum
    (FINAL / "complexity_metrics.json").write_text(json.dumps(out, indent=2),
                                                   encoding="utf-8")
    # joined csv
    extra = ["cand_slope", "cand_slope_ml", "ref_slope", "cand_ok_all",
             "cand_ms_small", "cand_ms_medium", "cand_ms_large"]
    cols = list(rows[0].keys()) if rows else []
    for c in extra:
        if cols and c not in cols:
            cols.append(c)
    with (FINAL / "complexity_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    make_plots(rows, out)
    print(f"[complexity_report] {len(rows)} rows, {len(scaling)} scaling rows "
          f"-> complexity_metrics.json/csv + plots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
