from typing import Union, Tuple, Dict, Any


def min_coin_change(
    coins: list[int], 
    amount: int, 
    include_summary: bool = False
) -> Union[Tuple[int, list[int]], Tuple[int, list[int], Dict[str, int]]]:
    """
    Finds the minimum number of coins needed to reach `amount` and reconstructs the combination.

    :param coins: List of positive integer coin denominations.
    :param amount: Target integer amount.
    :param include_summary: If True, returns a 3-tuple including operation metrics.
    :return: (min_coins, combination) or (min_coins, combination, operation_summary)
    """
    # Track operation metrics deterministically
    decisions_evaluated = 0
    optimal_updates = 0
    reconstruction_steps = 0

    def make_summary() -> Dict[str, int]:
        return {
            "decisions_evaluated": decisions_evaluated,
            "optimal_updates": optimal_updates,
            "reconstruction_steps": reconstruction_steps,
        }

    # Handle edge/invalid cases
    if amount == 0:
        if include_summary:
            return 0, [], make_summary()
        return 0, []

    if not coins or amount < 0:
        if include_summary:
            return -1, [], make_summary()
        return -1, []

    # Sort coins for deterministic path resolution during ties
    sorted_coins = sorted(coins)

    dp = [float('inf')] * (amount + 1)
    parent = [-1] * (amount + 1)
    dp[0] = 0

    # DP Execution & Operational Counting
    for i in range(1, amount + 1):
        for coin in sorted_coins:
            if i - coin >= 0:
                decisions_evaluated += 1
                if dp[i - coin] + 1 < dp[i]:
                    dp[i] = dp[i - coin] + 1
                    parent[i] = coin
                    optimal_updates += 1

    # Unreachable state
    if dp[amount] == float('inf'):
        if include_summary:
            return -1, [], make_summary()
        return -1, []

    # Path Reconstruction
    result_coins = []
    curr = amount
    while curr > 0:
        reconstruction_steps += 1
        coin_used = parent[curr]
        result_coins.append(coin_used)
        curr -= coin_used

    result_coins.sort()

    if include_summary:
        return dp[amount], result_coins, make_summary()
    
    return dp[amount], result_coins


# Verification / Demonstration
if __name__ == "__main__":
    test_coins = [1, 2, 5]
    target = 11

    # Default call (Backward-compatible original output)
    min_count, combination = min_coin_change(test_coins, target)
    print("--- Default Output ---")
    print(f"Result: count={min_count}, coins={combination}")

    # Feature-enabled call
    min_count, combination, summary = min_coin_change(test_coins, target, include_summary=True)
    print("\n--- Summary Feature Enabled ---")
    print(f"Result: count={min_count}, coins={combination}")
    print(f"Operation Summary: {summary}")