import csv
import math
import sys
from collections import defaultdict
from datetime import datetime


def parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main():
    if len(sys.argv) != 3:
        print("Usage: python analyzer.py input.csv output.csv")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    accounts = defaultdict(list)

    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            account = row["account"]
            timestamp = parse_timestamp(row["timestamp"])
            amount = float(row["amount"])
            accounts[account].append((timestamp, amount))

    results = []

    for account in sorted(accounts):
        transactions = sorted(accounts[account], key=lambda x: (x[0], x[1]))

        for i, (timestamp, amount) in enumerate(transactions):
            previous = transactions[max(0, i - 5):i]
            previous_amounts = [item[1] for item in previous]

            if previous_amounts:
                mean = sum(previous_amounts) / len(previous_amounts)
                variance = sum((x - mean) ** 2 for x in previous_amounts) / len(previous_amounts)
                stddev = math.sqrt(variance)

                if stddev == 0:
                    anomaly = amount > mean
                else:
                    anomaly = amount > mean + 3 * stddev
            else:
                mean = None
                stddev = None
                anomaly = False

            results.append({
                "account": account,
                "timestamp": timestamp.isoformat(),
                "amount": amount,
                "rolling_mean": mean,
                "population_stddev": stddev,
                "anomaly": anomaly
            })

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "account",
            "timestamp",
            "amount",
            "rolling_mean",
            "population_stddev",
            "anomaly"
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in results:
            writer.writerow(row)


if __name__ == "__main__":
    main()