from typing import List, Tuple, Dict


def capacity_constrained_knapsack(
    items: List[Tuple[int, int]],
    capacity: int
) -> Dict[str, object]:
    """
    Solve the 0/1 Capacity-Constrained Knapsack problem.

    Each item is a (weight, value) pair, and its position in `items`
    is its original index.

    Returns exactly:
        {
            "max_value": int,
            "selected_indices": List[int]
        }

    Rules:
    - Each item can be selected at most once.
    - Total weight must not exceed capacity.
    - Maximize total value.
    - For equal maximum values, choose the lexicographically
      smallest list of original indices.
    - Uses 0/1 knapsack DP with descending capacity updates.
    """

    if capacity < 0:
        raise ValueError("capacity must be non-negative")

    for index, (weight, value) in enumerate(items):
        if not isinstance(weight, int) or not isinstance(value, int):
            raise TypeError(
                f"item {index} weight and value must be integers"
            )

        if weight < 0:
            raise ValueError(
                f"item {index} weight must be non-negative"
            )

    # dp_value[c] is the best value achievable with capacity c.
    dp_value = [0] * (capacity + 1)

    # dp_indices[c] is the lexicographically smallest index tuple
    # achieving dp_value[c].
    dp_indices: List[Tuple[int, ...]] = [()] * (capacity + 1)

    for index, (weight, value) in enumerate(items):

        # IMPORTANT:
        # Descending capacity is required for 0/1 knapsack.
        #
        # If we went upward, dp[c - weight] could already contain
        # the current item, allowing the same item to be selected
        # multiple times.
        for c in range(capacity, weight - 1, -1):

            candidate_value = dp_value[c - weight] + value
            candidate_indices = dp_indices[c - weight] + (index,)

            if candidate_value > dp_value[c]:
                dp_value[c] = candidate_value
                dp_indices[c] = candidate_indices

            elif (
                candidate_value == dp_value[c]
                and candidate_indices < dp_indices[c]
            ):
                dp_indices[c] = candidate_indices

    return {
        "max_value": dp_value[capacity],
        "selected_indices": list(dp_indices[capacity]),
    }


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

if __name__ == "__main__":

    # Demonstrates the 0/1 requirement.
    # Item 0 cannot be used twice.
    items = [
        (2, 3),  # index 0
        (3, 4),  # index 1
    ]

    result = capacity_constrained_knapsack(items, 4)

    assert result == {
        "max_value": 4,
        "selected_indices": [1],
    }

    # Basic optimal selection.
    items = [
        (2, 3),  # 0
        (3, 4),  # 1
        (4, 5),  # 2
        (5, 7),  # 3
    ]

    result = capacity_constrained_knapsack(items, 7)

    assert result == {
        "max_value": 10,
        "selected_indices": [0, 3],
    }

    # Deterministic tie:
    # [0, 3] and [1, 2] both have value 10 and weight 7.
    # [0, 3] is lexicographically smaller.
    items = [
        (2, 5),  # 0
        (3, 5),  # 1
        (4, 5),  # 2
        (5, 5),  # 3
    ]

    result = capacity_constrained_knapsack(items, 7)

    assert result == {
        "max_value": 10,
        "selected_indices": [0, 3],
    }

    # Nothing fits.
    items = [
        (5, 10),
        (6, 20),
    ]

    result = capacity_constrained_knapsack(items, 4)

    assert result == {
        "max_value": 0,
        "selected_indices": [],
    }

    print("All tests passed.")