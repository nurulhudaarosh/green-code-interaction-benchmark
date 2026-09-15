import csv
import argparse
from decimal import Decimal, InvalidOperation
from datetime import datetime


def parse_timestamp(value):
    """Parse ISO-8601 timestamps for reliable chronological comparison."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"Invalid timestamp: {value}")


def process_events(input_file, output_file, summary_file):
    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    required_columns = {"customer_id", "timestamp", "status", "amount"}

    if not fieldnames or not required_columns.issubset(fieldnames):
        missing = required_columns - set(fieldnames or [])
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing))}"
        )

    # ---------------------------------------------------------
    # Step 1:
    # Remove duplicate (customer_id, timestamp) records.
    # Keep the LAST occurrence in the input file.
    # ---------------------------------------------------------
    last_occurrence = {}

    for index, row in enumerate(rows):
        key = (row["customer_id"], row["timestamp"])
        last_occurrence[key] = (index, row)

    deduplicated = [
        row
        for _, row in sorted(
            last_occurrence.values(),
            key=lambda item: item[0]
        )
    ]

    # ---------------------------------------------------------
    # Step 2:
    # Select the TRUE latest timestamp for each customer.
    #
    # Input order does NOT matter.
    # ---------------------------------------------------------
    latest_by_customer = {}

    for row in deduplicated:
        customer_id = row["customer_id"]
        timestamp = parse_timestamp(row["timestamp"])

        if customer_id not in latest_by_customer:
            latest_by_customer[customer_id] = (timestamp, row)
        else:
            current_timestamp, current_row = latest_by_customer[customer_id]

            if timestamp > current_timestamp:
                latest_by_customer[customer_id] = (timestamp, row)

    # ---------------------------------------------------------
    # Step 3:
    # Sort final customer records by customer_id.
    # ---------------------------------------------------------
    retained = [
        row
        for _, row in sorted(
            latest_by_customer.items(),
            key=lambda item: item[0]
        )
    ]

    # ---------------------------------------------------------
    # Step 4:
    # Calculate status summary using ONLY retained records.
    # ---------------------------------------------------------
    status_summary = {}

    for row in retained:
        status = row["status"]

        try:
            amount = Decimal(row["amount"])
        except InvalidOperation:
            raise ValueError(
                f"Invalid amount '{row['amount']}' "
                f"for customer '{row['customer_id']}'"
            )

        if status not in status_summary:
            status_summary[status] = {
                "count": 0,
                "total_amount": Decimal("0")
            }

        status_summary[status]["count"] += 1
        status_summary[status]["total_amount"] += amount

    # ---------------------------------------------------------
    # Step 5:
    # Write final customer records.
    # Already sorted by customer_id.
    # ---------------------------------------------------------
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(retained)

    # ---------------------------------------------------------
    # Step 6:
    # Write deterministic status summary.
    # ---------------------------------------------------------
    with open(summary_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["status", "count", "total_amount"])

        for status in sorted(status_summary):
            summary = status_summary[status]

            writer.writerow([
                status,
                summary["count"],
                format(summary["total_amount"], "f")
            ])

    print(f"Input records: {len(rows)}")
    print(f"After duplicate removal: {len(deduplicated)}")
    print(f"Final customer records: {len(retained)}")
    print(f"Customer output: {output_file}")
    print(f"Status summary: {summary_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Process customer event CSV files offline."
    )

    parser.add_argument(
        "input",
        help="Input customer event CSV file"
    )

    parser.add_argument(
        "-o",
        "--output",
        default="retained_customers.csv",
        help="Output CSV for final customer records"
    )

    parser.add_argument(
        "-s",
        "--summary",
        default="status_summary.csv",
        help="Output CSV for status summary"
    )

    args = parser.parse_args()

    process_events(
        args.input,
        args.output,
        args.summary
    )


if __name__ == "__main__":
    main()