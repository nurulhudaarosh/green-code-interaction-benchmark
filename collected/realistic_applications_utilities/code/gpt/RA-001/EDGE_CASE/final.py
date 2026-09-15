from collections import defaultdict


def analyze_expenses(records):
    totals = defaultdict(float)
    valid_records = []
    invalid_records = []

    for index, record in enumerate(records or []):
        # Ignore empty, None, or non-dictionary records.
        if not record or not isinstance(record, dict):
            invalid_records.append((index, "empty or malformed record"))
            continue

        # Normalize keys and whitespace.
        normalized = {
            str(key).strip().lower(): value
            for key, value in record.items()
        }

        category = normalized.get("category")
        amount = normalized.get("amount")

        # Reject missing or whitespace-only categories.
        if category is None or not str(category).strip():
            invalid_records.append((index, "missing category"))
            continue

        # Reject missing or whitespace-only amounts.
        if amount is None or (
            isinstance(amount, str) and not amount.strip()
        ):
            invalid_records.append((index, "missing amount"))
            continue

        # Convert the amount safely.
        try:
            amount = float(str(amount).strip())
        except (TypeError, ValueError):
            invalid_records.append((index, "malformed amount"))
            continue

        # Zero is a valid value and should not be treated as malformed.
        category = str(category).strip()

        totals[category] += amount
        valid_records.append({
            "category": category,
            "amount": amount
        })

    return {
        "total": sum(totals.values()),
        "count": len(valid_records),
        "category_totals": dict(totals),
        "invalid_records": invalid_records,
    }


if __name__ == "__main__":
    records = [
        {"category": " Food ", "amount": " 25.50 "},
        {"category": "Transport", "amount": 10},
        {"category": " Food ", "amount": 0},
        {},
        None,
        {"category": "   ", "amount": 15},
        {"category": "Bills", "amount": "abc"},
        {"category": " Shopping ", "amount": " 30 "},
        "malformed",
        {"category": "Food", "amount": 12.50},
    ]

    result = analyze_expenses(records)

    print("Total:", result["total"])
    print("Valid records:", result["count"])
    print("Category totals:", result["category_totals"])
    print("Invalid records:")

    for index, reason in result["invalid_records"]:
        print(f"  Record {index}: {reason}")