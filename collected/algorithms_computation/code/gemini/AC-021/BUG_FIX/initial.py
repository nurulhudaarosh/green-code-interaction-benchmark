def find_optimal_subset(nums: list[int], target: int) -> list[int] | None:
    """
    Finds a subset of positive integers from `nums` that sums to `target`.
    
    Optimizes by:
    1. Fewest elements (minimal cardinality).
    2. Lexicographically smallest list of 0-based indices.
    
    Returns the sorted list of indices, or None if no valid subset exists.
    """
    if target == 0:
        return []
    if target < 0:
        return None

    # dp[s] = (cardinality, tuple_of_indices) or None
    dp: list[tuple[int, tuple[int, ...]] | None] = [None] * (target + 1)
    dp[0] = (0, ())

    for i, num in enumerate(nums):
        if num > target:
            continue
        
        # Traverse backwards for 0/1 knapsack
        for s in range(target, num - 1, -1):
            prev_state = dp[s - num]
            if prev_state is not None:
                cand_count = prev_state[0] + 1
                cand_indices = prev_state[1] + (i,)
                cand_state = (cand_count, cand_indices)

                # Lexicographical comparison on tuple (count, indices)
                if dp[s] is None or cand_state < dp[s]:
                    dp[s] = cand_state

    if dp[target] is None:
        return None
    
    return list(dp[target][1])


# Example Usage & Test
if __name__ == "__main__":
    test_nums = [3, 1, 4, 2, 2, 5]
    test_target = 6
    
    result = find_optimal_subset(test_nums, test_target)
    print(f"Numbers: {test_nums}")
    print(f"Target: {test_target}")
    print(f"Optimal Indices: {result}")
    if result is not None:
        print(f"Selected Values: {[test_nums[i] for i in result]}")