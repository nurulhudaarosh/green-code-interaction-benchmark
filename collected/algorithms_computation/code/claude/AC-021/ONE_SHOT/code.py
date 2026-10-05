from typing import List, Optional, Sequence, Tuple


def min_cardinality_subset(nums: Sequence[int], target: int) -> Optional[List[int]]:
    """Return ascending indices of a subset of `nums` summing to `target`,
    with the fewest elements, ties broken by lexicographically smallest
    index list. Return None if impossible."""
    if target < 0:
        raise ValueError("target must be non-negative")
    for x in nums:
        if not isinstance(x, int) or isinstance(x, bool) or x <= 0:
            raise ValueError("all numbers must be positive integers")

    # dp[s] = (count, index_tuple) using items processed so far, or None.
    dp: List[Optional[Tuple[int, Tuple[int, ...]]]] = [None] * (target + 1)
    dp[0] = (0, ())

    # Process from the last index to the first so prepending keeps order.
    for i in range(len(nums) - 1, -1, -1):
        a = nums[i]
        if a > target:
            continue
        for s in range(target, a - 1, -1):  # descending => 0/1 usage
            prev = dp[s - a]
            if prev is None:
                continue
            cand = (prev[0] + 1, (i,) + prev[1])
            cur = dp[s]
            if cur is None or cand < cur:
                dp[s] = cand

    best = dp[target]
    return None if best is None else list(best[1])


if __name__ == "__main__":
    tests = [
        ([3, 34, 4, 12, 5, 2], 9, [2, 4]),          # 4 + 5
        ([5, 5, 5, 10], 10, [3]),                   # single element beats 5+5
        ([2, 3, 5, 5], 10, [2, 3]),                 # 5 + 5
        ([1, 2, 3, 4], 5, [0, 3]),                  # 1+4 beats 2+3 lexicographically
        ([7, 8], 0, []),                            # empty subset
        ([2, 4, 6], 5, None),                       # impossible
        ([], 3, None),
    ]
    for nums, t, expected in tests:
        got = min_cardinality_subset(nums, t)
        assert got == expected, (nums, t, got, expected)
        print(nums, t, "->", got)