"""
Transaction Aggregation Utility (deterministic)
-----------------------------------------------
Rules (deterministic, order-independent):
  1. Every customer in the master appears exactly once in the output,
     even if they have zero transactions.
  2. Any transaction whose customer_id is not in the customer master
     is ignored entirely (not counted, not summed, not surfaced).
  3. Output is sorted by customer_id ascending; ties are impossible
     because customer_id is unique in the master.
  4. Results do not depend on the input order of `transactions`.
"""

from collections import defaultdict


def aggregate_transactions(customers, transactions):
    """
    Aggregate transactions by customer and left-join to the customer master.

    Parameters
    ----------
    customers : list[dict]
        Customer master. Each dict must contain 'customer_id' (unique).
    transactions : list[dict]
        Each dict must contain 'customer_id' and 'amount'. Rows missing
        these keys, or referring to a customer_id not in `customers`,
        are ignored.

    Returns
    -------
    list[dict]
        One dict per customer, sorted by customer_id ascending, with
        'total_amount' (float, rounded to 2 dp) and 'transaction_count' (int).
    """
    # --- 1. Validate & index the customer master --------------------------
    # Deduplicate by customer_id defensively; last write wins but order is
    # preserved by insertion. Guarantees exactly one output row per id.
    master_by_id = {}
    for cust in customers:
        cid = cust.get("customer_id")
        if cid is None:
            continue  # malformed master row, skip
        if cid not in master_by_id:
            master_by_id[cid] = cust
        # If duplicate, keep the first occurrence for determinism.

    # --- 2. Pre-seed aggregates for EVERY known customer ------------------
    # This is what guarantees zero-transaction customers are included.
    totals = {
        cid: {"total_amount": 0.0, "transaction_count": 0}
        for cid in master_by_id
    }

    # --- 3. Aggregate transactions, ignoring unknown customer IDs --------
    for tx in transactions:
        cid = tx.get("customer_id")
        amount = tx.get("amount")

        # Skip malformed rows
        if cid is None or amount is None:
            continue

        # Skip unknown customer IDs (the "unknown transaction IDs" rule)
        if cid not in master_by_id:
            continue

        # Skip non-numeric amounts deterministically
        if not isinstance(amount, (int, float)):
            continue

        totals[cid]["total_amount"] += float(amount)
        totals[cid]["transaction_count"] += 1

    # --- 4. Left-join aggregates back onto the master ---------------------
    results = []
    for cid, cust in master_by_id.items():
        agg = totals[cid]
        results.append({
            **cust,
            "total_amount": round(agg["total_amount"], 2),
            "transaction_count": agg["transaction_count"],
        })

    # --- 5. Deterministic sort by customer_id -----------------------------
    # customer_id must be comparable; fall back to str() for mixed types.
    try:
        results.sort(key=lambda r: r["customer_id"])
    except TypeError:
        results.sort(key=lambda r: str(r["customer_id"]))

    return results


# ---------------------------
# Example / self-test
# ---------------------------
if __name__ == "__main__":
    customers = [
        {"customer_id": 3, "name": "Carol"},   # zero transactions
        {"customer_id": 1, "name": "Alice"},
        {"customer_id": 2, "name": "Bob"},
        {"customer_id": 4, "name": "Dave"},    # zero transactions
    ]

    # Note: transaction order is intentionally shuffled to prove
    # the result is order-independent.
    transactions = [
        {"transaction_id": "T4", "customer_id": 99, "amount": 999.99},  # unknown -> ignored
        {"transaction_id": "T2", "customer_id": 1,  "amount": 50.25},
        {"transaction_id": "T5", "customer_id": 4,  "amount": 75.00},   # actually Dave
        {"transaction_id": "T1", "customer_id": 1,  "amount": 100.50},
        {"transaction_id": "T3", "customer_id": 2,  "amount": 200.00},
        {"transaction_id": "T6", "customer_id": 42, "amount": 10.00},   # unknown -> ignored
        {"transaction_id": "T7", "customer_id": 3,  "amount": 5.00},    # Carol now has 1 tx
    ]

    for row in aggregate_transactions(customers, transactions):
        print(row)