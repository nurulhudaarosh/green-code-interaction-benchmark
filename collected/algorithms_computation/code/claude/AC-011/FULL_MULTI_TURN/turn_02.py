def knapsack01(items, capacity):
    """
    items: list of (weight, value) tuples; original index = position in list
    capacity: non-negative integer capacity

    Returns: (max_value, sorted_list_of_selected_original_indices)
    Uses 0/1 knapsack DP with a 1D array updated in DESCENDING capacity order.
    Ties broken by lexicographically smallest index list.
    Deterministic; standard library only.
    """
    n = len(items)
    W = capacity

    if n == 0 or W <= 0:
        return 0, []

    for w, v in items:
        if w < 0 or v < 0:
            raise ValueError("weights and values must be non-negative")

    # --- Pass 1: compute max value using 1D DP, descending capacity updates ---
    dp = [0] * (W + 1)
    for (w_i, v_i) in items:
        for c in range(W, w_i - 1, -1):  # descending: each item used at most once
            cand = dp[c - w_i] + v_i
            if cand > dp[c]:
                dp[c] = cand
    max_value = dp[W]

    # --- Pass 2: suffix feasibility table for deterministic lexicographic
    # reconstruction. feasible[i][c] = best value achievable using items
    # i..n-1 with capacity c. Built with the same descending-update 0/1
    # recurrence, one row per item, iterated from the last item backward. ---
    feasible = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        w_i, v_i = items[i]
        row_prev = feasible[i + 1]
        row_cur = feasible[i]
        for c in range(W + 1):
            best = row_prev[c]
            if w_i <= c:
                cand = row_prev[c - w_i] + v_i
                if cand > best:
                    best = cand
            row_cur[c] = best

    if feasible[0][W] != max_value:
        # sanity check: both passes must agree
        raise AssertionError("internal inconsistency between DP passes")

    # --- Reconstruct lexicographically smallest index list ---
    # Process items in increasing index order; skip item i if the optimal
    # remaining value is still reachable using only later items (i+1..n-1).
    selected = []
    c = W
    remaining_value = max_value
    for i in range(n):
        w_i, v_i = items[i]
        if feasible[i + 1][c] == remaining_value:
            continue  # exclude item i -> keeps index list lexicographically smaller
        selected.append(i)
        c -= w_i
        remaining_value -= v_i

    return max_value, sorted(selected)


if __name__ == "__main__":
    # Regression test for the tie-breaking bug
    items = [(2, 3), (3, 3)]
    value, indices = knapsack01(items, 3)
    assert value == 3
    assert indices == [0], f"expected [0], got {indices}"

    # Original demo
    items2 = [(2, 3), (3, 4), (4, 5), (5, 8)]
    value2, indices2 = knapsack01(items2, 5)
    print("Max value:", value2)
    print("Selected indices:", indices2)

    print("Tie case ok:", value, indices)