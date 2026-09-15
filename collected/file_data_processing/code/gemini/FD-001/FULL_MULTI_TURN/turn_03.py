import csv
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple


def process_customer_events(
    input_filepath: str,
    output_filepath: str,
    summary_filepath: Optional[str] = None,
    timestamp_format: str = "%Y-%m-%d %H:%M:%S",
) -> Dict[str, Dict[str, Any]]:
    """Process customer event CSV files.

    Rules applied:
    1. Deduplicate on (customer_id, timestamp): Keeps the last occurrence in file order.
    2. Per customer, select the chronologically latest record (ties broken by latest file order).
    3. Aggregate count and total amount by status using ONLY the final retained records.
    4. Write retained customer records sorted deterministically by customer_id.
    5. Optionally write status summary breakdown to a separate CSV file.

    Returns:
        Dict mapping status -> {'count': int, 'total_amount': Decimal}
    """
    deduped_records: Dict[Tuple[str, str], Tuple[int, datetime, Dict[str, str]]] = {}
    fieldnames: List[str] = []

    # 1. Read and deduplicate by (customer_id, timestamp), keeping the last occurrence
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

    # 2. Select chronologically latest record per customer
    latest_per_customer: List[Dict[str, str]] = []
    for customer_id, events in customer_events.items():
        events.sort(key=lambda item: (item[0], item[1]))
        latest_per_customer.append(events[-1][2])

    # Sort retained records deterministically by customer_id
    latest_per_customer.sort(key=lambda r: r["customer_id"].strip())

    # 3. Calculate status aggregations solely from retained records
    status_summary: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "total_amount": Decimal("0.00")}
    )

    for record in latest_per_customer:
        status = record.get("status", "UNKNOWN").strip()
        amount_val = record.get("amount", "0").strip()
        amount = Decimal(amount_val) if amount_val else Decimal("0.00")

        status_summary[status]["count"] += 1
        status_summary[status]["total_amount"] += amount

    # 4. Write retained customer records CSV
    with open(output_filepath, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(latest_per_customer)

    # 5. Optionally export summary CSV sorted deterministically by status
    if summary_filepath:
        with open(summary_filepath, mode="w", encoding="utf-8", newline="") as sumfile:
            sum_writer = csv.writer(sumfile)
            sum_writer.writerow(["status", "record_count", "total_amount"])
            for status in sorted(status_summary.keys()):
                metrics = status_summary[status]
                sum_writer.writerow([
                    status,
                    metrics["count"],
                    f"{metrics['total_amount']:.2f}",
                ])

    return dict(status_summary)


def print_status_summary(summary: Dict[str, Dict[str, Any]]) -> None:
    """Print a formatted table of the status summary."""
    print(f"\n{'Status':<15} | {'Retained Records':<18} | {'Total Amount':<12}")
    print("-" * 52)
    for status in sorted(summary.keys()):
        metrics = summary[status]
        print(f"{status:<15} | {metrics['count']:<18} | {metrics['total_amount']:>12.2f}")