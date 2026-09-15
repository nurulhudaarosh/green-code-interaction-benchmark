def lcs_with_reconstruction(s1: str, s2: str) -> tuple[int, str]:
    """
    Compute LCS length and reconstruct one LCS.
    
    Deterministic rule: on equal DP scores during reconstruction,
    prefer advancing in the first string (move up: i-1, j).
    
    Returns:
        (lcs_length, lcs_string)
    """
    m, n = len(s1), len(s2)
    
    # Build DP table: dp[i][j] = LCS length of s1[:i] and s2[:j]
    # Use (m+1) x (n+1) to include empty prefixes
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        c1 = s1[i - 1]
        row = dp[i]
        prev_row = dp[i - 1]
        for j in range(1, n + 1):
            if c1 == s2[j - 1]:
                row[j] = prev_row[j - 1] + 1
            else:
                # max of up and left
                up = prev_row[j]
                left = row[j - 1]
                row[j] = up if up >= left else left
    
    lcs_length = dp[m][n]
    
    # Reconstruct one LCS by walking backwards
    # Rule: on ties between up (i-1,j) and left (i,j-1), prefer up
    chars = []
    i, j = m, n
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            chars.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            # Prefer advancing in first string on ties
            i -= 1
        else:
            j -= 1
    
    chars.reverse()
    return lcs_length, ''.join(chars)


def main() -> None:
    test_cases = [
        ("ABCBDAB", "BDCABA"),
        ("AGGTAB", "GXTXAYB"),
        ("", "ABC"),
        ("ABC", ""),
        ("AAAA", "AA"),
        ("ABC", "ABC"),
        ("ABC", "DEF"),
    ]
    
    for s1, s2 in test_cases:
        length, seq = lcs_with_reconstruction(s1, s2)
        print(f"LCS('{s1}', '{s2}') -> length={length}, sequence='{seq}'")


if __name__ == "__main__":
    main()