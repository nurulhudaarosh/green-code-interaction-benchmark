import json
from collections import defaultdict
from statistics import mean, pstdev
from typing import List, Dict, Any


def analyze_transactions(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze transactions per account, chronologically.

    Each transaction dict must contain:
        - 'account': account identifier
        - 'amount': numeric amount
        - 'timestamp': sortable chronological key
        - (optionally) other fields preserved in output

    Transactions are grouped by account and processed in chronological order
    (by 'timestamp'). Output preserves that chronological order per account,
    with accounts ordered by their string representation.

    For every transaction, the rolling mean and population standard deviation
    are computed from the five immediately preceding amounts for that account
    (chronologically). If fewer than five preceding amounts exist, mean/pstdev
    are null and the transaction is not flagged.

    A transaction is flagged if:
        amount > mean + 3 * population_stddev
    OR
        population_stddev == 0 and amount > mean  (zero-deviation rule)
    """
    by_account: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    for txn in transactions:
        by_account[txn["account"]].append(txn)

    results: List[Dict[str, Any]] = []

    for account in sorted(by_account.keys(), key=lambda x: str(x)):
        account_txns = sorted(by_account[account], key=lambda t: t["timestamp"])
        history: List[float] = []
        for txn in account_txns:
            amount = txn["amount"]
            entry = dict(txn)
            entry["flagged"] = False
            entry["mean"] = None
            entry["pstdev"] = None
            entry["threshold"] = None

            if len(history) >= 5:
                window = history[-5:]
                m = mean(window)
                sd = pstdev(window)
                threshold = m + 3 * sd
                entry["mean"] = m
                entry["pstdev"] = sd
                entry["threshold"] = threshold

                if sd == 0:
                    # zero-deviation rule: only flag strictly larger amounts
                    if amount > m:
                        entry["flagged"] = True
                else:
                    if amount > threshold:
                        entry["flagged"] = True

            history.append(amount)
            results.append(entry)

    return results


def main():
    transactions = [
        {"account": "A", "amount": 100, "timestamp": "2024-01-01T00:00:00"},
        {"account": "A", "amount": 102, "timestamp": "2024-01-02T00:00:00"},
        {"account": "A", "amount": 98,  "timestamp": "2024-01-03T00:00:00"},
        {"account": "A", "amount": 101, "timestamp": "2024-01-04T00:00:00"},
        {"account": "A", "amount": 99,  "timestamp": "2024-01-05T00:00:00"},
        {"account": "A", "amount": 500, "timestamp": "2024-01-06T00:00:00"},
        {"account": "A", "amount": 100, "timestamp": "2024-01-07T00:00:00"},
        {"account": "B", "amount": 50,  "timestamp": "2024-01-01T00:00:00"},
        {"account": "B", "amount": 50,  "timestamp": "2024-01-02T00:00:00"},
        {"account": "B", "amount": 50,  "timestamp": "2024-01-03T00:00:00"},
        {"account": "B", "amount": 50,  "timestamp": "2024-01-04T00:00:00"},
        {"account": "B", "amount": 50,  "timestamp": "2024-01-05T00:00:00"},
        {"account": "B", "amount": 51,  "timestamp": "2024-01-06T00:00:00"},
        {"account": "B", "amount": 50,  "timestamp": "2024-01-07T00:00:00"},
    ]

    results = analyze_transactions(transactions)
    print(json.dumps(results, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()