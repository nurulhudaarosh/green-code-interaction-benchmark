import csv
import io
from collections import defaultdict
from typing import Dict, List, Tuple


def process_sales_csv(csv_input: str) -> str:
    """Reads CSV data string, skips invalid/malformed rows, aggregates sales data,

    and returns a sorted CSV string with total units, revenue,
    and weighted average unit price by (region, category).
    """
    # Key: (region, category) -> Value: [total_units, total_revenue]
    aggregated_data: Dict[Tuple[str, str], List[float]] = defaultdict(
        lambda: [0.0, 0.0]
    )

    reader = csv.DictReader(io.StringIO(csv_input.strip()))

    for row in reader:
        # 1. Safely extract string fields
        region = row.get("region", "")
        category = row.get("category", "")

        # Skip missing or empty region/category
        if not region or not category:
            continue

        region = region.strip()
        category = category.strip()

        if not region or not category:
            continue

        # 2. Validate and convert numeric fields (skip row if conversion fails)
        try:
            raw_units = row.get("units")
            raw_price = row.get("unit_price")

            # Check for None/empty strings explicitly before casting
            if raw_units is None or raw_price is None:
                continue

            # Strict float conversion catches "NaN", "Infinity", whitespace strings, etc.
            units_float = float(raw_units.strip())
            price_float = float(raw_price.strip())

            # Verify units is a valid whole integer
            if not units_float.is_integer():
                continue

            units = int(units_float)
            unit_price = price_float

            # Reject zero or negative values
            if units <= 0 or unit_price <= 0:
                continue

        except (ValueError, TypeError, OverflowError, AttributeError):
            # Skip any row with malformed numeric data
            continue

        # 3. Accumulate valid totals
        revenue = units * unit_price
        aggregated_data[(region, category)][0] += units
        aggregated_data[(region, category)][1] += revenue

    # Build output CSV
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
    # Test suite with various malformed numeric inputs
    sample_csv_data = """region,category,units,unit_price
North,Electronics,10,100.00
North,Electronics,5,120.00
North,Clothing,20,15.00
South,Electronics,invalid_num,50.00
South,Electronics,15,N/A
West,Home,12.5,25.00
West,Home,8,25.00
East,Office,,45.00
East,Office,10,
South,Clothing,-5,10.00
"""

    print("=== Aggregated CSV Output ===")
    print(process_sales_csv(sample_csv_data))