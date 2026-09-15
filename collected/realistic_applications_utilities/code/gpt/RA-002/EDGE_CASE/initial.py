def reconcile_inventory(inventory, reorder_levels, updates):
    """
    Handle:
    - Empty inventory/update data
    - Unknown SKUs
    - Zero stock
    - Boundary reorder levels (stock == reorder level)
    """

    if not inventory:
        return {"updated": {}, "low_stock": [], "unknown_skus": []}

    updated = dict(inventory)
    unknown_skus = []

    for sku, quantity in (updates or {}).items():
        if sku not in updated:
            unknown_skus.append(sku)
            continue

        # Ignore invalid/negative quantities
        if not isinstance(quantity, (int, float)) or quantity < 0:
            continue

        updated[sku] = quantity

    # Low stock includes zero stock and stock exactly at reorder level
    low_stock = [
        sku for sku, stock in updated.items()
        if stock <= reorder_levels.get(sku, float("-inf"))
    ]

    return {
        "updated": updated,
        "low_stock": low_stock,
        "unknown_skus": unknown_skus
    }