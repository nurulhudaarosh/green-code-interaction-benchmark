def osa_distance(s1: str, s2: str) -> int:
    """Compute the edit distance between s1 and s2 allowing insertion,

    deletion, substitution, and adjacent transposition (each costing 1).
    """
    n, m = len(s1), len(s2)

    # dp[i][j] stores the distance between s1[:i] and s2[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Initialize base cases
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    # Fill DP table
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sub_cost = 0 if s1[i - 1] == s2[j - 1] else 1

            dp[i][j] = min(
                dp[i - 1][j] + 1,  # Deletion
                dp[i][j - 1] + 1,  # Insertion
                dp[i - 1][j - 1] + sub_cost,  # Substitution / match
            )

            # Adjacent transposition check
            if (
                i > 1
                and j > 1
                and s1[i - 1] == s2[j - 2]
                and s1[i - 2] == s2[j - 1]
            ):
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)

    return dp[n][m]


if __name__ == "__main__":
    # Test cases demonstrating the four operations
    assert osa_distance("cat", "cat") == 0  # Identical
    assert osa_distance("cat", "cats") == 1  # Insertion
    assert osa_distance("cat", "at") == 1  # Deletion
    assert osa_distance("cat", "bat") == 1  # Substitution
    assert osa_distance("ca", "ac") == 1  # Adjacent transposition
    assert osa_distance("banana", "bnaan") == 2  # Combined operations
    print("All assertions passed.")