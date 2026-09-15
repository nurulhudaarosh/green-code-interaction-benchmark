import csv
import io
from collections import defaultdict


def analyze_transactions(transactions):
    """
    transactions: list of dicts with keys 'account', 'amount'
    Returns list of result dicts with fields:
      account, amount, mean, pstdev, threshold, flag
    """
    per_account = defaultdict(list)
    account_order = []
    for txn in transactions:
        acct = txn["account"]
        if acct not in per_account:
            account_order.append(acct)
        per_account[acct].append(txn["amount"])

    results = []

    for acct in account_order:
        amounts = per_account[acct]
        for i, amount in enumerate(amounts):
            window = amounts[max(0, i - 5):i]

            if len(window) == 0:
                results.append({
                    "account": acct,
                    "amount": amount,
                    "mean": None,
                    "pstdev": None,
                    "threshold": None,
                    "flag": False,
                })
                continue

            n = len(window)
            mean = sum(window) / n
            variance = sum((x - mean) ** 2 for x in window) / n
            pstdev = variance ** 0.5

            if pstdev == 0:
                threshold = mean
                flag = False
            else:
                threshold = mean + 3 * pstdev
                flag = amount > threshold

            results.append({
                "account": acct,
                "amount": amount,
                "mean": mean,
                "pstdev": pstdev,
                "threshold": threshold,
                "flag": flag,
            })

    return results


def format_output(results):
    lines = []
    header = f"{'account':<10} {'amount':>10} {'mean':>10} {'pstdev':>10} {'threshold':>10} {'flag':>5}"
    lines.append(header)
    lines.append("-" * len(header))
    for r in results:
        mean_s = f"{r['mean']:.4f}" if r["mean"] is not None else "-"
        pstdev_s = f"{r['pstdev']:.4f}" if r["pstdev"] is not None else "-"
        threshold_s = f"{r['threshold']:.4f}" if r["threshold"] is not None else "-"
        lines.append(
            f"{r['account']:<10} {r['amount']:>10.4f} {mean_s:>10} {pstdev_s:>10} {threshold_s:>10} {str(r['flag']):>5}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    transactions = [
        {"account": "A", "amount": 100.0},
        {"account": "A", "amount": 102.0},
        {"account": "A", "amount": 98.0},
        {"account": "A", "amount": 101.0},
        {"account": "A", "amount": 99.0},
        {"account": "A", "amount": 100.0},
        {"account": "A", "amount": 500.0},
        {"account": "B", "amount": 50.0},
        {"account": "B", "amount": 50.0},
        {"account": "B", "amount": 50.0},
        {"account": "B", "amount": 50.0},
        {"account": "B", "amount": 50.0},
        {"account": "B", "amount": 50.0},
        {"account": "B", "amount": 200.0},
    ]

    results = analyze_transactions(transactions)
    print(format_output(results))