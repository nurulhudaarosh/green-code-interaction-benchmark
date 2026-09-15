def knapsack_with_summary(items, capacity, return_summary=False):
    """
    Solve 0/1 knapsack with lexicographically smallest index list.
    
    Parameters:
        items: list of (weight, value)
        capacity: int
        return_summary: bool (default False) – if True, also return operation summary.
    
    Returns:
        If return_summary is False: list of selected indices.
        If return_summary is True: (list of selected indices, dict with summary)
    """
    n = len(items)
    W = capacity
    
    # DP array: dp[c] = max value with capacity c (at most)
    dp = [0] * (W + 1)
    
    # Counters for summary
    dp_updates = 0
    reconstruction_checks = 0
    
    # 0/1 knapsack with descending capacity
    for w, v in items:
        if w > W:
            continue
        # Descending loop
        for c in range(W, w - 1, -1):
            new_val = dp[c - w] + v
            if new_val > dp[c]:
                dp[c] = new_val
            dp_updates += 1   # every inner iteration is a decision/operation
    
    # Reconstruct lexicographically smallest optimal index list
    selected = []
    remaining = W
    for i, (w, v) in enumerate(items):
        reconstruction_checks += 1
        if w <= remaining and dp[remaining] == dp[remaining - w] + v:
            selected.append(i)
            remaining -= w
            # After including, we continue with the new remaining capacity.
            # The condition for later items uses the same dp array (which is global optimum).
    
    if return_summary:
        summary = {
            "dp_updates": dp_updates,
            "reconstruction_checks": reconstruction_checks,
            "total_operations": dp_updates + reconstruction_checks
        }
        return selected, summary
    else:
        return selected


# --------------------------------------------------------------------
# Example usage (demonstrates both modes)
if __name__ == "__main__":
    items = [(2, 3), (3, 4), (4, 5), (5, 6)]
    capacity = 8
    
    # Without summary (original behavior)
    result = knapsack_with_summary(items, capacity)
    print("Selected indices (no summary):", result)
    # Expected: [0, 3]  (value 9, lexicographically smaller than [1,2])
    
    # With summary (new feature)
    indices, summary = knapsack_with_summary(items, capacity, return_summary=True)
    print("Selected indices:", indices)
    print("Operation summary:", summary)