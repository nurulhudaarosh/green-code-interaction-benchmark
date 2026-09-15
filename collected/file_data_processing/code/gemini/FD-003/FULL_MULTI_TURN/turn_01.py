import csv
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Tuple


def parse_and_clean_row(row: Dict[str, str]) -> Tuple[str, str, int, Decimal] | None:
    """Validates and cleans a CSV row. Returns (region, category, units, unit_price) or None if invalid."""
    # Ensure mandatory keys exist
    required_keys = {"region", "category", "units", "unit_price"}
    if not required_keys.issubset(row.keys()):
        return None

    region = row["region"].strip()
    category = row["category"].strip()

    # Reject empty region or category
    if not region or not category:
        return None

    # Validate units (must be a positive integer)
    try:
        units = int(row["units"].strip())
        if units <= 0:
            return None
    except (ValueError, AttributeError):
        return None

    # Validate unit_price (must be a positive Decimal/float)
    try:
        unit_price = Decimal(row["unit_price"].strip())
        if unit_price <= 0:
            return None
    except (InvalidOperation, TypeError, AttributeError):
        return None

    return region, category, units, unit_price


def aggregate_sales(input_csv_path: str, output_csv_path: str) -> None:
    """Reads input CSV, aggregates sales metrics, and writes sorted results to output CSV."""
    # Map key: (region, category) -> [total_units, total_revenue]
    aggregated_data: Dict[Tuple[str, str], List] = defaultdict(
        lambda: [0, Decimal("0.00")]
    )

    with open(input_csv_path, mode="r", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)

        # Normalize field names to lowercase/stripped
        if reader.fieldnames:
            reader.fieldnames = [f.strip().lower() for f in reader.fieldnames]

        for row in reader:
            cleaned_data = parse_and_clean_row(row)
            if cleaned_data is None:
                continue  # Skip invalid rows

            region, category, units, unit_price = cleaned_data
            line_revenue = units * unit_price

            aggregated_data[(region, category)][0] += units
            aggregated_data[(region, category)][1] += line_revenue

    # Sort aggregated results alphabetically by region, then category
    sorted_keys = sorted(aggregated_data.keys(), key=lambda x: (x[0], x[1]))

    fieldnames = [
        "region",
        "category",
        "total_units",
        "total_revenue",
        "weighted_avg_unit_price",
    ]

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for region, category in sorted_keys:
            total_units, total_revenue = aggregated_data[(region, category)]
            # Weighted Average Unit Price = Total Revenue / Total Units
            weighted_avg_price = total_revenue / Decimal(total_units)

            writer.writerow(
                {
                    "region": region,
                    "category": category,
                    "total_units": total_units,
                    "total_revenue": f"{total_revenue:.2f}",
                    "weighted_avg_unit_price": f"{weighted_avg_price:.2f}",
                }
            )


if __name__ == "__main__":
    # Example usage:
    # Replace 'sales_input.csv' and 'sales_output.csv' with your target filenames.
    input_file = "sales_input.csv"
    output_file = "sales_output.csv"

    # Minimal example setup to demonstrate execution if run directly
    import os

    if not os.path.exists(input_file):
        sample_csv = (
            "region,category,units,unit_price\n"
            "North,Electronics,10,100.00\n"
            "North,Electronics,5,120.00\n"
            "North,Furniture,-2,50.00\n"  # Invalid (negative units)
            "South,Electronics,invalid,15.00\n"  # Invalid (bad units)
            "South,Furniture,8,45.50\n"
            "North,Furniture,4,50.00\n"
        )
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(sample_csv)

    aggregate_sales(input_file, output_file)
    print(f"Aggregation complete. Results written to {output_file}")