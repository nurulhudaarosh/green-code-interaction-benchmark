import csv
import sys
from statistics import median


def parse_number(value):
    """Try to parse a value as a float. Return None if not possible."""
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def compute_stats(values):
    """Compute statistics for a list of numeric values (already cleaned).

    Handles empty lists (all-missing columns) gracefully by returning
    None for each statistic instead of raising.
    """
    if not values:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
        }

    count = len(values)
    # min/max work fine with negatives and zeros.
    # mean = sum / count; count >= 1 here, so no ZeroDivisionError.
    # median handles negatives, zeros, and single-element lists.
    return {
        "count": count,
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / count,
        "median": median(values),
    }


def format_number(x):
    """Format a number nicely, or return 'N/A' for None."""
    if x is None:
        return "N/A"
    # Use integer formatting when the float is a whole number
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return f"{x:g}"


def analyze_csv(path, has_header=True):
    try:
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
    except FileNotFoundError:
        print(f"Error: file not found: {path}")
        return
    except OSError as e:
        print(f"Error reading file: {e}")
        return

    if not rows:
        print("Empty file. Nothing to analyze.")
        return

    if has_header:
        header = rows[0]
        data_rows = rows[1:]
    else:
        # Generate column names like col1, col2, ...
        num_cols = max((len(r) for r in rows), default=0)
        header = [f"col{i + 1}" for i in range(num_cols)]
        data_rows = rows

    num_cols = len(header)

    # If the header has no columns (e.g. a truly blank first line),
    # we can't produce meaningful stats.
    if num_cols == 0:
        print("No columns detected. Nothing to analyze.")
        return

    # Collect numeric values per column; skip missing/non-numeric entries.
    columns = [[] for _ in range(num_cols)]
    for row in data_rows:
        for i in range(num_cols):
            raw = row[i] if i < len(row) else None
            num = parse_number(raw)
            if num is not None:
                columns[i].append(num)

    # Compute statistics in input-column order.
    stats = [compute_stats(col) for col in columns]

    # Determine column width for nice printing.
    name_width = max((len(name) for name in header), default=len("Column"))
    name_width = max(name_width, len("Column"))

    print(f"{'Column':<{name_width}}  {'Count':>7}  {'Min':>12}  {'Max':>12}  "
          f"{'Mean':>12}  {'Median':>12}")
    print("-" * (name_width + 2 + 7 + 2 + 12 + 2 + 12 + 2 + 12 + 2 + 12))

    for name, s in zip(header, stats):
        # A column with no numeric values at all still prints cleanly.
        print(f"{name:<{name_width}}  {s['count']:>7}  "
              f"{format_number(s['min']):>12}  "
              f"{format_number(s['max']):>12}  "
              f"{format_number(s['mean']):>12}  "
              f"{format_number(s['median']):>12}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python csv_stats.py <file.csv> [--no-header]")
        sys.exit(1)

    path = sys.argv[1]
    has_header = "--no-header" not in sys.argv[2:]

    analyze_csv(path, has_header=has_header)


if __name__ == "__main__":
    main()