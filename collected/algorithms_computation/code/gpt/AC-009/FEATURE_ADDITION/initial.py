from typing import List, Tuple


def minimum_coin_change(
    coins: List[int],
    target: int
) -> Tuple[int, List[int]]:
    """
    Minimum Coin Construction.

    Returns:
        (minimum_coin_count, combination)

    Rules:
    - Coins may be reused unlimited times.
    - If impossible, return (-1, []).
    - target == 0 returns (0, []).
    - Uses one-dimensional unbounded coin-change DP.
    - Reconstruction is deterministic.
    - Among minimum-count constructions, the lexicographically
      smallest ascending combination is returned.
    """

    if target < 0:
        raise ValueError("target must be non-negative")

    # Remove invalid/non-positive denominations and duplicates.
    coins = sorted(set(coin for coin in coins if coin > 0))

    if target == 0:
        return 0, []

    if not coins:
        return -1, []

    INF = target + 1

    # dp[amount] = minimum number of coins needed to form amount.
    dp = [INF] * (target + 1)
    dp[0] = 0

    # One-dimensional unbounded coin-change DP.
    for amount in range(1, target + 1):
        for coin in coins:
            if coin > amount:
                break

            if dp[amount - coin] != INF:
                dp[amount] = min(
                    dp[amount],
                    dp[amount - coin] + 1
                )

    # Impossible to construct target.
    if dp[target] == INF:
        return -1, []

    # ---------------------------------------------------------
    # Deterministic reconstruction
    # ---------------------------------------------------------
    #
    # At every step, choose the smallest denomination that:
    #   1. fits in the remaining amount, and
    #   2. can still produce an optimal number of coins.
    #
    # Because we always choose the smallest valid denomination,
    # the resulting combination is deterministic and ascending.
    # ---------------------------------------------------------

    combination = []
    remaining = target
    remaining_coins = dp[target]

    while remaining > 0:
        selected = None

        for coin in coins:
            if coin > remaining:
                break

            # The coin must preserve an optimal solution.
            if (
                dp[remaining - coin] != INF
                and dp[remaining - coin] + 1 == remaining_coins
            ):
                selected = coin
                break

        # Defensive check; this should never happen.
        if selected is None:
            return -1, []

        combination.append(selected)
        remaining -= selected
        remaining_coins -= 1

    return dp[target], combination


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def run_tests() -> None:

    # Basic example
    assert minimum_coin_change([1, 2, 5], 11) == (
        3,
        [1, 5, 5]
    )

    # Impossible
    assert minimum_coin_change([2], 3) == (
        -1,
        []
    )

    # Target zero
    assert minimum_coin_change([1, 2, 5], 0) == (
        0,
        []
    )

    # Coin reuse
    assert minimum_coin_change([3], 9) == (
        3,
        [3, 3, 3]
    )

    # Multiple minimum-count constructions:
    # 6 can be:
    #   2 + 4
    #   3 + 3
    #
    # Both use 2 coins.
    # Deterministic rule chooses the lexicographically
    # smallest ascending combination: [2, 4].
    assert minimum_coin_change([2, 3, 4], 6) == (
        2,
        [2, 4]
    )

    # The original reconstruction could produce [5, 1].
    # Canonical deterministic reconstruction returns [1, 5].
    assert minimum_coin_change([1, 5], 6) == (
        2,
        [1, 5]
    )

    # Unsorted input must not affect the result.
    assert minimum_coin_change([5, 1, 2], 11) == (
        3,
        [1, 5, 5]
    )

    # Duplicate denominations must not affect the result.
    assert minimum_coin_change([5, 2, 5, 1, 2], 10) == (
        2,
        [5, 5]
    )

    # Another tie:
    # 8 -> [2, 6] or [3, 5], both use 2 coins.
    assert minimum_coin_change([2, 3, 5, 6], 8) == (
        2,
        [2, 6]
    )

    # No usable coins.
    assert minimum_coin_change([0, -1, -5], 10) == (
        -1,
        []
    )

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()