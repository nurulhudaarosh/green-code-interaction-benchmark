from typing import List, Optional


def _is_int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def min_card_lex_subset(nums: List[int], target: int) -> Optional[List[int]]:
    """Return ascending indices of a subset of nums summing to target,
    with minimum cardinality, then lexicographically smallest index list.
    Return None if impossible. Raise ValueError on invalid input."""
    if not _is_int(target) or target < 0:
        raise ValueError("target must be a non-negative integer")
    if any(not _is_int(x) or x <= 0 for x in nums):
        raise ValueError("nums must contain only positive integers")

    n = len(nums)
    INF = n + 1  # more than any possible subset size

    # cnt[i][s]: min elements from nums[i:] summing to s (INF if impossible)
    cnt = [[INF] * (target + 1) for _ in range(n + 1)]
    cnt[n][0] = 0

    for i in range(n - 1, -1, -1):
        a = nums[i]
        nxt, cur = cnt[i + 1], cnt[i]
        for s in range(target + 1):
            best = nxt[s]                          # skip item i
            if s >= a and nxt[s - a] + 1 < best:
                best = nxt[s - a] + 1              # take item i
            cur[s] = best

    if cnt[0][target] >= INF:
        return None

    # Greedy reconstruction: taking the smallest feasible index first
    # yields the lexicographically smallest optimal list.
    result, s = [], target
    for i in range(n):
        if s == 0:
            break
        a = nums[i]
        if s >= a and cnt[i + 1][s - a] + 1 == cnt[i][s]:
            result.append(i)
            s -= a
    return result


if __name__ == "__main__":
    tests = [
        ([3, 34, 4, 12, 5, 2], 9, [2, 4]),
        ([1, 2, 3, 4], 5, [0, 3]),
        ([5, 5, 5], 10, [0, 1]),
        ([2, 4], 7, None),
        ([7], 0, []),
        ([], 0, []),
        ([1, 1, 1, 1], 3, [0, 1, 2]),
        ([2, 3, 5, 7], 12, [2, 3]),
    ]
    for nums, t, expected in tests:
        assert min_card_lex_subset(nums, t) == expected, (nums, t)

    for bad in [([True, 2], 3), ([1, 2], True), ([1, 2], 2.0),
                ([1, 2], "3"), ([0, 1], 1), ([1], -1)]:
        try:
            min_card_lex_subset(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"should have rejected {bad}")
    print("All tests passed.")