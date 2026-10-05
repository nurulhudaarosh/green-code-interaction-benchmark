#!/usr/bin/env python3
"""
csv_stats.py - Per-column statistics for CSV files.

For each column, reports count, minimum, maximum, mean, and median.
Missing values are handled independently per column: a missing cell in one
column never causes the row to be dropped for any other column.
Columns are reported in the same order as in the input file.

Usage:
    python csv_stats.py data.csv
    python csv_stats.py data.csv --delimiter ";" --missing "N/A" --missing "-"
    cat data.csv | python csv_stats.py -
"""

import argparse
import csv
import math
import statistics
import sys
from typing import Dict, List, Optional, Sequence, Set

DEFAULT_MISSING = {"", "na", "n/a", "nan", "null", "none", "nil", "?", "-"}


def parse_number(raw: str, missing: Set[str]) -> Optional[float]:
    """Return a float for a valid numeric cell, or None if missing/non-numeric/non-finite."""
    if raw is None:
        return None
    text = raw.strip()
    if text.lower() in missing:
        return None
    try:
        value = float(text.replace(",", "")) if "," in text and "." not in text.split(",")[-1] and False else float(text)
    except ValueError:
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return value


def compute_stats(
    rows: Sequence[Sequence[str]],
    header: List[str],
    missing: Set[str],
) -> List[Dict[str, object]]:
    """Compute stats per column, independently handling missing values."""
    results = []
    for idx, name in enumerate(header):
        values: List[float] = []
        missing_count = 0
        invalid_count = 0
        for row in rows:
            raw = row[idx] if idx < len(row) else ""  # short rows count as missing
            if raw.strip().lower() in missing:
                missing_count += 1
                continue
            num = parse_number(raw, missing)
            if num is None:
                invalid_count += 1
            else:
                values.append(num)

        entry: Dict[str, object] = {
            "column": name,
            "count": len(values),
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "mean": statistics.fmean(values) if values else None,
            "median": statistics.median(values) if values else None,
            "missing": missing_count,
            "invalid": invalid_count,
        }
        results.append(entry)
    return results


def fmt(value: Optional[float], precision: int) -> str:
    if value is None:
        return "-"
    if float(value).is_integer() and abs(value) < 1e15:
        return str(int(value))
    return f"{value:.{precision}f}"


def print_table(results: List[Dict[str, object]], precision: int, show_skipped: bool) -> None:
    headers = ["column", "count", "min", "max", "mean", "median"]
    if show_skipped:
        headers += ["missing", "invalid"]

    table = []
    for r in results:
        row = [
            str(r["column"]),
            str(r["count"]),
            fmt(r["min"], precision),
            fmt(r["max"], precision),
            fmt(r["mean"], precision),
            fmt(r["median"], precision),
        ]
        if show_skipped:
            row += [str(r["missing"]), str(r["invalid"])]
        table.append(row)

    widths = [max(len(h), *(len(row[i]) for row in table)) if table else len(h)
              for i, h in enumerate(headers)]

    def line(cells: List[str]) -> str:
        first = cells[0].ljust(widths[0])
        rest = [c.rjust(widths[i + 1]) for i, c in enumerate(cells[1:])]
        return "  ".join([first] + rest)

    print(line(headers))
    print("  ".join("-" * w for w in widths))
    for row in table:
        print(line(row))


def read_csv(path: str, delimiter: str, encoding: str):
    handle = sys.stdin if path == "-" else open(path, newline="", encoding=encoding)
    try:
        reader = csv.reader(handle, delimiter=delimiter)
        try:
            header = [h.strip() for h in next(reader)]
        except StopIteration:
            raise ValueError("input is empty")
        rows = [row for row in reader if any(cell.strip() for cell in row)]
    finally:
        if handle is not sys.stdin:
            handle.close()
    return header, rows


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Per-column CSV statistics.")
    parser.add_argument("file", help="CSV file path, or '-' for stdin")
    parser.add_argument("-d", "--delimiter", default=",", help="field delimiter (default ',')")
    parser.add_argument("-e", "--encoding", default="utf-8-sig", help="file encoding (default utf-8-sig)")
    parser.add_argument("-m", "--missing", action="append", default=None,
                        help="extra token to treat as missing (repeatable, case-insensitive)")
    parser.add_argument("-p", "--precision", type=int, default=4, help="decimal places (default 4)")
    parser.add_argument("--show-skipped", action="store_true",
                        help="also show missing and invalid (non-numeric) cell counts")
    parser.add_argument("--json", action="store_true", help="output JSON instead of a table")
    args = parser.parse_args(argv)

    missing = set(DEFAULT_MISSING)
    if args.missing:
        missing.update(m.strip().lower() for m in args.missing)

    try:
        header, rows = read_csv(args.file, args.delimiter, args.encoding)
    except (OSError, ValueError, csv.Error, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    results = compute_stats(rows, header, missing)

    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        print_table(results, args.precision, args.show_skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())