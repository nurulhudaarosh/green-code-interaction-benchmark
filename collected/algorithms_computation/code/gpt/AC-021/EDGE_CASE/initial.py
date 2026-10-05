# Problem:
# Given a list of positive integers and a target, determine whether some
# subset sums exactly to the target.
#
# If a solution exists:
#   1. Minimize the number of selected elements.
#   2. Among all minimum-cardinality solutions, choose the
#      lexicographically smallest list of original indices.
#
# Key constraints / requirements:
# - Each input element can be used at most once (0/1 subset sum).
# - All input values are positive integers.
# - The target is a non-negative integer.
# - Indices are 0-based and refer to the original input order.
# - The result must be deterministic.
# - Tie-breaking must be exact:
#       minimum cardinality first,
#       then lexicographically smallest index list.
# - If no subset reaches the target, return an impossible result.
#
# Required output:
# A dictionary with:
#   {
#       "possible": bool,
#       "count": int,
#       "indices": list[int]
#   }
#
# For an impossible target:
#   {
#       "possible": False,
#       "count": -1,
#       "indices": []
#   }
#
# Algorithm:
# Use 0/1 subset-sum dynamic programming.
#
# For every reachable sum, store:
#   (minimum number of elements, lexicographically smallest index sequence)
#
# Each input element is processed once, and sums are traversed backwards
# so that an element cannot be used more than once.
#
# When a candidate reaches the same sum:
#   - Prefer fewer elements.
#   - If the cardinalities are equal, prefer the lexicographically smaller
#     index list.
#
# Because every stored sequence is explicitly retained, reconstruction is
# deterministic and no separate backtracking pass is necessary.
#
# Time complexity: O(n * target * L), where L is the cost of comparing/
# constructing index sequences in the worst case.
# Space complexity: O(target * L) for the stored reconstruction sequences.

from typing import List, Dict, Any


def minimum_cardinality_subset_sum(
    values: List[int],
    target: int
) -> Dict[str, Any]:
    """
    Find a subset whose values sum exactly to target.

    Optimization order:
        1. Minimum number of selected elements.
        2. Lexicographically smallest list of original indices.

    Returns:
        {
            "possible": True/False,
            "count": minimum number of elements or -1,
            "indices": selected original indices
        }
    """

    if target < 0:
        return {
            "possible": False,
            "count": -1,
            "indices": []
        }

    # dp[sum] = (cardinality, index_list)
    #
    # None means the sum is currently unreachable.
    dp = [None] * (target + 1)
    dp[0] = (0, [])

    for index, value in enumerate(values):
        # Values are positive, so values greater than target can never
        # contribute to a useful non-zero target.
        if value > target:
            continue

        # Descending order enforces the 0/1 restriction:
        # the current element cannot be reused during this iteration.
        for current_sum in range(target - value, -1, -1):
            state = dp[current_sum]

            if state is None:
                continue

            current_count, current_indices = state
            new_sum = current_sum + value

            candidate_count = current_count + 1
            candidate_indices = current_indices + [index]

            existing = dp[new_sum]

            if existing is None:
                dp[new_sum] = (candidate_count, candidate_indices)
            else:
                existing_count, existing_indices = existing

                # Primary criterion: fewer elements.
                if candidate_count < existing_count:
                    dp[new_sum] = (candidate_count, candidate_indices)

                # Secondary criterion: lexicographically smaller
                # original-index list.
                elif (
                    candidate_count == existing_count
                    and candidate_indices < existing_indices
                ):
                    dp[new_sum] = (candidate_count, candidate_indices)

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

# 1. Exact solution exists.
assert minimum_cardinality_subset_sum(
    [3, 7, 2, 9],
    10
) == {
    "possible": True,
    "count": 2,
    "indices": [0, 1]
}

# 2. Choose fewer elements even if another solution appears earlier.
assert minimum_cardinality_subset_sum(
    [2, 3, 5],
    5
) == {
    "possible": True,
    "count": 1,
    "indices": [2]
}

# 3. Multiple minimum-cardinality solutions:
# [0, 1] = 2 + 5 = 7
# [0, 2] = 2 + 5 = 7
# [1, 2] = 5 + 2 = 7
# The lexicographically smallest valid index list is [0, 1]
# for the corresponding values below.
assert minimum_cardinality_subset_sum(
    [2, 5, 5],
    7
) == {
    "possible": True,
    "count": 2,
    "indices": [0, 1]
}

# 4. Impossible target.
assert minimum_cardinality_subset_sum(
    [2, 4, 6],
    5
) == {
    "possible": False,
    "count": -1,
    "indices": []
}

# 5. Target zero: empty subset is the unique minimum-cardinality solution.
assert minimum_cardinality_subset_sum(
    [1, 2, 3],
    0
) == {
    "possible": True,
    "count": 0,
    "indices": []
}

# 6. Repeated values must still use distinct original indices.
assert minimum_cardinality_subset_sum(
    [4, 4, 4],
    8
) == {
    "possible": True,
    "count": 2,
    "indices": [0, 1]
}

# 7. A single element should beat every multi-element solution.
assert minimum_cardinality_subset_sum(
    [1, 4, 6, 10],
    10
) == {
    "possible": True,
    "count": 1,
    "indices": [3]
}

print("All tests passed.")