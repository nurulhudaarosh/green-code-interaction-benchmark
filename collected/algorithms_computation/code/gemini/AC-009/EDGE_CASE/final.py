def min_coin_change(coins: list[int], amount: int) -> tuple[int, list[int]]:
    """
    Finds the minimum number of coins needed to make up a given amount,
    along with the combination of coins used. Explicitly handles edge cases,
    empty coin lists, zero/negative amounts, and unreachable amounts.

    Args:
        coins: List of available coin denominations.
        amount: Target sum (non-negative integer).

    Returns:
        A tuple of (min_coin_count, list_of_coins_used).
        Returns (-1, []) if the target amount cannot be made up or is invalid.
    """
    # Boundary Case 1: Target amount is 0 (Smallest permitted valid input)
    if amount == 0:
        return (0, [])

    # Boundary Case 2: Negative amount or empty coin list with non-zero target
    if amount < 0 or not coins:
        return (-1, [])

    # Sanitize and sort coin denominations (remove duplicates and non-positive values)
    valid_coins = sorted(list(set(c for c in coins if c > 0)))

    # If no valid positive coins exist for a positive amount
    if not valid_coins:
        return (-1, [])

    # Initialize DP array and parent tracking array
    dp = [float('inf')] * (amount + 1)
    parent = [-1] * (amount + 1)
    dp[0] = 0

    # Fill DP table with deterministic tie-breaking (first strictly smaller count wins)
    for i in range(1, amount + 1):
        for coin in valid_coins:
            if i < coin:
                break  # Remaining coins are larger than current sub-amount
            if dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
                parent[i] = coin

    # Boundary Case 3: Disconnected / Unreachable Target
    if dp[amount] == float('inf'):
        return (-1, [])

    # Reconstruct the optimal combination
    result_coins = []
    curr = amount
    while curr > 0:
        coin_used = parent[curr]
        result_coins.append(coin_used)
        curr -= coin_used

    result_coins.sort()
    return (int(dp[amount]), result_coins)


def run_tests():
    test_cases = [
        # (coins, amount, expected_output, description)
        ([1, 2, 5], 11, (3, [1, 5, 5]), "Standard case"),
        ([2], 3, (-1, []), "Disconnected/Unreachable case"),
        ([1, 3, 4, 5], 7, (2, [3, 4]), "Tie-breaking case (Deterministic selection [3,4])"),
        
        # Explicit Boundary & Edge Cases
        ([1, 2, 5], 0, (0, []), "Smallest permitted input: amount = 0"),
        ([], 0, (0, []), "Empty coins with amount = 0"),
        ([], 5, (-1, []), "Empty coins with positive amount"),
        ([1, 2, 5], -5, (-1, []), "Negative target amount"),
        ([0, -1, -5], 10, (-1, []), "Only zero/negative coin denominations"),
        ([0, 2, 5], 6, (3, [2, 2, 2]), "Filter out invalid zero denomination"),
        ([5, 10], 3, (-1, []), "Target smaller than smallest coin denomination"),
        ([4, 6], 11, (-1, []), "Unreachable parity combination"),
        ([186, 419, 83, 408], 6249, (15, [83, 83, 408, 408, 408, 408, 408, 408, 408, 408, 408, 408, 408, 408, 419]), "Larger target case")
    ]

    print(f"{'Test Description':<48} | {'Result':<6} | Output")
    print("-" * 80)

    for coins, amount, expected, desc in test_cases:
        result = min_coin_change(coins, amount)
        passed = result == expected
        status = "PASS" if passed else "FAIL"
        print(f"{desc:<48} | {status:<6} | {result}")
        assert passed, f"Failed on '{desc}'. Expected {expected}, got {result}"


if __name__ == "__main__":
    run_tests()