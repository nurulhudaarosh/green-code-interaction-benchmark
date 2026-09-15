import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation


def parse_decimal(value):
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        d = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    if d < 0:
        return None
    return d


def aggregate_sales(input_path, output_path):
    agg = defaultdict(lambda: defaultdict(lambda: {'units': 0, 'revenue': Decimal('0')}))

    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [h.strip() for h in reader.fieldnames]

        for row in reader:
            region = (row.get('region') or '').strip()
            category = (row.get('category') or '').strip()
            units_raw = row.get('units')
            price_raw = row.get('unit_price')

            if not region or not category:
                continue

            try:
                units = int(str(units_raw).strip())
            except (TypeError, ValueError):
                continue
            if units < 0:
                continue

            price = parse_decimal(price_raw)
            if price is None:
                continue

            bucket = agg[region][category]
            bucket['units'] += units
            bucket['revenue'] += price * units

    results = []
    for region in sorted(agg.keys()):
        for category in sorted(agg[region].keys()):
            bucket = agg[region][category]
            units = bucket['units']
            revenue = bucket['revenue']
            weighted_avg = (revenue / units) if units > 0 else Decimal('0')
            results.append({
                'region': region,
                'category': category,
                'total_units': units,
                'total_revenue': revenue,
                'weighted_avg_unit_price': weighted_avg,
            })

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'region', 'category', 'total_units',
            'total_revenue', 'weighted_avg_unit_price'
        ])
        for r in results:
            writer.writerow([
                r['region'],
                r['category'],
                r['total_units'],
                f"{r['total_revenue']:.2f}",
                f"{r['weighted_avg_unit_price']:.4f}",
            ])

    return results


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 3:
        print("Usage: python sales_aggregator.py <input.csv> <output.csv>")
        sys.exit(1)

    results = aggregate_sales(sys.argv[1], sys.argv[2])
    print(f"Wrote {len(results)} aggregated rows to {sys.argv[2]}")