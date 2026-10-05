from typing import List, Optional


def subset_sum_fewest_lex_smallest(nums: List[int], target: int) -> Optional[List[int]]:
    """
    Return indices of a subset of nums summing exactly to target.

    Selection rules:
      1. fewest elements
      2. lexicographically smallest index list among those

    Returns None if no such subset exists.
    """
    if target < 0:
        return None
    if target == 0:
        return []

    n = len(nums)

    # dp[s] = best index list for sum s, or None if unreachable.
    # best = (minimum length, lexicographically smallest list)
    dp: List[Optional[List[int]]] = [None] * (target + 1)
    dp[0] = []

    for i, x in enumerate(nums):
        if x <= 0:
            continue
        # Traverse downward so item i is used at most once.
        for s in range(target, x - 1, -1):
            if dp[s - x] is None:
                continue

            candidate = dp[s - x] + [i]

            if dp[s] is None:
                dp[s] = candidate
            else:
                current = dp[s]
                # Compare by length first, then lexicographically.
                if len(candidate) < len(current) or (
                    len(candidate) == len(current) and candidate < current
                ):
                    dp[s] = candidate

    return dp[target]


if __name__ == "__main__":
    # Deterministic examples
    examples = [
        ([3, 34, 4, 12, 5, 2], 9),
        ([1, 2, 3, 4, 5], 10),
        ([2, 3, 7, 8, 10], 11),
        ([1, 1, 1, 1], 3),
        ([5, 6, 7], 20),
    ]

    for nums, target in examples:
        result = subset_sum_fewest_lex_smallest(nums, target)
        if result is None:
            print(f"nums={nums}, target={target} -> no solution")
        else:
            chosen = [nums[i] for i in result]
            print(
                f"nums={nums}, target={target} -> indices={result}, "
                f"values={chosen}, sum={sum(chosen)}"
            )