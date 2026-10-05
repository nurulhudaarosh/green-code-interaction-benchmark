def edit_distance_with_transposition(source: str, target: str) -> int:
    """
    Compute edit distance using:
      - insertion: 1
      - deletion: 1
      - substitution: 1
      - adjacent transposition: 1

    Returns:
        Minimum number of operations needed to transform source into target.
    """

    n = len(source)
    m = len(target)

    # dp[i][j] = minimum cost to transform source[:i] -> target[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Transforming a prefix into an empty string requires deletions.
    for i in range(1, n + 1):
        dp[i][0] = i

    # Transforming an empty string into a prefix requires insertions.
    for j in range(1, m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):

            # 1. Deletion
            deletion = dp[i - 1][j] + 1

            # 2. Insertion
            insertion = dp[i][j - 1] + 1

            # 3. Match / substitution
            substitution = dp[i - 1][j - 1] + (
                0 if source[i - 1] == target[j - 1] else 1
            )

            # Start with the best of the standard operations.
            best = min(deletion, insertion, substitution)

            # 4. Explicit adjacent transposition
            #
            # Example:
            # source: ...ab
            # target: ...ba
            #
            # Swapping adjacent a and b costs 1.
            if (
                i >= 2
                and j >= 2
                and source[i - 2] == target[j - 1]
                and source[i - 1] == target[j - 2]
            ):
                transposition = dp[i - 2][j - 2] + 1
                best = min(best, transposition)

            dp[i][j] = best

    return dp[n][m]


# -------------------------
# Deterministic test cases
# -------------------------
if __name__ == "__main__":
    tests = [
        ("", "", 0),
        ("abc", "", 3),
        ("", "abc", 3),
        ("abc", "abc", 0),
        ("abc", "adc", 1),      # substitution
        ("abc", "abdc", 1),     # insertion
        ("abc", "ac", 1),       # deletion
        ("ab", "ba", 1),        # adjacent transposition
        ("abcd", "abdc", 1),    # adjacent transposition
        ("ca", "ac", 1),        # adjacent transposition
    ]

    for source, target, expected in tests:
        result = edit_distance_with_transposition(source, target)
        assert result == expected, (
            f"Failed for {source!r} -> {target!r}: "
            f"expected {expected}, got {result}"
        )

    print("All tests passed.")

    # Example
    source = "abcd"
    target = "abdc"
    print(
        f"Edit distance from {source!r} to {target!r}:",
        edit_distance_with_transposition(source, target)
    )