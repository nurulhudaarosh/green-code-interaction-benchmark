#!/usr/bin/env python3
"""
inventory_reconcile.py

Compare two inventory CSV snapshots (old vs new) and produce a deterministic
reconciliation report.

Expected input CSV columns (header required):
    warehouse,product,quantity

Duplicate rows for the same (warehouse, product) key within a single file
are summed together before comparison.

Each (warehouse, product) key across both files is classified as:
    added     - present in new, not in old
    removed   - present in old, not in new
    changed   - present in both, quantity differs
    unchanged - present in both, quantity identical

Output CSV columns:
    warehouse,product,old_quantity,new_quantity,delta,status

Output rows are sorted deterministically by (warehouse, product) so that
repeated runs on the same inputs always produce byte-identical output.

Usage:
    python inventory_reconcile.py old.csv new.csv -o report.csv
"""

import argparse
import csv
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation


def parse_args():
    parser = argparse.ArgumentParser(
        description="Reconcile two inventory CSV snapshots (old vs new)."
    )
    parser.add_argument("old_csv", help="Path to the OLD snapshot CSV file")
    parser.add_argument("new_csv", help="Path to the NEW snapshot CSV file")
    parser.add_argument(
        "-o", "--output",
        default="reconciliation_report.csv",
        help="Path to write the output report CSV (default: %(default)s)"
    )
    parser.add_argument(
        "--warehouse-col", default="warehouse",
        help="Column name for warehouse (default: %(default)s)"
    )
    parser.add_argument(
        "--product-col", default="product",
        help="Column name for product (default: %(default)s)"
    )
    parser.add_argument(
        "--quantity-col", default="quantity",
        help="Column name for quantity (default: %(default)s)"
    )
    return parser.parse_args()


def load_snapshot(path, warehouse_col, product_col, quantity_col):
    """
    Load a CSV snapshot into a dict keyed by (warehouse, product),
    summing quantities for duplicate keys.

    Returns:
        dict[(str, str), Decimal]
    """
    totals = defaultdict(lambda: Decimal("0"))

    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            missing = [
                col for col in (warehouse_col, product_col, quantity_col)
                if col not in (reader.fieldnames or [])
            ]
            if missing:
                sys.exit(
                    f"Error: '{path}' is missing required column(s): "
                    f"{', '.join(missing)}. Found columns: {reader.fieldnames}"
                )

            for line_num, row in enumerate(reader, start=2):
                warehouse = (row.get(warehouse_col) or "").strip()
                product = (row.get(product_col) or "").strip()
                raw_qty = (row.get(quantity_col) or "").strip()

                if not warehouse or not product:
                    print(
                        f"Warning: skipping row {line_num} in '{path}' "
                        f"(missing warehouse/product): {row}",
                        file=sys.stderr
                    )
                    continue

                try:
                    qty = Decimal(raw_qty) if raw_qty != "" else Decimal("0")
                except InvalidOperation:
                    print(
                        f"Warning: skipping row {line_num} in '{path}' "
                        f"(invalid quantity '{raw_qty}'): {row}",
                        file=sys.stderr
                    )
                    continue

                totals[(warehouse, product)] += qty

    except FileNotFoundError:
        sys.exit(f"Error: file not found: '{path}'")
    except OSError as e:
        sys.exit(f"Error reading '{path}': {e}")

    return dict(totals)


def reconcile(old_totals, new_totals):
    """
    Compare old vs new totals and classify every key.

    Returns:
        list[dict] of report rows, unsorted.
    """
    all_keys = set(old_totals) | set(new_totals)
    rows = []

    for warehouse, product in all_keys:
        old_qty = old_totals.get((warehouse, product))
        new_qty = new_totals.get((warehouse, product))

        if old_qty is None and new_qty is not None:
            status = "added"
        elif old_qty is not None and new_qty is None:
            status = "removed"
        elif old_qty == new_qty:
            status = "unchanged"
        else:
            status = "changed"

        old_val = old_qty if old_qty is not None else Decimal("0")
        new_val = new_qty if new_qty is not None else Decimal("0")
        delta = new_val - old_val

        rows.append({
            "warehouse": warehouse,
            "product": product,
            "old_quantity": format_decimal(old_qty),
            "new_quantity": format_decimal(new_qty),
            "delta": format_decimal(delta),
            "status": status,
        })

    return rows


def format_decimal(value):
    """Return empty string for None (key absent from that file), else plain number string."""
    if value is None:
        return ""
    normalized = value.normalize()
    # Avoid scientific notation (e.g. 1E+2) from Decimal.normalize()
    if normalized == normalized.to_integral_value():
        return str(normalized.quantize(Decimal(1)))
    return str(normalized)


def write_report(rows, output_path):
    """Write rows to CSV, sorted deterministically by (warehouse, product)."""
    rows_sorted = sorted(rows, key=lambda r: (r["warehouse"], r["product"]))

    fieldnames = [
        "warehouse", "product", "old_quantity", "new_quantity", "delta", "status"
    ]

    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_sorted)
    except OSError as e:
        sys.exit(f"Error writing '{output_path}': {e}")

    return rows_sorted


def print_summary(rows_sorted):
    counts = defaultdict(int)
    for r in rows_sorted:
        counts[r["status"]] += 1

    print("Reconciliation summary:")
    for status in ("added", "removed", "changed", "unchanged"):
        print(f"  {status:9s}: {counts.get(status, 0)}")
    print(f"  {'total':9s}: {len(rows_sorted)}")


def main():
    args = parse_args()

    old_totals = load_snapshot(
        args.old_csv, args.warehouse_col, args.product_col, args.quantity_col
    )
    new_totals = load_snapshot(
        args.new_csv, args.warehouse_col, args.product_col, args.quantity_col
    )

    rows = reconcile(old_totals, new_totals)
    rows_sorted = write_report(rows, args.output)

    print(f"Wrote {len(rows_sorted)} rows to '{args.output}'")
    print_summary(rows_sorted)


if __name__ == "__main__":
    main()