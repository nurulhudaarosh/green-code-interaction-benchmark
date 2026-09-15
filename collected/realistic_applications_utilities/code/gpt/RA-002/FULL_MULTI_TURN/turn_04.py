def report_low_stock(records, reorder_levels):
    """Handle empty inputs and boundary reorder levels safely."""
    if not records or not reorder_levels:
        return []

    low_stock = []

    for record in records:
        if not isinstance(record, dict):
            continue

        sku = record.get("sku")
        quantity = record.get("quantity")

        # Ignore invalid records
        if not isinstance(sku, str) or not sku.strip():
            continue
        if not isinstance(quantity, (int, float)) or isinstance(quantity, bool) or quantity < 0:
            continue

        sku = sku.strip()

        # Only report known SKUs
        if sku not in reorder_levels:
            continue

        reorder_level = reorder_levels[sku]

        # Ignore invalid reorder levels
        if not isinstance(reorder_level, (int, float)) or isinstance(reorder_level, bool) or reorder_level < 0:
            continue

        # Boundary included: quantity == reorder_level is low stock
        if quantity <= reorder_level:
            low_stock.append({
                "sku": sku,
                "quantity": quantity,
                "reorder_level": reorder_level
            })

    return low_stock


# Boundary and empty-input tests
print(report_low_stock([], {}))
print(report_low_stock([{"sku": "A101", "quantity": 0}], {"A101": 0}))
print(report_low_stock([{"sku": "B202", "quantity": 5}], {"B202": 5}))
print(report_low_stock([{"sku": "C303", "quantity": 6}], {"C303": 5}))