import csv
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
import argparse


def process_events(input_file, output_file):
    with open(input_file, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # 1. Remove duplicate customer/timestamp records.
    # If the same (customer_id, timestamp) appears multiple times,
    # the LAST occurrence in the input file is retained.
    retained_by_key = {}

    for row in rows:
        key = (row["customer_id"], row["timestamp"])
        retained_by_key[key] = row

    # 2. From the de-duplicated records, select the
    # chronologically latest record for each customer.
    latest_by_customer = {}

    for row in retained_by_key.values():
        customer_id = row["customer_id"]

        if customer_id not in latest_by_customer:
            latest_by_customer[customer_id] = row
            continue

        current_timestamp = datetime.fromisoformat(row["timestamp"])
        existing_timestamp = datetime.fromisoformat(
            latest_by_customer[customer_id]["timestamp"]
        )

        if current_timestamp > existing_timestamp:
            latest_by_customer[customer_id] = row

    # 3. Calculate status totals ONLY from the retained
    # latest record for each customer.
    status_summary = defaultdict(
        lambda: {
            "count": 0,
            "total_amount": Decimal("0")
        }
    )

    for row in latest_by_customer.values():
        status = row["status"]
        amount = Decimal(row["amount"])

        status_summary[status]["count"] += 1
        status_summary[status]["total_amount"] += amount

    # 4. Write deterministic output sorted by customer_id.
    fieldnames = ["customer_id", "timestamp", "status", "amount"]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for customer_id in sorted(latest_by_customer):
            writer.writerow(latest_by_customer[customer_id])

    # 5. Print deterministic status summary.
    print("status,count,total_amount")

    for status in sorted(status_summary):
        data = status_summary[status]

        print(
            f"{status},"
            f"{data['count']},"
            f"{data['total_amount']:.2f}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Process customer event CSV files offline."
    )

    parser.add_argument("input", help="Input CSV file")
    parser.add_argument("output", help="Output CSV file")

    args = parser.parse_args()

    process_events(args.input, args.output)


if __name__ == "__main__":
    main()