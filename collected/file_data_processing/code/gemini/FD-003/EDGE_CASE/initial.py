import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Tuple, Union


def aggregate_sales_data(
    input_filepath: Union[str, Path], output_filepath: Union[str, Path]
) -> None:
    """Reads sales data from a CSV, validates rows, aggregates metrics by

    region and category, and outputs the results to a sorted CSV file.

    Input CSV Schema expected:
        Region, Category, Units, UnitPrice

    Output CSV Schema produced:
        Region, Category, TotalUnits, TotalRevenue, WeightedAvgUnitPrice
    """
    input_path = Path(input_filepath)
    output_path = Path(output_filepath)

    # Aggregation key: (Region, Category)
    # Value: [Total Units (int), Total Revenue (Decimal)]
    aggregated_data: Dict[Tuple[str, str], List[Union[int, Decimal]]] = defaultdict(
        lambda: [0, Decimal("0.00")]
    )

    valid_rows_count = 0
    invalid_rows_count = 0

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found at {input_path}")

    with input_path.open(mode="r", encoding="utf-8-sig", newline="") as infile:
        reader = csv.DictReader(infile)

        for row_num, row in enumerate(reader, start=2):  # Header is line 1
            region = row.get("Region", "").strip()
            category = row.get("Category", "").strip()
            raw_units = row.get("Units", "").strip()
            raw_price = row.get("UnitPrice", "").strip()

            # Ensure essential text fields exist
            if not region or not category:
                invalid_rows_count += 1
                continue

            # Validate Units (must be a positive integer)
            try:
                units = int(raw_units)
                if units <= 0:
                    invalid_rows_count += 1
                    continue
            except ValueError:
                invalid_rows_count += 1
                continue

            # Validate Unit Price (must be a positive numeric value)
            try:
                unit_price = Decimal(raw_price)
                if unit_price <= 0:
                    invalid_rows_count += 1
                    continue
            except InvalidOperation:
                invalid_rows_count += 1
                continue

            # Accumulate Total Units and Total Revenue (Units * UnitPrice)
            line_revenue = units * unit_price
            key = (region, category)
            aggregated_data[key][0] += units
            aggregated_data[key][1] += line_revenue
            valid_rows_count += 1

    # Sort aggregated results alphabetically by Region, then Category
    sorted_aggregated_keys = sorted(aggregated_data.keys(), key=lambda x: (x[0], x[1]))

    # Ensure target output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write results to output CSV
    with output_path.open(mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(
            ["Region", "Category", "TotalUnits", "TotalRevenue", "WeightedAvgUnitPrice"]
        )

        for region, category in sorted_aggregated_keys:
            total_units, total_revenue = aggregated_data[(region, category)]

            # Weighted Average Unit Price = Total Revenue / Total Units
            weighted_avg_price = total_revenue / Decimal(total_units)

            writer.writerow(
                [
                    region,
                    category,
                    total_units,
                    f"{total_revenue:.2f}",
                    f"{weighted_avg_price:.2f}",
                ]
            )

    print(
        f"Processing complete: {valid_rows_count} valid rows aggregated, "
        f"{invalid_rows_count} invalid rows skipped."
    )


if __name__ == "__main__":
    # Example usage demonstration
    sample_input = "sample_sales_data.csv"
    sample_output = "sales_summary.csv"

    # Generating a sample CSV file for demonstration
    sample_data = """Region,Category,Units,UnitPrice
North,Electronics,10,100.00
North,Electronics,5,150.00
North,Furniture,-2,50.00
South,Electronics,invalid,200.00
South,Electronics,20,200.00
North,Furniture,4,50.00
South,Furniture,10,abc
"""
    with open(sample_input, "w", encoding="utf-8") as f:
        f.write(sample_data.strip())

    # Execute aggregator
    aggregate_sales_data(sample_input, sample_output)