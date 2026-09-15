def generate_low_stock_report(records: list, reorder_level: int = 10) -> dict:
    """
    Build a low-stock report from raw inventory records.
    Handles: empty/None input, non-list input, empty-after-cleaning,
    unknown/malformed records, and boundary reorder levels.
    """
    empty_summary = {
        "total_valid_skus": 0, "low_stock_count": 0, "out_of_stock_count": 0,
        "healthy_count": 0, "rejected_count": 0, "total_units_short": 0,
    }

    # --- Guard: empty / missing / wrong-type input ---
    if records is None or not isinstance(records, list):
        return {"low_stock": [], "out_of_stock": [], "healthy": [], "rejected": [],
                "summary": empty_summary, "error": "No records provided (empty or invalid input)."}

    if len(records) == 0:
        return {"low_stock": [], "out_of_stock": [], "healthy": [], "rejected": [],
                "summary": empty_summary, "error": "Empty record list."}

    # --- Guard: invalid reorder_level (boundary/edge config) ---
    if not isinstance(reorder_level, (int, float)) or isinstance(reorder_level, bool):
        reorder_level = 10  # fall back to a sane default
    reorder_level = max(0, reorder_level)  # negative reorder levels make no sense

    seen, order, rejected = {}, [], []

    # --- Clean: dedupe (last wins) + drop invalid records ---
    for raw in records:
        if not isinstance(raw, dict):
            rejected.append((raw, "not a valid record (expected dict)"))
            continue

        sku, stock = raw.get("sku"), raw.get("stock")

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

    # --- Guard: nothing survived cleaning ---
    if not order:
        return {"low_stock": [], "out_of_stock": [], "healthy": [], "rejected": rejected,
                "summary": {**empty_summary, "rejected_count": len(rejected)},
                "error": "No valid records after cleaning."}

    # --- Classify (boundary case: stock == reorder_level counts as low_stock) ---
    low_stock, out_of_stock, healthy = [], [], []
    for sku in order:
        stock = seen[sku]["stock"]
        if stock == 0:
            out_of_stock.append({"sku": sku, "stock": stock})
        elif stock <= reorder_level:
            low_stock.append({"sku": sku, "stock": stock, "deficit": reorder_level - stock})
        else:
            healthy.append(sku)

    low_stock.sort(key=lambda r: r["stock"])

    return {
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


# --- Example usage: boundary + empty cases ---
if __name__ == "__main__":
    cases = [
        ("None input", None, 10),
        ("Not a list", {"sku": "A1", "stock": 5}, 10),
        ("Empty list", [], 10),
        ("All invalid -> empty after cleaning", [{"sku": "", "stock": -1}], 10),
        ("Boundary stock == reorder_level", [{"sku": "SKU1", "stock": 10}], 10),
        ("Negative reorder_level normalized to 0", [{"sku": "SKU2", "stock": 0}], -5),
        ("Bad reorder_level type falls back to default", [{"sku": "SKU3", "stock": 9}], "ten"),
    ]

    for label, recs, level in cases:
        print(f"--- {label} ---")
        print(generate_low_stock_report(recs, level))
        print()