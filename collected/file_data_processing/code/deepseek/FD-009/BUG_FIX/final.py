import csv
import sys
from collections import defaultdict, deque
from statistics import mean, pstdev


def analyze_transactions(input_path, output_path):
    # Preserve deterministic ordering of accounts by first appearance.
    accounts = {}
    order = []

    with open(input_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            account = row["account"]
            if account not in accounts:
                accounts[account] = []
                order.append(account)
            accounts[account].append(row)

    results = []

    for account in order:
        rows = accounts[account]
        recent = deque(maxlen=5)

        for row in rows:
            amount = float(row["amount"])

            if len(recent) < 5:
                status = "insufficient_history"
                avg = ""
                std = ""
                threshold = ""
            else:
                window = list(recent)
                avg = mean(window)
                std = pstdev(window)
                threshold = avg + 3 * std

                if std == 0:
                    # Zero-deviation rule: any value strictly above the
                    # constant window mean is flagged; otherwise normal.
                    status = "flagged" if amount > avg else "normal"
                else:
                    status = "flagged" if amount > threshold else "normal"

            results.append({
                "account": account,
                "transaction_id": row["transaction_id"],
                "amount": amount,
                "mean_prev5": avg,
                "pstdev_prev5": std,
                "threshold": threshold,
                "status": status,
            })

            recent.append(amount)

    fieldnames = [
        "account",
        "transaction_id",
        "amount",
        "mean_prev5",
        "pstdev_prev5",
        "threshold",
        "status",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "account": r["account"],
                "transaction_id": r["transaction_id"],
                "amount": f"{r['amount']:.2f}",
                "mean_prev5": f"{r['mean_prev5']:.6f}" if r["mean_prev5"] != "" else "",
                "pstdev_prev5": f"{r['pstdev_prev5']:.6f}" if r["pstdev_prev5"] != "" else "",
                "threshold": f"{r['threshold']:.6f}" if r["threshold"] != "" else "",
                "status": r["status"],
            })


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyzer.py <input.csv> <output.csv>", file=sys.stderr)
        sys.exit(1)
    analyze_transactions(sys.argv[1], sys.argv[2])