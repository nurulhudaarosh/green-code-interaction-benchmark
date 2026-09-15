def solve_lcs(s1: str, s2: str) -> tuple[int, str]:
    """
    Computes the LCS length and reconstructs a deterministic LCS string.
    Prefers advancing (decrementing index) in s1 on equal DP scores.
    """
    m, n = len(s1), len(s2)
    
    # Initialize DP table of size (m+1) x (n+1)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                
    lcs_length = dp[m][n]
    
    # Backtrack to reconstruct the sequence
    i, j = m, n
    lcs_chars = []
    
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            lcs_chars.append(s1[i - 1])
            i -= 1
            j -= 1
        # Tie-breaking rule: prefer s1 (i-1) if scores are equal
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
            
    lcs_string = "".join(reversed(lcs_chars))
    return lcs_length, lcs_string


# --- Verification Example ---
if __name__ == "__main__":
    string1 = "ABCDGH"
    string2 = "AEDFHR"
    length, res = solve_lcs(string1, string2)
    print(f"LCS Length: {length}")
    print(f"Reconstructed LCS: {res}")