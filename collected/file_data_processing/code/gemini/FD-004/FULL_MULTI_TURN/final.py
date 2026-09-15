import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def read_and_aggregate_csv(file_path: str) -> Dict[Tuple[str, str], int]:
    """Reads a CSV file containing warehouse, product, and quantity data.

    Sums quantities for duplicate (warehouse, product) keys within the file,
    properly accounting for repeated keys and zero values.
    """
    records: Dict[Tuple[str, str], int] = defaultdict(int)

    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Error: Input file '{file_path}' does not exist.")

    with path.open(mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        required_columns = {"warehouse", "product", "quantity"}
        if not reader.fieldnames or not required_columns.issubset(set(reader.fieldnames)):
            missing = required_columns - set(reader.fieldnames or [])
            raise ValueError(
                f"File '{file_path}' is missing required columns: {missing}"
            )

        for line_num, row in enumerate(reader, start=2):
            wh = row["warehouse"].strip()
            prod = row["product"].strip()
            qty_str = row["quantity"].strip()

            if not wh or not prod:
                continue

            try:
                qty = int(qty_str)
            except ValueError:
                raise ValueError(
                    f"Invalid integer quantity '{qty_str}' at line {line_num} in '{file_path}'."
                )

            # Sums quantities for duplicate (warehouse, product) keys, including zeros
            records[(wh, prod)] += qty

    return dict(records)


def reconcile_inventory(
    old_data: Dict[Tuple[str, str], int], new_data: Dict[Tuple[str, str], int]
) -> List[Dict[str, str]]:
    """Compares pre-aggregated old and new snapshot data.

    Deterministic classification rules:
    - Key in new only: 'added' (delta = new_qty)
    - Key in old only: 'removed' (delta = -old_qty)
    - Key in both:
        - new_qty == old_qty (including 0 to 0): 'unchanged' (delta = 0)
        - new_qty != old_qty: 'changed' (delta = new_qty - old_qty)
    Output is deterministically sorted by warehouse, then product.
    """
    # Deterministic lexical sorting of compound keys
    all_keys = set(old_data.keys()).union(set(new_data.keys()))
    sorted_keys = sorted(all_keys, key=lambda x: (x[0], x[1]))

    reconciled_rows: List[Dict[str, str]] = []

    for wh, prod in sorted_keys:
        has_old = (wh, prod) in old_data
        has_new = (wh, prod) in new_data

        old_qty = old_data.get((wh, prod))
        new_qty = new_data.get((wh, prod))

        if not has_old and has_new:
            # Key exists exclusively in the new snapshot
            status = "added"
            diff = new_qty
            old_val_str = ""
            new_val_str = str(new_qty)

        elif has_old and not has_new:
            # Key exists exclusively in the old snapshot
            status = "removed"
            diff = -old_qty
            old_val_str = str(old_qty)
            new_val_str = ""

        elif has_old and has_new:
            # Key exists in both snapshots (e.g., 0 to 0, 5 to 5, or 5 to 10)
            diff = new_qty - old_qty
            old_val_str = str(old_qty)
            new_val_str = str(new_qty)

            if diff == 0:
                status = "unchanged"  # Handles 0 -> 0 as well as N -> N
            else:
                status = "changed"
        else:
            continue

        reconciled_rows.append(
            {
                "warehouse": wh,
                "product": prod,
                "old_quantity": old_val_str,
                "new_quantity": new_val_str,
                "difference": str(diff),
                "status": status,
            }
        )

    return reconciled_rows


def write_reconciliation_csv(
    output_path: str, rows: List[Dict[str, str]]
) -> None:
    """Writes the deterministic reconciled rows to a target CSV file."""
    fieldnames = [
        "warehouse",
        "product",
        "old_quantity",
        "new_quantity",
        "difference",
        "status",
    ]

    path = Path(output_path)
    with path.open(mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if len(sys.argv) < 4:
        print("Usage: python reconcile.py <old_csv> <new_csv> <output_csv>")
        sys.exit(1)

    old_file = sys.argv[1]
    new_file = sys.argv[2]
    out_file = sys.argv[3]

    try:
        old_records = read_and_aggregate_csv(old_file)
        new_records = read_and_aggregate_csv(new_file)

        reconciled_data = reconcile_inventory(old_records, new_records)
        write_reconciliation_csv(out_file, reconciled_data)

        print(f"Reconciliation successful. Report saved to '{out_file}'.")
    except Exception as e:
        print(f"Error executing reconciliation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()