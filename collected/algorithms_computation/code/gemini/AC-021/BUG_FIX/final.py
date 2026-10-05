def find_optimal_subset(nums: list[int], target: int) -> list[int] | None:
    """
    Finds a subset of positive integers from `nums` that sums to `target`.
    
    Optimizes by:
    1. Minimal cardinality (fewest elements).
    2. Lexicographically smallest list of 0-based indices.
    
    Returns a sorted list of indices, or None if no valid subset exists.
    """
    if target == 0:
        return []
    if target < 0 or not nums:
        return None

    # dp[s] stores (cardinality, tuple_of_indices) for sum s
    dp: list[tuple[int, tuple[int, ...]] | None] = [None] * (target + 1)
    dp[0] = (0, ())

    for i, num in enumerate(nums):
        if num > target:
            continue
        
        # Traverse backwards to ensure 0/1 (each item used at most once)
        for s in range(target, num - 1, -1):
            prev = dp[s - num]
            if prev is not None:
                cand_count = prev[0] + 1
                cand_indices = prev[1] + (i,)
                cand_state = (cand_count, cand_indices)

                current = dp[s]
                if current is None or cand_state < current:
                    dp[s] = cand_state

    return list(dp[target][1]) if dp[target] is not None else None