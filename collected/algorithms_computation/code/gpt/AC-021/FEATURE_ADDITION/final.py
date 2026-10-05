"""
Minimum-Cardinality Subset Sum with optional operation_summary

Original problem:
Given a list of positive integers and a target sum, determine whether there
is a subset whose elements sum exactly to the target.

If a valid subset exists:
1. Choose the subset containing the fewest elements.
2. If multiple minimum-cardinality subsets exist, choose the
   lexicographically smallest list of original indices.

Original required output:
{
    "possible": bool,
    "count": int,
    "indices": list[int]
}

When no valid subset exists:
{
    "possible": False,
    "count": -1,
    "indices": []
}

When target == 0, the empty subset is the unique minimum-cardinality
solution:
{
    "possible": True,
    "count": 0,
    "indices": []
}

Added feature:
An optional `include_operation_summary` parameter can be set to True.
When enabled, the output additionally contains:

    "operation_summary": {
        "dp_decisions": <number of major DP candidate decisions>
    }

`dp_decisions` counts every reachable 0/1 DP transition considered by the
algorithm. This is deterministic and directly represents the major
computational decisions made while processing the input.

When `include_operation_summary` is False (the default), the original output
is returned unchanged.

Algorithm:
Use 0/1 subset-sum dynamic programming.

For every reachable sum, store:
- the minimum number of elements needed to form that sum;
- the lexicographically smallest index list among solutions with that
  minimum cardinality.

Process each input value once and update sums in descending order so an
element cannot be reused.

For each reachable transition:
- prefer smaller cardinality;
- if cardinality is equal, prefer the lexicographically smaller index list.

Complexity:
- Time: O(n * target), excluding the cost of copying/comparing stored
  index lists.
- Space: O(target * n) in the worst case because reconstruction sequences
  are stored explicitly.
"""


def minimum_cardinality_subset_sum(
    numbers,
    target,
    include_operation_summary=False
):
    """
    Find a subset of `numbers` whose sum is exactly `target`.

    Tie-breaking:
      1. Minimum number of selected elements.
      2. Lexicographically smallest list of original indices.

    Parameters:
        numbers: list of positive integers
        target: non-negative integer
        include_operation_summary:
            If True, include the deterministic operation_summary field.

    Returns:
        Original output fields:
        {
            "possible": bool,
            "count": int,
            "indices": list[int]
        }

        When include_operation_summary=True, also:
        {
            "operation_summary": {
                "dp_decisions": int
            }
        }
    """
    if target < 0:
        result = {
            "possible": False,
            "count": -1,
            "indices": []
        }

        if include_operation_summary:
            result["operation_summary"] = {
                "dp_decisions": 0
            }

        return result

    for value in numbers:
        if value <= 0:
            raise ValueError("All numbers must be positive integers.")

    # dp[s] is either None or:
    # (minimum_cardinality, lexicographically_smallest_index_list)
    dp = [None] * (target + 1)
    dp[0] = (0, [])

    # Counts the major candidate-selection decisions made by the DP.
    operation_count = 0

    for index, value in enumerate(numbers):
        # Descending sums enforce the 0/1 restriction.
        for current_sum in range(target, value - 1, -1):
            previous = dp[current_sum - value]

            if previous is None:
                continue

            operation_count += 1

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

                # First minimize cardinality.
                if candidate_count < existing_count:
                    dp[current_sum] = (
                        candidate_count,
                        candidate_indices
                    )

                # Then use lexicographically smallest index list.
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
        output = {
            "possible": False,
            "count": -1,
            "indices": []
        }
    else:
        count, indices = result

        output = {
            "possible": True,
            "count": count,
            "indices": indices
        }

    if include_operation_summary:
        output["operation_summary"] = {
            "dp_decisions": operation_count
        }

    return output


# ---------------------------------------------------------
# Tests: original behavior remains unchanged by default
# ---------------------------------------------------------

assert minimum_cardinality_subset_sum(
    [3, 5, 7, 10], 15
) == {
    "possible": True,
    "count": 2,
    "indices": [1, 2]
}

assert minimum_cardinality_subset_sum(
    [4, 3, 7, 6], 10
) == {
    "possible": True,
    "count": 2,
    "indices": [0, 3]
}

assert minimum_cardinality_subset_sum(
    [2, 4, 6, 8], 8
) == {
    "possible": True,
    "count": 1,
    "indices": [3]
}

assert minimum_cardinality_subset_sum(
    [2, 4, 6], 5
) == {
    "possible": False,
    "count": -1,
    "indices": []
}

assert minimum_cardinality_subset_sum(
    [1, 2, 3], 0
) == {
    "possible": True,
    "count": 0,
    "indices": []
}

assert minimum_cardinality_subset_sum(
    [5, 5, 5], 10
) == {
    "possible": True,
    "count": 2,
    "indices": [0, 1]
}

assert minimum_cardinality_subset_sum(
    [2, 3, 5], 5
) == {
    "possible": True,
    "count": 1,
    "indices": [2]
}

# ---------------------------------------------------------
# Tests: operation_summary enabled
# ---------------------------------------------------------

result = minimum_cardinality_subset_sum(
    [3, 5, 7, 10],
    15,
    include_operation_summary=True
)

assert result["possible"] is True
assert result["count"] == 2
assert result["indices"] == [1, 2]
assert "operation_summary" in result
assert isinstance(result["operation_summary"]["dp_decisions"], int)
assert result["operation_summary"]["dp_decisions"] > 0

# The summary is deterministic: the same input produces the same count.
result1 = minimum_cardinality_subset_sum(
    [5, 5, 5],
    10,
    include_operation_summary=True
)

result2 = minimum_cardinality_subset_sum(
    [5, 5, 5],
    10,
    include_operation_summary=True
)

assert result1 == result2

# Impossible target with summary.
result = minimum_cardinality_subset_sum(
    [2, 4, 6],
    5,
    include_operation_summary=True
)

assert result == {
    "possible": False,
    "count": -1,
    "indices": [],
    "operation_summary": {
        "dp_decisions": 3
    }
}

# Target zero has no DP transitions.
result = minimum_cardinality_subset_sum(
    [1, 2, 3],
    0,
    include_operation_summary=True
)

assert result == {
    "possible": True,
    "count": 0,
    "indices": [],
    "operation_summary": {
        "dp_decisions": 0
    }
}

print("All tests passed.")