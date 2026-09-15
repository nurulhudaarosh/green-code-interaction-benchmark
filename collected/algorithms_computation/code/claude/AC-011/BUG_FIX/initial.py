"""
Deterministic 0/1 Knapsack solver.

Given a list of (weight, value) items (0-indexed by their original position)
and an integer capacity, find a subset of items with total weight <= capacity
that maximizes total value. Among all subsets achieving the maximum value,
return the one whose sorted list of original indices is lexicographically
smallest.

Standard library only. No randomness, no I/O, no network/API/human interaction.
"""

from typing import List, Sequence, Tuple


def solve_knapsack(
    items: Sequence[Tuple[int, float]], capacity: int
) -> Tuple[float, List[int]]:
    """
    Solve the 0/1 knapsack problem.

    Args:
        items: sequence of (weight, value) pairs. The position of each pair
                in this sequence IS its original index (0-based).
        capacity: non-negative integer knapsack capacity.

    Returns:
        (max_value, selected_indices)
        - max_value: the maximum total value achievable.
        - selected_indices: sorted list of original indices of chosen items;
          among all optimal-value subsets, this is the lexicographically
          smallest such list.

    Raises:
        ValueError: on invalid input (negative capacity/weight, non-integer
                    weight/capacity, etc.)
    """
    if not isinstance(capacity, int) or capacity < 0:
        raise ValueError("capacity must be a non-negative integer")

    n = len(items)
    weights: List[int] = []
    values: List[float] = []
    for idx, (w, v) in enumerate(items):
        if not isinstance(w, int) or w < 0:
            raise ValueError(f"item {idx}: weight must be a non-negative integer")
        weights.append(w)
        values.append(v)

    # dp[i][c] = max value achievable using items[i:] with capacity c
    # (suffix DP; each item's contribution is added at most once per row,
    # mirroring the 0/1 guarantee of the descending-capacity 1D update).
    dp = [[0.0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(n - 1, -1, -1):
        w, v = weights[i], values[i]
        row_next = dp[i + 1]
        row_cur = dp[i]
        # Capacity considered in descending order: for a 0/1 item this order
        # is not strictly required in the suffix formulation (rows are
        # independent), but it mirrors the classic in-place update pattern
        # and keeps behavior consistent/deterministic.
        for c in range(capacity, -1, -1):
            best = row_next[c]
            if w <= c:
                candidate = v + row_next[c - w]
                if candidate > best:
                    best = candidate
            row_cur[c] = best

    max_value = dp[0][capacity]

    # Reconstruct the lexicographically smallest optimal index set:
    # greedily include the smallest-index item whenever doing so still
    # permits reaching the known optimum for the remaining sub-problem.
    selected: List[int] = []
    c = capacity
    for i in range(n):
        w, v = weights[i], values[i]
        if w <= c and abs((v + dp[i + 1][c - w]) - dp[i][c]) < 1e-9:
            selected.append(i)
            c -= w

    return max_value, selected


if __name__ == "__main__":
    # Deterministic example / self-test
    # items[i] = (weight, value), index i is the "original index"
    example_items = [
        (2, 3),   # index 0
        (3, 4),   # index 1
        (4, 5),   # index 2
        (5, 6),   # index 3
    ]
    cap = 5

    value, chosen = solve_knapsack(example_items, cap)
    print(f"Max value: {value}")
    print(f"Selected original indices (lexicographically smallest): {chosen}")

    # Tie-breaking example: two items with identical weight/value ratio
    # such that multiple subsets tie for the max value.
    tie_items = [
        (1, 1),  # index 0
        (1, 1),  # index 1
        (2, 2),  # index 2
    ]
    tie_cap = 2
    value2, chosen2 = solve_knapsack(tie_items, tie_cap)
    print(f"Max value: {value2}")
    print(f"Selected original indices (lexicographically smallest): {chosen2}")
    # Expect [0, 1] (lexicographically smaller than [2]) since both give value 2.