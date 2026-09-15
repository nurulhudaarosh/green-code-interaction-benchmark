def knapsack_01(weights: list[int], values: list[int], capacity: int) -> list[int]:
    """
    Solves the 0/1 Knapsack problem and returns the lexicographically smallest
    list of original 0-based indices that achieve the maximum total value.

    :param weights: List of item weights (non-negative integers).
    :param values: List of item values (non-negative integers).
    :param capacity: Maximum total weight capacity of the knapsack.
    :return: Sorted list of chosen 0-based item indices.
    """
    n = len(weights)
    
    # dp[c] stores the maximum value achievable for capacity c
    dp = [0] * (capacity + 1)
    
    # chosen[c] stores the list of item indices achieving dp[c]
    chosen = [[] for _ in range(capacity + 1)]

    for i in range(n):
        w = weights[i]
        v = values[i]
        
        if w > capacity:
            continue
            
        # Iterate descending to avoid using the same item multiple times
        for c in range(capacity, w - 1, -1):
            new_val = dp[c - w] + v
            candidate_indices = chosen[c - w] + [i]
            
            # Check if this choice yields a strictly higher value, or a tie
            # with a lexicographically smaller list of indices.
            if new_val > dp[c]:
                dp[c] = new_val
                chosen[c] = candidate_indices
            elif new_val == dp[c] and new_val > 0:
                if candidate_indices < chosen[c]:
                    chosen[c] = candidate_indices

    # Find the capacity yielding the absolute maximum value
    max_val = max(dp)
    
    # Among all capacities reaching max_val, select the lexicographically smallest index list
    best_indices = None
    for c in range(capacity + 1):
        if dp[c] == max_val:
            if best_indices is None or chosen[c] < best_indices:
                best_indices = chosen[c]

    return best_indices if best_indices is not None else []


# --- Example Usage ---
if __name__ == "__main__":
    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 6]
    capacity = 5

    selected_indices = knapsack_01(weights, values, capacity)
    print(f"Selected item indices: {selected_indices}")
    print(f"Total value: {sum(values[i] for i in selected_indices)}")
    print(f"Total weight: {sum(weights[i] for i in selected_indices)}")