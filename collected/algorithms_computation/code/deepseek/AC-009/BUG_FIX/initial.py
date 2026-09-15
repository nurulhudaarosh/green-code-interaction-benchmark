def coin_change(coins, amount):
    """
    Find minimum number of coins to make up the given amount.
    Coins can be reused.
    
    Args:
        coins: List of positive integers (coin denominations)
        amount: Non-negative integer target amount
        
    Returns:
        tuple: (min_coins, combination) where:
            - min_coins is the minimum number of coins needed (-1 if impossible)
            - combination is a list of coins used (empty list if impossible)
    """
    # Edge cases
    if not coins or amount < 0:
        return -1, []
    
    if amount == 0:
        return 0, []
    
    # Filter out coins larger than amount and sort for deterministic behavior
    valid_coins = sorted([c for c in coins if c > 0 and c <= amount])
    if not valid_coins:
        return -1, []
    
    # DP array: dp[i] = minimum coins to make amount i
    # Initialize with a large number (infinity)
    INF = float('inf')
    dp = [INF] * (amount + 1)
    dp[0] = 0
    
    # For reconstruction, store which coin was used last for each amount
    last_coin = [-1] * (amount + 1)
    
    # Unbounded knapsack style DP (complete knapsack)
    for i in range(1, amount + 1):
        for coin in valid_coins:
            if i >= coin and dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
                last_coin[i] = coin
    
    # Check if impossible
    if dp[amount] == INF:
        return -1, []
    
    # Reconstruct the combination
    combination = []
    remaining = amount
    while remaining > 0:
        coin = last_coin[remaining]
        if coin == -1:
            # This should not happen if dp[amount] is finite
            return -1, []
        combination.append(coin)
        remaining -= coin
    
    # Reverse to get coins in ascending order (deterministic)
    combination.sort()
    
    return dp[amount], combination


# Test with examples
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ([1, 2, 5], 11),
        ([2], 3),
        ([1, 3, 4], 6),
        ([25, 10, 5], 30),
        ([2, 4, 6], 7),
        ([1], 0),
        ([], 10),
        ([5, 10, 20], 0),
        ([3, 7, 11], 14),
        ([1, 2, 3, 4, 5], 100),
    ]
    
    for coins, amount in test_cases:
        count, combo = coin_change(coins, amount)
        print(f"coins={coins}, amount={amount}")
        print(f"  min coins={count}, combination={combo}")
        
        # Verify if possible
        if count != -1:
            assert sum(combo) == amount
            assert len(combo) == count
            # Verify all coins are from the valid set
            for c in combo:
                assert c in coins
        print()