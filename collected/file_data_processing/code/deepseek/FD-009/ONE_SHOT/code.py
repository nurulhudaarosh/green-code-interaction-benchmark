import csv
import sys
from collections import defaultdict, deque


def analyze_transactions(input_path, output_path):
    # Read all transactions
    rows = []
    with open(input_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    # Group transactions by account, preserving input order
    accounts = defaultdict(list)
    for row in rows:
        accounts[row["account"]].append(row)

    results = []
    for account in accounts:
        txns = accounts[account]
        history = deque(maxlen=5)

        for txn in txns:
            amount = float(txn["amount"])
            flagged = False
            mean = None
            std = None
            threshold = None

            if len(history) == 5:
                mean = sum(history) / 5.0
                # Population standard deviation
                variance = sum((x - mean) ** 2 for x in history) / 5.0
                std = variance ** 0.5
                threshold = mean + 3.0 * std

                if std == 0:
                    # Zero-deviation rule: flag only if strictly greater than mean
                    flagged = amount > mean
                else:
                    flagged = amount > threshold

            results.append({
                "account": txn["account"],
                "transaction_id": txn["transaction_id"],
                "amount": f"{amount:.2f}",
                "mean": "" if mean is None else f"{mean:.2f}",
                "std": "" if std is None else f"{std:.2f}",
                "threshold": "" if threshold is None else f"{threshold:.2f}",
                "flagged": "true" if flagged else "false",
            })

            history.append(amount)

    fieldnames = ["account", "transaction_id", "amount", "mean", "std", "threshold", "flagged"]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyzer.py <input.csv> <output.csv>")
        sys.exit(1)
    analyze_transactions(sys.argv[1], sys.argv[2])