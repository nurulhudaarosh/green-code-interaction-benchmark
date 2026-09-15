from collections import defaultdict

def analyze_expenses(records, min_amount=0):
    if not records:
        return {
            "total": 0.0,
            "count": 0,
            "by_category": {},
            "by_month": {}
        }

    if min_amount < 0:
        min_amount = 0

    category_totals = defaultdict(float)
    monthly_totals = defaultdict(float)
    total = 0.0
    count = 0

    for record in records:
        try:
            amount = float(record["amount"])
            category = record["category"]
            month = record["month"]
        except (KeyError, TypeError, ValueError):
            continue

        if amount < 0 or amount < min_amount:
            continue

        total += amount
        count += 1
        category_totals[category] += amount
        monthly_totals[month] += amount

    return {
        "total": round(total, 2),
        "count": count,
        "by_category": dict(sorted(category_totals.items(), key=lambda x: x[1], reverse=True)),
        "by_month": dict(sorted(monthly_totals.items()))
    }

result = analyze_expenses(records, min_amount=500)