from typing import Sequence


def longest_increasing_route(
    sequence: Sequence[int],
    include_operation_summary: bool = False,
) -> dict:
    """
    Find a maximum-length strictly increasing subsequence.

    Tie-breaking:
        Among all optimal subsequences, select the lexicographically smallest
        sequence of original 0-based indices.

    Dynamic programming:
        dp[i] is the best length of an increasing subsequence ending at i.
        predecessor[i] explicitly records the selected predecessor index.

    Complexity:
        Time:  O(n^2)
        Space: O(n) for DP/predecessor arrays, plus temporary index sequences
                for deterministic tie comparison.
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
    index_sequences = [(i,) for i in range(n)]

    major_operations = 0

    for i in range(n):
        for j in range(i):
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

    best_end = 0

    for i in range(1, n):
        if dp[i] > dp[best_end]:
            best_end = i
        elif dp[i] == dp[best_end]:
            if index_sequences[i] < index_sequences[best_end]:
                best_end = i

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
    # Smallest permitted input: empty sequence.
    assert longest_increasing_route([]) == {
        "length": 0,
        "indices": [],
        "values": [],
    }

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

    # Smallest non-empty input.
    assert longest_increasing_route([7]) == {
        "length": 1,
        "indices": [0],
        "values": [7],
    }

    assert longest_increasing_route(
        [7],
        include_operation_summary=True,
    ) == {
        "length": 1,
        "indices": [0],
        "values": [7],
        "operation_summary": {
            "major_operations": 0
        },
    }

    # No compatible predecessor pairs.
    assert longest_increasing_route([5, 4, 3, 2, 1]) == {
        "length": 1,
        "indices": [0],
        "values": [5],
    }

    # All values equal: strict inequality prevents chaining.
    assert longest_increasing_route([3, 3, 3]) == {
        "length": 1,
        "indices": [0],
        "values": [3],
    }

    # Normal increasing input.
    assert longest_increasing_route([1, 2, 3, 4]) == {
        "length": 4,
        "indices": [0, 1, 2, 3],
        "values": [1, 2, 3, 4],
    }

    # Lexicographic tie-breaking.
    assert longest_increasing_route([1, 3, 2, 4]) == {
        "length": 3,
        "indices": [0, 1, 3],
        "values": [1, 3, 4],
    }

    # Duplicate values with strictness and tie-breaking.
    assert longest_increasing_route([1, 2, 2, 3]) == {
        "length": 3,
        "indices": [0, 1, 3],
        "values": [1, 2, 3],
    }

    # Negative and positive values.
    assert longest_increasing_route([-3, -1, -2, 0]) == {
        "length": 3,
        "indices": [0, 1, 3],
        "values": [-3, -1, 0],
    }

    # Sequence analogue of a disconnected/no-edge structure.
    assert longest_increasing_route([10, 9, 8]) == {
        "length": 1,
        "indices": [0],
        "values": [10],
    }

    # Optional operation summary.
    result = longest_increasing_route(
        [1, 4, 2, 5],
        include_operation_summary=True,
    )

    assert result["length"] == 3
    assert result["indices"] == [0, 1, 3]
    assert result["values"] == [1, 4, 5]
    assert result["operation_summary"] == {
        "major_operations": 6
    }

    print("All tests passed.")


if __name__ == "__main__":
    _run_tests()