from typing import List, Tuple


def min_coins(coins: List[int], amount: int) -> Tuple[int, List[int]]:
    if amount < 0:
        raise ValueError("amount must be non-negative")

    distinct_coins = sorted({c for c in coins if isinstance(c, int) and c > 0})

    if amount == 0:
        return 0, []

    if not distinct_coins:
        return -1, []

    INF = float("inf")
    dp = [INF] * (amount + 1)
    dp[0] = 0
    choice = [0] * (amount + 1)

    for i in range(1, amount + 1):
        for c in distinct_coins:
            if c > i:
                break
            if dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
                choice[i] = c

    if dp[amount] == INF:
        return -1, []

    # Deterministic reconstruction: preserve the actual DP-chosen path,
    # do not reorder/sort the result afterward.
    result_coins = []
    remaining = amount
    while remaining > 0:
        c = choice[remaining]
        result_coins.append(c)
        remaining -= c

    result_coins.reverse()  # present in the order coins were applied (largest remainder first)
    return dp[amount], result_coins


if __name__ == "__main__":
    test_cases = [
        ([1, 2, 5], 11),
        ([2], 3),
        ([1], 0),
        ([186, 419, 83, 408], 6249),
        ([5, 10, 25], 30),
        ([2, 3], 7),
        ([1, 3, 4], 6),
    ]

    for coins, amount in test_cases:
        count, used = min_coins(coins, amount)
        print(f"coins={coins}, amount={amount} -> count={count}, used={used}")