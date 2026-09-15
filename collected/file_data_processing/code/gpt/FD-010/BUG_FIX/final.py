import json
import sys


def main():
    if len(sys.argv) != 3:
        print("Usage: python utility.py input.json output.json")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        print("0")
        return

    products = data.get("products", []) if isinstance(data, dict) else []

    if not isinstance(products, list):
        products = []

    rows = []
    invalid_products = 0

    for product in products:
        try:
            if not isinstance(product, dict):
                invalid_products += 1
                continue

            if not {"id", "name", "warehouses"}.issubset(product):
                invalid_products += 1
                continue

            warehouses = product["warehouses"]

            if not isinstance(warehouses, list):
                invalid_products += 1
                continue

            product_rows = []
            valid = True

            for warehouse in warehouses:
                if not isinstance(warehouse, dict):
                    valid = False
                    break

                if not {"id", "stock"}.issubset(warehouse):
                    valid = False
                    break

                if isinstance(warehouse["stock"], bool):
                    valid = False
                    break

                if not isinstance(warehouse["stock"], (int, float)):
                    valid = False
                    break

                product_rows.append({
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "warehouse_id": warehouse["id"],
                    "stock": warehouse["stock"]
                })

            if not valid:
                invalid_products += 1
                continue

            rows.extend(product_rows)

        except (KeyError, TypeError, ValueError):
            invalid_products += 1
            continue

    rows.sort(
        key=lambda row: (
            str(row["product_id"]),
            str(row["warehouse_id"])
        )
    )

    result = {
        "rows": rows,
        "invalid_products": invalid_products
    }

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except OSError:
        print("0")
        return

    print(invalid_products)


if __name__ == "__main__":
    main()