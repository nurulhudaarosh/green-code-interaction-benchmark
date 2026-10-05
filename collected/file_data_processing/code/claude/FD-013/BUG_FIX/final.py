#!/usr/bin/env python3
"""CSV statistics utility.

Reports count, min, max, mean, and median for every column, in input-column
order. Missing values are handled independently per column: a missing cell is
skipped only for its own column, and the rest of that row still contributes to
every other column.

Usage:
    python csv_stats.py data.csv
    python csv_stats.py data.csv --delimiter ";" --no-header
    cat data.csv | python csv_stats.py -
"""

import argparse
import csv
import math
import re
import statistics
import sys
from typing import List, Optional, TextIO

MISSING_TOKENS = {"", "na", "n/a", "nan", "null", "none", "-"}
THOUSANDS_RE = re.compile(r"^[+-]?\d{1,3}(,\d{3})+(\.\d+)?$")


class ColumnStats:
    """Accumulates values for a single column, independent of all others."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.values: List[float] = []
        self.missing = 0
        self.non_numeric = 0

    def add(self, cell: Optional[str]) -> None:
        if cell is None or cell.strip().lower() in MISSING_TOKENS:
            self.missing += 1
            return
        number = parse_number(cell)
        if number is None:
            self.non_numeric += 1
        else:
            self.values.append(number)

    def summary(self) -> dict:
        v = self.values
        return {
            "column": self.name,
            "count": len(v),
            "min": min(v) if v else None,
            "max": max(v) if v else None,
            "mean": statistics.fmean(v) if v else None,
            "median": statistics.median(v) if v else None,
            "missing": self.missing,
            "non_numeric": self.non_numeric,
        }


def parse_number(cell: str) -> Optional[float]:
    """Parse a finite float (allowing 1,234.5 style separators) or return None."""
    text = cell.strip()
    if THOUSANDS_RE.match(text):
        text = text.replace(",", "")
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def compute_stats(rows, has_header: bool) -> List[dict]:
    """Process rows one at a time; each cell goes only to its own column."""
    rows = iter(rows)
    try:
        first = next(rows)
    except StopIteration:
        return []

    columns: List[ColumnStats] = []
    if has_header:
        columns = [ColumnStats(n.strip() or f"column_{i + 1}") for i, n in enumerate(first)]
        pending = []
    else:
        columns = [ColumnStats(f"column_{i + 1}") for i in range(len(first))]
        pending = [first]

    def ingest(row: List[str]) -> None:
        # A row wider than the header adds new columns (appended in order).
        while len(row) > len(columns):
            columns.append(ColumnStats(f"column_{len(columns) + 1}"))
        for i, col in enumerate(columns):
            # Short rows count as missing for the absent trailing columns.
            col.add(row[i] if i < len(row) else None)

    for row in pending:
        ingest(row)
    for row in rows:
        if row:  # skip completely blank lines only
            ingest(row)

    return [c.summary() for c in columns]


def fmt(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value:.6g}"


def print_report(results: List[dict], out: TextIO) -> None:
    if not results:
        out.write("No data found.\n")
        return
    headers = ["column", "count", "min", "max", "mean", "median", "missing", "non_numeric"]
    table = [headers]
    for r in results:
        table.append([
            r["column"], str(r["count"]), fmt(r["min"]), fmt(r["max"]),
            fmt(r["mean"]), fmt(r["median"]), str(r["missing"]), str(r["non_numeric"]),
        ])
    widths = [max(len(row[c]) for row in table) for c in range(len(headers))]
    for n, row in enumerate(table):
        out.write("  ".join(
            cell.ljust(widths[c]) if c == 0 else cell.rjust(widths[c])
            for c, cell in enumerate(row)
        ).rstrip() + "\n")
        if n == 0:
            out.write("  ".join("-" * w for w in widths) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Per-column CSV statistics (count, min, max, mean, median)."
    )
    parser.add_argument("path", help="CSV file path, or '-' for stdin")
    parser.add_argument("-d", "--delimiter", default=",", help="field delimiter (default: ,)")
    parser.add_argument("--no-header", action="store_true", help="input has no header row")
    parser.add_argument("--encoding", default="utf-8-sig", help="file encoding (default: utf-8-sig)")
    args = parser.parse_args()

    try:
        if args.path == "-":
            reader = csv.reader(sys.stdin, delimiter=args.delimiter)
            results = compute_stats(reader, has_header=not args.no_header)
        else:
            with open(args.path, newline="", encoding=args.encoding) as f:
                reader = csv.reader(f, delimiter=args.delimiter)
                results = compute_stats(reader, has_header=not args.no_header)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print_report(results, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())