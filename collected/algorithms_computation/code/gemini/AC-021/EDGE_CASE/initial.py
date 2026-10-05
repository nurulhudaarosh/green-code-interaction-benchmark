def subset_sum_optimal(numbers: list[int], target: int) -> list[int] | None:
    """
    Finds a subset of positive integers that sums to target.
    Breaks ties by:
      1. Fewest elements
      2. Lexicographically smallest 0-based index list
    """
    if target < 0:
        return None
    if target == 0:
        return []

    # dp[s] = (count, indices)
    dp: list[tuple[int, list[int]] | None] = [None] * (target + 1)
    dp[0] = (0, [])

    for i, v in enumerate(numbers):
        if v > target:
            continue
        for s in range(target, v - 1, -1):
            prev = dp[s - v]
            if prev is not None:
                cand_count = prev[0] + 1
                cand_indices = prev[1] + [i]

                curr = dp[s]
                if curr is None:
                    dp[s] = (cand_count, cand_indices)
                else:
                    curr_count, curr_indices = curr
                    # Compare cardinality first, then lexicographical index list
                    if (cand_count, cand_indices) < (curr_count, curr_indices):
                        dp[s] = (cand_count, cand_indices)

    return dp[target][1] if dp[target] is not None else None


# Example usage
if __name__ == "__main__":
    nums = [3, 34, 4, 12, 5, 2]
    tgt = 9
    indices = subset_sum_optimal(nums, tgt)
    print(f"Indices: {indices}")
    if indices is not None:
        print(f"Values: {[nums[i] for i in indices]}")
        print(f"Sum: {sum(nums[i] for i in indices)}")