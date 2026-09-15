import csv
import io
from collections import defaultdict
from typing import Dict, List, Tuple


def process_sales_csv(csv_input: str) -> str:
    """Reads CSV data string, validates rows, aggregates sales data,

    and returns a sorted CSV string with the results.
    """
    # Key: (region, category) -> Value: [total_units, total_revenue]
    aggregated_data: Dict[Tuple[str, str], List[float]] = defaultdict(
        lambda: [0.0, 0.0]
    )

    reader = csv.DictReader(io.StringIO(csv_input.strip()))

    for row in reader:
        # Extract values (handling unexpected whitespace)
        region = row.get("region", "").strip()
        category = row.get("category", "").strip()
        raw_units = row.get("units", "").strip()
        raw_price = row.get("unit_price", "").strip()

        # Row validation
        if not region or not category:
            continue

        try:
            units = int(raw_units)
            unit_price = float(raw_price)

            # Units and prices must be positive
            if units <= 0 or unit_price <= 0:
                continue
        except (ValueError, TypeError):
            # Ignore invalid numeric rows
            continue

        # Aggregate totals
        revenue = units * unit_price
        aggregated_data[(region, category)][0] += units
        aggregated_data[(region, category)][1] += revenue

    # Prepare output buffer
    output_buffer = io.StringIO()
    writer = csv.writer(output_buffer)

    # Write CSV Header
    writer.writerow(
        [
            "region",
            "category",
            "total_units",
            "total_revenue",
            "weighted_avg_unit_price",
        ]
    )

    # Sort records by Region and then Category
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


# Example Usage & Verification:
if __name__ == "__main__":
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

    result_csv = process_sales_csv(sample_csv_data)
    print(result_csv)