from typing import List, Tuple, Union, Dict


def min_coins(
    coins: List[int],
    amount: int,
    include_summary: bool = False,
) -> Union[Tuple[int, List[int]], Tuple[int, List[int], Dict[str, int]]]:
    """
    Minimum Coin Construction.

    Problem: Given coin denominations (reusable without limit) and a
    non-negative integer target `amount`, find the minimum number of
    coins summing exactly to `amount` via 1-D unbounded coin-change DP
    with deterministic reconstruction. Return -1 and [] if impossible.

    Required outputs (always present, unchanged):
        min_count : int -- minimum coins, or -1 if impossible.
        coin_list : List[int] -- coins used in deterministic reconstructed
                                  order, or [] if impossible / amount == 0.

    Optional output (only when include_summary=True):
        operation_summary : dict with transitions_evaluated,
                             dp_updates_applied, reconstruction_steps.

    Difficult / edge cases handled:
        - amount == 0 (smallest permitted target) -> (0, [])
        - coins == [] (empty/disconnected denomination set) -> (-1, [])
          unless amount == 0, which is always trivially achievable.
        - coins containing only values > amount -> (-1, [])
        - a single coin denomination equal to amount -> (1, [coin])
        - duplicate / non-positive / non-int entries in coins are
          filtered out during normalization, same as before.
    """
    if amount < 0:
        raise ValueError("amount must be non-negative")

    distinct_coins = sorted({c for c in coins if isinstance(c, int) and c > 0})

    if amount == 0:
        if include_summary:
            return 0, [], {
                "transitions_evaluated": 0,
                "dp_updates_applied": 0,
                "reconstruction_steps": 0,
            }
        return 0, []

    if not distinct_coins:
        if include_summary:
            return -1, [], {
                "transitions_evaluated": 0,
                "dp_updates_applied": 0,
                "reconstruction_steps": 0,
            }
        return -1, []

    INF = float("inf")
    dp = [INF] * (amount + 1)
    dp[0] = 0
    choice = [0] * (amount + 1)

    transitions_evaluated = 0
    dp_updates_applied = 0

    for i in range(1, amount + 1):
        for c in distinct_coins:
            if c > i:
                break
            transitions_evaluated += 1
            if dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
                choice[i] = c
                dp_updates_applied += 1

    if dp[amount] == INF:
        if include_summary:
            return -1, [], {
                "transitions_evaluated": transitions_evaluated,
                "dp_updates_applied": dp_updates_applied,
                "reconstruction_steps": 0,
            }
        return -1, []

    result_coins = []
    remaining = amount
    while remaining > 0:
        c = choice[remaining]
        result_coins.append(c)
        remaining -= c

    result_coins.reverse()

    if include_summary:
        summary = {
            "transitions_evaluated": transitions_evaluated,
            "dp_updates_applied": dp_updates_applied,
            "reconstruction_steps": len(result_coins),
        }
        return dp[amount], result_coins, summary

    return dp[amount], result_coins


if __name__ == "__main__":
    test_cases = [
        ([1, 2, 5], 11),
        ([2], 3),
        ([1], 0),
        ([186, 419, 83, 408], 6249),
        ([5, 10, 25], 30),
        ([2, 3], 7),
        ([1, 3, 4], 6),
        # --- difficult / edge cases ---
        ([], 0),          # empty coin set, smallest amount -> trivially 0
        ([], 5),          # empty coin set, nonzero amount -> impossible
        ([5], 0),         # smallest permitted target with nonempty coins
        ([7], 7),         # single denomination exactly equal to amount
        ([4], 6),         # single denomination, unreachable -> impossible
        ([3, 3, 3], 9),   # duplicate denominations collapse to one
        ([0, -1, 2], 4),  # non-positive entries filtered out
    ]

    print("-- default behavior --")
    for coins, amount in test_cases:
        result = min_coins(coins, amount)
        print(f"coins={coins}, amount={amount} -> {result}")

    print("\n-- with operation_summary --")
    for coins, amount in test_cases:
        result = min_coins(coins, amount, include_summary=True)
        print(f"coins={coins}, amount={amount} -> {result}")

    # --- assertions validating edge cases and original rules ---
    assert min_coins([], 0) == (0, [])
    assert min_coins([], 5) == (-1, [])
    assert min_coins([5], 0) == (0, [])
    assert min_coins([7], 7) == (1, [7])
    assert min_coins([4], 6) == (-1, [])
    assert min_coins([3, 3, 3], 9) == (3, [3, 3, 3])
    assert min_coins([0, -1, 2], 4) == (2, [2, 2])
    print("\nAll edge-case assertions passed.")