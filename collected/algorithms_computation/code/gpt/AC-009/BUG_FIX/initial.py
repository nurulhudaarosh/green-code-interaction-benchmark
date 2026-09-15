from typing import List, Tuple


def minimum_coin_change(
    coins: List[int],
    target: int
) -> Tuple[int, List[int]]:
    """
    Find a minimum-number coin combination for the given target.

    Coins may be reused unlimited times.

    Returns:
        (count, combination)

        If impossible:
            (-1, [])

    Deterministic tie-breaking:
        Among choices producing the same minimum number of coins,
        choose the smaller denomination.
    """

    # Basic validation
    if target < 0:
        raise ValueError("target must be non-negative")

    # Keep only positive, unique denominations.
    # Sorting gives deterministic iteration/tie-breaking.
    coins = sorted(set(coin for coin in coins if coin > 0))

    # Target 0 requires zero coins.
    if target == 0:
        return 0, []

    if not coins:
        return -1, []

    INF = target + 1

    # dp[amount] = minimum number of coins needed
    dp = [INF] * (target + 1)

    # choice[amount] = coin used to reach the optimal solution
    choice = [None] * (target + 1)

    dp[0] = 0

    # Unbounded coin-change DP
    for amount in range(1, target + 1):
        for coin in coins:
            if coin > amount:
                break

            previous = dp[amount - coin]

            if previous == INF:
                continue

            candidate = previous + 1

            # Strictly better solution
            if candidate < dp[amount]:
                dp[amount] = candidate
                choice[amount] = coin

            # Equal solution:
            # coins are processed in ascending order, so the first
            # choice is already the smaller denomination.
            elif candidate == dp[amount]:
                if choice[amount] is None or coin < choice[amount]:
                    choice[amount] = coin

    # Target cannot be formed
    if dp[target] == INF:
        return -1, []

    # Deterministic reconstruction
    combination = []
    amount = target

    while amount > 0:
        coin = choice[amount]

        # Defensive check; should never happen for a reachable target.
        if coin is None:
            return -1, []

        combination.append(coin)
        amount -= coin

    return dp[target], combination


# -------------------------
# Tests
# -------------------------

def run_tests() -> None:
    # Standard case
    count, combination = minimum_coin_change([1, 2, 5], 11)
    assert count == 3
    assert combination == [5, 5, 1]

    # Impossible target
    count, combination = minimum_coin_change([2], 3)
    assert count == -1
    assert combination == []

    # Target zero
    count, combination = minimum_coin_change([1, 2, 5], 0)
    assert count == 0
    assert combination == []

    # Coin reuse
    count, combination = minimum_coin_change([3], 9)
    assert count == 3
    assert combination == [3, 3, 3]

    # Deterministic tie:
    # 6 = 3 + 3 or 2 + 2 + 2.
    # Minimum is 3 + 3.
    count, combination = minimum_coin_change([2, 3], 6)
    assert count == 2
    assert combination == [3, 3]

    # Duplicate denominations
    count, combination = minimum_coin_change([1, 2, 2, 5], 10)
    assert count == 2
    assert combination == [5, 5]

    # Unsorted input
    count, combination = minimum_coin_change([7, 1, 3], 14)
    assert count == 2
    assert combination == [7, 7]

    # No positive usable coins
    count, combination = minimum_coin_change([0, -1, -5], 10)
    assert count == -1
    assert combination == []

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()

    # Example usage
    count, combination = minimum_coin_change([1, 2, 5], 11)
    print("Minimum count:", count)
    print("Combination:", combination)