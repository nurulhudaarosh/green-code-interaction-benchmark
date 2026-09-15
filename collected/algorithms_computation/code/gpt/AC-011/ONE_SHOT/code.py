from typing import List, Tuple


def knapsack(items: List[Tuple[int, int]], capacity: int) -> Tuple[int, List[int]]:
    """
    Solve the 0/1 knapsack problem.

    Args:
        items: List of (weight, value) pairs. The position in this list
               is the item's original index.
        capacity: Maximum total weight allowed.

    Returns:
        (max_value, selected_indices)

        selected_indices is sorted in increasing original-index order.
        For equal-value solutions, the lexicographically smallest index
        list is returned.

    Raises:
        ValueError: If capacity or an item weight is negative.
    """
    if capacity < 0:
        raise ValueError("capacity must be non-negative")

    for weight, value in items:
        if weight < 0:
            raise ValueError("item weights must be non-negative")

    # dp[c] = (best_value, selected_indices)
    #
    # Initially, selecting nothing is possible for every capacity.
    dp = [(0, []) for _ in range(capacity + 1)]

    for index, (weight, value) in enumerate(items):
        # Descending capacity is essential for 0/1 knapsack:
        # it prevents the current item from being selected more than once.
        for c in range(capacity, weight - 1, -1):
            previous_value, previous_indices = dp[c - weight]
            candidate_value = previous_value + value
            candidate_indices = previous_indices + [index]

            current_value, current_indices = dp[c]

            if candidate_value > current_value:
                dp[c] = (candidate_value, candidate_indices)
            elif candidate_value == current_value:
                if candidate_indices < current_indices:
                    dp[c] = (candidate_value, candidate_indices)

    return dp[capacity]


# -------------------- Tests --------------------

def _run_tests() -> None:
    # Basic case
    assert knapsack(
        [(2, 3), (3, 4), (4, 5)],
        5
    ) == (7, [0, 1])

    # Nothing fits
    assert knapsack(
        [(5, 10), (6, 20)],
        3
    ) == (0, [])

    # Capacity zero
    assert knapsack(
        [(1, 10), (2, 20)],
        0
    ) == (0, [])

    # Repeated values/weights.
    # [0, 1] and [2, 3] both have weight 4 and value 10;
    # [0, 1] is lexicographically smaller.
    assert knapsack(
        [(2, 5), (2, 5), (2, 5), (2, 5)],
        4
    ) == (10, [0, 1])

    # Deterministic tie: selecting item 0 alone has the same
    # value as selecting item 1 alone, so [0] must win.
    assert knapsack(
        [(2, 10), (2, 10)],
        2
    ) == (10, [0])

    # A combination ties with another combination.
    # [0, 2] and [1, 2] have equal weight/value;
    # [0, 2] is lexicographically smaller.
    assert knapsack(
        [(2, 5), (2, 5), (1, 5)],
        3
    ) == (10, [0, 2])

    # Empty item list
    assert knapsack([], 10) == (0, [])

    # An item with zero weight can be selected.
    assert knapsack(
        [(0, 7), (2, 3)],
        2
    ) == (10, [0, 1])

    # Negative capacity is invalid.
    try:
        knapsack([(1, 1)], -1)
        assert False, "Expected ValueError"
    except ValueError:
        pass

    print("All tests passed.")


if __name__ == "__main__":
    _run_tests()