import pandas as pd


def process_customer_transactions(
    customers_df: pd.DataFrame, transactions_df: pd.DataFrame
) -> pd.DataFrame:
    """Aggregates transactions by customer ID deterministically.

    Handles:
    - Transactions with null/missing transaction IDs (ignored).
    - Transactions referring to customer IDs not in the customer master (ignored).
    - Customers with no valid transactions (included with 0 count/amount).
    - Output strictly sorted by customer_id.
    """
    # 1. Drop transactions missing a valid transaction ID
    valid_txns = transactions_df.dropna(subset=["transaction_id"])

    # 2. Filter transactions to only keep those referring to known customer IDs
    known_customer_ids = set(customers_df["customer_id"].dropna().unique())
    valid_txns = valid_txns[valid_txns["customer_id"].isin(known_customer_ids)]

    # 3. Aggregate transactions by customer ID
    aggregated_txns = (
        valid_txns.groupby("customer_id", as_index=False)
        .agg(
            total_amount=("amount", "sum"), transaction_count=("transaction_id", "count")
        )
    )

    # 4. Left join on customer master to preserve all known customers (including 0-transaction ones)
    result = pd.merge(customers_df, aggregated_txns, on="customer_id", how="left")

    # 5. Fill NaNs deterministically for customers without transactions
    result["total_amount"] = result["total_amount"].fillna(0.0)
    result["transaction_count"] = result["transaction_count"].fillna(0).astype(int)

    # 6. Sort deterministically by customer ID
    result = result.sort_values("customer_id").reset_index(drop=True)

    return result


# --- Example Usage ---
if __name__ == "__main__":
    customers_df = pd.DataFrame({
        "customer_id": [101, 102, 103, 104],
        "customer_name": ["Alice", "Bob", "Charlie", "David"],
    })

    transactions_df = pd.DataFrame({
        "transaction_id": ["TX1", "TX2", None, "TX4", "TX5", "TX6"],
        "customer_id": [
            101,
            101,
            102,
            999,
            103,
            101,
        ],  # 999 = unknown customer ID, None = missing txn ID
        "amount": [150.00, 50.00, 200.00, 500.00, 75.50, 25.00],
    })

    output_df = process_customer_transactions(customers_df, transactions_df)
    print(output_df)