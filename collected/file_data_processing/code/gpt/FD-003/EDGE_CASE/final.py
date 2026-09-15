import csv
from collections import defaultdict

def aggregate_sales(input_file, output_file):
    totals = defaultdict(lambda: {
        "total_units": 0,
        "total_revenue": 0.0
    })

    with open(input_file, "r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            try:
                region = row["region"].strip()
                category = row["category"].strip()
                units = int(row["units"])
                unit_price = float(row["unit_price"])

                # Consistent validation:
                # units must be positive and unit_price must be positive.
                if not region or not category:
                    continue

                if units <= 0 or unit_price <= 0:
                    continue

            except (KeyError, ValueError, TypeError):
                continue

            key = (region, category)
            revenue = units * unit_price

            totals[key]["total_units"] += units
            totals[key]["total_revenue"] += revenue

    with open(output_file, "w", newline="", encoding="utf-8") as outfile:
        fieldnames = [
            "region",
            "category",
            "total_units",
            "total_revenue",
            "weighted_avg_unit_price"
        ]

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        # Sorting by region and category makes output deterministic.
        for region, category in sorted(totals):
            data = totals[(region, category)]
            total_units = data["total_units"]
            total_revenue = data["total_revenue"]

            weighted_avg = total_revenue / total_units

            writer.writerow({
                "region": region,
                "category": category,
                "total_units": total_units,
                "total_revenue": round(total_revenue, 2),
                "weighted_avg_unit_price": round(weighted_avg, 2)
            })


if __name__ == "__main__":
    aggregate_sales("sales.csv", "sales_summary.csv")