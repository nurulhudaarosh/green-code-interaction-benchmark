id="4m8x2q"
import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation


def aggregate_sales(input_file, output_file):
    aggregates = defaultdict(lambda: {
        "total_units": Decimal("0"),
        "total_revenue": Decimal("0")
    })

    with open(input_file, "r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            try:
                region = row["region"].strip()
                category = row["category"].strip()

                # Convert numeric fields safely.
                units = Decimal(row["units"].strip())
                unit_price = Decimal(row["unit_price"].strip())

                # Skip rows with missing grouping fields.
                if not region or not category:
                    continue

                # Units must be positive.
                # Unit price can be zero but cannot be negative.
                if units <= 0 or unit_price < 0:
                    continue

                # Reject non-finite numeric values such as NaN or Infinity.
                if not units.is_finite() or not unit_price.is_finite():
                    continue

            except (
                KeyError,
                AttributeError,
                InvalidOperation,
                TypeError,
            ):
                # Skip malformed rows without affecting aggregates.
                continue

            key = (region, category)
            aggregates[key]["total_units"] += units
            aggregates[key]["total_revenue"] += units * unit_price

    with open(output_file, "w", newline="", encoding="utf-8") as outfile:
        fieldnames = [
            "region",
            "category",
            "total_units",
            "total_revenue",
            "weighted_avg_unit_price",
        ]

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        # Explicit sorting makes the output deterministic.
        for (region, category), data in sorted(aggregates.items()):
            total_units = data["total_units"]
            total_revenue = data["total_revenue"]

            weighted_avg = total_revenue / total_units

            writer.writerow({
                "region": region,
                "category": category,
                "total_units": total_units,
                "total_revenue": total_revenue.quantize(
                    Decimal("0.01")
                ),
                "weighted_avg_unit_price": weighted_avg.quantize(
                    Decimal("0.01")
                ),
            })


if __name__ == "__main__":
    aggregate_sales("sales.csv", "sales_summary.csv")