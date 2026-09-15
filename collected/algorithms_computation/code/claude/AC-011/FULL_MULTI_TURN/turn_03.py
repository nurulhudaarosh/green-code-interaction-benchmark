def knapsack01(items, capacity, include_summary=False):
    """
    items: list of (weight, value) tuples; original index = position in list
    capacity: non-negative integer capacity
    include_summary: if True, also return a deterministic operation_summary dict.

    Default behavior (include_summary=False) is UNCHANGED from the original spec:
        returns (max_value, sorted_list_of_selected_original_indices)

    If include_summary=True, returns:
        (max_value, sorted_list_of_selected_original_indices, operation_summary)

    Uses 0/1 knapsack DP with a 1D array updated in DESCENDING capacity order.
    Ties broken by lexicographically smallest index list.
    Deterministic; standard library only.
    """
    n = len(items)
    W = capacity

    if n == 0 or W <= 0:
        if include_summary:
            return 0, [], {
                "dp_transitions": 0,
                "feasibility_cells": 0,
                "inclusion_decisions": 0,
                "total_operations": 0,
            }
        return 0, []

    for w, v in items:
        if w < 0 or v < 0:
            raise ValueError("weights and values must be non-negative")

    # --- Pass 1: max value via 1D DP, descending capacity updates ---
    dp = [0] * (W + 1)
    dp_transitions = 0
    for (w_i, v_i) in items:
        for c in range(W, w_i - 1, -1):  # descending: each item used at most once
            dp_transitions += 1  # each capacity cell visited = one decision
            cand = dp[c - w_i] + v_i
            if cand > dp[c]:
                dp[c] = cand
    max_value = dp[W]

    # --- Pass 2: suffix feasibility table for lexicographic reconstruction ---
    feasible = [[0] * (W + 1) for _ in range(n + 1)]
    feasibility_cells = 0
    for i in range(n - 1, -1, -1):
        w_i, v_i = items[i]
        row_prev = feasible[i + 1]
        row_cur = feasible[i]
        for c in range(W + 1):
            feasibility_cells += 1
            best = row_prev[c]
            if w_i <= c:
                cand = row_prev[c - w_i] + v_i
                if cand > best:
                    best = cand
            row_cur[c] = best

    if feasible[0][W] != max_value:
        raise AssertionError("internal inconsistency between DP passes")

    # --- Reconstruct lexicographically smallest index list ---
    selected = []
    c = W
    remaining_value = max_value
    inclusion_decisions = 0
    for i in range(n):
        inclusion_decisions += 1
        w_i, v_i = items[i]
        if feasible[i + 1][c] == remaining_value:
            continue  # exclude item i -> lexicographically smaller
        selected.append(i)
        c -= w_i
        remaining_value -= v_i

    result_value = max_value
    result_indices = sorted(selected)

    if not include_summary:
        return result_value, result_indices

    operation_summary = {
        "dp_transitions": dp_transitions,
        "feasibility_cells": feasibility_cells,
        "inclusion_decisions": inclusion_decisions,
        "total_operations": dp_transitions + feasibility_cells + inclusion_decisions,
    }
    return result_value, result_indices, operation_summary


if __name__ == "__main__":
    # Backward-compatibility check: default call unchanged
    items = [(2, 3), (3, 4), (4, 5), (5, 8)]
    value, indices = knapsack01(items, 5)
    print("Max value:", value)
    print("Selected indices:", indices)

    # Tie-breaking regression check
    tie_items = [(2, 3), (3, 3)]
    tv, ti = knapsack01(tie_items, 3)
    assert tv == 3 and ti == [0], f"expected (3, [0]), got ({tv}, {ti})"

    # New opt-in feature
    value2, indices2, summary = knapsack01(items, 5, include_summary=True)
    print("Max value:", value2)
    print("Selected indices:", indices2)
    print("Operation summary:", summary)