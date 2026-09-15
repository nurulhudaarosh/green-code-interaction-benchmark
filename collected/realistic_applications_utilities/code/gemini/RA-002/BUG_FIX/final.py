from datetime import datetime
import numpy as np
import pandas as pd


def reconcile_inventory(
    system_df: pd.DataFrame,
    count_df: pd.DataFrame,
    cost_df: pd.DataFrame,
    unit_variance_threshold: float = 10.0,
    cost_variance_threshold: float = 100.0,
) -> dict[str, pd.DataFrame]:
    """Reconciles physical inventory counts against system records across multiple locations.

    Validates numeric quantities/costs, enforces non-negativity, consolidates duplicate SKU entries,
    and calculates operational and financial variance metrics.

    Parameters:
    - system_df: System stock records [sku, location, system_qty]
    - count_df: Physical count records [sku, location, physical_qty]
    - cost_df: Unit cost & metadata [sku, item_name, category, unit_cost]
    - unit_variance_threshold: Flag if abs(unit variance) >= threshold
    - cost_variance_threshold: Flag if abs(cost variance) >= threshold

    Returns:
    - Dictionary containing item-level reconciliation, category summary, and audit exceptions.
    """
    # Make copies to avoid mutating input DataFrames
    sys_df = system_df.copy()
    phy_df = count_df.copy()
    cst_df = cost_df.copy()

    # 1. Standardize string formatting for primary key joins
    for df, key in [
        (sys_df, "system_qty"),
        (phy_df, "physical_qty"),
        (cst_df, "unit_cost"),
    ]:
        df["sku"] = df["sku"].astype(str).str.strip().str.upper()
        if "location" in df.columns:
            df["location"] = df["location"].astype(str).str.strip().str.upper()

    # 2. Invalid Quantity & Type Validation
    sys_df["system_qty"] = pd.to_numeric(sys_df["system_qty"], errors="coerce")
    phy_df["physical_qty"] = pd.to_numeric(
        phy_df["physical_qty"], errors="coerce"
    )
    cst_df["unit_cost"] = pd.to_numeric(cst_df["unit_cost"], errors="coerce")

    if (
        sys_df["system_qty"].isna().any()
        or phy_df["physical_qty"].isna().any()
    ):
        raise ValueError(
            "Invalid quantity detected: Non-numeric or missing quantity values found in records."
        )

    if cst_df["unit_cost"].isna().any():
        raise ValueError(
            "Invalid cost detected: Non-numeric or missing unit costs found in catalog."
        )

    if (sys_df["system_qty"] < 0).any() or (phy_df["physical_qty"] < 0).any():
        raise ValueError(
            "Invalid quantity detected: Inventory counts cannot be negative numbers."
        )

    if (cst_df["unit_cost"] < 0).any():
        raise ValueError(
            "Invalid cost detected: Unit cost values cannot be negative."
        )

    # 3. Consolidate Duplicate SKUs per Location
    sys_df = (
        sys_df.groupby(["sku", "location"], as_index=False)["system_qty"]
        .sum()
    )
    phy_df = (
        phy_df.groupby(["sku", "location"], as_index=False)["physical_qty"]
        .sum()
    )
    cst_df = cst_df.drop_duplicates(subset=["sku"], keep="last")

    # 4. Perform Reconciliation Merges
    reconciled = pd.merge(sys_df, phy_df, on=["sku", "location"], how="outer")
    reconciled = pd.merge(reconciled, cst_df, on="sku", how="left")

    # Populate default metadata for missing join entries
    reconciled["system_qty"] = reconciled["system_qty"].fillna(0)
    reconciled["physical_qty"] = reconciled["physical_qty"].fillna(0)
    reconciled["unit_cost"] = reconciled["unit_cost"].fillna(0.0)
    reconciled["item_name"] = reconciled["item_name"].fillna("Unknown SKU")
    reconciled["category"] = reconciled["category"].fillna("Uncategorized")

    # 5. Financial & Variance Computations
    reconciled["unit_variance"] = (
        reconciled["physical_qty"] - reconciled["system_qty"]
    )
    reconciled["system_value"] = (
        reconciled["system_qty"] * reconciled["unit_cost"]
    )
    reconciled["physical_value"] = (
        reconciled["physical_qty"] * reconciled["unit_cost"]
    )
    reconciled["cost_variance"] = (
        reconciled["unit_variance"] * reconciled["unit_cost"]
    )
    reconciled["abs_cost_variance"] = reconciled["cost_variance"].abs()

    # Accuracy percentage per SKU record
    reconciled["item_accuracy_pct"] = np.where(
        reconciled["system_qty"] == 0,
        np.where(reconciled["physical_qty"] == 0, 100.0, 0.0),
        (
            1
            - (
                reconciled["unit_variance"].abs()
                / reconciled[["system_qty", "physical_qty"]].max(axis=1)
            )
        )
        * 100.0,
    )

    # Discrepancy Classification Logic
    conditions = [
        (reconciled["unit_variance"] == 0),
        (reconciled["system_qty"] == 0) & (reconciled["physical_qty"] > 0),
        (reconciled["system_qty"] > 0) & (reconciled["physical_qty"] == 0),
        (reconciled["unit_variance"] > 0),
        (reconciled["unit_variance"] < 0),
    ]
    choices = [
        "Matched",
        "Unrecorded Stock (Surplus)",
        "Missing Stock (Total Loss)",
        "Physical Surplus",
        "Physical Shortage",
    ]
    reconciled["discrepancy_type"] = np.select(
        conditions, choices, default="Unknown"
    )

    # 6. Audit Exception Flagging
    reconciled["requires_audit"] = (
        reconciled["unit_variance"].abs() >= unit_variance_threshold
    ) | (reconciled["abs_cost_variance"] >= cost_variance_threshold)

    # 7. Category Aggregations
    category_summary = (
        reconciled.groupby("category")
        .agg(
            skus_counted=("sku", "nunique"),
            total_system_qty=("system_qty", "sum"),
            total_physical_qty=("physical_qty", "sum"),
            net_unit_variance=("unit_variance", "sum"),
            total_system_val=("system_value", "sum"),
            total_physical_val=("physical_value", "sum"),
            net_cost_variance=("cost_variance", "sum"),
            abs_cost_variance=("abs_cost_variance", "sum"),
            flagged_audit_items=("requires_audit", "sum"),
        )
        .reset_index()
    )

    category_summary["abs_val_accuracy_pct"] = np.where(
        category_summary["total_system_val"] == 0,
        100.0,
        (
            1
            - (
                category_summary["abs_cost_variance"]
                / category_summary["total_system_val"]
            )
        )
        * 100.0,
    )

    # Extract high-priority audit exceptions
    audit_exceptions = (
        reconciled[reconciled["requires_audit"]]
        .sort_values(by="abs_cost_variance", ascending=False)
        .reset_index(drop=True)
    )

    return {
        "item_reconciliation": reconciled,
        "category_summary": category_summary,
        "audit_exceptions": audit_exceptions,
    }


# ==============================================================================
# Verification Execution
# ==============================================================================
if __name__ == "__main__":
    # Duplicate SKU entries at WH-A (SKU-101 appears twice in system & physical counts)
    df_system = pd.DataFrame(
        {
            "sku": ["SKU-101", "SKU-101", "SKU-102", "SKU-103"],
            "location": ["WH-A", "WH-A", "WH-A", "WH-B"],
            "system_qty": [100, 50, 40, 200],  # SKU-101 totals 150
        }
    )

    df_physical = pd.DataFrame(
        {
            "sku": ["SKU-101", "SKU-101", "SKU-102", "SKU-103"],
            "location": ["WH-A", "WH-A", "WH-A", "WH-B"],
            "physical_qty": [90, 55, 30, 200],  # SKU-101 totals 145
        }
    )

    df_master = pd.DataFrame(
        {
            "sku": ["SKU-101", "SKU-102", "SKU-103"],
            "item_name": ["Laptop A", "Monitor B", "Keyboard C"],
            "category": ["Electronics", "Electronics", "Accessories"],
            "unit_cost": [800.0, 200.0, 40.0],
        }
    )

    # 1. Run Reconciliation
    results = reconcile_inventory(
        df_system, df_physical, df_master, unit_variance_threshold=5
    )

    print("=== DEDUPLICATED ITEM RECONCILIATION ===")
    print(
        results["item_reconciliation"][
            [
                "sku",
                "location",
                "system_qty",
                "physical_qty",
                "unit_variance",
                "cost_variance",
                "discrepancy_type",
                "requires_audit",
            ]
        ]
    )

    # 2. Test Invalid Quantity Exception Handling
    print("\n=== TESTING INVALID QUANTITY HANDLING ===")
    df_invalid = df_physical.copy()
    df_invalid.loc[0, "physical_qty"] = -15  # Negative quantity

    try:
        reconcile_inventory(df_system, df_invalid, df_master)
    except ValueError as err:
        print(f"Caught Expected Error: {err}")