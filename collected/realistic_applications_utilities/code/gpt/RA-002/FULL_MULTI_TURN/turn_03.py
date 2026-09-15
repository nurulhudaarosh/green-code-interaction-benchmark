def report_low_stock(records, reorder_levels):
    """Return items whose stock is at or below their reorder level."""
    low_stock = []

    for record in records:
        sku = record.get("sku")
        quantity = record.get("quantity")

        if sku in reorder_levels and quantity <= reorder_levels[sku]:
            low_stock.append({
                "sku": sku,
                "quantity": quantity,
                "reorder_level": reorder_levels[sku]
            })

    return low_stock


# Example
records = [
    {"sku": "A101", "quantity": 10},
    {"sku": "B202", "quantity": 5},
    {"sku": "C303", "quantity": 0}
]

reorder_levels = {
    "A101": 10,
    "B202": 6,
    "C303": 5
}

print("Low-stock items:")
for item in report_low_stock(records, reorder_levels):
    print(item)