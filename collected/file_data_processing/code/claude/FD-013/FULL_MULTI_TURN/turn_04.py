#!/usr/bin/env python3
"""
csv_stats.py - Per-column statistics for CSV files.

Reports count, minimum, maximum, mean, and median for every column, in the
same order the columns appear in the input.

Missing values are handled independently per column: a blank/NA cell in one
column never discards the row for any other column. Example:

    a,b
    1,10
    ,20      <- 'a' is missing here, but 20 still counts toward 'b'
    3,

    a: count=2 (1, 3)    b: count=2 (10, 20)

Edge cases (none of these crash):
  * A column that is entirely missing (or has no numeric values) reports
    count=0 and "-" for min/max/mean/median (null in JSON, blank in CSV).
  * Negative values and zeros are ordinary values and are included normally.
    (A lone "-" is a missing-value marker; "-5" is the number -5.)
  * A header-only file yields count=0 for every column.
  * Extremely large values cannot overflow the mean or median computation.

Median: computed per column over that column's own valid values.
Odd count  -> the middle value.
Even count -> the average of the two middle values.

Usage:
    python csv_stats.py data.csv
    python csv_stats.py data.csv --delimiter ";" --missing "N/A" "-" --format json
    cat data.csv | python csv_stats.py -
    python csv_stats.py --selftest
"""

import argparse
import csv
import io
import json
import math
import sys
from typing import Dict, Iterable, List, Optional, Sequence

DEFAULT_MISSING = ["", "na", "n/a", "nan", "null", "none", "nil", "-", "--", "?"]


def _has_thousands_commas(text: str) -> bool:
    """Detect values like '1,234,567.89' or '-1,234'."""
    if "," not in text:
        return False
    head = text.partition(".")[0]
    parts = head.lstrip("+-").split(",")
    return (
        all(p.isdigit() for p in parts)
        and 1 <= len(parts[0]) <= 3
        and all(len(p) == 3 for p in parts[1:])
    )


def parse_number(raw: Optional[str], missing: set) -> Optional[float]:
    """Return a finite float, or None if the cell is missing/non-numeric.

    Negative numbers and zeros are valid. Negative zero is normalized to 0.0.
    """
    if raw is None:
        return None
    text = raw.strip()
    if text.lower() in missing:
        return None
    try:
        value = float(text.replace(",", "")) if _has_thousands_commas(text) else float(text)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return value + 0.0  # turns -0.0 into 0.0


def median_of(values: Sequence[float]) -> Optional[float]:
    """Median of a list of numbers; None if the list is empty."""
    n = len(values)
    if n == 0:
        return None
    ordered = sorted(values)
    mid = n // 2
    if n % 2 == 1:
        return ordered[mid]
    # a/2 + b/2 avoids overflow when both middle values are near the float max
    return ordered[mid - 1] / 2 + ordered[mid] / 2


def mean_of(values: Sequence[float]) -> Optional[float]:
    """Arithmetic mean; None if empty. Safe against float overflow."""
    n = len(values)
    if n == 0:
        return None
    try:
        return math.fsum(values) / n
    except OverflowError:
        return math.fsum(v / n for v in values)


def compute_stats(
    rows: Iterable[Sequence[str]],
    header: List[str],
    missing: set,
) -> List[Dict[str, object]]:
    """Accumulate values per column independently, then compute statistics.

    Every cell is judged on its own. A missing or invalid cell only skips
    that one column's accumulator; the other cells in the row are still used.
    """
    columns: List[List[float]] = [[] for _ in header]
    non_numeric = [0] * len(header)

    for row in rows:
        for idx in range(len(header)):
            cell = row[idx] if idx < len(row) else ""  # short row -> missing cell
            value = parse_number(cell, missing)
            if value is not None:
                columns[idx].append(value)
            elif cell.strip().lower() not in missing:
                non_numeric[idx] += 1  # has content, but not a usable number

    results = []
    for idx, name in enumerate(header):
        values = columns[idx]
        has_data = len(values) > 0  # test the list, never a statistic (0 is valid)
        entry: Dict[str, object] = {
            "column": name,
            "count": len(values),
            "min": min(values) if has_data else None,
            "max": max(values) if has_data else None,
            "mean": mean_of(values),
            "median": median_of(values),
        }
        if non_numeric[idx]:
            entry["non_numeric_skipped"] = non_numeric[idx]
        results.append(entry)
    return results


def fmt(value: object, precision: int) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        if value == int(value) and abs(value) < 1e15:
            return str(int(value))
        text = f"{value:.{max(precision, 0)}f}"
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return "0" if text in ("", "-0") else text
    return str(value)


COLUMNS = ["column", "count", "min", "max", "mean", "median"]


def render_table(results: List[Dict[str, object]], precision: int) -> str:
    table = [COLUMNS] + [[fmt(r[h], precision) for h in COLUMNS] for r in results]
    widths = [max(len(row[i]) for row in table) for i in range(len(COLUMNS))]

    def line(row: List[str]) -> str:
        cells = [row[0].ljust(widths[0])]
        cells += [c.rjust(widths[i]) for i, c in enumerate(row[1:], start=1)]
        return "  ".join(cells)

    out = [line(table[0]), "  ".join("-" * w for w in widths)]
    out.extend(line(r) for r in table[1:])

    notes = [r for r in results if r.get("non_numeric_skipped")]
    if notes:
        out.append("")
        for r in notes:
            out.append(
                f"note: column '{r['column']}' had {r['non_numeric_skipped']} "
                f"non-numeric value(s) that were ignored"
            )
    return "\n".join(out)


def render_csv(results: List[Dict[str, object]], precision: int) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(COLUMNS)
    for r in results:
        writer.writerow(
            [r["column"], r["count"]]
            + ["" if r[k] is None else fmt(r[k], precision) for k in COLUMNS[2:]]
        )
    return buf.getvalue().rstrip("\n")


def analyze(handle, delimiter: str, missing: set, no_header: bool) -> List[Dict[str, object]]:
    reader = csv.reader(handle, delimiter=delimiter)
    try:
        first = next(reader)
    except StopIteration:
        raise ValueError("input is empty")

    if no_header:
        header = [f"col{i + 1}" for i in range(len(first))]
        rows: Iterable[Sequence[str]] = _chain(first, reader)
    else:
        header = [h.strip() or f"col{i + 1}" for i, h in enumerate(first)]
        rows = reader
    return compute_stats(rows, header, missing)


def _chain(first: Sequence[str], rest: Iterable[Sequence[str]]):
    yield first
    yield from rest


def _run(text: str) -> Dict[str, Dict[str, object]]:
    res = analyze(io.StringIO(text), ",", set(DEFAULT_MISSING), False)
    return {r["column"]: r for r in res}


def selftest() -> int:
    # --- per-column missing handling, odd/even medians -------------------
    data = "a,b,c,d\n1,10,x,2\n,20,,4\n3,,,6\n5,30,,8\n"
    res = analyze(io.StringIO(data), ",", set(DEFAULT_MISSING), False)
    by = {r["column"]: r for r in res}
    assert [r["column"] for r in res] == ["a", "b", "c", "d"]
    a, b, c, d = (by[k] for k in "abcd")
    assert (a["count"], a["min"], a["max"], a["mean"], a["median"]) == (3, 1, 5, 3, 3)
    assert (b["count"], b["min"], b["max"], b["mean"], b["median"]) == (3, 10, 30, 20, 20)
    assert c["count"] == 0 and c["median"] is None and c["non_numeric_skipped"] == 1
    assert (d["count"], d["min"], d["max"], d["mean"], d["median"]) == (4, 2, 8, 5, 5)

    # --- negatives, zeros, negative zero, and an entirely missing column --
    e = _run("neg,zero,negzero,empty,text\n-5,0,-0,,x\n-3,0,0,NA,y\n-1,0,0.0,-,\n")
    assert (e["neg"]["count"], e["neg"]["min"], e["neg"]["max"]) == (3, -5, -1)
    assert (e["neg"]["mean"], e["neg"]["median"]) == (-3, -3)
    assert (e["zero"]["count"], e["zero"]["min"], e["zero"]["max"]) == (3, 0, 0)
    assert e["zero"]["mean"] == 0 and e["zero"]["median"] == 0
    assert repr(e["negzero"]["min"]) == "0.0"  # never "-0.0"
    for name in ("empty", "text"):
        col = e[name]
        assert col["count"] == 0
        assert col["min"] is col["max"] is col["mean"] is col["median"] is None
    assert e["text"]["non_numeric_skipped"] == 2

    # --- header-only file, short rows, blank lines ------------------------
    h = _run("p,q\n")
    assert h["p"]["count"] == 0 and h["q"]["median"] is None
    s = _run("p,q\n1\n\n2,5\n")
    assert s["p"]["count"] == 2 and s["q"]["count"] == 1

    # --- overflow safety ---------------------------------------------------
    o = _run("x\n1e308\n1e308\n")["x"]
    assert o["mean"] == 1e308 and o["median"] == 1e308

    # --- formatting edge cases --------------------------------------------
    assert fmt(-0.00001, 4) == "0"
    assert fmt(10.4, 0) == "10"
    assert fmt(float("inf"), 4) == "inf"
    assert median_of([]) is None and median_of([7]) == 7
    assert median_of([3, 1, 2]) == 2 and median_of([4, 1, 3, 2]) == 2.5

    print("selftest passed\n")
    print(render_table(res, 4))
    print()
    print(render_table(list(e.values()), 4))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Per-column count/min/max/mean/median for a CSV file; "
        "missing values are handled independently per column."
    )
    parser.add_argument("file", nargs="?", help="CSV file path, or '-' for stdin")
    parser.add_argument("-d", "--delimiter", default=",", help="field delimiter (default: ,)")
    parser.add_argument("--encoding", default="utf-8-sig", help="file encoding (default: utf-8-sig)")
    parser.add_argument(
        "-m", "--missing", nargs="+", default=None,
        help="extra strings to treat as missing (case-insensitive), added to the defaults: "
        + ", ".join(repr(m) for m in DEFAULT_MISSING),
    )
    parser.add_argument("--no-header", action="store_true",
                        help="input has no header row; columns are named col1, col2, ...")
    parser.add_argument("-p", "--precision", type=int, default=4, help="decimal places (default: 4)")
    parser.add_argument("-f", "--format", choices=["table", "csv", "json"], default="table",
                        help="output format (default: table)")
    parser.add_argument("--selftest", action="store_true",
                        help="verify missing-value handling, edge cases, and all statistics")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.file:
        parser.error("the following arguments are required: file")

    missing = set(DEFAULT_MISSING)
    if args.missing:
        missing.update(m.strip().lower() for m in args.missing)

    try:
        handle = sys.stdin if args.file == "-" else open(args.file, newline="", encoding=args.encoding)
    except OSError as exc:
        print(f"error: cannot open {args.file}: {exc}", file=sys.stderr)
        return 1

    try:
        with handle:
            results = analyze(handle, args.delimiter, missing, args.no_header)
    except (ValueError, UnicodeDecodeError, csv.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    precision = max(args.precision, 0)
    if args.format == "json":
        print(json.dumps(results, indent=2))
    elif args.format == "csv":
        print(render_csv(results, precision))
    else:
        print(render_table(results, precision))
    return 0


if __name__ == "__main__":
    sys.exit(main())