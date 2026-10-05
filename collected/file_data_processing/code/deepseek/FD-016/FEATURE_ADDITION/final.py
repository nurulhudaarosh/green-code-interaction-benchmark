"""
Transaction Aggregation Utility
------------------------------
Aggregates transactions by customer, ignores unknown transaction IDs,
joins results to the customer master (including zero-transaction customers
with transaction_count=0 and total_amount=0.0), and sorts by customer ID.
"""

from collections import defaultdict


def aggregate_transactions(customers, transactions):
    """
    Parameters
    ----------
    customers : list of dict
        Each dict must have a 'customer_id' key.
        Example: [{'customer_id': 1, 'name': 'Alice'}, ...]
    transactions : list of dict
        Each dict must have 'transaction_id', 'customer_id', and 'amount'.
        Transactions whose 'customer_id' is not in the customer master
        are considered "unknown" and ignored.

    Returns
    -------
    list of dict
        One record per customer, sorted by customer_id, with keys:
        customer_id, name (if present), transaction_count, total_amount.
        Customers with no transactions will have transaction_count=0
        and total_amount=0.0.
    """
    # Build a set of known customer IDs for O(1) lookup
    known_customer_ids = {c["customer_id"] for c in customers}

    # Aggregate transactions by customer, ignoring unknown transaction IDs
    totals = defaultdict(lambda: {"transaction_count": 0, "total_amount": 0.0})
    for txn in transactions:
        cid = txn.get("customer_id")
        if cid not in known_customer_ids:
            continue  # ignore unknown transaction IDs
        totals[cid]["transaction_count"] += 1
        totals[cid]["total_amount"] += txn.get("amount", 0.0)

    # Join aggregated results back to the customer master.
    # Iterate over the master so zero-transaction customers are always included.
    results = []
    for cust in customers:
        cid = cust["customer_id"]
        agg = totals.get(cid, {"transaction_count": 0, "total_amount": 0.0})
        record = dict(cust)  # preserve all master fields
        record["transaction_count"] = agg["transaction_count"]
        record["total_amount"] = round(agg["total_amount"], 2)
        results.append(record)

    # Sort by customer ID
    results.sort(key=lambda r: r["customer_id"])
    return results


# ---------------- Example usage ----------------
if __name__ == "__main__":
    customers = [
        {"customer_id": 3, "name": "Carol"},
        {"customer_id": 1, "name": "Alice"},
        {"customer_id": 2, "name": "Bob"},
        {"customer_id": 4, "name": "Dave"},  # zero transactions
        {"customer_id": 5, "name": "Eve"},   # zero transactions
    ]

    transactions = [
        {"transaction_id": "T1", "customer_id": 1, "amount": 100.50},
        {"transaction_id": "T2", "customer_id": 1, "amount": 50.00},
        {"transaction_id": "T3", "customer_id": 3, "amount": 200.00},
        {"transaction_id": "T4", "customer_id": 2, "amount": 75.25},
        {"transaction_id": "T5", "customer_id": 999, "amount": 999.99},  # unknown
        {"transaction_id": "T6", "customer_id": 888, "amount": 1.00},    # unknown
    ]

    report = aggregate_transactions(customers, transactions)
    for row in report:
        print(row)