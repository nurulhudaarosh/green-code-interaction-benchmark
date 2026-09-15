import csv
import json
import sys
from collections import defaultdict


def aggregate_sales(input_file, output_file):
    data = defaultdict(lambda: {
        "total_units": 0,
        "total_revenue": 0.0
    })

    invalid_rows = 0

    with open(input_file, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        required_columns = {"region", "category", "units", "unit_price"}

        if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
            raise ValueError(
                "CSV must contain: region, category, units, unit_price"
            )

        for row in reader:
            try:
                region = row["region"].strip()
                category = row["category"].strip()

                if not region or not category:
                    raise ValueError

                units = int(row["units"])
                unit_price = float(row["unit_price"])

                if units <= 0 or unit_price < 0:
                    raise ValueError

            except (ValueError, TypeError, KeyError):
                invalid_rows += 1
                continue

            key = (region, category)

            data[key]["total_units"] += units
            data[key]["total_revenue"] += units * unit_price

    results = []

    for (region, category), values in sorted(data.items()):
        total_units = values["total_units"]
        total_revenue = values["total_revenue"]

        weighted_average_unit_price = (
            total_revenue / total_units
            if total_units > 0
            else 0.0
        )

        results.append({
            "region": region,
            "category": category,
            "total_units": total_units,
            "total_revenue": round(total_revenue, 2),
            "weighted_average_unit_price": round(
                weighted_average_unit_price, 2
            )
        })

    output = {
        "invalid_rows": invalid_rows,
        "results": results
    }

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python sales_aggregator.py input.csv output.json")
        sys.exit(1)

    aggregate_sales(sys.argv[1], sys.argv[2])
    print(f"Sales aggregation completed: {sys.argv[2]}")