def subset_sum_lex_min(nums, target):
    """
    Minimum-Cardinality Subset Sum with lexicographically smallest index list.

    Given `nums` (positive ints) and `target`, return the sorted list of
    0-based indices of a subset summing exactly to `target`, such that:
      1) it has the fewest elements possible, and
      2) among those, its sorted index list is lexicographically smallest.
    Returns None if no such subset exists. Returns [] if target == 0.
    """
    n = len(nums)

    if target == 0:
        return []
    if target < 0:
        return None

    IMPOSSIBLE = 255  # max cardinality <= n <= 200, fits in a byte

    # suf[i][s] = min cardinality using items i..n-1 to reach sum s.
    # 255 means impossible.
    suf = [bytearray([IMPOSSIBLE]) * (target + 1) for _ in range(n + 1)]
    suf[n][0] = 0

    for i in range(n - 1, -1, -1):
        # Start with "skip item i"
        suf[i][:] = suf[i + 1][:]
        num = nums[i]
        if num > target:
            continue
        # Read from suf[i+1] (source), write to suf[i] (dest) — safe.
        for s in range(target, num - 1, -1):
            prev = suf[i + 1][s - num]
            if prev != IMPOSSIBLE:
                cand = prev + 1
                if cand < suf[i][s]:
                    suf[i][s] = cand

    if suf[0][target] == IMPOSSIBLE:
        return None

    # Greedy forward reconstruction:
    # At each step, pick the smallest index i that can be part of *some*
    # minimum-cardinality solution using only items after i.
    remaining = target
    needed = suf[0][target]
    result = []
    for i in range(n):
        if needed == 0:
            break
        num = nums[i]
        if num <= remaining and suf[i + 1][remaining - num] == needed - 1:
            result.append(i)
            remaining -= num
            needed -= 1

    return result


if __name__ == "__main__":
    tests = [
        ([3, 34, 4, 12, 5, 2], 9, [2, 4]),   # 4 + 5 = 9, card 2
        ([1, 2, 3], 100, None),               # no solution
        ([1, 2, 3], 0, []),                   # empty subset
        ([1, 1, 1, 1], 2, [0, 1]),            # lex smallest pair
        ([1, 2, 2, 1], 3, [0, 1]),            # lex smallest pair
        ([1, 1, 1, 1, 1], 5, [0, 1, 2, 3, 4]),# all five
        ([2, 3, 5, 7], 10, [1, 3]),           # 3 + 7 = 10, card 2
        ([5, 1, 1, 1, 1], 5, [0]),            # single 5 at index 0
        ([1, 5, 1, 1, 1], 5, [1]),            # single 5 at index 1
    ]
    for nums, target, expected in tests:
        got = subset_sum_lex_min(nums, target)
        status = "OK" if got == expected else "FAIL"
        print(f"{status}: nums={nums}, target={target} -> {got} (expected {expected})")