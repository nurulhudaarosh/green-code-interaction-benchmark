# Minimum-Cardinality Subset Sum
#
# Original problem:
# Given a list of positive integers and a non-negative target, determine
# whether a subset of the values sums exactly to the target.
#
# If a valid subset exists:
#   1. Choose the subset with the fewest elements.
#   2. If multiple subsets have the same minimum cardinality, choose the
#      lexicographically smallest list of original indices.
#
# Each input element may be used at most once (0/1 subset sum).
#
# Difficult valid cases explicitly handled:
# - Smallest permitted input:
#       values = [], target = 0
#   The empty subset is valid and has cardinality 0.
#
# - Empty input with a positive target:
#       values = [], target > 0
#   No subset can reach the target.
#
# - Empty/disconnected reachable-state structure:
#   Some sums may be unreachable while other sums are reachable. Unreachable
#   DP states remain None and are never used for reconstruction.
#
# - Target zero:
#   The empty subset is always the minimum-cardinality solution because all
#   values are positive.
#
# Original required output is preserved:
#   {
#       "possible": bool,
#       "count": int,
#       "indices": list[int]
#   }
#
# Impossible result:
#   {
#       "possible": False,
#       "count": -1,
#       "indices": []
#   }
#
# Tie-breaking remains:
#   1. Minimum number of selected elements.
#   2. Lexicographically smallest original-index list.
#
# Algorithm:
# Use 0/1 subset-sum DP.
#
# dp[s] stores:
#     (minimum_cardinality, lexicographically_smallest_index_list)
#
# Process each value once and iterate sums backwards so an element cannot be
# selected more than once.
#
# For a candidate state:
# - Prefer it when it uses fewer elements.
# - If cardinality is equal, prefer the lexicographically smaller index list.
#
# The stored index sequence is already in increasing original-index order
# because elements are processed from left to right.
#
# Complexity:
#   Time:  O(n * target * L) in the worst case, where L is the cost of
#          comparing/copying an index sequence.
#   Space: O(target * L) for the stored reconstruction sequences.
#
# Standard library only. No network, APIs, external services, randomness,
# or human interaction.


from typing import Any, Dict, List


def minimum_cardinality_subset_sum(
    values: List[int],
    target: int
) -> Dict[str, Any]:
    """
    Return the minimum-cardinality subset whose values sum to target.

    Among equal-cardinality solutions, return the lexicographically
    smallest list of original indices.
    """

    # A negative target cannot be formed from positive integers.
    if target < 0:
        return {
            "possible": False,
            "count": -1,
            "indices": []
        }

    # dp[sum] = (minimum count, lexicographically smallest index list)
    # None means this sum is currently unreachable.
    dp = [None] * (target + 1)

    # The empty subset forms sum 0.
    dp[0] = (0, [])

    for index, value in enumerate(values):
        # Positive values larger than target cannot help form any sum
        # from 0 through target.
        if value > target:
            continue

        # Descending iteration is essential for 0/1 subset sum.
        for current_sum in range(target - value, -1, -1):
            state = dp[current_sum]

            # This is one of the "disconnected" / unreachable states.
            if state is None:
                continue

            current_count, current_indices = state
            new_sum = current_sum + value

            candidate_count = current_count + 1
            candidate_indices = current_indices + [index]

            existing = dp[new_sum]

            if existing is None:
                dp[new_sum] = (
                    candidate_count,
                    candidate_indices
                )
                continue

            existing_count, existing_indices = existing

            # Primary rule: minimum cardinality.
            if candidate_count < existing_count:
                dp[new_sum] = (
                    candidate_count,
                    candidate_indices
                )

            # Secondary rule: lexicographically smallest index list.
            elif (
                candidate_count == existing_count
                and candidate_indices < existing_indices
            ):
                dp[new_sum] = (
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


# ============================================================
# Tests
# ============================================================

# 1. Smallest permitted input:
# Empty list and target 0.
# The empty subset is valid and is necessarily minimum-cardinality.
assert minimum_cardinality_subset_sum(
    [],
    0
) == {
    "possible": True,
    "count": 0,
    "indices": []
}


# 2. Empty input with a positive target.
# There are no elements from which to construct the target.
assert minimum_cardinality_subset_sum(
    [],
    1
) == {
    "possible": False,
    "count": -1,
    "indices": []
}


# 3. Target zero with non-empty input.
# Because all values are positive, the empty subset is always optimal.
assert minimum_cardinality_subset_sum(
    [5, 2, 9],
    0
) == {
    "possible": True,
    "count": 0,
    "indices": []
}


# 4. Disconnected reachable sums.
# With [2, 4], sums such as 1 and 3 are unreachable, while 0, 2, 4,
# and 6 are reachable. Target 3 must correctly remain impossible.
assert minimum_cardinality_subset_sum(
    [2, 4],
    3
) == {
    "possible": False,
    "count": -1,
    "indices": []
}


# 5. A reachable state separated by unreachable sums.
# 2 + 4 = 6, so target 6 is reachable even though many intermediate
# sums are not.
assert minimum_cardinality_subset_sum(
    [2, 4],
    6
) == {
    "possible": True,
    "count": 2,
    "indices": [0, 1]
}


# 6. Ordinary exact solution.
assert minimum_cardinality_subset_sum(
    [3, 7, 2, 9],
    10
) == {
    "possible": True,
    "count": 2,
    "indices": [0, 1]
}


# 7. Minimum cardinality must take priority.
# 2 + 3 + 5 = 10, but [2] alone gives 5 only; 10 itself is the
# one-element optimum.
assert minimum_cardinality_subset_sum(
    [2, 3, 5, 10],
    10
) == {
    "possible": True,
    "count": 1,
    "indices": [3]
}


# 8. Equal-cardinality solutions must use lexicographically smallest
# original-index list.
#
# [0, 1] -> 2 + 5 = 7
# [0, 2] -> 2 + 5 = 7
# [1, 2] -> 5 + 5 = 10, not 7
#
# Therefore [0, 1] is selected.
assert minimum_cardinality_subset_sum(
    [2, 5, 5],
    7
) == {
    "possible": True,
    "count": 2,
    "indices": [0, 1]
}


# 9. Repeated values still represent different original indices.
assert minimum_cardinality_subset_sum(
    [4, 4, 4],
    8
) == {
    "possible": True,
    "count": 2,
    "indices": [0, 1]
}


# 10. 0/1 restriction:
# The value 3 cannot be reused to make 6.
assert minimum_cardinality_subset_sum(
    [3],
    6
) == {
    "possible": False,
    "count": -1,
    "indices": []
}


# 11. Another disconnected structure:
# With [5, 10], target 7 is unreachable even though 5 is reachable.
assert minimum_cardinality_subset_sum(
    [5, 10],
    7
) == {
    "possible": False,
    "count": -1,
    "indices": []
}


# 12. Smallest non-empty input with a reachable target.
assert minimum_cardinality_subset_sum(
    [1],
    1
) == {
    "possible": True,
    "count": 1,
    "indices": [0]
}


# 13. Smallest non-empty input with an unreachable target.
assert minimum_cardinality_subset_sum(
    [1],
    2
) == {
    "possible": False,
    "count": -1,
    "indices": []
}


print("All tests passed.")