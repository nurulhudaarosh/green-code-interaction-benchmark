#!/usr/bin/env python3
"""
Inventory Reconciliation Utility
---------------------------------
Compares an "old" and a "new" CSV inventory snapshot and produces a
deterministic, sorted reconciliation report.

Expected input CSV columns (case-insensitive, order doesn't matter):
    warehouse, product, quantity

Duplicate (warehouse, product) rows within a single snapshot are summed
together before comparison. Keys are matched case-insensitively and with
surrounding whitespace stripped (e.g. "W1"/"w1 " are the same warehouse),
so quantities merge correctly even if casing/spacing is inconsistent.
The first-seen casing is kept for display in the output.

Quantities are parsed and summed using Decimal (not float) so that
equality checks are exact. This matters because repeated keys can sum
to exactly zero (e.g. +5 and -5 on the same key), and float arithmetic
can leave tiny non-zero residuals (e.g. 0.1 + 0.2 - 0.3 != 0.0) that
would misclassify a true zero-to-zero record as "changed" -- and could
do so inconsistently depending on row order. Decimal avoids this, so
classification is fully deterministic and reproducible.

Each (warehouse, product) key across both snapshots is classified as:
    - added      : present in new, absent in old
    - removed    : present in old, absent in new
    - changed    : present in both, quantity differs (including 0 -> nonzero)
    - unchanged  : present in both, quantity identical (including 0 -> 0)

Output CSV columns:
    warehouse, product, old_qty, new_qty, diff, status

Usage:
    python reconcile_inventory.py old.csv new.csv output.csv
"""

import csv
import sys
import argparse
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Dict, Tuple, Iterable

Key = Tuple[str, str]


def load_snapshot(path: str) -> Dict[Key, Decimal]:
    """
    Load a CSV snapshot into a dict keyed by (warehouse, product),
    summing quantities (as Decimal) for duplicate keys.

    Keys are matched case-insensitively / whitespace-trimmed so that
    e.g. "W1"/"w1" and "Widget"/"widget " are treated as the same key
    and their quantities are summed together. The original casing from
    the first occurrence of each key is used for display in the output.

    A key whose summed quantity is exactly zero is still retained (not
    dropped) -- it's a legitimate zero-quantity record, not an absence.
    """
    totals: Dict[Key, Decimal] = defaultdict(lambda: Decimal("0"))
    display: Dict[Key, Key] = {}  # normalized key -> original-cased (warehouse, product)

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError(f"{path}: file has no header row")

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
                continue

            try:
                qty = Decimal(raw_qty) if raw_qty != "" else Decimal("0")
            except InvalidOperation:
                raise ValueError(
                    f"{path}, line {line_num}: invalid quantity '{raw_qty}' "
                    f"for warehouse='{warehouse}', product='{product}'"
                )

            norm_key = (warehouse.lower(), product.lower())
            display.setdefault(norm_key, (warehouse, product))
            totals[norm_key] += qty

    return {display[norm_key]: qty for norm_key, qty in totals.items()}


def format_qty(value: Decimal) -> str:
    """Render quantities without unnecessary trailing zeros (Decimal-safe)."""
    normalized = value.normalize()
    if normalized == 0:
        return "0"
    sign, digits, exponent = normalized.as_tuple()
    if exponent >= 0:
        return str(int(normalized))
    return format(normalized, "f")


def reconcile(old: Dict[Key, Decimal], new: Dict[Key, Decimal]) -> Iterable[dict]:
    """
    Compare old vs new snapshots and yield one record per key,
    sorted deterministically by (warehouse, product).

    Every record includes:
      - old_qty / new_qty : the summed Decimal quantities (blank if key absent)
      - diff              : new_qty - old_qty (the quantity delta), exact
      - status            : added | removed | changed | unchanged
    """
    def norm(k: Key) -> Key:
        return (k[0].lower(), k[1].lower())

    old_by_norm = {norm(k): (k, v) for k, v in old.items()}
    new_by_norm = {norm(k): (k, v) for k, v in new.items()}

    all_norm_keys = set(old_by_norm.keys()) | set(new_by_norm.keys())

    def sort_key(nk: Key) -> Key:
        display = old_by_norm.get(nk, new_by_norm.get(nk))[0]
        return display

    for nk in sorted(all_norm_keys, key=sort_key):
        in_old = nk in old_by_norm
        in_new = nk in new_by_norm

        old_display, old_qty = old_by_norm.get(nk, (None, Decimal("0")))
        new_display, new_qty = new_by_norm.get(nk, (None, Decimal("0")))
        display_key = old_display if old_display is not None else new_display
        warehouse, product = display_key

        diff = new_qty - old_qty

        if in_new and not in_old:
            status = "added"
        elif in_old and not in_new:
            status = "removed"
        elif diff == 0:
            status = "unchanged"
        else:
            status = "changed"

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