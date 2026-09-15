#!/usr/bin/env python3
"""
Inventory Reconciliation Utility
---------------------------------
Compares an "old" and a "new" CSV inventory snapshot and produces a
deterministic, sorted reconciliation report.

Expected input CSV columns (case-insensitive, order doesn't matter):
    warehouse, product, quantity

Duplicate (warehouse, product) rows within a single snapshot are summed
together before comparison.

Each (warehouse, product) key across both snapshots is classified as:
    - added      : present in new, absent in old
    - removed    : present in old, absent in new
    - changed    : present in both, quantity differs
    - unchanged  : present in both, quantity identical

Output CSV columns:
    warehouse, product, old_qty, new_qty, diff, status

Usage:
    python reconcile_inventory.py old.csv new.csv output.csv
"""

import csv
import sys
import argparse
from collections import defaultdict
from typing import Dict, Tuple, Iterable

Key = Tuple[str, str]


def load_snapshot(path: str) -> Dict[Key, float]:
    """
    Load a CSV snapshot into a dict keyed by (warehouse, product),
    summing quantities for duplicate keys.
    """
    totals: Dict[Key, float] = defaultdict(float)

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError(f"{path}: file has no header row")

        # Normalize headers -> case-insensitive lookup
        normalized = {name.strip().lower(): name for name in reader.fieldnames}
        required = ["warehouse", "product", "quantity"]
        missing = [col for col in required if col not in normalized]
        if missing:
            raise ValueError(
                f"{path}: missing required column(s): {', '.join(missing)}"
            )

        wh_col = normalized["warehouse"]
        prod_col = normalized["product"]
        qty_col = normalized["quantity"]

        for line_num, row in enumerate(reader, start=2):
            warehouse = (row.get(wh_col) or "").strip()
            product = (row.get(prod_col) or "").strip()
            raw_qty = (row.get(qty_col) or "").strip()

            if not warehouse or not product:
                # Skip malformed rows silently but don't crash the run
                continue

            try:
                qty = float(raw_qty) if raw_qty != "" else 0.0
            except ValueError:
                raise ValueError(
                    f"{path}, line {line_num}: invalid quantity '{raw_qty}' "
                    f"for warehouse='{warehouse}', product='{product}'"
                )

            totals[(warehouse, product)] += qty

    return totals


def format_qty(value: float) -> str:
    """Render quantities as ints when whole, otherwise trimmed floats."""
    if value == int(value):
        return str(int(value))
    return f"{value:g}"


def reconcile(old: Dict[Key, float], new: Dict[Key, float]) -> Iterable[dict]:
    """
    Compare old vs new snapshots and yield one record per key,
    sorted deterministically by (warehouse, product).
    """
    all_keys = set(old.keys()) | set(new.keys())

    for warehouse, product in sorted(all_keys):
        key = (warehouse, product)
        in_old = key in old
        in_new = key in new

        old_qty = old.get(key, 0.0)
        new_qty = new.get(key, 0.0)
        diff = new_qty - old_qty

        if in_new and not in_old:
            status = "added"
        elif in_old and not in_new:
            status = "removed"
        elif diff != 0:
            status = "changed"
        else:
            status = "unchanged"

        yield {
            "warehouse": warehouse,
            "product": product,
            "old_qty": format_qty(old_qty) if in_old else "",
            "new_qty": format_qty(new_qty) if in_new else "",
            "diff": format_qty(diff),
            "status": status,
        }


def write_report(records: Iterable[dict], path: str) -> None:
    fieldnames = ["warehouse", "product", "old_qty", "new_qty", "diff", "status"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def summarize(records: Iterable[dict]) -> Dict[str, int]:
    counts = defaultdict(int)
    for r in records:
        counts[r["status"]] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconcile old vs new inventory CSV snapshots."
    )
    parser.add_argument("old_csv", help="Path to the old snapshot CSV")
    parser.add_argument("new_csv", help="Path to the new snapshot CSV")
    parser.add_argument("output_csv", help="Path to write the reconciliation report")
    args = parser.parse_args()

    try:
        old_totals = load_snapshot(args.old_csv)
        new_totals = load_snapshot(args.new_csv)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    records = list(reconcile(old_totals, new_totals))
    write_report(records, args.output_csv)

    counts = summarize(records)
    print(f"Reconciliation complete -> {args.output_csv}")
    print(f"  total keys : {len(records)}")
    for status in ["added", "removed", "changed", "unchanged"]:
        print(f"  {status:<9}: {counts.get(status, 0)}")


if __name__ == "__main__":
    main()