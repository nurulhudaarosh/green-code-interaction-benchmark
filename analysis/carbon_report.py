#!/usr/bin/env python3
"""Convert measured energy (J, package RAPL) into operational CO2eq.

    co2_g = (energy_j / 3.6e6 kWh_per_j) * grid_intensity_g_per_kwh

Writes results/final/carbon_report.{json,csv} and the per-unit carbon CSV,
plus results/final/plots/carbon_by_condition.png.
"""
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "results" / "energy_runs.jsonl"
FINAL = REPO / "results" / "final"
PLOTS = FINAL / "plots"
CONFIG = REPO / "config" / "hardware.json"

KWH_PER_J = 1.0 / 3.6e6
DEFAULT_INTENSITY = {"global_average": 480, "us_average": 369,
                     "eu_average": 251, "low_carbon_france": 56}
CONDS = ["ONE_SHOT", "BUG_FIX", "FEATURE_ADDITION", "EDGE_CASE", "FULL_MULTI_TURN"]


def joules_to_gco2(energy_j, intensity_g_per_kwh):
    return energy_j * KWH_PER_J * intensity_g_per_kwh


def load_intensity():
    try:
        cfg = json.loads(CONFIG.read_text())
        grid = cfg.get("grid_carbon_intensity", {})
        sources = grid.get("sources_gco2eq_per_kwh", DEFAULT_INTENSITY)
        primary = grid.get("primary", "global_average")
    except (OSError, json.JSONDecodeError):
        sources, primary = DEFAULT_INTENSITY, "global_average"
    if primary not in sources:
        primary = next(iter(sources))
    return primary, sources


def load_units():
    units = {}
    for line in LEDGER.read_text().splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("status") != "ok" or r.get("energy_pkg_j") in (None, ""):
            continue
        key = (r["category"], r["task_id"], r["model"], r["condition"])
        units[key] = float(r["energy_pkg_j"])
    return units


def med(vals):
    return statistics.median(vals) if vals else None


def mean(vals):
    return statistics.mean(vals) if vals else None


def main():
    primary, sources = load_intensity()
    intensity = sources[primary]
    units = load_units()
    FINAL.mkdir(parents=True, exist_ok=True)

    co2 = {k: joules_to_gco2(e, intensity) for k, e in units.items()}

    with (FINAL / "carbon_report.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["category", "task_id", "model", "condition",
                    "energy_j", "co2_ug"])
        for (cat, tid, model, cond), e in sorted(units.items()):
            w.writerow([cat, tid, model, cond, e, round(co2[(cat, tid, model, cond)] * 1e6, 6)])

    by_cond = {}
    for cond in CONDS:
        vals = [e for k, e in units.items() if k[3] == cond]
        cvals = [co2[k] for k in units if k[3] == cond]
        if vals:
            by_cond[cond] = {
                "n": len(vals),
                "mean_energy_j": round(mean(vals), 4),
                "median_energy_j": round(med(vals), 4),
                "mean_co2_ug": round(mean(cvals) * 1e6, 3),
                "median_co2_ug": round(med(cvals) * 1e6, 3),
                "total_co2_ug": round(sum(cvals) * 1e6, 3),
                "total_co2_mg": round(sum(cvals) * 1e3, 6)}

    delta = {}
    for cond in CONDS[1:]:
        pairs = [(co2[(k[0], k[1], k[2], "ONE_SHOT")], co2[k])
                 for k in units if k[3] == cond
                 and (k[0], k[1], k[2], "ONE_SHOT") in units]
        pairs = [(a, b) for a, b in pairs if a > 0]
        if len(pairs) < 5:
            continue
        pct = [(b - a) / a * 100 for a, b in pairs]
        abs_ug = [(b - a) * 1e6 for a, b in pairs]
        delta[cond] = {
            "n_paired": len(pct),
            "mean_pct": round(mean(pct), 2),
            "median_pct": round(med(pct), 2),
            "mean_abs_ug_per_run": round(mean(abs_ug), 3),
            "median_abs_ug_per_run": round(med(abs_ug), 3),
            "median_oneshot_co2_ug": round(med([a for a, _ in pairs]) * 1e6, 3),
            "median_condition_co2_ug": round(med([b for _, b in pairs]) * 1e6, 3)}

    total_energy = sum(units.values())
    total_co2_g = joules_to_gco2(total_energy, intensity)
    med_c4 = by_cond.get("FULL_MULTI_TURN", {}).get("median_co2_ug")
    med_c0 = by_cond.get("ONE_SHOT", {}).get("median_co2_ug")

    sensitivity = {}
    for name, ci in sources.items():
        sensitivity[name] = {
            "intensity_gco2eq_per_kwh": ci,
            "total_co2_mg": round(joules_to_gco2(total_energy, ci) * 1e3, 6),
            "median_oneshot_co2_ug": round(joules_to_gco2(med([e for k, e in units.items() if k[3] == "ONE_SHOT"]), ci) * 1e6, 3),
            "median_multi_turn_co2_ug": round(joules_to_gco2(med([e for k, e in units.items() if k[3] == "FULL_MULTI_TURN"]), ci) * 1e6, 3)}

    report = {
        "primary_intensity_source": primary,
        "intensity_gco2eq_per_kwh": intensity,
        "n_units": len(units),
        "total": {
            "energy_j": round(total_energy, 3),
            "energy_kwh": round(total_energy * KWH_PER_J, 9),
            "co2_g": round(total_co2_g, 6),
            "co2_mg": round(total_co2_g * 1e3, 4)},
        "by_condition": by_cond,
        "delta_vs_oneshot": delta,
        "scaling": {
            "median_oneshot_co2_ug_per_run": med_c0,
            "median_multi_turn_co2_ug_per_run": med_c4,
            "extra_co2_ug_per_multi_turn_run": round(med_c4 - med_c0, 3) if med_c0 and med_c4 else None,
            "projected_1e6_runs_g": round(sum(c for k, c in co2.items() if k[3] == "FULL_MULTI_TURN") / max(1, sum(1 for k in co2 if k[3] == "FULL_MULTI_TURN")) * 1e6, 3) if co2 else None},
        "sensitivity_by_intensity": sensitivity}

    (FINAL / "carbon_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        make_plot(by_cond)
    except Exception as exc:  # plotting is best-effort
        print(f"[carbon] plot skipped: {exc}", file=sys.stderr)

    print(f"carbon report: {len(units)} units, {intensity} gCO2eq/kWh ({primary})")
    for cond, s in by_cond.items():
        print(f"  {cond:<17} n={s['n']:<4} median={s['median_co2_ug']} ugCO2  total={s['total_co2_mg']} mgCO2")
    print(f"  TOTAL {report['total']['co2_mg']} mgCO2 ({report['total']['energy_j']} J)")
    print("-> results/final/carbon_report.{json,csv}")


def make_plot(by_cond):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    PLOTS.mkdir(parents=True, exist_ok=True)
    conds = [c for c in CONDS if c in by_cond]
    short = ["C0\nONE_SHOT", "C1\nBUG_FIX", "C2\nFEATURE\nADD",
             "C3\nEDGE\nCASE", "C4\nFULL\nMULTI-TURN"]
    labels = [short[CONDS.index(c)] for c in conds]
    vals = [by_cond[c]["median_co2_ug"] for c in conds]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(range(len(conds)), vals, color="#059669", width=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v + max(vals) * 0.02, f"{v:.1f}", ha="center", fontsize=9)
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Median operational CO2eq per run (ug)")
    ax.set_title("Median carbon footprint of final program by interaction condition")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOTS / "carbon_by_condition.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    print("wrote carbon_by_condition.png")


if __name__ == "__main__":
    main()
