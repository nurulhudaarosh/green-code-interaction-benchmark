import csv
import math
import sys
from statistics import median


def compute_stats(values):
    """Compute count, min, max, mean, median for a list of numeric values."""
    n = len(values)
    if n == 0:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None}
    return {
        "count": n,
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / n,
        "median": median(values),
    }


def parse_number(raw):
    """Parse a raw CSV cell as a float. Return None if missing or invalid."""
    if raw is None:
        return None
    s = raw.strip()
    if s == "":
        return None
    if s.lower() in {"na", "n/a", "nan", "null", "none", "-", "--"}:
        return None
    try:
        val = float(s)
    except ValueError:
        return None
    if math.isnan(val) or math.isinf(val):
        return None
    return val


def csv_stats(path, has_header=True):
    """Compute per-column statistics. Missing values are handled independently
    per column and results are returned in input-column order."""
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    if not rows:
        return []

    if has_header:
        header = rows[0]
        data_rows = rows[1:]
    else:
        header = [f"col_{i}" for i in range(len(rows[0]))]
        data_rows = rows

    num_cols = len(header)
    columns = [[] for _ in range(num_cols)]

    for row in data_rows:
        for i in range(num_cols):
            raw = row[i] if i < len(row) else None
            val = parse_number(raw)
            if val is not None:
                columns[i].append(val)

    results = []
    for name, values in zip(header, columns):
        stats = compute_stats(values)
        stats["column"] = name
        results.append(stats)
    return results


def print_stats(results):
    """Pretty-print per-column statistics."""
    if not results:
        print("No columns found.")
        return

    name_w = max(len("column"), max(len(r["column"]) for r in results))
    fmt = f"{{:<{name_w}}}  {{:>8}}  {{:>12}}  {{:>12}}  {{:>14}}  {{:>14}}"

    print(fmt.format("column", "count", "min", "max", "mean", "median"))
    print("-" * (name_w + 2 + 8 + 2 + 12 + 2 + 12 + 2 + 14 + 2 + 14))

    for r in results:
        def f(x):
            return "n/a" if x is None else f"{x:.6g}"
        print(fmt.format(r["column"], r["count"], f(r["min"]), f(r["max"]),
                         f(r["mean"]), f(r["median"])))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python csv_stats.py <file.csv> [--no-header]")
        sys.exit(1)

    path = sys.argv[1]
    has_header = "--no-header" not in sys.argv[2:]
    print_stats(csv_stats(path, has_header=has_header))