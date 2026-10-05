#!/usr/bin/env python3
"""
Flatten nested product JSON into sorted warehouse-level rows.

Expected input (a list of products, or {"products": [...]}):

[
  {
    "product_id": "P-100",
    "name": "Widget",
    "category": "Hardware",            # optional
    "warehouses": [
      {"warehouse_id": "W-2", "location": "Berlin", "stock": 0},
      {"warehouse_id": "W-1", "location": "Austin", "stock": 25}
    ]
  },
  {"product_id": "P-200", "name": "Gadget", "warehouses": []}   # valid, empty
]

Rules:
  * A product is MALFORMED if it is not an object, has a missing/blank or
    non-scalar `product_id`, a missing/blank `name`, or `warehouses` that is
    missing/null/not a list. Malformed products are skipped and counted;
    processing continues.
  * An EMPTY `warehouses` list ([]) is VALID. The product is not malformed,
    is not counted as invalid, and is tallied in `empty_products`.
    By default it contributes no rows (there are no warehouse entries to
    flatten). With --include-empty it contributes one placeholder row with
    warehouse_id/location/stock set to null, so the product is preserved in
    the output. Placeholder stock is null, never 0, so it is not mistaken
    for real zero stock.
  * Every valid warehouse entry becomes its own row. An entry is valid if it
    is an object with a non-blank scalar `warehouse_id` and an integer
    `stock` >= 0 (bool rejected). ZERO STOCK IS VALID and is always kept.
    Invalid entries are skipped and counted separately.
  * Each product is processed in isolation: an unexpected error while
    handling one product marks only that product as malformed, and none of
    its rows are kept.
  * Output rows are sorted by (product_id, warehouse_id); placeholder rows
    sort before real rows of the same product.
"""

import argparse
import csv
import json
import sys
from typing import Any

REQUIRED_PRODUCT_FIELDS = ("product_id", "name", "warehouses")
REQUIRED_WAREHOUSE_FIELDS = ("warehouse_id", "stock")


def _is_missing(value: Any) -> bool:
    """None or blank string counts as missing. 0, False and [] do NOT."""
    return value is None or (isinstance(value, str) and not value.strip())


def _is_valid_id(value: Any) -> bool:
    """IDs must be a non-blank string or a non-bool integer."""
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, str) and bool(value.strip())


def is_valid_product(product: Any) -> bool:
    if not isinstance(product, dict):
        return False
    # [] is not "missing", so an empty warehouses list passes here
    if any(_is_missing(product.get(f)) for f in REQUIRED_PRODUCT_FIELDS):
        return False
    if not _is_valid_id(product["product_id"]):
        return False
    return isinstance(product["warehouses"], list)


def is_valid_warehouse(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    # stock == 0 passes here: _is_missing only rejects None / blank strings
    if any(_is_missing(entry.get(f)) for f in REQUIRED_WAREHOUSE_FIELDS):
        return False
    if not _is_valid_id(entry["warehouse_id"]):
        return False
    stock = entry["stock"]
    # bool is a subclass of int, so exclude it explicitly
    return isinstance(stock, int) and not isinstance(stock, bool) and stock >= 0


def load_products(path: str) -> list:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and isinstance(data.get("products"), list):
        return data["products"]
    if isinstance(data, list):
        return data
    raise ValueError("Top-level JSON must be a list or an object with a 'products' list.")


def _row(product: dict, entry: dict | None) -> dict:
    return {
        "product_id": product["product_id"],
        "name": product["name"],
        "category": product.get("category"),
        "warehouse_id": entry["warehouse_id"] if entry else None,
        "location": entry.get("location") if entry else None,
        "stock": entry["stock"] if entry else None,  # real zero stays 0
    }


def flatten_product(product: Any, include_empty: bool = False) -> tuple[list[dict], int, bool]:
    """
    Flatten one product into one row per valid warehouse entry.
    Returns (rows, invalid_warehouse_count, is_empty_product).
    Raises ValueError if the product is malformed.
    """
    if not is_valid_product(product):
        raise ValueError("malformed product")

    warehouses = product["warehouses"]
    if not warehouses:  # valid product with an empty warehouse list
        return ([_row(product, None)] if include_empty else []), 0, True

    rows: list[dict] = []
    bad_entries = 0
    for entry in warehouses:
        if not is_valid_warehouse(entry):
            bad_entries += 1
            continue
        rows.append(_row(product, entry))
    return rows, bad_entries, False


def _sort_key(row: dict) -> tuple:
    wid = row["warehouse_id"]
    # str() keeps sorting safe for mixed int/str ids; None (placeholder) sorts first
    return (str(row["product_id"]), "" if wid is None else str(wid))


def flatten_products(products: list, include_empty: bool = False) -> tuple[list[dict], dict]:
    """Return (sorted_rows, stats). Never aborts because of a bad product."""
    rows: list[dict] = []
    stats = {
        "total_products": len(products),
        "invalid_products": 0,
        "empty_products": 0,
        "invalid_warehouse_entries": 0,
        "zero_stock_rows": 0,
        "rows": 0,
    }

    for product in products:
        try:
            # Rows are staged per product so a failure can't leave partial output.
            product_rows, bad_entries, is_empty = flatten_product(product, include_empty)
        except Exception:  # malformed or unexpected: skip, count, keep going
            stats["invalid_products"] += 1
            continue
        rows.extend(product_rows)
        stats["invalid_warehouse_entries"] += bad_entries
        stats["empty_products"] += int(is_empty)

    rows.sort(key=_sort_key)
    stats["rows"] = len(rows)
    # `is 0`-style check via type: placeholder stock is None, so it never counts
    stats["zero_stock_rows"] = sum(1 for r in rows if r["stock"] == 0)
    return rows, stats


def write_csv(rows: list[dict], out) -> None:
    fields = ["product_id", "name", "category", "warehouse_id", "location", "stock"]
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)  # None is written as an empty cell; 0 is written as "0"


def main() -> int:
    parser = argparse.ArgumentParser(description="Flatten nested product/warehouse JSON.")
    parser.add_argument("input", help="Path to input JSON file")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Emit one placeholder row (null warehouse fields) for valid products "
        "with an empty warehouses list.",
    )
    args = parser.parse_args()

    try:
        products = load_products(args.input)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error reading input: {exc}", file=sys.stderr)
        return 1

    rows, stats = flatten_products(products, include_empty=args.include_empty)

    out = open(args.output, "w", encoding="utf-8", newline="") if args.output else sys.stdout
    try:
        if args.format == "csv":
            write_csv(rows, out)
        else:
            json.dump(rows, out, indent=2)
            out.write("\n")
    finally:
        if out is not sys.stdout:
            out.close()

    print(
        f"Products: {stats['total_products']} | "
        f"malformed products skipped: {stats['invalid_products']} | "
        f"empty-warehouse products: {stats['empty_products']} | "
        f"invalid warehouse entries skipped: {stats['invalid_warehouse_entries']} | "
        f"rows written: {stats['rows']} (zero-stock: {stats['zero_stock_rows']})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())