from typing import List, Tuple


def min_coin_change(coins: List[int], target: int) -> Tuple[int, List[int]]:
    """
    Find a minimum-number coin combination for the given target.

    Coins can be reused unlimited times.

    Returns:
        (count, combination)

        If impossible:
            (-1, [])

    Deterministic tie-breaking:
        Among equally optimal choices for an amount, prefer the
        smaller denomination.
    """
    if target < 0:
        return -1, []

    # Keep only positive, unique denominations.
    # Sorting gives deterministic tie-breaking.
    denominations = sorted(set(c for c in coins if c > 0))

    if target == 0:
        return 0, []

    if not denominations:
        return -1, []

    INF = target + 1

    # dp[amount] = minimum number of coins needed.
    dp = [INF] * (target + 1)

    # choice[amount] = coin selected for the optimal solution.
    choice = [-1] * (target + 1)

    dp[0] = 0

    # Unbounded coin-change DP.
    for amount in range(1, target + 1):
        for coin in denominations:
            if coin > amount:
                break

            previous = dp[amount - coin]

            if previous == INF:
                continue

            candidate = previous + 1

            # Strictly better only.
            # Because denominations are sorted, equal candidates
            # retain the smaller denomination already considered.
            if candidate < dp[amount]:
                dp[amount] = candidate
                choice[amount] = coin

    # Target cannot be formed.
    if dp[target] == INF:
        return -1, []

    # Deterministic reconstruction.
    result = []
    amount = target

    while amount > 0:
        coin = choice[amount]

        # Defensive check; should never happen for a reachable target.
        if coin == -1:
            return -1, []

        result.append(coin)
        amount -= coin

    return dp[target], result


# -------------------------
# Tests
# -------------------------

def run_tests() -> None:
    # Standard case:
    # 11 = 5 + 5 + 1 -> 3 coins
    assert min_coin_change([1, 2, 5], 11) == (3, [1, 5, 5])

    # Impossible target.
    assert min_coin_change([2, 4], 7) == (-1, [])

    # Target zero.
    assert min_coin_change([1, 2, 5], 0) == (0, [])

    # Single denomination.
    assert min_coin_change([3], 9) == (3, [3, 3, 3])

    # Duplicate denominations do not change the answer.
    assert min_coin_change([1, 2, 2, 5], 6) == (2, [1, 5])

    # Deterministic tie:
    # 4 can be made with [1, 3] or [2, 2].
    # Smaller denomination is preferred at amount 4,
    # producing [1, 3].
    assert min_coin_change([1, 2, 3], 4) == (2, [1, 3])

    # Another tie:
    # 6 can be [1, 5] or [3, 3].
    # At amount 6, coin 1 is selected because it is the
    # smaller denomination among equally optimal candidates.
    assert min_coin_change([1, 3, 5], 6) == (2, [1, 5])

    # Unsorted input must still give deterministic output.
    assert min_coin_change([5, 1, 3], 4) == (2, [1, 3])

    # No usable coins.
    assert min_coin_change([], 10) == (-1, [])

    # Non-positive denominations are ignored.
    assert min_coin_change([0, -2, 2], 6) == (3, [2, 2, 2])

    # Exact coin.
    assert min_coin_change([2, 5, 10], 10) == (1, [10])

    # A larger reusable-coin case.
    count, combination = min_coin_change([1, 7, 10], 14)
    assert count == 2
    assert sum(combination) == 14
    assert len(combination) == count

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()