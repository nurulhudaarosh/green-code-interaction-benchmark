import csv
from collections import defaultdict
from pathlib import Path


def load_snapshot(path):
    """Load a CSV snapshot and aggregate quantities for duplicate keys."""
    totals = defaultdict(int)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"warehouse", "product", "quantity"}
        if not required.issubset(reader.fieldnames or []):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(f"Missing required columns in {path}: {sorted(missing)}")
        for row in reader:
            key = (row["warehouse"].strip(), row["product"].strip())
            qty_raw = row["quantity"].strip()
            qty = int(qty_raw) if qty_raw else 0
            totals[key] += qty
    return dict(totals)


def reconcile(old_path, new_path, out_path):
    old = load_snapshot(old_path)
    new = load_snapshot(new_path)

    all_keys = sorted(set(old) | set(new))

    rows = []
    summary = {"added": 0, "removed": 0, "changed": 0, "unchanged": 0}

    for key in all_keys:
        warehouse, product = key
        old_qty = old.get(key)
        new_qty = new.get(key)
        delta = (new_qty if new_qty is not None else 0) - (old_qty if old_qty is not None else 0)

        if old_qty is None:
            status = "added"
        elif new_qty is None:
            status = "removed"
        elif old_qty != new_qty:
            status = "changed"
        else:
            status = "unchanged"

        summary[status] += 1

        rows.append({
            "warehouse": warehouse,
            "product": product,
            "old_quantity": "" if old_qty is None else old_qty,
            "new_quantity": "" if new_qty is None else new_qty,
            "delta": delta,
            "status": status,
        })

    fieldnames = ["warehouse", "product", "old_quantity", "new_quantity", "delta", "status"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return summary


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python reconcile.py <old.csv> <new.csv> <output.csv>")
        sys.exit(1)

    old_csv, new_csv, output_csv = sys.argv[1:4]
    if not Path(old_csv).exists():
        print(f"Old snapshot not found: {old_csv}")
        sys.exit(1)
    if not Path(new_csv).exists():
        print(f"New snapshot not found: {new_csv}")
        sys.exit(1)

    summary = reconcile(old_csv, new_csv, output_csv)
    print(f"Wrote {output_csv}")
    print(f"Summary: {summary}")