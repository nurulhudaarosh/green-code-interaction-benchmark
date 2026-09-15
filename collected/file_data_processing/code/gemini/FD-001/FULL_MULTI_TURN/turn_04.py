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
    """Process customer event CSV files regardless of input row order.

    Pipeline:
    1. Deduplicate on (customer_id, raw_timestamp): Keeps the last occurrence in file order.
    2. Chronologically select the true latest timestamp for each customer:
       - Compares parsed `datetime` objects.
       - Breaks timestamp ties using the higher file index (latest occurrence in file).
    3. Aggregate count and total amount by status solely on the final retained records.
    4. Deterministically sort final retained customer records by `customer_id` ascending.
    5. Optionally write a status summary CSV.
    """
    # Key: (customer_id, raw_timestamp) -> Value: (file_index, parsed_datetime, row_dict)
    # Overwriting ensures that within identical (customer_id, timestamp) pairs, the last occurrence in the file is kept.
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

    # Find the true latest record per customer regardless of row order in input
    # max() compares (datetime, file_index):
    # - primary key: true chronological datetime
    # - secondary key: latest file order index for ties
    latest_per_customer: List[Dict[str, str]] = []
    for customer_id, events in customer_events.items():
        latest_event = max(events, key=lambda item: (item[0], item[1]))
        latest_per_customer.append(latest_event[2])

    # Sort final retained records strictly and deterministically by customer_id
    latest_per_customer.sort(key=lambda r: r["customer_id"].strip())

    # Calculate status metrics exclusively from the retained customer records
    status_summary: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "total_amount": Decimal("0.00")}
    )

    for record in latest_per_customer:
        status = record.get("status", "UNKNOWN").strip()
        amount_raw = record.get("amount", "0").strip()
        amount = Decimal(amount_raw) if amount_raw else Decimal("0.00")

        status_summary[status]["count"] += 1
        status_summary[status]["total_amount"] += amount

    # Write sorted customer-level records
    with open(output_filepath, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(latest_per_customer)

    # Optionally write status summary CSV
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