import pandas as pd


def aggregate_customer_transactions(
    customers_df: pd.DataFrame, transactions_df: pd.DataFrame
) -> pd.DataFrame:
    """Aggregates transactions by customer ID, joins with customer master data,

    includes customers with zero transactions, and drops invalid transactions.

    Parameters:
    ----------
    customers_df : pd.DataFrame
        Master customer data containing 'customer_id' and customer attributes.
    transactions_df : pd.DataFrame
        Transaction records containing 'transaction_id', 'customer_id', and
        'amount'.

    Returns:
    -------
    pd.DataFrame
        Aggregated report sorted by 'customer_id'.
    """
    # 1. Ignore/drop records with missing or unknown transaction IDs
    valid_txns = transactions_df.dropna(subset=["transaction_id"])

    # 2. Aggregate transactions by customer_id
    aggregated_txns = (
        valid_txns.groupby("customer_id", as_index=False)
        .agg(
            total_spend=("amount", "sum"),
            transaction_count=("transaction_id", "count"),
        )
    )

    # 3. Left join customer master to keep all customers (including 0-transaction customers)
    result_df = pd.merge(
        customers_df, aggregated_txns, on="customer_id", how="left"
    )

    # 4. Fill NaN values for customers with zero transactions
    result_df["total_spend"] = result_df["total_spend"].fillna(0.0)
    result_df["transaction_count"] = (
        result_df["transaction_count"].fillna(0).astype(int)
    )

    # 5. Sort ascending by customer_id
    result_df = result_df.sort_values(
        by="customer_id", ascending=True
    ).reset_index(drop=True)

    return result_df


# Example Usage
if __name__ == "__main__":
    # Sample Customer Master Data
    customers_data = pd.DataFrame(
        {
            "customer_id": [101, 102, 103, 104],
            "customer_name": ["Alice", "Bob", "Charlie", "Diana"],
        }
    )

    # Sample Transaction Data (contains valid, NaN transaction_id, and multi-transactions)
    transactions_data = pd.DataFrame(
        {
            "transaction_id": ["TXN001", "TXN002", None, "TXN004"],
            "customer_id": [101, 101, 102, 103],
            "amount": [150.00, 50.00, 200.00, 75.50],
        }
    )

    report = aggregate_customer_transactions(customers_data, transactions_data)
    print(report)