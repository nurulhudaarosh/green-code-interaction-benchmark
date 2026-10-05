import csv
import math
import statistics
import sys
from typing import Dict, List, Union


def is_missing(val: str) -> bool:
    """Check if a string cell value represents a missing entry."""
    val_clean = val.strip()
    return val_clean == "" or val_clean.lower() in {"na", "n/a", "null", "none", "nan"}


def calculate_column_stats(filepath: str) -> None:
    """
    Reads a CSV file, calculates statistics (count, min, max, mean, median)
    for numeric columns independently handling missing values, and prints
    the results in the original input-column order.
    """
    with open(filepath, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            print("CSV file is empty.")
            return

        # Preserve order with lists per column index
        columns_data: List[List[float]] = [[] for _ in headers]

        for row in reader:
            for idx, cell in enumerate(row):
                if idx >= len(headers):
                    continue  # Ignore extra columns beyond headers
                if not is_missing(cell):
                    try:
                        val = float(cell)
                        if not math.isnan(val):
                            columns_data[idx].append(val)
                    except ValueError:
                        # Skip non-numeric non-missing strings
                        pass

    # Print results in original column order
    print(f"{'Column':<20} {'Count':<8} {'Min':<12} {'Max':<12} {'Mean':<12} {'Median':<12}")
    print("-" * 76)

    for header, data in zip(headers, columns_data):
        if not data:
            print(f"{header:<20} {0:<8} {'N/A':<12} {'N/A':<12} {'N/A':<12} {'N/A':<12}")
            continue

        count = len(data)
        col_min = min(data)
        col_max = max(data)
        col_mean = statistics.mean(data)
        col_median = statistics.median(data)

        print(
            f"{header:<20} {count:<8} {col_min:<12.4g} {col_max:<12.4g} {col_mean:<12.4g} {col_median:<12.4g}"
        )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        calculate_column_stats(sys.argv[1])
    else:
        print("Usage: python csv_stats.py <path_to_csv>")