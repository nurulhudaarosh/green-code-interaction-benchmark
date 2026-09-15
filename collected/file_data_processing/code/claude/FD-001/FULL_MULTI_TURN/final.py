#!/usr/bin/env python3
"""
Customer Event CSV Utility (offline, stdlib-only)

Pipeline:
1. Read input CSV (expected columns: customer_id, timestamp, status, amount)
2. Remove duplicate (customer_id, timestamp) records -> keep the LAST
   occurrence found in the input file for each identical key.
3. Compute count, total/average/min/max amount per status, using ONLY the
   retained (deduped) records -- no further filtering or collapsing.
4. Select the TRUE latest record per customer_id by comparing actual
   parsed timestamps (not file order -- input files are not guaranteed
   to be sorted chronologically). Ties broken by later file position.
5. Write two deterministic outputs:
   - customer_records.csv (one row per customer -- the true latest
     record for each customer_id -- sorted by customer_id)
   - status_summary.csv   (count + amount stats per status, computed from
     ALL retained/deduped records, sorted by status)
   ...and print the same status summary as a formatted console table.

Usage:
    python customer_events.py input.csv --outdir ./output
"""

import csv
import argparse
from datetime import datetime
from collections import defaultdict
from decimal import Decimal, InvalidOperation


REQUIRED_FIELDS = ["customer_id", "timestamp", "status", "amount"]

TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
]


def parse_timestamp(value: str) -> datetime:
    value = value.strip()
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized timestamp format: {value!r}")


def parse_amount(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        raise ValueError(f"Invalid amount value: {value!r}")


def load_rows(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_FIELDS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        rows = []
        for i, raw in enumerate(reader, start=2):  # line 1 = header
            try:
                row = {
                    "customer_id": raw["customer_id"].strip(),
                    "timestamp": raw["timestamp"].strip(),
                    "status": raw["status"].strip(),
                    "amount": raw["amount"].strip(),
                    "_dt": parse_timestamp(raw["timestamp"]),
                    "_amt": parse_amount(raw["amount"]),
                    "_input_order": i,
                }
            except ValueError as e:
                raise ValueError(f"Row {i}: {e}") from e
            rows.append(row)
        return rows


def dedupe_by_customer_and_timestamp(rows):
    """Keep the LAST occurrence for each (customer_id, timestamp) pair."""
    dedup = {}
    for row in rows:
        key = (row["customer_id"], row["timestamp"])
        dedup[key] = row  # later occurrence always overwrites earlier one
    return list(dedup.values())


def latest_per_customer(retained_rows):
    """
    Select the TRUE latest record for each customer_id by comparing the
    actual parsed timestamp (_dt), not file order -- the input file is
    not guaranteed to be sorted chronologically. If two records for the
    same customer share the exact same timestamp, the one that appears
    later in the file wins (consistent with the "keep the last
    occurrence" rule used elsewhere).
    """
    latest = {}
    for row in retained_rows:
        cid = row["customer_id"]
        current = latest.get(cid)
        if current is None:
            latest[cid] = row
            continue
        if row["_dt"] > current["_dt"]:
            latest[cid] = row
        elif row["_dt"] == current["_dt"] and row["_input_order"] > current["_input_order"]:
            latest[cid] = row
    return latest  # dict: customer_id -> row


def summarize_by_status(retained_rows):
    """
    Count, total/average/min/max amount per status, using only the
    retained (deduped) records.
    """
    summary = defaultdict(lambda: {
        "count": 0,
        "total_amount": Decimal("0"),
        "min_amount": None,
        "max_amount": None,
    })
    for row in retained_rows:
        s = summary[row["status"]]
        amt = row["_amt"]
        s["count"] += 1
        s["total_amount"] += amt
        s["min_amount"] = amt if s["min_amount"] is None else min(s["min_amount"], amt)
        s["max_amount"] = amt if s["max_amount"] is None else max(s["max_amount"], amt)

    for s in summary.values():
        s["avg_amount"] = (s["total_amount"] / s["count"]) if s["count"] else Decimal("0")

    return summary


def write_customer_records(latest_rows, out_path):
    """One row per customer -- the true latest record -- sorted by customer_id."""
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "timestamp", "status", "amount"])
        for cid in sorted(latest_rows.keys()):
            row = latest_rows[cid]
            writer.writerow([row["customer_id"], row["timestamp"], row["status"], row["amount"]])


def write_status_summary(summary, out_path):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["status", "count", "total_amount", "avg_amount", "min_amount", "max_amount"])
        for status in sorted(summary.keys()):
            s = summary[status]
            writer.writerow([
                status,
                s["count"],
                str(s["total_amount"]),
                str(s["avg_amount"]),
                str(s["min_amount"]),
                str(s["max_amount"]),
            ])


def print_status_summary(summary):
    """Pretty-print the per-status breakdown to the console."""
    headers = ["status", "count", "total_amount", "avg_amount", "min_amount", "max_amount"]
    rows = []
    for status in sorted(summary.keys()):
        s = summary[status]
        rows.append([
            status,
            str(s["count"]),
            str(s["total_amount"]),
            str(s["avg_amount"]),
            str(s["min_amount"]),
            str(s["max_amount"]),
        ])

    widths = [max(len(h), *(len(r[i]) for r in rows)) if rows else len(h)
              for i, h in enumerate(headers)]

    def fmt_row(cells):
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    print(fmt_row(headers))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print(fmt_row(r))


def main():
    parser = argparse.ArgumentParser(description="Process customer event CSV file (offline).")
    parser.add_argument("input_csv", help="Path to input CSV file")
    parser.add_argument("--outdir", default=".", help="Directory to write output files (default: current dir)")
    args = parser.parse_args()

    rows = load_rows(args.input_csv)
    retained_rows = dedupe_by_customer_and_timestamp(rows)
    summary = summarize_by_status(retained_rows)  # status totals use ALL retained records
    latest_rows = latest_per_customer(retained_rows)  # true latest per customer, by timestamp

    customer_out = f"{args.outdir.rstrip('/')}/customer_records.csv"
    summary_out = f"{args.outdir.rstrip('/')}/status_summary.csv"

    write_customer_records(latest_rows, customer_out)
    write_status_summary(summary, summary_out)

    print(f"Input rows read:              {len(rows)}")
    print(f"Retained after (customer,ts) dedup: {len(retained_rows)}")
    print(f"Unique customers (true latest): {len(latest_rows)}")
    print()
    print("Status summary (from retained records only):")
    print_status_summary(summary)
    print()
    print(f"Wrote: {customer_out}")
    print(f"Wrote: {summary_out}")


if __name__ == "__main__":
    main()