#!/usr/bin/env python3
"""Empirical time-complexity probe.

Runs every final program (and each task's reference) through its per-task
harness at small/medium/large scales in an isolated subprocess, times each
scale, and fits a log-log growth exponent:

    log(cand_ms) = b * log(size_bytes) + a      ->  b == empirical slope

b ~ 0 -> constant, ~1 -> linear, ~2 -> quadratic, higher -> superlinear.

Reads:  results/energy_runs.jsonl (which programs to probe)
Writes: results/final/scaling.csv, results/final/scaling_summary.json
"""
import csv
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "results" / "energy_runs.jsonl"
FINAL = REPO / "results" / "final"
OUT_CSV = FINAL / "scaling.csv"
WORKER = REPO / "analysis" / "scale_worker.py"
SCALES = ["small", "medium", "large"]
PER_PROG_TIMEOUT = 90
WORKER_ENV = {"GCB_SCALE_REPS": "3", "GCB_SCALE_BUDGET_MS": "4000"}


def slope(points):
    """Least-squares slope of log(y) vs log(x). points = [(x, y)]."""
    pts = [(math.log(x), math.log(max(y, 1e-6)))
           for x, y in points if x and x > 0 and y is not None]
    if len(pts) < 2:
        return None
    mx = sum(p[0] for p in pts) / len(pts)
    my = sum(p[1] for p in pts) / len(pts)
    den = sum((p[0] - mx) ** 2 for p in pts)
    if den == 0:
        return None
    return sum((p[0] - mx) * (p[1] - my) for p in pts) / den


def run_worker(cat, tid, prog):
    cmd = [sys.executable, str(WORKER), cat, tid, prog, *SCALES]
    env = dict(os.environ)
    env.update(WORKER_ENV)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=PER_PROG_TIMEOUT, cwd=str(REPO), env=env)
    except subprocess.TimeoutExpired:
        return {"error": "worker_timeout"}
    line = (r.stdout or "").strip().splitlines()
    if not line:
        return {"error": f"no_output rc={r.returncode}"}
    try:
        return json.loads(line[-1])
    except json.JSONDecodeError:
        return {"error": "bad_json"}


def load_targets(categories):
    """(cat, task, model, cond, file) for measured programs."""
    rows = []
    seen = set()
    for l in LEDGER.read_text().splitlines():
        try:
            r = json.loads(l)
        except json.JSONDecodeError:
            continue
        if r.get("status") != "ok":
            continue
        cat = r["category"]
        if categories and cat not in categories:
            continue
        key = r["file"]
        if key in seen:
            continue
        seen.add(key)
        rows.append((cat, r["task_id"], r["model"], r["condition"],
                     "collected/" + r["file"]))
    return rows


def main():
    argv = sys.argv[1:]
    limit = None
    if "--limit" in argv:
        i = argv.index("--limit")
        limit = int(argv[i + 1])
        del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("-")]
    categories = set(args) if args else None
    targets = load_targets(categories)
    targets.sort(key=lambda t: (t[0], t[1], t[2], t[3]))
    if limit:
        targets = targets[:limit]
    have = {}
    if OUT_CSV.is_file():
        for row in csv.DictReader(OUT_CSV.open()):
            have[row["program"]] = row
    FINAL.mkdir(parents=True, exist_ok=True)
    refs_done = set()
    if OUT_CSV.is_file():
        for row in have.values():
            if row.get("ref_slope"):
                refs_done.add((row["category"], row["task_id"]))

    # reference slopes (once per task)
    ref_slopes = {}
    for cat, tid in sorted({(t[0], t[1]) for t in targets}):
        if (cat, tid) in refs_done:
            continue
        res = run_worker(cat, tid, "--reference")
        if "scales" in res:
            pts = [(v["size_bytes"], v["ref_ms"]) for v in res["scales"].values()
                   if v.get("ref_ok") and v.get("ref_ms") is not None]
            ref_slopes[(cat, tid)] = slope(pts)
        print(f"[ref] {cat}/{tid} slope={ref_slopes.get((cat, tid))}", flush=True)

    # fill missing ref slopes from existing rows
    for row in have.values():
        if row.get("ref_slope"):
            ref_slopes[(row["category"], row["task_id"])] = float(row["ref_slope"])

    cols = ["category", "task_id", "model", "condition", "program",
            "cand_slope", "cand_slope_ml", "ref_slope", "cand_ms_small",
            "cand_ms_medium", "cand_ms_large", "size_small", "size_medium",
            "size_large", "cand_ok_all", "error"]
    f = OUT_CSV.open("w", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for row in have.values():
        w.writerow({k: row.get(k, "") for k in cols})

    t_start = time.time()
    n = 0
    for i, (cat, tid, model, cond, prog) in enumerate(targets, 1):
        if prog in have and have[prog].get("cand_slope_ml") not in ("", None):
            continue
        res = run_worker(cat, tid, prog)
        rec = {"category": cat, "task_id": tid, "model": model,
               "condition": cond, "program": prog,
               "cand_slope": "", "cand_slope_ml": "", "ref_slope": "",
               "cand_ms_small": "", "cand_ms_medium": "", "cand_ms_large": "",
               "size_small": "", "size_medium": "", "size_large": "",
               "cand_ok_all": "", "error": ""}
        if "error" in res:
            rec["error"] = res["error"]
        else:
            pts, ml_pts = [], []
            ok_all = True
            for s in SCALES:
                v = res.get("scales", {}).get(s)
                if not v or "error" in v or not v.get("cand_ok"):
                    ok_all = False
                    continue
                rec[f"size_{s}"] = v["size_bytes"]
                rec[f"cand_ms_{s}"] = v["cand_ms"]
                if v["cand_ms"] is not None:
                    pts.append((v["size_bytes"], v["cand_ms"]))
                    if s in ("medium", "large"):
                        ml_pts.append((v["size_bytes"], v["cand_ms"]))
            rec["cand_ok_all"] = int(ok_all and len(pts) == 3)
            sl = slope(pts)
            rec["cand_slope"] = round(sl, 4) if sl is not None else ""
            ml = slope(ml_pts)
            rec["cand_slope_ml"] = round(ml, 4) if ml is not None else ""
        rsl = ref_slopes.get((cat, tid))
        rec["ref_slope"] = round(rsl, 4) if rsl is not None else ""
        w.writerow(rec)
        f.flush()
        have[prog] = rec
        n += 1
        if i % 25 == 0 or i == len(targets):
            el = time.time() - t_start
            print(f"[{i}/{len(targets)}] {n} done in {el:.0f}s "
                  f"({el/max(1,n):.2f}s/prog)", flush=True)
    f.close()

    build_summary(have, ref_slopes)
    print(f"[scaling] {len(have)} programs -> {OUT_CSV.relative_to(REPO)}")
    return 0


def build_summary(have, ref_slopes):
    import statistics as st
    rows = [r for r in have.values() if r.get("cand_slope_ml") not in ("", None)]
    summary = {"n_programs": len(have), "n_slopes": len(rows),
               "n_reference_tasks": len([v for v in ref_slopes.values()
                                         if v is not None])}
    if rows:
        summary["median_cand_slope_ml"] = round(
            st.median(float(r["cand_slope_ml"]) for r in rows), 4)
    by_cond = {}
    for c in ["ONE_SHOT", "BUG_FIX", "FEATURE_ADDITION", "EDGE_CASE",
              "FULL_MULTI_TURN"]:
        sub = [float(r["cand_slope_ml"]) for r in rows if r["condition"] == c]
        by_cond[c] = {"n": len(sub),
                      "median_slope": round(st.median(sub), 4) if sub else None,
                      "pct_superlinear": round(100 * sum(1 for s in sub if s >= 1.5) / len(sub), 1) if sub else None}
    summary["by_condition"] = by_cond
    by_model = {}
    for m in sorted({r["model"] for r in rows}):
        sub = [float(r["cand_slope_ml"]) for r in rows if r["model"] == m]
        by_model[m] = {"n": len(sub),
                       "median_slope": round(st.median(sub), 4) if sub else None}
    summary["by_model"] = by_model
    by_cat = {}
    for c in sorted({r["category"] for r in rows}):
        sub = [float(r["cand_slope_ml"]) for r in rows if r["category"] == c]
        by_cat[c] = {"n": len(sub),
                     "median_slope": round(st.median(sub), 4) if sub else None}
    summary["by_category"] = by_cat
    refs = [v for v in ref_slopes.values() if v is not None]
    if refs:
        summary["median_reference_slope"] = round(st.median(refs), 4)
    (FINAL / "scaling_summary.json").write_text(json.dumps(summary, indent=2),
                                                encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
