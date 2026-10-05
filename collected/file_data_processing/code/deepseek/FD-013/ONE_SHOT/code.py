import csv
import sys
from statistics import mean, median


def parse_number(value):
    """Try to parse a value as a float. Return None if not possible."""
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def compute_statistics(filepath):
    with open(filepath, newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print("Empty CSV file.")
            return

        # One bucket of numeric values per column
        columns = [[] for _ in header]

        for row in reader:
            for i in range(len(header)):
                if i < len(row):
                    num = parse_number(row[i])
                    if num is not None:
                        columns[i].append(num)

    # Report in input-column order
    for name, values in zip(header, columns):
        if values:
            print(f"Column: {name}")
            print(f"  Count:   {len(values)}")
            print(f"  Minimum: {min(values)}")
            print(f"  Maximum: {max(values)}")
            print(f"  Mean:    {mean(values)}")
            print(f"  Median:  {median(values)}")
        else:
            print(f"Column: {name}")
            print("  No numeric values found.")
        print()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python stats.py <file.csv>")
        sys.exit(1)
    compute_statistics(sys.argv[1])