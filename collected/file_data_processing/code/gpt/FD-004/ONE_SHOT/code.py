import csv
import sys
from collections import defaultdict


def read_snapshot(filename):
    data = defaultdict(int)

    with open(filename, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            warehouse = row["warehouse"].strip()
            product = row["product"].strip()
            quantity = int(row["quantity"])

            data[(warehouse, product)] += quantity

    return data


def reconcile(old_file, new_file, output_file):
    old_data = read_snapshot(old_file)
    new_data = read_snapshot(new_file)

    all_keys = set(old_data) | set(new_data)
    results = []

    for warehouse, product in all_keys:
        old_quantity = old_data.get((warehouse, product), 0)
        new_quantity = new_data.get((warehouse, product), 0)
        difference = new_quantity - old_quantity

        if (warehouse, product) not in old_data:
            status = "added"
        elif (warehouse, product) not in new_data:
            status = "removed"
        elif old_quantity != new_quantity:
            status = "changed"
        else:
            status = "unchanged"

        results.append({
            "warehouse": warehouse,
            "product": product,
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
            "difference": difference,
            "status": status
        })

    results.sort(key=lambda row: (row["warehouse"], row["product"]))

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "warehouse",
            "product",
            "old_quantity",
            "new_quantity",
            "difference",
            "status"
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python inventory_reconciliation.py old.csv new.csv output.csv")
        sys.exit(1)

    old_file = sys.argv[1]
    new_file = sys.argv[2]
    output_file = sys.argv[3]

    reconcile(old_file, new_file, output_file)