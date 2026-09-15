from typing import List, Tuple


def knapsack(
    weights: List[int],
    values: List[int],
    capacity: int
) -> List[int]:
    """
    Solve the 0/1 knapsack problem.

    Args:
        weights: Weight of each item.
        values: Value of each item.
        capacity: Maximum allowed total weight.

    Returns:
        A list of original item indices, sorted increasingly.

        The returned solution:
        1. Has maximum total value.
        2. Among equal-value solutions, has the
           lexicographically smallest index list.

    Raises:
        ValueError: If input lengths do not match or if any
                    weight/capacity is negative.
    """

    if len(weights) != len(values):
        raise ValueError("weights and values must have the same length")

    if capacity < 0:
        raise ValueError("capacity must be non-negative")

    if any(weight < 0 for weight in weights):
        raise ValueError("item weights must be non-negative")

    n = len(weights)

    # dp[c] = (best_value, selected_indices)
    #
    # Initially, selecting nothing gives value 0 and [].
    dp: List[Tuple[int, List[int]]] = [
        (0, []) for _ in range(capacity + 1)
    ]

    for i in range(n):
        weight = weights[i]
        value = values[i]

        # Descending capacity is required for 0/1 knapsack.
        for c in range(capacity, weight - 1, -1):
            previous_value, previous_indices = dp[c - weight]

            candidate_value = previous_value + value
            candidate_indices = previous_indices + [i]

            current_value, current_indices = dp[c]

            # Prefer larger value.
            if candidate_value > current_value:
                dp[c] = (candidate_value, candidate_indices)

            # For equal value, prefer lexicographically
            # smaller list of original indices.
            elif (
                candidate_value == current_value
                and candidate_indices < current_indices
            ):
                dp[c] = (candidate_value, candidate_indices)

    return dp[capacity][1]


if __name__ == "__main__":
    # Example
    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 7]
    capacity = 7

    result = knapsack(weights, values, capacity)
    print(result)