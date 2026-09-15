"""
Deterministic minimum-coin-change solver.

Given a list of coin denominations and a target amount, finds a combination
of coins (with unlimited reuse of each denomination) that sums exactly to
the target using the minimum number of coins.

Uses a 1-D unbounded coin-change DP with deterministic reconstruction:
  - denominations are deduplicated and sorted ascending before the DP runs,
    so that whenever two coins would yield the same minimal count, the
    smaller denomination is always the one recorded (strict '<' comparison
    plus fixed iteration order => same result every run).

No network access, external services, randomness, or human interaction
are used; only the Python standard library.
"""

from __future__ import annotations

from typing import List, Tuple

INF = float("inf")


def min_coins(coins: List[int], amount: int) -> Tuple[int, List[int]]:
    """
    Compute the minimum number of coins (with unlimited reuse) that sum
    exactly to `amount`.

    Parameters
    ----------
    coins : list of int
        Coin denominations. Must be positive integers; duplicates and
        unsorted order are tolerated (they are normalized internally).
    amount : int
        Non-negative target amount.

    Returns
    -------
    (count, combination) : (int, list of int)
        `count` is the minimum number of coins needed and `combination`
        is one concrete list of coins (length == count) summing to
        `amount`. If it is impossible to make `amount` exactly, returns
        (-1, []).

    Raises
    ------
    ValueError
        If `amount` is negative, or if `coins` contains no positive
        denomination while `amount > 0`.
    TypeError
        If `coins` or `amount` are not of the expected types.
    """
    # ---- Input validation -------------------------------------------------
    if not isinstance(amount, int) or isinstance(amount, bool):
        raise TypeError("amount must be an int")
    if amount < 0:
        raise ValueError("amount must be non-negative")

    if not isinstance(coins, (list, tuple)):
        raise TypeError("coins must be a list (or tuple) of ints")

    # Normalize: keep only positive ints, dedupe, sort ascending for
    # deterministic tie-breaking during reconstruction.
    normalized = sorted({c for c in coins if isinstance(c, int) and not isinstance(c, bool) and c > 0})

    # ---- Trivial case -------------------------------------------------
    if amount == 0:
        return 0, []

    if not normalized:
        # No usable denominations and amount > 0 => impossible.
        return -1, []

    # ---- DP setup -------------------------------------------------
    # dp[i]     = minimum number of coins to make amount i
    # choice[i] = coin denomination used for the last step reaching i
    dp = [INF] * (amount + 1)
    choice = [0] * (amount + 1)
    dp[0] = 0

    for i in range(1, amount + 1):
        for c in normalized:              # fixed ascending order => deterministic
            if c > i:
                break                      # coins sorted ascending; no larger coin fits
            candidate = dp[i - c] + 1
            if candidate < dp[i]:          # strict '<' keeps the first (smallest) winner
                dp[i] = candidate
                choice[i] = c

    if dp[amount] == INF:
        return -1, []

    # ---- Reconstruction -------------------------------------------------
    result: List[int] = []
    remaining = amount
    while remaining > 0:
        c = choice[remaining]
        result.append(c)
        remaining -= c

    # Sorted for a stable, readable, deterministic output list.
    result.sort()
    return len(result), result


def _self_test() -> None:
    """A few sanity checks demonstrating deterministic behavior."""
    cases = [
        ([1, 2, 5], 11, 3),      # 5+5+1
        ([2], 3, -1),            # impossible
        ([1], 0, 0),             # trivial zero amount
        ([186, 419, 83, 408], 6249, 20),
        ([1, 5, 10, 25], 63, 6), # 25+25+10+1+1+1
    ]
    for coins, amount, expected_count in cases:
        count, combo = min_coins(coins, amount)
        assert count == expected_count, f"{coins}, {amount}: got {count}, expected {expected_count}"
        if count != -1:
            assert sum(combo) == amount, "combination does not sum to amount"
            assert len(combo) == count, "combination length mismatch"
        print(f"coins={coins}, amount={amount} -> count={count}, combo={combo}")

    # Determinism check: same input, run twice, identical output list.
    r1 = min_coins([1, 5, 10, 25], 63)
    r2 = min_coins([25, 10, 5, 1], 63)  # different input order
    assert r1 == r2, "result should be deterministic regardless of input coin order"
    print("Determinism check passed:", r1)


if __name__ == "__main__":
    _self_test()