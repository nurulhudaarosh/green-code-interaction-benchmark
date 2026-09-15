from collections import defaultdict

def reconcile_inventory(records):
    """
    Reconcile inventory records by SKU.

    Each record must contain:
        {"sku": <str>, "quantity": <int/float>}

    Rules:
    - SKU must be non-empty.
    - Quantity must be numeric and >= 0.
    - Duplicate SKUs are combined by summing quantities.
    - Invalid records raise ValueError.
    """
    inventory = defaultdict(float)

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each inventory record must be a dictionary.")

        sku = record.get("sku")
        quantity = record.get("quantity")

        if not isinstance(sku, str) or not sku.strip():
            raise ValueError("SKU must be a non-empty string.")

        # bool is excluded because bool is a subclass of int in Python.
        if isinstance(quantity, bool) or not isinstance(quantity, (int, float)):
            raise ValueError(f"Invalid quantity for SKU '{sku}'.")

        if quantity < 0:
            raise ValueError(f"Quantity cannot be negative for SKU '{sku}'.")

        inventory[sku.strip()] += quantity

    # Return integers as ints when possible.
    return {
        sku: int(qty) if isinstance(qty, float) and qty.is_integer() else qty
        for sku, qty in inventory.items()
    }


# Example
records = [
    {"sku": "A101", "quantity": 10},
    {"sku": "B202", "quantity": 5},
    {"sku": "A101", "quantity": 7},   # duplicate SKU -> 17
]

print(reconcile_inventory(records))
# {'A101': 17, 'B202': 5}