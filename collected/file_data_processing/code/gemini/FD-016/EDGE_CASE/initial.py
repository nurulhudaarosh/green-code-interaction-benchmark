import pandas as pd


def process_customer_transactions(
    customers_df: pd.DataFrame, transactions_df: pd.DataFrame
) -> pd.DataFrame:
    """Aggregates transactions by customer ID, matches with customer master data,

    includes customers with zero transactions, drops invalid transaction IDs,
    and sorts output by customer ID.
    """
    # 1. Drop rows with missing or invalid transaction IDs
    valid_txns = transactions_df.dropna(subset=["transaction_id"])

    # 2. Aggregate transactions by customer ID
    aggregated_txns = (
        valid_txns.groupby("customer_id", as_index=False)
        .agg(
            total_amount=("amount", "sum"), transaction_count=("transaction_id", "count")
        )
    )

    # 3. Join with customer master (Left Join ensures zero-transaction customers are kept)
    result = pd.merge(customers_df, aggregated_txns, on="customer_id", how="left")

    # 4. Fill NaN values for customers with zero transactions
    result["total_amount"] = result["total_amount"].fillna(0.0)
    result["transaction_count"] = result["transaction_count"].fillna(0).astype(int)

    # 5. Sort by customer ID
    result = result.sort_values("customer_id").reset_index(drop=True)

    return result


# --- Example Usage ---
if __name__ == "__main__":
    # Sample Customer Master Data
    customers_data = {
        "customer_id": [101, 102, 103, 104],
        "customer_name": ["Alice", "Bob", "Charlie", "David"],
    }
    customers_df = pd.DataFrame(customers_data)

    # Sample Transaction Data (includes None/NaN for unknown IDs and an unknown customer)
    transactions_data = {
        "transaction_id": ["TX1001", "TX1002", None, "TX1004", "TX1005"],
        "customer_id": [101, 101, 102, 103, 101],
        "amount": [150.00, 50.00, 200.00, 75.50, 25.00],
    }
    transactions_df = pd.DataFrame(transactions_data)

    # Process and display output
    output_df = process_customer_transactions(customers_df, transactions_df)
    print(output_df)