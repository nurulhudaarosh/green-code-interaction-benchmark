import csv
from collections import defaultdict
from typing import Dict, List, Set, Tuple


def read_and_aggregate(filepath: str) -> Dict[Tuple[str, str], int]:
    """Reads a CSV file and aggregates quantities for repeating (Warehouse, SKU) keys.

    Assumes CSV has headers: 'Warehouse', 'SKU', 'Quantity'
    """
    inventory = defaultdict(int)
    with open(filepath, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = (row["Warehouse"].strip(), row["SKU"].strip())
            qty = int(row["Quantity"].strip())
            inventory[key] += qty
    return dict(inventory)


def reconcile_inventories(
    old_file: str, new_file: str, output_file: str
) -> None:
    """Reconciles old vs. new inventory snapshots with deterministic sorting.

    Handles zero-quantity values and repeated keys gracefully:
    - ADDED: Key exists ONLY in the new snapshot file.
    - REMOVED: Key exists ONLY in the old snapshot file.
    - CHANGED: Key exists in BOTH files, but aggregated quantities differ.
    - UNCHANGED: Key exists in BOTH files with matching quantities (including 0 -> 0).
    """
    old_inv = read_and_aggregate(old_file)
    new_inv = read_and_aggregate(new_file)

    old_keys: Set[Tuple[str, str]] = set(old_inv.keys())
    new_keys: Set[Tuple[str, str]] = set(new_inv.keys())

    # Union of all unique (Warehouse, SKU) keys across both snapshots
    all_keys = old_keys.union(new_keys)

    reconciled_rows: List[Dict[str, object]] = []

    for key in all_keys:
        wh, sku = key
        in_old = key in old_keys
        in_new = key in new_keys

        old_qty = old_inv.get(key, 0)
        new_qty = new_inv.get(key, 0)
        diff_qty = new_qty - old_qty

        # Classify status based on file presence, not just nonzero quantities
        if in_new and not in_old:
            status = "ADDED"
        elif in_old and not in_new:
            status = "REMOVED"
        elif diff_qty != 0:
            status = "CHANGED"
        else:
            # Present in both files and diff_qty == 0 (handles 0 -> 0)
            status = "UNCHANGED"

        reconciled_rows.append(
            {
                "Warehouse": wh,
                "SKU": sku,
                "Status": status,
                "Old_Qty": old_qty,
                "New_Qty": new_qty,
                "Diff_Qty": diff_qty,
            }
        )

    # Deterministic output sorting: Warehouse (Ascending), then SKU (Ascending)
    reconciled_rows.sort(key=lambda row: (str(row["Warehouse"]), str(row["SKU"])))

    # Write output to CSV
    fieldnames = [
        "Warehouse",
        "SKU",
        "Status",
        "Old_Qty",
        "New_Qty",
        "Diff_Qty",
    ]
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reconciled_rows)


if __name__ == "__main__":
    reconcile_inventories(
        old_file="old_snapshot.csv",
        new_file="new_snapshot.csv",
        output_file="reconciliation_report.csv",
    )