import csv
import sys
from collections import defaultdict


def read_snapshot(filename):
    inventory = defaultdict(int)

    with open(filename, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            key = (row["warehouse"], row["product"])
            inventory[key] += int(row["quantity"])

    return inventory


def reconcile(old_file, new_file, output_file):
    old_inventory = read_snapshot(old_file)
    new_inventory = read_snapshot(new_file)

    all_keys = sorted(set(old_inventory) | set(new_inventory))

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "warehouse",
            "product",
            "old_quantity",
            "new_quantity",
            "delta",
            "status"
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for warehouse, product in all_keys:
            key = (warehouse, product)

            old_exists = key in old_inventory
            new_exists = key in new_inventory

            old_quantity = old_inventory.get(key, 0)
            new_quantity = new_inventory.get(key, 0)

            delta = new_quantity - old_quantity

            if old_exists and new_exists:
                if old_quantity == new_quantity:
                    status = "unchanged"
                else:
                    status = "changed"
            elif new_exists:
                status = "added"
            else:
                status = "removed"

            writer.writerow({
                "warehouse": warehouse,
                "product": product,
                "old_quantity": old_quantity,
                "new_quantity": new_quantity,
                "delta": delta,
                "status": status
            })


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python inventory_reconciliation.py old.csv new.csv output.csv")
        sys.exit(1)

    reconcile(sys.argv[1], sys.argv[2], sys.argv[3])