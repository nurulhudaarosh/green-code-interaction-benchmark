def edit_distance_with_transposition(
    source: str,
    target: str,
    include_operation_summary: bool = False
):
    """
    Compute edit distance using:
      - insertion: 1
      - deletion: 1
      - substitution: 1
      - adjacent transposition: 1

    Original behavior:
        Returns an integer containing the minimum edit distance.

    Extended behavior:
        If include_operation_summary=True, returns:
        {
            "distance": <minimum edit distance>,
            "operation_summary": {
                "major_operations": <number of major DP decisions>
            }
        }

    The summary is deterministic and does not change the computed distance.
    """

    n = len(source)
    m = len(target)

    # dp[i][j] = minimum cost to transform source[:i] -> target[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Count each initialized DP boundary cell as one major operation.
    major_operations = 0

    # Empty target: deletions.
    for i in range(1, n + 1):
        dp[i][0] = i
        major_operations += 1

    # Empty source: insertions.
    for j in range(1, m + 1):
        dp[0][j] = j
        major_operations += 1

    # Fill the DP table.
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            # One major computational decision for this DP state.
            major_operations += 1

            # 1. Deletion
            deletion = dp[i - 1][j] + 1

            # 2. Insertion
            insertion = dp[i][j - 1] + 1

            # 3. Match / substitution
            substitution = dp[i - 1][j - 1] + (
                0 if source[i - 1] == target[j - 1] else 1
            )

            best = min(deletion, insertion, substitution)

            # 4. Explicit adjacent transposition.
            if (
                i >= 2
                and j >= 2
                and source[i - 2] == target[j - 1]
                and source[i - 1] == target[j - 2]
            ):
                transposition = dp[i - 2][j - 2] + 1
                best = min(best, transposition)

            dp[i][j] = best

    distance = dp[n][m]

    # Preserve the original output when the feature is not requested.
    if not include_operation_summary:
        return distance

    return {
        "distance": distance,
        "operation_summary": {
            "major_operations": major_operations
        }
    }


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------
if __name__ == "__main__":
    # Original behavior remains unchanged.
    assert edit_distance_with_transposition("", "") == 0
    assert edit_distance_with_transposition("abc", "") == 3
    assert edit_distance_with_transposition("", "abc") == 3
    assert edit_distance_with_transposition("abc", "abc") == 0

    # Standard operations.
    assert edit_distance_with_transposition("abc", "adc") == 1  # substitution
    assert edit_distance_with_transposition("abc", "abdc") == 1  # insertion
    assert edit_distance_with_transposition("abc", "ac") == 1  # deletion

    # Explicit adjacent transposition.
    assert edit_distance_with_transposition("ab", "ba") == 1
    assert edit_distance_with_transposition("abcd", "abdc") == 1
    assert edit_distance_with_transposition("ca", "ac") == 1

    # Feature enabled.
    result = edit_distance_with_transposition(
        "ab",
        "ba",
        include_operation_summary=True
    )

    assert result["distance"] == 1

    # (2 + 1) boundary cells + (2 * 2) interior DP cells = 7
    assert result["operation_summary"]["major_operations"] == 7

    print("All tests passed.")

    # Example with the new feature.
    print(
        edit_distance_with_transposition(
            "abcd",
            "abdc",
            include_operation_summary=True
        )
    )