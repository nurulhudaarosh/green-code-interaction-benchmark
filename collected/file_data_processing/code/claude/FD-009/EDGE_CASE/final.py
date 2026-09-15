import csv
import json
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any
from collections import defaultdict

WINDOW_SIZE = 5


@dataclass
class Transaction:
    account_id: str
    transaction_id: str
    timestamp: str
    amount: float
    is_flagged: bool = field(default=False)
    mean_preceding: float = field(default=None)
    stdev_preceding: float = field(default=None)


def load_transactions(rows: List[Dict[str, Any]]) -> List[Transaction]:
    return [
        Transaction(
            account_id=str(r["account_id"]),
            transaction_id=str(r["transaction_id"]),
            timestamp=str(r["timestamp"]),
            amount=float(r["amount"]),
        )
        for r in rows
    ]


def order_transactions(transactions: List[Transaction]) -> Dict[str, List[Transaction]]:
    """Group by account and sort strictly by chronological timestamp,
    with transaction_id as a deterministic tiebreaker for equal timestamps.
    Input order is never trusted."""
    by_account: Dict[str, List[Transaction]] = defaultdict(list)
    for t in transactions:
        by_account[t.account_id].append(t)

    for account_id in by_account:
        by_account[account_id].sort(key=lambda t: (t.timestamp, t.transaction_id))

    return by_account


def analyze_account(txns: List[Transaction]) -> None:
    """Mutates transactions in place. Each transaction is evaluated against
    the 5 chronologically immediately preceding transactions for that account."""
    for i, txn in enumerate(txns):
        if i < WINDOW_SIZE:
            # Not enough chronological history yet — cannot evaluate
            continue

        window = [t.amount for t in txns[i - WINDOW_SIZE:i]]
        mean = statistics.mean(window)
        stdev = statistics.pstdev(window)  # population standard deviation

        txn.mean_preceding = mean
        txn.stdev_preceding = stdev

        if stdev == 0:
            # Zero-deviation boundary: every value in the window was identical.
            # There is no valid "mean + 3*stdev" threshold to compare against
            # (it collapses to the mean itself), so the rule is applied exactly:
            # any amount that deviates at all from that constant is flagged.
            txn.is_flagged = txn.amount != mean
        else:
            threshold = mean + 3 * stdev
            txn.is_flagged = txn.amount > threshold


def analyze_transactions(rows: List[Dict[str, Any]]) -> List[Transaction]:
    transactions = load_transactions(rows)
    grouped = order_transactions(transactions)  # chronological per account

    for account_id in grouped:
        analyze_account(grouped[account_id])

    # Deterministic output ordering: stable account_id order, then
    # chronological (timestamp, transaction_id) order within each account
    result = []
    for account_id in sorted(grouped.keys()):
        result.extend(grouped[account_id])

    return result


def write_csv(transactions: List[Transaction], path: str) -> None:
    fieldnames = [
        "account_id",
        "transaction_id",
        "timestamp",
        "amount",
        "mean_preceding",
        "stdev_preceding",
        "is_flagged",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in transactions:
            writer.writerow({
                "account_id": t.account_id,
                "transaction_id": t.transaction_id,
                "timestamp": t.timestamp,
                "amount": f"{t.amount:.2f}",
                "mean_preceding": f"{t.mean_preceding:.6f}" if t.mean_preceding is not None else "",
                "stdev_preceding": f"{t.stdev_preceding:.6f}" if t.stdev_preceding is not None else "",
                "is_flagged": t.is_flagged,
            })


def write_json(transactions: List[Transaction], path: str) -> None:
    data = [
        {
            "account_id": t.account_id,
            "transaction_id": t.transaction_id,
            "timestamp": t.timestamp,
            "amount": round(t.amount, 2),
            "mean_preceding": round(t.mean_preceding, 6) if t.mean_preceding is not None else None,
            "stdev_preceding": round(t.stdev_preceding, 6) if t.stdev_preceding is not None else None,
            "is_flagged": t.is_flagged,
        }
        for t in transactions
    ]
    with open(path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    # Deliberately unsorted input, including a zero-deviation window
    # (t1–t5 are all 100 exactly) followed by a boundary case (t6 = 100, not flagged)
    # and an anomaly (t7 = 5000, flagged)
    sample_rows = [
        {"account_id": "A1", "transaction_id": "t3", "timestamp": "2024-01-03T00:00:00", "amount": 100},
        {"account_id": "A1", "transaction_id": "t1", "timestamp": "2024-01-01T00:00:00", "amount": 100},
        {"account_id": "A1", "transaction_id": "t7", "timestamp": "2024-01-07T00:00:00", "amount": 5000},
        {"account_id": "A1", "transaction_id": "t5", "timestamp": "2024-01-05T00:00:00", "amount": 100},
        {"account_id": "A1", "transaction_id": "t2", "timestamp": "2024-01-02T00:00:00", "amount": 100},
        {"account_id": "A1", "transaction_id": "t6", "timestamp": "2024-01-06T00:00:00", "amount": 100},
        {"account_id": "A1", "transaction_id": "t4", "timestamp": "2024-01-04T00:00:00", "amount": 100},
    ]

    analyzed = analyze_transactions(sample_rows)
    write_csv(analyzed, "output.csv")
    write_json(analyzed, "output.json")

    for t in analyzed:
        print(t)