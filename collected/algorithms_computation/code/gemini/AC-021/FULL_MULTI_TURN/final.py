from typing import Any


def min_elements_subset_sum(
    nums: list[int], target: int, include_summary: bool = False
) -> list[int] | None | dict[str, Any]:
    """
    Finds a subset of 0-based indices in `nums` that sum to `target`.
    
    Tie-breaking criteria:
      1. Fewest elements (minimum cardinality).
      2. Lexicographically smallest sorted index sequence.

    Handles boundary and disconnected cases explicitly:
      - target == 0: Returns []
      - target < 0 or unreachable (e.g. empty nums with target > 0): Returns None
    """
    metrics = {
        "states_inspected": 0,
        "candidates_evaluated": 0,
        "table_updates": 0,
    }

    # Case 1: Negative targets are invalid
    if target < 0:
        indices = None
        return {"indices": indices, "operation_summary": metrics} if include_summary else indices

    # Case 2: Target 0 is always achievable via empty set (size 0)
    if target == 0:
        indices = []
        return {"indices": indices, "operation_summary": metrics} if include_summary else indices

    # Case 3: Empty input with target > 0 is unreachable
    if not nums:
        indices = None
        return {"indices": indices, "operation_summary": metrics} if include_summary else indices

    # DP Table: dp[s] = (element_count, index_list) for sum s
    dp: list[tuple[int, list[int]] | None] = [None] * (target + 1)
    dp[0] = (0, [])

    for i, val in enumerate(nums):
        if val > target:
            continue

        for s in range(target, val - 1, -1):
            metrics["states_inspected"] += 1
            prev = dp[s - val]
            
            if prev is not None:
                metrics["candidates_evaluated"] += 1
                cand_count = prev[0] + 1
                cand_indices = prev[1] + [i]
                
                curr = dp[s]
                # Lexicographical comparison on tuple (cardinality, index_sequence)
                if curr is None or (cand_count, cand_indices) < (curr[0], curr[1]):
                    dp[s] = (cand_count, cand_indices)
                    metrics["table_updates"] += 1

    indices = dp[target][1] if dp[target] is not None else None

    if include_summary:
        return {
            "indices": indices,
            "operation_summary": metrics,
        }
    return indices


# =====================================================================
# Unit Tests
# =====================================================================

def run_tests():
    # 1. Target 0 with empty nums
    assert min_elements_subset_sum([], 0) == []

    # 2. Target > 0 with empty nums (disconnected structure)
    assert min_elements_subset_sum([], 5) is None

    # 3. Smallest input: single element match
    assert min_elements_subset_sum([7], 7) == [0]

    # 4. Smallest input: single element mismatch
    assert min_elements_subset_sum([7], 5) is None

    # 5. Negative target boundary
    assert min_elements_subset_sum([1, 2, 3], -1) is None

    # 6. Target unreachable (disconnected sum)
    assert min_elements_subset_sum([2, 4, 6], 5) is None

    # 7. Cardinality tie-breaking (prefer 1 element [4] over 2 elements [0, 1] for target 10)
    # arr = [2, 3, 5, 7, 10]
    assert min_elements_subset_sum([2, 3, 5, 7, 10], 10) == [4]

    # 8. Lexicographical tie-breaking (equal cardinality)
    # [3, 4, 3, 1] with target 7 -> [0, 1] (3+4) vs [1, 2] (4+3). [0, 1] < [1, 2]
    assert min_elements_subset_sum([3, 4, 3, 1], 7) == [0, 1]

    # 9. Feature toggle test (include_summary)
    res_with_summary = min_elements_subset_sum([3, 4, 3, 1], 7, include_summary=True)
    assert isinstance(res_with_summary, dict)
    assert res_with_summary["indices"] == [0, 1]
    assert "operation_summary" in res_with_summary
    assert res_with_summary["operation_summary"]["table_updates"] > 0

    print("All tests passed successfully!")


if __name__ == "__main__":
    run_tests()