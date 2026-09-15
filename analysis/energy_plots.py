#!/usr/bin/env python3
"""Generate result plots from results/energy_runs.jsonl -> results/final/plots/."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "results" / "energy_runs.jsonl"
PLOTS = REPO / "results" / "final" / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

CONDS = ["ONE_SHOT", "BUG_FIX", "FEATURE_ADDITION", "EDGE_CASE", "FULL_MULTI_TURN"]
SHORT = ["C0\nONE_SHOT", "C1\nBUG_FIX", "C2\nFEATURE\nADD", "C3\nEDGE\nCASE", "C4\nFULL\nMULTI-TURN"]


def load():
    last = {}
    for line in LEDGER.read_text().splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        last[(r["category"], r["task_id"], r["model"], r["condition"])] = r
    return last


def med(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def mean(v):
    return sum(v) / len(v) if v else 0


def save(fig, name):
    fig.tight_layout()
    fig.savefig(PLOTS / name, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def main():
    data = load()
    ok = {k: r for k, r in data.items() if r["status"] == "ok"}

    # 1. median energy + IQR per condition
    fig, ax = plt.subplots(figsize=(8, 5))
    xs = range(len(CONDS))
    meds, q1, q3 = [], [], []
    for c in CONDS:
        v = sorted(r["energy_pkg_j"] for k, r in ok.items() if k[3] == c)
        meds.append(med(v))
        q1.append(v[int(len(v) * 0.25)])
        q3.append(v[int(len(v) * 0.75)])
    ax.bar(xs, meds, color="#3b82f6", width=0.6)
    ax.errorbar(xs, meds, yerr=[meds[i] - q1[i] for i in xs], fmt="none",
                ecolor="#1e3a8a", capsize=5)
    ax.set_xticks(list(xs)); ax.set_xticklabels(SHORT)
    ax.set_ylabel("Energy per run (J, package RAPL)")
    ax.set_title("Median energy of final program by interaction condition")
    ax.grid(axis="y", alpha=0.3)
    save(fig, "energy_by_condition.png")

    # 2. paired delta vs ONE_SHOT (median + mean) + Wilcoxon p
    fig, ax = plt.subplots(figsize=(8, 5))
    mean_d, med_d, ps = [], [], []
    for c in CONDS[1:]:
        ds = []
        for k, r in ok.items():
            if k[3] == c:
                c0 = (k[0], k[1], k[2], "ONE_SHOT")
                if c0 in ok and ok[c0]["energy_pkg_j"] > 0:
                    ds.append((r["energy_pkg_j"] - ok[c0]["energy_pkg_j"])
                              / ok[c0]["energy_pkg_j"] * 100)
        mean_d.append(mean(ds)); med_d.append(med(ds))
        try:
            ps.append(stats.wilcoxon([ok[(k[0], k[1], k[2], "ONE_SHOT")]["energy_pkg_j"]
                                     for k in ok if k[3] == c and
                                     (k[0], k[1], k[2], "ONE_SHOT") in ok],
                                    [r["energy_pkg_j"] for k, r in ok.items() if k[3] == c
                                     and (k[0], k[1], k[2], "ONE_SHOT") in ok]).pvalue)
        except ValueError:
            ps.append(None)
    x = range(len(CONDS[1:]))
    ax.bar([i - 0.2 for i in x], mean_d, width=0.4, label="mean", color="#ef4444")
    ax.bar([i + 0.2 for i in x], med_d, width=0.4, label="median", color="#10b981")
    for i, p in enumerate(ps):
        if p is not None:
            ax.text(i, max(mean_d[i], med_d[i]) + 8, f"p={p:.3f}", ha="center", fontsize=9)
    ax.set_xticks(list(x)); ax.set_xticklabels(SHORT[1:])
    ax.set_ylabel("Δ Energy vs ONE_SHOT (%)")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_title("Energy change vs one-shot (paired by task×model)")
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    save(fig, "delta_vs_oneshot.png")

    # 3. delta by model
    fig, ax = plt.subplots(figsize=(8, 5))
    models = sorted({k[2] for k in ok})
    md, mm = [], []
    for m in models:
        ds = []
        for k, r in ok.items():
            if k[2] == m and k[3] == "FULL_MULTI_TURN":
                c0 = (k[0], k[1], k[2], "ONE_SHOT")
                if c0 in ok and ok[c0]["energy_pkg_j"] > 0:
                    ds.append((r["energy_pkg_j"] - ok[c0]["energy_pkg_j"])
                              / ok[c0]["energy_pkg_j"] * 100)
        md.append(med(ds) if ds else 0); mm.append(mean(ds) if ds else 0)
    x = range(len(models))
    ax.bar([i - 0.2 for i in x], mm, width=0.4, label="mean", color="#f59e0b")
    ax.bar([i + 0.2 for i in x], md, width=0.4, label="median", color="#6366f1")
    ax.set_xticks(list(x)); ax.set_xticklabels(models)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("Δ Energy C4 vs C0 (%)")
    ax.set_title("Multi-turn vs one-shot energy change by model")
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    save(fig, "delta_by_model.png")

    # 4. failure rate per condition
    fig, ax = plt.subplots(figsize=(8, 5))
    fr = []
    for c in CONDS:
        n = sum(1 for k in data if k[3] == c)
        b = sum(1 for k, r in data.items() if k[3] == c and r["status"] != "ok")
        fr.append(b / n * 100 if n else 0)
    ax.bar(range(len(CONDS)), fr, color="#dc2626", width=0.6)
    for i, v in enumerate(fr):
        ax.text(i, v + 0.5, f"{v:.1f}%", ha="center")
    ax.set_xticks(range(len(CONDS))); ax.set_xticklabels(SHORT)
    ax.set_ylabel("Programs that failed to run (%)")
    ax.set_title("Runnability failure rate by interaction condition")
    ax.grid(axis="y", alpha=0.3)
    save(fig, "failure_rate_by_condition.png")

    # 5. delta by category
    fig, ax = plt.subplots(figsize=(9, 5))
    cats = sorted({k[0] for k in ok})
    dcat = []
    for cat in cats:
        ds = []
        for k, r in ok.items():
            if k[0] == cat and k[3] == "FULL_MULTI_TURN":
                c0 = (k[0], k[1], k[2], "ONE_SHOT")
                if c0 in ok and ok[c0]["energy_pkg_j"] > 0:
                    ds.append((r["energy_pkg_j"] - ok[c0]["energy_pkg_j"])
                              / ok[c0]["energy_pkg_j"] * 100)
        dcat.append(med(ds) if ds else 0)
    ax.barh(range(len(cats)), dcat, color="#8b5cf6")
    ax.set_yticks(range(len(cats))); ax.set_yticklabels(cats)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("Median Δ Energy C4 vs C0 (%)")
    ax.set_title("Multi-turn energy change by task category")
    ax.grid(axis="x", alpha=0.3)
    save(fig, "delta_by_category.png")

    # 6. scatter one-shot vs multi-turn (same task×model)
    fig, ax = plt.subplots(figsize=(6, 6))
    xs, ys = [], []
    for k, r in ok.items():
        if k[3] == "FULL_MULTI_TURN":
            c0 = (k[0], k[1], k[2], "ONE_SHOT")
            if c0 in ok and ok[c0]["energy_pkg_j"] > 0:
                xs.append(ok[c0]["energy_pkg_j"]); ys.append(r["energy_pkg_j"])
    ax.scatter(xs, ys, alpha=0.6, color="#0ea5e9", edgecolor="k", linewidth=0.3)
    lim = [min(xs + ys) * 0.8, max(xs + ys) * 1.2]
    ax.plot(lim, lim, "k--", lw=1, label="equal energy")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("ONE_SHOT energy (J)"); ax.set_ylabel("FULL_MULTI_TURN energy (J)")
    ax.set_title("Paired energy: one-shot vs full multi-turn")
    ax.legend(); ax.grid(alpha=0.3, which="both")
    save(fig, "scatter_oneshot_vs_multiturn.png")

    # 7. runtime vs energy
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter([r["runtime_s"] for r in ok.values()],
               [r["energy_pkg_j"] for r in ok.values()],
               alpha=0.45, color="#14b8a6", edgecolor="k", linewidth=0.2)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Runtime (s)"); ax.set_ylabel("Energy (J)")
    ax.set_title("Energy vs runtime (all measured programs)")
    ax.grid(alpha=0.3, which="both")
    save(fig, "energy_vs_runtime.png")

    # 8. box plot energy by condition
    fig, ax = plt.subplots(figsize=(8, 5))
    boxes = [[r["energy_pkg_j"] for k, r in ok.items() if k[3] == c] for c in CONDS]
    ax.boxplot(boxes, tick_labels=CONDS, showfliers=False)
    ax.set_ylabel("Energy per run (J)")
    ax.set_title("Energy distribution by condition (outliers hidden)")
    ax.grid(axis="y", alpha=0.3)
    save(fig, "box_energy_by_condition.png")


if __name__ == "__main__":
    main()
