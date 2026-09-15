def min_coin_change(coins: list[int], amount: int) -> tuple[int, list[int]]:
    """
    Finds the minimum number of coins needed to reach `amount` and 
    returns a tuple (minimum_coin_count, list_of_coins_used).
    Returns (-1, []) if the amount cannot be formed.
    """
    if amount == 0:
        return 0, []
    if not coins or amount < 0:
        return -1, []

    # Sort denominations to enforce deterministic coin selection during ties
    sorted_coins = sorted(coins)

    # dp[i] will store the minimum number of coins needed for amount i
    dp = [float('inf')] * (amount + 1)
    # parent[i] will store the last coin denomination used to achieve amount i optimally
    parent = [-1] * (amount + 1)

    dp[0] = 0

    for i in range(1, amount + 1):
        for coin in sorted_coins:
            if i - coin >= 0 and dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
                parent[i] = coin

    # If the target amount is unreachable
    if dp[amount] == float('inf'):
        return -1, []

    # Reconstruct the deterministic combination of coins used
    result_coins = []
    curr = amount
    while curr > 0:
        coin_used = parent[curr]
        result_coins.append(coin_used)
        curr -= coin_used

    # Sort the returned coins for clean, deterministic presentation
    result_coins.sort()

    return dp[amount], result_coins


# Verification / Example Usage
if __name__ == "__main__":
    test_coins = [1, 2, 5]
    target = 11
    count, combination = min_coin_change(test_coins, target)
    print(f"Target: {target}, Coins: {test_coins}")
    print(f"Minimum Count: {count}")
    print(f"Coins Used: {combination}")