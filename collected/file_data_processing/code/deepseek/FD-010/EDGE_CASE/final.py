import json
from typing import Any


REQUIRED_PRODUCT_FIELDS = ["id", "name", "warehouses"]
REQUIRED_WAREHOUSE_FIELDS = ["warehouse", "stock"]


def is_valid_product(product: Any) -> bool:
    if not isinstance(product, dict):
        return False
    for field in REQUIRED_PRODUCT_FIELDS:
        if field not in product:
            return False
    if not isinstance(product["warehouses"], list):
        return False
    return True


def is_valid_warehouse(warehouse: Any) -> bool:
    if not isinstance(warehouse, dict):
        return False
    for field in REQUIRED_WAREHOUSE_FIELDS:
        if field not in warehouse:
            return False
    if not isinstance(warehouse["warehouse"], str):
        return False
    if not isinstance(warehouse["stock"], (int, float)) or isinstance(warehouse["stock"], bool):
        return False
    return True


def flatten_products(data: Any) -> tuple[list[dict], int]:
    rows: list[dict] = []
    invalid_count = 0

    products = data if isinstance(data, list) else [data]

    for product in products:
        if not is_valid_product(product):
            invalid_count += 1
            continue

        product_id = product["id"]
        product_name = product["name"]

        # Empty warehouses list is valid: product counts as valid, no rows emitted.
        for warehouse in product["warehouses"]:
            if not is_valid_warehouse(warehouse):
                invalid_count += 1
                continue
            rows.append({
                "id": product_id,
                "name": product_name,
                "warehouse": warehouse["warehouse"],
                "stock": warehouse["stock"],  # zero stock preserved
            })

    rows.sort(key=lambda r: (str(r["id"]), r["warehouse"]))
    return rows, invalid_count


def process_json(raw: str) -> tuple[list[dict], int]:
    data = json.loads(raw)
    return flatten_products(data)


if __name__ == "__main__":
    sample = json.dumps([
        {
            "id": 1,
            "name": "Widget",
            "warehouses": [
                {"warehouse": "A", "stock": 5},
                {"warehouse": "B", "stock": 0},
            ],
        },
        {
            "id": 2,
            "name": "Empty",
            "warehouses": [],
        },
        {
            "id": 3,
            "name": "ZeroOnly",
            "warehouses": [
                {"warehouse": "A", "stock": 0},
            ],
        },
        {
            "id": 4,
            "name": "Broken",
            "warehouses": [
                {"warehouse": "C"},
            ],
        },
        {
            "name": "Missing ID",
            "warehouses": [],
        },
    ])

    rows, invalid = process_json(sample)
    print(json.dumps(rows, indent=2))
    print(f"Invalid products/warehouses: {invalid}")