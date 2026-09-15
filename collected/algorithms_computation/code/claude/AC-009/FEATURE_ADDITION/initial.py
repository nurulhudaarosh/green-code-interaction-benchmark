"""
Problem
-------
Given a list of coin denominations and a target amount, find a combination
of coins (each denomination may be reused any number of times) that sums
exactly to the target using the MINIMUM number of coins.

If the target cannot be formed with the given coins, return (-1, []).

Key constraints
---------------
- Coins may be reused an unlimited number of times (unbounded knapsack style).
- Denominations are positive integers; amount is a non-negative integer.
- Must be deterministic: given the same input, always return the same
  count and the same list of coins (ties broken in a fixed, reproducible way).
- No network access, APIs, external services, randomness, or human
  interaction — pure standard-library computation only.

Required output
----------------
A tuple: (min_count, coins_used)
  - min_count: minimum number of coins needed, or -1 if impossible.
  - coins_used: a list of the actual coins summing to `amount`
                (length == min_count), or [] if impossible.

Algorithm
---------
Classic 1-D unbounded coin-change DP:
  dp[a] = minimum number of coins to make amount `a`
  dp[0] = 0 ; dp[a] = min(dp[a - c] + 1) over all coins c <= a

Alongside dp, we keep choice[a] = the coin used to arrive at the optimal
dp[a] (the last coin added). To guarantee determinism (a fixed, repeatable
answer even when multiple coin combos give the same minimal count), we:
  1. Sort and de-duplicate the coin list once, up front.
  2. When scanning coins for a given amount, always iterate in that fixed
     sorted order and only overwrite choice[a] on a STRICT improvement
     (dp[a-c] + 1 < dp[a]), never on ties — so the first coin (in sorted
     order) that achieves the minimum is always kept.
  3. Reconstruct the coin list by walking choice[] from `amount` down to 0.

Complexity: O(amount * len(coins)) time, O(amount) space.
"""

from typing import List, Tuple


def min_coins(coins: List[int], amount: int) -> Tuple[int, List[int]]:
    # --- Validate / normalize input ---
    if amount < 0:
        raise ValueError("amount must be non-negative")

    # Keep only positive integer denominations; sort + de-duplicate for determinism.
    clean_coins = sorted({c for c in coins if isinstance(c, int) and c > 0})

    if amount == 0:
        return 0, []

    if not clean_coins:
        return -1, []

    INF = float("inf")
    dp = [INF] * (amount + 1)
    dp[0] = 0
    choice = [None] * (amount + 1)  # choice[a] = coin used for optimal dp[a]

    for a in range(1, amount + 1):
        for c in clean_coins:          # fixed, sorted order -> deterministic
            if c > a:
                break                  # sorted, so no smaller coin left to try
            if dp[a - c] + 1 < dp[a]:  # strict improvement only (no tie overwrite)
                dp[a] = dp[a - c] + 1
                choice[a] = c

    if dp[amount] == INF:
        return -1, []

    # --- Reconstruct the coin combination ---
    result = []
    remaining = amount
    while remaining > 0:
        c = choice[remaining]
        result.append(c)
        remaining -= c

    result.sort()  # deterministic presentation order
    return dp[amount], result


if __name__ == "__main__":
    test_cases = [
        ([1, 2, 5], 11),
        ([2], 3),
        ([1], 0),
        ([186, 419, 83, 408], 6249),
        ([3, 7], 5),
    ]

    for coins, amt in test_cases:
        count, used = min_coins(coins, amt)
        print(f"coins={coins}, amount={amt} -> count={count}, used={used}")