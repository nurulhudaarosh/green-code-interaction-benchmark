from typing import Optional


# Simulated inventory: SKU -> (stock, reorder_level, reorder_qty)
INVENTORY = {
    "SKU-001": {"stock": 5,  "reorder_level": 10, "reorder_qty": 50},  # below level
    "SKU-002": {"stock": 0,  "reorder_level": 10, "reorder_qty": 50},  # zero stock
    "SKU-003": {"stock": 10, "reorder_level": 10, "reorder_qty": 50},  # boundary
    "SKU-004": {"stock": 25, "reorder_level": 10, "reorder_qty": 50},  # sufficient
}


def check_reorder(sku: str, inventory: Optional[dict] = None) -> dict:
    """Return a reorder decision for a single SKU, handling edge cases."""
    inventory = inventory if inventory is not None else INVENTORY

    # Unknown SKU
    if sku not in inventory:
        return {"sku": sku, "action": "skip", "reason": "unknown_sku", "qty": 0}

    item = inventory[sku]
    stock = item.get("stock", 0)
    level = item.get("reorder_level", 0)
    qty = item.get("reorder_qty", 0)

    # Zero stock — always reorder (unless reorder is disabled)
    if stock == 0:
        if level > 0 and qty > 0:
            return {"sku": sku, "action": "reorder", "reason": "zero_stock", "qty": qty}
        return {"sku": sku, "action": "skip", "reason": "reorder_disabled", "qty": 0}

    # Boundary: stock == reorder_level triggers reorder (<= rule)
    if stock <= level:
        return {"sku": sku, "action": "reorder", "reason": "at_or_below_level", "qty": qty}

    return {"sku": sku, "action": "skip", "reason": "sufficient_stock", "qty": 0}


def process(skus: Optional[list] = None, inventory: Optional[dict] = None) -> list:
    """Process a batch of SKUs. Empty/None input returns an empty list."""
    if not skus:                       # handles [] and None
        return []
    return [check_reorder(s, inventory) for s in skus]


# --- Demo ---
if __name__ == "__main__":
    # Empty data
    print(process([]))                 # []
    print(process(None))               # []

    # Mixed cases: below, zero stock, boundary, sufficient, unknown
    for row in process(["SKU-001", "SKU-002", "SKU-003", "SKU-004", "SKU-999"]):
        print(row)