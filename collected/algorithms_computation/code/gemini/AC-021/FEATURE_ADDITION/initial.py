def min_subset_sum_indices(nums: list[int], target: int) -> list[int] | None:
    """
    Finds a subset of indices whose elements sum to `target`.
    Optimizes for:
      1. Minimal number of elements (cardinality).
      2. Lexicographically smallest index list.
    """
    if target == 0:
        return []
    if target < 0:
        return None

    # dp[s] = (cardinality, index_list) for sum s
    dp = [None] * (target + 1)
    dp[0] = (0, [])

    for i, val in enumerate(nums):
        if val > target:
            continue
        
        # Iterate backward to prevent reusing the same item multiple times
        for s in range(target, val - 1, -1):
            prev = dp[s - val]
            if prev is not None:
                cand_card = prev[0] + 1
                cand_seq = prev[1] + [i]
                
                curr = dp[s]
                if curr is None:
                    dp[s] = (cand_card, cand_seq)
                else:
                    curr_card, curr_seq = curr
                    # Tie-breaking logic: 1. Smaller cardinality, 2. Lexicographically smaller sequence
                    if (cand_card < curr_card) or (cand_card == curr_card and cand_seq < curr_seq):
                        dp[s] = (cand_card, cand_seq)

    return dp[target][1] if dp[target] is not None else None


# --- Example Usage ---
if __name__ == "__main__":
    nums = [3, 2, 5, 8, 1, 4]
    target = 9

    result = min_subset_sum_indices(nums, target)
    print(f"Target: {target}")
    print(f"Array: {nums}")
    print(f"Indices: {result}")
    if result is not None:
        print(f"Elements: {[nums[i] for i in result]}")
        print(f"Sum: {sum(nums[i] for i in result)}")