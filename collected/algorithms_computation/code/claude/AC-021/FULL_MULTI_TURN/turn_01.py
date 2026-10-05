from typing import List, Optional, Tuple


def min_count_lex_smallest_subset(nums: List[int], target: int) -> Optional[List[int]]:
    """Return ascending 0-based indices of a subset of `nums` summing to `target`,
    with minimum cardinality, ties broken by lexicographically smallest index list.
    Return None if impossible."""
    if target < 0:
        return None
    if target == 0:
        return []

    # dp[s] = (count, indices_tuple) or None, using items processed so far.
    dp: List[Optional[Tuple[int, Tuple[int, ...]]]] = [None] * (target + 1)
    dp[0] = (0, ())

    # Process items from last to first so the newly added index is always the smallest.
    for i in range(len(nums) - 1, -1, -1):
        a = nums[i]
        if a <= 0 or a > target:
            continue  # positives only per the spec; skip anything unusable
        # Descending sums => 0/1 semantics (dp[s - a] still reflects items > i).
        for s in range(target, a - 1, -1):
            prev = dp[s - a]
            if prev is None:
                continue
            cand = (prev[0] + 1, (i,) + prev[1])
            cur = dp[s]
            if cur is None or cand < cur:
                dp[s] = cand

    best = dp[target]
    return list(best[1]) if best is not None else None


if __name__ == "__main__":
    tests = [
        ([3, 34, 4, 12, 5, 2], 9, [2, 4]),     # 4+5 (two elements) beats 3+4+2
        ([1, 2, 3, 4], 5, [0, 3]),             # 1+4 and 2+3 tie; [0,3] < [1,2]
        ([5, 5, 5], 10, [0, 1]),               # equal values: smallest indices
        ([2, 4, 6], 5, None),                  # impossible
        ([7], 0, []),                          # empty subset
        ([1, 1, 1, 1, 4], 4, [4]),             # single element beats four 1s
    ]
    for nums, t, expected in tests:
        got = min_count_lex_smallest_subset(nums, t)
        assert got == expected, (nums, t, got, expected)
        print(f"nums={nums}, target={t} -> {got}")