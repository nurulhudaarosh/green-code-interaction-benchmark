import json
import sys


def process_products(data):
    rows = []
    invalid_products = 0

    products = data.get("products", [])

    if not isinstance(products, list):
        return rows, 0

    for product in products:
        if not isinstance(product, dict):
            invalid_products += 1
            continue

        product_id = product.get("product_id")
        product_name = product.get("product_name")
        warehouses = product.get("warehouses")

        if (
            not isinstance(product_id, (str, int))
            or not isinstance(product_name, str)
            or not isinstance(warehouses, list)
        ):
            invalid_products += 1
            continue

        valid_product = True
        product_rows = []

        for warehouse in warehouses:
            if not isinstance(warehouse, dict):
                valid_product = False
                break

            warehouse_id = warehouse.get("warehouse_id")
            stock = warehouse.get("stock")

            if (
                not isinstance(warehouse_id, (str, int))
                or isinstance(warehouse_id, bool)
                or not isinstance(stock, (int, float))
                or isinstance(stock, bool)
                or stock < 0
            ):
                valid_product = False
                break

            product_rows.append({
                "product_id": product_id,
                "product_name": product_name,
                "warehouse_id": warehouse_id,
                "stock": stock
            })

        if not valid_product:
            invalid_products += 1
            continue

        rows.extend(product_rows)

    rows.sort(
        key=lambda row: (
            str(row["product_id"]),
            str(row["warehouse_id"])
        )
    )

    return rows, invalid_products


def main():
    if len(sys.argv) != 2:
        print("Usage: python utility.py input.json")
        sys.exit(1)

    input_file = sys.argv[1]

    try:
        with open(input_file, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        print("Invalid JSON file.")
        sys.exit(1)

    if not isinstance(data, dict):
        print("Invalid JSON structure.")
        sys.exit(1)

    rows, invalid_products = process_products(data)

    output = {
        "products": rows,
        "invalid_products": invalid_products
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()