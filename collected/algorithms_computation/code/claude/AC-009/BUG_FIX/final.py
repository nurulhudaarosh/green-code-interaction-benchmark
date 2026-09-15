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
  - the returned combination is exactly the path walked during
    reconstruction (largest-remaining-amount first), NOT re-sorted
    afterward, since re-sorting would not faithfully represent the
    deterministic reconstruction the DP actually performed.

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

    Returns
    -------
    (count, combination) : (int, list of int)
        `count` is the minimum number of coins needed and `combination`
        is the exact deterministic reconstruction (in the order coins
        were applied while walking back from `amount` to `0`), summing
        to `amount` with length `count`. If impossible, returns (-1, []).
    """
    if not isinstance(amount, int) or isinstance(amount, bool):
        raise TypeError("amount must be an int")
    if amount < 0:
        raise ValueError("amount must be non-negative")

    if not isinstance(coins, (list, tuple)):
        raise TypeError("coins must be a list (or tuple) of ints")

    normalized = sorted({c for c in coins if isinstance(c, int) and not isinstance(c, bool) and c > 0})

    if amount == 0:
        return 0, []

    if not normalized:
        return -1, []

    dp = [INF] * (amount + 1)
    choice = [0] * (amount + 1)
    dp[0] = 0

    for i in range(1, amount + 1):
        for c in normalized:
            if c > i:
                break
            candidate = dp[i - c] + 1
            if candidate < dp[i]:
                dp[i] = candidate
                choice[i] = c

    if dp[amount] == INF:
        return -1, []

    result: List[int] = []
    remaining = amount
    while remaining > 0:
        c = choice[remaining]
        result.append(c)
        remaining -= c

    # NOTE: no re-sort here — this is exactly the deterministic
    # reconstruction path the DP walked, which is what "deterministic
    # reconstruction" requires callers to be able to rely on.
    return len(result), result


def _self_test() -> None:
    cases = [
        ([1, 2, 5], 11, 3, [5, 5, 1]),
        ([2], 3, -1, []),
        ([1], 0, 0, []),
        ([1, 3, 4], 6, 2, [3, 3]),
        ([1, 5, 10, 25], 63, 6, [25, 25, 10, 1, 1, 1]),
    ]
    for coins, amount, expected_count, expected_combo in cases:
        count, combo = min_coins(coins, amount)
        assert count == expected_count, f"{coins}, {amount}: got {count}, expected {expected_count}"
        assert combo == expected_combo, f"{coins}, {amount}: got {combo}, expected {expected_combo}"
        if count != -1:
            assert sum(combo) == amount
            assert len(combo) == count
        print(f"coins={coins}, amount={amount} -> count={count}, combo={combo}")

    r1 = min_coins([1, 5, 10, 25], 63)
    r2 = min_coins([25, 10, 5, 1], 63)
    assert r1 == r2, "result should be deterministic regardless of input coin order"
    print("Determinism check passed:", r1)


if __name__ == "__main__":
    _self_test()