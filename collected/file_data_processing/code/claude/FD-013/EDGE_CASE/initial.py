#!/usr/bin/env python3
"""
csv_stats.py - Per-column CSV statistics utility.

Reports count, minimum, maximum, mean, and median for each numeric column,
in the same order the columns appear in the input. Missing values are handled
independently per column: a blank/NA cell in one column never causes the row
to be dropped from any other column's statistics.

Usage:
    python csv_stats.py data.csv
    python csv_stats.py data.csv --delimiter ";" --missing "-" "?" --format json
    cat data.csv | python csv_stats.py -
"""

import argparse
import csv
import json
import math
import statistics
import sys
from typing import Dict, List, Optional, Sequence

DEFAULT_MISSING = {"", "na", "n/a", "nan", "null", "none", "nil", "-", "--", "?"}


def parse_number(raw: str, missing: set) -> Optional[float]:
    """Return a float, or None if the cell is missing or non-numeric/non-finite."""
    if raw is None:
        return None
    text = raw.strip()
    if text.lower() in missing:
        return None
    try:
        value = float(text.replace(",", "")) if "," in text and "." in text else float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def compute_stats(path: str, delimiter: str, missing: set, has_header: bool) -> List[Dict]:
    """Stream the CSV once and return per-column stats in input-column order."""
    handle = sys.stdin if path == "-" else open(path, newline="", encoding="utf-8-sig")
    try:
        reader = csv.reader(handle, delimiter=delimiter)
        try:
            first = next(reader)
        except StopIteration:
            return []

        if has_header:
            names = [n.strip() or f"column_{i + 1}" for i, n in enumerate(first)]
            pending: List[Sequence[str]] = []
        else:
            names = [f"column_{i + 1}" for i in range(len(first))]
            pending = [first]

        n_cols = len(names)
        values: List[List[float]] = [[] for _ in range(n_cols)]
        missing_counts = [0] * n_cols
        non_numeric = [0] * n_cols

        def consume(row: Sequence[str]) -> None:
            if not row or all(not c.strip() for c in row) and n_cols > 1:
                # Entirely blank line: skip rather than count as missing everywhere.
                if not row:
                    return
            for i in range(n_cols):
                cell = row[i] if i < len(row) else None  # short rows => missing
                if cell is None or cell.strip().lower() in missing:
                    missing_counts[i] += 1
                    continue
                num = parse_number(cell, missing)
                if num is None:
                    non_numeric[i] += 1
                else:
                    values[i].append(num)

        for row in pending:
            consume(row)
        for row in reader:
            consume(row)
    finally:
        if handle is not sys.stdin:
            handle.close()

    results = []
    for i, name in enumerate(names):  # input-column order preserved
        col = values[i]
        entry = {
            "column": name,
            "count": len(col),
            "min": min(col) if col else None,
            "max": max(col) if col else None,
            "mean": statistics.fmean(col) if col else None,
            "median": statistics.median(col) if col else None,
            "missing": missing_counts[i],
            "non_numeric": non_numeric[i],
        }
        results.append(entry)
    return results


def fmt(value: Optional[float], precision: int) -> str:
    if value is None:
        return "-"
    if float(value).is_integer() and abs(value) < 1e15:
        return str(int(value))
    return f"{value:.{precision}f}"


def render_table(results: List[Dict], precision: int) -> str:
    headers = ["column", "count", "min", "max", "mean", "median"]
    rows = [
        [
            r["column"],
            str(r["count"]),
            fmt(r["min"], precision),
            fmt(r["max"], precision),
            fmt(r["mean"], precision),
            fmt(r["median"], precision),
        ]
        for r in results
    ]
    widths = [max(len(h), *(len(row[i]) for row in rows)) if rows else len(h)
              for i, h in enumerate(headers)]
    line = lambda cells: "  ".join(
        c.ljust(widths[i]) if i == 0 else c.rjust(widths[i]) for i, c in enumerate(cells)
    )
    out = [line(headers), line(["-" * w for w in widths])]
    out += [line(r) for r in rows]
    return "\n".join(out)


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Per-column CSV statistics.")
    p.add_argument("file", help="CSV file path, or '-' for stdin")
    p.add_argument("-d", "--delimiter", default=",", help="field delimiter (default: ,)")
    p.add_argument("--no-header", action="store_true", help="first row is data, not a header")
    p.add_argument("--missing", nargs="*", default=None,
                   help="extra tokens to treat as missing (case-insensitive)")
    p.add_argument("--format", choices=["table", "json", "csv"], default="table")
    p.add_argument("--precision", type=int, default=4, help="decimal places (default: 4)")
    args = p.parse_args(argv)

    missing = set(DEFAULT_MISSING)
    if args.missing:
        missing |= {m.strip().lower() for m in args.missing}

    try:
        results = compute_stats(args.file, args.delimiter, missing, not args.no_header)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2
    except (OSError, csv.Error, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not results:
        print("error: input is empty", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(results, indent=2))
    elif args.format == "csv":
        w = csv.writer(sys.stdout)
        w.writerow(["column", "count", "min", "max", "mean", "median"])
        for r in results:
            w.writerow([r["column"], r["count"], r["min"], r["max"], r["mean"], r["median"]])
    else:
        print(render_table(results, args.precision))

    # Note columns with no numeric data or with skipped non-numeric cells.
    for r in results:
        if r["count"] == 0:
            print(f"note: column '{r['column']}' has no numeric values", file=sys.stderr)
        elif r["non_numeric"]:
            print(f"note: column '{r['column']}' skipped {r['non_numeric']} non-numeric cell(s)",
                  file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())