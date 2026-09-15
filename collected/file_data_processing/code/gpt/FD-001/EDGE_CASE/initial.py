import csv
import argparse
from decimal import Decimal, InvalidOperation


def process_events(input_file, output_file, summary_file):
    # Read all rows while preserving input order
    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    required_columns = {"customer_id", "timestamp", "status", "amount"}

    if not required_columns.issubset(reader.fieldnames or []):
        missing = required_columns - set(reader.fieldnames or [])
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    # ---------------------------------------------------------
    # Step 1: Remove duplicate customer/timestamp records.
    # Keep the LAST occurrence in the input file.
    # ---------------------------------------------------------
    last_occurrence = {}

    for index, row in enumerate(rows):
        key = (row["customer_id"], row["timestamp"])
        last_occurrence[key] = (index, row)

    # Sort by original input position so chronological selection
    # remains deterministic when timestamps are equal.
    deduplicated = [
        item[1]
        for item in sorted(last_occurrence.values(), key=lambda x: x[0])
    ]

    # ---------------------------------------------------------
    # Step 2: Select the chronologically latest record
    # for each customer.
    #
    # If timestamps are identical, the later input occurrence
    # wins (which is already guaranteed by deduplication).
    # ---------------------------------------------------------
    latest_by_customer = {}

    for row in deduplicated:
        customer_id = row["customer_id"]

        if customer_id not in latest_by_customer:
            latest_by_customer[customer_id] = row
        else:
            current = latest_by_customer[customer_id]

            if row["timestamp"] > current["timestamp"]:
                latest_by_customer[customer_id] = row

    # ---------------------------------------------------------
    # Step 3: Sort final customer records deterministically.
    # ---------------------------------------------------------
    retained = sorted(
        latest_by_customer.values(),
        key=lambda row: row["customer_id"]
    )

    # ---------------------------------------------------------
    # Step 4: Calculate count and total amount by status
    # using ONLY the retained customer records.
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
    # Step 5: Write retained customer records.
    # ---------------------------------------------------------
    fieldnames = reader.fieldnames

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(retained)

    # ---------------------------------------------------------
    # Step 6: Write deterministic status summary.
    # Sort statuses alphabetically.
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

    print(f"Processed {len(rows)} input records.")
    print(f"After duplicate removal: {len(deduplicated)} records.")
    print(f"Final retained customer records: {len(retained)}.")
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
        help="Output CSV containing the latest record for each customer"
    )

    parser.add_argument(
        "-s",
        "--summary",
        default="status_summary.csv",
        help="Output CSV containing status counts and total amounts"
    )

    args = parser.parse_args()

    process_events(
        args.input,
        args.output,
        args.summary
    )


if __name__ == "__main__":
    main()