import csv
import sys
from collections import defaultdict

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py customers.csv transactions.csv")
        return

    customer_file = sys.argv[1]
    transaction_file = sys.argv[2]

    customers = {}

    with open(customer_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            customer_id = row["customer_id"]
            customers[customer_id] = row

    totals = defaultdict(lambda: {
        "transaction_count": 0,
        "total_amount": 0.0
    })

    with open(transaction_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            customer_id = row["customer_id"]

            if customer_id not in customers:
                continue

            try:
                amount = float(row["amount"])
            except (ValueError, TypeError):
                continue

            totals[customer_id]["transaction_count"] += 1
            totals[customer_id]["total_amount"] += amount

    if not customers:
        return

    fieldnames = list(next(iter(customers.values())).keys())
    fieldnames.extend(["transaction_count", "total_amount"])

    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()

    for customer_id in sorted(customers.keys()):
        row = dict(customers[customer_id])

        row["transaction_count"] = totals[customer_id]["transaction_count"]
        row["total_amount"] = totals[customer_id]["total_amount"]

        writer.writerow(row)

if __name__ == "__main__":
    main()