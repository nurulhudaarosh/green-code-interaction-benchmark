import csv
import math
from typing import Dict, List, Optional, Union


def compute_column_stats(
    values: List[float],
) -> Dict[str, Optional[Union[int, float]]]:
    """Computes count, min, max, mean, and median for a list of numeric values."""
    count = len(values)
    if count == 0:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
        }

    sorted_vals = sorted(values)
    min_val = sorted_vals[0]
    max_val = sorted_vals[-1]
    mean_val = sum(sorted_vals) / count

    # Compute median
    mid = count // 2
    if count % 2 == 1:
        median_val = sorted_vals[mid]
    else:
        median_val = (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0

    return {
        "count": count,
        "min": min_val,
        "max": max_val,
        "mean": mean_val,
        "median": median_val,
    }


def analyze_csv(
    filepath: str,
    missing_values: Optional[set] = None,
) -> Dict[str, Dict[str, Optional[Union[int, float]]]]:
    """Reads a CSV file and calculates statistics for each numeric column independently,

    preserving input column order. Missing/non-numeric values are skipped per
    column.
    """
    if missing_values is None:
        missing_values = {"", "NA", "N/A", "null", "None", "nan", "NaN"}

    with open(filepath, mode="r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)

        try:
            headers = next(reader)
        except StopIteration:
            return {}

        # Dictionary maintaining insertion order (Python 3.7+)
        column_data: Dict[str, List[float]] = {
            header.strip(): [] for header in headers
        }

        for row in reader:
            for header, val in zip(headers, row):
                clean_header = header.strip()
                val_str = val.strip()

                if val_str in missing_values:
                    continue

                try:
                    numeric_val = float(val_str)
                    if not math.isnan(numeric_val):
                        column_data[clean_header].append(numeric_val)
                except ValueError:
                    # Skip non-numeric entries (e.g., text values)
                    continue

    results = {}
    for header, values in column_data.items():
        results[header] = compute_column_stats(values)

    return results


def print_stats_table(
    stats: Dict[str, Dict[str, Optional[Union[int, float]]]]
) -> None:
    """Prints calculated statistics in a clean tabular format."""
    if not stats:
        print("No data or columns found.")
        return

    headers = ["Column", "Count", "Min", "Max", "Mean", "Median"]
    print(
        f"{headers[0]:<20} {headers[1]:>8} {headers[2]:>12} {headers[3]:>12} {headers[4]:>12} {headers[5]:>12}"
    )
    print("-" * 78)

    for col, col_stats in stats.items():
        count = str(col_stats["count"])
        min_v = (
            f"{col_stats['min']:.4g}" if col_stats["min"] is not None else "N/A"
        )
        max_v = (
            f"{col_stats['max']:.4g}" if col_stats["max"] is not None else "N/A"
        )
        mean_v = (
            f"{col_stats['mean']:.4g}"
            if col_stats["mean"] is not None
            else "N/A"
        )
        med_v = (
            f"{col_stats['median']:.4g}"
            if col_stats["median"] is not None
            else "N/A"
        )

        print(
            f"{col:<20} {count:>8} {min_v:>12} {max_v:>12} {mean_v:>12} {med_v:>12}"
        )


if __name__ == "__main__":
    import tempfile

    # Example usage with sample CSV data containing missing values and mixed types
    sample_csv_content = """Age, Score, Income, Category
25, 88.5, 50000, A
30, NA, 62000, B
, 92.0, , A
22, 79.5, 48000, B
35, 95.0, N/A, C
40, , 75000, A
"""

    with tempfile.NamedTemporaryFile(
        mode="w+", delete=False, suffix=".csv"
    ) as tmp:
        tmp.write(sample_csv_content)
        tmp_path = tmp.name

    results = analyze_csv(tmp_path)
    print_stats_table(results)