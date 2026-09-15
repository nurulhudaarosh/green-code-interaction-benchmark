#!/usr/bin/env python3
import csv
import sys
import math
import argparse
from collections import defaultdict


def parse_args():
    parser = argparse.ArgumentParser(description="Aggregate sales CSV by region and category.")
    parser.add_argument("input", help="Path to input CSV file")
    parser.add_argument("output", help="Path to output CSV file")
    parser.add_argument("--encoding", default="utf-8", help="File encoding (default: utf-8)")
    return parser.parse_args()


def parse_int_field(raw):
    if raw is None:
        raise ValueError("missing value")
    s = raw.strip()
    if s == "":
        raise ValueError("empty value")
    if not (s.lstrip("-").isdigit()):
        raise ValueError(f"not a plain integer: {s!r}")
    return int(s)


def parse_float_field(raw):
    if raw is None:
        raise ValueError("missing value")
    s = raw.strip()
    if s == "":
        raise ValueError("empty value")
    value = float(s)
    if not math.isfinite(value):
        raise ValueError(f"non-finite value: {s!r}")
    return value


def validate_row(row, row_num):
    try:
        normalized = {(k or "").strip().lower(): v for k, v in row.items()}

        region = (normalized.get("region") or "").strip()
        category = (normalized.get("category") or "").strip()
        units_raw = normalized.get("units")
        price_raw = normalized.get("unit_price")

        if not region or not category:
            print(f"[WARN] Row {row_num}: missing region/category -> skipped", file=sys.stderr)
            return None

        try:
            units = parse_int_field(units_raw)
        except (ValueError, TypeError) as e:
            print(f"[WARN] Row {row_num}: invalid units '{units_raw}' ({e}) -> skipped", file=sys.stderr)
            return None

        if units <= 0:
            print(f"[WARN] Row {row_num}: non-positive units '{units}' -> skipped", file=sys.stderr)
            return None

        try:
            unit_price = parse_float_field(price_raw)
        except (ValueError, TypeError) as e:
            print(f"[WARN] Row {row_num}: invalid unit_price '{price_raw}' ({e}) -> skipped", file=sys.stderr)
            return None

        if unit_price <= 0:
            print(f"[WARN] Row {row_num}: non-positive unit_price '{unit_price}' -> skipped", file=sys.stderr)
            return None

        return region, category, units, unit_price

    except Exception as e:
        print(f"[WARN] Row {row_num}: unexpected error ({e}) -> skipped", file=sys.stderr)
        return None


def aggregate_sales(input_path, encoding="utf-8"):
    aggregates = defaultdict(lambda: {"total_units": 0, "total_revenue": 0.0})

    valid_count = 0
    invalid_count = 0

    with open(input_path, newline="", encoding=encoding) as f:
        reader = csv.DictReader(f)

        required_cols = {"region", "category", "units", "unit_price"}
        fieldnames_lower = {(fn or "").strip().lower() for fn in (reader.fieldnames or [])}
        missing = required_cols - fieldnames_lower
        if missing:
            raise ValueError(f"Input CSV is missing required columns: {sorted(missing)}")

        for row_num, row in enumerate(reader, start=2):
            result = validate_row(row, row_num)
            if result is None:
                invalid_count += 1
                continue

            region, category, units, unit_price = result
            key = (region, category)
            aggregates[key]["total_units"] += units
            aggregates[key]["total_revenue"] += units * unit_price
            valid_count += 1

    print(f"[INFO] Processed rows: {valid_count} valid, {invalid_count} invalid/skipped", file=sys.stderr)
    return aggregates


def write_results(aggregates, output_path):
    fieldnames = ["region", "category", "total_units", "total_revenue", "weighted_avg_unit_price"]

    sorted_keys = sorted(aggregates.keys(), key=lambda k: (k[0], k[1]))

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for region, category in sorted_keys:
            data = aggregates[(region, category)]
            total_units = data["total_units"]
            total_revenue = data["total_revenue"]
            weighted_avg_price = total_revenue / total_units if total_units else 0.0

            writer.writerow({
                "region": region,
                "category": category,
                "total_units": total_units,
                "total_revenue": round(total_revenue, 2),
                "weighted_avg_unit_price": round(weighted_avg_price, 4),
            })


def main():
    args = parse_args()
    try:
        aggregates = aggregate_sales(args.input, encoding=args.encoding)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    if not aggregates:
        print("[WARN] No valid rows found; output file will contain only headers.", file=sys.stderr)

    write_results(aggregates, args.output)
    print(f"[INFO] Wrote aggregated results to '{args.output}'", file=sys.stderr)


if __name__ == "__main__":
    main()