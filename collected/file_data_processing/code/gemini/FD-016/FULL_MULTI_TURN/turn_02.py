import pandas as pd


def aggregate_customer_transactions(
    customers_df: pd.DataFrame, transactions_df: pd.DataFrame
) -> pd.DataFrame:
    """Aggregates transactions by customer ID, joining to customer master.

    Drops unknown/invalid transaction IDs, excludes transaction rows for
    unknown customer IDs, retains 0-transaction master customers, and sorts by
    customer_id.
    """
    # 1. Drop rows with null/empty transaction IDs
    valid_txns = transactions_df.dropna(subset=["transaction_id"]).copy()

    # 2. Filter out transactions with customer IDs not present in customer master
    valid_txns = valid_txns[
        valid_txns["customer_id"].isin(customers_df["customer_id"])
    ]

    # 3. Aggregate valid transactions by customer_id
    aggregated_txns = (
        valid_txns.groupby("customer_id", as_index=False)
        .agg(
            total_spend=("amount", "sum"),
            transaction_count=("transaction_id", "count"),
        )
    )

    # 4. Left join to retain all customer master records (including 0-transaction customers)
    result_df = pd.merge(
        customers_df, aggregated_txns, on="customer_id", how="left"
    )

    # 5. Fill missing values for customers with zero transactions
    result_df["total_spend"] = result_df["total_spend"].fillna(0.0)
    result_df["transaction_count"] = (
        result_df["transaction_count"].fillna(0).astype(int)
    )

    # 6. Sort by customer_id ascending
    result_df = result_df.sort_values(
        by="customer_id", ascending=True
    ).reset_index(drop=True)

    return result_df


# Example Usage
if __name__ == "__main__":
    customers_data = pd.DataFrame(
        {
            "customer_id": [101, 102, 103, 104],
            "customer_name": ["Alice", "Bob", "Charlie", "Diana"],
        }
    )

    transactions_data = pd.DataFrame(
        {
            "transaction_id": ["TXN001", "TXN002", "TXN003", None, "TXN005"],
            "customer_id": [101, 101, 999, 102, 103],  # 999 is unknown customer
            "amount": [150.00, 50.00, 500.00, 200.00, 75.50],
        }
    )

    report = aggregate_customer_transactions(customers_data, transactions_data)
    print(report)