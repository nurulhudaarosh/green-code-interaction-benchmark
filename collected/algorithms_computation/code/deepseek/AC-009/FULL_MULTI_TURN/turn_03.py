def min_coin_combination(coins, target):
    """
    Returns (min_coins, combination, operation_summary) where:
    - min_coins: minimum number of coins needed to make target, or -1 if impossible
    - combination: list of coin values achieving that minimum, or [] if impossible
    - operation_summary: dict with 'dp_operations' and 'reconstruction_operations' counts
    
    Coins may be reused unlimited times.
    Deterministic tie-breaking: prefers coins appearing earlier in the input list.
    Uses 1D unbounded coin-change DP with deterministic reconstruction.
    """
    # Edge cases
    if target < 0:
        return -1, [], {"dp_operations": 0, "reconstruction_operations": 0}
    if target == 0:
        return 0, [], {"dp_operations": 0, "reconstruction_operations": 0}

    # Filter coins that could potentially be used
    useful_coins = [c for c in coins if c <= target]
    if not useful_coins:
        return -1, [], {"dp_operations": 0, "reconstruction_operations": 0}

    INF = float('inf')
    dp = [INF] * (target + 1)
    dp[0] = 0

    # 1D unbounded coin-change DP with operation counting
    dp_operations = 0
    for coin in useful_coins:
        for amt in range(coin, target + 1):
            dp_operations += 1  # Count each comparison/update attempt
            if dp[amt - coin] + 1 <= dp[amt]:
                dp[amt] = dp[amt - coin] + 1

    # If target is unreachable
    if dp[target] == INF:
        return -1, [], {"dp_operations": dp_operations, "reconstruction_operations": 0}

    # Deterministic reconstruction with operation counting
    combination = []
    remaining = target
    reconstruction_operations = 0
    while remaining > 0:
        for coin in useful_coins:
            reconstruction_operations += 1  # Count each coin check
            if remaining >= coin and dp[remaining] == dp[remaining - coin] + 1:
                combination.append(coin)
                remaining -= coin
                break
        else:
            # Safety guard - should never happen with correct DP
            raise RuntimeError("Reconstruction failed: inconsistent DP state")

    operation_summary = {
        "dp_operations": dp_operations,
        "reconstruction_operations": reconstruction_operations,
        "total_operations": dp_operations + reconstruction_operations
    }

    return dp[target], combination, operation_summary


# Example usage demonstrating the feature
if __name__ == "__main__":
    # Test 1: Normal case
    coins1 = [1, 2, 5]
    target1 = 11
    count1, combo1, summary1 = min_coin_combination(coins1, target1)
    print(f"Coins: {coins1}, Target: {target1}")
    print(f"Result: count={count1}, combination={combo1}")
    print(f"Summary: {summary1}\n")

    # Test 2: Impossible case
    coins2 = [2]
    target2 = 3
    count2, combo2, summary2 = min_coin_combination(coins2, target2)
    print(f"Coins: {coins2}, Target: {target2}")
    print(f"Result: count={count2}, combination={combo2}")
    print(f"Summary: {summary2}\n")

    # Test 3: Target 0
    coins3 = [5, 10]
    target3 = 0
    count3, combo3, summary3 = min_coin_combination(coins3, target3)
    print(f"Coins: {coins3}, Target: {target3}")
    print(f"Result: count={count3}, combination={combo3}")
    print(f"Summary: {summary3}\n")

    # Test 4: Multiple optimal solutions (demonstrates deterministic tie-breaking)
    coins4 = [2, 3, 4]
    target4 = 6
    count4, combo4, summary4 = min_coin_combination(coins4, target4)
    print(f"Coins: {coins4}, Target: {target4}")
    print(f"Result: count={count4}, combination={combo4}")
    print(f"Summary: {summary4}\n")

    # Test 5: Larger example
    coins5 = [3, 5, 7, 11]
    target5 = 30
    count5, combo5, summary5 = min_coin_combination(coins5, target5)
    print(f"Coins: {coins5}, Target: {target5}")
    print(f"Result: count={count5}, combination={combo5}")
    print(f"Summary: {summary5}")