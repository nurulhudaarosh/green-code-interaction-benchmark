def knapsack_01(weights: list[int], values: list[int], capacity: int) -> list[int]:
    """
    Solves 0/1 Knapsack deterministically with exact tie-breaking.
    
    Returns the original item indices maximizing total value within capacity.
    If multiple subsets give the same optimal value, returns the lexicographically
    smallest list of indices.
    """
    n = len(weights)
    
    # dp[i][w] = max value using a subset of items from index 0..i-1 with capacity w
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        w_i, v_i = weights[i - 1], values[i - 1]
        for w in range(capacity + 1):
            if w_i <= w:
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - w_i] + v_i)
            else:
                dp[i][w] = dp[i - 1][w]
                
    # To find the lexicographically smallest index list:
    # We reconstruct selected items from index 0 to n-1.
    selected_indices = []
    curr_w = capacity
    
    # Find the smallest total weight that achieves the maximum possible value dp[n][capacity]
    max_val = dp[n][capacity]
    for w in range(capacity + 1):
        if dp[n][w] == max_val:
            curr_w = w
            break
            
    for i in range(n):
        w_i, v_i = weights[i], values[i]
        # Check if we can/should include item i
        # Including item i requires dp[n][curr_w] == dp[i+1][curr_w]
        # We prefer taking item i early if it belongs to an optimal state sequence
        if w_i <= curr_w and dp[n][curr_w] == dp[n][curr_w - w_i] + v_i:
            # Verify that excluding vs including leads to valid max_val path
            if dp[i + 1][curr_w] != dp[i][curr_w]:
                selected_indices.append(i)
                curr_w -= w_i

    return selected_indices


# Verification of Fix
if __name__ == "__main__":
    weights = [1, 1]
    values = [10, 10]
    capacity = 1
    
    result = knapsack_01(weights, values, capacity)
    print(f"Selected Indices: {result}")  # Output: [0]