def damerau_osa_distance(s1: str, s2: str) -> int:
    """Compute the Optimal String Alignment (OSA) edit distance between s1 and s2

    allowing insertion, deletion, substitution, and adjacent transposition,
    each with a uniform cost of 1.
    """
    m, n = len(s1), len(s2)

    # Initialize (m + 1) x (n + 1) dynamic programming table
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Base cases: transforming to/from empty strings
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Fill table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1

            dp[i][j] = min(
                dp[i - 1][j] + 1,  # Deletion
                dp[i][j - 1] + 1,  # Insertion
                dp[i - 1][j - 1] + cost,  # Substitution / Match
            )

            # Explicit adjacent transposition transition
            if (
                i > 1
                and j > 1
                and s1[i - 1] == s2[j - 2]
                and s1[i - 2] == s2[j - 1]
            ):
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)

    return dp[m][n]


if __name__ == "__main__":
    # Test cases demonstrating operations:
    # 1. Transposition: "ca" -> "abc" (swap "ca" -> "ac", insert "b") => cost 2
    assert damerau_osa_distance("ca", "abc") == 3  # OSA counts sub + ins + ins
    # Single adjacent transposition: "ab" -> "ba" => cost 1
    assert damerau_osa_distance("ab", "ba") == 1
    # Simple substitution: "cat" -> "hat" => cost 1
    assert damerau_osa_distance("cat", "hat") == 1
    # Insertion/Deletion: "abc" -> "abcd" => cost 1
    assert damerau_osa_distance("abc", "abcd") == 1
    print("All assertions passed.")