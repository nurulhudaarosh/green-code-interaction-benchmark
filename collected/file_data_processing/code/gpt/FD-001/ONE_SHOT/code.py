import csv
import argparse
from collections import defaultdict
from decimal import Decimal, InvalidOperation


REQUIRED_COLUMNS = {"customer_id", "timestamp", "status", "amount"}


def process_events(input_csv, output_csv):
    rows = []

    # Read input CSV
    with open(input_csv, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("Input CSV has no header.")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        for line_no, row in enumerate(reader, start=2):
            try:
                amount = Decimal(row["amount"])
            except (InvalidOperation, TypeError):
                raise ValueError(
                    f"Invalid amount on line {line_no}: {row['amount']}"
                )

            rows.append({
                "customer_id": row["customer_id"],
                "timestamp": row["timestamp"],
                "status": row["status"],
                "amount": amount
            })

    # Remove duplicate customer/timestamp records.
    # Assigning again keeps the LAST occurrence.
    deduplicated = {}

    for row in rows:
        key = (row["customer_id"], row["timestamp"])
        deduplicated[key] = row

    # Select chronologically latest record for each customer
    latest_records = {}

    for row in deduplicated.values():
        customer_id = row["customer_id"]

        if (
            customer_id not in latest_records
            or row["timestamp"] > latest_records[customer_id]["timestamp"]
        ):
            latest_records[customer_id] = row

    # Sort by customer_id for deterministic output
    retained = sorted(
        latest_records.values(),
        key=lambda row: row["customer_id"]
    )

    # Calculate count and total amount by status
    summary = defaultdict(lambda: {
        "count": 0,
        "total_amount": Decimal("0")
    })

    for row in retained:
        status = row["status"]

        summary[status]["count"] += 1
        summary[status]["total_amount"] += row["amount"]

    # Write output CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Retained records
        writer.writerow([
            "customer_id",
            "timestamp",
            "status",
            "amount"
        ])

        for row in retained:
            writer.writerow([
                row["customer_id"],
                row["timestamp"],
                row["status"],
                format(row["amount"], "f")
            ])

        # Status summary
        writer.writerow([])
        writer.writerow([
            "status",
            "count",
            "total_amount"
        ])

        for status in sorted(summary):
            writer.writerow([
                status,
                summary[status]["count"],
                format(summary[status]["total_amount"], "f")
            ])


def main():
    parser = argparse.ArgumentParser(
        description="Process customer event CSV files."
    )

    parser.add_argument(
        "input_csv",
        help="Path to input CSV file"
    )

    parser.add_argument(
        "output_csv",
        help="Path to output CSV file"
    )

    args = parser.parse_args()

    process_events(
        args.input_csv,
        args.output_csv
    )

    print("Processing completed successfully.")
    print(f"Output written to: {args.output_csv}")


if __name__ == "__main__":
    main()