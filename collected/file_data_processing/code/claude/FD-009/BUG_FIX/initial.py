import csv
import statistics
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class Transaction:
    txn_id: str
    account_id: str
    timestamp: str
    amount: float
    is_flagged: bool = False
    baseline_mean: Optional[float] = None
    baseline_stddev: Optional[float] = None
    baseline_threshold: Optional[float] = None
    baseline_count: int = 0


WINDOW_SIZE = 5


def load_transactions(filepath: str) -> List[Transaction]:
    transactions = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append(
                Transaction(
                    txn_id=row["txn_id"],
                    account_id=row["account_id"],
                    timestamp=row["timestamp"],
                    amount=float(row["amount"]),
                )
            )
    return transactions


def order_by_account(transactions: List[Transaction]) -> Dict[str, List[Transaction]]:
    grouped: Dict[str, List[Transaction]] = {}
    for txn in transactions:
        grouped.setdefault(txn.account_id, []).append(txn)

    for account_id in grouped:
        grouped[account_id].sort(key=lambda t: (t.timestamp, t.txn_id))

    return grouped


def compute_baseline_stats(preceding_amounts: List[float]):
    mean = statistics.mean(preceding_amounts)
    stddev = statistics.pstdev(preceding_amounts)
    return mean, stddev


def is_unusually_high(amount: float, mean: float, stddev: float) -> bool:
    if stddev == 0:
        return amount != mean
    threshold = mean + 3 * stddev
    return amount > threshold


def analyze_account(transactions: List[Transaction]) -> None:
    for i, txn in enumerate(transactions):
        window = transactions[max(0, i - WINDOW_SIZE):i]
        if len(window) < WINDOW_SIZE:
            txn.baseline_count = len(window)
            continue

        amounts = [t.amount for t in window]
        mean, stddev = compute_baseline_stats(amounts)
        threshold = mean + 3 * stddev

        txn.baseline_count = len(window)
        txn.baseline_mean = mean
        txn.baseline_stddev = stddev
        txn.baseline_threshold = threshold
        txn.is_flagged = is_unusually_high(txn.amount, mean, stddev)


def analyze_all(transactions: List[Transaction]) -> List[Transaction]:
    grouped = order_by_account(transactions)

    results: List[Transaction] = []
    for account_id in sorted(grouped.keys()):
        account_txns = grouped[account_id]
        analyze_account(account_txns)
        results.extend(account_txns)

    return results


def write_output(transactions: List[Transaction], filepath: str) -> None:
    fieldnames = [
        "txn_id",
        "account_id",
        "timestamp",
        "amount",
        "baseline_count",
        "baseline_mean",
        "baseline_stddev",
        "baseline_threshold",
        "is_flagged",
    ]

    ordered = sorted(transactions, key=lambda t: (t.account_id, t.timestamp, t.txn_id))

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in ordered:
            writer.writerow(
                {
                    "txn_id": t.txn_id,
                    "account_id": t.account_id,
                    "timestamp": t.timestamp,
                    "amount": f"{t.amount:.2f}",
                    "baseline_count": t.baseline_count,
                    "baseline_mean": f"{t.baseline_mean:.6f}" if t.baseline_mean is not None else "",
                    "baseline_stddev": f"{t.baseline_stddev:.6f}" if t.baseline_stddev is not None else "",
                    "baseline_threshold": f"{t.baseline_threshold:.6f}" if t.baseline_threshold is not None else "",
                    "is_flagged": t.is_flagged,
                }
            )


def main(input_path: str, output_path: str) -> None:
    transactions = load_transactions(input_path)
    analyzed = analyze_all(transactions)
    write_output(analyzed, output_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python transaction_analyzer.py <input.csv> <output.csv>")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])