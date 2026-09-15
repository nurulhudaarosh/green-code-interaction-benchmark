import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def read_and_aggregate_csv(file_path: str) -> Dict[Tuple[str, str], int]:
    """Reads a CSV file and aggregates duplicate (warehouse, product) keys

    by summing their quantities within the snapshot before returning the mapping.
    """
    records: Dict[Tuple[str, str], int] = defaultdict(int)

    with open(file_path, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        required_columns = {"warehouse", "product", "quantity"}
        if not required_columns.issubset(set(reader.fieldnames or [])):
            missing = required_columns - set(reader.fieldnames or [])
            raise ValueError(
                f"Missing required columns {missing} in {file_path}"
            )

        for row_num, row in enumerate(reader, start=2):
            try:
                warehouse = row["warehouse"].strip()
                product = row["product"].strip()
                quantity = int(row["quantity"].strip())
            except ValueError as err:
                raise ValueError(
                    f"Invalid integer in 'quantity' at row {row_num} of {file_path}"
                ) from err

            # Sum repeated keys within the same snapshot
            records[(warehouse, product)] += quantity

    return records


def reconcile_inventories(
    old_csv_path: str, new_csv_path: str, output_csv_path: str
) -> None:
    """Reconciles old and new CSV inventory snapshots after aggregating key duplicates.

    Outputs a deterministically sorted CSV report.
    """
    # 1. Sum quantities for duplicate keys within each snapshot independently
    old_inventory = read_and_aggregate_csv(old_csv_path)
    new_inventory = read_and_aggregate_csv(new_csv_path)

    # 2. Extract union of all unique (warehouse, product) keys and sort deterministically
    all_keys = set(old_inventory.keys()) | set(new_inventory.keys())
    sorted_keys = sorted(all_keys, key=lambda x: (x[0], x[1]))

    report_rows: List[Dict[str, str | int]] = []

    # 3. Classify each unique key based on aggregated values
    for warehouse, product in sorted_keys:
        key = (warehouse, product)
        in_old = key in old_inventory
        in_new = key in new_inventory

        old_qty = old_inventory[key] if in_old else 0
        new_qty = new_inventory[key] if in_new else 0
        diff_qty = new_qty - old_qty

        if in_new and not in_old:
            status = "ADDED"
        elif in_old and not in_new:
            status = "REMOVED"
        elif old_qty != new_qty:
            status = "CHANGED"
        else:
            status = "UNCHANGED"

        report_rows.append(
            {
                "warehouse": warehouse,
                "product": product,
                "old_quantity": old_qty,
                "new_quantity": new_qty,
                "diff_quantity": diff_qty,
                "status": status,
            }
        )

    # 4. Ensure destination path exists and write output report
    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "warehouse",
        "product",
        "old_quantity",
        "new_quantity",
        "diff_quantity",
        "status",
    ]
    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        old_file = f"{temp_dir}/old_snapshot.csv"
        new_file = f"{temp_dir}/new_snapshot.csv"
        reconciled_file = f"{temp_dir}/reconciled_report.csv"

        # Old snapshot with duplicate keys:
        # (WH-A, Widget-1) -> 10 + 5 = 15
        # (WH-A, Widget-2) -> 20 + 30 = 50
        with open(old_file, "w", newline="", encoding="utf-8") as f:
            f.write(
                "warehouse,product,quantity\n"
                "WH-A,Widget-1,10\n"
                "WH-A,Widget-1,5\n"
                "WH-A,Widget-2,20\n"
                "WH-A,Widget-2,30\n"
            )

        # New snapshot with duplicate keys:
        # (WH-A, Widget-1) -> 8 + 7 = 15 (UNCHANGED vs 15)
        # (WH-A, Widget-2) -> 10 + 10 = 20 (CHANGED vs 50 -> diff: -30)
        # (WH-B, Widget-3) -> 5 + 5 = 10 (ADDED -> diff: +10)
        with open(new_file, "w", newline="", encoding="utf-8") as f:
            f.write(
                "warehouse,product,quantity\n"
                "WH-A,Widget-1,8\n"
                "WH-A,Widget-1,7\n"
                "WH-A,Widget-2,10\n"
                "WH-A,Widget-2,10\n"
                "WH-B,Widget-3,5\n"
                "WH-B,Widget-3,5\n"
            )

        reconcile_inventories(old_file, new_file, reconciled_file)

        print("Reconciliation Output:\n")
        with open(reconciled_file, "r", encoding="utf-8") as f:
            print(f.read())