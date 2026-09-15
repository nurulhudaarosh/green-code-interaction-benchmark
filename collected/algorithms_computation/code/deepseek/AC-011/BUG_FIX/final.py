def knapsack_selection(weights, values, capacity):
    """
    Returns lexicographically smallest list of indices achieving maximum value.
    Uses 0/1 knapsack DP with suffix table for deterministic reconstruction.
    
    Args:
        weights: List of item weights
        values: List of item values
        capacity: Maximum total weight allowed
    
    Returns:
        List of original indices (0-based) of selected items
    """
    n = len(weights)
    W = capacity
    
    # suffix[i][w] = maximum value using items from i to n-1 with capacity w
    # Initialize with -1 (impossible), but suffix[n][w] = 0 (no items left)
    suffix = [[-1] * (W + 1) for _ in range(n + 1)]
    for w in range(W + 1):
        suffix[n][w] = 0
    
    # Fill suffix DP table from bottom to top
    for i in range(n - 1, -1, -1):
        wi, vi = weights[i], values[i]
        for w in range(W + 1):
            # Option 1: Skip item i
            best = suffix[i + 1][w]
            
            # Option 2: Take item i if capacity allows
            if w >= wi:
                take = vi + suffix[i + 1][w - wi]
                if take > best:
                    best = take
            
            suffix[i][w] = best
    
    optimal_value = suffix[0][W]
    
    # Reconstruct lexicographically smallest optimal solution
    selected = []
    remaining_cap = W
    remaining_target = optimal_value
    
    for i in range(n):
        wi, vi = weights[i], values[i]
        
        # Check if we can include item i and still achieve the optimal value
        if wi <= remaining_cap:
            if vi + suffix[i + 1][remaining_cap - wi] == remaining_target:
                # Include this item (smallest index that can still achieve optimum)
                selected.append(i)
                remaining_cap -= wi
                remaining_target -= vi
        # If we skip, remaining_cap and remaining_target stay unchanged
    
    return selected


# Example usage and testing
if __name__ == "__main__":
    # Test case 1: Unique optimal solution
    weights1 = [2, 3, 4, 5]
    values1 = [3, 4, 5, 6]
    cap1 = 8
    print("Test 1:", knapsack_selection(weights1, values1, cap1))
    # Expected: [0, 3] (value 9, weight 7) or [1, 2] (value 9, weight 7)
    # Lexicographically smallest: [0, 3]
    
    # Test case 2: Multiple optimal solutions with tie-breaking
    weights2 = [2, 2, 3, 3]
    values2 = [4, 4, 5, 5]
    cap2 = 5
    print("Test 2:", knapsack_selection(weights2, values2, cap2))
    # Expected: [0, 2] (value 9, weight 5)
    # [0, 3] also gives 9, [1, 2] gives 9, [1, 3] gives 9
    # Lexicographically smallest: [0, 2]
    
    # Test case 3: Another tie-breaking scenario
    weights3 = [1, 2, 2, 3]
    values3 = [2, 3, 3, 4]
    cap3 = 4
    print("Test 3:", knapsack_selection(weights3, values3, cap3))
    # Expected: [0, 3] (value 6, weight 4)
    # [1, 2] also gives 6 (weight 4)
    # Lexicographically smallest: [0, 3]
    
    # Test case 4: All equal values
    weights4 = [2, 3, 2, 3]
    values4 = [5, 5, 5, 5]
    cap4 = 5
    print("Test 4:", knapsack_selection(weights4, values4, cap4))
    # Expected: [0, 1] (value 10, weight 5)
    # Many optimal solutions, lexicographically smallest is [0, 1]
    
    # Test case 5: Empty input
    print("Test 5:", knapsack_selection([], [], 10))
    # Expected: []
    
    # Test case 6: Single item
    print("Test 6:", knapsack_selection([5], [10], 5))
    # Expected: [0]
    
    # Test case 7: Item too heavy
    print("Test 7:", knapsack_selection([10], [100], 5))
    # Expected: []