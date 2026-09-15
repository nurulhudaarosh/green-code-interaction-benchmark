def inventory_utility(records, reorder_levels):
    """Clean inventory data and generate a low-stock report."""
    if not records:
        return {"inventory": [], "low_stock": []}

    inventory = {}

    for record in records:
        if not isinstance(record, dict):
            continue

        sku = record.get("sku")
        quantity = record.get("quantity")

        # Validate SKU and quantity
        if not isinstance(sku, str) or not sku.strip():
            continue
        if (
            not isinstance(quantity, (int, float))
            or isinstance(quantity, bool)
            or quantity < 0
        ):
            continue

        sku = sku.strip()

        # Duplicate SKU: latest valid record wins
        inventory[sku] = {
            "sku": sku,
            "quantity": quantity
        }

    # Low-stock reporting
    low_stock = []
    for item in inventory.values():
        sku = item["sku"]

        if sku in reorder_levels:
            reorder_level = reorder_levels[sku]

            if (
                isinstance(reorder_level, (int, float))
                and not isinstance(reorder_level, bool)
                and reorder_level >= 0
                and item["quantity"] <= reorder_level
            ):
                low_stock.append({
                    "sku": sku,
                    "quantity": item["quantity"],
                    "reorder_level": reorder_level
                })

    return {
        "inventory": list(inventory.values()),
        "low_stock": low_stock
    }


# Example
records = [
    {"sku": "A101", "quantity": 10},
    {"sku": "B202", "quantity": 3},
    {"sku": "A101", "quantity": 5},   # duplicate -> latest wins
    {"sku": "C303", "quantity": -1},  # invalid
]

reorder_levels = {
    "A101": 5,
    "B202": 5,
    "C303": 2
}

result = inventory_utility(records, reorder_levels)

print("Inventory:", result["inventory"])
print("Low stock:", result["low_stock"])