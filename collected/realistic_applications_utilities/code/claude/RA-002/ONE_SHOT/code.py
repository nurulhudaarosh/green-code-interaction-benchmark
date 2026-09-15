def reconcile_inventory(records, reorder_levels):
    """
    Complete inventory reconciliation:
    - Handles empty inputs
    - Removes duplicate SKUs (latest valid record wins)
    - Rejects invalid records/quantities
    - Ignores unknown SKUs
    - Handles zero stock
    - Treats quantity == reorder level as low stock
    - Returns reconciliation + low-stock report
    """
    if not records or not reorder_levels:
        return {
            "reconciled": [],
            "low_stock": [],
            "invalid_records": [],
            "unknown_skus": []
        }

    reconciled = {}
    invalid_records = []
    unknown_skus = []

    for record in records:
        if not isinstance(record, dict):
            invalid_records.append(record)
            continue

        sku = record.get("sku")
        quantity = record.get("quantity")

        # Invalid SKU
        if not isinstance(sku, str) or not sku.strip():
            invalid_records.append(record)
            continue

        sku = sku.strip()

        # Invalid quantity
        if (
            not isinstance(quantity, (int, float))
            or isinstance(quantity, bool)
            or quantity < 0
        ):
            invalid_records.append(record)
            continue

        # Unknown SKU
        if sku not in reorder_levels:
            unknown_skus.append(sku)
            continue

        reorder_level = reorder_levels[sku]

        # Invalid reorder level
        if (
            not isinstance(reorder_level, (int, float))
            or isinstance(reorder_level, bool)
            or reorder_level < 0
        ):
            invalid_records.append(record)
            continue

        # Duplicate SKU: latest valid record replaces previous one
        reconciled[sku] = {
            "sku": sku,
            "quantity": quantity,
            "reorder_level": reorder_level
        }

    # Low-stock report: boundary is inclusive
    low_stock = [
        item for item in reconciled.values()
        if item["quantity"] <= item["reorder_level"]
    ]

    return {
        "reconciled": list(reconciled.values()),
        "low_stock": low_stock,
        "invalid_records": invalid_records,
        "unknown_skus": sorted(set(unknown_skus))
    }


# Example
records = [
    {"sku": "A101", "quantity": 10},
    {"sku": "B202", "quantity": 0},
    {"sku": "A101", "quantity": 5},     # duplicate -> latest kept
    {"sku": "C303", "quantity": -2},    # invalid
    {"sku": "X999", "quantity": 8},     # unknown SKU
    {"sku": "D404", "quantity": "10"}   # invalid
]

reorder_levels = {
    "A101": 5,
    "B202": 3,
    "C303": 5,
    "D404": 4
}

result = reconcile_inventory(records, reorder_levels)

print("Reconciled:", result["reconciled"])
print("Low stock:", result["low_stock"])
print("Invalid:", result["invalid_records"])
print("Unknown SKUs:", result["unknown_skus"])