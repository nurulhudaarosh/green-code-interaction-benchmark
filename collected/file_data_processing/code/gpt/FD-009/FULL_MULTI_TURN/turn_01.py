import csv
import math
import sys


def analyze_transactions(input_file, output_file):
    transactions = []

    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            transactions.append({
                "account": row["account"],
                "timestamp": row["timestamp"],
                "amount": float(row["amount"])
            })

    transactions.sort(
        key=lambda x: (x["account"], x["timestamp"])
    )

    results = []
    account_transactions = {}

    for transaction in transactions:
        account = transaction["account"]

        if account not in account_transactions:
            account_transactions[account] = []

        previous = account_transactions[account][-5:]

        if previous:
            mean = sum(previous) / len(previous)
            variance = sum((x - mean) ** 2 for x in previous) / len(previous)
            stddev = math.sqrt(variance)

            if stddev == 0:
                anomaly = transaction["amount"] > mean
            else:
                anomaly = transaction["amount"] > mean + 3 * stddev
        else:
            mean = ""
            stddev = ""
            anomaly = False

        results.append({
            "account": transaction["account"],
            "timestamp": transaction["timestamp"],
            "amount": transaction["amount"],
            "rolling_mean": mean,
            "rolling_stddev": stddev,
            "anomaly": anomaly
        })

        account_transactions[account].append(transaction["amount"])

    results.sort(
        key=lambda x: (x["account"], x["timestamp"])
    )

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "account",
            "timestamp",
            "amount",
            "rolling_mean",
            "rolling_stddev",
            "anomaly"
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in results:
            writer.writerow(row)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyzer.py input.csv output.csv")
        sys.exit(1)

    analyze_transactions(sys.argv[1], sys.argv[2])