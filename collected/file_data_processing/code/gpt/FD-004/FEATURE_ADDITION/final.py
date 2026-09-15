import csv
import sys


def read_snapshot(filename):
    data = {}

    with open(filename, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            key = (row["warehouse"], row["product"])
            quantity = int(row["quantity"])
            data[key] = data.get(key, 0) + quantity

    return data


def reconcile(old_file, new_file, output_file):
    old_data = read_snapshot(old_file)
    new_data = read_snapshot(new_file)

    all_keys = set(old_data) | set(new_data)
    results = []

    for key in all_keys:
        warehouse, product = key
        old_quantity = old_data.get(key, 0)
        new_quantity = new_data.get(key, 0)
        delta = new_quantity - old_quantity

        if key not in old_data:
            status = "added"
        elif key not in new_data:
            status = "removed"
        elif old_quantity == new_quantity:
            status = "unchanged"
        else:
            status = "changed"

        results.append([
            warehouse,
            product,
            old_quantity,
            new_quantity,
            delta,
            status
        ])

    results.sort(key=lambda row: (row[0], row[1]))

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "warehouse",
            "product",
            "old_quantity",
            "new_quantity",
            "quantity_delta",
            "status"
        ])

        writer.writerows(results)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python inventory_reconciliation.py old.csv new.csv output.csv")
        sys.exit(1)

    reconcile(sys.argv[1], sys.argv[2], sys.argv[3])