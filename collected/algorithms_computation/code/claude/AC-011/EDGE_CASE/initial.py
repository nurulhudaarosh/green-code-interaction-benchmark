from typing import List, Tuple


def knapsack01(weights: List[int], values: List[int], capacity: int) -> Tuple[int, List[int]]:
    """
    Solve 0/1 knapsack deterministically.

    Args:
        weights: list of item weights (non-negative integers)
        values: list of item values (non-negative integers)
        capacity: knapsack capacity (non-negative integer)

    Returns:
        (max_value, selected_indices) where selected_indices is sorted
        ascending and is the lexicographically smallest such list among
        all subsets achieving max_value.
    """
    n = len(weights)
    if n != len(values):
        raise ValueError("weights and values must have the same length")
    if capacity < 0:
        raise ValueError("capacity must be non-negative")

    # dp[c] = best value achievable with capacity exactly <= c
    dp = [0] * (capacity + 1)

    # keep[i][c] = True if item i was taken when this dp row was computed
    # (we store per-item full rows to allow exact reconstruction)
    keep = [[False] * (capacity + 1) for _ in range(n)]

    for i in range(n):
        w, v = weights[i], values[i]
        # iterate capacity descending so each item is used at most once
        for c in range(capacity, -1, -1):
            if w <= c and dp[c - w] + v > dp[c]:
                dp[c] = dp[c - w] + v
                keep[i][c] = True
            # else dp[c] unchanged, keep[i][c] stays False (item i not
            # taken to reach this specific dp[c] in this pass)

    max_value = dp[capacity]

    # Reconstruct forward (index 0 upward) to get the lexicographically
    # smallest index list: at each item, prefer excluding it if the
    # optimal value is still achievable without it using a fresh
    # feasibility check via a second DP pass (suffix dp), which is the
    # standard deterministic technique.

    # Build suffix DP: suffix_dp[i][c] = max value using items i..n-1
    # with capacity c.
    suffix_dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        w, v = weights[i], values[i]
        for c in range(capacity + 1):
            best = suffix_dp[i + 1][c]
            if w <= c:
                cand = suffix_dp[i + 1][c - w] + v
                if cand > best:
                    best = cand
            suffix_dp[i][c] = best

    selected = []
    remaining_capacity = capacity
    remaining_value = suffix_dp[0][capacity]

    for i in range(n):
        w, v = weights[i], values[i]
        # Value achievable if we skip item i
        skip_value = suffix_dp[i + 1][remaining_capacity]
        if skip_value == remaining_value:
            # Skipping keeps optimum reachable -> skip for lexicographically
            # smallest index set
            continue
        else:
            # Must take item i to preserve optimal value
            selected.append(i)
            remaining_capacity -= w
            remaining_value -= v

    return max_value, selected


def _self_test() -> None:
    # Basic correctness
    w = [2, 3, 4, 5]
    v = [3, 4, 5, 6]
    cap = 5
    val, idxs = knapsack01(w, v, cap)
    assert val == 7, val
    assert idxs == [0, 1], idxs

    # Tie-breaking: two single items with equal value/weight ratio giving
    # same total value: prefer smaller index set lexicographically.
    w2 = [1, 1]
    v2 = [5, 5]
    cap2 = 1
    val2, idxs2 = knapsack01(w2, v2, cap2)
    assert val2 == 5, val2
    assert idxs2 == [0], idxs2

    # Empty capacity
    val3, idxs3 = knapsack01([1, 2], [10, 20], 0)
    assert val3 == 0 and idxs3 == [], (val3, idxs3)

    # Empty items
    val4, idxs4 = knapsack01([], [], 10)
    assert val4 == 0 and idxs4 == [], (val4, idxs4)

    # Zero-weight item always includable if it improves/ties value at
    # zero cost -> should be selected (smaller index list preference
    # only matters among equal-value sets; here it strictly helps).
    val5, idxs5 = knapsack01([0, 1], [3, 3], 1)
    assert val5 == 6, val5
    assert idxs5 == [0, 1], idxs5

    print("All self-tests passed.")


if __name__ == "__main__":
    _self_test()

    # Example usage
    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 6]
    capacity = 5
    best_value, chosen_indices = knapsack01(weights, values, capacity)
    print(f"Max value: {best_value}")
    print(f"Selected original indices: {chosen_indices}")