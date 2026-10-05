def edit_distance(s: str, t: str) -> int:
    """
    Compute the edit distance between s and t using:
      - insertion: 1
      - deletion: 1
      - substitution: 1
      - adjacent transposition: 1

    Returns:
        The minimum number of operations required to transform s into t.
    """

    n = len(s)
    m = len(t)

    # dp[i][j] = minimum cost to transform s[:i] into t[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Transforming a prefix into an empty string requires deletions.
    for i in range(n + 1):
        dp[i][0] = i

    # Transforming an empty string into a prefix requires insertions.
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):

            # 1. Deletion
            deletion = dp[i - 1][j] + 1

            # 2. Insertion
            insertion = dp[i][j - 1] + 1

            # 3. Match or substitution
            substitution = dp[i - 1][j - 1] + (
                0 if s[i - 1] == t[j - 1] else 1
            )

            dp[i][j] = min(
                deletion,
                insertion,
                substitution
            )

            # 4. Adjacent transposition
            #
            # Example:
            # s = "ab"
            # t = "ba"
            #
            # Swap adjacent 'a' and 'b' at cost 1.
            if (
                i >= 2
                and j >= 2
                and s[i - 2] == t[j - 1]
                and s[i - 1] == t[j - 2]
            ):
                transposition = dp[i - 2][j - 2] + 1
                dp[i][j] = min(dp[i][j], transposition)

    return dp[n][m]


# ---------------------------------------------------------
# Deterministic tests
# ---------------------------------------------------------

def run_tests():
    test_cases = [
        # Empty strings
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),

        # Identical strings
        ("abc", "abc", 0),

        # Single operation
        ("abc", "abx", 1),   # substitution
        ("abc", "abcd", 1),  # insertion
        ("abcd", "abc", 1),  # deletion

        # Adjacent transposition
        ("ab", "ba", 1),
        ("abcd", "acbd", 1),

        # Multiple operations
        ("kitten", "sitting", 3),

        # Different lengths
        ("abc", "xyz", 3),
    ]

    for s, t, expected in test_cases:
        result = edit_distance(s, t)
        assert result == expected, (
            f"Failed for {s!r} -> {t!r}: "
            f"expected {expected}, got {result}"
        )

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()

    # Example
    s = "ca"
    t = "ac"

    print(f"Edit distance from {s!r} to {t!r}: {edit_distance(s, t)}")