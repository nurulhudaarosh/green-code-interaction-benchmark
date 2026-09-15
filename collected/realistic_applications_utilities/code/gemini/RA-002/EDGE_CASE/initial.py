from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class InventoryResult:
    status: str
    reorder_needed: bool
    stock_level: int


def process_inventory_batch(
    inventory_db: Dict[str, int], reorder_levels: Dict[str, int], sku_list: List[str]
) -> Dict[str, InventoryResult]:
    results = {}

    # 1. Handle Empty Data (Input validation)
    if not sku_list:
        return results

    for sku in sku_list:
        # 2. Handle Unknown SKUs
        if sku not in inventory_db or sku not in reorder_levels:
            results[sku] = InventoryResult(
                status="UNKNOWN_SKU", reorder_needed=False, stock_level=-1
            )
            continue

        stock = inventory_db[sku]
        reorder_threshold = reorder_levels[sku]

        # Boundary Reorder Check: Triggers reorder when stock is AT or BELOW boundary (<=)
        needs_reorder = stock <= reorder_threshold

        # 3. Handle Zero Stock
        if stock == 0:
            results[sku] = InventoryResult(
                status="OUT_OF_STOCK", reorder_needed=True, stock_level=0
            )
        # 4. Handle Boundary Reorder Levels and Normal Stock
        elif needs_reorder:
            results[sku] = InventoryResult(
                status="REORDER_BOUNDARY_REACHED" if stock == reorder_threshold else "LOW_STOCK",
                reorder_needed=True,
                stock_level=stock,
            )
        else:
            results[sku] = InventoryResult(
                status="IN_STOCK", reorder_needed=False, stock_level=stock
            )

    return results


# Example Usage & Test Scenarios
if __name__ == "__main__":
    db = {"SKU_NORMAL": 50, "SKU_BOUNDARY": 10, "SKU_ZERO": 0}
    reorder_thresholds = {"SKU_NORMAL": 10, "SKU_BOUNDARY": 10, "SKU_ZERO": 10}

    # Empty Data
    assert process_inventory_batch(db, reorder_thresholds, []) == {}

    # Batch Processing across all edge cases
    test_skus = ["SKU_NORMAL", "SKU_BOUNDARY", "SKU_ZERO", "SKU_MISSING"]
    output = process_inventory_batch(db, reorder_thresholds, test_skus)

    for sku, res in output.items():
        print(f"{sku}: Status='{res.status}', Reorder={res.reorder_needed}, Stock={res.stock_level}")