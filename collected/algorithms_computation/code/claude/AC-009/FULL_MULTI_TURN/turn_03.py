from typing import List, Tuple, Union, Dict


def min_coins(
    coins: List[int],
    amount: int,
    include_summary: bool = False,
) -> Union[Tuple[int, List[int]], Tuple[int, List[int], Dict[str, int]]]:
    """
    Minimum Coin Construction.

    Original required outputs (always present):
        min_count : int  -- minimum coins to make `amount`, or -1 if impossible.
        coin_list : List[int] -- coins used, in deterministic reconstructed
                                  order, or [] if impossible / amount == 0.

    Optional new output (only when include_summary=True):
        operation_summary : dict with deterministic counts of major
                             computational decisions made by the DP:
            - transitions_evaluated : number of (i, coin) pairs examined
            - dp_updates_applied    : number of times dp[i] was improved
            - reconstruction_steps  : number of coins emitted during
                                       backward reconstruction

    When include_summary=False (default), the return value is exactly
    the original (min_count, coin_list) tuple -- unchanged behavior.
    """
    if amount < 0:
        raise ValueError("amount must be non-negative")

    distinct_coins = sorted({c for c in coins if isinstance(c, int) and c > 0})

    # --- Trivial cases: preserve original semantics exactly ---
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

    # Deterministic reconstruction: preserve the actual DP-chosen path.
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
    ]

    print("-- default behavior (unchanged) --")
    for coins, amount in test_cases:
        result = min_coins(coins, amount)
        print(f"coins={coins}, amount={amount} -> {result}")

    print("\n-- with operation_summary --")
    for coins, amount in test_cases:
        result = min_coins(coins, amount, include_summary=True)
        print(f"coins={coins}, amount={amount} -> {result}")