import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple


def parse_and_clean_row(row: Dict[str, str]) -> Optional[Tuple[str, str, int, Decimal]]:
    """Validates and cleans a CSV row. Returns (region, category, units, unit_price) or None if invalid."""
    if not isinstance(row, dict):
        return None

    # Check that required field keys exist
    required_keys = {"region", "category", "units", "unit_price"}
    if not required_keys.issubset(row.keys()):
        return None

    # Retrieve values safely, protecting against None/non-string values
    raw_region = row.get("region")
    raw_category = row.get("category")
    raw_units = row.get("units")
    raw_unit_price = row.get("unit_price")

    if not all(isinstance(val, str) for val in (raw_region, raw_category, raw_units, raw_unit_price)):
        return None

    region = raw_region.strip()
    category = raw_category.strip()

    # Reject empty text values
    if not region or not category:
        return None

    # Robust integer parsing for units (skips floats, non-numeric strings, and <= 0)
    try:
        units_str = raw_units.strip()
        units = int(units_str)
        if units <= 0:
            return None
    except (ValueError, AttributeError):
        return None

    # Robust Decimal parsing for unit_price (skips non-numeric strings and <= 0)
    try:
        price_str = raw_unit_price.strip()
        unit_price = Decimal(price_str)
        if unit_price <= 0:
            return None
    except (InvalidOperation, TypeError, AttributeError):
        return None

    return region, category, units, unit_price


def aggregate_sales(input_csv_path: str, output_csv_path: str) -> None:
    """Reads input CSV, safely ignores all malformed rows, and outputs aggregated results."""
    # Key: (region, category) -> [total_units, total_revenue]
    aggregated_data: Dict[Tuple[str, str], List] = defaultdict(
        lambda: [0, Decimal("0.00")]
    )

    with open(input_csv_path, mode="r", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)

        # Normalize fieldnames if present
        if reader.fieldnames:
            reader.fieldnames = [f.strip().lower() for f in reader.fieldnames]

        for row in reader:
            cleaned_data = parse_and_clean_row(row)
            if cleaned_data is None:
                continue  # Skip any malformed or invalid row completely

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
    input_file = "sales_input.csv"
    output_file = "sales_output.csv"

    # Example containing various malformed numeric formats
    sample_csv = (
        "region,category,units,unit_price\n"
        "North,Electronics,10,100.00\n"       # Valid
        "North,Electronics,five,120.00\n"     # Invalid (non-numeric units) -> Skipped
        "North,Electronics,5,120.00$\n"       # Invalid (symbol in price) -> Skipped
        "South,Electronics,8.5,15.00\n"       # Invalid (float units) -> Skipped
        "South,Furniture,8,45.50\n"           # Valid
        "South,Furniture,0,50.00\n"           # Invalid (zero units) -> Skipped
        "North,Furniture,4,NaN\n"             # Invalid (NaN price) -> Skipped
        "North,Furniture,4,50.00\n"           # Valid
    )

    with open(input_file, "w", encoding="utf-8") as f:
        f.write(sample_csv)

    aggregate_sales(input_file, output_file)
    print(f"Aggregation complete. Results written to {output_file}")