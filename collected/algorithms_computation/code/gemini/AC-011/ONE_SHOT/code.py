def knapsack_lexicographical(weights: list[int], values: list[int], capacity: int) -> list[int]:
    """
    Solves the 0/1 Knapsack Problem and returns the list of selected item indices.
    Ties in total value are broken by choosing the lexicographically smallest index list.
    
    :param weights: List of item weights (non-negative integers)
    :param values: List of item values (non-negative integers)
    :param capacity: Maximum capacity of the knapsack (non-negative integer)
    :return: Lexicographically smallest list of selected 0-based item indices
    """
    n = len(weights)
    
    # dp[w] = (max_value, index_list)
    # Initialize dp table where for capacity 0, value is 0 and index list is empty
    dp = [(0, []) for _ in range(capacity + 1)]
    
    for i in range(n):
        w_i = weights[i]
        v_i = values[i]
        
        # Skip items that exceed total capacity
        if w_i > capacity:
            continue
            
        # Update DP table in reverse order to ensure each item is used at most once
        for cap in range(capacity, w_i - 1, -1):
            prev_val, prev_indices = dp[cap - w_i]
            cand_val = prev_val + v_i
            cand_indices = prev_indices + [i]
            
            curr_val, curr_indices = dp[cap]
            
            # Update if candidate yields strictly higher value
            if cand_val > curr_val:
                dp[cap] = (cand_val, cand_indices)
            # Break ties with lexicographically smaller index list
            elif cand_val == curr_val:
                if cand_indices < curr_indices:
                    dp[cap] = (cand_val, cand_indices)

    # Find the maximum value across all valid capacities <= capacity
    max_val = -1
    best_indices = []
    
    for cap in range(capacity + 1):
        val, indices = dp[cap]
        if val > max_val:
            max_val = val
            best_indices = indices
        elif val == max_val:
            if indices < best_indices:
                best_indices = indices

    return best_indices


# --- Example Usage ---
if __name__ == "__main__":
    # Test Case: Multiple combinations can yield the same maximum value
    weights = [2, 3, 4, 5, 2]
    values = [3, 4, 5, 6, 3]
    capacity = 7
    
    selected_indices = knapsack_lexicographical(weights, values, capacity)
    print("Selected original indices:", selected_indices)