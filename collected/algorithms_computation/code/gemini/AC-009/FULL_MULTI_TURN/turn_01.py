def min_coin_change(coins: list[int], amount: int) -> tuple[int, list[int]]:
    """
    Finds the minimum number of coins to reach a target amount and returns both
    the count and the exact combination of coins used.
    
    Returns:
        tuple[int, list[int]]: (min_coin_count, list_of_coins_used)
    """
    if amount < 0:
        return -1, []
    if amount == 0:
        return 0, []
    
    # Filter non-positive coins and sort for deterministic behavior
    valid_coins = sorted([c for c in coins if c > 0])
    if not valid_coins:
        return -1, []

    # dp[i] holds the minimum number of coins needed for amount i
    dp = [float('inf')] * (amount + 1)
    # parent[i] holds the coin used to reach amount i
    parent = [-1] * (amount + 1)
    
    dp[0] = 0

    for i in range(1, amount + 1):
        for coin in valid_coins:
            if coin > i:
                break  # Since valid_coins is sorted, no larger coin can fit
            if dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
                parent[i] = coin

    # If amount cannot be reached
    if dp[amount] == float('inf'):
        return -1, []

    # Reconstruct the optimal combination
    combination = []
    curr = amount
    while curr > 0:
        coin_used = parent[curr]
        combination.append(coin_used)
        curr -= coin_used

    return int(dp[amount]), combination


# Example Usage
if __name__ == "__main__":
    sample_coins = [1, 2, 5]
    sample_amount = 11
    count, combination = min_coin_change(sample_coins, sample_amount)
    print(f"Amount: {sample_amount}")
    print(f"Minimum Coins: {count}")
    print(f"Combination: {combination}")