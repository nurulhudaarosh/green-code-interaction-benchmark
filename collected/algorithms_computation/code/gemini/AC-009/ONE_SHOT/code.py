from typing import List, Tuple

def min_coins_change(coins: List[int], amount: int) -> Tuple[int, List[int]]:
    """
    Finds the minimum number of coins needed to reach 'amount' and returns
    the count and the sorted list of coins used.
    
    Returns:
        Tuple[int, List[int]]: (min_coin_count, list_of_coins)
        If impossible, returns (-1, []).
    """
    if amount < 0:
        return -1, []
    if amount == 0:
        return 0, []
    
    # Sort coin denominations for deterministic behavior
    sorted_coins = sorted(list(set(coins)))
    
    # dp[i] stores the minimum coins to make amount i
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    
    # parent_coin[i] stores the coin value used to reach amount i
    parent_coin = [-1] * (amount + 1)
    
    for i in range(1, amount + 1):
        for coin in sorted_coins:
            if i - coin >= 0 and dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
                parent_coin[i] = coin

    # If target amount is unreachable
    if dp[amount] == float('inf'):
        return -1, []
    
    # Reconstruct the coin combination
    result_coins = []
    curr = amount
    while curr > 0:
        c = parent_coin[curr]
        result_coins.append(c)
        curr -= c
        
    result_coins.sort()
    return int(dp[amount]), result_coins


# Example Execution:
if __name__ == "__main__":
    denominations = [1, 2, 5]
    target = 11
    count, chosen_coins = min_coins_change(denominations, target)
    print(f"Target: {target}")
    print(f"Minimum coins count: {count}")
    print(f"Coins used: {chosen_coins}")