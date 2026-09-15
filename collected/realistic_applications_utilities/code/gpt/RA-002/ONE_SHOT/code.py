# Inventory reconciliation: compare expected vs. physical stock,
# calculate variances, flag discrepancies, and produce a reconciliation report.

from collections import defaultdict
from decimal import Decimal, InvalidOperation


def reconcile_inventory(expected_inventory, physical_inventory,
                        tolerance=0, include_zero_variance=False):
    """
    expected_inventory / physical_inventory:
        Dict or iterable of records with:
        {
            "sku": str,
            "quantity": number,
            "unit_cost": optional number
        }

    Returns a reconciliation report containing:
    - expected quantity
    - physical quantity
    - variance
    - variance value
    - status
    - missing/extra SKUs
    - totals
    """

    tolerance = Decimal(str(tolerance))
    expected = defaultdict(lambda: {"quantity": Decimal("0"), "unit_cost": Decimal("0")})
    physical = defaultdict(lambda: {"quantity": Decimal("0"), "unit_cost": Decimal("0")})

    def normalize(records):
        if isinstance(records, dict):
            records = [
                {"sku": sku, "quantity": qty}
                for sku, qty in records.items()
            ]

        result = defaultdict(lambda: {"quantity": Decimal("0"), "unit_cost": Decimal("0")})

        for record in records:
            if not isinstance(record, dict):
                raise TypeError("Each inventory record must be a dictionary.")

            sku = str(record.get("sku", "")).strip()
            if not sku:
                raise ValueError("Every inventory record must have a SKU.")

            try:
                quantity = Decimal(str(record.get("quantity", 0)))
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError(f"Invalid quantity for SKU '{sku}'.")

            if quantity < 0:
                raise ValueError(f"Quantity cannot be negative for SKU '{sku}'.")

            try:
                unit_cost = Decimal(str(record.get("unit_cost", 0)))
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError(f"Invalid unit cost for SKU '{sku}'.")

            result[sku]["quantity"] += quantity

            # Keep the latest non-zero unit cost when provided.
            if unit_cost != 0:
                result[sku]["unit_cost"] = unit_cost

        return result

    expected = normalize(expected_inventory)
    physical = normalize(physical_inventory)

    all_skus = sorted(set(expected) | set(physical))
    reconciliation = []

    total_expected = Decimal("0")
    total_physical = Decimal("0")
    total_variance = Decimal("0")
    total_variance_value = Decimal("0")

    for sku in all_skus:
        expected_qty = expected[sku]["quantity"]
        physical_qty = physical[sku]["quantity"]
        unit_cost = (
            expected[sku]["unit_cost"]
            if expected[sku]["unit_cost"] != 0
            else physical[sku]["unit_cost"]
        )

        variance = physical_qty - expected_qty
        variance_value = variance * unit_cost

        if abs(variance) <= tolerance:
            status = "MATCH"
        elif expected_qty == 0:
            status = "EXTRA"
        elif physical_qty == 0:
            status = "MISSING"
        elif variance > 0:
            status = "OVERAGE"
        else:
            status = "SHORTAGE"

        if include_zero_variance or variance != 0:
            reconciliation.append({
                "sku": sku,
                "expected_quantity": expected_qty,
                "physical_quantity": physical_qty,
                "variance": variance,
                "unit_cost": unit_cost,
                "variance_value": variance_value,
                "status": status
            })

        total_expected += expected_qty
        total_physical += physical_qty
        total_variance += variance
        total_variance_value += variance_value

    matched = sum(1 for r in reconciliation if r["status"] == "MATCH")
    shortages = sum(1 for r in reconciliation if r["status"] == "SHORTAGE")
    overages = sum(1 for r in reconciliation if r["status"] == "OVERAGE")
    missing = sum(1 for r in reconciliation if r["status"] == "MISSING")
    extra = sum(1 for r in reconciliation if r["status"] == "EXTRA")

    return {
        "reconciliation": reconciliation,
        "summary": {
            "total_skus": len(all_skus),
            "matched": matched,
            "shortages": shortages,
            "overages": overages,
            "missing": missing,
            "extra": extra,
            "total_expected_quantity": total_expected,
            "total_physical_quantity": total_physical,
            "total_variance": total_variance,
            "total_variance_value": total_variance_value,
            "reconciled": (
                shortages == 0
                and overages == 0
                and missing == 0
                and extra == 0
            )
        }
    }


# Example
expected_inventory = [
    {"sku": "A101", "quantity": 100, "unit_cost": 10},
    {"sku": "B202", "quantity": 50, "unit_cost": 20},
    {"sku": "C303", "quantity": 25, "unit_cost": 15},
]

physical_inventory = [
    {"sku": "A101", "quantity": 98},
    {"sku": "B202", "quantity": 55},
    {"sku": "D404", "quantity": 10, "unit_cost": 8},
]

report = reconcile_inventory(
    expected_inventory,
    physical_inventory,
    tolerance=0
)

print("Inventory Reconciliation")
print("=" * 70)

for item in report["reconciliation"]:
    print(
        f"{item['sku']}: "
        f"Expected={item['expected_quantity']}, "
        f"Physical={item['physical_quantity']}, "
        f"Variance={item['variance']}, "
        f"Status={item['status']}, "
        f"Variance Value={item['variance_value']}"
    )

print("\nSummary")
print("=" * 70)

for key, value in report["summary"].items():
    print(f"{key}: {value}")