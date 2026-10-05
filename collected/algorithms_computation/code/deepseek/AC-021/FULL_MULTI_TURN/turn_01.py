def subset_sum_lex_min(nums, target):
    """
    Find a subset of `nums` (0/1 knapsack) summing to `target`.
    Tie-break: fewest elements, then lexicographically smallest sorted index list.

    Returns list of indices (ascending) or None if no solution exists.
    """
    n = len(nums)

    # target == 0 -> empty subset is the unique optimal solution
    if target == 0:
        return []

    # dp_suffix[i][s] = min cardinality using items i..n-1 to reach sum s.
    # 255 means "impossible". Max cardinality <= n <= 200, fits in a byte.
    IMPOSSIBLE = 255
    dp_suffix = [bytearray([IMPOSSIBLE]) * (target + 1) for _ in range(n + 1)]
    dp_suffix[n][0] = 0

    for i in range(n - 1, -1, -1):
        # Start with "skip item i" option
        dp_suffix[i][:] = dp_suffix[i + 1][:]
        num = nums[i]
        if num > target:
            continue
        # Read source from dp_suffix[i+1] to avoid reusing item i.
        # Since dp_suffix[i] is a copy of dp_suffix[i+1] before updates,
        # we can safely iterate s descending and update in place.
        for s in range(target, num - 1, -1):
            prev = dp_suffix[i + 1][s - num]
            if prev != IMPOSSIBLE:
                cand = prev + 1
                if cand < dp_suffix[i][s]:
                    dp_suffix[i][s] = cand

    if dp_suffix[0][target] == IMPOSSIBLE:
        return None

    # Greedy reconstruction: at each step pick the smallest feasible index.
    remaining = target
    needed = dp_suffix[0][target]
    result = []
    for i in range(n):
        if needed == 0:
            break
        num = nums[i]
        if num <= remaining and dp_suffix[i + 1][remaining - num] == needed - 1:
            result.append(i)
            remaining -= num
            needed -= 1

    return result


if __name__ == "__main__":
    # Example 1
    nums = [3, 34, 4, 12, 5, 2]
    target = 9
    print("Example 1:", subset_sum_lex_min(nums, target))  # [2, 4] -> 4 + 5 = 9

    # Example 2: no solution
    print("Example 2:", subset_sum_lex_min([1, 2, 3], 100))  # None

    # Example 3: target == 0
    print("Example 3:", subset_sum_lex_min([1, 2, 3], 0))  # []

    # Example 4: lexicographic tie-break demo
    # nums = [1, 1, 1, 1], target = 2 -> min cardinality 2.
    # Possible index pairs: [0,1], [0,2], [0,3], [1,2], [1,3], [2,3]
    # Lexicographically smallest: [0, 1]
    print("Example 4:", subset_sum_lex_min([1, 1, 1, 1], 2))  # [0, 1]