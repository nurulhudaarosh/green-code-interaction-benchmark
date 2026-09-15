def lcs_with_deterministic_reconstruction(A: str, B: str):
    n, m = len(A), len(B)
    dp = [[0]*(m+1) for _ in range(n+1)]

    # Fill dp table
    for i in range(1, n+1):
        for j in range(1, m+1):
            if A[i-1] == B[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    # Reconstruct LCS deterministically
    i, j = n, m
    lcs_chars = []
    while i > 0 and j > 0:
        if A[i-1] == B[j-1]:
            lcs_chars.append(A[i-1])
            i -= 1
            j -= 1
        else:
            if dp[i-1][j] == dp[i][j-1]:
                # Tie - prefer advancing in A (reduce i)
                i -= 1
            elif dp[i-1][j] > dp[i][j-1]:
                i -= 1
            else:
                j -= 1

    lcs_chars.reverse()
    return dp[n][m], ''.join(lcs_chars)


# Example usage:
if __name__ == "__main__":
    A = "ABCD"
    B = "ABDC"
    length, lcs = lcs_with_deterministic_reconstruction(A, B)
    print(f"LCS length: {length}")
    print(f"LCS string: {lcs}")