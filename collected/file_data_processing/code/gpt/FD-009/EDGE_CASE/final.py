import csv
import math
import sys


def analyze_transactions(input_file, output_file):
    transactions = {}

    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            account = row["account"]
            timestamp = row["timestamp"]
            amount = float(row["amount"])

            if account not in transactions:
                transactions[account] = []

            transactions[account].append((timestamp, amount))

    results = []

    for account in sorted(transactions):
        records = sorted(transactions[account], key=lambda x: (x[0], x[1]))

        for i, (timestamp, amount) in enumerate(records):
            previous = [records[j][1] for j in range(max(0, i - 5), i)]

            if previous:
                mean = sum(previous) / len(previous)
                variance = sum((x - mean) ** 2 for x in previous) / len(previous)
                stddev = math.sqrt(variance)

                if stddev == 0:
                    anomaly = amount > mean
                else:
                    anomaly = amount > mean + 3 * stddev
            else:
                mean = 0.0
                stddev = 0.0
                anomaly = False

            results.append([
                account,
                timestamp,
                amount,
                mean,
                stddev,
                anomaly
            ])

    results.sort(key=lambda x: (x[0], x[1], x[2]))

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "account",
            "timestamp",
            "amount",
            "rolling_mean",
            "rolling_stddev",
            "anomaly"
        ])

        for account, timestamp, amount, mean, stddev, anomaly in results:
            writer.writerow([
                account,
                timestamp,
                f"{amount:.6f}",
                f"{mean:.6f}",
                f"{stddev:.6f}",
                str(anomaly).lower()
            ])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyzer.py input.csv output.csv")
        sys.exit(1)

    analyze_transactions(sys.argv[1], sys.argv[2])