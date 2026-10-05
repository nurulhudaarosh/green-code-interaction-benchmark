def subset_sum_lex_min(nums, target, return_summary=False):
    """
    Minimum-Cardinality Subset Sum with lexicographically smallest index list.

    Given `nums` (positive ints) and `target`, return the sorted list of
    0-based indices of a subset summing exactly to `target`, such that:
      1) it has the fewest elements possible, and
      2) among those, its sorted index list is lexicographically smallest.
    Returns None if no such subset exists. Returns [] if target == 0.

    If `return_summary=True`, also return a dict with an `operation_summary`
    field reporting deterministic operation counts.

    Original behavior is preserved exactly when `return_summary=False`.
    """
    n = len(nums)

    # Deterministic operation counters
    ops = {
        "dp_transition_attempts": 0,   # inner-loop iterations during DP build
        "reconstruction_steps": 0,     # index inspections during reconstruction
        "feasibility_checks": 0,       # final "is target reachable?" checks
    }

    # --- Trivial cases (still counted deterministically) ---
    if target == 0:
        ops["feasibility_checks"] += 1
        result = []
        if return_summary:
            return result, {"operation_summary": ops}
        return result

    if target < 0:
        ops["feasibility_checks"] += 1
        result = None
        if return_summary:
            return result, {"operation_summary": ops}
        return result

    IMPOSSIBLE = 255  # max cardinality <= n <= 200, fits in a byte

    # suf[i][s] = min cardinality using items i..n-1 to reach sum s.
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
            ops["dp_transition_attempts"] += 1
            prev = suf[i + 1][s - num]
            if prev != IMPOSSIBLE:
                cand = prev + 1
                if cand < suf[i][s]:
                    suf[i][s] = cand

    # Feasibility check on the full set
    ops["feasibility_checks"] += 1
    if suf[0][target] == IMPOSSIBLE:
        result = None
        if return_summary:
            return result, {"operation_summary": ops}
        return result

    # Greedy forward reconstruction: pick the smallest feasible index at each step.
    remaining = target
    needed = suf[0][target]
    result = []
    for i in range(n):
        if needed == 0:
            break
        ops["reconstruction_steps"] += 1
        num = nums[i]
        if num <= remaining and suf[i + 1][remaining - num] == needed - 1:
            result.append(i)
            remaining -= num
            needed -= 1

    if return_summary:
        return result, {"operation_summary": ops}
    return result


if __name__ == "__main__":
    tests = [
        ([3, 34, 4, 12, 5, 2], 9, [2, 4]),
        ([1, 2, 3], 100, None),
        ([1, 2, 3], 0, []),
        ([1, 1, 1, 1], 2, [0, 1]),
        ([1, 2, 2, 1], 3, [0, 1]),
        ([1, 1, 1, 1, 1], 5, [0, 1, 2, 3, 4]),
        ([2, 3, 5, 7], 10, [1, 3]),
        ([5, 1, 1, 1, 1], 5, [0]),
        ([1, 5, 1, 1, 1], 5, [1]),
    ]

    print("=== Original behavior (return_summary=False) ===")
    for nums, target, expected in tests:
        got = subset_sum_lex_min(nums, target)
        status = "OK" if got == expected else "FAIL"
        print(f"{status}: nums={nums}, target={target} -> {got} (expected {expected})")

    print("\n=== New feature (return_summary=True) ===")
    for nums, target, expected in tests:
        got, summary = subset_sum_lex_min(nums, target, return_summary=True)
        status = "OK" if got == expected else "FAIL"
        print(f"{status}: nums={nums}, target={target} -> {got} | {summary}")