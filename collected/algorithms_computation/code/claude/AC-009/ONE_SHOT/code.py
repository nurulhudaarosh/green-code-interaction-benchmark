def min_coin_change(coins, amount):
    """
    Deterministic minimum-coin-change solver.

    Args:
        coins: list of positive int denominations
        amount: non-negative int target

    Returns:
        (count, coin_list): count is min number of coins (-1 if impossible),
        coin_list is the list of coins used (empty if impossible or amount == 0).
    """
    if amount < 0:
        raise ValueError("amount must be non-negative")

    # Deterministic order: sorted unique positive denominations
    denoms = sorted(set(c for c in coins if isinstance(c, int) and c > 0))

    if amount == 0:
        return 0, []

    if not denoms:
        return -1, []

    INF = float('inf')
    dp = [INF] * (amount + 1)
    choice = [0] * (amount + 1)  # coin used to reach amount a
    dp[0] = 0

    for a in range(1, amount + 1):
        best = INF
        best_coin = 0
        for c in denoms:          # fixed sorted order -> deterministic ties
            if c <= a and dp[a - c] + 1 < best:
                best = dp[a - c] + 1
                best_coin = c
        dp[a] = best
        choice[a] = best_coin

    if dp[amount] == INF:
        return -1, []

    # Reconstruct
    result = []
    remaining = amount
    while remaining > 0:
        c = choice[remaining]
        result.append(c)
        remaining -= c

    result.sort()  # deterministic presentation order
    return dp[amount], result


if __name__ == "__main__":
    tests = [
        ([1, 2, 5], 11),
        ([2], 3),
        ([1], 0),
        ([186, 419, 83, 408], 6249),
        ([5, 10, 25], 30),
    ]
    for coins, amt in tests:
        count, combo = min_coin_change(coins, amt)
        print(f"coins={coins}, amount={amt} -> count={count}, combo={combo}")