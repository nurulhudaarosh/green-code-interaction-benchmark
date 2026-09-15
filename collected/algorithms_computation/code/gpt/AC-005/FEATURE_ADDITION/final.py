from typing import List, Union, Dict, Any


def longest_increasing_route(
    a: List[int],
    include_operation_summary: bool = False,
) -> Union[List[int], Dict[str, Any]]:
    """
    Find a maximum-length strictly increasing subsequence.

    Among all optimal subsequences, return the lexicographically smallest
    sequence of original 0-based indices.

    Parameters
    ----------
    a:
        Input integer sequence.
    include_operation_summary:
        If False, preserve the original return value: List[int].
        If True, return a dictionary containing both the indices and
        a deterministic operation summary.

    Returns
    -------
    List[int]
        Original behavior when include_operation_summary=False.

    dict
        {
            "indices": List[int],
            "operation_summary": {
                "major_operations": int
            }
        }
        when include_operation_summary=True.

    Complexity
    ----------
    Time:  O(n^2)
    Space: O(n^2) worst case because explicit index sequences are stored.
    """

    n = len(a)

    if n == 0:
        result: List[int] = []

        if include_operation_summary:
            return {
                "indices": result,
                "operation_summary": {
                    "major_operations": 0
                },
            }

        return result

    # length[i] is the best subsequence length ending at i.
    length = [1] * n

    # predecessor[i] records the explicitly selected predecessor.
    predecessor = [None] * n

    # sequence[i] stores the lexicographically smallest index sequence
    # among optimal subsequences ending at i.
    sequence = [[i] for i in range(n)]

    # Number of major DP pair decisions.
    major_operations = 0

    for i in range(n):
        for j in range(i):
            major_operations += 1

            # Strictly increasing condition.
            if a[j] >= a[i]:
                continue

            candidate_length = length[j] + 1
            candidate_sequence = sequence[j] + [i]

            if candidate_length > length[i]:
                length[i] = candidate_length
                predecessor[i] = j
                sequence[i] = candidate_sequence

            elif candidate_length == length[i]:
                # Explicit deterministic tie breaking.
                if candidate_sequence < sequence[i]:
                    predecessor[i] = j
                    sequence[i] = candidate_sequence

    # Determine the globally maximum subsequence length.
    best_length = max(length)

    # Select the lexicographically smallest index sequence among
    # all subsequences having that maximum length.
    best_sequence = None

    for i in range(n):
        if length[i] == best_length:
            if best_sequence is None or sequence[i] < best_sequence:
                best_sequence = sequence[i]

    # n > 0, so best_sequence is guaranteed to exist.
    result = best_sequence

    # Preserve the exact original return type/shape unless requested.
    if not include_operation_summary:
        return result

    return {
        "indices": result,
        "operation_summary": {
            "major_operations": major_operations
        },
    }