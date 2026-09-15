def lcs_with_reconstruction(s1: str, s2: str) -> tuple[int, str]:
    m, n = len(s1), len(s2)
    
    # Step 1: Compute DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                
    lcs_length = dp[m][n]
    
    # Step 2: Backtrack to reconstruct the LCS string
    i, j = m, n
    lcs_chars = []
    
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            lcs_chars.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            # Deterministic tie-breaking: prefer advancing in s1 (decrementing i)
            i -= 1
        else:
            j -= 1
            
    lcs_string = "".join(reversed(lcs_chars))
    return lcs_length, lcs_string


# Example usage
if __name__ == "__main__":
    str1 = "ABCBDAB"
    str2 = "BDCABA"
    length, result = lcs_with_reconstruction(str1, str2)
    print(f"Length: {length}")
    print(f"LCS:    {result}")