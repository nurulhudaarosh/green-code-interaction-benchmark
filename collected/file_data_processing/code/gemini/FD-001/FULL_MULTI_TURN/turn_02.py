import csv
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Tuple


def process_customer_events(
    input_filepath: str,
    output_filepath: str,
    timestamp_format: str = "%Y-%m-%d %H:%M:%S",
) -> Dict[str, Dict[str, Any]]:
    """Process customer event CSV files.

    Rules applied:
    1. Deduplicate on (customer_id, timestamp): Keeps the last occurrence in the file by file order.
    2. Per customer, select the chronologically latest record (breaking identical timestamps by last file occurrence).
    3. Aggregate count and total amount by status using ONLY the final retained records.
    4. Write output CSV sorted deterministically by customer_id.
    """
    # Track file encounter index alongside row data
    # Key: (customer_id, timestamp) -> Value: (file_index, parsed_dt, row)
    # Overwriting existing keys ensures the last occurrence in file order is kept.
    deduped_records: Dict[Tuple[str, str], Tuple[int, datetime, Dict[str, str]]] = {}
    fieldnames: List[str] = []

    with open(input_filepath, mode="r", encoding="utf-8-sig", newline="") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []
        for index, row in enumerate(reader):
            customer_id = row["customer_id"].strip()
            raw_ts = row["timestamp"].strip()
            parsed_dt = datetime.strptime(raw_ts, timestamp_format)
            deduped_records[(customer_id, raw_ts)] = (index, parsed_dt, row)

    # Group deduplicated records by customer_id
    customer_events: Dict[str, List[Tuple[datetime, int, Dict[str, str]]]] = defaultdict(list)
    for (customer_id, _), (file_index, parsed_dt, row) in deduped_records.items():
        customer_events[customer_id].append((parsed_dt, file_index, row))

    # For each customer, pick the chronologically latest record.
    # If a customer has events at equal timestamps, the higher file_index (last occurrence) wins.
    latest_per_customer: List[Dict[str, str]] = []
    for customer_id, events in customer_events.items():
        events.sort(key=lambda item: (item[0], item[1]))
        latest_per_customer.append(events[-1][2])

    # Deterministic output sorting by customer_id ascending
    latest_per_customer.sort(key=lambda r: r["customer_id"].strip())

    # Aggregate status totals using exclusively the final retained records
    status_summary: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "total_amount": Decimal("0.00")}
    )

    for record in latest_per_customer:
        status = record.get("status", "UNKNOWN").strip()
        amount_val = record.get("amount", "0").strip()
        amount = Decimal(amount_val) if amount_val else Decimal("0.00")

        status_summary[status]["count"] += 1
        status_summary[status]["total_amount"] += amount

    # Write final retained records to CSV
    with open(output_filepath, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(latest_per_customer)

    return dict(status_summary)