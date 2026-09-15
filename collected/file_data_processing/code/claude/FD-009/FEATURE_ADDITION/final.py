import csv
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Transaction:
    account_id: str
    transaction_id: str
    timestamp: str
    amount: float
    is_flagged: bool = False
    rolling_mean: float = field(default=None)
    rolling_stdev: float = field(default=None)
    window_size: int = field(default=0)


def load_transactions(filepath: str) -> List[Transaction]:
    transactions = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append(
                Transaction(
                    account_id=row["account_id"],
                    transaction_id=row["transaction_id"],
                    timestamp=row["timestamp"],
                    amount=float(row["amount"]),
                )
            )
    return transactions


def group_and_order_by_account(
    transactions: List[Transaction],
) -> Dict[str, List[Transaction]]:
    grouped = defaultdict(list)
    for txn in transactions:
        grouped[txn.account_id].append(txn)

    for account_id in grouped:
        grouped[account_id].sort(key=lambda t: (t.timestamp, t.transaction_id))

    return grouped


def analyze_account(transactions: List[Transaction], window: int = 5) -> None:
    """Compute rolling mean/stdev/flag for EVERY transaction, using up to the
    `window` immediately preceding transactions (fewer for early ones).

    - The first transaction in an account has no preceding history, so no
      baseline can be computed and it is never flagged.
    - Transactions 2..window use whatever preceding transactions exist
      (1 to window-1 of them).
    - Transactions after the first `window` use exactly `window` preceding
      transactions.

    Flagging rule:
        threshold = mean + 3 * population_stdev
        flagged if amount > threshold

    Zero-deviation rule:
        If the preceding window has zero population standard deviation
        (all preceding amounts identical), any amount that differs from
        that constant value is flagged, regardless of magnitude. An amount
        equal to the constant value is not flagged.
    """
    for i, txn in enumerate(transactions):
        if i == 0:
            # No preceding transactions available; no baseline possible.
            txn.window_size = 0
            continue

        start = max(0, i - window)
        preceding = [t.amount for t in transactions[start:i]]

        mean = statistics.mean(preceding)
        stdev = statistics.pstdev(preceding)

        txn.rolling_mean = mean
        txn.rolling_stdev = stdev
        txn.window_size = len(preceding)

        if stdev == 0:
            txn.is_flagged = txn.amount != mean
        else:
            threshold = mean + 3 * stdev
            txn.is_flagged = txn.amount > threshold


def analyze_all_accounts(
    grouped: Dict[str, List[Transaction]], window: int = 5
) -> None:
    for account_id in grouped:
        analyze_account(grouped[account_id], window=window)


def write_output(grouped: Dict[str, List[Transaction]], filepath: str) -> None:
    fieldnames = [
        "account_id",
        "transaction_id",
        "timestamp",
        "amount",
        "rolling_mean",
        "rolling_stdev",
        "window_size",
        "is_flagged",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for account_id in sorted(grouped.keys()):
            for txn in grouped[account_id]:
                writer.writerow(
                    {
                        "account_id": txn.account_id,
                        "transaction_id": txn.transaction_id,
                        "timestamp": txn.timestamp,
                        "amount": f"{txn.amount:.2f}",
                        "rolling_mean": (
                            f"{txn.rolling_mean:.6f}"
                            if txn.rolling_mean is not None
                            else ""
                        ),
                        "rolling_stdev": (
                            f"{txn.rolling_stdev:.6f}"
                            if txn.rolling_stdev is not None
                            else ""
                        ),
                        "window_size": txn.window_size,
                        "is_flagged": txn.is_flagged,
                    }
                )


def run_analysis(input_path: str, output_path: str, window: int = 5) -> None:
    transactions = load_transactions(input_path)
    grouped = group_and_order_by_account(transactions)
    analyze_all_accounts(grouped, window=window)
    write_output(grouped, output_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python transaction_analyzer.py <input.csv> <output.csv>")
        sys.exit(1)

    run_analysis(sys.argv[1], sys.argv[2])