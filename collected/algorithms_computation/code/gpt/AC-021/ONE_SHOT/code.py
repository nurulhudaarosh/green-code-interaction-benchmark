"""
Problem: Exact Subset Sum with Deterministic Tie-Breaking

Identify and understand the problem:
Given a list of positive integers and a target sum, determine whether some
subset of the elements sums exactly to the target.

If multiple valid subsets exist:
1. Choose the subset containing the fewest elements.
2. If multiple subsets have the same minimum cardinality, choose the
   lexicographically smallest list of original indices.

Key constraints and required output:
- All input values are positive integers.
- Each element may be used at most once (0/1 subset sum).
- The target is an integer.
- If no subset reaches the target, return:
      {"possible": False, "count": -1, "indices": []}
- If a solution exists, return:
      {"possible": True, "count": k, "indices": [...]}
  where k is the minimum number of elements and `indices` is the
  lexicographically smallest index list among all minimum-cardinality
  solutions.
- Indices are 0-based and listed in increasing order.
- The solution is deterministic.

Algorithm:
Use 0/1 subset-sum dynamic programming.

For every reachable sum, store:
    (minimum cardinality, lexicographically smallest index sequence)

For each input value, process sums in descending order so that an element
cannot be reused. When adding the current index:
- Prefer the candidate with fewer elements.
- If cardinalities are equal, prefer the lexicographically smaller
  index sequence.

Because the stored sequence is always sorted by original index and every
new index is larger than the indices already stored, normal Python tuple
lexicographic comparison gives the required deterministic tie-breaking.

Time complexity:
    O(n * target)
with tuple-comparison/reconstruction overhead for stored sequences.

Space complexity:
    O(target), excluding the stored reconstruction sequences.
"""


from typing import List, Dict, Tuple


def exact_subset_sum(
    values: List[int],
    target: int,
    include_operation_summary: bool = False,
) -> Dict[str, object]:
    """
    Find a minimum-cardinality subset whose values sum to target.

    Tie-breaking:
    - Minimum number of elements.
    - Lexicographically smallest original-index list.

    Returns:
        {
            "possible": bool,
            "count": int,
            "indices": list[int]
        }

    If include_operation_summary=True, an additional deterministic field
    is returned:
        "operation_summary": {
            "dp_transitions": int
        }

    The operation count is the number of candidate 0/1 DP transitions
    actually considered.
    """

    if target < 0:
        raise ValueError("target must be non-negative")

    if any(value <= 0 for value in values):
        raise ValueError("all values must be positive integers")

    # Sum 0 is always reachable using the empty subset.
    # Each state stores:
    #   (cardinality, tuple_of_indices)
    dp: List[Tuple[int, Tuple[int, ...]] | None] = [None] * (target + 1)
    dp[0] = (0, ())

    transitions = 0

    for index, value in enumerate(values):
        # Descending order enforces the 0/1 restriction.
        for current_sum in range(target - value, -1, -1):
            state = dp[current_sum]

            if state is None:
                continue

            new_sum = current_sum + value
            candidate_count = state[0] + 1
            candidate_indices = state[1] + (index,)

            transitions += 1

            existing = dp[new_sum]

            if existing is None:
                dp[new_sum] = (candidate_count, candidate_indices)
            else:
                existing_count, existing_indices = existing

                if candidate_count < existing_count:
                    dp[new_sum] = (candidate_count, candidate_indices)
                elif (
                    candidate_count == existing_count
                    and candidate_indices < existing_indices
                ):
                    dp[new_sum] = (candidate_count, candidate_indices)

    if dp[target] is None:
        result: Dict[str, object] = {
            "possible": False,
            "count": -1,
            "indices": [],
        }
    else:
        count, indices = dp[target]
        result = {
            "possible": True,
            "count": count,
            "indices": list(indices),
        }

    if include_operation_summary:
        result["operation_summary"] = {
            "dp_transitions": transitions
        }

    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def run_tests() -> None:
    # Basic possible case.
    assert exact_subset_sum(
        [3, 1, 4, 2], 6
    ) == {
        "possible": True,
        "count": 2,
        "indices": [0, 2],
    }

    # Minimum cardinality wins:
    # [0, 1] -> 4, [2] -> 4, so index [2] is selected.
    assert exact_subset_sum(
        [2, 2, 4], 4
    ) == {
        "possible": True,
        "count": 1,
        "indices": [2],
    }

    # Equal-cardinality tie:
    # [0, 3] and [1, 2] both sum to 6.
    # [0, 3] is lexicographically smaller.
    assert exact_subset_sum(
        [1, 2, 4, 5], 6
    ) == {
        "possible": True,
        "count": 2,
        "indices": [0, 3],
    }

    # Repeated values with deterministic tie-breaking.
    # Several pairs sum to 6; [0, 1] is lexicographically smallest.
    assert exact_subset_sum(
        [3, 3, 3, 3], 6
    ) == {
        "possible": True,
        "count": 2,
        "indices": [0, 1],
    }

    # Empty subset for target 0.
    assert exact_subset_sum(
        [5, 7, 9], 0
    ) == {
        "possible": True,
        "count": 0,
        "indices": [],
    }

    # Impossible target.
    assert exact_subset_sum(
        [2, 4, 6], 5
    ) == {
        "possible": False,
        "count": -1,
        "indices": [],
    }

    # Empty input.
    assert exact_subset_sum(
        [], 0
    ) == {
        "possible": True,
        "count": 0,
        "indices": [],
    }

    assert exact_subset_sum(
        [], 5
    ) == {
        "possible": False,
        "count": -1,
        "indices": [],
    }

    # Operation summary is deterministic and does not alter the original
    # required fields.
    result = exact_subset_sum(
        [2, 3, 5], 5, include_operation_summary=True
    )

    assert result["possible"] is True
    assert result["count"] == 1
    assert result["indices"] == [2]
    assert result["operation_summary"]["dp_transitions"] == 4

    # Invalid inputs.
    try:
        exact_subset_sum([1, 2, 0], 2)
        assert False
    except ValueError:
        pass

    try:
        exact_subset_sum([1, 2, -3], 2)
        assert False
    except ValueError:
        pass

    try:
        exact_subset_sum([1, 2], -1)
        assert False
    except ValueError:
        pass


if __name__ == "__main__":
    run_tests()