def clean_inventory_records(records: list) -> tuple[list, list]:
    """
    Clean a list of inventory record dicts (e.g. [{"sku": "A1", "stock": 5}, ...]).
    - Removes duplicate records (same SKU appearing more than once; keeps the
      last occurrence, since later entries usually represent the latest count).
    - Removes invalid records: missing/empty SKU, non-numeric or negative stock,
      or malformed entries (not a dict / missing required keys).
    Returns (cleaned_records, rejected_records) so nothing is silently lost.
    """
    seen = {}          # sku -> cleaned record (dedup, last-write-wins)
    rejected = []       # (record, reason)
    order = []          # preserve first-seen order of valid SKUs

    for raw in records:
        # Malformed entry (not a dict)
        if not isinstance(raw, dict):
            rejected.append((raw, "not a valid record (expected dict)"))
            continue

        sku = raw.get("sku")
        stock = raw.get("stock")

        # Missing/empty SKU
        if not sku or not isinstance(sku, str) or not sku.strip():
            rejected.append((raw, "missing or empty SKU"))
            continue
        sku = sku.strip().upper()

        # Invalid stock value
        if stock is None or isinstance(stock, bool) or not isinstance(stock, (int, float)):
            rejected.append((raw, f"invalid stock value: {stock!r}"))
            continue
        if stock < 0:
            rejected.append((raw, f"negative stock: {stock}"))
            continue

        # Duplicate handling: keep last occurrence, but flag the earlier one
        if sku in seen:
            rejected.append((seen[sku], f"duplicate SKU '{sku}' — superseded by later record"))
        else:
            order.append(sku)

        seen[sku] = {"sku": sku, "stock": stock}

    cleaned = [seen[s] for s in order]
    return cleaned, rejected


# --- Example usage ---
if __name__ == "__main__":
    raw_records = [
        {"sku": "sku100", "stock": 5},
        {"sku": "SKU100", "stock": 8},       # duplicate (case-insensitive), later wins
        {"sku": "", "stock": 10},            # empty SKU
        {"sku": "SKU200", "stock": -3},      # negative stock
        {"sku": "SKU300", "stock": "abc"},   # invalid stock type
        {"sku": "SKU400", "stock": 0},       # valid, zero stock
        "not_a_record",                       # malformed
        {"sku": "SKU400", "stock": 12},      # duplicate of SKU400
    ]

    cleaned, rejected = clean_inventory_records(raw_records)

    print("Cleaned records:")
    for r in cleaned:
        print(" ", r)

    print("\nRejected records:")
    for rec, reason in rejected:
        print(f"  {rec} -> {reason}")