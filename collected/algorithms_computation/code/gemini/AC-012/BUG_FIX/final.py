def lcs_with_reconstruction(s1: str, s2: str) -> tuple[int, str]:
    m, n = len(s1), len(s2)
    
    # Step 1: Compute standard DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                
    lcs_length = dp[m][n]
    
    # Step 2: Backtrack with strict precedence:
    # 1. Prefer advancing in s1 (i -> i - 1) if dp[i - 1][j] == dp[i][j]
    # 2. Otherwise, match characters if s1[i - 1] == s2[j - 1]
    # 3. Otherwise, advance in s2 (j -> j - 1)
    i, j = m, n
    lcs_chars = []
    
    while i > 0 and j > 0:
        if dp[i - 1][j] == dp[i][j]:
            # Deterministic rule: prefer advancing in s1 on equal scores
            i -= 1
        elif s1[i - 1] == s2[j - 1]:
            # Match character and move diagonally
            lcs_chars.append(s1[i - 1])
            i -= 1
            j -= 1
        else:
            # Advance in s2
            j -= 1
            
    lcs_string = "".join(reversed(lcs_chars))
    return lcs_length, lcs_string


# Demonstration
if __name__ == "__main__":
    s1, s2 = "ABA", "BA"
    length, res = lcs_with_reconstruction(s1, s2)
    print(f"S1: {s1}, S2: {s2}")
    print(f"LCS Length: {length}")
    print(f"Reconstructed LCS: {res}")