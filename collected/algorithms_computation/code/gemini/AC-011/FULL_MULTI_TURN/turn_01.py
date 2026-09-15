def knapsack_01(weights: list[int], values: list[int], capacity: int) -> list[int]:
    """
    Solves the 0/1 Knapsack problem deterministically.
    
    Returns the list of original indices of selected items that maximize 
    total value within the given capacity. Ties are broken by choosing 
    the lexicographically smallest list of indices.
    """
    n = len(weights)
    
    # dp[w] stores a tuple: (max_value, sorted_list_of_selected_indices)
    dp = [(0, []) for _ in range(capacity + 1)]
    
    for i in range(n):
        w_i, v_i = weights[i], values[i]
        
        # Traverse capacities in reverse to ensure 0/1 item usage
        for w in range(capacity, w_i - 1, -1):
            prev_val, prev_indices = dp[w - w_i]
            cand_val = prev_val + v_i
            cand_indices = prev_indices + [i]
            
            curr_val, curr_indices = dp[w]
            
            # Update DP table if candidate provides higher value,
            # or equal value with a lexicographically smaller index list
            if cand_val > curr_val:
                dp[w] = (cand_val, cand_indices)
            elif cand_val == curr_val:
                if cand_indices < curr_indices:
                    dp[w] = (cand_val, cand_indices)

    # Find the maximum value achieved across all capacities w <= capacity
    best_val = -1
    best_indices = []
    
    for w in range(capacity + 1):
        val, indices = dp[w]
        if val > best_val:
            best_val = val
            best_indices = indices
        elif val == best_val and val > 0:
            if indices < best_indices:
                best_indices = indices
                
    return best_indices


# Example Usage
if __name__ == "__main__":
    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 6]
    capacity = 5
    
    selected_indices = knapsack_01(weights, values, capacity)
    print(f"Selected Item Indices: {selected_indices}")