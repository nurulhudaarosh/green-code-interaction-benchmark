from typing import List, Tuple


def knapsack(
    weights: List[int],
    values: List[int],
    capacity: int
) -> List[int]:
    """
    Solve the Capacity-Constrained 0/1 Knapsack problem.

    Rules:
    1. Each item can be selected at most once.
    2. Total weight must not exceed capacity.
    3. Maximize total value.
    4. If multiple solutions have the same value,
       return the lexicographically smallest list
       of original item indices.
    5. Uses 0/1 knapsack DP with descending capacity updates.

    Returns:
        List[int]: selected original indices in increasing order.
    """

    # Input validation
    if len(weights) != len(values):
        raise ValueError("weights and values must have the same length")

    if capacity < 0:
        raise ValueError("capacity must be non-negative")

    if any(w < 0 for w in weights):
        raise ValueError("weights must be non-negative")

    # dp[c] = (maximum_value, selected_indices)
    dp: List[Tuple[int, List[int]]] = [
        (0, []) for _ in range(capacity + 1)
    ]

    # Process each item exactly once.
    for i, (weight, value) in enumerate(zip(weights, values)):

        # Descending capacity update is required for 0/1 knapsack.
        for c in range(capacity, weight - 1, -1):

            current_value, current_indices = dp[c]

            previous_value, previous_indices = dp[c - weight]

            # Try selecting the current item.
            candidate_value = previous_value + value
            candidate_indices = previous_indices + [i]

            # Primary rule: maximize value.
            if candidate_value > current_value:
                dp[c] = (candidate_value, candidate_indices)

            # Secondary rule: lexicographically smallest indices.
            elif (
                candidate_value == current_value
                and candidate_indices < current_indices
            ):
                dp[c] = (candidate_value, candidate_indices)

    return dp[capacity][1]


# ============================================================
# TESTS
# ============================================================

def test_basic_case():
    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 7]
    capacity = 7

    assert knapsack(weights, values, capacity) == [0, 3]


def test_lexicographic_tie():
    """
    Items 0 and 1 both have value 5 and weight 1.

    Both [0] and [1] are optimal.
    Lexicographically smallest is [0].
    """
    weights = [1, 1]
    values = [5, 5]
    capacity = 1

    assert knapsack(weights, values, capacity) == [0]


def test_multiple_equal_solutions():
    """
    Every pair has the same value.
    The lexicographically smallest pair is [0, 1].
    """
    weights = [1, 1, 1]
    values = [4, 4, 4]
    capacity = 2

    assert knapsack(weights, values, capacity) == [0, 1]


def test_item_cannot_be_reused():
    """
    There is only one item. Even though capacity is large
    enough to hold it multiple times, it can only be used once.
    """
    weights = [2]
    values = [10]
    capacity = 4

    assert knapsack(weights, values, capacity) == [0]


def test_empty_input():
    assert knapsack([], [], 10) == []


def test_zero_capacity():
    weights = [1, 2, 3]
    values = [10, 20, 30]
    capacity = 0

    assert knapsack(weights, values, capacity) == []


def test_item_too_heavy():
    weights = [5, 6, 7]
    values = [10, 20, 30]
    capacity = 2

    assert knapsack(weights, values, capacity) == []


def test_better_value_beats_lexicographic_order():
    """
    [0] has value 5.
    [1] has value 10.

    Higher value must win even though [0] is
    lexicographically smaller.
    """
    weights = [2, 2]
    values = [5, 10]
    capacity = 2

    assert knapsack(weights, values, capacity) == [1]


def test_equal_value_different_number_of_items():
    """
    [0] has value 10.
    [1, 2] also has value 10.

    Compare lists lexicographically:
        [0] < [1, 2]

    Therefore [0] must be selected.
    """
    weights = [2, 1, 1]
    values = [10, 5, 5]
    capacity = 2

    assert knapsack(weights, values, capacity) == [0]


def test_input_validation():
    try:
        knapsack([1, 2], [10], 3)
        assert False
    except ValueError:
        pass

    try:
        knapsack([1, -2], [10, 20], 3)
        assert False
    except ValueError:
        pass

    try:
        knapsack([1, 2], [10, 20], -1)
        assert False
    except ValueError:
        pass


# ============================================================
# RUN ALL TESTS
# ============================================================

def run_tests():
    test_basic_case()
    test_lexicographic_tie()
    test_multiple_equal_solutions()
    test_item_cannot_be_reused()
    test_empty_input()
    test_zero_capacity()
    test_item_too_heavy()
    test_better_value_beats_lexicographic_order()
    test_equal_value_different_number_of_items()
    test_input_validation()

    print("All tests passed!")


if __name__ == "__main__":
    run_tests()