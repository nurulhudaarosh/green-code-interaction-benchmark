def coin_change(coins, amount):
    """
    Find minimum number of coins to make up the given amount.
    Coins can be reused.
    
    Tie-breaking rule: When multiple combinations achieve the minimum coin count,
    return the combination that is lexicographically smallest when sorted.
    
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
    INF = float('inf')
    dp = [INF] * (amount + 1)
    dp[0] = 0
    
    # For reconstruction, store which coin was used last for each amount
    # We'll use a list of tuples to handle ties deterministically
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
    
    # Reconstruct ONE optimal solution
    # Note: This reconstruction may not give the tie-breaking we want
    # We need to enforce deterministic tie-breaking
    
    # Correct approach: Store all ways to achieve each amount with minimal coins
    # Then choose the lexicographically smallest combination
    
    # We'll use a different DP that stores the actual combination
    dp_comb = [None] * (amount + 1)
    dp_comb[0] = []
    
    for i in range(1, amount + 1):
        best_comb = None
        for coin in valid_coins:
            if i >= coin and dp_comb[i - coin] is not None:
                candidate = sorted(dp_comb[i - coin] + [coin])
                if best_comb is None or len(candidate) < len(best_comb) or \
                   (len(candidate) == len(best_comb) and candidate < best_comb):
                    best_comb = candidate
        dp_comb[i] = best_comb
    
    if dp_comb[amount] is None:
        return -1, []
    
    return len(dp_comb[amount]), dp_comb[amount]


# Alternative: More efficient DP with tie handling using lexicographic ordering
def coin_change_deterministic(coins, amount):
    """
    More efficient version that maintains both count and lexicographically smallest
    combination for each amount.
    """
    if not coins or amount < 0:
        return -1, []
    
    if amount == 0:
        return 0, []
    
    valid_coins = sorted([c for c in coins if c > 0 and c <= amount])
    if not valid_coins:
        return -1, []
    
    # dp[i] = (min_coins, combination) for amount i
    # Initialize with None for impossible states
    dp = [None] * (amount + 1)
    dp[0] = (0, [])
    
    for i in range(1, amount + 1):
        best = None
        for coin in valid_coins:
            if i >= coin and dp[i - coin] is not None:
                count, combo = dp[i - coin]
                new_combo = sorted(combo + [coin])
                candidate = (count + 1, new_combo)
                
                if best is None:
                    best = candidate
                elif candidate[0] < best[0]:
                    best = candidate
                elif candidate[0] == best[0] and candidate[1] < best[1]:
                    # Tie-break: lexicographically smaller combination
                    best = candidate
        
        dp[i] = best
    
    if dp[amount] is None:
        return -1, []
    
    return dp[amount][0], dp[amount][1]


# Test the corrected implementation
if __name__ == "__main__":
    test_cases = [
        ([2, 3, 4], 6),    # Tie: [2,4] and [3,3] -> both 2 coins
        ([1, 2, 3], 4),    # Tie: [1,3] and [2,2] -> both 2 coins
        ([2, 5, 3], 8),    # [3,5] is optimal with 2 coins
        ([1, 2, 5], 11),   # Multiple ways, [1,5,5] uses 3 coins
        ([2], 3),          # Impossible
        ([1, 3, 4], 6),    # [3,3] vs [2,4] (2 is not available)
        ([25, 10, 5], 30), # [5,10,15?] actually [5,10,10,5] = 4 coins
        ([2, 4, 6], 7),    # Impossible
        ([1], 0),          # 0 coins needed
        ([3, 7, 11], 14),  # [3,11] or [7,7] both 2 coins
    ]
    
    print("Using coin_change (original approach with tie-breaking):")
    for coins, amount in test_cases:
        count, combo = coin_change(coins, amount)
        print(f"coins={coins}, amount={amount} -> min={count}, combo={combo}")
    
    print("\nUsing coin_change_deterministic (explicit tie-breaking):")
    for coins, amount in test_cases:
        count, combo = coin_change_deterministic(coins, amount)
        print(f"coins={coins}, amount={amount} -> min={count}, combo={combo}")