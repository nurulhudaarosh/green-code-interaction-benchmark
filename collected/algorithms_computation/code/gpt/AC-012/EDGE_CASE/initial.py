def lcs(x: str, y: str) -> dict:
    """
    Compute the Longest Common Subsequence (LCS) of two strings.

    Deterministic tie-breaking:
        If dp[i-1][j] == dp[i][j-1], prefer advancing
        in the first string (move up).

    Returns:
        {
            "length": int,
            "lcs": str
        }

    Time:  O(n * m)
    Space: O(n * m)
    """

    n = len(x)
    m = len(y)

    # dp[i][j] = LCS length of x[:i] and y[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # predecessor[i][j]:
    #   "diag" -> came from (i-1, j-1)
    #   "up"   -> came from (i-1, j)
    #   "left" -> came from (i, j-1)
    predecessor = [[None] * (m + 1) for _ in range(n + 1)]

    # Build the DP table.
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                predecessor[i][j] = "diag"

            elif dp[i - 1][j] >= dp[i][j - 1]:
                # Prefer advancing in the first string on ties.
                dp[i][j] = dp[i - 1][j]
                predecessor[i][j] = "up"

            else:
                dp[i][j] = dp[i][j - 1]
                predecessor[i][j] = "left"

    # Reconstruct the LCS using the predecessor table.
    result = []
    i, j = n, m

    while i > 0 and j > 0:
        move = predecessor[i][j]

        if move == "diag":
            result.append(x[i - 1])
            i -= 1
            j -= 1

        elif move == "up":
            i -= 1

        elif move == "left":
            j -= 1

        else:
            # This can only occur at the DP boundaries.
            break

    result.reverse()

    return {
        "length": dp[n][m],
        "lcs": "".join(result)
    }


# -------------------------
# Examples / tests
# -------------------------

if __name__ == "__main__":
    tests = [
        ("ABCBDAB", "BDCABA"),
        ("AGGTAB", "GXTXAYB"),
        ("ABC", "ABC"),
        ("ABC", "DEF"),
        ("", "ABC"),
        ("ABC", ""),
        ("AAAA", "AA"),
    ]

    for x, y in tests:
        print(f"X = {x!r}, Y = {y!r}")
        print(lcs(x, y))
        print()