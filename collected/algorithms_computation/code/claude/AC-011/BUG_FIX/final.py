"""
Deterministic 0/1 Knapsack solver using descending-capacity DP updates.

Given a list of (weight, value) items (0-indexed by original position) and
an integer capacity, find a subset of items with total weight <= capacity
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
    Solve the 0/1 knapsack problem with a descending-capacity 1D DP.

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

    # dp_history[i] = the 1D dp array (over capacities 0..capacity) AFTER
    # processing item i with the classic descending-capacity in-place update.
    # dp_history[-1] (conceptually "before any item") is the all-zero array.
    dp = [0.0] * (capacity + 1)
    dp_history: List[List[float]] = [dp[:]]  # history[0] = state before item 0

    for i in range(n):
        w, v = weights[i], values[i]
        # Descending capacity update: guarantees each item used at most once.
        for c in range(capacity, w - 1, -1):
            candidate = dp[c - w] + v
            if candidate > dp[c]:
                dp[c] = candidate
        dp_history.append(dp[:])  # history[i+1] = state after item i

    max_value = dp[capacity]

    # Reconstruct the lexicographically smallest optimal index set.
    # Walk items in increasing index order; at each step, prefer to INCLUDE
    # the current item if doing so still permits reaching the overall
    # optimum for the remaining items, using EXACT comparisons against the
    # actual DP values that were computed (no floating-point tolerance).
    selected: List[int] = []
    c = capacity
    target = max_value
    for i in range(n):
        w, v = weights[i], values[i]
        before = dp_history[i]      # state before considering item i
        after_all = dp_history[n]   # not used directly; kept for clarity

        if w <= c:
            # Best value achievable from item i onward, at capacity c,
            # if we include item i now: v + (best using items i+1..n-1
            # with capacity c-w). That "best using items i+1..n-1" is
            # exactly dp_history[n][c-w] restricted to suffix i+1..n-1 —
            # but our dp is a forward 1D array, so we instead verify
            # feasibility by re-deriving the suffix-optimal value via a
            # second, item-indexed forward pass comparison below.
            pass

        # To keep the reconstruction exact and O(n*capacity) without a
        # separate suffix table, recompute what "including item i" would
        # require: the remaining target must be achievable by items
        # i+1..n-1 with capacity c-w. We check this using a suffix DP
        # computed on demand (see suffix_best below), built once.
        break  # placeholder, replaced by suffix table below

    # Build a suffix-best table aligned with descending-capacity semantics:
    # suffix[i][c] = max value using items i..n-1 with capacity c, computed
    # with the same descending-capacity 0/1 update per item (so it matches
    # dp's semantics exactly and uses exact/no-tolerance comparisons).
    suffix = [[0.0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        w, v = weights[i], values[i]
        row = suffix[i + 1][:]
        for c in range(capacity, w - 1, -1):
            candidate = row[c - w] + v
            if candidate > row[c]:
                row[c] = candidate
        suffix[i] = row

    assert suffix[0][capacity] == max_value  # descending-update DP agrees with suffix table

    selected = []
    c = capacity
    for i in range(n):
        w, v = weights[i], values[i]
        if w <= c and v + suffix[i + 1][c - w] == suffix[i][c]:
            selected.append(i)
            c -= w

    return max_value, selected


if __name__ == "__main__":
    # Demonstrates the fix: exact tie-breaking, no float tolerance needed.
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

    # Tie-breaking example: two items tie in weight/value ratio.
    tie_items = [
        (1, 1),  # index 0
        (1, 1),  # index 1
        (2, 2),  # index 2
    ]
    tie_cap = 2
    value2, chosen2 = solve_knapsack(tie_items, tie_cap)
    print(f"Max value: {value2}")
    print(f"Selected original indices (lexicographically smallest): {chosen2}")
    # Expect [0, 1] (lexicographically smaller than [2]), value 2.

    # Regression check against the old buggy float-tolerance approach:
    # values chosen so an epsilon-based check could misfire.
    edge_items = [
        (3, 0.1 + 0.2),          # index 0 -> 0.3 (imprecise float)
        (3, 0.30000000000000004) # index 1 -> exact float repr of 0.1+0.2
    ]
    edge_cap = 3
    value3, chosen3 = solve_knapsack(edge_items, edge_cap)
    print(f"Max value: {value3}")
    print(f"Selected original indices (lexicographically smallest): {chosen3}")
    # Expect [0] deterministically (smallest index among equal-value ties).