#!/usr/bin/env python3
"""
inventory_reconcile.py

Compare two inventory CSV snapshots (old vs new) and produce a deterministic
reconciliation report.

Expected input CSV columns (header required):
    warehouse,product,quantity

Duplicate rows for the same (warehouse, product) key within a single file
are summed together before comparison.

Each (warehouse, product) key across both files is classified as exactly
ONE of the following, in this priority order:
    added     - key present in new snapshot only
    removed   - key present in old snapshot only
    changed   - key present in both, but quantity differs
    unchanged - key present in both, and quantity is identical

Output CSV columns:
    warehouse,product,old_quantity,new_quantity,delta,status

Output rows are sorted deterministically first by status (added, removed,
changed, unchanged) and then by (warehouse, product), so that:
  - repeated runs on the same inputs always produce byte-identical output
  - unchanged records are visually/structurally separated from the records
    that actually represent a difference (added/removed/changed)

Use --skip-unchanged to omit unchanged records from the report entirely
(they are still counted in the printed summary).

Usage:
    python inventory_reconcile.py old.csv new.csv -o report.csv
    python inventory_reconcile.py old.csv new.csv -o report.csv --skip-unchanged
"""

import argparse
import csv
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation


# Fixed priority order used for both classification display and sorting.
STATUS_ORDER = {"added": 0, "removed": 1, "changed": 2, "unchanged": 3}


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
    parser.add_argument(
        "--skip-unchanged", action="store_true",
        help="Exclude unchanged records from the output CSV "
             "(they are still counted in the printed summary)"
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


def classify(old_qty, new_qty):
    """
    Classify a single key given its old/new quantities (either may be None
    if the key was absent from that snapshot). Returns one of:
    'added', 'removed', 'changed', 'unchanged'.
    """
    if old_qty is None and new_qty is not None:
        return "added"
    if old_qty is not None and new_qty is None:
        return "removed"
    if old_qty == new_qty:
        return "unchanged"
    return "changed"


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

        status = classify(old_qty, new_qty)

        old_val = old_qty if old_qty is not None else Decimal("0")
        new_val = new_qty if new_qty is not None else Decimal("0")
        delta = new_val - old_val  # added -> delta == new_val; removed -> delta == -old_val

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


def sort_key(row):
    """
    Deterministic sort: status priority first (added, removed, changed,
    unchanged), then warehouse, then product. This keeps records that
    represent an actual difference clearly separated from unchanged ones,
    while still being fully deterministic across runs.
    """
    return (STATUS_ORDER[row["status"]], row["warehouse"], row["product"])


def write_report(rows, output_path, skip_unchanged=False):
    """Write rows to CSV, sorted deterministically (status, warehouse, product)."""
    if skip_unchanged:
        rows_to_write = [r for r in rows if r["status"] != "unchanged"]
    else:
        rows_to_write = rows

    rows_sorted = sorted(rows_to_write, key=sort_key)

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


def print_summary(all_rows, written_rows, output_path, skip_unchanged):
    counts = defaultdict(int)
    for r in all_rows:
        counts[r["status"]] += 1

    print("Reconciliation summary (all keys):")
    for status in ("added", "removed", "changed", "unchanged"):
        print(f"  {status:9s}: {counts.get(status, 0)}")
    print(f"  {'total':9s}: {len(all_rows)}")

    if skip_unchanged:
        print(
            f"\nNote: unchanged records were excluded from '{output_path}' "
            f"(--skip-unchanged). {len(written_rows)} rows written."
        )
    else:
        print(f"\nWrote {len(written_rows)} rows to '{output_path}'.")


def main():
    args = parse_args()

    old_totals = load_snapshot(
        args.old_csv, args.warehouse_col, args.product_col, args.quantity_col
    )
    new_totals = load_snapshot(
        args.new_csv, args.warehouse_col, args.product_col, args.quantity_col
    )

    all_rows = reconcile(old_totals, new_totals)
    written_rows = write_report(all_rows, args.output, skip_unchanged=args.skip_unchanged)

    print_summary(all_rows, written_rows, args.output, args.skip_unchanged)


if __name__ == "__main__":
    main()