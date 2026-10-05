import json
from typing import Any, Dict, List, Tuple


def process_product_catalog(json_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Processes a nested product JSON structure:
    - Validates required fields ('id', 'name', 'warehouses').
    - Flattens valid warehouse entries into tabular records.
    - Preserves zero-stock items while validating warehouse fields.
    - Counts invalid/malformed product records.
    - Sorts output rows by product ID and warehouse name.

    Returns:
        Tuple containing:
            - List of flattened warehouse rows (sorted)
            - Count of invalid product entries
    """
    flattened_rows: List[Dict[str, Any]] = []
    invalid_count = 0

    for item in json_data:
        # Validate base product object structure
        if not isinstance(item, dict):
            invalid_count += 1
            continue

        product_id = item.get("id")
        product_name = item.get("name")
        warehouses = item.get("warehouses")

        # Check required product-level fields
        if product_id is None or not product_name or not isinstance(warehouses, list):
            invalid_count += 1
            continue

        has_valid_warehouse = False

        for wh in warehouses:
            if not isinstance(wh, dict):
                continue

            wh_name = wh.get("warehouse_name")
            stock = wh.get("stock")

            # Validate warehouse required fields (stock can be 0)
            if not wh_name or stock is None or not isinstance(stock, (int, float)):
                continue

            flattened_rows.append({
                "product_id": product_id,
                "product_name": product_name,
                "category": item.get("category", "Uncategorized"),
                "warehouse_name": wh_name,
                "location": wh.get("location", "Unknown"),
                "stock": stock
            })
            has_valid_warehouse = True

        # If a product had no valid warehouse entries, flag it as invalid
        if not has_valid_warehouse:
            invalid_count += 1

    # Sort flattened rows by product_id, then warehouse_name
    flattened_rows.sort(key=lambda x: (x["product_id"], x["warehouse_name"]))

    return flattened_rows, invalid_count


# ==========================================
# Example Usage & Verification
# ==========================================
if __name__ == "__main__":
    sample_json_str = """
    [
        {
            "id": 101,
            "name": "Wireless Mouse",
            "category": "Electronics",
            "warehouses": [
                {"warehouse_name": "East Coast Hub", "location": "NY", "stock": 150},
                {"warehouse_name": "West Coast Hub", "location": "CA", "stock": 0}
            ]
        },
        {
            "id": 102,
            "name": "Mechanical Keyboard",
            "category": "Electronics",
            "warehouses": [
                {"warehouse_name": "Central Depot", "location": "TX", "stock": 42}
            ]
        },
        {
            "id": 103,
            "name": "Invalid Product Missing Warehouses"
        },
        {
            "id": 104,
            "name": "Broken Warehouse Entry",
            "warehouses": [
                {"warehouse_name": "North Hub", "stock": null}
            ]
        }
    ]
    """

    data = json.loads(sample_json_str)
    flattened, invalid_products = process_product_catalog(data)

    print(f"--- Processed Records (Total Invalid Products: {invalid_products}) ---")
    print(json.dumps(flattened, indent=2))