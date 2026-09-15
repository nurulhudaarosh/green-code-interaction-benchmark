import csv
import io
import sys
from collections import defaultdict
from typing import Dict, List, Tuple


def process_sales_csv(csv_input: str) -> str:
    """Reads CSV data string, validates rows, aggregates sales data,

    and returns a sorted CSV string with total units, revenue,
    and weighted average unit price by (region, category).
    """
    # Key: (region, category) -> Value: [total_units, total_revenue]
    aggregated_data: Dict[Tuple[str, str], List[float]] = defaultdict(
        lambda: [0.0, 0.0]
    )

    reader = csv.DictReader(io.StringIO(csv_input.strip()))

    for row in reader:
        # Extract fields and normalize string inputs
        region = row.get("region", "").strip() if row.get("region") else ""
        category = (
            row.get("category", "").strip() if row.get("category") else ""
        )
        raw_units = row.get("units", "").strip() if row.get("units") else ""
        raw_price = (
            row.get("unit_price", "").strip() if row.get("unit_price") else ""
        )

        # Validate required text fields
        if not region or not category:
            continue

        # Validate numeric inputs (units must be integer > 0, price must be float > 0)
        try:
            units = int(raw_units)
            unit_price = float(raw_price)

            if units <= 0 or unit_price <= 0:
                continue
        except (ValueError, TypeError):
            continue

        # Accumulate totals
        revenue = units * unit_price
        aggregated_data[(region, category)][0] += units
        aggregated_data[(region, category)][1] += revenue

    # Write aggregated results to string buffer
    output_buffer = io.StringIO()
    writer = csv.writer(output_buffer)

    writer.writerow(
        [
            "region",
            "category",
            "total_units",
            "total_revenue",
            "weighted_avg_unit_price",
        ]
    )

    # Sort output primary by Region, secondary by Category
    sorted_keys = sorted(aggregated_data.keys(), key=lambda x: (x[0], x[1]))

    for region, category in sorted_keys:
        total_units, total_revenue = aggregated_data[(region, category)]
        weighted_avg_price = (
            total_revenue / total_units if total_units > 0 else 0.0
        )

        writer.writerow(
            [
                region,
                category,
                int(total_units),
                f"{total_revenue:.2f}",
                f"{weighted_avg_price:.2f}",
            ]
        )

    return output_buffer.getvalue()


def process_sales_files(input_filepath: str, output_filepath: str) -> None:
    """Reads input CSV file, processes sales aggregation, and writes output file."""
    with open(input_filepath, mode="r", encoding="utf-8") as infile:
        csv_data = infile.read()

    result_csv = process_sales_csv(csv_data)

    with open(output_filepath, mode="w", encoding="utf-8", newline="") as outfile:
        outfile.write(result_csv)


if __name__ == "__main__":
    # Standard usage demo with inline CSV string
    sample_csv_data = """region,category,units,unit_price
North,Electronics,10,100.00
North,Electronics,5,120.00
North,Clothing,20,15.00
South,Electronics,-5,50.00
South,Electronics,15,40.00
West,Home,abc,25.00
West,Home,8,25.00
,Clothing,10,20.00
South,Clothing,0,10.00
"""

    print("=== Aggregated CSV Output ===")
    print(process_sales_csv(sample_csv_data))