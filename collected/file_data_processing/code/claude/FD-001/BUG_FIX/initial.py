#!/usr/bin/env python3
"""
customer_event_processor.py

Offline utility for processing customer event CSV files.

Pipeline:
  1. Deduplicate on (customer_id, timestamp), keeping the LAST occurrence
     in the file for any exact duplicate pair.
  2. From the deduplicated records, select the chronologically LATEST
     record for each customer.
  3. Using only those retained (one-per-customer) records, calculate the
     count and total amount grouped by status.
  4. Write deterministic output:
       - latest_by_customer.csv, sorted by customer_id
       - status_summary.csv,   sorted by status

No third-party dependencies. Uses only the Python standard library, so it
runs fully offline.

Usage:
    python customer_event_processor.py --input events.csv --output-dir out/

    # Custom column names, if your CSV doesn't use the defaults:
    python customer_event_processor.py --input events.csv \
        --customer-col cust_id --timestamp-col event_ts \
        --status-col state --amount-col value

    # Skip malformed rows instead of failing on them:
    python customer_event_processor.py --input events.csv --skip-invalid
"""

import argparse
import csv
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


class RowError(ValueError):
    """Raised when a single CSV row can't be parsed."""


def parse_timestamp(raw: str) -> datetime:
    """
    Parse a timestamp string into a datetime for chronological comparison.

    Accepts ISO 8601 (e.g. 2024-01-15T10:30:00, 2024-01-15 10:30:00,
    with or without a 'Z' suffix or UTC offset). Raises RowError if the
    value can't be parsed by any supported format.
    """
    raw = raw.strip()
    if not raw:
        raise RowError("empty timestamp")

    candidate = raw
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"

    # Try native ISO parsing first (handles most real-world cases).
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        pass

    # Fall back to a small set of common explicit formats.
    fallback_formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d",
    )
    for fmt in fallback_formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    raise RowError(f"unrecognized timestamp format: {raw!r}")


def parse_amount(raw: str) -> Decimal:
    """Parse a monetary amount as Decimal for exact, deterministic sums."""
    raw = raw.strip().replace(",", "")
    if raw == "":
        raise RowError("empty amount")
    try:
        return Decimal(raw)
    except InvalidOperation:
        raise RowError(f"unrecognized amount format: {raw!r}")


def load_rows(
    input_path: Path,
    customer_col: str,
    timestamp_col: str,
    status_col: str,
    amount_col: str,
    encoding: str,
    skip_invalid: bool,
):
    """
    Read the CSV and return a list of normalized row dicts:
        {"customer_id": str, "timestamp": datetime, "timestamp_raw": str,
         "status": str, "amount": Decimal, "row": original dict}
    Preserves original file order (required for deterministic
    "keep last occurrence" dedup).
    """
    rows = []
    warnings = []

    with input_path.open(newline="", encoding=encoding) as f:
        reader = csv.DictReader(f)

        required = {customer_col, timestamp_col, status_col, amount_col}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(
                f"Input CSV is missing required column(s): {sorted(missing)}. "
                f"Found columns: {reader.fieldnames}"
            )

        for line_num, raw_row in enumerate(reader, start=2):  # header is line 1
            try:
                customer_id = (raw_row.get(customer_col) or "").strip()
                if not customer_id:
                    raise RowError("empty customer_id")

                timestamp_raw = (raw_row.get(timestamp_col) or "").strip()
                timestamp = parse_timestamp(timestamp_raw)

                status = (raw_row.get(status_col) or "").strip()
                if not status:
                    raise RowError("empty status")

                amount = parse_amount(raw_row.get(amount_col) or "")

                rows.append(
                    {
                        "customer_id": customer_id,
                        "timestamp": timestamp,
                        "timestamp_raw": timestamp_raw,
                        "status": status,
                        "amount": amount,
                        "row": raw_row,
                    }
                )
            except RowError as exc:
                msg = f"line {line_num}: {exc}"
                if skip_invalid:
                    warnings.append(msg)
                    continue
                raise SystemExit(
                    f"Invalid data at {msg}. "
                    f"Re-run with --skip-invalid to skip bad rows instead."
                )

    return rows, warnings


def deduplicate_keep_last(rows):
    """
    Remove duplicate (customer_id, timestamp) records, keeping the LAST
    occurrence in file order. Returns a list in first-seen key order with
    values from the last occurrence (dict insertion order gives this for
    free: overwriting a key does not move its position).
    """
    dedup = {}
    for r in rows:
        key = (r["customer_id"], r["timestamp"])
        dedup[key] = r
    return list(dedup.values())


def select_latest_per_customer(rows):
    """
    From deduplicated rows, pick the chronologically latest record for
    each customer. Ties (identical parsed timestamp for the same
    customer, which can occur only if two differently-formatted
    timestamp strings parse to the same instant) are broken
    deterministically in favor of whichever record was encountered
    first in `rows`.
    """
    latest = {}
    for r in rows:
        cid = r["customer_id"]
        if cid not in latest or r["timestamp"] > latest[cid]["timestamp"]:
            latest[cid] = r
    return latest  # dict: customer_id -> row


def summarize_by_status(latest_records):
    """
    Compute count and total amount per status, using only the retained
    (one per customer) records.
    """
    summary = {}
    for r in latest_records.values():
        status = r["status"]
        bucket = summary.setdefault(status, {"count": 0, "total_amount": Decimal("0")})
        bucket["count"] += 1
        bucket["total_amount"] += r["amount"]
    return summary


def format_amount(d: Decimal) -> str:
    """Format a Decimal amount with exactly 2 decimal places."""
    return str(d.quantize(Decimal("0.01")))


def write_latest_by_customer(latest_records, output_path: Path):
    fieldnames = ["customer_id", "timestamp", "status", "amount"]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for cid in sorted(latest_records.keys()):
            r = latest_records[cid]
            writer.writerow(
                {
                    "customer_id": r["customer_id"],
                    "timestamp": r["timestamp"].isoformat(),
                    "status": r["status"],
                    "amount": format_amount(r["amount"]),
                }
            )


def write_status_summary(summary, output_path: Path):
    fieldnames = ["status", "count", "total_amount"]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for status in sorted(summary.keys()):
            bucket = summary[status]
            writer.writerow(
                {
                    "status": status,
                    "count": bucket["count"],
                    "total_amount": format_amount(bucket["total_amount"]),
                }
            )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Deduplicate customer events, pick each customer's latest "
        "record, and summarize counts/totals by status. Runs fully offline."
    )
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write output CSVs into (default: current directory)",
    )
    parser.add_argument("--customer-col", default="customer_id")
    parser.add_argument("--timestamp-col", default="timestamp")
    parser.add_argument("--status-col", default="status")
    parser.add_argument("--amount-col", default="amount")
    parser.add_argument("--encoding", default="utf-8")
    parser.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Skip rows with unparseable data instead of aborting",
    )
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows, warnings = load_rows(
        input_path,
        args.customer_col,
        args.timestamp_col,
        args.status_col,
        args.amount_col,
        args.encoding,
        args.skip_invalid,
    )

    for w in warnings:
        print(f"WARNING: skipped invalid row - {w}", file=sys.stderr)

    deduped = deduplicate_keep_last(rows)
    latest_records = select_latest_per_customer(deduped)
    summary = summarize_by_status(latest_records)

    latest_out = output_dir / "latest_by_customer.csv"
    summary_out = output_dir / "status_summary.csv"

    write_latest_by_customer(latest_records, latest_out)
    write_status_summary(summary, summary_out)

    print(f"Input rows read:              {len(rows)}")
    print(f"Rows skipped (invalid):       {len(warnings)}")
    print(f"Unique (customer, ts) pairs:  {len(deduped)}")
    print(f"Distinct customers:           {len(latest_records)}")
    print(f"Wrote: {latest_out}")
    print(f"Wrote: {summary_out}")


if __name__ == "__main__":
    main()