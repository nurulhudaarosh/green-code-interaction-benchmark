"""
Customer transaction aggregation utility.

Deterministic rules (same inputs always give the same output):
  1. Output rows come ONLY from the customer master. Nothing in the
     transaction data can create a row.
  2. Customers with no valid transactions are included with
     transaction_count = 0 and total_amount = Decimal("0.00").
  3. A transaction is ignored if its transaction ID is not in the known set.
  4. A transaction is ignored if its customer ID is not in the master.
  5. A transaction ID that appears more than once is counted only once
     (the first occurrence in input order wins).
  6. If the master repeats a customer ID, the first master row wins.
  7. Totals are rounded to 2 decimal places (ROUND_HALF_UP) once, after summing.
  8. Output is sorted by customer ID (ties are impossible after rule 6).
     Mixed ID types are ordered by type name first, so sorting never raises.

Ignored transactions can optionally be collected via the `rejects` argument,
in input order, each with a fixed reason code.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Iterable, Mapping

ZERO_COUNT = 0
ZERO_AMOUNT = Decimal("0.00")
CENT = Decimal("0.01")

REASON_UNKNOWN_TXN = "unknown_transaction_id"
REASON_UNKNOWN_CUSTOMER = "unknown_customer_id"
REASON_DUPLICATE_TXN = "duplicate_transaction_id"


def _sort_key(value: Any) -> tuple:
    return (type(value).__name__, value)


def aggregate_transactions(
    transactions: Iterable[Mapping[str, Any]],
    customer_master: Iterable[Mapping[str, Any]],
    known_transaction_ids: Iterable[Any],
    rejects: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Args:
        transactions: rows with keys 'transaction_id', 'customer_id', 'amount'.
        customer_master: rows with keys 'customer_id', 'name' (extra keys are kept).
        known_transaction_ids: valid transaction IDs; any others are ignored.
        rejects: optional list that receives {'transaction': row, 'reason': code}
            for every ignored transaction, in input order.

    Returns:
        One dict per distinct master customer, sorted by customer_id, with added
        'transaction_count' and 'total_amount' fields.
    """
    known_ids = set(known_transaction_ids)

    # Rule 6: first master row per customer ID wins.
    master: dict[Any, Mapping[str, Any]] = {}
    for cust in customer_master:
        master.setdefault(cust["customer_id"], cust)

    # Rules 1 and 2: every master customer starts at zero; only these keys exist.
    counts: dict[Any, int] = {cid: ZERO_COUNT for cid in master}
    totals: dict[Any, Decimal] = {cid: Decimal("0") for cid in master}

    seen_txn_ids: set[Any] = set()

    def reject(txn: Mapping[str, Any], reason: str) -> None:
        if rejects is not None:
            rejects.append({"transaction": txn, "reason": reason})

    for txn in transactions:
        txn_id = txn["transaction_id"]

        if txn_id not in known_ids:                      # rule 3
            reject(txn, REASON_UNKNOWN_TXN)
            continue
        if txn["customer_id"] not in master:             # rule 4
            reject(txn, REASON_UNKNOWN_CUSTOMER)
            continue
        if txn_id in seen_txn_ids:                       # rule 5
            reject(txn, REASON_DUPLICATE_TXN)
            continue

        seen_txn_ids.add(txn_id)
        cid = txn["customer_id"]
        counts[cid] += 1
        totals[cid] += Decimal(str(txn["amount"]))

    result = [
        {
            **cust,
            "transaction_count": counts[cid],
            "total_amount": totals[cid].quantize(CENT, rounding=ROUND_HALF_UP),  # rule 7
        }
        for cid, cust in master.items()
    ]
    result.sort(key=lambda row: _sort_key(row["customer_id"]))  # rule 8
    return result


if __name__ == "__main__":
    master = [
        {"customer_id": 3, "name": "Carol"},
        {"customer_id": 1, "name": "Alice"},
        {"customer_id": 2, "name": "Bob"},    # no transactions at all
        {"customer_id": 4, "name": "Dave"},   # only an unknown-ID transaction
        {"customer_id": 1, "name": "Alice (duplicate master row)"},  # ignored
    ]
    txns = [
        {"transaction_id": "T1", "customer_id": 1, "amount": "10.50"},
        {"transaction_id": "T2", "customer_id": 1, "amount": "4.50"},
        {"transaction_id": "T2", "customer_id": 1, "amount": "4.50"},     # duplicate txn ID
        {"transaction_id": "T3", "customer_id": 3, "amount": "99.99"},
        {"transaction_id": "TX", "customer_id": 4, "amount": "500.00"},   # unknown txn ID
        {"transaction_id": "TY", "customer_id": 99, "amount": "50.00"},   # unknown txn ID + customer
        {"transaction_id": "T4", "customer_id": 42, "amount": "7.00"},    # unknown customer
    ]
    known = ["T1", "T2", "T3", "T4"]

    rejected: list[dict[str, Any]] = []
    rows = aggregate_transactions(txns, master, known, rejects=rejected)

    for row in rows:
        print(row)
    for r in rejected:
        print("rejected:", r["transaction"]["transaction_id"], "->", r["reason"])

    # Output:
    # {'customer_id': 1, 'name': 'Alice', 'transaction_count': 2, 'total_amount': Decimal('15.00')}
    # {'customer_id': 2, 'name': 'Bob', 'transaction_count': 0, 'total_amount': Decimal('0.00')}
    # {'customer_id': 3, 'name': 'Carol', 'transaction_count': 1, 'total_amount': Decimal('99.99')}
    # {'customer_id': 4, 'name': 'Dave', 'transaction_count': 0, 'total_amount': Decimal('0.00')}
    # rejected: T2 -> duplicate_transaction_id
    # rejected: TX -> unknown_transaction_id
    # rejected: TY -> unknown_transaction_id
    # rejected: T4 -> unknown_customer_id

    assert [r["customer_id"] for r in rows] == [1, 2, 3, 4]
    assert rows[0]["name"] == "Alice" and rows[0]["transaction_count"] == 2
    assert rows[1]["transaction_count"] == 0 and rows[1]["total_amount"] == Decimal("0.00")
    assert rows[3]["transaction_count"] == 0 and rows[3]["total_amount"] == Decimal("0.00")
    assert [r["reason"] for r in rejected] == [
        REASON_DUPLICATE_TXN, REASON_UNKNOWN_TXN, REASON_UNKNOWN_TXN, REASON_UNKNOWN_CUSTOMER,
    ]

    # Determinism check: shuffled master order gives identical output.
    assert aggregate_transactions(txns, list(reversed(master)), known) == rows