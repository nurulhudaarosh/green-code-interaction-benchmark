#!/usr/bin/env python3
"""
Access Log to CSV Converter

Parses Apache/Nginx combined-format access logs and exports to CSV,
adding a `statusClass` column derived from the HTTP status code.

Usage:
    python log_to_csv.py input.log output.csv
    cat access.log | python log_to_csv.py - output.csv
    python log_to_csv.py access.log  # prints to stdout
"""

import argparse
import csv
import re
import sys
from datetime import datetime


# Apache/Nginx "combined" log format:
# 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 "http://ref/" "Mozilla/4.08 [en]"
LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+)\s+'              # client IP
    r'(?P<ident>\S+)\s+'            # ident (usually -)
    r'(?P<user>\S+)\s+'             # remote user
    r'\[(?P<time>[^\]]+)\]\s+'      # timestamp
    r'"(?P<request>[^"]*)"\s+'      # request line
    r'(?P<status>\d{3})\s+'         # status code
    r'(?P<size>\S+)'                # response size
    r'(?:\s+"(?P<referer>[^"]*)")?' # referer
    r'(?:\s+"(?P<agent>[^"]*)")?'   # user agent
)

CSV_FIELDS = [
    "ip", "ident", "user", "time", "method", "path", "protocol",
    "status", "statusClass", "size", "referer", "agent"
]


def status_class(status: int) -> str:
    """Map HTTP status code to its class (1xx..5xx)."""
    if 100 <= status <= 599:
        return f"{status // 100}xx"
    return "unknown"


def parse_timestamp(ts: str) -> str:
    """Convert Apache timestamp to ISO 8601. Falls back to original on error."""
    try:
        dt = datetime.strptime(ts, "%d/%b/%Y:%H:%M:%S %z")
        return dt.isoformat()
    except ValueError:
        return ts


def parse_line(line: str) -> dict | None:
    """Parse a single log line into a dict, or None if it doesn't match."""
    match = LOG_PATTERN.match(line.strip())
    if not match:
        return None

    data = match.groupdict()

    # Split the request line into method / path / protocol
    request = data.get("request") or ""
    parts = request.split(" ", 2)
    method = parts[0] if len(parts) > 0 else ""
    path = parts[1] if len(parts) > 1 else ""
    protocol = parts[2] if len(parts) > 2 else ""

    try:
        status_int = int(data["status"])
    except (TypeError, ValueError):
        status_int = 0

    return {
        "ip": data["ip"],
        "ident": data["ident"],
        "user": data["user"],
        "time": parse_timestamp(data["time"]),
        "method": method,
        "path": path,
        "protocol": protocol,
        "status": status_int,
        "statusClass": status_class(status_int),
        "size": data["size"],
        "referer": data.get("referer") or "",
        "agent": data.get("agent") or "",
    }


def convert(infile, outfile, skip_invalid: bool = True) -> tuple[int, int]:
    """Convert log file to CSV. Returns (written, skipped) counts."""
    written = 0
    skipped = 0

    writer = csv.DictWriter(outfile, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()

    for lineno, line in enumerate(infile, 1):
        if not line.strip():
            continue
        row = parse_line(line)
        if row is None:
            skipped += 1
            if not skip_invalid:
                print(f"Warning: could not parse line {lineno}: {line.rstrip()}",
                      file=sys.stderr)
            continue
        writer.writerow(row)
        written += 1

    return written, skipped


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert access logs to CSV with a statusClass column."
    )
    parser.add_argument("input", help="Input log file, or '-' for stdin")
    parser.add_argument("output", nargs="?", default="-",
                        help="Output CSV file, or '-' for stdout (default)")
    parser.add_argument("--strict", action="store_true",
                        help="Warn on unparseable lines")
    args = parser.parse_args(argv)

    # Open input
    if args.input == "-":
        infile = sys.stdin
        close_in = False
    else:
        infile = open(args.input, "r", encoding="utf-8", errors="replace")
        close_in = True

    # Open output
    if args.output == "-":
        outfile = sys.stdout
        close_out = False
    else:
        outfile = open(args.output, "w", encoding="utf-8", newline="")
        close_out = True

    try:
        written, skipped = convert(infile, outfile, skip_invalid=not args.strict)
    finally:
        if close_in:
            infile.close()
        if close_out:
            outfile.close()

    print(f"Wrote {written} rows, skipped {skipped} unparseable lines.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())