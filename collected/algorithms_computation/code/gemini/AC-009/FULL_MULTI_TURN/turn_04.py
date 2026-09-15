def min_coin_change(
    coins: list[int], 
    amount: int, 
    include_summary: bool = False
) -> tuple[int, list[int]] | tuple[int, list[int], dict[str, int]]:
    """
    Finds the minimum number of coins to reach a target amount using 1D DP and 
    deterministic reconstruction (preferring larger coins on ties). Handles edge cases 
    such as zero amount, empty coin list, or disconnected/unreachable amounts.
    """
    summary = {
        "total_states_evaluated": 0,
        "relaxation_attempts": 0,
        "optimal_updates": 0
    }

    # Smallest permitted inputs / Invalid amounts
    if amount < 0:
        return (-1, [], summary) if include_summary else (-1, [])
    if amount == 0:
        return (0, [], summary) if include_summary else (0, [])

    # Filter positive unique coins and sort DESCENDING for deterministic tie-breaking
    valid_coins = sorted(list(set(c for c in coins if c > 0)), reverse=True)
    
    # Disconnected / Empty structure check
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


# Unit Tests
def run_tests():
    test_cases = [
        # (Name, coins, amount, expected_result)
        ("Zero amount (smallest permitted input)", [1, 2, 5], 0, (0, [])),
        ("Empty coins list", [], 10, (-1, [])),
        ("Non-positive coins only", [0, -2, -5], 5, (-1, [])),
        ("Coins strictly larger than amount", [10, 20], 5, (-1, [])),
        ("Disconnected/Unreachable parity", [2, 4], 5, (-1, [])),
        ("Single valid coin match", [5], 5, (1, [5])),
        ("Deterministic tie breaking ([4, 2] vs [3, 3])", [2, 3, 4], 6, (2, [4, 2])),
        ("Standard unbounded change", [1, 2, 5], 11, (3, [5, 5, 1])),
    ]

    for name, coins, amount, expected in test_cases:
        res = min_coin_change(coins, amount)
        assert res == expected, f"Failed [{name}]: expected {expected}, got {res}"
        print(f"PASSED: {name} -> {res}")

    # Summary verification
    count, comb, summary = min_coin_change([2, 3, 4], 6, include_summary=True)
    assert count == 2 and comb == [4, 2] and summary["total_states_evaluated"] == 6
    print("PASSED: Operation summary feature check")

if __name__ == "__main__":
    run_tests()