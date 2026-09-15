"""
Minimum-coin-count coin change (unbounded knapsack DP).

Given a list of coin denominations and a target amount, find a combination
of coins (each denomination reusable without limit) that sums exactly to
the amount using the fewest coins possible.

Deterministic by construction:
    - Coins are de-duplicated and sorted ascending before the DP runs.
    - The DP scans coins in that fixed ascending order and only updates
      dp[i] on a STRICT improvement (dp[i-c] + 1 < dp[i]), so the first
      (smallest) denomination that achieves the best count for a given
      amount is always the one recorded. Re-running with the same input
      always reconstructs the same coin list, not just the same count.

No network access, no randomness, no external dependencies, no I/O
beyond what the caller explicitly triggers via __main__.
"""

from typing import List, Tuple

INF = float("inf")


def min_coins(coins: List[int], amount: int) -> Tuple[int, List[int]]:
    """
    Compute the minimum number of coins (with reuse allowed) that sum
    exactly to `amount`.

    Args:
        coins: list of positive integer denominations. Non-positive or
               duplicate values are ignored/de-duplicated.
        amount: non-negative integer target.

    Returns:
        (min_count, coin_list)
            - coin_list sums to `amount` and has length `min_count`.
            - If `amount` cannot be formed exactly, returns (-1, []).
            - If `amount == 0`, returns (0, []).

    Raises:
        ValueError: if amount is negative.
    """
    if amount < 0:
        raise ValueError("amount must be non-negative")

    # Sanitize: keep only positive, unique denominations, sorted ascending
    # for deterministic tie-breaking.
    unique_coins = sorted({c for c in coins if isinstance(c, int) and c > 0})

    if amount == 0:
        return 0, []

    if not unique_coins:
        return -1, []

    # dp[i]     = minimum number of coins to make amount i (INF if impossible)
    # choice[i] = denomination used for the last coin placed to reach i
    dp = [0] + [INF] * amount
    choice = [0] * (amount + 1)

    for i in range(1, amount + 1):
        for c in unique_coins:
            if c > i:
                break  # coins sorted ascending; no smaller coin left to try
            if dp[i - c] + 1 < dp[i]:  # strict '<' => deterministic tie-break
                dp[i] = dp[i - c] + 1
                choice[i] = c

    if dp[amount] == INF:
        return -1, []

    # Reconstruct the coin list by walking the choice[] trail backwards.
    result = []
    remaining = amount
    while remaining > 0:
        c = choice[remaining]
        result.append(c)
        remaining -= c

    return dp[amount], result


def _self_check() -> None:
    """Small deterministic sanity checks (no randomness, no I/O side effects)."""
    cases = [
        (([1, 2, 5], 11), (3, [1, 5, 5])),
        (([2], 3), (-1, [])),
        (([1], 0), (0, [])),
        (([186, 419, 83, 408], 6249), (20, None)),  # count known; list not hand-verified here
    ]
    for (coins, amount), (expected_count, expected_list) in cases:
        count, lst = min_coins(coins, amount)
        assert count == expected_count, f"count mismatch for {coins}, {amount}: got {count}"
        if count == -1:
            assert lst == [], "impossible case should return empty list"
        else:
            assert sum(lst) == amount, "coin list does not sum to amount"
            assert len(lst) == count, "coin list length does not match reported count"
        if expected_list is not None:
            assert lst == expected_list, f"list mismatch: got {lst}"
    print("All self-checks passed.")


if __name__ == "__main__":
    _self_check()

    demo_coins = [1, 2, 5]
    demo_amount = 11
    count, coin_list = min_coins(demo_coins, demo_amount)
    print(f"coins={demo_coins}, amount={demo_amount} -> count={count}, coins used={coin_list}")

    demo_coins2 = [2]
    demo_amount2 = 3
    count2, coin_list2 = min_coins(demo_coins2, demo_amount2)
    print(f"coins={demo_coins2}, amount={demo_amount2} -> count={count2}, coins used={coin_list2}")