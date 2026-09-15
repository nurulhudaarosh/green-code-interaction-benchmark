import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple


def parse_and_clean_row(row: Dict[str, str]) -> Optional[Tuple[str, str, int, Decimal]]:
    """Validates and cleans a CSV row. 

    Validation Rules:
    - Must contain 'region', 'category', 'units', and 'unit_price' fields.
    - 'region' and 'category' must be non-empty strings after stripping whitespace.
    - 'units' must be a strictly positive integer (> 0). Zero and negative units are skipped.
    - 'unit_price' must be a strictly positive Decimal (> 0). Zero and negative prices are skipped.
    """
    if not isinstance(row, dict):
        return None

    # Verify key existence
    required_keys = {"region", "category", "units", "unit_price"}
    if not required_keys.issubset(row.keys()):
        return None

    raw_region = row.get("region")
    raw_category = row.get("category")
    raw_units = row.get("units")
    raw_unit_price = row.get("unit_price")

    if not all(isinstance(val, str) for val in (raw_region, raw_category, raw_units, raw_unit_price)):
        return None

    region = raw_region.strip()
    category = raw_category.strip()

    if not region or not category:
        return None

    # Validate units: Must be an integer AND strictly > 0 (filters out zero and non-positive units)
    try:
        units_str = raw_units.strip()
        units = int(units_str)
        if units <= 0:
            return None
    except (ValueError, AttributeError):
        return None

    # Validate unit_price: Must be a Decimal AND strictly > 0 (filters out zero and non-positive prices)
    try:
        price_str = raw_unit_price.strip()
        unit_price = Decimal(price_str)
        if unit_price <= 0:
            return None
    except (InvalidOperation, TypeError, AttributeError):
        return None

    return region, category, units, unit_price


def aggregate_sales(input_csv_path: str, output_csv_path: str) -> None:
    """Reads input CSV, applies consistent validation filtering zero/negative values,

    aggregates metrics, and writes deterministically sorted output.
    """
    # Key: (region, category) -> [total_units, total_revenue]
    aggregated_data: Dict[Tuple[str, str], List] = defaultdict(
        lambda: [0, Decimal("0.00")]
    )

    with open(input_csv_path, mode="r", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)

        if reader.fieldnames:
            reader.fieldnames = [f.strip().lower() for f in reader.fieldnames]

        for row in reader:
            cleaned_data = parse_and_clean_row(row)
            if cleaned_data is None:
                continue

            region, category, units, unit_price = cleaned_data
            line_revenue = units * unit_price

            aggregated_data[(region, category)][0] += units
            aggregated_data[(region, category)][1] += line_revenue

    # Deterministic sorting: lexicographical order by region, then category
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
            weighted_avg_unit_price = total_revenue / Decimal(total_units)

            writer.writerow(
                {
                    "region": region,
                    "category": category,
                    "total_units": total_units,
                    "total_revenue": f"{total_revenue:.2f}",
                    "weighted_avg_unit_price": f"{weighted_avg_unit_price:.2f}",
                }
            )


if __name__ == "__main__":
    input_file = "sales_input.csv"
    output_file = "sales_output.csv"

    # Edge-case test matrix including zero/negative units and prices
    sample_csv = (
        "region,category,units,unit_price\n"
        "North,Electronics,10,100.00\n"       # Valid
        "North,Electronics,0,120.00\n"        # Invalid (Zero units) -> Skipped
        "North,Electronics,-5,120.00\n"       # Invalid (Negative units) -> Skipped
        "South,Electronics,5,0.00\n"          # Invalid (Zero price) -> Skipped
        "South,Electronics,5,-15.00\n"        # Invalid (Negative price) -> Skipped
        "South,Furniture,8,45.50\n"           # Valid
        "North,Furniture,4,50.00\n"           # Valid
    )

    with open(input_file, "w", encoding="utf-8") as f:
        f.write(sample_csv)

    aggregate_sales(input_file, output_file)
    print(f"Aggregation complete. Output written to {output_file}")