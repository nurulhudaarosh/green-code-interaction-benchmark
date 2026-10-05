def subset_sum_optimal(numbers: list[int], target: int) -> list[int] | None:
    """
    Finds a subset of positive integers that sums to target.
    
    Tie-breaking rules:
      1. Fewest elements (minimum cardinality)
      2. Lexicographically smallest 0-based index list
      
    Returns a sorted list of 0-based indices, or None if no solution exists.
    """
    if target < 0:
        return None
    if target == 0:
        return []
    if not numbers:
        return None

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
                if curr is None or (cand_count, cand_indices) < curr:
                    dp[s] = (cand_count, cand_indices)

    return dp[target][1] if dp[target] is not None else None


# =====================================================================
# Unit Tests
# =====================================================================

def run_tests():
    test_cases = [
        # (numbers, target, expected_output, description)
        
        # --- Minimal / Boundary Cases ---
        ([], 0, [], "Empty array with target 0"),
        ([], 5, None, "Empty array with positive target"),
        ([5], 0, [], "Non-empty array with target 0"),
        ([5], 5, [0], "Single element equal to target"),
        ([5], 3, None, "Single element unequal to target"),
        
        # --- Standard & Disconnected Cases ---
        ([1, 2, 3], 7, None, "Unreachable/disconnected target (sum of all elements < target)"),
        ([2, 4, 6], 5, None, "Unreachable/disconnected target (odd target with even numbers)"),
        ([3, 34, 4, 12, 5, 2], 9, [2, 4], "Standard case: 4 + 5 = 9 at indices [2, 4]"),
        
        # --- Tie-Breaking: Minimum Cardinality First ---
        # 10 can be made by [10] (1 element, idx 3) or [2, 3, 5] (3 elements, idx 0, 1, 2)
        ([2, 3, 5, 10], 10, [3], "Prefer fewer elements over earlier indices"),
        
        # --- Tie-Breaking: Lexicographical Index Order Second ---
        # 5 can be formed by [2, 3] at indices [0, 1] OR [2, 3] at indices [0, 2] OR [5] at index 3/4
        # Minimum cardinality = 1 element -> [3] (val 5 at idx 3) vs [4] (val 5 at idx 4) -> prefers [3]
        ([2, 3, 3, 5, 5], 5, [3], "Lexicographical tie-break among minimum cardinality"),
        # Equal length (2 elements): [1, 4] (indices [0, 3]) vs [2, 3] (indices [1, 2]) -> prefers [0, 3]
        ([1, 2, 3, 4], 5, [0, 3], "Lexicographical tie-break: [0, 3] < [1, 2]"),
        
        # --- Elements larger than target ---
        ([100, 200, 1, 2], 3, [2, 3], "Filter out elements larger than target"),
    ]

    passed = 0
    for idx, (nums, target, expected, desc) in enumerate(test_cases, 1):
        result = subset_sum_optimal(nums, target)
        assert result == expected, f"Test {idx} Failed ({desc}): Expected {expected}, got {result}"
        passed += 1
        print(f"Test {idx} Passed: {desc} -> Output: {result}")

    print(f"\nAll {passed}/{len(test_cases)} tests passed successfully.")


if __name__ == "__main__":
    run_tests()