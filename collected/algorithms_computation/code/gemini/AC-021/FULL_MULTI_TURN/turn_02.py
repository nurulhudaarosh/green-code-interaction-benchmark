def min_elements_subset_sum(nums: list[int], target: int) -> list[int] | None:
    """
    Finds a subset of 0-based indices in `nums` that sum to `target`.
    Tie-breaking criteria:
      1. Fewest elements (minimum cardinality).
      2. Lexicographically smallest sorted index sequence.
    Returns None if no subset sums to `target`.
    """
    if target == 0:
        return []
    if target < 0:
        return None

    # dp[s] = (element_count, index_list) for sum s
    dp: list[tuple[int, list[int]] | None] = [None] * (target + 1)
    dp[0] = (0, [])

    for i, val in enumerate(nums):
        if val > target:
            continue
        # Outer loop processes indices in increasing order 0..n-1.
        # Inner loop iterates backwards to enforce 0/1 knapsack constraint.
        for s in range(target, val - 1, -1):
            prev = dp[s - val]
            if prev is not None:
                cand_count = prev[0] + 1
                cand_indices = prev[1] + [i]
                
                curr = dp[s]
                # Compare by (cardinality, index_sequence)
                if curr is None or (cand_count, cand_indices) < (curr[0], curr[1]):
                    dp[s] = (cand_count, cand_indices)

    return dp[target][1] if dp[target] is not None else None