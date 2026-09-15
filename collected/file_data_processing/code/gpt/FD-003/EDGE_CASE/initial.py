import csv
from collections import defaultdict

def aggregate_sales(input_file, output_file):
    totals = defaultdict(lambda: {
        "total_units": 0,
        "total_revenue": 0.0,
        "weighted_price_sum": 0.0
    })

    with open(input_file, "r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            try:
                region = row["region"].strip()
                category = row["category"].strip()
                units = int(row["units"])
                unit_price = float(row["unit_price"])

                if not region or not category:
                    continue

                if units <= 0 or unit_price < 0:
                    continue

            except (KeyError, ValueError, TypeError):
                continue

            key = (region, category)
            totals[key]["total_units"] += units
            totals[key]["total_revenue"] += units * unit_price
            totals[key]["weighted_price_sum"] += units * unit_price

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

        for (region, category), data in sorted(totals.items()):
            total_units = data["total_units"]
            weighted_avg = (
                data["weighted_price_sum"] / total_units
                if total_units > 0 else 0.0
            )

            writer.writerow({
                "region": region,
                "category": category,
                "total_units": total_units,
                "total_revenue": round(data["total_revenue"], 2),
                "weighted_avg_unit_price": round(weighted_avg, 2)
            })


if __name__ == "__main__":
    aggregate_sales("sales.csv", "sales_summary.csv")