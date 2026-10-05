import pandas as pd


def aggregate_customer_transactions(
    customers_df: pd.DataFrame, transactions_df: pd.DataFrame
) -> pd.DataFrame:
    """Aggregates transactions by customer, joining back to the customer master.

    Ensures customers with zero transactions are included with explicitly zeroed
    counts and amounts.

    Parameters:
        customers_df (pd.DataFrame): Customer master data containing
          'customer_id'.
        transactions_df (pd.DataFrame): Transaction log containing
          'transaction_id', 'customer_id', and 'amount'.

    Returns:
        pd.DataFrame: Merged customer dataset with total_amount and
        transaction_count, sorted by customer_id.
    """
    # 1. Filter out records with unknown/missing transaction IDs
    valid_transactions = transactions_df.dropna(
        subset=["transaction_id"]
    ).copy()

    # 2. Aggregate valid transactions by customer_id
    aggregated_tx = (
        valid_transactions.groupby("customer_id", as_index=False)
        .agg(
            total_amount=("amount", "sum"),
            transaction_count=("transaction_id", "count"),
        )
    )

    # 3. Left join onto customer master to retain customers without transactions
    result_df = pd.merge(
        customers_df, aggregated_tx, on="customer_id", how="left"
    )

    # 4. Explicitly fill zero transaction count and zero total amount for customers with no transactions
    result_df["total_amount"] = result_df["total_amount"].fillna(0.0)
    result_df["transaction_count"] = (
        result_df["transaction_count"].fillna(0).astype(int)
    )

    # 5. Sort by customer_id and reset index
    result_df = result_df.sort_values(by="customer_id").reset_index(drop=True)

    return result_df


# --- Example Run ---
if __name__ == "__main__":
    customers = pd.DataFrame(
        {
            "customer_id": [101, 102, 103, 104],
            "name": ["Alice", "Bob", "Charlie", "Diana"],
        }
    )

    transactions = pd.DataFrame(
        {
            "transaction_id": ["TX101", None, "TX102", "TX103"],
            "customer_id": [101, 101, 102, 101],
            "amount": [50.0, 999.0, 75.5, 25.0],
        }
    )

    df_summary = aggregate_customer_transactions(customers, transactions)
    print(df_summary)