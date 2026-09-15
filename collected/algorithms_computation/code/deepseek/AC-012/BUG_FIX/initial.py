def lcs_with_deterministic_reconstruction(s1, s2):
    n, m = len(s1), len(s2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Build DP table for LCS length
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    # Reconstruct LCS with deterministic rule:
    lcs_chars = []
    i, j = n, m
    while i > 0 and j > 0:
        if s1[i-1] == s2[j-1]:
            lcs_chars.append(s1[i-1])
            i -= 1
            j -= 1
        else:
            if dp[i-1][j] == dp[i][j-1]:
                # Tie: prefer moving up (advance in first string)
                i -= 1
            elif dp[i-1][j] > dp[i][j-1]:
                i -= 1
            else:
                j -= 1

    lcs_chars.reverse()
    lcs_str = ''.join(lcs_chars)

    return dp[n][m], lcs_str


# Example Usage
if __name__ == "__main__":
    a = "AGGTAB"
    b = "GXTXAYB"
    length, sequence = lcs_with_deterministic_reconstruction(a, b)
    print("LCS Length:", length)
    print("LCS sequence:", sequence)