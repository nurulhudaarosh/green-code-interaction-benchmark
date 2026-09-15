import math
from collections import defaultdict
from typing import Dict, List, Tuple

def analyze_and_print_transactions(transactions: List[Tuple[str, float, str]]) -> None:
    """
    Orders transactions per account, calculates rolling statistics from the 5 preceding 
    amounts, applies zero-deviation/3-sigma rules, and outputs formatted results.
    """
    grouped_txs = defaultdict(list)
    for idx, (account_id, amount, timestamp) in enumerate(transactions):
        grouped_txs[account_id].append((timestamp, idx, amount))

    results = []
    for account_id in sorted(grouped_txs.keys()):
        acc_txs = sorted(grouped_txs[account_id], key=lambda x: (x[0], x[1]))
        
        history = []
        for timestamp, original_idx, amount in acc_txs:
            if not history:
                rolling_mean = 0.0
                pop_std_dev = 0.0
                flagged = False
            else:
                n = len(history)
                rolling_mean = sum(history) / n
                variance = sum((x - rolling_mean) ** 2 for x in history) / n
                pop_std_dev = math.sqrt(variance)
                
                # Anomaly check: Zero-deviation rule vs 3-Sigma rule
                if pop_std_dev == 0.0:
                    flagged = amount > rolling_mean
                else:
                    flagged = amount > (rolling_mean + 3 * pop_std_dev)
            
            results.append({
                "account_id": account_id,
                "timestamp": timestamp,
                "amount": amount,
                "rolling_mean": rolling_mean,
                "pop_std_dev": pop_std_dev,
                "flagged": flagged,
                "original_idx": original_idx
            })
            
            # Maintain sliding window of max 5 preceding values
            history.append(amount)
            if len(history) > 5:
                history.pop(0)

    # Sort deterministically
    results.sort(key=lambda x: (x["account_id"], x["timestamp"], x["original_idx"]))

    # Output details for every transaction
    print(f"{'Account':<8} {'Timestamp':<20} {'Amount':<10} {'Rolling Mean':<14} {'Pop StdDev':<12} {'Anomaly Flag'}")
    print("=" * 75)
    for r in results:
        print(
            f"{r['account_id']:<8} "
            f"{r['timestamp']:<20} "
            f"{r['amount']:<10.2f} "
            f"{r['rolling_mean']:<14.2f} "
            f"{r['pop_std_dev']:<12.2f} "
            f"{str(r['flagged']):<12}"
        )

if __name__ == "__main__":
    sample_data = [
        ("ACC1", 100.0, "2026-01-01T10:00:00"),
        ("ACC1", 100.0, "2026-01-01T10:05:00"),
        ("ACC1", 100.0, "2026-01-01T10:10:00"),
        ("ACC1", 105.0, "2026-01-01T10:15:00"),
        ("ACC1", 500.0, "2026-01-01T10:20:00"),
        ("ACC2", 50.0, "2026-01-01T09:00:00"),
        ("ACC2", 50.0, "2026-01-01T09:10:00"),
        ("ACC2", 200.0, "2026-01-01T09:20:00")
    ]
    
    analyze_and_print_transactions(sample_data)