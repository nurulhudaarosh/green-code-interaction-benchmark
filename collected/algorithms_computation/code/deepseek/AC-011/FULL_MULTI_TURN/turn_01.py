def knapsack_selected_indices(weights, values, capacity):
    """
    Solve 0/1 knapsack and return lexicographically smallest list of selected indices.
    
    Args:
        weights: List of item weights
        values:  List of item values
        capacity: Knapsack capacity
    
    Returns:
        List of original indices (0-based) in ascending order
    """
    n = len(weights)
    
    # DP table: dp[i][c] = max value using items from i to n-1 with capacity c
    # We use (n+1) x (capacity+1) for easy reconstruction
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    # Fill DP table from bottom to top (reverse order for tie-breaking)
    for i in range(n - 1, -1, -1):
        w = weights[i]
        v = values[i]
        for c in range(capacity + 1):
            if c >= w:
                dp[i][c] = max(dp[i + 1][c], dp[i + 1][c - w] + v)
            else:
                dp[i][c] = dp[i + 1][c]
    
    # Reconstruct lexicographically smallest index list
    selected = []
    remaining_capacity = capacity
    
    for i in range(n):
        # If skipping item i still gives optimal value, skip it
        if dp[i][remaining_capacity] == dp[i + 1][remaining_capacity]:
            continue
        else:
            # Must include item i
            selected.append(i)
            remaining_capacity -= weights[i]
    
    return selected


# Example usage
if __name__ == "__main__":
    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 6]
    capacity = 5
    
    result = knapsack_selected_indices(weights, values, capacity)
    print(f"Selected indices: {result}")
    print(f"Total value: {sum(values[i] for i in result)}")
    print(f"Total weight: {sum(weights[i] for i in result)}")
    
    # Test with tie-breaking
    weights2 = [1, 1, 2]
    values2 = [2, 2, 4]
    capacity2 = 2
    result2 = knapsack_selected_indices(weights2, values2, capacity2)
    print(f"\nTie test - Selected indices: {result2}")  # Should be [0, 1] not [2]