"""
Problem:
Determine whether a subset of positive integers sums exactly to a target.
If multiple subsets are possible:
1. Choose the subset containing the fewest elements.
2. If there is still a tie, choose the lexicographically smallest list
   of original indices.

Key constraints / requirements:
- Each input element can be used at most once (0/1 subset sum).
- All numbers are positive integers.
- The target is a non-negative integer.
- Indices refer to the original input order.
- The result must be deterministic.
- If no subset reaches the target, return an impossible result.
- For target == 0, the empty subset is the unique minimum-cardinality choice.

Required output:
{
    "possible": bool,
    "count": int,
    "indices": list[int]
}

Algorithm:
Use 0/1 subset-sum dynamic programming.

For every reachable sum, store:
- the minimum number of elements needed to make that sum;
- the lexicographically smallest original-index sequence among solutions
  having that minimum cardinality.

We process each value exactly once and update sums in descending order so
that an item cannot be reused.

For a candidate solution:
- prefer the one with smaller cardinality;
- if cardinalities are equal, prefer the lexicographically smaller index list.

This gives deterministic reconstruction without relying on randomness,
sorting of equal candidates, or external services.

Complexity:
- Time: O(n * target), with additional work for comparing/storing index lists.
- Space: O(target * n) in the worst case because reconstruction sequences
  are stored explicitly.
"""


def minimum_cardinality_subset_sum(numbers, target):
    """
    Find a subset of `numbers` whose sum is exactly `target`.

    Tie-breaking:
      1. Minimum number of selected elements.
      2. Lexicographically smallest list of original indices.

    Returns:
        {
            "possible": bool,
            "count": int,
            "indices": list[int]
        }
    """
    if target < 0:
        return {
            "possible": False,
            "count": -1,
            "indices": []
        }

    n = len(numbers)

    # dp[s] is either None or:
    # (minimum_cardinality, lexicographically_smallest_index_list)
    dp = [None] * (target + 1)
    dp[0] = (0, [])

    for index, value in enumerate(numbers):
        if value <= 0:
            raise ValueError("All numbers must be positive integers.")

        # Descending sums enforce the 0/1 restriction.
        for current_sum in range(target, value - 1, -1):
            previous = dp[current_sum - value]

            if previous is None:
                continue

            previous_count, previous_indices = previous

            candidate_count = previous_count + 1
            candidate_indices = previous_indices + [index]

            existing = dp[current_sum]

            if existing is None:
                dp[current_sum] = (
                    candidate_count,
                    candidate_indices
                )
            else:
                existing_count, existing_indices = existing

                # First minimize cardinality, then lexicographic order.
                if candidate_count < existing_count:
                    dp[current_sum] = (
                        candidate_count,
                        candidate_indices
                    )
                elif (
                    candidate_count == existing_count
                    and candidate_indices < existing_indices
                ):
                    dp[current_sum] = (
                        candidate_count,
                        candidate_indices
                    )

    result = dp[target]

    if result is None:
        return {
            "possible": False,
            "count": -1,
            "indices": []
        }

    count, indices = result

    return {
        "possible": True,
        "count": count,
        "indices": indices
    }


# -------------------------
# Tests
# -------------------------

# Exact target with a unique minimum-cardinality solution.
assert minimum_cardinality_subset_sum(
    [3, 5, 7, 10], 15
) == {
    "possible": True,
    "count": 2,
    "indices": [1, 2]
}

# Same cardinality: [0, 3] and [1, 2] both sum to 10.
# [0, 3] is lexicographically smaller.
assert minimum_cardinality_subset_sum(
    [4, 3, 7, 6], 10
) == {
    "possible": True,
    "count": 2,
    "indices": [0, 3]
}

# A one-element solution must beat any multi-element solution.
assert minimum_cardinality_subset_sum(
    [2, 4, 6, 8], 8
) == {
    "possible": True,
    "count": 1,
    "indices": [3]
}

# Impossible target.
assert minimum_cardinality_subset_sum(
    [2, 4, 6], 5
) == {
    "possible": False,
    "count": -1,
    "indices": []
}

# Target zero: empty subset has minimum cardinality.
assert minimum_cardinality_subset_sum(
    [1, 2, 3], 0
) == {
    "possible": True,
    "count": 0,
    "indices": []
}

# Repeated values with deterministic lexicographic tie-breaking.
# [0, 1] and [0, 2] both have the same values/cardinality;
# [0, 1] is lexicographically smaller.
assert minimum_cardinality_subset_sum(
    [5, 5, 5], 10
) == {
    "possible": True,
    "count": 2,
    "indices": [0, 1]
}

# A later single element should beat an earlier two-element solution.
assert minimum_cardinality_subset_sum(
    [2, 3, 5], 5
) == {
    "possible": True,
    "count": 1,
    "indices": [2]
}

# Deterministic tie with multiple possible pairs.
assert minimum_cardinality_subset_sum(
    [1, 4, 2, 3, 5], 5
) == {
    "possible": True,
    "count": 1,
    "indices": [4]
}

print("All tests passed.")