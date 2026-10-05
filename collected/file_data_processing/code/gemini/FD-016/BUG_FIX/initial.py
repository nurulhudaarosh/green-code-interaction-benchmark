import pandas as pd


def process_customer_transactions(
    customers_df: pd.DataFrame, transactions_df: pd.DataFrame
) -> pd.DataFrame:
    """Aggregates transactions by customer, ignores unknown transaction IDs,

    joins with customer master (including zero-transaction customers), and sorts
    by customer ID.
    """
    # Filter out transactions with unknown/missing transaction IDs
    valid_tx = transactions_df.dropna(subset=["transaction_id"]).copy()

    # Aggregate transactions by customer ID
    aggregated_tx = (
        valid_tx.groupby("customer_id", as_index=False)
        .agg(
            total_amount=("amount", "sum"),
            transaction_count=("transaction_id", "count"),
        )
    )

    # Outer join with customer master to ensure customers with zero transactions are included
    result = customers_df.merge(aggregated_tx, on="customer_id", how="left")

    # Fill NaN values for customers without transactions
    result["total_amount"] = result["total_amount"].fillna(0.0)
    result["transaction_count"] = result["transaction_count"].fillna(0).astype(int)

    # Sort by customer_id
    result = result.sort_values("customer_id").reset_index(drop=True)

    return result


# Example Usage
if __name__ == "__main__":
    # Sample Customer Master Data
    customers = pd.DataFrame(
        {
            "customer_id": [101, 102, 103, 104],
            "customer_name": ["Alice", "Bob", "Charlie", "Diana"],
        }
    )

    # Sample Transaction Data (includes missing/unknown transaction IDs)
    transactions = pd.DataFrame(
        {
            "transaction_id": ["T1", "T2", None, "T4", "T5"],
            "customer_id": [101, 101, 102, 103, 101],
            "amount": [50.0, 30.0, 100.0, 200.0, 20.0],
        }
    )

    # Process and display summary
    summary_df = process_customer_transactions(customers, transactions)
    print(summary_df)