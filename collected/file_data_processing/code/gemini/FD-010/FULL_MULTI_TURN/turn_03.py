import json
from typing import Any, Dict, List, Tuple


def process_inventory(data: Any) -> Tuple[List[Dict[str, Any]], int]:
    """
    Reads nested product JSON data and flattens EVERY valid warehouse stock entry 
    into a separate row, explicitly retaining items with zero stock (`stock == 0`).

    Rules:
    - Skips and counts malformed product dictionaries or products missing required fields.
    - Flattens each valid warehouse entry into its own dictionary row.
    - Keeps stock values >= 0 (including 0). Ignores negative, missing, or non-numeric stock.
    - Counts products with zero valid warehouse entries as invalid/skipped.
    - Sorts the final flattened rows by product_id, then warehouse location.

    :param data: List of product dictionaries or loaded JSON structure.
    :return: Tuple of (flattened_rows, total_invalid_products_count)
    """
    flattened_rows: List[Dict[str, Any]] = []
    invalid_product_count = 0

    if not isinstance(data, list):
        return [], 1

    for product in data:
        try:
            # 1. Skip non-dict product entries
            if not isinstance(product, dict):
                invalid_product_count += 1
                continue

            product_id = product.get("id")
            product_name = product.get("name")
            warehouses = product.get("warehouses")

            # 2. Validate top-level product schema
            if (
                product_id is None
                or not isinstance(product_name, str)
                or not product_name.strip()
                or not isinstance(warehouses, list)
            ):
                invalid_product_count += 1
                continue

            valid_warehouses_found = 0

            # 3. Flatten every valid warehouse entry into its own row
            for wh in warehouses:
                if not isinstance(wh, dict):
                    continue

                location = wh.get("location")
                stock = wh.get("stock")

                # Validate warehouse fields (stock can be 0, but not negative or non-numeric)
                if (
                    not isinstance(location, str)
                    or not location.strip()
                    or stock is None
                    or isinstance(stock, bool)  # exclude booleans (True/False)
                    or not isinstance(stock, (int, float))
                    or stock < 0
                ):
                    continue

                # Output a separate row per valid warehouse stock entry
                flattened_rows.append(
                    {
                        "product_id": product_id,
                        "product_name": product_name,
                        "location": location,
                        "stock": stock,
                    }
                )
                valid_warehouses_found += 1

            # Count products that yielded no valid warehouse rows
            if valid_warehouses_found == 0:
                invalid_product_count += 1

        except Exception:
            invalid_product_count += 1
            continue

    # 4. Sort all separate flattened rows by product_id, then location
    flattened_rows.sort(key=lambda row: (row["product_id"], row["location"]))

    return flattened_rows, invalid_product_count


# ==========================================
# Example Usage & Verification
# ==========================================
if __name__ == "__main__":
    raw_json = """
    [
        {
            "id": 302,
            "name": "4K Monitor",
            "warehouses": [
                {"location": "US-East", "stock": 25},
                {"location": "US-Central", "stock": 0},
                {"location": "US-West", "stock": 0}
            ]
        },
        {
            "id": 301,
            "name": "Mechanical Keyboard",
            "warehouses": [
                {"location": "EU-Main", "stock": 100},
                {"location": "US-East", "stock": 0},
                {"location": "Corrupted-Location", "stock": -50}
            ]
        },
        "malformed_product_string_entry",
        {
            "id": 303,
            "name": "Out of Stock Product",
            "warehouses": [
                {"location": "Global-Hub", "stock": 0}
            ]
        }
    ]
    """

    data = json.loads(raw_json)
    rows, skipped_count = process_inventory(data)

    print(f"Skipped / Invalid Products Count: {skipped_count}\n")
    print("Flattened Separate Rows (including Zero Stock):")
    print(json.dumps(rows, indent=2))