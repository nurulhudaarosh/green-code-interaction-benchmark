def lcs(s1: str, s2: str):
    m, n = len(s1), len(s2)
    
    # Build DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    length = dp[m][n]
    
    # Deterministic reconstruction: on tie, prefer i-1 (advance in s1)
    i, j = m, n
    chars = []
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            chars.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1  # prefer advancing in first string on equal scores
        else:
            j -= 1
    
    lcs_str = ''.join(reversed(chars))
    return length, lcs_str


if __name__ == "__main__":
    tests = [
        ("ABCBDAB", "BDCABA"),
        ("AGGTAB", "GXTXAYB"),
        ("", "ABC"),
        ("ABC", ""),
        ("ABC", "ABC"),
        ("ABC", "DEF"),
        ("XMJYAUZ", "MZJAWXU"),
    ]
    for a, b in tests:
        length, seq = lcs(a, b)
        print(f"LCS({a!r}, {b!r}) -> length={length}, sequence={seq!r}")