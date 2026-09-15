#!/usr/bin/env python3
"""
customer_event_processor.py

Offline utility for processing customer event CSV files.

Pipeline:
    1. Read raw event rows from a CSV file.
    2. Remove duplicate (customer_id, timestamp) rows, keeping the LAST
       occurrence in the file for each duplicate key.
    3. From the deduplicated rows, select the chronologically LATEST
       record per customer_id.
    4. Compute count and total amount per status, over the retained
       (latest-per-customer) records only.
    5. Write two deterministic CSV outputs:
         - retained records, sorted by customer_id
         - status summary, sorted by status

No network access or third-party packages are used; only the Python
standard library. Safe to run fully offline.

Usage:
    python customer_event_processor.py events.csv \
        --retained-output retained_records.csv \
        --summary-output status_summary.csv

    # Custom column names / explicit timestamp format
    python customer_event_processor.py events.csv \
        --customer-col cust_id --timestamp-col ts \
        --status-col state --amount-col amt \
        --timestamp-format "%Y-%m-%d %H:%M:%S"
"""

import argparse
import csv
import sys
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class Event:
    customer_id: str
    timestamp: datetime
    timestamp_raw: str
    status: str
    amount: Decimal
    row_index: int  # original file order; used for stable dedup/tie-break
    raw_row: Dict[str, str]


def parse_timestamp(value: str, fmt: Optional[str]) -> datetime:
    value = value.strip()
    if fmt:
        return datetime.strptime(value, fmt)
    # Accept a trailing "Z" as UTC, since fromisoformat rejects it directly
    # on older Python versions.
    iso_value = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return datetime.fromisoformat(iso_value)
    except ValueError as exc:
        raise ValueError(
            f"Could not parse timestamp {value!r}. "
            "Pass --timestamp-format to specify an explicit strptime format "
            "(e.g. '%Y-%m-%d %H:%M:%S')."
        ) from exc


def parse_amount(value: str) -> Decimal:
    cleaned = value.strip().replace(",", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Could not parse amount {value!r} as a decimal number.") from exc


def read_events(
    path: Path,
    customer_col: str,
    timestamp_col: str,
    status_col: str,
    amount_col: str,
    timestamp_format: Optional[str],
) -> List[Event]:
    events: List[Event] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {customer_col, timestamp_col, status_col, amount_col}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Input CSV is missing required column(s): {sorted(missing)}. "
                f"Found columns: {reader.fieldnames}"
            )
        for i, row in enumerate(reader):
            customer_id = row[customer_col].strip()
            ts_raw = row[timestamp_col]
            ts = parse_timestamp(ts_raw, timestamp_format)
            status = row[status_col].strip()
            amount = parse_amount(row[amount_col])
            events.append(
                Event(
                    customer_id=customer_id,
                    timestamp=ts,
                    timestamp_raw=ts_raw.strip(),
                    status=status,
                    amount=amount,
                    row_index=i,
                    raw_row=row,
                )
            )
    return events


def dedupe_keep_last(events: List[Event]) -> List[Event]:
    """Remove duplicate (customer_id, timestamp) rows, keeping the last
    occurrence in original file order for each key."""
    last_by_key: Dict[Tuple[str, datetime], Event] = {}
    for ev in events:
        key = (ev.customer_id, ev.timestamp)
        last_by_key[key] = ev  # a later occurrence overwrites an earlier one
    # Preserve original file order for determinism downstream.
    return sorted(last_by_key.values(), key=lambda e: e.row_index)


def latest_per_customer(events: List[Event]) -> List[Event]:
    """Select the chronologically latest record for each customer_id.
    Ties on identical max timestamp are broken by original file order
    (the row that appeared later in the file wins), for determinism."""
    best_by_customer: Dict[str, Event] = {}
    for ev in events:
        current = best_by_customer.get(ev.customer_id)
        if current is None or (ev.timestamp, ev.row_index) > (current.timestamp, current.row_index):
            best_by_customer[ev.customer_id] = ev
    return list(best_by_customer.values())


def summarize_by_status(events: List[Event]) -> Dict[str, Dict[str, Decimal]]:
    summary: Dict[str, Dict[str, Decimal]] = {}
    for ev in events:
        bucket = summary.setdefault(ev.status, {"count": Decimal(0), "total_amount": Decimal(0)})
        bucket["count"] += 1
        bucket["total_amount"] += ev.amount
    return summary


def write_retained(
    path: Path,
    events: List[Event],
    customer_col: str,
    timestamp_col: str,
    status_col: str,
    amount_col: str,
) -> None:
    ordered = sorted(events, key=lambda e: e.customer_id)
    fieldnames = [customer_col, timestamp_col, status_col, amount_col]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for ev in ordered:
            writer.writerow(
                {
                    customer_col: ev.customer_id,
                    timestamp_col: ev.timestamp_raw,
                    status_col: ev.status,
                    amount_col: format(ev.amount.normalize(), "f"),
                }
            )


def write_summary(path: Path, summary: Dict[str, Dict[str, Decimal]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["status", "count", "total_amount"])
        for status in sorted(summary.keys()):
            bucket = summary[status]
            writer.writerow(
                [status, int(bucket["count"]), format(bucket["total_amount"].normalize(), "f")]
            )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deduplicate and summarize customer event CSV files (fully offline)."
    )
    parser.add_argument("input", type=Path, help="Path to the input CSV file.")
    parser.add_argument(
        "--retained-output",
        type=Path,
        default=Path("retained_records.csv"),
        help="Where to write the retained (latest-per-customer) records. Default: retained_records.csv",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("status_summary.csv"),
        help="Where to write the count/total-amount-by-status summary. Default: status_summary.csv",
    )
    parser.add_argument("--customer-col", default="customer_id", help="Customer ID column name.")
    parser.add_argument("--timestamp-col", default="timestamp", help="Timestamp column name.")
    parser.add_argument("--status-col", default="status", help="Status column name.")
    parser.add_argument("--amount-col", default="amount", help="Amount column name.")
    parser.add_argument(
        "--timestamp-format",
        default=None,
        help="Optional strptime format (e.g. '%%Y-%%m-%%d %%H:%%M:%%S'). "
        "If omitted, ISO 8601 parsing is attempted.",
    )
    args = parser.parse_args(argv)

    events = read_events(
        args.input,
        args.customer_col,
        args.timestamp_col,
        args.status_col,
        args.amount_col,
        args.timestamp_format,
    )
    deduped = dedupe_keep_last(events)
    retained = latest_per_customer(deduped)
    summary = summarize_by_status(retained)

    write_retained(
        args.retained_output, retained, args.customer_col, args.timestamp_col, args.status_col, args.amount_col
    )
    write_summary(args.summary_output, summary)

    print(f"Read {len(events)} rows from {args.input}")
    print(f"After dedup on (customer_id, timestamp), keeping last: {len(deduped)} rows")
    print(f"Retained (latest record per customer): {len(retained)} rows -> {args.retained_output}")
    print(f"Status summary -> {args.summary_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())