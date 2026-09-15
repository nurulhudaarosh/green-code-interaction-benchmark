def lcs_with_reconstruction(s1: str, s2: str) -> tuple[int, str]:
    """
    Computes the LCS length and reconstructs one LCS string deterministically.
    Prefers advancing in s1 (moving i -> i-1) when DP scores are equal.
    """
    m, n = len(s1), len(s2)
    
    # Step 1: Build the DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                
    lcs_length = dp[m][n]
    
    # Step 2: Reconstruct the sequence using the deterministic rule
    lcs_chars = []
    i, j = m, n
    
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            lcs_chars.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            # Tie-breaker preference: prefer decrementing i (advancing in s1)
            i -= 1
        else:
            j -= 1
            
    # Reverse to get correct order
    reconstructed_lcs = "".join(reversed(lcs_chars))
    
    return lcs_length, reconstructed_lcs


# Example usage:
if __name__ == "__main__":
    str1 = "ABCBDAB"
    str2 = "BDCABA"
    
    length, lcs_str = lcs_with_reconstruction(str1, str2)
    print(f"LCS Length: {length}")
    print(f"Reconstructed LCS: '{lcs_str}'")