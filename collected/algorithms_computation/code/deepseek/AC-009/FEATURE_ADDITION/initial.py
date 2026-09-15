def coin_change(coins, target):
    """
    Find minimum number of coins to make target amount using given denominations.
    Coins can be reused. Returns (min_count, coin_combination).
    If impossible: returns (-1, [])
    
    Args:
        coins: List of positive integers representing coin denominations
        target: Non-negative integer target amount
    
    Returns:
        tuple: (minimum number of coins, list of coins used)
    """
    # Edge cases
    if target == 0:
        return (0, [])
    if not coins:
        return (-1, [])
    
    # Filter out coins larger than target and sort for deterministic behavior
    valid_coins = sorted([c for c in coins if c > 0 and c <= target])
    if not valid_coins:
        return (-1, [])
    
    # DP array: min coins to make each amount
    INF = float('inf')
    dp = [INF] * (target + 1)
    dp[0] = 0
    
    # Reconstruction array: last coin used to make each amount
    # -1 means no coin used yet
    last_coin = [-1] * (target + 1)
    
    # Unbounded DP (complete knapsack style)
    for amount in range(1, target + 1):
        for coin in valid_coins:
            if coin <= amount and dp[amount - coin] + 1 < dp[amount]:
                dp[amount] = dp[amount - coin] + 1
                last_coin[amount] = coin
    
    # Check if target is reachable
    if dp[target] == INF:
        return (-1, [])
    
    # Reconstruct the combination deterministically
    # Since we always take the first coin that improves dp (due to sorted coins),
    # the reconstruction is deterministic
    combination = []
    remaining = target
    while remaining > 0:
        coin = last_coin[remaining]
        if coin == -1:
            # Should not happen if dp[target] is finite
            return (-1, [])
        combination.append(coin)
        remaining -= coin
    
    # Sort for deterministic output (ascending order)
    combination.sort()
    
    return (dp[target], combination)


# Example usage and test cases
if __name__ == "__main__":
    # Test case 1: Standard example
    coins1 = [1, 2, 5]
    target1 = 11
    count1, combo1 = coin_change(coins1, target1)
    print(f"Coins: {coins1}, Target: {target1}")
    print(f"Minimum coins: {count1}, Combination: {combo1}")  # Should be 3, [5, 5, 1]
    print()
    
    # Test case 2: Impossible
    coins2 = [2]
    target2 = 3
    count2, combo2 = coin_change(coins2, target2)
    print(f"Coins: {coins2}, Target: {target2}")
    print(f"Minimum coins: {count2}, Combination: {combo2}")  # Should be -1, []
    print()
    
    # Test case 3: Target 0
    coins3 = [1, 2, 5]
    target3 = 0
    count3, combo3 = coin_change(coins3, target3)
    print(f"Coins: {coins3}, Target: {target3}")
    print(f"Minimum coins: {count3}, Combination: {combo3}")  # Should be 0, []
    print()
    
    # Test case 4: Empty coins
    coins4 = []
    target4 = 10
    count4, combo4 = coin_change(coins4, target4)
    print(f"Coins: {coins4}, Target: {target4}")
    print(f"Minimum coins: {count4}, Combination: {combo4}")  # Should be -1, []
    print()
    
    # Test case 5: Coins larger than target
    coins5 = [10, 20, 30]
    target5 = 15
    count5, combo5 = coin_change(coins5, target5)
    print(f"Coins: {coins5}, Target: {target5}")
    print(f"Minimum coins: {count5}, Combination: {combo5}")  # Should be -1, []
    print()
    
    # Test case 6: Multiple optimal solutions - deterministic behavior
    coins6 = [1, 3, 4]
    target6 = 6
    count6, combo6 = coin_change(coins6, target6)
    print(f"Coins: {coins6}, Target: {target6}")
    print(f"Minimum coins: {count6}, Combination: {combo6}")  # Should be 2, [3, 3]
    print()
    
    # Test case 7: Larger target
    coins7 = [2, 5, 10]
    target7 = 27
    count7, combo7 = coin_change(coins7, target7)
    print(f"Coins: {coins7}, Target: {target7}")
    print(f"Minimum coins: {count7}, Combination: {combo7}")  # Should be 4, [10, 10, 5, 2]