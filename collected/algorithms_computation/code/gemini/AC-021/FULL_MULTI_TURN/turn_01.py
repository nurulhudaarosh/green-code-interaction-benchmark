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
        # Iterate backwards to prevent using the same element multiple times
        for s in range(target, val - 1, -1):
            prev = dp[s - val]
            if prev is not None:
                cand_count = prev[0] + 1
                cand_indices = prev[1] + [i]
                
                curr = dp[s]
                if curr is None or (cand_count, cand_indices) < (curr[0], curr[1]):
                    dp[s] = (cand_count, cand_indices)

    return dp[target][1] if dp[target] is not None else None


# Example Usage & Verification:
if __name__ == "__main__":
    arr = [2, 3, 5, 7, 10]
    t = 10
    res = min_elements_subset_sum(arr, t)
    print(f"Indices: {res}")  # Output: [4] (since arr[4] == 10 uses 1 element)

    arr2 = [3, 4, 3, 1]
    t2 = 7
    res2 = min_elements_subset_sum(arr2, t2)
    print(f"Indices: {res2}") # Output: [0, 1] (arr[0] + arr[1] = 3 + 4 = 7, size 2)