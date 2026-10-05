from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Iterable, Mapping, Any


def aggregate_transactions(
    customers: Iterable[Mapping[str, Any]],
    transactions: Iterable[Mapping[str, Any]],
    known_transaction_ids: Iterable[Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Aggregate transactions per customer and join to the customer master.

    Inputs
    ------
    customers : rows with at least "customer_id" (other fields are carried through).
    transactions : rows with "transaction_id", "customer_id", "amount".
    known_transaction_ids : optional set of valid transaction IDs. Any transaction
        whose ID is not in this set is ignored. If None, every transaction ID is
        treated as known.

    Behavior
    --------
    - Unknown transaction IDs are ignored.
    - Duplicate transaction IDs are counted once (first occurrence wins).
    - Transactions for customers not in the master are dropped (master is the left side).
    - Customers with no transactions are included with count 0 and total 0.
    - Output is sorted by customer_id.
    """
    known = set(known_transaction_ids) if known_transaction_ids is not None else None

    totals: dict[Any, Decimal] = defaultdict(Decimal)
    counts: dict[Any, int] = defaultdict(int)
    seen_ids: set[Any] = set()

    for txn in transactions:
        txn_id = txn.get("transaction_id")
        if txn_id is None or (known is not None and txn_id not in known):
            continue  # unknown transaction ID
        if txn_id in seen_ids:
            continue  # duplicate transaction
        seen_ids.add(txn_id)

        cust_id = txn.get("customer_id")
        amount = Decimal(str(txn.get("amount", 0) or 0))
        totals[cust_id] += amount
        counts[cust_id] += 1

    result = []
    for cust in customers:
        cust_id = cust["customer_id"]
        result.append(
            {
                **cust,
                "transaction_count": counts.get(cust_id, 0),
                "total_amount": totals.get(cust_id, Decimal("0")),
            }
        )

    result.sort(key=lambda row: row["customer_id"])
    return result


if __name__ == "__main__":
    customers = [
        {"customer_id": 3, "name": "Cara"},
        {"customer_id": 1, "name": "Ali"},
        {"customer_id": 2, "name": "Ben"},  # no transactions
    ]
    transactions = [
        {"transaction_id": "T1", "customer_id": 1, "amount": "10.50"},
        {"transaction_id": "T2", "customer_id": 1, "amount": "4.50"},
        {"transaction_id": "T3", "customer_id": 3, "amount": "20.00"},
        {"transaction_id": "T9", "customer_id": 3, "amount": "99.00"},   # unknown ID
        {"transaction_id": "T4", "customer_id": 42, "amount": "5.00"},   # not in master
    ]
    valid_ids = {"T1", "T2", "T3", "T4"}

    for row in aggregate_transactions(customers, transactions, valid_ids):
        print(row)