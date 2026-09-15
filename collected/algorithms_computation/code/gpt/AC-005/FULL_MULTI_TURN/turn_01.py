from typing import Sequence


def longest_increasing_route(sequence: Sequence[int]) -> dict:
    """
    Return a maximum-length strictly increasing subsequence.

    Among all maximum-length subsequences, choose the one whose
    original 0-based index sequence is lexicographically smallest.

    Time:  O(n^2)
    Space: O(n^2) worst case due to explicit index tuples.
    """
    n = len(sequence)

    if n == 0:
        return {
            "length": 0,
            "indices": [],
            "values": [],
        }

    # Best subsequence ending at each index.
    best_len = [1] * n
    best_indices = [(i,) for i in range(n)]

    for i in range(n):
        for j in range(i):
            if sequence[j] < sequence[i]:
                candidate_len = best_len[j] + 1
                candidate_indices = best_indices[j] + (i,)

                if candidate_len > best_len[i]:
                    best_len[i] = candidate_len
                    best_indices[i] = candidate_indices
                elif (
                    candidate_len == best_len[i]
                    and candidate_indices < best_indices[i]
                ):
                    best_indices[i] = candidate_indices

    maximum_length = max(best_len)

    # Explicit global tie breaking.
    optimal_indices = min(
        best_indices[i]
        for i in range(n)
        if best_len[i] == maximum_length
    )

    return {
        "length": maximum_length,
        "indices": list(optimal_indices),
        "values": [sequence[i] for i in optimal_indices],
    }


def _run_tests() -> None:
    assert longest_increasing_route([1, 2, 3, 4]) == {
        "length": 4,
        "indices": [0, 1, 2, 3],
        "values": [1, 2, 3, 4],
    }

    assert longest_increasing_route([5, 4, 3, 2, 1]) == {
        "length": 1,
        "indices": [0],
        "values": [5],
    }

    # Equal values are not strictly increasing.
    assert longest_increasing_route([2, 2, 2]) == {
        "length": 1,
        "indices": [0],
        "values": [2],
    }

    assert longest_increasing_route([1, 3, 2, 4]) == {
        "length": 3,
        "indices": [0, 1, 3],
        "values": [1, 3, 4],
    }

    # Empty input.
    assert longest_increasing_route([]) == {
        "length": 0,
        "indices": [],
        "values": [],
    }

    # Single element.
    assert longest_increasing_route([42]) == {
        "length": 1,
        "indices": [0],
        "values": [42],
    }

    assert longest_increasing_route([-3, -1, -2, 0]) == {
        "length": 3,
        "indices": [0, 1, 3],
        "values": [-3, -1, 0],
    }

    print("All tests passed.")


if __name__ == "__main__":
    _run_tests()