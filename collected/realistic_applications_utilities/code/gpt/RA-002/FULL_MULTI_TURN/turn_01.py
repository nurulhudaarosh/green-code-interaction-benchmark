def reconcile_inventory(inventory, transactions):
    """
    Reconcile inventory by applying quantity changes from transactions.

    inventory: {"SKU001": 10, "SKU002": 5}
    transactions: [{"sku": "SKU001", "quantity": 3},
                   {"sku": "SKU002", "quantity": -2}]
    """

    inventory = dict(inventory or {})

    for transaction in transactions or []:
        sku = transaction.get("sku")
        quantity = transaction.get("quantity", 0)

        # Ignore unknown SKUs and invalid quantities
        if sku not in inventory:
            continue
        if not isinstance(quantity, (int, float)) or quantity < 0:
            continue

        inventory[sku] += quantity

    return inventory