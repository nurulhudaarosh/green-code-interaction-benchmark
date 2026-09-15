def min_coin_combination(coins, target):
    """
    Returns (min_coins, combination) where:
    - min_coins is the minimum number of coins needed, or -1 if impossible.
    - combination is a list of coin values achieving that minimum, or [] if impossible.
    """
    if target < 0:
        return -1, []
    if target == 0:
        return 0, []

    # Filter out coins larger than target (they can't be used)
    useful_coins = [c for c in coins if c <= target]
    if not useful_coins:
        return -1, []

    INF = float('inf')
    dp = [INF] * (target + 1)
    dp[0] = 0

    # Unbounded knapsack: iterate coins then amounts forward
    for coin in useful_coins:
        for amt in range(coin, target + 1):
            if dp[amt - coin] + 1 < dp[amt]:
                dp[amt] = dp[amt - coin] + 1

    if dp[target] == INF:
        return -1, []

    # Deterministic reconstruction
    combination = []
    remaining = target
    while remaining > 0:
        for coin in useful_coins:  # Iterate in given order for determinism
            if remaining >= coin and dp[remaining] == dp[remaining - coin] + 1:
                combination.append(coin)
                remaining -= coin
                break
        else:
            # Should never happen if DP is correct
            raise RuntimeError("Reconstruction failed")

    return dp[target], combination


# Example usage (not part of the final answer, just for demonstration)
if __name__ == "__main__":
    # Test 1
    coins1 = [1, 2, 5]
    target1 = 11
    print(min_coin_combination(coins1, target1))  # (3, [5, 5, 1]) or (3, [5, 2, 2, 2]?) 
    # Our deterministic: 5,5,1

    # Test 2
    coins2 = [2]
    target2 = 3
    print(min_coin_combination(coins2, target2))  # (-1, [])

    # Test 3
    coins3 = [4, 6, 9]
    target3 = 20
    print(min_coin_combination(coins3, target3))  # (3, [6, 6, 8? no]) -> actually 9+9+? no, 6+6+? no -> 4+? 
    # 4*5=20 (5 coins), 6+6+4+4=20 (4 coins), 9+? 11 no. Best: 4+4+6+6=20 (4 coins) -> our DP will find 4,4,6,6