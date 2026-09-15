from typing import List, Tuple, Dict


def capacity_constrained_knapsack(
    items: List[Tuple[int, int]],
    capacity: int
) -> Dict[str, object]:
    """
    Solve the 0/1 Capacity-Constrained Knapsack problem.

    Parameters
    ----------
    items:
        A list of (weight, value) pairs. The position in this list is
        the item's original index.
    capacity:
        Maximum total weight allowed.

    Returns
    -------
    dict:
        {
            "max_value": int,
            "selected_indices": List[int]
        }

    Tie-breaking:
        If multiple selections have the same maximum value, the
        lexicographically smallest list of original indices is returned.

    Algorithm:
        0/1 knapsack DP with descending capacity updates.
    """

    if capacity < 0:
        raise ValueError("capacity must be non-negative")

    for i, item in enumerate(items):
        if len(item) != 2:
            raise ValueError(f"item {i} must be a (weight, value) pair")

        weight, value = item

        if not isinstance(weight, int) or not isinstance(value, int):
            raise TypeError("weights and values must be integers")

        if weight < 0:
            raise ValueError("item weights must be non-negative")

    # dp_value[c] = maximum value achievable with capacity c
    dp_value = [0] * (capacity + 1)

    # dp_indices[c] = lexicographically smallest index tuple
    # achieving dp_value[c]
    dp_indices: List[Tuple[int, ...]] = [()] * (capacity + 1)

    # Process items in original-index order.
    for index, (weight, value) in enumerate(items):

        # Descending capacity ensures every item is used at most once.
        for c in range(capacity, weight - 1, -1):
            candidate_value = dp_value[c - weight] + value
            candidate_indices = dp_indices[c - weight] + (index,)

            # Take the candidate if it has a better value.
            if candidate_value > dp_value[c]:
                dp_value[c] = candidate_value
                dp_indices[c] = candidate_indices

            # For equal values, use lexicographically smaller indices.
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
# Example
# ---------------------------------------------------------

if __name__ == "__main__":
    items = [
        (2, 3),  # index 0
        (3, 4),  # index 1
        (4, 5),  # index 2
        (5, 7),  # index 3
    ]

    capacity = 7

    result = capacity_constrained_knapsack(items, capacity)

    print(result)