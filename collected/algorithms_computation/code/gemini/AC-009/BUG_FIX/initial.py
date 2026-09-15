from typing import List, Tuple

def min_coin_change(coins: List[int], amount: int) -> Tuple[int, List[int]]:
    if amount == 0:
        return 0, []
    if amount < 0 or not coins:
        return -1, []

    # Sort denominations to ensure deterministic state transitions
    coins = sorted(list(set(coins)))

    # Initialize DP array and Parent array
    inf = float('inf')
    dp = [inf] * (amount + 1)
    parent = [-1] * (amount + 1)
    dp[0] = 0

    # Fill DP table
    for i in range(1, amount + 1):
        for coin in coins:
            if i - coin >= 0 and dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
                parent[i] = coin

    # If amount cannot be formed
    if dp[amount] == inf:
        return -1, []

    # Reconstruct the coin combination deterministically
    combination = []
    curr = amount
    while curr > 0:
        coin_used = parent[curr]
        combination.append(coin_used)
        curr -= coin_used

    combination.sort()
    return int(dp[amount]), combination


# Example Usage & Test
if __name__ == "__main__":
    denominations = [1, 2, 5]
    target = 11
    count, chosen_coins = min_coin_change(denominations, target)
    print(f"Target: {target}")
    print(f"Minimum Coins: {count}")
    print(f"Coins Used: {chosen_coins}")