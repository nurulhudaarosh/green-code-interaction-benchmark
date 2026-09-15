def knapsack_indices(items, capacity):
    """
    items: list of (weight, value)
    capacity: integer
    Returns list of original indices (0-based) that maximize value,
    with lexicographically smallest index list among optimal solutions.
    """
    n = len(items)
    # dp[c] = max value for capacity c
    dp = [0] * (capacity + 1)
    
    # 0/1 knapsack with descending capacity
    for w, v in items:
        if w > capacity:
            continue
        # iterate backwards to avoid reusing item
        for c in range(capacity, w - 1, -1):
            new_val = dp[c - w] + v
            if new_val > dp[c]:
                dp[c] = new_val
    
    # Reconstruct lexicographically smallest optimal index list
    selected = []
    remaining_cap = capacity
    # We need the original dp array after all items.
    # We process items in increasing index order.
    for i, (w, v) in enumerate(items):
        if w <= remaining_cap and dp[remaining_cap] == dp[remaining_cap - w] + v:
            # Include this item
            selected.append(i)
            remaining_cap -= w
            # Note: after we include, dp[remaining_cap] now refers to the optimal
            # value for the new remaining capacity using all items.
            # The condition still holds for later items.
    return selected

# Example usage:
if __name__ == "__main__":
    # Test case
    items = [(2, 3), (3, 4), (4, 5), (5, 6)]
    capacity = 8
    print(knapsack_indices(items, capacity))  # Expected: [0, 2] (values 3+5=8) or [1,2]? Actually 0+2 gives 8, 1+2 gives 9? Let's compute: item0 (2,3), item1 (3,4), item2 (4,5), item3 (5,6). Capacity 8: best is item1+item2 = 3+4 weight 7, value 9; or item0+item2 = 2+4 weight 6, value 8; or item0+item3 = 2+5 weight 7, value 9? item0+item3 = 2+5=7 weight, value 3+6=9, so best value 9 with two possible subsets: [0,3] and [1,2]. Lexicographically smaller is [0,3] because 0 < 1. Our algorithm should pick [0,3].
    # Let's test: 
    print(knapsack_indices(items, 8))  # Should output [0, 3]