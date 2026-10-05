def edit_distance_with_transposition(s: str, t: str) -> int:
    """
    Compute edit distance between s and t using:
      - insertion: 1
      - deletion: 1
      - substitution: 1
      - adjacent transposition: 1

    Deterministic tie handling:
      transposition > substitution/match > deletion > insertion

    Returns:
        Minimum edit distance as an integer.
    """

    n = len(s)
    m = len(t)

    # dp[i][j] = minimum cost to transform s[:i] into t[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Base cases
    for i in range(n + 1):
        dp[i][0] = i

    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):

            # Fixed deterministic priority:
            # 1 = transposition
            # 2 = match/substitution
            # 3 = deletion
            # 4 = insertion

            candidates = []

            # Insertion
            candidates.append((dp[i][j - 1] + 1, 4))

            # Deletion
            candidates.append((dp[i - 1][j] + 1, 3))

            # Match / substitution
            substitution_cost = 0 if s[i - 1] == t[j - 1] else 1
            candidates.append(
                (dp[i - 1][j - 1] + substitution_cost, 2)
            )

            # Explicit adjacent transposition
            #
            # Example:
            #     s = "ab"
            #     t = "ba"
            #
            #     "ab" -> "ba"
            #
            # The two adjacent characters are swapped at cost 1.
            if (
                i >= 2
                and j >= 2
                and s[i - 2] == t[j - 1]
                and s[i - 1] == t[j - 2]
            ):
                candidates.append(
                    (dp[i - 2][j - 2] + 1, 1)
                )

            # Select minimum cost.
            # If costs tie, the smaller priority wins.
            dp[i][j] = min(candidates)[0]

    return dp[n][m]


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def run_tests():
    test_cases = [
        # Empty strings
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),

        # Identical strings
        ("abc", "abc", 0),

        # Insertion
        ("abc", "abcd", 1),

        # Deletion
        ("abcd", "abc", 1),

        # Substitution
        ("abc", "abx", 1),

        # Adjacent transposition
        ("ab", "ba", 1),
        ("abcd", "acbd", 1),

        # Multiple edits
        ("kitten", "sitting", 3),

        # Different strings
        ("abc", "xyz", 3),

        # Single-character strings
        ("a", "a", 0),
        ("a", "b", 1),
    ]

    for s, t, expected in test_cases:
        result = edit_distance_with_transposition(s, t)

        assert result == expected, (
            f"Failed for {s!r} -> {t!r}: "
            f"expected {expected}, got {result}"
        )

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()

    # Small defect demonstration:
    # Without the explicit transposition transition,
    # "ab" -> "ba" would incorrectly require cost 2.
    # With the corrected transition, the answer is 1.

    s = "ab"
    t = "ba"

    print(
        f"Edit distance from {s!r} to {t!r}: "
        f"{edit_distance_with_transposition(s, t)}"
    )