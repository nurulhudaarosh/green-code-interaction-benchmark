import json
from typing import Any


REQUIRED_PRODUCT_FIELDS = ("id", "name", "warehouses")
REQUIRED_WAREHOUSE_FIELDS = ("warehouse", "stock")


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_valid_product(product: Any) -> bool:
    if not isinstance(product, dict):
        return False
    return all(field in product for field in REQUIRED_PRODUCT_FIELDS)


def is_valid_warehouse(warehouse: Any) -> bool:
    if not isinstance(warehouse, dict):
        return False
    if not all(field in warehouse for field in REQUIRED_WAREHOUSE_FIELDS):
        return False
    return isinstance(warehouse["stock"], (int, float))


def flatten_products(products: list) -> tuple[list[dict], int]:
    rows: list[dict] = []
    invalid_count = 0

    for product in products:
        if not is_valid_product(product):
            invalid_count += 1
            continue

        warehouses = product.get("warehouses")
        if not isinstance(warehouses, list):
            invalid_count += 1
            continue

        for warehouse in warehouses:
            if not is_valid_warehouse(warehouse):
                continue
            rows.append(
                {
                    "id": product["id"],
                    "name": product["name"],
                    "warehouse": warehouse["warehouse"],
                    "stock": warehouse["stock"],
                }
            )

    return rows, invalid_count


def sort_rows(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda r: (
            str(r["name"]).lower(),
            str(r["warehouse"]).lower(),
            r["id"],
        ),
    )


def process_products(path: str) -> tuple[list[dict], int]:
    data = load_json(path)

    if isinstance(data, dict):
        products = data.get("products", [])
    elif isinstance(data, list):
        products = data
    else:
        products = []

    rows, invalid_count = flatten_products(products)
    return sort_rows(rows), invalid_count


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python utility.py <products.json>")
        sys.exit(1)

    rows, invalid = process_products(sys.argv[1])

    print(f"Valid rows: {len(rows)}")
    print(f"Invalid products: {invalid}")
    print(json.dumps(rows, indent=2))