from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class InventoryItem:
    sku: str
    stock: int
    reorder_level: int

@dataclass
class EvaluationResult:
    sku: str
    status: str
    needs_reorder: bool
    current_stock: int

def evaluate_inventory(items: List[InventoryItem], target_skus: List[str]) -> List[EvaluationResult]:
    # 1. Handle Empty Data: Input list or targets are empty
    if not items or not target_skus:
        return []

    # Map inventory for quick lookup
    inventory_map: Dict[str, InventoryItem] = {item.sku: item for item in items}
    results: List[EvaluationResult] = []

    for sku in target_skus:
        # 2. Handle Unknown SKUs: SKU not present in inventory lookup
        if sku not in inventory_map:
            results.append(EvaluationResult(
                sku=sku,
                status="UNKNOWN_SKU",
                needs_reorder=False,
                current_stock=0
            ))
            continue

        item = inventory_map[sku]

        # Handle stock logic & 4. Boundary Reorder Levels (stock <= reorder_level)
        match item.stock:
            # 3. Handle Zero Stock
            case 0:
                results.append(EvaluationResult(
                    sku=sku,
                    status="CRITICAL_OUT_OF_STOCK",
                    needs_reorder=True,
                    current_stock=0
                ))
            # Boundary case: Exact reorder threshold
            case _ if item.stock == item.reorder_level:
                results.append(EvaluationResult(
                    sku=sku,
                    status="BOUNDARY_REORDER_LEVEL",
                    needs_reorder=True,
                    current_stock=item.stock
                ))
            # Below boundary threshold
            case _ if item.stock < item.reorder_level:
                results.append(EvaluationResult(
                    sku=sku,
                    status="BELOW_REORDER_LEVEL",
                    needs_reorder=True,
                    current_stock=item.stock
                ))
            # Healthy stock level
            case _:
                results.append(EvaluationResult(
                    sku=sku,
                    status="HEALTHY_STOCK",
                    needs_reorder=False,
                    current_stock=item.stock
                ))

    return results


# --- Test Cases ---
if __name__ == "__main__":
    inventory = [
        InventoryItem(sku="SKU-BOUNDARY", stock=10, reorder_level=10), # Boundary level
        InventoryItem(sku="SKU-ZERO", stock=0, reorder_level=5),       # Zero stock
        InventoryItem(sku="SKU-OK", stock=50, reorder_level=10),        # Healthy
    ]

    skus_to_check = ["SKU-BOUNDARY", "SKU-ZERO", "SKU-OK", "SKU-MISSING"]

    results = evaluate_inventory(inventory, skus_to_check)
    for r in results:
        print(f"SKU: {r.sku:<12} | Status: {r.status:<22} | Reorder: {str(r.needs_reorder):<5} | Stock: {r.current_stock}")

    # Test Empty Data Case
    assert evaluate_inventory([], skus_to_check) == []
    assert evaluate_inventory(inventory, []) == []