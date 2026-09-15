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
    mean_prev: float = field(default=0.0)
    stdev_prev: float = field(default=0.0)
    is_unusually_high: bool = field(default=False)
    reason: str = field(default="")


WINDOW_SIZE = 5


def load_transactions(rows: List[dict]) -> List[Transaction]:
    """
    Parse raw dict rows (e.g. from CSV) into Transaction objects.
    Input order is NOT assumed to be chronological or grouped by account --
    order_transactions() below is what establishes chronological order.
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
    Deterministic chronological ordering: by account_id, then timestamp,
    then transaction_id (stable tiebreaker for equal timestamps). This is
    the single source of truth for "chronological order per account" --
    analyze_transactions() must never process a list that hasn't gone
    through this function first, since input may arrive unsorted.
    """
    return sorted(
        transactions,
        key=lambda t: (t.account_id, t.timestamp, t.transaction_id),
    )


def compute_window_stats(preceding_amounts: List[float]):
    """
    Given the available preceding amounts (chronologically prior to the
    current transaction), return (mean, population_stdev).
    """
    mean = statistics.mean(preceding_amounts)
    stdev = statistics.pstdev(preceding_amounts)  # population standard deviation
    return mean, stdev


def flag_unusually_high(amount: float, mean: float, stdev: float):
    """
    Flag if amount > mean + 3 * population_stdev.

    Zero-deviation boundary (exact rule):
    When the preceding window has stdev == 0 (all preceding amounts
    identical), mean + 3*stdev collapses to exactly `mean`. The boundary
    is handled with a strict inequality on `amount > mean`:
      - amount == mean  -> NOT flagged (equal to the constant history)
      - amount >  mean  -> flagged ("zero_deviation_exceeded")
      - amount <  mean  -> NOT flagged
    This is the same strict-greater-than semantics as the general case,
    just evaluated against `mean` directly instead of `mean + 3*stdev`,
    since multiplying zero by 3 carries no information.
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
    Establishes chronological order per account (regardless of input order),
    then for each transaction computes the rolling mean, population standard
    deviation, and anomaly flag from the amounts immediately preceding it
    in that chronological sequence.

    - Full window: once WINDOW_SIZE prior transactions exist for the
      account, use exactly the most recent WINDOW_SIZE of them.
    - Partial window: fewer than WINDOW_SIZE but at least 1 prior
      transaction -- use whatever is available so every row still gets
      stats and a flag.
    - No history: the account's first transaction has nothing to compare
      against. mean_prev is set to its own amount and stdev_prev to 0,
      which correctly yields "not flagged" under the zero-deviation rule
      (amount == mean_prev, not strictly greater).
    """
    ordered = order_transactions(transactions)  # chronological, per account

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
        elif len(history) >= 1:
            preceding = history[:]  # partial window: all prior amounts so far
            mean, stdev = compute_window_stats(preceding)
            txn.mean_prev = mean
            txn.stdev_prev = stdev
            is_high, reason = flag_unusually_high(txn.amount, mean, stdev)
            txn.is_unusually_high = is_high
            txn.reason = f"partial_window_{len(preceding)}_{reason}"
        else:
            txn.mean_prev = txn.amount
            txn.stdev_prev = 0.0
            txn.is_unusually_high = False
            txn.reason = "no_prior_history"

        history.append(txn.amount)  # only added AFTER computing stats

    return ordered


def write_output(transactions: List[Transaction], output_path: str) -> None:
    """
    Write deterministic CSV output: rows sorted by (account_id, timestamp,
    transaction_id), with fixed column order and formatted floats.
    Every transaction has a mean_prev, stdev_prev, and anomaly flag.
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
                    "mean_prev": f"{t.mean_prev:.6f}",
                    "stdev_prev": f"{t.stdev_prev:.6f}",
                    "is_unusually_high": t.is_unusually_high,
                    "reason": t.reason,
                }
            )


def run(input_csv_path: str, output_csv_path: str) -> None:
    with open(input_csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)  # may be unsorted / arbitrary order

    transactions = load_transactions(rows)
    analyzed = analyze_transactions(transactions)  # sorts chronologically internally
    write_output(analyzed, output_csv_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python transaction_analyzer.py <input.csv> <output.csv>")
        sys.exit(1)

    run(sys.argv[1], sys.argv[2])