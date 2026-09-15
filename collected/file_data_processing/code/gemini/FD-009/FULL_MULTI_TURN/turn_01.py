from collections import deque
import csv
from decimal import Decimal, ROUND_HALF_UP
import math

# Sample dataset matching typical transaction format
sample_transactions = [
    {"account_id": "ACC1", "tx_id": "T101", "timestamp": "2026-03-01T10:00:00Z", "amount": 100.00},
    {"account_id": "ACC1", "tx_id": "T102", "timestamp": "2026-03-01T10:05:00Z", "amount": 102.00},
    {"account_id": "ACC1", "tx_id": "T103", "timestamp": "2026-03-01T10:10:00Z", "amount": 98.00},
    {"account_id": "ACC1", "tx_id": "T104", "timestamp": "2026-03-01T10:15:00Z", "amount": 101.00},
    {"account_id": "ACC1", "tx_id": "T105", "timestamp": "2026-03-01T10:20:00Z", "amount": 99.00},
    {"account_id": "ACC1", "tx_id": "T106", "timestamp": "2026-03-01T10:25:00Z", "amount": 150.00},  # High outlier
    {"account_id": "ACC2", "tx_id": "T201", "timestamp": "2026-03-01T11:00:00Z", "amount": 50.00},
    {"account_id": "ACC2", "tx_id": "T202", "timestamp": "2026-03-01T11:01:00Z", "amount": 50.00},
    {"account_id": "ACC2", "tx_id": "T203", "timestamp": "2026-03-01T11:02:00Z", "amount": 50.00},
    {"account_id": "ACC2", "tx_id": "T204", "timestamp": "2026-03-01T11:03:00Z", "amount": 50.00},
    {"account_id": "ACC2", "tx_id": "T205", "timestamp": "2026-03-01T11:04:00Z", "amount": 50.00},
    {"account_id": "ACC2", "tx_id": "T206", "timestamp": "2026-03-01T11:05:00Z", "amount": 50.01},  # Flagged under zero-dev rule
]

def format_dec(val):
    if val is None:
        return ""
    return str(Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def analyze_transactions(transactions, window_size=5):
    # Deterministic sorting: by account, timestamp, and tx_id as a tie-breaker
    sorted_txs = sorted(
        transactions,
        key=lambda x: (x["account_id"], x["timestamp"], x["tx_id"])
    )

    history = {}
    analyzed_results = []

    for tx in sorted_txs:
        acc_id = tx["account_id"]
        amt = float(tx["amount"])

        if acc_id not in history:
            history[acc_id] = deque(maxlen=window_size)

        window = list(history[acc_id])

        if len(window) < window_size:
            mean = None
            std_dev = None
            threshold = None
            is_anomaly = False
        else:
            mean = sum(window) / window_size
            variance = sum((x - mean) ** 2 for x in window) / window_size
            std_dev = math.sqrt(variance)

            # Zero-deviation rule: flag if amount exceeds mean when variance is zero
            if std_dev == 0:
                is_anomaly = amt > mean
                threshold = mean
            else:
                threshold = mean + (3 * std_dev)
                is_anomaly = amt > threshold

        analyzed_results.append({
            "account_id": acc_id,
            "tx_id": tx["tx_id"],
            "timestamp": tx["timestamp"],
            "amount": amt,
            "window_mean": mean,
            "window_std_dev": std_dev,
            "threshold": threshold,
            "is_anomaly": is_anomaly
        })

        # Slide window forward after evaluation
        history[acc_id].append(amt)

    return analyzed_results

def write_deterministic_csv(results, output_file="analyzed_transactions.csv"):
    fieldnames = [
        "account_id", "tx_id", "timestamp", "amount", 
        "window_mean", "window_std_dev", "threshold", "is_anomaly"
    ]
    
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in results:
            writer.writerow({
                "account_id": row["account_id"],
                "tx_id": row["tx_id"],
                "timestamp": row["timestamp"],
                "amount": format_dec(row["amount"]),
                "window_mean": format_dec(row["window_mean"]),
                "window_std_dev": format_dec(row["window_std_dev"]),
                "threshold": format_dec(row["threshold"]),
                "is_anomaly": row["is_anomaly"]
            })

if __name__ == "__main__":
    results = analyze_transactions(sample_transactions)
    write_deterministic_csv(results)
    
    # Print formatted output to console
    for r in results:
        print(
            f"{r['account_id']} | {r['tx_id']} | {r['timestamp']} | "
            f"Amt: {format_dec(r['amount']):>6} | Mean: {format_dec(r['window_mean']):>6} | "
            f"StdDev: {format_dec(r['window_std_dev']):>5} | Flag: {r['is_anomaly']}"
        )