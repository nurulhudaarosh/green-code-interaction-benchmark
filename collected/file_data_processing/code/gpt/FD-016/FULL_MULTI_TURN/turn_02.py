import csv
import sys
from collections import defaultdict

def main():
    if len(sys.argv) != 3:
        print("Usage: python utility.py customers.csv transactions.csv")
        return

    customer_file = sys.argv[1]
    transaction_file = sys.argv[2]

    customers = {}

    with open(customer_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            customer_id = row["customer_id"]
            customers[customer_id] = row

    transaction_count = defaultdict(int)
    transaction_amount = defaultdict(float)

    with open(transaction_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            customer_id = row["customer_id"]

            # Ignore transactions for unknown customers
            if customer_id not in customers:
                continue

            transaction_count[customer_id] += 1
            transaction_amount[customer_id] += float(row["amount"])

    if not customers:
        return

    first_customer = next(iter(customers))
    fieldnames = list(customers[first_customer].keys())
    fieldnames += ["transaction_count", "transaction_amount"]

    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()

    # Only customer master records create output rows
    for customer_id in sorted(customers):
        result = customers[customer_id].copy()
        result["transaction_count"] = transaction_count[customer_id]
        result["transaction_amount"] = transaction_amount[customer_id]
        writer.writerow(result)


if __name__ == "__main__":
    main()