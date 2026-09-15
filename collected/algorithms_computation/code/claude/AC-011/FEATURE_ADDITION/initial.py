"""
PROBLEM
-------
0/1 Knapsack: given n indivisible items, each with a non-negative integer
weight w[i] and value v[i], and a knapsack of integer capacity C, choose a
subset of items whose total weight does not exceed C while maximizing total
value. Each item may be chosen at most once (0/1, not fractional).

If multiple subsets achieve the same maximum total value, return the subset
whose sorted list of original indices is lexicographically smallest (i.e.
compared element-by-element as sequences; a shorter list that is a prefix of
a longer one is considered smaller, e.g. [1] < [1,2] and [0,3] < [1]).

KEY CONSTRAINTS
---------------
- Items are indivisible (0/1 knapsack, not fractional knapsack).
- weight[i] >= 0 (integers), value[i] may be any real/int but must be
  comparable; capacity C >= 0 (integer) — required for DP table indexing.
- n can be 0 (empty item list) -> answer is an empty selection.
- Deterministic: no randomness, no network/API calls, no external services,
  no human interaction. Pure standard library, pure computation.

REQUIRED OUTPUT
----------------
- The list of *original indices* (indices into the input items list) of the
  selected items, sorted ascending, representing the lexicographically
  smallest index list among all subsets that attain the optimal value.
- (The achieved optimal total value is also returned for convenience.)

ALGORITHM
---------
Standard 0/1 knapsack DP, computed as a SUFFIX dp table so we can both
determine the optimum and reconstruct the lexicographically smallest
optimal index set in a single left-to-right greedy pass:

  dp[i][c] = max total value obtainable using only items i, i+1, ..., n-1
             with remaining capacity c.

  Recurrence (0 <= i < n):
      dp[i][c] = dp[i+1][c]                                   (skip item i)
      dp[i][c] = max(dp[i][c], v[i] + dp[i+1][c-w[i]])         (take item i,
                                                                 if w[i]<=c)
  Base case: dp[n][c] = 0 for all c.

Reconstruction (why this yields the lexicographically smallest index list):
Because indices are processed in increasing order 0,1,...,n-1, and because
including a smaller index i (whenever it is still consistent with reaching
the overall optimum) always produces a sequence that is lexicographically
<= any sequence that skips i in favor of only larger indices, the correct
greedy rule is:

  Walk i = 0..n-1, tracking remaining capacity c and remaining value target
  `rem` (initially dp[0][C]).
    - If w[i] <= c and v[i] + dp[i+1][c-w[i]] == rem:
          include item i; rem -= v[i]; c -= w[i]
    - Else:
          skip item i (dp[i+1][c] == rem must hold, by definition of dp[i][c])

This greedy choice is provably optimal for lexicographic minimality: at
every step we prefer "include i" whenever it remains feasible to reach the
global optimum, because doing so places the smallest available index as
early as possible in the output sequence, which lexicographically dominates
any alternative that defers to a strictly larger index (or omits i).

Complexity: O(n * C) time and O(n * C) space for the DP table (needed for
reconstruction). This is pseudo-polynomial (depends on the magnitude of C).
"""

from typing import List, Sequence, Tuple, NamedTuple


class KnapsackResult(NamedTuple):
    total_value: float
    selected_indices: List[int]


def solve_knapsack_01(
    items: Sequence[Tuple[int, float]],
    capacity: int,
) -> KnapsackResult:
    """
    Solve the 0/1 knapsack problem exactly and deterministically.

    Args:
        items: sequence of (weight, value) pairs. weight must be a
               non-negative integer. value may be int or float.
               The position of each pair in this sequence is its
               "original index", returned in the result.
        capacity: non-negative integer knapsack capacity.

    Returns:
        KnapsackResult(total_value, selected_indices) where
        selected_indices is the lexicographically smallest list of
        original indices (ascending) achieving the maximum total_value.

    Raises:
        ValueError: on invalid (negative / non-integer) weights or capacity.
    """
    n = len(items)

    if not isinstance(capacity, int) or capacity < 0:
        raise ValueError("capacity must be a non-negative integer")

    weights: List[int] = []
    values: List[float] = []
    for idx, (w, v) in enumerate(items):
        if not isinstance(w, int) or w < 0:
            raise ValueError(f"item {idx} has invalid weight {w!r}; "
                              f"weights must be non-negative integers")
        weights.append(w)
        values.append(v)

    # dp[i][c] = max value achievable using items[i:] with capacity c.
    # Use (n+1) x (capacity+1) table; dp[n][*] = 0 by initialization.
    dp: List[List[float]] = [[0.0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(n - 1, -1, -1):
        w_i, v_i = weights[i], values[i]
        row_i = dp[i]
        row_next = dp[i + 1]
        for c in range(capacity + 1):
            best = row_next[c]  # skip item i
            if w_i <= c:
                take = v_i + row_next[c - w_i]
                if take > best:
                    best = take
            row_i[c] = best

    total_value = dp[0][capacity]

    # Reconstruct lexicographically smallest optimal index set.
    selected: List[int] = []
    rem_capacity = capacity
    rem_value = total_value

    for i in range(n):
        w_i, v_i = weights[i], values[i]
        can_take = w_i <= rem_capacity
        if can_take:
            candidate = v_i + dp[i + 1][rem_capacity - w_i]
        else:
            candidate = None

        # Prefer taking item i whenever it keeps the optimum reachable,
        # since that yields the lexicographically smallest index list.
        if can_take and candidate == rem_value:
            selected.append(i)
            rem_capacity -= w_i
            rem_value -= v_i
        # else: skipping must be consistent, i.e. dp[i+1][rem_capacity] == rem_value

    return KnapsackResult(total_value=total_value, selected_indices=selected)


if __name__ == "__main__":
    # Deterministic self-contained demonstration (no external input needed).
    demo_items = [
        (2, 3),   # index 0
        (3, 4),   # index 1
        (4, 5),   # index 2
        (5, 6),   # index 3
    ]
    demo_capacity = 5

    result = solve_knapsack_01(demo_items, demo_capacity)
    print(f"Optimal total value: {result.total_value}")
    print(f"Selected original indices: {result.selected_indices}")

    # Example designed to show a tie broken lexicographically:
    # two disjoint items of equal combined value vs one single item.
    tie_items = [
        (1, 10),  # index 0
        (1, 10),  # index 1  -> {0,1} has value 20, weight 2
        (2, 20),  # index 2  -> {2} alone also has value 20, weight 2
    ]
    tie_result = solve_knapsack_01(tie_items, capacity=2)
    print(f"Tie-break value: {tie_result.total_value}")
    print(f"Tie-break indices (expect [0, 1], lexicographically smaller "
          f"than [2]): {tie_result.selected_indices}")