from typing import List, Optional, Dict, Any


def subset_sum_fewest_lex_smallest(
    nums: List[int],
    target: int,
    return_operation_summary: bool = False,
) -> Any:
    """
    Return indices of a subset of nums summing exactly to target.

    Selection rules:
      1. fewest elements
      2. lexicographically smallest index list among those

    Returns:
      - None if no such subset exists, unless operation summary is requested.
      - Otherwise, the index list by default.
      - If return_operation_summary=True, returns a dict with:
          {
              "indices": List[int] or None,
              "operation_summary": {
                  "major_operations": int
              }
          }
    """
    if target < 0:
        result = None
        if return_operation_summary:
            return {
                "indices": result,
                "operation_summary": {"major_operations": 0},
            }
        return result

    if target == 0:
        result = []
        if return_operation_summary:
            return {
                "indices": result,
                "operation_summary": {"major_operations": 0},
            }
        return result

    n = len(nums)

    dp: List[Optional[List[int]]] = [None] * (target + 1)
    dp[0] = []

    major_operations = 0

    for i, x in enumerate(nums):
        if x <= 0:
            continue

        for s in range(target, x - 1, -1):
            if dp[s - x] is None:
                continue

            # One major computational decision:
            # consider extending a reachable previous sum with item i.
            major_operations += 1

            candidate = dp[s - x] + [i]

            if dp[s] is None:
                dp[s] = candidate
            else:
                current = dp[s]
                if len(candidate) < len(current) or (
                    len(candidate) == len(current) and candidate < current
                ):
                    dp[s] = candidate

    result = dp[target]

    if return_operation_summary:
        return {
            "indices": result,
            "operation_summary": {"major_operations": major_operations},
        }
    return result


if __name__ == "__main__":
    examples = [
        ([3, 34, 4, 12, 5, 2], 9),
        ([1, 2, 3, 4, 5], 10),
        ([2, 3, 7, 8, 10], 11),
        ([1, 1, 1, 1], 3),
        ([5, 6, 7], 20),
    ]

    for nums, target in examples:
        result = subset_sum_fewest_lex_smallest(
            nums, target, return_operation_summary=True
        )
        indices = result["indices"]
        ops = result["operation_summary"]["major_operations"]

        if indices is None:
            print(f"nums={nums}, target={target} -> no solution, major_operations={ops}")
        else:
            chosen = [nums[i] for i in indices]
            print(
                f"nums={nums}, target={target} -> indices={indices}, "
                f"values={chosen}, sum={sum(chosen)}, major_operations={ops}"
            )