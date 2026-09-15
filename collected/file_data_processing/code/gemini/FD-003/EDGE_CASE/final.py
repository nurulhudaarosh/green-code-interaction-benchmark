import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Tuple, Union


def aggregate_sales_data(
    input_filepath: Union[str, Path], output_filepath: Union[str, Path]
) -> None:
    """Reads sales data from a CSV, validates rows, aggregates metrics by

    region and category, and outputs deterministic results to a sorted CSV.

    Validation Rules:
        - Region and Category must be non-empty strings.
        - Units must be a strictly positive integer (> 0). Non-positive values (<= 0)
          or non-integer representations are treated as invalid and skipped.
        - UnitPrice must be a non-negative decimal (>= 0). Zero prices are allowed;
          negative prices (< 0) or non-numeric values are skipped.

    Aggregation Rules:
        - TotalRevenue = sum(Units * UnitPrice)
        - WeightedAvgUnitPrice = TotalRevenue / TotalUnits
        - Data sorted deterministically by Region, then Category (case-sensitive).
    """
    input_path = Path(input_filepath)
    output_path = Path(output_filepath)

    # Aggregation key: (Region, Category) -> [Total Units (int), Total Revenue (Decimal)]
    aggregated_data: Dict[Tuple[str, str], List[Union[int, Decimal]]] = defaultdict(
        lambda: [0, Decimal("0.00")]
    )

    valid_rows_count = 0
    invalid_rows_count = 0

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found at {input_path}")

    with input_path.open(mode="r", encoding="utf-8-sig", newline="") as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            region = row.get("Region", "").strip() if row.get("Region") else ""
            category = row.get("Category", "").strip() if row.get("Category") else ""
            raw_units = row.get("Units", "").strip() if row.get("Units") else ""
            raw_price = row.get("UnitPrice", "").strip() if row.get("UnitPrice") else ""

            # 1. Validate mandatory string fields
            if not region or not category:
                invalid_rows_count += 1
                continue

            # 2. Validate Units: Must be a strictly positive integer (> 0)
            try:
                units = int(raw_units)
                if units <= 0:
                    invalid_rows_count += 1
                    continue
            except (ValueError, TypeError):
                invalid_rows_count += 1
                continue

            # 3. Validate Unit Price: Must be a non-negative numeric value (>= 0)
            try:
                unit_price = Decimal(raw_price)
                if unit_price < Decimal("0"):
                    invalid_rows_count += 1
                    continue
            except (InvalidOperation, TypeError):
                invalid_rows_count += 1
                continue

            # 4. Accumulate valid entries
            line_revenue = units * unit_price
            key = (region, category)
            aggregated_data[key][0] += units
            aggregated_data[key][1] += line_revenue
            valid_rows_count += 1

    # Deterministic sorting: Sort by Region, then Category (lexicographical order)
    sorted_aggregated_keys = sorted(aggregated_data.keys(), key=lambda k: (k[0], k[1]))

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write aggregated data
    with output_path.open(mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(
            ["Region", "Category", "TotalUnits", "TotalRevenue", "WeightedAvgUnitPrice"]
        )

        for region, category in sorted_aggregated_keys:
            total_units, total_revenue = aggregated_data[(region, category)]

            # TotalUnits is guaranteed > 0 because invalid units (<= 0) were rejected
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
    sample_input = "sample_sales_data.csv"
    sample_output = "sales_summary.csv"

    # Edge-case test dataset covering zero prices, zero/negative units, and invalid inputs
    sample_data = """Region,Category,Units,UnitPrice
North,Electronics,10,100.00
North,Electronics,5,0.00
North,Furniture,-5,50.00
North,Furniture,0,50.00
South,Electronics,20,150.50
South,Electronics,10,-10.00
East,Apparel,15,0.00
West,Apparel,bad_val,25.00
"""
    with open(sample_input, "w", encoding="utf-8") as f:
        f.write(sample_data.strip())

    aggregate_sales_data(sample_input, sample_output)