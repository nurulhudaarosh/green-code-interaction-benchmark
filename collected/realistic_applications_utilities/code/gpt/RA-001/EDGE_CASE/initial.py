from collections import defaultdict


def analyze_expenses(records, minimum_amount=0):
    """
    Analyze transaction records while safely handling:
    - empty records
    - malformed records
    - zero-value transactions
    - whitespace-heavy fields

    Expected record format:
        {"category": "Food", "amount": 25.50}
    """

    totals = defaultdict(float)
    valid_transactions = []
    invalid_records = []

    for index, record in enumerate(records or []):
        # Empty or non-dictionary records are malformed.
        if not isinstance(record, dict) or not record:
            invalid_records.append({
                "index": index,
                "record": record,
                "reason": "empty or malformed record"
            })
            continue

        # Normalize keys where possible.
        normalized = {
            str(key).strip().lower(): value
            for key, value in record.items()
        }

        category = normalized.get("category")
        amount = normalized.get("amount")

        # Handle missing/whitespace-only category.
        if category is None or not str(category).strip():
            invalid_records.append({
                "index": index,
                "record": record,
                "reason": "missing or empty category"
            })
            continue

        # Handle missing/empty amount.
        if amount is None or (isinstance(amount, str) and not amount.strip()):
            invalid_records.append({
                "index": index,
                "record": record,
                "reason": "missing or empty amount"
            })
            continue

        # Safely convert amount to a number.
        try:
            amount = float(str(amount).strip())
        except (TypeError, ValueError):
            invalid_records.append({
                "index": index,
                "record": record,
                "reason": "invalid amount"
            })
            continue

        # Reject non-finite values.
        if amount != amount or amount in (float("inf"), float("-inf")):
            invalid_records.append({
                "index": index,
                "record": record,
                "reason": "non-finite amount"
            })
            continue

        # Zero-value transactions are valid, but can be excluded
        # by a positive minimum_amount filter.
        category = str(category).strip()

        if amount < minimum_amount:
            continue

        valid_transactions.append({
            "category": category,
            "amount": amount
        })
        totals[category] += amount

    total_expenses = sum(item["amount"] for item in valid_transactions)

    return {
        "total_expenses": total_expenses,
        "transaction_count": len(valid_transactions),
        "category_totals": dict(sorted(totals.items())),
        "invalid_records": invalid_records,
    }


if __name__ == "__main__":
    transactions = [
        {"category": " Food ", "amount": " 25.50 "},
        {"category": "Transport", "amount": 10},
        {"category": "Food", "amount": 0},
        {},
        None,
        {"category": "   ", "amount": 15},
        {"category": "Bills", "amount": "not-a-number"},
        {"category": "Shopping", "amount": " 30 "},
        {"category": "Food", "amount": 12.50},
        {"category": "Transport", "amount": "   "},
    ]

    result = analyze_expenses(transactions, minimum_amount=0)

    print("Total expenses:", result["total_expenses"])
    print("Valid transactions:", result["transaction_count"])
    print("Category totals:")

    for category, total in result["category_totals"].items():
        print(f"  {category}: {total:.2f}")

    print("Invalid records:")
    for invalid in result["invalid_records"]:
        print(f"  Record {invalid['index']}: {invalid['reason']}")