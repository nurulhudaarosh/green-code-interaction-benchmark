import csv
import sys


def read_inventory(filename):
    inventory = {}

    with open(filename, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            warehouse = row["warehouse"]
            product = row["product"]
            quantity = int(row["quantity"])

            key = (warehouse, product)
            inventory[key] = inventory.get(key, 0) + quantity

    return inventory


def reconcile(old_file, new_file, output_file):
    old_inventory = read_inventory(old_file)
    new_inventory = read_inventory(new_file)

    all_keys = set(old_inventory) | set(new_inventory)

    results = []

    for warehouse, product in all_keys:
        old_quantity = old_inventory.get((warehouse, product), 0)
        new_quantity = new_inventory.get((warehouse, product), 0)
        delta = new_quantity - old_quantity

        if (warehouse, product) not in old_inventory:
            status = "added"
        elif (warehouse, product) not in new_inventory:
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
            "quantity_delta": delta,
            "status": status
        })

    results.sort(key=lambda row: (row["warehouse"], row["product"]))

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "warehouse",
            "product",
            "old_quantity",
            "new_quantity",
            "quantity_delta",
            "status"
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python inventory_reconciliation.py old.csv new.csv output.csv")
        sys.exit(1)

    reconcile(sys.argv[1], sys.argv[2], sys.argv[3])