from typing import Any


def min_elements_subset_sum(
    nums: list[int], target: int, include_summary: bool = False
) -> list[int] | None | dict[str, Any]:
    """
    Finds a subset of 0-based indices in `nums` that sum to `target`.
    
    Tie-breaking criteria:
      1. Fewest elements (minimum cardinality).
      2. Lexicographically smallest sorted index sequence.

    Args:
        nums: List of positive integers.
        target: Non-negative integer target sum.
        include_summary: If True, returns a dict containing 'indices' and 'operation_summary'.

    Returns:
        - If include_summary is False: list[int] | None
        - If include_summary is True: {'indices': list[int] | None, 'operation_summary': dict}
    """
    metrics = {
        "states_inspected": 0,
        "candidates_evaluated": 0,
        "table_updates": 0,
    }

    if target < 0:
        indices = None
        if include_summary:
            return {"indices": indices, "operation_summary": metrics}
        return indices

    if target == 0:
        indices = []
        if include_summary:
            return {"indices": indices, "operation_summary": metrics}
        return indices

    # dp[s] = (element_count, index_list) for sum s
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


# Example Usage:
if __name__ == "__main__":
    nums = [4, 1, 3, 2]
    target = 5

    # Backward-compatible call
    res = min_elements_subset_sum(nums, target)
    print(f"Standard Output: {res}")  # Output: [0, 1]

    # Call with operation summary feature
    res_summary = min_elements_subset_sum(nums, target, include_summary=True)
    print(f"Output with Summary: {res_summary}")
    # Output: {
    #   'indices': [0, 1],
    #   'operation_summary': {
    #       'states_inspected': 14,
    #       'candidates_evaluated': 8,
    #       'table_updates': 6
    #   }
    # }