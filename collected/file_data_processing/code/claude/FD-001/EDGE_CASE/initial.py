#!/usr/bin/env python3
"""
customer_events.py — Offline CSV utility for customer event processing.

Pipeline:
  1. Read input CSV (expects at least: customer_id, timestamp, status, amount).
  2. Remove duplicate (customer_id, timestamp) records, keeping the LAST
     occurrence in file order.
  3. From the deduplicated set, keep only the chronologically LATEST record
     per customer_id.
  4. Compute count and total amount per status, using only those retained
     (latest-per-customer) records.
  5. Write deterministic output:
       - retained records, sorted by customer_id
       - status summary (count, total_amount), sorted by status

No external dependencies — stdlib only, runs fully offline.
"""

import csv
import sys
import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation
from collections import OrderedDict, defaultdict


REQUIRED_FIELDS = ("customer_id", "timestamp", "status", "amount")

# Timestamp formats to try, in order. Extend as needed.
TIMESTAMP_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y",
)


class RowError(ValueError):
    """Raised when a row cannot be parsed/validated."""


def parse_timestamp(raw: str) -> datetime:
    raw = raw.strip()
    # Try native ISO parsing first (handles most modern formats, incl. offsets)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        pass
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise RowError(f"Unparseable timestamp: {raw!r}")


def parse_amount(raw: str) -> Decimal:
    try:
        return Decimal(raw.strip())
    except (InvalidOperation, AttributeError):
        raise RowError(f"Unparseable amount: {raw!r}")


def read_rows(path: str):
    """Read CSV, validate required columns, parse timestamp/amount.
    Returns a list of dicts in original file order (row_index preserved)."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_FIELDS if c not in (reader.fieldnames or [])]
        if missing:
            raise RowError(f"Missing required columns: {missing}")

        rows = []
        for i, raw_row in enumerate(reader):
            try:
                ts = parse_timestamp(raw_row["timestamp"])
                amt = parse_amount(raw_row["amount"])
            except RowError as e:
                print(f"[WARN] Skipping row {i}: {e}", file=sys.stderr)
                continue

            customer_id = raw_row["customer_id"].strip()
            status = raw_row["status"].strip()
            if not customer_id or not status:
                print(f"[WARN] Skipping row {i}: missing customer_id/status", file=sys.stderr)
                continue

            rows.append({
                "customer_id": customer_id,
                "timestamp": ts,
                "timestamp_raw": raw_row["timestamp"].strip(),
                "status": status,
                "amount": amt,
                "_order": i,
            })
        return rows


def dedupe_keep_last(rows):
    """Remove duplicate (customer_id, timestamp) records, keeping the LAST
    occurrence in file order. Uses an OrderedDict to overwrite earlier
    entries deterministically as later duplicates are encountered."""
    deduped = OrderedDict()
    for row in rows:
        key = (row["customer_id"], row["timestamp"])
        deduped[key] = row  # later occurrence overwrites earlier one
    return list(deduped.values())


def latest_per_customer(rows):
    """From deduplicated rows, keep only the chronologically latest record
    per customer_id. Ties broken by original file order (last one wins),
    for full determinism."""
    latest = {}
    for row in rows:
        cid = row["customer_id"]
        current = latest.get(cid)
        if current is None:
            latest[cid] = row
            continue
        if row["timestamp"] > current["timestamp"]:
            latest[cid] = row
        elif row["timestamp"] == current["timestamp"] and row["_order"] > current["_order"]:
            latest[cid] = row
    return list(latest.values())


def summarize_by_status(rows):
    """Count and total amount by status, over the given (retained) rows."""
    counts = defaultdict(int)
    totals = defaultdict(lambda: Decimal("0"))
    for row in rows:
        counts[row["status"]] += 1
        totals[row["status"]] += row["amount"]
    return counts, totals


def write_retained_csv(rows, path):
    rows_sorted = sorted(rows, key=lambda r: r["customer_id"])
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "timestamp", "status", "amount"])
        for r in rows_sorted:
            writer.writerow([
                r["customer_id"],
                r["timestamp"].isoformat(),
                r["status"],
                format(r["amount"], "f"),
            ])


def write_summary_csv(counts, totals, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["status", "count", "total_amount"])
        for status in sorted(counts.keys()):
            writer.writerow([status, counts[status], format(totals[status], "f")])


def process(input_path, retained_out_path, summary_out_path):
    rows = read_rows(input_path)
    deduped = dedupe_keep_last(rows)
    retained = latest_per_customer(deduped)
    counts, totals = summarize_by_status(retained)

    write_retained_csv(retained, retained_out_path)
    write_summary_csv(counts, totals, summary_out_path)

    return {
        "input_rows": len(rows),
        "after_dedupe": len(deduped),
        "retained_customers": len(retained),
        "status_counts": dict(counts),
        "status_totals": {k: format(v, "f") for k, v in totals.items()},
    }


def main():
    parser = argparse.ArgumentParser(description="Process customer event CSV (offline).")
    parser.add_argument("input_csv", help="Path to input CSV file")
    parser.add_argument("--retained-out", default="retained_records.csv",
                         help="Output path for retained (latest-per-customer) records")
    parser.add_argument("--summary-out", default="status_summary.csv",
                         help="Output path for count/total-by-status summary")
    args = parser.parse_args()

    stats = process(args.input_csv, args.retained_out, args.summary_out)

    print("Done.")
    print(f"  Input rows read:        {stats['input_rows']}")
    print(f"  After dedupe:           {stats['after_dedupe']}")
    print(f"  Retained (per customer):{stats['retained_customers']}")
    print("  Status summary:")
    for status in sorted(stats["status_counts"]):
        print(f"    {status}: count={stats['status_counts'][status]}, "
              f"total={stats['status_totals'][status]}")


if __name__ == "__main__":
    main()