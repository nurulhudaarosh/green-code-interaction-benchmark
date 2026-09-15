import csv
import sys
from collections import defaultdict


def is_valid_number(value, allow_zero=False):
    try:
        num = float(value)
    except (TypeError, ValueError):
        return False, None
    if allow_zero:
        if num < 0:
            return False, None
    else:
        if num <= 0:
            return False, None
    return True, num


def validate_row(row):
    region = (row.get("region") or "").strip()
    category = (row.get("category") or "").strip()

    if not region or not category:
        return False, None, None, None, None

    units_valid, units = is_valid_number(row.get("units"), allow_zero=False)
    if not units_valid or units != int(units):
        return False, None, None, None, None
    units = int(units)

    price_valid, unit_price = is_valid_number(row.get("unit_price"), allow_zero=False)
    if not price_valid:
        return False, None, None, None, None

    return True, region, category, units, unit_price


def aggregate_sales(input_path):
    aggregates = defaultdict(lambda: {"total_units": 0, "total_revenue": 0.0})
    valid_count = 0
    invalid_count = 0

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required_cols = {"region", "category", "units", "unit_price"}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            missing = required_cols - set(reader.fieldnames or [])
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

        for row in reader:
            is_valid, region, category, units, unit_price = validate_row(row)
            if not is_valid:
                invalid_count += 1
                continue

            valid_count += 1
            key = (region, category)
            aggregates[key]["total_units"] += units
            aggregates[key]["total_revenue"] += units * unit_price

    return aggregates, valid_count, invalid_count


def build_results(aggregates):
    results = []
    for (region, category), data in aggregates.items():
        total_units = data["total_units"]
        total_revenue = data["total_revenue"]
        weighted_avg_price = (total_revenue / total_units) if total_units > 0 else 0.0

        results.append({
            "region": region,
            "category": category,
            "total_units": total_units,
            "total_revenue": round(total_revenue, 2),
            "weighted_avg_unit_price": round(weighted_avg_price, 2),
        })

    results.sort(key=lambda r: (r["region"], r["category"]))
    return results


def write_results(results, output_path):
    fieldnames = [
        "region",
        "category",
        "total_units",
        "total_revenue",
        "weighted_avg_unit_price",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)


def main():
    if len(sys.argv) != 3:
        print("Usage: python sales_aggregator.py <input_csv> <output_csv>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        aggregates, valid_count, invalid_count = aggregate_sales(input_path)
    except FileNotFoundError:
        print(f"Error: input file not found: {input_path}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    results = build_results(aggregates)
    write_results(results, output_path)

    print(f"Processed rows -> valid: {valid_count}, invalid/skipped: {invalid_count}")
    print(f"Aggregated {len(results)} region/category groups")
    print(f"Results written to: {output_path}")


if __name__ == "__main__":
    main()