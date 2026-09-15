import csv
import argparse
import sys
from collections import defaultdict


FIELDNAMES = ["warehouse", "product", "old_qty", "new_qty", "delta", "status"]


def load_snapshot(path):
    aggregated = defaultdict(int)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"warehouse", "product", "quantity"}
        if not required.issubset(reader.fieldnames or []):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(
                f"File {path!r} is missing required columns: {sorted(missing)}"
            )
        for lineno, row in enumerate(reader, start=2):
            warehouse = (row.get("warehouse") or "").strip()
            product = (row.get("product") or "").strip()
            qty_raw = (row.get("quantity") or "").strip()
            if not warehouse or not product:
                raise ValueError(f"Empty warehouse/product at {path}:{lineno}")
            try:
                qty = int(qty_raw)
            except ValueError:
                raise ValueError(f"Invalid quantity {qty_raw!r} at {path}:{lineno}")
            aggregated[(warehouse, product)] += qty
    return aggregated


def reconcile(old, new):
    all_keys = sorted(set(old) | set(new))
    for key in all_keys:
        warehouse, product = key
        in_old = key in old
        in_new = key in new
        old_qty = old.get(key, 0)
        new_qty = new.get(key, 0)

        if in_old and not in_new:
            status = "removed"
            delta = -old_qty
        elif in_new and not in_old:
            status = "added"
            delta = new_qty
        elif old_qty == new_qty:
            status = "unchanged"
            delta = 0
        else:
            status = "changed"
            delta = new_qty - old_qty

        yield {
            "warehouse": warehouse,
            "product": product,
            "old_qty": old_qty,
            "new_qty": new_qty,
            "delta": delta,
            "status": status,
        }


def write_report(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize(rows):
    counts = defaultdict(int)
    for row in rows:
        counts[row["status"]] += 1
    return counts


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Reconcile two inventory CSV snapshots."
    )
    parser.add_argument("old_csv", help="Path to the old inventory CSV")
    parser.add_argument("new_csv", help="Path to the new inventory CSV")
    parser.add_argument(
        "-o", "--output",
        default="reconciliation.csv",
        help="Output CSV path (default: reconciliation.csv)",
    )
    args = parser.parse_args(argv)

    try:
        old = load_snapshot(args.old_csv)
        new = load_snapshot(args.new_csv)
    except (OSError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    rows = list(reconcile(old, new))
    write_report(rows, args.output)

    counts = summarize(rows)
    print(f"Wrote {len(rows)} rows to {args.output}")
    print(
        "Summary — "
        f"added: {counts['added']}, "
        f"removed: {counts['removed']}, "
        f"changed: {counts['changed']}, "
        f"unchanged: {counts['unchanged']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())