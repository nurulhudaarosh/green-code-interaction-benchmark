def subset_sum_lex_min(nums, target, return_summary=False):
    """
    Minimum-Cardinality Subset Sum with lexicographically smallest index list.

    Given `nums` (positive ints) and `target`, return the sorted list of
    0-based indices of a subset summing exactly to `target`, such that:
      1) it has the fewest elements possible, and
      2) among those, its sorted index list is lexicographically smallest.
    Returns None if no such subset exists. Returns [] if target == 0.

    If `return_summary=True`, also returns a dict with an `operation_summary`
    field reporting deterministic operation counts.

    Original behavior is preserved exactly when `return_summary=False`.
    """
    n = len(nums)

    ops = {
        "dp_transition_attempts": 0,
        "reconstruction_steps": 0,
        "feasibility_checks": 0,
    }

    # --- Trivial / edge cases -------------------------------------------
    # Empty nums, or target == 0 -> [] is the unique minimal-cardinality solution.
    if target == 0:
        ops["feasibility_checks"] += 1
        result = []
        if return_summary:
            return result, {"operation_summary": ops}
        return result

    # Negative target is not meaningful for positive-integer inputs.
    if target < 0:
        ops["feasibility_checks"] += 1
        result = None
        if return_summary:
            return result, {"operation_summary": ops}
        return result

    # Empty nums but positive target -> infeasible.
    if n == 0:
        ops["feasibility_checks"] += 1
        result = None
        if return_summary:
            return result, {"operation_summary": ops}
        return result
    # -------------------------------------------------------------------

    IMPOSSIBLE = 255  # max cardinality <= n <= 200, fits in a byte

    # suf[i][s] = min cardinality using items i..n-1 to reach sum s.
    suf = [bytearray([IMPOSSIBLE]) * (target + 1) for _ in range(n + 1)]
    suf[n][0] = 0

    for i in range(n - 1, -1, -1):
        suf[i][:] = suf[i + 1][:]
        num = nums[i]
        # Skip elements larger than target: they cannot be in any solution.
        if num > target or num <= 0:
            continue
        for s in range(target, num - 1, -1):
            ops["dp_transition_attempts"] += 1
            prev = suf[i + 1][s - num]
            if prev != IMPOSSIBLE:
                cand = prev + 1
                if cand < suf[i][s]:
                    suf[i][s] = cand

    ops["feasibility_checks"] += 1
    if suf[0][target] == IMPOSSIBLE:
        result = None
        if return_summary:
            return result, {"operation_summary": ops}
        return result

    # Greedy forward reconstruction: smallest feasible index at each step.
    remaining = target
    needed = suf[0][target]
    result = []
    for i in range(n):
        if needed == 0:
            break
        ops["reconstruction_steps"] += 1
        num = nums[i]
        if num <= 0:
            continue
        if num <= remaining and suf[i + 1][remaining - num] == needed - 1:
            result.append(i)
            remaining -= num
            needed -= 1

    if return_summary:
        return result, {"operation_summary": ops}
    return result


if __name__ == "__main__":
    # ------------------- Existing behavior tests -------------------
    print("=== Existing behavior tests ===")
    base_tests = [
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
    for nums, target, expected in base_tests:
        got = subset_sum_lex_min(nums, target)
        status = "OK" if got == expected else "FAIL"
        print(f"{status}: nums={nums}, target={target} -> {got} (expected {expected})")

    # ------------------- Difficult / edge-case tests -------------------
    print("\n=== Difficult / edge-case tests ===")
    edge_tests = [
        # (nums, target, expected, description)

        # Smallest permitted inputs
        ([], 0, [], "empty nums, target=0"),
        ([], 1, None, "empty nums, positive target (infeasible)"),
        ([], -1, None, "empty nums, negative target"),
        ([1], 0, [], "single element, target=0"),
        ([1], 1, [0], "single element equals target"),
        ([1], 2, None, "single element less than target"),
        ([5], 3, None, "single element greater than target"),

        # Empty / disconnected structures
        ([10, 20, 30], 5, None, "all elements > target (disconnected)"),
        ([10, 20, 30], 30, [2], "only largest element matches target"),
        ([1, 2, 3], -5, None, "negative target with non-empty nums"),

        # Tie-breaking with duplicates
        ([1, 1, 1, 1, 1], 3, [0, 1, 2], "many 1s, lex smallest triple"),
        ([2, 1, 1, 1], 3, [0, 1], "2+1=3, lex smallest is [0,1] not [1,2]"),
        ([1, 2, 1, 2], 3, [0, 1], "1+2=3, lex smallest [0,1]"),
        ([3, 1, 1, 1], 3, [0], "single 3 beats three 1s (cardinality wins)"),
        ([1, 1, 1, 3], 3, [3], "single 3 at end wins over three 1s"),

        # Elements exceeding target mixed with valid ones
        ([100, 1, 2, 3], 5, [1, 2, 3], "skip huge element, use 1+2+? no; 2+3=5"),
        ([100, 2, 3, 1], 5, [1, 2], "2+3=5 lex smallest [1,2]"),
        ([100, 1, 4], 5, [1, 2], "1+4=5"),

        # Exact target present multiple times
        ([2, 2, 2], 2, [0], "target matches first element"),
        ([1, 2, 2], 2, [1], "target matches index 1"),
        ([2, 2, 1], 2, [0], "target matches index 0"),

        # Cardinality priority over lexicographic order
        ([1, 1, 1, 1, 5], 5, [4], "cardinality 1 beats cardinality 5"),
        ([1, 1, 1, 1, 2, 3], 5, [4, 5], "2+3=5 card 2 beats 5x1 card 5"),
    ]

    all_ok = True
    for nums, target, expected, desc in edge_tests:
        got = subset_sum_lex_min(nums, target)
        ok = (got == expected)
        all_ok = all_ok and ok
        status = "OK" if ok else "FAIL"
        print(f"{status}: {desc} | nums={nums}, target={target} -> {got} (expected {expected})")

    # ------------------- Operation summary feature -------------------
    print("\n=== Operation summary feature ===")
    got, summary = subset_sum_lex_min([3, 34, 4, 12, 5, 2], 9, return_summary=True)
    print(f"nums=[3,34,4,12,5,2], target=9 -> {got} | {summary}")

    got, summary = subset_sum_lex_min([], 0, return_summary=True)
    print(f"nums=[], target=0 -> {got} | {summary}")

    got, summary = subset_sum_lex_min([100, 200], 50, return_summary=True)
    print(f"nums=[100,200], target=50 -> {got} | {summary}")

    print(f"\nAll edge tests passed: {all_ok}")