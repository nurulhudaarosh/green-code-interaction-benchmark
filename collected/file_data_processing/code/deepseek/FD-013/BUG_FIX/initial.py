import csv
import sys
from statistics import median


def parse_number(value):
    """Try to parse a value as float. Return None for missing/invalid values."""
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def compute_column_stats(values):
    """Compute stats for a list of numeric values (missing already removed)."""
    n = len(values)
    if n == 0:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
        }
    return {
        "count": n,
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / n,
        "median": median(values),
    }


def format_number(x):
    """Format a number nicely, or return 'N/A' if None."""
    if x is None:
        return "N/A"
    # If it's effectively an integer, show as int
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return f"{x:.6g}"


def csv_stats(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print("Empty CSV file.")
            return

        num_cols = len(header)
        columns = [[] for _ in range(num_cols)]

        for row in reader:
            for i in range(num_cols):
                raw = row[i] if i < len(row) else ""
                val = parse_number(raw)
                if val is not None:
                    columns[i].append(val)

    # Report in input-column order
    for name, values in zip(header, columns):
        stats = compute_column_stats(values)
        print(f"Column: {name}")
        print(f"  Count:  {stats['count']}")
        print(f"  Min:    {format_number(stats['min'])}")
        print(f"  Max:    {format_number(stats['max'])}")
        print(f"  Mean:   {format_number(stats['mean'])}")
        print(f"  Median: {format_number(stats['median'])}")
        print()


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <file.csv>")
        sys.exit(1)
    csv_stats(sys.argv[1])


if __name__ == "__main__":
    main()