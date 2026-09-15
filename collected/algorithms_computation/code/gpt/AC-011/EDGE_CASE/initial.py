from typing import List, Tuple, Dict, Any


def knapsack(
    weights: List[int],
    values: List[int],
    capacity: int,
) -> Dict[str, Any]:
    """
    Solve the 0/1 capacity-constrained knapsack problem.

    Given indivisible items with weights and values, select a subset whose
    total weight is at most `capacity` and whose total value is maximum.

    Tie-breaking:
        If multiple selections have the same maximum value, return the
        lexicographically smallest list of original item indices.

    Returns:
        {
            "max_value": int,
            "selected_indices": List[int]
        }

    Requirements:
        - 0/1 knapsack
        - Descending capacity updates
        - Deterministic output
        - Standard library only
    """

    if len(weights) != len(values):
        raise ValueError("weights and values must have the same length")

    if capacity < 0:
        raise ValueError("capacity must be non-negative")

    if any(w < 0 for w in weights):
        raise ValueError("item weights must be non-negative")

    n = len(weights)

    # dp[c] = best (value, selected_indices) achievable with capacity <= c.
    #
    # Storing the indices allows deterministic lexicographic tie-breaking.
    dp: List[Tuple[int, List[int]]] = [
        (0, []) for _ in range(capacity + 1)
    ]

    for i in range(n):
        weight = weights[i]
        value = values[i]

        # Descending capacity update is essential for 0/1 knapsack:
        # it prevents item i from being selected more than once.
        for c in range(capacity, weight - 1, -1):
            previous_value, previous_indices = dp[c - weight]

            candidate_value = previous_value + value
            candidate_indices = previous_indices + [i]

            current_value, current_indices = dp[c]

            if candidate_value > current_value:
                dp[c] = (candidate_value, candidate_indices)
            elif candidate_value == current_value:
                if candidate_indices < current_indices:
                    dp[c] = (candidate_value, candidate_indices)

    max_value, selected_indices = dp[capacity]

    return {
        "max_value": max_value,
        "selected_indices": selected_indices,
    }


# Example
if __name__ == "__main__":
    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 6]
    capacity = 7

    result = knapsack(weights, values, capacity)
    print(result)