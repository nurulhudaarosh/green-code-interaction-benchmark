#!/usr/bin/env python3
"""Flatten nested product/warehouse JSON into sorted rows.

Expected input (a list, or an object with a "products" list):

[
  {
    "sku": "A-100",
    "name": "Widget",
    "warehouses": [
      {"warehouse_id": "W1", "location": "Berlin", "quantity": 12},
      {"warehouse_id": "W2", "location": "Austin", "quantity": 0}
    ]
  }
]

Rules:
- A product is invalid if it is not an object, or if `sku` / `name` is
  missing or not a non-empty string, or if `warehouses` is not a list.
  Invalid products are counted and skipped.
- A warehouse entry is valid if `warehouse_id` is a non-empty string and
  `quantity` is an integer >= 0. Invalid entries are skipped.
- Zero stock is valid and is kept.
- Rows are sorted by (sku, warehouse_id).
"""

import argparse
import csv
import json
import sys
from typing import Any

PRODUCT_REQUIRED = ("sku", "name", "warehouses")
WAREHOUSE_REQUIRED = ("warehouse_id", "quantity")
OUTPUT_FIELDS = ["sku", "name", "warehouse_id", "location", "quantity"]


def _non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _valid_quantity(value: Any) -> bool:
    # bool is a subclass of int, so exclude it explicitly.
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def is_valid_product(product: Any) -> bool:
    if not isinstance(product, dict):
        return False
    if any(field not in product for field in PRODUCT_REQUIRED):
        return False
    return (
        _non_empty_str(product["sku"])
        and _non_empty_str(product["name"])
        and isinstance(product["warehouses"], list)
    )


def is_valid_warehouse(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if any(field not in entry for field in WAREHOUSE_REQUIRED):
        return False
    return _non_empty_str(entry["warehouse_id"]) and _valid_quantity(entry["quantity"])


def flatten_products(data: Any) -> tuple[list[dict], int]:
    """Return (sorted flat rows, count of invalid products)."""
    if isinstance(data, dict):
        data = data.get("products", [])
    if not isinstance(data, list):
        raise ValueError("Top-level JSON must be a list or an object with a 'products' list.")

    rows: list[dict] = []
    invalid_products = 0

    for product in data:
        if not is_valid_product(product):
            invalid_products += 1
            continue

        for entry in product["warehouses"]:
            if not is_valid_warehouse(entry):
                continue
            rows.append(
                {
                    "sku": product["sku"].strip(),
                    "name": product["name"].strip(),
                    "warehouse_id": entry["warehouse_id"].strip(),
                    "location": entry.get("location"),
                    "quantity": entry["quantity"],  # zero is preserved
                }
            )

    rows.sort(key=lambda r: (r["sku"], r["warehouse_id"]))
    return rows, invalid_products


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_csv(rows: list[dict], out) -> None:
    writer = csv.DictWriter(out, fieldnames=OUTPUT_FIELDS)
    writer.writeheader()
    writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Flatten nested product JSON.")
    parser.add_argument("input", help="Path to the input JSON file")
    parser.add_argument("-o", "--output", help="Write CSV here (default: stdout)")
    args = parser.parse_args()

    try:
        data = load_json(args.input)
        rows, invalid_count = flatten_products(data)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            write_csv(rows, fh)
    else:
        write_csv(rows, sys.stdout)

    print(f"Rows: {len(rows)} | Invalid products: {invalid_count}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())