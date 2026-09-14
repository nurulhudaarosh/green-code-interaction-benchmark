#!/usr/bin/env python3
"""Measurement progress tracker (idempotent, resume-safe).

Members finish at different times, and energy measurement is slow, so the
runner must never re-run programs that were already measured.

Source of truth:  results/measurement_ledger.jsonl  (append-only)
    One JSON line per measured program. A unit counts as DONE only if its
    latest entry has status "measured" (or "error") AND its code sha256
    still matches the file in collected/. If the code changed (member
    re-submitted), it becomes pending again automatically.

Unit = one FINAL program: category/task/model/interaction.

Usage:
    python3 scripts/measure_progress.py status
    python3 scripts/measure_progress.py queue [--category C] [--model M]
                                              [--limit N] [-o FILE.jsonl]
    python3 scripts/measure_progress.py record collected/SR/../code.py \
            --status measured --metrics results/raw/xxx.json [--note "..."]
"""

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COLLECTED = REPO / "collected"
LEDGER = REPO / "results" / "measurement_ledger.jsonl"

FINAL_BY_INTERACTION = {
    "ONE_SHOT": "code.py",
    "BUG_FIX": "final.py",
    "FEATURE_ADDITION": "final.py",
    "EDGE_CASE": "final.py",
    "FULL_MULTI_TURN": "final.py",
}


def sha256_file(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parse_unit(rel: Path):
    """collected/<cat>/code/<model>/<task>/<INT>/<file>.py -> parts."""
    parts = rel.parts
    try:
        i = parts.index("code")
    except ValueError:
        return None
    if len(parts) < i + 5:
        return None
    return {
        "category": parts[1],
        "model": parts[i + 1],
        "task_id": parts[i + 2],
        "interaction": parts[i + 3],
        "file": parts[-1],
    }


def scan_units(all_files: bool = False):
    units = []
    if not COLLECTED.is_dir():
        return units
    for py in sorted(COLLECTED.glob("*/code/*/*/*/*.py")):
        rel = py.relative_to(REPO)
        u = parse_unit(rel)
        if u is None:
            continue
        if not all_files and FINAL_BY_INTERACTION.get(u["interaction"], "final.py") != u["file"]:
            continue
        if py.stat().st_size == 0:
            continue
        u["rel"] = str(rel)
        u["sha256"] = sha256_file(py)
        units.append(u)
    return units


def load_ledger():
    done = {}
    if LEDGER.is_file():
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                print(f"WARNING: bad ledger line skipped: {line[:80]}", file=sys.stderr)
                continue
            done[(e["category"], e["task_id"], e["model"], e["interaction"], e["file"])] = e
    return done


def classify(units, ledger, redo_failed=False):
    pending, measured, stale = [], [], []
    for u in units:
        key = (u["category"], u["task_id"], u["model"], u["interaction"], u["file"])
        entry = ledger.get(key)
        if entry is None:
            pending.append(u)
        elif entry.get("sha256") != u["sha256"]:
            u["superseded_by"] = entry.get("ts")
            stale.append(u)
            pending.append(u)
        elif entry.get("status") in ("error", "skipped") and redo_failed:
            pending.append(u)
        else:
            measured.append((u, entry))
    return pending, measured, stale


def cmd_status(args):
    units = scan_units(args.all_files)
    ledger = load_ledger()
    pending, measured, stale = classify(units, ledger, args.redo_failed)
    by = defaultdict(lambda: {"total": 0, "done": 0, "error": 0})
    for u in units:
        k = (u["category"], u["model"])
        by[k]["total"] += 1
    for u, entry in measured:
        k = (u["category"], u["model"])
        by[k]["error"] += entry.get("status") == "error"
        by[k]["done"] += entry.get("status") != "pending-retry"
    cats = sorted({c for c, _ in by})
    models = sorted({m for _, m in by})
    print(f"Ledger: {LEDGER.relative_to(REPO)}  ({sum(1 for _ in open(LEDGER)) if LEDGER.is_file() else 0} entries)")
    print(f"{'category/model':<24}" + "".join(f"{m:>12}" for m in models) + f"{'TOTAL':>12}")
    for c in cats:
        row = f"{c:<24}"
        tot = dn = 0
        for m in models:
            v = by.get((c, m), {"total": 0, "done": 0, "error": 0})
            tot += v["total"]
            dn += v["done"]
            cell = f"{v['done']}/{v['total']}" if v["total"] else "-"
            row += f"{cell:>12}"
        row += f"{dn}/{tot}".rjust(12)
        print(row)
    print(f"\nmeasured: {len(measured)}  pending: {len(pending)}  "
          f"code-changed(re-measure): {len(stale)}")
    return 0


def cmd_queue(args):
    units = scan_units(args.all_files)
    pending, _, stale = classify(units, load_ledger(), args.redo_failed)
    if args.category:
        pending = [u for u in pending if u["category"] == args.category]
    if args.model:
        pending = [u for u in pending if u["model"] == args.model]
    if args.limit:
        pending = pending[: args.limit]
    out = Path(args.output) if args.output else None
    lines = [json.dumps(u, ensure_ascii=False) for u in pending]
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        print(f"{len(lines)} pending units -> {out}")
    else:
        print("\n".join(lines))
        print(f"\n{len(pending)} pending units", file=sys.stderr)
    return 0


def cmd_record(args):
    rel = Path(args.file).resolve().relative_to(REPO)
    u = parse_unit(rel)
    if u is None:
        print(f"ERROR: path must be under collected/<category>/code/...: {rel}", file=sys.stderr)
        return 1
    p = REPO / rel
    if not p.is_file():
        print(f"ERROR: file not found: {rel}", file=sys.stderr)
        return 1
    if args.status not in ("measured", "error", "skipped"):
        print("ERROR: --status must be 'measured', 'error' or 'skipped'", file=sys.stderr)
        return 1
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": args.status,
        "rel": str(rel),
        "sha256": sha256_file(p),
        "note": args.note or "",
        **u,
    }
    if args.metrics:
        entry["metrics"] = str(Path(args.metrics).resolve().relative_to(REPO))
    if args.if_changed:
        prev = load_ledger().get(
            (u["category"], u["task_id"], u["model"], u["interaction"], u["file"])
        )
        if prev and (prev.get("status"), prev.get("note"), prev.get("sha256")) == (
            entry["status"], entry["note"], entry["sha256"]
        ):
            print(f"unchanged: {u['category']} {u['task_id']} {u['model']} "
                  f"{u['interaction']} [{args.status}] — not appended")
            return 0
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"recorded: {u['category']} {u['task_id']} {u['model']} "
          f"{u['interaction']} [{args.status}]")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("status", help="progress table per category x model")
    sp.add_argument("--all-files", action="store_true", help="track every .py, not only final programs")
    sp.add_argument("--redo-failed", action="store_true", help="treat status=error as pending")
    sp.set_defaults(fn=cmd_status)

    qp = sub.add_parser("queue", help="list pending (not yet measured) programs")
    qp.add_argument("--category")
    qp.add_argument("--model")
    qp.add_argument("--limit", type=int)
    qp.add_argument("-o", "--output", help="write JSONL queue to file")
    qp.add_argument("--all-files", action="store_true")
    qp.add_argument("--redo-failed", action="store_true")
    qp.set_defaults(fn=cmd_queue)

    rp = sub.add_parser("record", help="append one ledger entry after measuring")
    rp.add_argument("file", help="path to the measured .py file (under collected/)")
    rp.add_argument("--status", required=True, choices=["measured", "error", "skipped"])
    rp.add_argument("--metrics", help="path to the metrics/result file for this run")
    rp.add_argument("--note")
    rp.add_argument("--if-changed", action="store_true",
                    help="skip append if latest entry has identical status/note/sha")
    rp.set_defaults(fn=cmd_record)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
