#!/usr/bin/env python3
"""Track units whose code failed, into files you can fix manually.

Outputs:
  results/final/problems.csv  (machine-readable)
  results/final/problems.md   (human-readable, per problem with rerun cmd)
"""

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LEDGER = ROOT / "results" / "measurement_ledger.jsonl"
FINAL = ROOT / "results" / "final"
RAW = ROOT / "results" / "raw"

KIND_HINTS = {
    "candidate_import": "Syntax/import error in the submitted file (often stray module-level demo code). Fix the file; only its sha changes and only that file is re-measured.",
    "incorrect_result": "Output does not match the reference at one or more scales.",
    "timeout": "Execution exceeded the per-run timeout.",
    "no_driver_output": "run() produced no output.",
    "task_not_in_dataset": "Task id not found in dataset/tasks.json.",
}


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    args = ap.parse_args()

    problems = []
    if LEDGER.exists():
        latest = {}
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            key = (e.get("category", ""), e.get("task_id", e.get("task", "")),
                   e.get("model", ""), e.get("interaction", ""), e.get("file", ""))
            latest[key] = e
        for e in latest.values():
            if e.get("status") not in ("error", "skipped"):
                continue
            raw = load_json(e.get("metrics") or e.get("path") or "") or {}
            reason = (e.get("reason") or raw.get("reason") or raw.get("error")
                      or e.get("note") or e.get("status"))
            if isinstance(reason, str) and reason.startswith("candidate_import"):
                reason = "candidate_import"
            problems.append({
                "category": e.get("category", ""),
                "task": e.get("task_id", e.get("task", "")),
                "model": e.get("model", ""),
                "interaction": e.get("interaction", ""),
                "file": e.get("rel", ""),
                "member_file": e.get("file", ""),
                "kind": "harness_missing" if e.get("status") == "skipped" and reason == "no_harness" else reason,
                "hint": KIND_HINTS.get(reason, "See the raw result JSON for details."),
                "raw_path": e.get("metrics", ""),
            })

    # ingest-level problems (syntax_errors/empty are relative paths, e.g.
    # "code/gpt/SR-001/ONE_SHOT/code.py")
    def unit_of(rel):
        parts = str(rel).split("/")
        return {
            "task": parts[2] if len(parts) > 2 else "?",
            "model": parts[1] if len(parts) > 1 else "?",
            "interaction": parts[3] if len(parts) > 3 else "?",
        }

    for rep in sorted((ROOT / "collected").glob("*/ingest_report.json")):
        data = load_json(rep) or {}
        for cat in ("syntax_errors",):
            for item in data.get(cat, []) or []:
                u = unit_of(item)
                problems.append({
                    "category": rep.parent.name,
                    "task": u["task"],
                    "model": u["model"],
                    "interaction": u["interaction"],
                    "file": str(ROOT / "collected" / rep.parent.name / item),
                    "member_file": "",
                    "kind": f"ingest_{cat}",
                    "hint": "File does not compile (check the reported line). Fix the file and rerun.",
                    "raw_path": "",
                })
        for item in data.get("empty", []) or []:
            u = unit_of(item)
            problems.append({
                "category": rep.parent.name,
                "task": u["task"],
                "model": u["model"],
                "interaction": u["interaction"],
                "file": str(ROOT / "collected" / rep.parent.name / item),
                "member_file": "",
                "kind": "ingest_empty",
                "hint": "File is empty in the member's submission.",
                "raw_path": "",
            })

    FINAL.mkdir(parents=True, exist_ok=True)
    csv_path = FINAL / "problems.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["category", "task", "model", "interaction",
                                          "file", "member_file", "kind", "hint", "raw_path"])
        w.writeheader()
        for p in problems:
            w.writerow(p)

    md = ["# Problem code tracker", ""]
    md.append(f"Total problem entries: **{len(problems)}**")
    md.append("")
    md.append("Fix the member file in `collected/<category>/code/...` and rerun the pipeline:")
    md.append("only that unit's sha changes, so only it is re-measured.")
    md.append("")
    for p in problems:
        md.append(f"## {p['task']} / {p['model']} / {p['interaction']}  ({p['category']})")
        md.append(f"- kind: **{p['kind']}**")
        if p["file"]:
            md.append(f"- file: `{p['file']}`")
        if p["raw_path"]:
            md.append(f"- detail: `{p['raw_path']}`")
        md.append(f"- hint: {p['hint']}")
        md.append(f"- rerun: `python3 scripts/run_pipeline.py`")
        md.append("")
    md_path = FINAL / "problems.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"[problems] {len(problems)} entries -> {csv_path}")
    print(f"[problems] {len(problems)} entries -> {md_path}")


if __name__ == "__main__":
    main()
