"""
Customer transaction aggregation utility.

Rules:
  1. Output rows come ONLY from the customer master, so nothing in the
     transaction data (unknown transaction IDs, unknown customers) can
     create a row.
  2. Transactions with an unknown transaction ID are ignored entirely.
  3. Transactions for customers not in the master are ignored as well.
  4. Every master customer appears in the output. Customers with no valid
     transactions get an explicit transaction_count of 0 and total_amount
     of Decimal("0.00").
  5. Results are sorted by customer ID.
"""

from decimal import Decimal
from typing import Any, Iterable, Mapping

ZERO_COUNT = 0
ZERO_AMOUNT = Decimal("0.00")


def aggregate_transactions(
    transactions: Iterable[Mapping[str, Any]],
    customer_master: Iterable[Mapping[str, Any]],
    known_transaction_ids: Iterable[Any],
) -> list[dict[str, Any]]:
    """
    Args:
        transactions: rows with keys 'transaction_id', 'customer_id', 'amount'.
        customer_master: rows with keys 'customer_id', 'name' (extra keys are kept).
        known_transaction_ids: valid transaction IDs; any others are ignored.

    Returns:
        One dict per master customer, sorted by customer_id, with added
        'transaction_count' and 'total_amount' fields (0 and 0.00 when the
        customer has no valid transactions).
    """
    known_ids = set(known_transaction_ids)
    master = list(customer_master)

    # Seed every master customer with zeros. Only master customers can ever
    # hold an entry, so transaction data cannot create rows.
    stats: dict[Any, list] = {
        cust["customer_id"]: [ZERO_COUNT, ZERO_AMOUNT] for cust in master
    }

    for txn in transactions:
        if txn["transaction_id"] not in known_ids:
            continue  # unknown transaction ID: ignored
        entry = stats.get(txn["customer_id"])
        if entry is None:
            continue  # customer not in master: ignored
        entry[0] += 1
        entry[1] += Decimal(str(txn["amount"]))

    result = [
        {
            **cust,
            "transaction_count": stats[cust["customer_id"]][0],
            "total_amount": stats[cust["customer_id"]][1],
        }
        for cust in master
    ]
    result.sort(key=lambda row: row["customer_id"])
    return result


if __name__ == "__main__":
    master = [
        {"customer_id": 3, "name": "Carol"},
        {"customer_id": 1, "name": "Alice"},
        {"customer_id": 2, "name": "Bob"},    # no transactions -> zeros
        {"customer_id": 4, "name": "Dave"},   # only an unknown-ID transaction -> zeros
    ]
    txns = [
        {"transaction_id": "T1", "customer_id": 1, "amount": "10.50"},
        {"transaction_id": "T2", "customer_id": 1, "amount": "4.50"},
        {"transaction_id": "T3", "customer_id": 3, "amount": "99.99"},
        {"transaction_id": "TX", "customer_id": 4, "amount": "500.00"},   # unknown txn ID -> ignored
        {"transaction_id": "TY", "customer_id": 99, "amount": "50.00"},   # unknown txn ID, unknown customer -> no row
        {"transaction_id": "T4", "customer_id": 42, "amount": "7.00"},    # customer not in master -> no row
    ]
    known = ["T1", "T2", "T3", "T4"]

    rows = aggregate_transactions(txns, master, known)
    for row in rows:
        print(row)

    # Output:
    # {'customer_id': 1, 'name': 'Alice', 'transaction_count': 2, 'total_amount': Decimal('15.00')}
    # {'customer_id': 2, 'name': 'Bob', 'transaction_count': 0, 'total_amount': Decimal('0.00')}
    # {'customer_id': 3, 'name': 'Carol', 'transaction_count': 1, 'total_amount': Decimal('99.99')}
    # {'customer_id': 4, 'name': 'Dave', 'transaction_count': 0, 'total_amount': Decimal('0.00')}

    assert [r["customer_id"] for r in rows] == [1, 2, 3, 4]
    assert rows[1]["transaction_count"] == 0 and rows[1]["total_amount"] == Decimal("0.00")
    assert rows[3]["transaction_count"] == 0 and rows[3]["total_amount"] == Decimal("0.00")