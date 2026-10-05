"""
Transaction aggregation utility.

Assumptions (adjust if your data differs):
  * customers:    DataFrame with a unique `customer_id` column plus any master attributes.
  * transactions: DataFrame with `transaction_id`, `customer_id`, `amount`.
  * known_transaction_ids: iterable of valid transaction IDs. Transactions whose
    ID is not in this set are ignored.
  * Duplicate transaction IDs are counted once (first occurrence wins).
  * Transactions for customers missing from the master are dropped.
  * Customers with no valid transactions get transaction_count = 0 and
    total_amount = 0.0 (this also holds when NO transaction is valid at all).
"""

from typing import Iterable

import pandas as pd


def aggregate_transactions_by_customer(
    customers: pd.DataFrame,
    transactions: pd.DataFrame,
    known_transaction_ids: Iterable,
    *,
    customer_col: str = "customer_id",
    txn_id_col: str = "transaction_id",
    amount_col: str = "amount",
) -> pd.DataFrame:
    """Return the customer master joined to per-customer transaction totals.

    Output columns: all customer master columns plus
      * transaction_count - number of valid, de-duplicated transactions (int)
      * total_amount      - sum of their amounts (float)
    Every customer in the master appears exactly once; those without valid
    transactions have 0 and 0.0. Rows are sorted by customer ID ascending.
    """
    # Validate inputs
    for df, name, cols in (
        (customers, "customers", [customer_col]),
        (transactions, "transactions", [customer_col, txn_id_col, amount_col]),
    ):
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"{name} is missing required columns: {missing}")

    if customers[customer_col].duplicated().any():
        raise ValueError(f"customers has duplicate values in '{customer_col}'")

    # 1. Ignore unknown transaction IDs; count each transaction ID only once
    valid_txns = transactions[
        transactions[txn_id_col].isin(set(known_transaction_ids))
    ].drop_duplicates(subset=txn_id_col, keep="first")

    # Treat missing / non-numeric amounts as 0 so they never produce NaN totals
    amounts = pd.to_numeric(valid_txns[amount_col], errors="coerce").fillna(0.0)

    # 2. Aggregate by customer (index = customer ID)
    aggregated = (
        amounts.groupby(valid_txns[customer_col])
        .agg(transaction_count="size", total_amount="sum")
    )

    # 3. Align to the customer master: every master customer gets a row, and
    #    customers with no valid transactions are explicitly filled with 0.
    stats = aggregated.reindex(customers[customer_col].to_numpy(), fill_value=0)
    stats.index = customers.index  # re-attach to the master's row index

    result = customers.copy()
    result["transaction_count"] = stats["transaction_count"].astype(int)
    result["total_amount"] = stats["total_amount"].astype(float)

    # 4. Sort by customer ID
    return result.sort_values(customer_col, kind="stable").reset_index(drop=True)


if __name__ == "__main__":
    customers_df = pd.DataFrame(
        {
            "customer_id": [3, 1, 2, 4],
            "name": ["Carol", "Alice", "Bob", "Dave"],
        }
    )

    transactions_df = pd.DataFrame(
        {
            "transaction_id": ["t1", "t2", "t3", "t4", "t5", "t2"],  # t2 duplicated
            "customer_id": [1, 1, 2, 3, 1, 1],
            "amount": [100.0, 50.0, 75.0, 20.0, 999.0, 50.0],
        }
    )

    known_ids = {"t1", "t2", "t3", "t4"}  # t5 is unknown -> ignored

    print(aggregate_transactions_by_customer(customers_df, transactions_df, known_ids))
    # Expected:
    #    customer_id   name  transaction_count  total_amount
    # 0            1  Alice                  2         150.0
    # 1            2    Bob                  1          75.0
    # 2            3  Carol                  1          20.0
    # 3            4   Dave                  0           0.0   <- zero-transaction customer

    # Edge case: no valid transactions at all -> every customer shows 0 / 0.0
    print(aggregate_transactions_by_customer(customers_df, transactions_df, set()))