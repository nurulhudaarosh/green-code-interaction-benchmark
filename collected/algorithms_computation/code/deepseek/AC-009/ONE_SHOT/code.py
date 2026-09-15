from typing import List, Tuple

def coin_change(coins: List[int], target: int) -> Tuple[int, List[int]]:
    """
    Find minimum number of coins to make target amount using given denominations.
    Coins can be reused.
    
    Args:
        coins: List of coin denominations (positive integers)
        target: Target amount (non-negative integer)
    
    Returns:
        Tuple of (minimum number of coins, list of coins used)
        Returns (-1, []) if impossible
    """
    if target == 0:
        return 0, []
    
    if not coins or target < 0:
        return -1, []
    
    # Remove duplicates and sort for deterministic behavior
    coins = sorted(set(coins))
    
    # Filter out coins larger than target (they can't be used)
    coins = [c for c in coins if c <= target]
    
    if not coins:
        return -1, []
    
    # dp[i] = minimum coins needed to make amount i
    # prev[i] = last coin used to make amount i (for reconstruction)
    INF = float('inf')
    dp = [INF] * (target + 1)
    prev = [-1] * (target + 1)
    
    dp[0] = 0
    
    # Unbounded knapsack: iterate amounts, then coins
    # This allows reuse of coins
    for amount in range(1, target + 1):
        for coin in coins:
            if amount >= coin and dp[amount - coin] + 1 < dp[amount]:
                dp[amount] = dp[amount - coin] + 1
                prev[amount] = coin
    
    if dp[target] == INF:
        return -1, []
    
    # Reconstruct the combination
    combination = []
    remaining = target
    while remaining > 0:
        coin = prev[remaining]
        combination.append(coin)
        remaining -= coin
    
    # Reverse to get coins in ascending order for deterministic output
    combination.sort()
    
    return dp[target], combination


def main():
    """Test the implementation with example cases."""
    test_cases = [
        ([1, 2, 5], 11),
        ([2], 3),
        ([1, 3, 4], 6),
        ([], 5),
        ([5, 10], 0),
        ([2, 4, 6], 7),
        ([25, 10, 5, 1], 30),
    ]
    
    for coins, target in test_cases:
        count, combo = coin_change(coins, target)
        if count == -1:
            print(f"Coins: {coins}, Target: {target} -> Impossible")
        else:
            print(f"Coins: {coins}, Target: {target} -> Count: {count}, Combination: {combo}")
            # Verify
            assert sum(combo) == target
            assert len(combo) == count
            for c in combo:
                assert c in coins


if __name__ == "__main__":
    main()