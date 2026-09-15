def knapsack_01(weights: list[int], values: list[int], capacity: int) -> list[int]:
    """
    Solves the 0/1 Knapsack problem using descending dynamic programming updates.
    Returns the lexicographically smallest list of original 0-based indices
    that achieves the maximum total value under the capacity constraint.
    """
    n = len(weights)
    
    # dp[c] stores (-max_value, sorted_list_of_indices)
    # Using negative value allows tuple comparison to naturally prioritize 
    # higher values first, then lexicographically smaller index lists.
    dp = [(-0, []) for _ in range(capacity + 1)]

    for i in range(n):
        w = weights[i]
        v = values[i]
        
        if w > capacity:
            continue
            
        # Descending capacity update to prevent picking the same item multiple times
        for c in range(capacity, w - 1, -1):
            prev_val, prev_indices = dp[c - w]
            candidate = (prev_val - v, prev_indices + [i])
            
            # Tuple comparison naturally handles:
            # 1. Higher value (-value is smaller)
            # 2. Lexicographically smaller index set on value ties
            if candidate < dp[c]:
                dp[c] = candidate

    # Find the globally optimal tuple across all valid capacities [0..capacity]
    best_neg_val, best_indices = min(dp)
    
    return best_indices


# --- Verification ---
if __name__ == "__main__":
    # Test 1: Zero-value tie-breaker test
    w1, v1, cap1 = [1, 1], [0, 0], 1
    res1 = knapsack_01(w1, v1, cap1)
    print(f"Test 1 Result: {res1} (Expected: [])")
    assert res1 == [], f"Failed Test 1: got {res1}"

    # Test 2: Standard tie-breaker test
    w2, v2, cap2 = [2, 2, 1, 1], [3, 3, 2, 1], 3
    # Candidate value 5: indices [0, 2] (weight 3) vs [1, 2] (weight 3)
    res2 = knapsack_01(w2, v2, cap2)
    print(f"Test 2 Result: {res2} (Expected: [0, 2])")
    assert res2 == [0, 2], f"Failed Test 2: got {res2}"

    print("All tests passed successfully!")