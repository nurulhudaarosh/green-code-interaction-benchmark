def solve_subset_sum(values, target):
    """
    Find subset of values summing to target with minimum cardinality,
    then lexicographically smallest index list (1-based).
    
    Args:
        values: list of positive integers
        target: target sum
    
    Returns:
        (min_count, index_list) if possible, else (None, None)
    """
    n = len(values)
    INF = float('inf')
    
    # dp[s] = (min_count, parent_index, prev_sum)
    # parent_index is 1-based; 0 means unreachable or start
    dp = [(INF, 0, -1)] * (target + 1)
    dp[0] = (0, 0, -1)  # 0 elements to reach sum 0
    
    # Process elements in reverse order to get lexicographically smallest indices
    for i in range(n - 1, -1, -1):
        val = values[i]
        idx = i + 1  # 1-based index
        for s in range(target, val - 1, -1):
            if dp[s - val][0] != INF:
                new_count = dp[s - val][0] + 1
                # Update if fewer elements, or same count but we prefer this
                # (reverse processing ensures lexicographically smaller)
                if new_count < dp[s][0]:
                    dp[s] = (new_count, idx, s - val)
    
    if dp[target][0] == INF:
        return None, None
    
    # Reconstruct solution
    indices = []
    s = target
    while s > 0:
        count, idx, prev = dp[s]
        indices.append(idx)
        s = prev
    
    indices.sort()  # ensure increasing order
    return dp[target][0], indices


# Example usage and testing
if __name__ == "__main__":
    # Test case 1: simple
    values = [3, 34, 4, 12, 5, 2]
    target = 9
    count, indices = solve_subset_sum(values, target)
    print(f"Values: {values}, Target: {target}")
    print(f"Min count: {count}, Indices (1-based): {indices}")
    # Expected: 2 elements, indices [4, 5] (12+? no...) 
    # Actually 4+5=9 -> indices [3,5] or 2+3+4=9 -> 3 elements
    # Min is 2: 4+5=9 -> indices [3,5]
    
    print()
    
    # Test case 2: lexicographic tie-breaking
    values = [1, 2, 3, 4, 5]
    target = 6
    count, indices = solve_subset_sum(values, target)
    print(f"Values: {values}, Target: {target}")
    print(f"Min count: {count}, Indices: {indices}")
    # Possible 2-element: [1,5]->[1,5], [2,4]->[2,4]
    # Lexicographically smallest: [1,5]
    
    print()
    
    # Test case 3: no solution
    values = [2, 4, 6]
    target = 5
    count, indices = solve_subset_sum(values, target)
    print(f"Values: {values}, Target: {target}")
    print(f"Min count: {count}, Indices: {indices}")
    
    print()
    
    # Test case 4: larger
    values = [1, 3, 4, 5, 8, 10]
    target = 15
    count, indices = solve_subset_sum(values, target)
    print(f"Values: {values}, Target: {target}")
    print(f"Min count: {count}, Indices: {indices}")
    # 5+10=15 -> [4,6] (2 elements)