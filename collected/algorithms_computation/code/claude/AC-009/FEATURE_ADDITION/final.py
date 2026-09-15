"""
Problem (restated)
-------------------
Given a list of coin denominations and a target amount, find a combination
of coins (each denomination may be reused any number of times) that sums
exactly to the target using the MINIMUM number of coins. Coins may be
reused. If the target cannot be formed with the given coins, return
count -1 and an empty list.

Key constraints
---------------
- Coins may be reused an unlimited number of times (unbounded knapsack style).
- Denominations are positive integers; amount is a non-negative integer.
- Must be deterministic: given the same input, always return the same
  count and the same list of coins (ties broken in a fixed, reproducible way).
- No network access, APIs, external services, randomness, or human
  interaction — pure standard-library computation only.

Required outputs (original, unchanged)
---------------------------------------
A tuple: (min_count, coins_used)
  - min_count: minimum number of coins needed, or -1 if impossible.
  - coins_used: a list of the actual coins summing to `amount`
                (length == min_count), or [] if impossible.
These two fields are always returned exactly as before, regardless of
whether the new optional feature is enabled.

New optional feature
---------------------
When explicitly requested (via `include_summary=True`), the function
additionally returns a third field, `operation_summary`: a dict reporting
a deterministic count of the major computational decisions/operations the
algorithm performed — specifically the number of dp[a] update checks
(inner loop iterations) and the number of strict improvements actually
applied. This field is purely diagnostic and never affects min_count or
coins_used. When the feature is disabled/not requested, the return shape
and values are identical to the original two-field contract.

Algorithm
---------
Classic 1-D unbounded coin-change DP:
  dp[a] = minimum number of coins to make amount `a`
  dp[0] = 0 ; dp[a] = min(dp[a - c] + 1) over all coins c <= a

choice[a] = the coin used to arrive at the optimal dp[a] (the last coin
added), updated only on STRICT improvement (never on ties) to guarantee
a deterministic result when scanning coins in fixed sorted order.

Reconstruction walks choice[] from `amount` down to 0.

Complexity: O(amount * len(coins)) time, O(amount) space.
"""

from typing import List, Tuple, Union, Dict


def min_coins(
    coins: List[int],
    amount: int,
    include_summary: bool = False,
) -> Union[Tuple[int, List[int]], Tuple[int, List[int], Dict[str, int]]]:
    # --- Validate / normalize input ---
    if amount < 0:
        raise ValueError("amount must be non-negative")

    clean_coins = sorted({c for c in coins if isinstance(c, int) and c > 0})

    # --- Trivial cases ---
    if amount == 0:
        if include_summary:
            return 0, [], {"dp_checks": 0, "improvements_applied": 0}
        return 0, []

    if not clean_coins:
        if include_summary:
            return -1, [], {"dp_checks": 0, "improvements_applied": 0}
        return -1, []

    INF = float("inf")
    dp = [INF] * (amount + 1)
    dp[0] = 0
    choice = [None] * (amount + 1)

    dp_checks = 0            # number of dp[a-c]+1 comparisons performed
    improvements_applied = 0  # number of strict improvements actually applied

    for a in range(1, amount + 1):
        for c in clean_coins:
            if c > a:
                break
            dp_checks += 1
            if dp[a - c] + 1 < dp[a]:
                dp[a] = dp[a - c] + 1
                choice[a] = c
                improvements_applied += 1

    if dp[amount] == INF:
        if include_summary:
            return -1, [], {
                "dp_checks": dp_checks,
                "improvements_applied": improvements_applied,
            }
        return -1, []

    # --- Reconstruct the coin combination ---
    result = []
    remaining = amount
    while remaining > 0:
        c = choice[remaining]
        result.append(c)
        remaining -= c

    result.sort()

    if include_summary:
        summary = {
            "dp_checks": dp_checks,
            "improvements_applied": improvements_applied,
        }
        return dp[amount], result, summary

    return dp[amount], result


if __name__ == "__main__":
    test_cases = [
        ([1, 2, 5], 11),
        ([2], 3),
        ([1], 0),
        ([186, 419, 83, 408], 6249),
        ([3, 7], 5),
    ]

    print("Without summary (original contract, unchanged):")
    for coins, amt in test_cases:
        count, used = min_coins(coins, amt)
        print(f"  coins={coins}, amount={amt} -> count={count}, used={used}")

    print("\nWith summary (new optional feature):")
    for coins, amt in test_cases:
        count, used, summary = min_coins(coins, amt, include_summary=True)
        print(
            f"  coins={coins}, amount={amt} -> count={count}, used={used}, "
            f"operation_summary={summary}"
        )