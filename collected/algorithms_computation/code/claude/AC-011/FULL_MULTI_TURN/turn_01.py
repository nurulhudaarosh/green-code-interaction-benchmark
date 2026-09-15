def knapsack01(items, capacity):
    """
    items: list of (weight, value) tuples, original index = position in list
    capacity: non-negative integer capacity

    Returns: (max_value, sorted_list_of_selected_original_indices)
    Ties broken by lexicographically smallest index list.
    """
    n = len(items)
    W = capacity

    if n == 0 or W <= 0:
        return 0, []

    # dp[i][c] = max value using first i items with capacity c
    dp = [[0] * (W + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        w_i, v_i = items[i - 1]
        for c in range(W + 1):
            best = dp[i - 1][c]  # don't take item i-1
            if w_i <= c:
                cand = dp[i - 1][c - w_i] + v_i
                if cand > best:
                    best = cand
            dp[i][c] = best

    max_value = dp[n][W]

    # Reconstruct: to get lexicographically smallest index list among
    # optimal solutions, decide items in increasing index order (0..n-1),
    # greedily EXCLUDING an item if there exists an optimal completion
    # without it (since excluding a smaller index first, when both choices
    # lead to an optimal total, yields the lexicographically smaller set).
    selected = []
    c = W
    # feasible[i][c] = best achievable value using items i..n-1 with capacity c
    feasible = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        w_i, v_i = items[i]
        for cc in range(W + 1):
            best = feasible[i + 1][cc]
            if w_i <= cc:
                cand = feasible[i + 1][cc - w_i] + v_i
                if cand > best:
                    best = cand
            feasible[i][cc] = best

    remaining_value = max_value
    c = W
    for i in range(n):
        w_i, v_i = items[i]
        # Try excluding item i: can we still reach remaining_value using items i+1..n-1?
        if feasible[i + 1][c] == remaining_value:
            continue  # exclude item i (prefer smaller index list -> skip if possible)
        else:
            # must include item i
            selected.append(i)
            c -= w_i
            remaining_value -= v_i

    return max_value, sorted(selected)


if __name__ == "__main__":
    # Deterministic demo
    items = [(2, 3), (3, 4), (4, 5), (5, 8)]
    capacity = 5
    value, indices = knapsack01(items, capacity)
    print("Max value:", value)
    print("Selected indices:", indices)