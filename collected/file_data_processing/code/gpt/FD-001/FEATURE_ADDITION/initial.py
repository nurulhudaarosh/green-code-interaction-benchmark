import csv
from collections import defaultdict
from datetime import datetime
from decimal import Decimal


def process_customer_events(input_file, output_file):
    rows = []

    # Read input and preserve original order
    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for index, row in enumerate(reader):
            row["_input_order"] = index
            rows.append(row)

    # 1. Remove duplicate customer_id + timestamp records.
    #    Keep the LAST occurrence in the input file.
    retained_by_key = {}

    for row in rows:
        key = (row["customer_id"], row["timestamp"])
        retained_by_key[key] = row

    deduplicated = list(retained_by_key.values())

    # 2. Select the chronologically latest record for each customer.
    latest_by_customer = {}

    for row in deduplicated:
        customer_id = row["customer_id"]

        if customer_id not in latest_by_customer:
            latest_by_customer[customer_id] = row
        else:
            current = latest_by_customer[customer_id]

            current_time = datetime.fromisoformat(current["timestamp"])
            new_time = datetime.fromisoformat(row["timestamp"])

            if new_time > current_time:
                latest_by_customer[customer_id] = row
            elif new_time == current_time:
                # This normally cannot happen after deduplication,
                # but preserves the last input occurrence if needed.
                if row["_input_order"] > current["_input_order"]:
                    latest_by_customer[customer_id] = row

    latest_records = list(latest_by_customer.values())

    # 3. Calculate count and total amount by status
    #    using ONLY the retained/latest records.
    status_summary = defaultdict(lambda: {"count": 0, "total_amount": Decimal("0")})

    for row in latest_records:
        status = row["status"]
        amount = Decimal(row["amount"])

        status_summary[status]["count"] += 1
        status_summary[status]["total_amount"] += amount

    # 4. Sort records deterministically by customer_id
    latest_records.sort(key=lambda row: row["customer_id"])

    # 5. Write deterministic output.
    fieldnames = ["customer_id", "timestamp", "status", "amount"]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in latest_records:
            writer.writerow({
                "customer_id": row["customer_id"],
                "timestamp": row["timestamp"],
                "status": row["status"],
                "amount": row["amount"]
            })

    # Print status summary in deterministic status order
    print("Status Summary")
    print("-" * 40)

    for status in sorted(status_summary):
        summary = status_summary[status]

        print(
            f"{status}: "
            f"count={summary['count']}, "
            f"total_amount={summary['total_amount']}"
        )


if __name__ == "__main__":
    process_customer_events(
        input_file="customer_events.csv",
        output_file="customer_events_processed.csv"
    )