def lcs_with_reconstruction(s1: str, s2: str) -> tuple[int, str]:
    """
    Computes the LCS length and reconstructs the LCS string deterministically.
    Prefers advancing in s1 when DP scores are equal.
    """
    m, n = len(s1), len(s2)
    
    # Build DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
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
        # Deterministic tie-breaking: prefer moving up (advancing in s1) when dp values are equal
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
            
    lcs_string = "".join(reversed(lcs_chars))
    return lcs_length, lcs_string


# Example usage
if __name__ == "__main__":
    s1 = "ABCBDAB"
    s2 = "BDCABA"
    length, lcs = lcs_with_reconstruction(s1, s2)
    print(f"S1: {s1}")
    print(f"S2: {s2}")
    print(f"LCS Length: {length}")
    print(f"Reconstructed LCS: '{lcs}'")