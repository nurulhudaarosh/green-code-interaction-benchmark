import csv
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Tuple, Any


def process_customer_events(input_filepath: str, output_filepath: str) -> Dict[str, Dict[str, Any]]:
    """
    Processes customer event CSV records offline:
      1. Deduplicates (customer_id, timestamp) by keeping the last occurrence.
      2. Selects the chronologically latest record for each customer.
      3. Aggregates count and total amount grouped by status on retained records.
      4. Writes the latest records sorted deterministically by customer_id to output CSV.
    
    Expected CSV Header:
      customer_id,timestamp,status,amount (plus any additional columns)
    """
    # Step 1: Deduplicate (customer_id, timestamp) preserving the last occurrence in file
    deduped_events: Dict[Tuple[str, str], dict] = {}
    fieldnames: List[str] = []

    with open(input_filepath, mode="r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []
        for row in reader:
            key = (row["customer_id"].strip(), row["timestamp"].strip())
            deduped_events[key] = row  # Overwrites earlier occurrences

    # Step 2: Select the chronologically latest record per customer
    # Group records by customer_id and parse timestamps (ISO 8601 / standard datetime formats)
    customer_latest: Dict[str, dict] = {}
    customer_latest_dt: Dict[str, datetime] = {}

    for row in deduped_events.values():
        cid = row["customer_id"].strip()
        # Parse ISO-8601 / common timestamp formats
        ts_str = row["timestamp"].strip()
        try:
            dt = datetime.fromisoformat(ts_str)
        except ValueError:
            # Fallback for formats like "YYYY-MM-DD HH:MM:SS"
            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

        if cid not in customer_latest_dt or dt > customer_latest_dt[cid]:
            customer_latest_dt[cid] = dt
            customer_latest[cid] = row

    # Step 3: Compute aggregations (count and total amount by status) on retained records
    status_summary: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "total_amount": Decimal("0.00")})

    for row in customer_latest.values():
        status = row.get("status", "UNKNOWN").strip()
        amount_raw = row.get("amount", "0").strip()
        amount = Decimal(amount_raw) if amount_raw else Decimal("0.00")

        status_summary[status]["count"] += 1
        status_summary[status]["total_amount"] += amount

    # Step 4: Write output sorted deterministically by customer_id
    sorted_records = [customer_latest[cid] for cid in sorted(customer_latest.keys())]

    with open(output_filepath, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted_records)

    # Format summary for clean inspection
    summary_result = {
        status: {
            "count": data["count"],
            "total_amount": f"{data['total_amount']:.2f}"
        }
        for status, data in sorted(status_summary.items())
    }

    return summary_result


if __name__ == "__main__":
    import io

    # Demonstration with in-memory sample CSV data
    sample_csv = """customer_id,timestamp,status,amount
C101,2026-03-01T10:00:00,COMPLETED,45.50
C102,2026-03-01T11:00:00,PENDING,12.00
C101,2026-03-01T10:00:00,COMPLETED,50.00
C101,2026-03-02T09:30:00,COMPLETED,100.00
C103,2026-03-01T08:00:00,FAILED,25.00
C102,2026-03-03T14:15:00,COMPLETED,30.00
"""

    with open("input_events.csv", "w", encoding="utf-8") as f:
        f.write(sample_csv.strip())

    summary = process_customer_events("input_events.csv", "output_latest_events.csv")
    print("Status Aggregation Summary:")
    for status, metrics in summary.items():
        print(f"  {status}: Count = {metrics['count']}, Total Amount = {metrics['total_amount']}")

    print("\nGenerated CSV Contents (output_latest_events.csv):")
    with open("output_latest_events.csv", "r", encoding="utf-8") as f:
        print(f.read())