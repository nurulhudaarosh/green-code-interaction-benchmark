#!/usr/bin/env python3
"""Recover public tests from the ORIGINAL corrupt TL dataset by evaluating
the Python expressions the member's generator wrote instead of JSON.

The tests section in the source file contains entries like
    {"type": "large", "input": [f'...' for i in range(5)], "expected": ...}
which are valid Python but not JSON. This script extracts each expression
with bracket-aware scanning and eval()s it in a restricted namespace, then
writes the recovered tests into the frozen local dataset.

Usage:
    python3 scripts/recover_tl_tests.py --dry-run
    python3 scripts/recover_tl_tests.py
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "inbox" / "text_log_processing" / "dataset" / "dataset.json"
DEST = REPO / "dataset" / "text_log_processing" / "dataset.json"

SAFE = {"range": range, "len": len, "str": str, "int": int, "float": float,
        "list": list, "dict": dict, "set": set, "sorted": sorted,
        "round": round, "min": min, "max": max}


def extract_expr(text, start):
    """Extract a balanced expression starting at `start` (value position).
    Returns (end_index, expr_str)."""
    i, n = start, len(text)
    depth = 0
    quote = None
    while i < n:
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
        elif c in "[({":
            depth += 1
        elif c in "])}":
            if depth == 0:
                return i, text[start:i]
            depth -= 1
        elif c == "," and depth == 0:
            return i, text[start:i]
        i += 1
    return n, text[start:n]


def py_eval(expr):
    return eval(expr.strip(), {"__builtins__": {}}, SAFE)  # noqa: S307


def jsonable(v):
    """Make an evaluated Python value JSON-serializable (sets->sorted lists,
    tuples->lists, other objects->repr)."""
    if isinstance(v, (set, frozenset)):
        return sorted(jsonable(x) for x in v)
    if isinstance(v, (list, tuple)):
        return [jsonable(x) for x in v]
    if isinstance(v, dict):
        return {str(k): jsonable(x) for k, x in v.items()}
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return repr(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    raw = SRC.read_text(encoding="utf-8")
    frozen = json.loads(DEST.read_text(encoding="utf-8"))
    tasks = frozen["tasks"]

    # walk the raw text per task
    recovered = 0
    for task in tasks:
        tid = task["task_id"]
        i = raw.find(f'"task_id": "{tid}"')
        if i < 0:
            print(f"  {tid}: not found in source")
            continue
        j = raw.find('"task_id"', i + 10)
        block = raw[i:j if j > 0 else len(raw)]
        t0 = block.find('"tests": {')
        t1 = block.find('"reference_solution"')
        if t0 < 0 or t1 < 0:
            print(f"  {tid}: no tests block")
            continue
        section = block[t0:t1]
        tests = []
        pos = 0
        while True:
            m = re.search(r'"input"\s*:\s*', section[pos:])
            if not m:
                break
            vs = pos + m.end()
            ve, expr = extract_expr(section, vs)
            entry = {"type": "recovered"}
            try:
                entry["input"] = jsonable(py_eval(expr))
            except Exception as e:  # noqa: BLE001
                entry["input"] = None
                entry["error"] = f"{type(e).__name__}: {e}"[:120]
            # expected (optional)
            m2 = re.search(r'"expected"\s*:\s*', section[ve:ve + 4000])
            if m2:
                es = ve + m2.start() + m2.end()
                ee, eexpr = extract_expr(section, es)
                try:
                    entry["expected"] = jsonable(py_eval(eexpr))
                except Exception:  # noqa: BLE001
                    entry["expected"] = None
            tests.append(entry)
            pos = ve + 1
        ok_tests = [t for t in tests if t.get("input") is not None]
        if ok_tests:
            if not args.dry_run:
                task["tests"] = {"public_tests": tests}
            print(f"  {tid}: recovered {len(ok_tests)}/{len(tests)} test(s); "
                  f"input sample: {json.dumps(ok_tests[0]['input'], default=str)[:90]}")
            recovered += 1
        else:
            print(f"  {tid}: no recoverable tests ({len(tests)} tried)")

    print(f"\nrecovered tests for {recovered}/{len(tasks)} tasks")
    if not args.dry_run and recovered:
        DEST.write_text(json.dumps(frozen, indent=2, ensure_ascii=False),
                        encoding="utf-8")
        print(f"updated {DEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
