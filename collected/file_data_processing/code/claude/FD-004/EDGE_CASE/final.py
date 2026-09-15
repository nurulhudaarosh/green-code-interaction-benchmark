#!/usr/bin/env python3
"""
Inventory Reconciliation Utility
---------------------------------
Compares two CSV snapshots (old vs new) of warehouse/product inventory,
sums duplicate (warehouse, product) records, classifies each key as
added / removed / changed / unchanged, computes the quantity delta
(new - old), and writes a deterministic, sorted CSV report.

Zero-quantity handling:
    - A key present in both snapshots with quantity 0 in each is
      classified "unchanged" (delta == 0), same as any other equal pair.
    - A key present only in the new snapshot (even with quantity 0) is
      still "added" — its *presence* changed, not just its quantity.
    - A key present only in the old snapshot (even with quantity 0) is
      still "removed" for the same reason.
    - Duplicate rows for the same (warehouse, product) are summed before
      classification, so summation order never affects the result.

Expected input CSV columns (header required):
    warehouse,product,quantity

Usage:
    python reconcile_inventory.py old.csv new.csv -o report.csv
"""

import argparse
import csv
import sys
from collections import defaultdict
from typing import Dict, Tuple, List, Optional

Key = Tuple[str, str]  # (warehouse, product)


def load_and_sum(path: str) -> Dict[Key, int]:
    """Read a CSV file and sum quantities for duplicate (warehouse, product) keys.

    Summation via += is commutative/associative, so the result is identical
    regardless of row order in the file -> deterministic.
    """
    totals: Dict[Key, int] = defaultdict(int)

    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            required = {"warehouse", "product", "quantity"}
            if reader.fieldnames is None or not required.issubset(
                {c.strip().lower() for c in reader.fieldnames}
            ):
                raise ValueError(
                    f"{path}: missing required columns {required}, "
                    f"found {reader.fieldnames}"
                )

            col_map = {c.strip().lower(): c for c in reader.fieldnames}

            for row_num, row in enumerate(reader, start=2):
                warehouse = row[col_map["warehouse"]].strip()
                product = row[col_map["product"]].strip()
                qty_raw = row[col_map["quantity"]].strip()

                if not warehouse or not product:
                    raise ValueError(
                        f"{path}, row {row_num}: warehouse/product cannot be empty"
                    )

                try:
                    qty = int(float(qty_raw))
                except ValueError:
                    raise ValueError(
                        f"{path}, row {row_num}: invalid quantity '{qty_raw}'"
                    )

                totals[(warehouse, product)] += qty  # zero is a perfectly valid running total

    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    return totals


def classify(old_qty: Optional[int], new_qty: Optional[int]) -> str:
    """Pure classification function — same inputs always give same output.

    old_qty / new_qty are None when the key is absent from that snapshot,
    and an int (possibly 0) when present.
    """
    if old_qty is None and new_qty is not None:
        return "added"
    if old_qty is not None and new_qty is None:
        return "removed"
    # Both present (including both == 0)
    return "unchanged" if old_qty == new_qty else "changed"


def reconcile(
    old_totals: Dict[Key, int], new_totals: Dict[Key, int]
) -> List[dict]:
    """Classify every key across both snapshots and compute deltas."""
    all_keys = set(old_totals) | set(new_totals)
    results = []

    for warehouse, product in all_keys:
        key = (warehouse, product)
        old_qty = old_totals.get(key)  # None if absent, int (maybe 0) if present
        new_qty = new_totals.get(key)  # None if absent, int (maybe 0) if present

        status = classify(old_qty, new_qty)

        # Display values: absent keys show as 0 in the report, but classification
        # above was already decided using the None/presence distinction, not
        # these display values.
        old_display = old_qty if old_qty is not None else 0
        new_display = new_qty if new_qty is not None else 0
        delta = new_display - old_display

        results.append(
            {
                "warehouse": warehouse,
                "product": product,
                "old_quantity": old_display,
                "new_quantity": new_display,
                "delta": delta,
                "status": status,
            }
        )

    # Deterministic ordering: sort by (warehouse, product) regardless of
    # dict/set iteration order, which Python does not guarantee across runs
    # for sets built from arbitrary insertion order.
    results.sort(key=lambda r: (r["warehouse"], r["product"]))
    return results


def write_report(results: List[dict], out_path: str) -> None:
    """Write the reconciliation results to a sorted, deterministic CSV."""
    fieldnames = ["warehouse", "product", "old_quantity", "new_quantity", "delta", "status"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)


def print_summary(results: List[dict]) -> None:
    """Print a quick summary of classification counts to stdout."""
    counts = defaultdict(int)
    for r in results:
        counts[r["status"]] += 1

    print("Reconciliation Summary")
    print("-----------------------")
    for status in ("added", "removed", "changed", "unchanged"):
        print(f"  {status:10}: {counts[status]}")
    print(f"  {'total keys':10}: {len(results)}")


def main():
    parser = argparse.ArgumentParser(
        description="Reconcile two inventory CSV snapshots (old vs new)."
    )
    parser.add_argument("old_csv", help="Path to the OLD snapshot CSV file")
    parser.add_argument("new_csv", help="Path to the NEW snapshot CSV file")
    parser.add_argument(
        "-o", "--output", default="reconciliation_report.csv",
        help="Output CSV path (default: reconciliation_report.csv)"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Suppress the summary printout"
    )
    args = parser.parse_args()

    old_totals = load_and_sum(args.old_csv)
    new_totals = load_and_sum(args.new_csv)

    results = reconcile(old_totals, new_totals)
    write_report(results, args.output)

    if not args.quiet:
        print_summary(results)
        print(f"\nReport written to: {args.output}")


if __name__ == "__main__":
    main()