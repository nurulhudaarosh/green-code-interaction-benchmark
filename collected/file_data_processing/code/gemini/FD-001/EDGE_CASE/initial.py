import csv
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Tuple


def process_customer_events(
    input_filepath: str, 
    output_filepath: str
) -> Dict[str, Dict[str, Any]]:
    """
    Processes customer event CSV files offline:
      1. Deduplicates (customer_id, timestamp) keeping the last occurrence.
      2. Retains the chronologically latest record per customer.
      3. Computes record count and total amount grouped by status.
      4. Writes retained records sorted deterministically by customer_id to output_filepath.
    
    Expected CSV columns:
      customer_id,timestamp,status,amount
    """
    # Step 1: Deduplicate (customer_id, timestamp) preserving the last occurrence
    deduped_events: Dict[Tuple[str, str], dict] = {}
    fieldnames: List[str] = []

    with open(input_filepath, mode="r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []
        for row in reader:
            key = (row["customer_id"].strip(), row["timestamp"].strip())
            deduped_events[key] = row  # Overwrites prior occurrences

    # Step 2: Select the chronologically latest record for each customer
    customer_latest: Dict[str, dict] = {}
    customer_latest_dt: Dict[str, datetime] = {}

    for row in deduped_events.values():
        cid = row["customer_id"].strip()
        ts_str = row["timestamp"].strip()

        # Parse ISO-8601 or standard datetime formats
        try:
            dt = datetime.fromisoformat(ts_str)
        except ValueError:
            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

        # Keep the latest timestamp; strictly newer timestamps replace existing ones
        if cid not in customer_latest_dt or dt >= customer_latest_dt[cid]:
            customer_latest_dt[cid] = dt
            customer_latest[cid] = row

    # Step 3: Compute aggregations (count and total amount by status) on retained records
    status_summary: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"retained_count": 0, "total_amount": Decimal("0.00")}
    )

    for row in customer_latest.values():
        status = row.get("status", "UNKNOWN").strip()
        amount_str = row.get("amount", "0").strip()
        amount = Decimal(amount_str) if amount_str else Decimal("0.00")

        status_summary[status]["retained_count"] += 1
        status_summary[status]["total_amount"] += amount

    # Step 4: Write output sorted deterministically by customer_id
    sorted_records = [customer_latest[cid] for cid in sorted(customer_latest.keys())]

    with open(output_filepath, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted_records)

    # Format summary dictionary
    return {
        status: {
            "retained_count": metrics["retained_count"],
            "total_amount": f"{metrics['total_amount']:.2f}"
        }
        for status, metrics in sorted(status_summary.items())
    }


if __name__ == "__main__":
    sample_data = """customer_id,timestamp,status,amount
C101,2026-03-01T10:00:00,COMPLETED,45.50
C102,2026-03-01T11:00:00,PENDING,12.00
C101,2026-03-01T10:00:00,COMPLETED,50.00
C101,2026-03-02T09:30:00,COMPLETED,100.00
C103,2026-03-01T08:00:00,FAILED,25.00
C102,2026-03-03T14:15:00,COMPLETED,30.00
"""
    with open("input_events.csv", "w", encoding="utf-8") as f:
        f.write(sample_data.strip())

    summary = process_customer_events("input_events.csv", "output_latest_events.csv")
    print("Status Aggregation on Retained Records:")
    for status, data in summary.items():
        print(f"  {status}: Count = {data['retained_count']}, Total = {data['total_amount']}")