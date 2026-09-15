def knapsack01(items, capacity, include_summary=False):
    """
    items: list of (weight, value) tuples; original index = position in list
    capacity: non-negative integer capacity
    include_summary: if True, also return a deterministic operation_summary dict.

    Default (include_summary=False): returns (max_value, sorted_selected_indices)
    If include_summary=True: returns (max_value, sorted_selected_indices, operation_summary)

    Uses 0/1 knapsack DP with a 1D array updated in DESCENDING capacity order.
    Ties broken by lexicographically smallest index list.
    Deterministic; standard library only.
    """
    n = len(items)
    W = capacity

    if W < 0:
        raise ValueError("capacity must be non-negative")

    if n == 0 or W == 0:
        # capacity 0: only zero-weight items could be included
        selected = []
        remaining_value = 0
        if W == 0 and n > 0:
            for i, (w_i, v_i) in enumerate(items):
                if w_i < 0 or v_i < 0:
                    raise ValueError("weights and values must be non-negative")
                if w_i == 0 and v_i > 0:
                    selected.append(i)
            remaining_value = sum(items[i][1] for i in selected)
        if include_summary:
            return remaining_value, sorted(selected), {
                "dp_transitions": 0,
                "feasibility_cells": 0,
                "inclusion_decisions": 0,
                "total_operations": 0,
            }
        return remaining_value, sorted(selected)

    for w, v in items:
        if w < 0 or v < 0:
            raise ValueError("weights and values must be non-negative")

    # --- Pass 1: max value via 1D DP, descending capacity updates ---
    dp = [0] * (W + 1)
    dp_transitions = 0
    for (w_i, v_i) in items:
        if w_i == 0:
            # zero-weight item: always beneficial if positive value, free to add
            if v_i > 0:
                for c in range(W + 1):
                    dp[c] += v_i
            dp_transitions += 1
            continue
        if w_i > W:
            # can never be included; no capacity cells to update
            continue
        for c in range(W, w_i - 1, -1):
            dp_transitions += 1
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
            continue
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def _run_tests():
    # 1. Empty items list
    v, idx = knapsack01([], 10)
    assert (v, idx) == (0, []), f"empty items failed: {(v, idx)}"

    # 2. Zero capacity, items present
    v, idx = knapsack01([(1, 5), (2, 3)], 0)
    assert (v, idx) == (0, []), f"zero capacity failed: {(v, idx)}"

    # 3. Zero capacity with a zero-weight item present
    v, idx = knapsack01([(0, 4), (2, 3)], 0)
    assert (v, idx) == (4, [0]), f"zero capacity + zero-weight item failed: {(v, idx)}"

    # 4. Zero-weight item at normal capacity (always includable)
    v, idx = knapsack01([(0, 4), (3, 5)], 3)
    assert (v, idx) == (9, [0, 1]), f"zero-weight item failed: {(v, idx)}"

    # 5. Zero-weight, zero-value item: should not force inclusion (tie -> exclude for lexicographic min)
    v, idx = knapsack01([(0, 0), (2, 5)], 2)
    assert (v, idx) == (5, [1]), f"zero-weight zero-value failed: {(v, idx)}"

    # 6. Item weight exceeds capacity -> never selected
    v, idx = knapsack01([(100, 50), (2, 3)], 5)
    assert (v, idx) == (3, [1]), f"oversized item failed: {(v, idx)}"

    # 7. Capacity exactly equals sum of all weights -> take everything
    items = [(2, 3), (3, 4), (5, 6)]
    v, idx = knapsack01(items, 10)
    assert (v, idx) == (13, [0, 1, 2]), f"exact total weight failed: {(v, idx)}"

    # 8. Single item exactly matching capacity
    v, idx = knapsack01([(7, 9)], 7)
    assert (v, idx) == (9, [0]), f"single exact-fit item failed: {(v, idx)}"

    # 9. All items identical -> lexicographically smallest single index on tie
    v, idx = knapsack01([(3, 3), (3, 3), (3, 3)], 3)
    assert (v, idx) == (3, [0]), f"identical items tie-break failed: {(v, idx)}"

    # 10. Larger-scale boundary: many items, moderate capacity (correctness + perf sanity)
    n = 50
    items = [(i % 7 + 1, (i * 13) % 29 + 1) for i in range(n)]
    v, idx = knapsack01(items, 60)
    total_w = sum(items[i][0] for i in idx)
    assert total_w <= 60, "capacity violated in large test"
    # brute-force cross-check on a smaller slice for confidence
    small_items = items[:12]
    best_val, best_idx = 0, []
    from itertools import combinations
    for r in range(len(small_items) + 1):
        for combo in combinations(range(len(small_items)), r):
            w = sum(small_items[i][0] for i in combo)
            val = sum(small_items[i][1] for i in combo)
            if w <= 15:
                if val > best_val or (val == best_val and sorted(combo) < best_idx):
                    best_val, best_idx = val, list(combo)
    v2, idx2 = knapsack01(small_items, 15)
    assert (v2, idx2) == (best_val, best_idx), f"brute-force mismatch: {(v2, idx2)} vs {(best_val, best_idx)}"

    # 11. include_summary preserves original fields and adds summary only when requested
    v, idx = knapsack01(items[:5], 10)
    v3, idx3, summary = knapsack01(items[:5], 10, include_summary=True)
    assert (v, idx) == (v3, idx3), "summary flag altered original output"
    assert set(summary.keys()) == {"dp_transitions", "feasibility_cells", "inclusion_decisions", "total_operations"}
    assert summary["total_operations"] == (
        summary["dp_transitions"] + summary["feasibility_cells"] + summary["inclusion_decisions"]
    )

    print("All boundary and regression tests passed.")


if __name__ == "__main__":
    _run_tests()