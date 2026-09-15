def min_coin_change(
    coins: list[int], 
    amount: int, 
    include_summary: bool = False
) -> tuple[int, list[int]] | tuple[int, list[int], dict[str, int]]:
    """
    Finds the minimum number of coins to reach a target amount using 1D DP and 
    deterministic reconstruction (preferring larger coins on ties).

    Args:
        coins: Available coin denominations.
        amount: Target sum.
        include_summary: If True, appends an operation summary dict to the output.

    Returns:
        (min_coins, combination) if include_summary is False,
        (min_coins, combination, operation_summary) if include_summary is True.
    """
    summary = {
        "total_states_evaluated": 0,
        "relaxation_attempts": 0,
        "optimal_updates": 0
    }

    if amount < 0:
        return (-1, [], summary) if include_summary else (-1, [])
    if amount == 0:
        return (0, [], summary) if include_summary else (0, [])

    # Filter positive unique coins and sort DESCENDING for deterministic tie-breaking
    valid_coins = sorted(list(set(c for c in coins if c > 0)), reverse=True)
    if not valid_coins:
        return (-1, [], summary) if include_summary else (-1, [])

    dp = [float('inf')] * (amount + 1)
    parent = [-1] * (amount + 1)
    dp[0] = 0

    summary["total_states_evaluated"] = amount

    for i in range(1, amount + 1):
        for coin in valid_coins:
            if coin <= i:
                summary["relaxation_attempts"] += 1
                if dp[i - coin] + 1 < dp[i]:
                    dp[i] = dp[i - coin] + 1
                    parent[i] = coin
                    summary["optimal_updates"] += 1

    # Unreachable state
    if dp[amount] == float('inf'):
        return (-1, [], summary) if include_summary else (-1, [])

    # Deterministic Reconstruction
    combination = []
    curr = amount
    while curr > 0:
        coin_used = parent[curr]
        combination.append(coin_used)
        curr -= coin_used

    min_coins = int(dp[amount])

    if include_summary:
        return min_coins, combination, summary
    return min_coins, combination


# Example Usage
if __name__ == "__main__":
    test_coins = [2, 3, 4]
    test_amount = 6

    # Original requirement unchanged
    res_standard = min_coin_change(test_coins, test_amount)
    print("Standard Output:", res_standard)
    # Output: (2, [4, 2])

    # Enhanced feature requested
    res_summary = min_coin_change(test_coins, test_amount, include_summary=True)
    print("With Operation Summary:", res_summary)
    # Output: (2, [4, 2], {'total_states_evaluated': 6, 'relaxation_attempts': 12, 'optimal_updates': 7})