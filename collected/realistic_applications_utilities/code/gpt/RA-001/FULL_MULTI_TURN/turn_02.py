def analyze_expenses(records):
    totals = {}
    valid_records = 0

    for record in records:
        if not isinstance(record, str):
            continue

        record = record.strip()
        if not record:
            continue

        parts = record.split(",")

        if len(parts) != 2:
            continue

        category = parts[0].strip()
        amount_text = parts[1].strip()

        if not category or not amount_text:
            continue

        try:
            amount = float(amount_text)
        except (ValueError, TypeError):
            continue

        if amount < 0:
            continue

        totals[category] = totals.get(category, 0.0) + amount
        valid_records += 1

    return {
        "totals": totals,
        "valid_records": valid_records
    }


if __name__ == "__main__":
    records = [
        "Food,25.50",
        "Transport,10",
        "Malformed Record",
        "Food,15.25",
        "",
        "Shopping,abc",
        "Transport,5",
        " ,20",
        "Entertainment,30"
    ]

    result = analyze_expenses(records)

    print("Expense totals:")
    for category, total in result["totals"].items():
        print(f"{category}: ${total:.2f}")

    print(f"Valid records: {result['valid_records']}")