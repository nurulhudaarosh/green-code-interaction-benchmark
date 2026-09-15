import csv
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Transaction:
    account_id: str
    transaction_id: str
    timestamp: datetime
    amount: float
    mean_prev: Optional[float] = field(default=None)
    stdev_prev: Optional[float] = field(default=None)
    is_unusually_high: bool = field(default=False)
    reason: str = field(default="")


WINDOW_SIZE = 5


def load_transactions(rows: List[dict]) -> List[Transaction]:
    """
    Parse raw dict rows (e.g. from CSV) into Transaction objects.
    Expected keys: account_id, transaction_id, timestamp, amount
    """
    transactions = []
    for row in rows:
        transactions.append(
            Transaction(
                account_id=str(row["account_id"]),
                transaction_id=str(row["transaction_id"]),
                timestamp=datetime.fromisoformat(row["timestamp"]),
                amount=float(row["amount"]),
            )
        )
    return transactions


def order_transactions(transactions: List[Transaction]) -> List[Transaction]:
    """
    Deterministic ordering: by account_id, then timestamp, then transaction_id
    (transaction_id used as a stable tiebreaker for same-timestamp entries).
    """
    return sorted(
        transactions,
        key=lambda t: (t.account_id, t.timestamp, t.transaction_id),
    )


def compute_window_stats(preceding_amounts: List[float]):
    """
    Given exactly WINDOW_SIZE preceding amounts, return (mean, population_stdev).
    """
    mean = statistics.mean(preceding_amounts)
    stdev = statistics.pstdev(preceding_amounts)  # population standard deviation
    return mean, stdev


def flag_unusually_high(amount: float, mean: float, stdev: float):
    """
    Flag if amount > mean + 3 * population_stdev.

    Zero-deviation rule: when the five preceding amounts are all identical,
    stdev == 0, so mean + 3*stdev == mean. In that case ANY amount strictly
    greater than that constant mean must be flagged -- not just amounts that
    clear some multiple-of-stdev threshold (which is meaningless when
    stdev is 0). An amount equal to the mean is NOT flagged; only a larger
    current amount is.
    """
    if stdev == 0:
        if amount > mean:
            return True, "zero_deviation_exceeded"
        return False, "zero_deviation_not_exceeded"

    threshold = mean + 3 * stdev
    if amount > threshold:
        return True, "exceeds_mean_plus_3sd"
    return False, "within_normal_range"


def analyze_transactions(transactions: List[Transaction]) -> List[Transaction]:
    """
    For each transaction, look at the WINDOW_SIZE immediately preceding
    transactions for the same account (in chronological order) and flag
    unusually high values. Transactions with fewer than WINDOW_SIZE prior
    transactions in their account's history are not flagged (insufficient
    history) but still appear in the output with null stats.
    """
    ordered = order_transactions(transactions)

    history_by_account = {}

    for txn in ordered:
        history = history_by_account.setdefault(txn.account_id, [])

        if len(history) >= WINDOW_SIZE:
            preceding = history[-WINDOW_SIZE:]
            mean, stdev = compute_window_stats(preceding)
            txn.mean_prev = mean
            txn.stdev_prev = stdev
            txn.is_unusually_high, txn.reason = flag_unusually_high(
                txn.amount, mean, stdev
            )
        else:
            txn.mean_prev = None
            txn.stdev_prev = None
            txn.is_unusually_high = False
            txn.reason = "insufficient_history"

        history.append(txn.amount)

    return ordered


def write_output(transactions: List[Transaction], output_path: str) -> None:
    """
    Write deterministic CSV output: rows sorted by (account_id, timestamp,
    transaction_id), with fixed column order and formatted floats.
    """
    fieldnames = [
        "account_id",
        "transaction_id",
        "timestamp",
        "amount",
        "mean_prev",
        "stdev_prev",
        "is_unusually_high",
        "reason",
    ]

    ordered = order_transactions(transactions)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in ordered:
            writer.writerow(
                {
                    "account_id": t.account_id,
                    "transaction_id": t.transaction_id,
                    "timestamp": t.timestamp.isoformat(),
                    "amount": f"{t.amount:.2f}",
                    "mean_prev": f"{t.mean_prev:.6f}" if t.mean_prev is not None else "",
                    "stdev_prev": f"{t.stdev_prev:.6f}" if t.stdev_prev is not None else "",
                    "is_unusually_high": t.is_unusually_high,
                    "reason": t.reason,
                }
            )


def run(input_csv_path: str, output_csv_path: str) -> None:
    with open(input_csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    transactions = load_transactions(rows)
    analyzed = analyze_transactions(transactions)
    write_output(analyzed, output_csv_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python transaction_analyzer.py <input.csv> <output.csv>")
        sys.exit(1)

    run(sys.argv[1], sys.argv[2])