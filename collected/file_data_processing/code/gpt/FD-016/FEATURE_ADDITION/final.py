import csv
import sys
from collections import defaultdict

def main():
    customer_file = sys.argv[1]
    transaction_file = sys.argv[2]

    customers = {}

    with open(customer_file, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            customer_id = row["customer_id"]
            customers[customer_id] = row

    transaction_count = defaultdict(int)
    transaction_amount = defaultdict(float)

    with open(transaction_file, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            customer_id = row["customer_id"]

            if customer_id not in customers:
                continue

            try:
                amount = float(row["amount"])
            except (ValueError, TypeError):
                continue

            transaction_count[customer_id] += 1
            transaction_amount[customer_id] += amount

    customer_fields = list(next(iter(customers.values())).keys())
    fieldnames = customer_fields + ["transaction_count", "transaction_amount"]

    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()

    for customer_id in sorted(customers):
        output = customers[customer_id].copy()
        output["transaction_count"] = transaction_count.get(customer_id, 0)
        output["transaction_amount"] = transaction_amount.get(customer_id, 0)

        writer.writerow(output)

if __name__ == "__main__":
    main()