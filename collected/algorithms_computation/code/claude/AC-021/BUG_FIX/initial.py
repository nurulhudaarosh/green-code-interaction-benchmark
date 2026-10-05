from typing import List, Optional


def min_card_lex_subset(nums: List[int], target: int) -> Optional[List[int]]:
    """Return ascending indices of a subset of nums summing to target,
    with minimum cardinality, then lexicographically smallest index list.
    Return None if impossible."""
    if target < 0 or any((not isinstance(x, int)) or x <= 0 for x in nums):
        raise ValueError("nums must be positive integers and target >= 0")

    n = len(nums)
    INF = float("inf")

    # cnt[i][s]: min elements from nums[i:] summing to s
    cnt = [[INF] * (target + 1) for _ in range(n + 1)]
    cnt[n][0] = 0

    for i in range(n - 1, -1, -1):
        a = nums[i]
        nxt, cur = cnt[i + 1], cnt[i]
        for s in range(target + 1):
            best = nxt[s]                      # skip item i
            if s >= a and nxt[s - a] + 1 < best:
                best = nxt[s - a] + 1          # take item i
            cur[s] = best

    if cnt[0][target] == INF:
        return None

    result, s = [], target
    for i in range(n):
        if s == 0:
            break
        a = nums[i]
        if s >= a and cnt[i + 1][s - a] + 1 == cnt[i][s]:
            result.append(i)                   # taking i keeps optimality
            s -= a
    return result


if __name__ == "__main__":
    tests = [
        ([3, 34, 4, 12, 5, 2], 9, [2, 4]),   # 4 + 5
        ([1, 2, 3, 4], 5, [0, 3]),           # {1,4} beats {2,3} by index
        ([5, 5, 5], 10, [0, 1]),
        ([2, 4], 7, None),
        ([7], 0, []),
        ([1, 1, 1, 1], 3, [0, 1, 2]),
        ([2, 3, 5, 7], 12, [2, 3]),          # 5 + 7, two elements
    ]
    for nums, t, expected in tests:
        got = min_card_lex_subset(nums, t)
        assert got == expected, (nums, t, got, expected)
    print("All tests passed.")