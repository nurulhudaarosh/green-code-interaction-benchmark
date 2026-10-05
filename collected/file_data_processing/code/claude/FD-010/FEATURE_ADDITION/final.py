#!/usr/bin/env python3
"""Flatten nested product JSON: one row per valid warehouse stock entry.

Input: a list of products, or an object with a "products" list.

[
  {
    "id": "P100",
    "name": "Widget",
    "category": "tools",
    "warehouses": [
      {"warehouse_id": "W1", "location": "Berlin", "stock": 0},
      {"warehouse_id": "W2", "location": "Paris",  "stock": 25}
    ]
  }
]

Rules:
  * Product required fields: id, name, warehouses (a list).
  * Warehouse required fields: warehouse_id, stock (integer >= 0).
  * Every valid warehouse entry becomes its own row. Zero stock is kept.
  * Invalid warehouse entries are skipped individually.
  * A product is invalid (and counted) if its own fields are bad or it has
    no valid warehouse entries.
  * Rows are sorted by (product_id, warehouse_id).
"""

import argparse
import json
import sys
from typing import Any


def _present(value: Any) -> bool:
    """Not None and not a blank string."""
    return value is not None and not (isinstance(value, str) and not value.strip())


def _valid_stock(value: Any) -> bool:
    # bool is a subclass of int, so exclude it. 0 is valid.
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_product(product: Any) -> bool:
    return (
        isinstance(product, dict)
        and _present(product.get("id"))
        and _present(product.get("name"))
        and isinstance(product.get("warehouses"), list)
    )


def _valid_warehouse(entry: Any) -> bool:
    return (
        isinstance(entry, dict)
        and _present(entry.get("warehouse_id"))
        and _valid_stock(entry.get("stock"))
    )


def load_products(path: str) -> list:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        data = data.get("products", [])
    if not isinstance(data, list):
        raise ValueError("Top-level JSON must be a list or an object with a 'products' list.")
    return data


def flatten_products(products: list) -> tuple[list[dict], int]:
    """Return (sorted_rows, invalid_product_count)."""
    rows: list[dict] = []
    invalid_count = 0

    for product in products:
        if not _valid_product(product):
            invalid_count += 1
            continue

        product_rows = [
            {
                "product_id": product["id"],
                "product_name": product["name"],
                "category": product.get("category"),
                "warehouse_id": wh["warehouse_id"],
                "location": wh.get("location"),
                "stock": wh["stock"],
            }
            for wh in product["warehouses"]
            if _valid_warehouse(wh)
        ]

        if not product_rows:
            invalid_count += 1
            continue

        rows.extend(product_rows)

    rows.sort(key=lambda r: (str(r["product_id"]), str(r["warehouse_id"])))
    return rows, invalid_count


def _self_test() -> None:
    sample = [
        {"id": "B", "name": "Bolt", "warehouses": [
            {"warehouse_id": "W2", "stock": 0},      # zero stock: kept
            {"warehouse_id": "W1", "stock": 5},
            {"warehouse_id": "W3", "stock": -1},     # invalid: skipped
        ]},
        {"id": "A", "name": "Axle", "warehouses": [
            {"warehouse_id": "W1", "stock": 0},      # zero stock: kept
        ]},
        {"id": "C", "name": "", "warehouses": []},   # invalid product
        {"id": "D", "name": "Dial", "warehouses": [
            {"stock": 3},                            # no warehouse_id
        ]},                                          # invalid product
        "not a dict",                                # invalid product
    ]
    rows, invalid = flatten_products(sample)
    assert [(r["product_id"], r["warehouse_id"], r["stock"]) for r in rows] == [
        ("A", "W1", 0), ("B", "W1", 5), ("B", "W2", 0)
    ], rows
    assert invalid == 3, invalid
    print("Self-test passed.", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Flatten nested product JSON.")
    parser.add_argument("input", nargs="?", help="Path to input JSON file")
    parser.add_argument("-o", "--output", help="Write rows to this JSON file (default: stdout)")
    parser.add_argument("--self-test", action="store_true", help="Run built-in checks and exit")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        return 0
    if not args.input:
        parser.error("input file is required (or use --self-test)")

    try:
        products = load_products(args.input)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error reading input: {exc}", file=sys.stderr)
        return 1

    rows, invalid = flatten_products(products)

    payload = json.dumps(rows, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(payload)
    else:
        print(payload)

    print(f"Rows: {len(rows)} | Invalid products: {invalid}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())