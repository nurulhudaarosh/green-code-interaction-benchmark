import json
from collections import defaultdict
from statistics import mean, pstdev
from typing import List, Dict, Any


def analyze_transactions(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze transactions per account.

    Each transaction dict must contain:
        - 'account': account identifier
        - 'amount': numeric amount
        - (optionally) other fields preserved in output

    Ordering: transactions are processed per account in the order given.

    For every transaction, the rolling mean and population standard deviation
    are computed from the five immediately preceding amounts for that account.
    If fewer than five preceding amounts exist, mean/pstdev are null and the
    transaction is not flagged.

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
        history: List[float] = []
        for txn in by_account[account]:
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
        {"account": "A", "amount": 100},
        {"account": "A", "amount": 102},
        {"account": "A", "amount": 98},
        {"account": "A", "amount": 101},
        {"account": "A", "amount": 99},
        {"account": "A", "amount": 500},
        {"account": "A", "amount": 100},
        {"account": "B", "amount": 50},
        {"account": "B", "amount": 50},
        {"account": "B", "amount": 50},
        {"account": "B", "amount": 50},
        {"account": "B", "amount": 50},
        {"account": "B", "amount": 51},
        {"account": "B", "amount": 50},
    ]

    results = analyze_transactions(transactions)
    print(json.dumps(results, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()