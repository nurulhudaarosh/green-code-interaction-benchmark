"""
Inventory Reconciliation Utility
=================================
A deterministic Python utility that compares two CSV snapshots (Old vs. New) of inventory.
It aggregates duplicate (Warehouse, Product_ID) records, explicitly distinguishes UNCHANGED records 
from ADDED, REMOVED, and CHANGED items, and computes the exact quantity delta (New_Qty - Old_Qty).
"""

import csv
import argparse
from pathlib import Path
from typing import Dict, Tuple, List, NamedTuple


class InventoryRecord(NamedTuple):
    warehouse: str
    product_id: str


def read_and_aggregate_csv(
    file_path: str,
    qty_col: str = "Quantity",
    warehouse_col: str = "Warehouse",
    product_col: str = "Product_ID",
) -> Dict[Tuple[str, str], float]:
    """
    Reads a CSV file and aggregates (sums) quantities for duplicate (Warehouse, Product_ID) keys.

    :param file_path: Path to input CSV file.
    :param qty_col: Column name for quantity.
    :param warehouse_col: Column name for warehouse identifier.
    :param product_col: Column name for product identifier.
    :return: Dictionary mapping (Warehouse, Product_ID) -> Total Quantity.
    """
    aggregated_data: Dict[Tuple[str, str], float] = {}
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        fieldnames = set(reader.fieldnames) if reader.fieldnames else set()
        missing = {warehouse_col, product_col, qty_col} - fieldnames
        if missing:
            raise ValueError(f"Missing required columns {missing} in file: {file_path}")

        for row_num, row in enumerate(reader, start=2):
            wh = row[warehouse_col].strip()
            prod = row[product_col].strip()
            qty_str = row[qty_col].strip()

            if not wh or not prod:
                continue  # Skip blank keys

            try:
                qty = float(qty_str) if qty_str else 0.0
            except ValueError:
                raise ValueError(
                    f"Invalid numeric quantity '{qty_str}' at row {row_num} in {file_path}"
                )

            key = (wh, prod)
            aggregated_data[key] = aggregated_data.get(key, 0.0) + qty

    return aggregated_data


def reconcile_inventory(
    old_csv: str,
    new_csv: str,
    output_csv: str,
    qty_col: str = "Quantity",
    warehouse_col: str = "Warehouse",
    product_col: str = "Product_ID",
) -> List[Dict[str, str]]:
    """
    Reconciles old and new inventory snapshots.

    Status Classifications:
    - ADDED: Key exists in New but not Old.
    - REMOVED: Key exists in Old but not New.
    - CHANGED: Key exists in both, but Old_Qty != New_Qty.
    - UNCHANGED: Key exists in both, and Old_Qty == New_Qty.

    Calculates: Delta = New_Qty - Old_Qty.
    Outputs: Deterministically sorted by Warehouse, then Product_ID.
    """
    old_data = read_and_aggregate_csv(old_csv, qty_col, warehouse_col, product_col)
    new_data = read_and_aggregate_csv(new_csv, qty_col, warehouse_col, product_col)

    # Deterministic sorting across all keys
    all_keys = sorted(set(old_data.keys()).union(set(new_data.keys())))
    reconciled_rows = []

    for wh, prod in all_keys:
        in_old = (wh, prod) in old_data
        in_new = (wh, prod) in new_data

        old_qty = old_data.get((wh, prod), 0.0)
        new_qty = new_data.get((wh, prod), 0.0)
        delta = new_qty - old_qty

        # Explicit classification logic distinguishing UNCHANGED from all other states
        if in_new and not in_old:
            status = "ADDED"
        elif in_old and not in_new:
            status = "REMOVED"
        elif old_qty != new_qty:
            status = "CHANGED"
        else:
            status = "UNCHANGED"

        def format_num(val: float) -> str:
            """Formats floats cleanly to strip trailing zeroes for integers."""
            return str(int(val)) if val.is_integer() else f"{val:.4f}".rstrip("0").rstrip(".")

        reconciled_rows.append(
            {
                "Warehouse": wh,
                "Product_ID": prod,
                "Status": status,
                "Old_Qty": format_num(old_qty) if in_old else "0",
                "New_Qty": format_num(new_qty) if in_new else "0",
                "Qty_Delta": format_num(delta),
            }
        )

    # Write output to CSV
    fieldnames = ["Warehouse", "Product_ID", "Status", "Old_Qty", "New_Qty", "Qty_Delta"]
    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reconciled_rows)

    print(f"Reconciliation successful. Report written to: {output_csv}")
    return reconciled_rows


def create_sample_data():
    """Generates sample CSV files showcasing UNCHANGED, ADDED, REMOVED, and CHANGED statuses."""
    old_content = """Warehouse,Product_ID,Quantity
WH-A,PROD-101,50
WH-A,PROD-101,20
WH-A,PROD-102,100
WH-B,PROD-201,15
WH-B,PROD-202,30
"""
    new_content = """Warehouse,Product_ID,Quantity
WH-A,PROD-101,70
WH-A,PROD-102,120
WH-A,PROD-103,45
WH-B,PROD-201,15
"""
    with open("inventory_old.csv", "w", encoding="utf-8") as f:
        f.write(old_content)

    with open("inventory_new.csv", "w", encoding="utf-8") as f:
        f.write(new_content)

    print("Created demo files: 'inventory_old.csv' and 'inventory_new.csv'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconcile two inventory CSV snapshots.")
    parser.add_argument("--old", default="inventory_old.csv", help="Path to old CSV snapshot")
    parser.add_argument("--new", default="inventory_new.csv", help="Path to new CSV snapshot")
    parser.add_argument("--out", default="inventory_reconciliation.csv", help="Output path")
    parser.add_argument("--demo", action="store_true", help="Generate demo data and execute")

    args = parser.parse_args()

    if args.demo or not (Path(args.old).exists() and Path(args.new).exists()):
        create_sample_data()

    reconcile_inventory(args.old, args.new, args.out)