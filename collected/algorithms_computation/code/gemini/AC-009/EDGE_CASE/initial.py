def min_coin_change(coins: list[int], amount: int) -> tuple[int, list[int]]:
    """
    Finds the minimum number of coins needed to make up a given amount,
    along with the combination of coins used.

    Args:
        coins: List of available coin denominations (positive integers).
        amount: Target sum (non-negative integer).

    Returns:
        A tuple of (min_coin_count, list_of_coins_used).
        Returns (-1, []) if the target amount cannot be made up.
    """
    if amount == 0:
        return (0, [])
    if not coins or amount < 0:
        return (-1, [])

    # Sort denominations to ensure deterministic transitions and reconstruction
    sorted_coins = sorted(list(set(coins)))

    # Initialize DP array and parent tracking array
    dp = [float('inf')] * (amount + 1)
    parent = [-1] * (amount + 1)
    dp[0] = 0

    # Fill DP table
    for i in range(1, amount + 1):
        for coin in sorted_coins:
            if i < coin:
                break  # Remaining coins are larger than current sub-amount
            if dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
                parent[i] = coin

    # Check if target amount is reachable
    if dp[amount] == float('inf'):
        return (-1, [])

    # Reconstruct the optimal combination
    result_coins = []
    curr = amount
    while curr > 0:
        coin_used = parent[curr]
        result_coins.append(coin_used)
        curr -= coin_used

    result_coins.sort()
    return (int(dp[amount]), result_coins)


# Execution & Verification Examples
if __name__ == "__main__":
    test_cases = [
        ([1, 2, 5], 11),  # Expected: (3, [1, 5, 5])
        ([2], 3),         # Expected: (-1, [])
        ([1, 3, 4, 5], 7), # Expected: (2, [2, 5] or [3, 4] depending on ties -> deterministic selection gives [2, 5] or [3, 4])
        ([186, 419, 83, 408], 6249), # Edge/larger case
        ([1], 0)          # Expected: (0, [])
    ]

    for coins, amount in test_cases:
        count, combo = min_coin_change(coins, amount)
        print(f"Coins: {coins}, Amount: {amount} -> Count: {count}, Combination: {combo}")