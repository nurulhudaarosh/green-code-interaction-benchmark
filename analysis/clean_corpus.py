#!/usr/bin/env python3
"""Clean-corpus definition for the Green Code Interaction Benchmark paper.

Exclusion rule (collection artifacts, NOT model faults — excluded from ALL
paper counts):
  - whole `search_retrieval` category (only 2 units collected, ~no code)
  - NOT_PYTHON      (prose submitted instead of code — extraction failure)
  - CLI_ARGS        (harness invoked program without its required CLI args)
  - OTHER           (usage-message exits — same invocation mismatch class)
  - SILENT_RC1      (schema mismatch / no-op exits)
  - MISSING_FILE    (program assumed dirs the harness never provided)
  - MISSING_DEP     (sandbox lacked the imported module)

Kept as genuine model failures: WRONG_OUTPUT + RUNTIME_BUG.

Outputs:
  results/final/excluded_units.json  (list of "cat|task|model|cond" keys)
  results/final/clean_corpus.json    (all headline numbers for the paper)
"""

import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FINAL = REPO / "results" / "final"

EXCLUDED_REASONS = {"NOT_PYTHON", "CLI_ARGS", "OTHER", "SILENT_RC1",
                    "MISSING_FILE", "MISSING_DEP"}
KEPT_REASONS = {"WRONG_OUTPUT", "RUNTIME_BUG"}
DROP_CATEGORIES = {"search_retrieval"}

CONDITIONS = ["ONE_SHOT", "BUG_FIX", "FEATURE_ADDITION", "EDGE_CASE",
              "FULL_MULTI_TURN"]


def key_of(r):
    return "|".join((r["category"], r["task_id"], r["model"], r["condition"]))


def main():
    metrics = list(csv.DictReader(open(FINAL / "code_metrics.csv")))
    fails = list(csv.DictReader(open(FINAL / "energy_failures.csv")))
    fail_by_key = {key_of(r): r for r in fails}

    excluded, kept_fail = [], []
    for r in metrics:
        k = key_of(r)
        if r["category"] in DROP_CATEGORIES:
            excluded.append(k)
            continue
        if r["status"] == "unmeasured":
            reason = (fail_by_key.get(k) or {}).get("reason", "UNKNOWN")
            if reason in EXCLUDED_REASONS:
                excluded.append(k)
            elif reason in KEPT_REASONS:
                kept_fail.append(k)
            else:
                raise SystemExit(f"unclassified failure reason: {reason} at {k}")

    excl_set = set(excluded)
    clean = [r for r in metrics if key_of(r) not in excl_set]
    measured = [r for r in clean if r["status"] == "ok"]

    def med(xs):
        xs = sorted(xs)
        return statistics.median(xs) if xs else None

    e = [float(r["energy_pkg_j"]) for r in measured if r["energy_pkg_j"]]
    rt = [float(r["runtime_s"]) for r in measured if r["runtime_s"]]
    total_j = sum(e)

    by_cond = defaultdict(list)
    for r in measured:
        if r["energy_pkg_j"]:
            by_cond[r["condition"]].append(float(r["energy_pkg_j"]))
    cond_med = {c: med(by_cond[c]) for c in CONDITIONS}

    clean_tot = Counter(r["condition"] for r in clean)
    kept_by_cond = Counter()
    for k in kept_fail:
        kept_by_cond[k.split("|")[3]] += 1
    fail_rate = {c: kept_by_cond[c] / clean_tot[c] for c in CONDITIONS}

    by_cat = Counter(r["category"] for r in clean)
    parse_ok = sum(1 for r in clean if r["parse_ok"] == "1")
    # carbon @ 480 gCO2eq/kWh from the same clean measured set:
    # mg = J / 3.6e6 (kWh) * 480 (g/kWh) * 1000 (mg/g) = J * 480/3600
    total_mg_co2 = total_j * 480 / 3600.0

    out = {
        "rule": {
            "dropped_categories": sorted(DROP_CATEGORIES),
            "excluded_reasons": sorted(EXCLUDED_REASONS),
            "kept_failure_reasons": sorted(KEPT_REASONS),
        },
        "n_raw_finals": len(metrics),
        "n_excluded_collection_artifacts": len([k for k in excluded
                                                if not k.startswith("search_retrieval")]),
        "n_dropped_search_retrieval": sum(1 for k in excluded
                                          if k.startswith("search_retrieval")),
        "n_clean": len(clean),
        "n_measured": len(measured),
        "n_genuine_failures": len(kept_fail),
        "genuine_failure_share": len(kept_fail) / len(clean),
        "parse_ok_clean": parse_ok,
        "measured_share": len(measured) / len(clean),
        "median_energy_J": med(e),
        "total_energy_J": total_j,
        "total_carbon_mg_co2eq_480": total_mg_co2,
        "median_runtime_s": med(rt),
        "cond_median_energy_J": cond_med,
        "cond_totals": dict(clean_tot),
        "cond_genuine_failures": dict(kept_by_cond),
        "cond_genuine_fail_rate": fail_rate,
        "by_category_clean": dict(by_cat),
        "models": sorted({r["model"] for r in clean}),
        "conditions": CONDITIONS,
    }
    (FINAL / "excluded_units.json").write_text(json.dumps(sorted(excluded), indent=1))
    (FINAL / "clean_corpus.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1)[:2000])


if __name__ == "__main__":
    main()
