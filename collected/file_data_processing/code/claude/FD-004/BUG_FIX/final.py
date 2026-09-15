#!/usr/bin/env python3
"""
Inventory Reconciliation Utility
---------------------------------
Compares an "old" and a "new" CSV inventory snapshot and produces a
deterministic, sorted report classifying each (warehouse, product) key as:

    ADDED     - present only in new
    REMOVED   - present only in old
    CHANGED   - present in both, quantity differs
    UNCHANGED - present in both, quantity identical

Duplicate rows for the same (warehouse, product) key within a single
snapshot are summed before comparison. Keys are matched case-insensitively
and with surrounding whitespace stripped, so "WH1"/"wh1"/" WH1 " are
treated as the same warehouse.

Expected CSV columns (header row required):
    warehouse,product,quantity

Usage:
    python reconcile_inventory.py old.csv new.csv -o report.csv
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path


def load_snapshot(path):
    """
    Load a CSV file into a dict of {(warehouse, product): total_quantity}.
    Duplicate keys within the file are summed. Keys are normalized
    (stripped + lowercased) for matching, but the output preserves the
    first-seen original casing for display.
    """
    totals = defaultdict(int)
    display_keys = {}  # normalized_key -> (original_warehouse, original_product)

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        required = {"warehouse", "product", "quantity"}
        if reader.fieldnames is None or not required.issubset(
            {c.strip().lower() for c in reader.fieldnames}
        ):
            raise ValueError(
                f"{path}: CSV must have headers: warehouse, product, quantity"
            )

        header_map = {c.strip().lower(): c for c in reader.fieldnames}

        for line_num, row in enumerate(reader, start=2):
            warehouse_raw = (row.get(header_map["warehouse"]) or "").strip()
            product_raw = (row.get(header_map["product"]) or "").strip()
            qty_raw = (row.get(header_map["quantity"]) or "").strip()

            if not warehouse_raw or not product_raw:
                raise ValueError(
                    f"{path}:{line_num}: missing warehouse or product value"
                )

            try:
                qty = int(qty_raw)
            except ValueError:
                try:
                    qty = int(float(qty_raw))
                except ValueError:
                    raise ValueError(
                        f"{path}:{line_num}: invalid quantity '{qty_raw}'"
                    )

            norm_key = (warehouse_raw.lower(), product_raw.lower())
            totals[norm_key] += qty

            # Keep the first-seen original casing for display purposes
            display_keys.setdefault(norm_key, (warehouse_raw, product_raw))

    # Rebuild dict using original (display) casing as the final key
    return {display_keys[k]: v for k, v in totals.items()}


def reconcile(old_totals, new_totals):
    """
    Compare two {(warehouse, product): qty} dicts and return a sorted
    list of result rows. Matching between old and new is done on the
    normalized (lowercased, stripped) key so casing differences between
    snapshots don't produce false ADDED/REMOVED pairs.
    """
    def norm(k):
        return (k[0].lower(), k[1].lower())

    old_by_norm = {norm(k): (k, v) for k, v in old_totals.items()}
    new_by_norm = {norm(k): (k, v) for k, v in new_totals.items()}

    all_norm_keys = set(old_by_norm) | set(new_by_norm)
    results = []

    for nk in all_norm_keys:
        old_entry = old_by_norm.get(nk)
        new_entry = new_by_norm.get(nk)

        old_key, old_qty = old_entry if old_entry else (None, None)
        new_key, new_qty = new_entry if new_entry else (None, None)

        # Prefer the new snapshot's casing for display if present
        display_key = new_key if new_key is not None else old_key
        warehouse, product = display_key

        if old_qty is None and new_qty is not None:
            status = "ADDED"
            delta = new_qty
        elif old_qty is not None and new_qty is None:
            status = "REMOVED"
            delta = -old_qty
        else:
            delta = new_qty - old_qty
            status = "CHANGED" if delta != 0 else "UNCHANGED"

        results.append({
            "warehouse": warehouse,
            "product": product,
            "old_quantity": old_qty if old_qty is not None else "",
            "new_quantity": new_qty if new_qty is not None else "",
            "delta": delta,
            "status": status,
        })

    # Deterministic sort: warehouse, then product, then status
    results.sort(key=lambda r: (r["warehouse"], r["product"], r["status"]))
    return results


def write_report(results, out_path):
    fieldnames = [
        "warehouse", "product", "old_quantity",
        "new_quantity", "delta", "status",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def print_summary(results):
    counts = defaultdict(int)
    for r in results:
        counts[r["status"]] += 1
    print("Reconciliation summary:", file=sys.stderr)
    for status in ("ADDED", "REMOVED", "CHANGED", "UNCHANGED"):
        print(f"  {status:<10} {counts.get(status, 0)}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Reconcile two inventory CSV snapshots.")
    parser.add_argument("old_csv", type=Path, help="Path to old snapshot CSV")
    parser.add_argument("new_csv", type=Path, help="Path to new snapshot CSV")
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("reconciliation_report.csv"),
        help="Path for output report CSV (default: reconciliation_report.csv)"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress summary output"
    )
    args = parser.parse_args()

    try:
        old_totals = load_snapshot(args.old_csv)
        new_totals = load_snapshot(args.new_csv)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    results = reconcile(old_totals, new_totals)
    write_report(results, args.output)

    if not args.quiet:
        print_summary(results)
        print(f"Report written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()