"""
Minimum-Cardinality 0/1 Subset Sum with lexicographically smallest index list.

Problem:
    Given positive integers `values` and a target integer, find a subset
    summing exactly to target such that:
      1) The subset has the fewest elements (minimum cardinality).
      2) Among those, the 1-based index list (increasing order) is
         lexicographically smallest.
    If no subset sums to target, return (None, None).

Approach:
    0/1 subset-sum DP storing the reconstruction sequence per reachable sum.
    Descending s guarantees each item is used at most once.
    Update rule compares (cardinality, index_list) lexicographically.
"""


def solve_subset_sum(values, target):
    if target < 0:
        return None, None

    n = len(values)
    # dp[s] = None if unreachable, else list of 1-based indices for best solution of sum s
    dp = [None] * (target + 1)
    dp[0] = []

    for i in range(n):
        val = values[i]
        idx = i + 1
        if val > target:
            continue
        # Descending s to enforce 0/1 (each item at most once)
        for s in range(target, val - 1, -1):
            if dp[s - val] is None:
                continue
            candidate = dp[s - val] + [idx]
            if dp[s] is None:
                dp[s] = candidate
                continue
            # Primary: fewer elements. Secondary: lexicographically smaller index list.
            if (len(candidate) < len(dp[s]) or
                (len(candidate) == len(dp[s]) and candidate < dp[s])):
                dp[s] = candidate

    if dp[target] is None:
        return None, None
    return len(dp[target]), dp[target]


if __name__ == "__main__":
    tests = [
        ([1, 1, 2, 2], 4),                    # -> (2, [1, 3])
        ([2, 3, 1, 1], 3),                    # -> (1, [2])
        ([3, 34, 4, 12, 5, 2], 9),            # -> (2, [3, 5])
        ([2, 4, 6], 5),                       # -> (None, None)
        ([1, 2, 3, 4, 5], 6),                 # -> (2, [1, 5])
        ([1, 3, 4, 5, 8, 10], 15),            # -> (2, [4, 6])
    ]
    for values, target in tests:
        count, indices = solve_subset_sum(values, target)
        print(f"values={values}, target={target} -> count={count}, indices={indices}")