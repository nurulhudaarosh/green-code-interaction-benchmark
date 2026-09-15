def lcs_with_reconstruction(s1: str, s2: str):
    """
    Compute LCS length and reconstruct one LCS.

    Deterministic tie handling:
      - On equal DP scores (dp[i-1][j] == dp[i][j-1]), prefer advancing
        in the first string (move UP in the DP table).
      - Take the diagonal (match) only when it STRICTLY improves over
        moving up, i.e. dp[i-1][j] < dp[i][j].

    Returns:
        tuple: (lcs_length, lcs_string)
    """
    m, n = len(s1), len(s2)

    # Step 1: Quadratic DP table
    # dp[i][j] = LCS length of s1[:i] and s2[:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    lcs_length = dp[m][n]

    # Step 2: Predecessor reconstruction with deterministic tie-breaking
    lcs_chars = []
    i, j = m, n
    while i > 0 and j > 0:
        match = (s1[i - 1] == s2[j - 1])
        diagonal_strictly_better = (
            match
            and dp[i][j] == dp[i - 1][j - 1] + 1
            and dp[i - 1][j] < dp[i][j]
        )
        if diagonal_strictly_better:
            lcs_chars.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1  # prefer advancing in s1
        else:
            j -= 1

    lcs_string = ''.join(reversed(lcs_chars))
    return lcs_length, lcs_string


if __name__ == "__main__":
    tests = [
        ("ABCBDAB", "BDCABA"),
        ("ABC", "DEF"),
        ("HELLO", "HELLO"),
        ("", "ABC"),
        ("AB", "BA"),
        ("BA", "AB"),
        ("AGGTAB", "GXTXAYB"),
        ("AA", "A"),
        ("BAA", "BA"),
    ]
    for s1, s2 in tests:
        length, lcs = lcs_with_reconstruction(s1, s2)
        print(f"s1='{s1}', s2='{s2}' -> length={length}, LCS='{lcs}'")