def generate_low_stock_report(records: list, reorder_level: int = 10) -> dict:
    """
    Build a low-stock report from raw inventory records.
    Pipeline: clean records (dedupe + drop invalid) -> classify each SKU
    against the reorder level -> summarize.

    Returns a dict with:
      - 'low_stock': list of {sku, stock, deficit} needing reorder (stock <= reorder_level, stock > 0)
      - 'out_of_stock': list of {sku, stock} with zero stock
      - 'healthy': list of skus above reorder level
      - 'rejected': invalid/duplicate records dropped during cleaning
      - 'summary': counts + total units short
    """
    seen = {}
    order = []
    rejected = []

    # --- Clean: dedupe (last wins) + drop invalid records ---
    for raw in records:
        if not isinstance(raw, dict):
            rejected.append((raw, "not a valid record (expected dict)"))
            continue

        sku = raw.get("sku")
        stock = raw.get("stock")

        if not sku or not isinstance(sku, str) or not sku.strip():
            rejected.append((raw, "missing or empty SKU"))
            continue
        sku = sku.strip().upper()

        if stock is None or isinstance(stock, bool) or not isinstance(stock, (int, float)):
            rejected.append((raw, f"invalid stock value: {stock!r}"))
            continue
        if stock < 0:
            rejected.append((raw, f"negative stock: {stock}"))
            continue

        if sku in seen:
            rejected.append((seen[sku], f"duplicate SKU '{sku}' — superseded by later record"))
        else:
            order.append(sku)
        seen[sku] = {"sku": sku, "stock": stock}

    # --- Classify cleaned records ---
    low_stock, out_of_stock, healthy = [], [], []

    for sku in order:
        stock = seen[sku]["stock"]
        if stock == 0:
            out_of_stock.append({"sku": sku, "stock": stock})
        elif stock <= reorder_level:  # includes the boundary case (stock == reorder_level)
            low_stock.append({
                "sku": sku,
                "stock": stock,
                "deficit": reorder_level - stock
            })
        else:
            healthy.append(sku)

    # Sort low stock by most urgent (smallest stock) first
    low_stock.sort(key=lambda r: r["stock"])

    report = {
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "healthy": healthy,
        "rejected": rejected,
        "summary": {
            "total_valid_skus": len(order),
            "low_stock_count": len(low_stock),
            "out_of_stock_count": len(out_of_stock),
            "healthy_count": len(healthy),
            "rejected_count": len(rejected),
            "total_units_short": sum(r["deficit"] for r in low_stock),
        },
    }
    return report


# --- Example usage ---
if __name__ == "__main__":
    raw_records = [
        {"sku": "sku100", "stock": 5},
        {"sku": "SKU100", "stock": 8},       # duplicate, later wins
        {"sku": "", "stock": 10},            # empty SKU -> rejected
        {"sku": "SKU200", "stock": -3},      # negative -> rejected
        {"sku": "SKU300", "stock": "abc"},   # invalid type -> rejected
        {"sku": "SKU400", "stock": 0},       # out of stock
        {"sku": "SKU500", "stock": 10},      # boundary, reorder_level=10
        {"sku": "SKU600", "stock": 25},      # healthy
        "not_a_record",                       # malformed -> rejected
    ]

    report = generate_low_stock_report(raw_records, reorder_level=10)

    print("=== LOW STOCK REPORT ===")
    for item in report["low_stock"]:
        print(f"  {item['sku']}: {item['stock']} units (need {item['deficit']} more)")

    print("\n=== OUT OF STOCK ===")
    for item in report["out_of_stock"]:
        print(f"  {item['sku']}")

    print("\n=== SUMMARY ===")
    for k, v in report["summary"].items():
        print(f"  {k}: {v}")

    if report["rejected"]:
        print("\n=== REJECTED RECORDS ===")
        for rec, reason in report["rejected"]:
            print(f"  {rec} -> {reason}")