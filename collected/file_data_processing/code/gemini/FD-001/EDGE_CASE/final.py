import csv
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Tuple


def process_unordered_customer_events(
    input_filepath: str, 
    output_filepath: str
) -> Dict[str, Dict[str, Any]]:
    """
    Processes unordered customer event CSV files offline:
      1. Deduplicates (customer_id, timestamp) by keeping the last occurrence seen in the file.
      2. Finds the true chronologically latest record per customer (independent of row order).
      3. Calculates record count and total amount grouped by status on the retained records.
      4. Writes the retained records sorted deterministically by customer_id (ascending).
    """
    deduped_events: Dict[Tuple[str, str], dict] = {}
    fieldnames: List[str] = []

    # Step 1: Deduplicate (customer_id, timestamp) - file iteration order ensures last occurrence wins
    with open(input_filepath, mode="r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []
        for row in reader:
            key = (row["customer_id"].strip(), row["timestamp"].strip())
            deduped_events[key] = row

    # Step 2: Group by customer_id and select the true maximum timestamp
    customer_latest: Dict[str, dict] = {}
    customer_latest_dt: Dict[str, datetime] = {}

    for row in deduped_events.values():
        cid = row["customer_id"].strip()
        ts_str = row["timestamp"].strip()

        # Parse timestamp formats (handles ISO-8601 with/without 'T', offsets, and standard datetimes)
        try:
            dt = datetime.fromisoformat(ts_str)
        except ValueError:
            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

        # Select the strictly latest chronological timestamp
        if cid not in customer_latest_dt or dt > customer_latest_dt[cid]:
            customer_latest_dt[cid] = dt
            customer_latest[cid] = row

    # Step 3: Compute count and total amount by status from the retained records
    status_summary_acc: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"retained_count": 0, "total_amount": Decimal("0.00")}
    )

    for row in customer_latest.values():
        status = row.get("status", "UNKNOWN").strip()
        amount_str = row.get("amount", "0").strip()
        amount = Decimal(amount_str) if amount_str else Decimal("0.00")

        status_summary_acc[status]["retained_count"] += 1
        status_summary_acc[status]["total_amount"] += amount

    # Step 4: Write final records sorted deterministically by customer_id
    sorted_records = [customer_latest[cid] for cid in sorted(customer_latest.keys())]

    with open(output_filepath, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted_records)

    # Return status aggregation dictionary
    return {
        status: {
            "retained_count": metrics["retained_count"],
            "total_amount": f"{metrics['total_amount']:.2f}"
        }
        for status, metrics in sorted(status_summary_acc.items())
    }


if __name__ == "__main__":
    # Example containing out-of-order timestamps and duplicates
    unordered_sample = """customer_id,timestamp,status,amount
C103,2026-03-05T12:00:00,COMPLETED,150.00
C101,2026-03-04T09:00:00,PENDING,30.00
C102,2026-03-01T08:00:00,FAILED,10.00
C101,2026-03-01T10:00:00,COMPLETED,20.00
C101,2026-03-04T09:00:00,COMPLETED,75.00
C102,2026-03-03T18:30:00,COMPLETED,90.00
"""
    with open("unordered_events.csv", "w", encoding="utf-8") as f:
        f.write(unordered_sample.strip())

    summary = process_unordered_customer_events(
        input_filepath="unordered_events.csv",
        output_filepath="final_customer_events.csv"
    )

    print("Aggregated Status Metrics:")
    for status, metrics in summary.items():
        print(f"  {status}: Count={metrics['retained_count']}, Total=${metrics['total_amount']}")

    print("\nDeterministic Output (sorted by customer_id):")
    with open("final_customer_events.csv", "r", encoding="utf-8") as f:
        print(f.read())