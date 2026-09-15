# Longest Strictly Increasing Subsequence
# Tie-breaking:
# Among all maximum-length increasing subsequences,
# return the lexicographically smallest sequence of original indices.

def longest_increasing_subsequence(sequence):
    """
    Return:
        (maximum_length, lexicographically_smallest_index_sequence)

    Example:
        sequence = [3, 1, 2, 4]
        returns (3, [1, 2, 3])
    """

    n = len(sequence)

    if n == 0:
        return 0, []

    # dp[i] = longest increasing subsequence length ending at i
    dp = [1] * n

    # path[i] = lexicographically smallest index sequence
    # for an optimal subsequence ending at i.
    path = [[i] for i in range(n)]

    # Quadratic dynamic programming.
    for i in range(n):
        for j in range(i):
            # Strictly increasing condition.
            if sequence[j] < sequence[i]:
                candidate_length = dp[j] + 1
                candidate_path = path[j] + [i]

                # Better length always wins.
                if candidate_length > dp[i]:
                    dp[i] = candidate_length
                    path[i] = candidate_path

                # For equal lengths, explicitly apply
                # lexicographic tie-breaking on original indices.
                elif candidate_length == dp[i]:
                    if candidate_path < path[i]:
                        path[i] = candidate_path

    # Find the globally maximum length.
    maximum_length = max(dp)

    # Among all optimal subsequences, choose the one with
    # the lexicographically smallest original-index sequence.
    best_path = None

    for i in range(n):
        if dp[i] == maximum_length:
            if best_path is None or path[i] < best_path:
                best_path = path[i]

    return maximum_length, best_path


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def run_tests():
    # Basic case
    assert longest_increasing_subsequence(
        [3, 1, 2, 4]
    ) == (3, [1, 2, 3])

    # Already strictly increasing
    assert longest_increasing_subsequence(
        [1, 2, 3, 4]
    ) == (4, [0, 1, 2, 3])

    # Strictly decreasing
    assert longest_increasing_subsequence(
        [4, 3, 2, 1]
    ) == (1, [0])

    # Repeated values are not allowed to extend an LIS.
    assert longest_increasing_subsequence(
        [2, 2, 2, 2]
    ) == (1, [0])

    # Repeated values with a longer increasing subsequence.
    assert longest_increasing_subsequence(
        [1, 2, 2, 3]
    ) == (3, [0, 1, 3])

    # Deterministic lexicographic tie-breaking.
    # Multiple LISs have length 2:
    # [0, 2] -> [1, 3]
    # [0, 3] -> [1, 4]
    # [1, 2] -> [2, 3]
    # [1, 3] -> [2, 4]
    # Lexicographically smallest is [0, 2].
    assert longest_increasing_subsequence(
        [1, 2, 3, 4]
    ) == (4, [0, 1, 2, 3])

    # Multiple optimal choices with equal length.
    assert longest_increasing_subsequence(
        [2, 1, 3]
    ) == (2, [0, 2])

    # Another tie case.
    assert longest_increasing_subsequence(
        [1, 3, 2, 4]
    ) == (3, [0, 1, 3])

    # Empty sequence.
    assert longest_increasing_subsequence(
        []
    ) == (0, [])

    # Single element.
    assert longest_increasing_subsequence(
        [10]
    ) == (1, [0])

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()