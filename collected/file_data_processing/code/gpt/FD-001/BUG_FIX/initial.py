import csv
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
import argparse


def process_events(input_file, output_file):
    # Read CSV
    with open(input_file, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Remove duplicate customer_id + timestamp records.
    # Keeping the last occurrence means later rows overwrite earlier rows.
    deduplicated = {}

    for row in rows:
        key = (row["customer_id"], row["timestamp"])
        deduplicated[key] = row

    # Select chronologically latest record for each customer
    latest = {}

    for row in deduplicated.values():
        customer_id = row["customer_id"]

        if customer_id not in latest:
            latest[customer_id] = row
        else:
            current_time = datetime.fromisoformat(row["timestamp"])
            previous_time = datetime.fromisoformat(
                latest[customer_id]["timestamp"]
            )

            if current_time > previous_time:
                latest[customer_id] = row

    # Calculate count and total amount by status
    summary = defaultdict(lambda: {"count": 0, "total_amount": Decimal("0")})

    for row in latest.values():
        status = row["status"]
        amount = Decimal(row["amount"])

        summary[status]["count"] += 1
        summary[status]["total_amount"] += amount

    # Write deterministic output sorted by customer_id
    fieldnames = ["customer_id", "timestamp", "status", "amount"]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for customer_id in sorted(latest):
            writer.writerow(latest[customer_id])

    # Print summary in deterministic status order
    print("\nSummary by status:")
    print("status,count,total_amount")

    for status in sorted(summary):
        data = summary[status]
        print(
            f"{status},"
            f"{data['count']},"
            f"{data['total_amount']:.2f}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Process customer event CSV files offline."
    )

    parser.add_argument(
        "input",
        help="Input CSV file"
    )

    parser.add_argument(
        "output",
        help="Output CSV file"
    )

    args = parser.parse_args()

    process_events(args.input, args.output)


if __name__ == "__main__":
    main()