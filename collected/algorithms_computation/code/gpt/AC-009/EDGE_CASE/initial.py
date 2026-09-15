from typing import List, Dict


def minimum_coin_construction(
    denominations: List[int],
    target: int
) -> Dict[str, object]:
    """
    Find a minimum-number coin combination for the target amount.

    Coins may be reused unlimited times.

    Returns:
        {
            "count": minimum number of coins, or -1 if impossible,
            "coins": deterministic list of selected coin values
        }

    Deterministic tie-breaking:
        When multiple coins give the same minimum count for an amount,
        the smaller denomination is preferred.
    """

    # Validate input.
    if target < 0:
        raise ValueError("target must be non-negative")

    if any(coin <= 0 for coin in denominations):
        raise ValueError("all coin denominations must be positive")

    # Remove duplicate denominations and sort them so that
    # iteration and tie-breaking are deterministic.
    coins = sorted(set(denominations))

    # No coins available.
    if not coins:
        if target == 0:
            return {"count": 0, "coins": []}
        return {"count": -1, "coins": []}

    # dp[amount] = minimum number of coins needed.
    # target + 1 acts as infinity because no valid solution
    # can require more than target coins when denominations are
    # positive integers.
    INF = target + 1
    dp = [INF] * (target + 1)

    # choice[amount] = coin selected to construct this amount.
    choice = [-1] * (target + 1)

    dp[0] = 0

    # One-dimensional unbounded coin-change DP.
    for amount in range(1, target + 1):
        for coin in coins:
            if coin > amount:
                break

            previous = dp[amount - coin]

            if previous == INF:
                continue

            candidate = previous + 1

            # Strictly better solution.
            if candidate < dp[amount]:
                dp[amount] = candidate
                choice[amount] = coin

            # Equal solution: prefer the smaller denomination.
            elif candidate == dp[amount]:
                if choice[amount] == -1 or coin < choice[amount]:
                    choice[amount] = coin

    # Target cannot be constructed.
    if dp[target] == INF:
        return {
            "count": -1,
            "coins": []
        }

    # Deterministic reconstruction.
    result = []
    amount = target

    while amount > 0:
        coin = choice[amount]

        # Defensive check; should never happen for a reachable target.
        if coin == -1:
            return {
                "count": -1,
                "coins": []
            }

        result.append(coin)
        amount -= coin

    return {
        "count": dp[target],
        "coins": result
    }


# Example usage
if __name__ == "__main__":
    print(minimum_coin_construction([1, 3, 4], 6))
    # {'count': 2, 'coins': [3, 3]}

    print(minimum_coin_construction([2, 4], 7))
    # {'count': -1, 'coins': []}

    print(minimum_coin_construction([1, 2, 5], 11))
    # {'count': 3, 'coins': [5, 5, 1]}