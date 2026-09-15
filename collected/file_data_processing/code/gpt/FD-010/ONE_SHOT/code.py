import json
import sys


def main():
    if len(sys.argv) != 3:
        print("Usage: python utility.py input.json output.json")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        with open(input_file, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        print("Invalid input file")
        return

    products = data.get("products")

    if not isinstance(products, list):
        print("Invalid input structure")
        return

    rows = []
    invalid_products = 0

    for product in products:
        if not isinstance(product, dict):
            invalid_products += 1
            continue

        product_id = product.get("product_id")
        name = product.get("name")
        warehouses = product.get("warehouses")

        if (
            product_id is None
            or not isinstance(product_id, (str, int))
            or not isinstance(name, str)
            or not name.strip()
            or not isinstance(warehouses, list)
        ):
            invalid_products += 1
            continue

        valid_product = True
        product_rows = []

        for warehouse in warehouses:
            if not isinstance(warehouse, dict):
                continue

            warehouse_id = warehouse.get("warehouse_id")
            stock = warehouse.get("stock")

            if (
                warehouse_id is None
                or not isinstance(warehouse_id, (str, int))
                or isinstance(stock, bool)
                or not isinstance(stock, (int, float))
                or stock < 0
            ):
                continue

            product_rows.append({
                "product_id": product_id,
                "name": name,
                "warehouse_id": warehouse_id,
                "stock": stock
            })

        if valid_product:
            rows.extend(product_rows)

    rows.sort(
        key=lambda row: (
            str(row["product_id"]),
            str(row["warehouse_id"])
        )
    )

    result = {
        "invalid_products": invalid_products,
        "rows": rows
    }

    try:
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=2)
    except OSError:
        print("Could not write output file")


if __name__ == "__main__":
    main()