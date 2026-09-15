from typing import Sequence


def longest_increasing_route(
    sequence: Sequence[int],
    include_operation_summary: bool = False,
) -> dict:
    """
    Find a maximum-length strictly increasing subsequence.

    Tie-breaking:
        Among all maximum-length subsequences, return the one whose
        original 0-based index sequence is lexicographically smallest.

    Optional operation_summary:
        If include_operation_summary=True, the returned dictionary also
        contains:
            "operation_summary": {
                "major_operations": number of DP pair decisions
            }

    Complexity:
        Time:  O(n^2)
        Space: O(n) for DP/predecessor arrays, plus temporary index
                sequences used for deterministic tie comparison.
    """
    n = len(sequence)

    if n == 0:
        result = {
            "length": 0,
            "indices": [],
            "values": [],
        }

        if include_operation_summary:
            result["operation_summary"] = {
                "major_operations": 0
            }

        return result

    dp = [1] * n
    predecessor = [-1] * n

    # Explicit index sequences make tie-breaking deterministic.
    index_sequences = [(i,) for i in range(n)]

    major_operations = 0

    for i in range(n):
        for j in range(i):
            # One major DP decision for every examined predecessor pair.
            major_operations += 1

            if sequence[j] >= sequence[i]:
                continue

            candidate_length = dp[j] + 1
            candidate_indices = index_sequences[j] + (i,)

            if candidate_length > dp[i]:
                dp[i] = candidate_length
                predecessor[i] = j
                index_sequences[i] = candidate_indices

            elif candidate_length == dp[i]:
                if candidate_indices < index_sequences[i]:
                    predecessor[i] = j
                    index_sequences[i] = candidate_indices

    # Select the globally optimal ending index.
    best_end = 0

    for i in range(1, n):
        if dp[i] > dp[best_end]:
            best_end = i
        elif dp[i] == dp[best_end]:
            if index_sequences[i] < index_sequences[best_end]:
                best_end = i

    # Reconstruct the selected subsequence through predecessors.
    indices = []
    current = best_end

    while current != -1:
        indices.append(current)
        current = predecessor[current]

    indices.reverse()

    result = {
        "length": len(indices),
        "indices": indices,
        "values": [sequence[i] for i in indices],
    }

    if include_operation_summary:
        result["operation_summary"] = {
            "major_operations": major_operations
        }

    return result


def _run_tests() -> None:
    # Original behavior: no operation_summary when disabled.
    assert longest_increasing_route([1, 2, 3, 4]) == {
        "length": 4,
        "indices": [0, 1, 2, 3],
        "values": [1, 2, 3, 4],
    }

    # Optional feature enabled.
    assert longest_increasing_route(
        [1, 2, 3, 4],
        include_operation_summary=True,
    ) == {
        "length": 4,
        "indices": [0, 1, 2, 3],
        "values": [1, 2, 3, 4],
        "operation_summary": {
            "major_operations": 6
        },
    }

    # Explicit lexicographic tie-breaking.
    assert longest_increasing_route(
        [1, 3, 2, 4],
        include_operation_summary=True,
    ) == {
        "length": 3,
        "indices": [0, 1, 3],
        "values": [1, 3, 4],
        "operation_summary": {
            "major_operations": 6
        },
    }

    # Decreasing sequence.
    assert longest_increasing_route(
        [5, 4, 3, 2, 1],
        include_operation_summary=True,
    ) == {
        "length": 1,
        "indices": [0],
        "values": [5],
        "operation_summary": {
            "major_operations": 10
        },
    }

    # Equal values cannot form a strictly increasing subsequence.
    assert longest_increasing_route(
        [2, 2, 2],
        include_operation_summary=True,
    ) == {
        "length": 1,
        "indices": [0],
        "values": [2],
        "operation_summary": {
            "major_operations": 3
        },
    }

    # Empty input.
    assert longest_increasing_route(
        [],
        include_operation_summary=True,
    ) == {
        "length": 0,
        "indices": [],
        "values": [],
        "operation_summary": {
            "major_operations": 0
        },
    }

    # Empty input without the optional feature.
    assert longest_increasing_route([]) == {
        "length": 0,
        "indices": [],
        "values": [],
    }

    # Single element.
    assert longest_increasing_route(
        [42],
        include_operation_summary=True,
    ) == {
        "length": 1,
        "indices": [0],
        "values": [42],
        "operation_summary": {
            "major_operations": 0
        },
    }

    # Negative and mixed values.
    assert longest_increasing_route(
        [-3, -1, -2, 0],
        include_operation_summary=True,
    ) == {
        "length": 3,
        "indices": [0, 1, 3],
        "values": [-3, -1, 0],
        "operation_summary": {
            "major_operations": 6
        },
    }

    print("All tests passed.")


if __name__ == "__main__":
    _run_tests()