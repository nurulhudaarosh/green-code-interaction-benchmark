def min_coin_change(coins: list[int], amount: int) -> tuple[int, list[int]]:
    """
    Finds the minimum number of coins to reach a target amount and returns both
    the count and a deterministically reconstructed combination (preferring larger coins).
    
    Returns:
        tuple[int, list[int]]: (min_coin_count, list_of_coins_used)
    """
    if amount < 0:
        return -1, []
    if amount == 0:
        return 0, []
    
    # Filter positive coins and sort in DESCENDING order for deterministic tie-breaking
    # (Preferring larger coins when coin counts are identical)
    valid_coins = sorted(list(set(c for c in coins if c > 0)), reverse=True)
    if not valid_coins:
        return -1, []

    # dp[i] holds minimum coins needed for amount i
    dp = [float('inf')] * (amount + 1)
    # parent[i] holds the coin denomination chosen for amount i
    parent = [-1] * (amount + 1)
    
    dp[0] = 0

    for i in range(1, amount + 1):
        for coin in valid_coins:
            if coin <= i and dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
                parent[i] = coin

    # If amount cannot be reached
    if dp[amount] == float('inf'):
        return -1, []

    # Deterministic Path Reconstruction
    combination = []
    curr = amount
    while curr > 0:
        coin_used = parent[curr]
        combination.append(coin_used)
        curr -= coin_used

    return int(dp[amount]), combination


# Verification Example
if __name__ == "__main__":
    # Ties between [4, 2] and [3, 3] (both 2 coins)
    # Solved deterministically picking [4, 2] due to descending order preference
    test_coins = [2, 3, 4]
    test_amount = 6
    count, combination = min_coin_change(test_coins, test_amount)
    print(f"Amount: {test_amount}")
    print(f"Minimum Coins: {count}")
    print(f"Deterministic Combination: {combination}")  # Output: [4, 2]