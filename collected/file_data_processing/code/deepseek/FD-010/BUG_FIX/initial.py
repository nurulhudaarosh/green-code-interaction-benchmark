import json
from typing import Any

REQUIRED_PRODUCT_FIELDS = ["id", "name", "warehouses"]
REQUIRED_WAREHOUSE_FIELDS = ["warehouse_id", "stock"]


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
    if not isinstance(warehouse["stock"], (int, float)):
        return False
    return True


def flatten_products(data: Any) -> tuple[list[dict], int]:
    rows: list[dict] = []
    invalid_count = 0

    products = data if isinstance(data, list) else data.get("products", [])

    for product in products:
        if not is_valid_product(product):
            invalid_count += 1
            continue

        valid_warehouses = [w for w in product["warehouses"] if is_valid_warehouse(w)]

        if not valid_warehouses:
            invalid_count += 1
            continue

        for wh in valid_warehouses:
            rows.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "warehouse_id": wh["warehouse_id"],
                "stock": wh["stock"],
                "category": product.get("category"),
                "price": product.get("price"),
                "location": wh.get("location"),
            })

    return rows, invalid_count


def sort_rows(rows: list[dict], sort_keys: list[str] | None = None) -> list[dict]:
    if sort_keys is None:
        sort_keys = ["product_id", "warehouse_id"]

    def sort_key(row: dict):
        return tuple((row.get(k) is None, row.get(k)) for k in sort_keys)

    return sorted(rows, key=sort_key)


def process_products(json_input: Any, sort_keys: list[str] | None = None) -> dict:
    data = load_json(json_input) if isinstance(json_input, str) else json_input
    rows, invalid_count = flatten_products(data)
    rows = sort_rows(rows, sort_keys)
    return {
        "rows": rows,
        "invalid_count": invalid_count,
        "total_rows": len(rows),
    }