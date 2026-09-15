import csv
import sys
from collections import defaultdict


def is_valid_number(value):
    try:
        num = float(value)
        return num >= 0
    except (ValueError, TypeError):
        return False


def validate_row(row):
    region = (row.get("region") or "").strip()
    category = (row.get("category") or "").strip()
    units_raw = row.get("units")
    price_raw = row.get("unit_price")

    if not region or not category:
        return False, None, None
    if not is_valid_number(units_raw):
        return False, None, None
    if not is_valid_number(price_raw):
        return False, None, None

    units = float(units_raw)
    unit_price = float(price_raw)

    if units < 0 or unit_price < 0:
        return False, None, None

    return True, units, unit_price


def aggregate_sales(input_path):
    """
    First pass: aggregate raw totals only (units, revenue) per (region, category).
    The weighted average price is intentionally NOT computed here — it is
    derived afterward in add_weighted_average() so the totals stay untouched.
    """
    aggregates = defaultdict(lambda: {"total_units": 0.0, "total_revenue": 0.0})
    skipped_count = 0
    processed_count = 0

    with open(input_path, newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        required_columns = {"region", "category", "units", "unit_price"}
        if not required_columns.issubset(set(reader.fieldnames or [])):
            missing = required_columns - set(reader.fieldnames or [])
            raise ValueError(f"Input CSV is missing required columns: {missing}")

        for line_num, row in enumerate(reader, start=2):
            is_valid, units, unit_price = validate_row(row)
            if not is_valid:
                skipped_count += 1
                print(f"Skipping invalid row at line {line_num}: {row}", file=sys.stderr)
                continue

            region = row["region"].strip()
            category = row["category"].strip()
            revenue = units * unit_price

            key = (region, category)
            aggregates[key]["total_units"] += units
            aggregates[key]["total_revenue"] += revenue
            processed_count += 1

    print(f"Processed {processed_count} valid rows, skipped {skipped_count} invalid rows.", file=sys.stderr)
    return aggregates


def add_weighted_average(aggregates):
    """
    Adds 'weighted_avg_unit_price' to each group's dict WITHOUT modifying
    the existing 'total_units' / 'total_revenue' values.
    weighted_avg_unit_price = total_revenue / total_units
    """
    for key, data in aggregates.items():
        total_units = data["total_units"]
        total_revenue = data["total_revenue"]
        data["weighted_avg_unit_price"] = (
            total_revenue / total_units if total_units > 0 else 0.0
        )
    return aggregates


def write_results(aggregates, output_path):
    fieldnames = ["region", "category", "total_units", "total_revenue", "weighted_avg_unit_price"]
    sorted_keys = sorted(aggregates.keys(), key=lambda k: (k[0], k[1]))

    with open(output_path, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for region, category in sorted_keys:
            data = aggregates[(region, category)]
            writer.writerow({
                "region": region,
                "category": category,
                "total_units": round(data["total_units"], 2),
                "total_revenue": round(data["total_revenue"], 2),
                "weighted_avg_unit_price": round(data["weighted_avg_unit_price"], 4),
            })


def main():
    if len(sys.argv) != 3:
        print("Usage: python sales_aggregator.py <input_csv> <output_csv>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        aggregates = aggregate_sales(input_path)
    except FileNotFoundError:
        print(f"Error: input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not aggregates:
        print("Warning: no valid rows were aggregated. Output file will only contain headers.", file=sys.stderr)

    aggregates = add_weighted_average(aggregates)
    write_results(aggregates, output_path)
    print(f"Results written to '{output_path}'.")


if __name__ == "__main__":
    main()