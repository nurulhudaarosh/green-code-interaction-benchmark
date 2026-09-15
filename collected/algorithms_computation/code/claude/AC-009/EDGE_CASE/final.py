"""
=====================================================================
PROBLEM RESTATEMENT — Minimum Coin Construction
=====================================================================
Given:
    - coins:  a collection of coin denominations (positive integers,
              each denomination available in unlimited supply / reusable).
    - amount: a non-negative integer target sum.

Find:
    - A multiset of coins, drawn from `coins` with repetition allowed,
      whose values sum EXACTLY to `amount`, using the FEWEST coins
      possible.

Output:
    - (min_count, coin_list) where coin_list sums to `amount` and has
      length min_count.
    - If no combination of the given coins can reach `amount` exactly,
      return (-1, []) — the amount is "unreachable" from the coin set.
    - amount == 0 is always reachable trivially, with 0 coins: (0, []).

This version explicitly handles boundary / difficult cases:
    - Smallest permitted input: amount == 0 (any coin set, including
      empty), and a single coin whose value equals amount exactly.
    - Empty / disconnected structures: an empty coins list (no way to
      construct anything except amount == 0), and coin sets that are
      "disconnected" from the target — i.e. no combination of the
      given denominations can ever land exactly on `amount` (e.g. all
      coins even, target odd; or every coin larger than the target).

Determinism (unchanged from original):
    - Coins are de-duplicated and sorted ascending before the DP runs.
    - The DP scans coins in that fixed ascending order and only updates
      dp[i] on a STRICT improvement (dp[i-c] + 1 < dp[i]), so the first
      (smallest) denomination that achieves the best count for a given
      amount is always the one recorded. Re-running with the same input
      always reconstructs the same coin list, not just the same count.

No network access, no randomness, no external dependencies, no I/O
beyond what the caller explicitly triggers via __main__.
=====================================================================
"""

from typing import List, Tuple

INF = float("inf")


def min_coins(coins: List[int], amount: int) -> Tuple[int, List[int]]:
    """
    Compute the minimum number of coins (with reuse allowed) that sum
    exactly to `amount`.

    Args:
        coins: list of positive integer denominations. Non-positive or
               duplicate values are ignored/de-duplicated. May be empty.
        amount: non-negative integer target.

    Returns:
        (min_count, coin_list)
            - coin_list sums to `amount` and has length `min_count`.
            - If `amount` cannot be formed exactly (including when
              `coins` is empty and amount > 0, or when the coin set is
              "disconnected" from the target), returns (-1, []).
            - If `amount == 0`, returns (0, []), regardless of `coins`
              (including an empty coins list) — this is the smallest
              permitted input case.

    Raises:
        ValueError: if amount is negative.
    """
    if amount < 0:
        raise ValueError("amount must be non-negative")

    # Sanitize: keep only positive, unique denominations, sorted ascending
    # for deterministic tie-breaking.
    unique_coins = sorted({c for c in coins if isinstance(c, int) and c > 0})

    # Smallest permitted input: amount == 0 is always trivially reachable,
    # even with an empty or otherwise unusable coin set.
    if amount == 0:
        return 0, []

    # Empty / disconnected structure: no coins available at all, but a
    # positive amount is requested -> unreachable.
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

    # Disconnected structure: target amount is unreachable with this coin
    # set (e.g. all coins even and amount odd, or every coin > amount).
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
    """Deterministic sanity checks, including boundary/edge cases."""
    cases = [
        # --- Original core cases -----------------------------------
        (([1, 2, 5], 11), (3, [1, 5, 5])),
        (([2], 3), (-1, [])),
        (([1], 0), (0, [])),
        (([186, 419, 83, 408], 6249), (20, None)),  # count known; list not hand-verified

        # --- Smallest permitted input --------------------------------
        (([], 0), (0, [])),                # smallest possible: no coins, zero target
        (([1, 2, 5], 0), (0, [])),          # amount == 0 with a normal coin set
        (([5], 5), (1, [5])),               # single coin exactly equal to amount
        (([5], 0), (0, [])),                # single coin, zero amount

        # --- Empty / disconnected structures --------------------------
        (([], 7), (-1, [])),                # empty coin set, positive amount -> unreachable
        (([4, 6], 7), (-1, [])),            # all-even coins, odd target -> disconnected
        (([10], 3), (-1, [])),              # only coin bigger than target -> disconnected
        (([3, 3, 3], 9), (3, [3, 3, 3])),   # duplicate denominations collapse to one
        (([-2, 0, 3], 6), (2, [3, 3])),     # non-positive values filtered out first
    ]
    for (coins, amount), (expected_count, expected_list) in cases:
        count, lst = min_coins(coins, amount)
        assert count == expected_count, (
            f"count mismatch for coins={coins}, amount={amount}: "
            f"expected {expected_count}, got {count}"
        )
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

    demo_coins3 = []
    demo_amount3 = 0
    count3, coin_list3 = min_coins(demo_coins3, demo_amount3)
    print(f"coins={demo_coins3}, amount={demo_amount3} -> count={count3}, coins used={coin_list3}")