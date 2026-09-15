def lcs_with_reconstruction(s1: str, s2: str) -> tuple[int, str]:
    """
    Computes the LCS length and reconstructs the LCS string deterministically.
    Prefers advancing in s1 (moving up in DP table) on score ties.
    """
    m, n = len(s1), len(s2)
    
    # 1. DP Table Construction
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                
    lcs_length = dp[m][n]
    
    # 2. Deterministic Backtracking
    i, j = m, n
    lcs_chars = []
    
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            lcs_chars.append(s1[i - 1])
            i -= 1
            j -= 1
        # Tie-breaking rule: prefer advancing in s1 (i-1) when score is equal
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
            
    lcs_string = "".join(reversed(lcs_chars))
    return lcs_length, lcs_string


def run_tests():
    test_cases = [
        # (Name, s1, s2, Expected Length, Expected Output String)
        (
            "Original Example", 
            "ABCBDAB", "BDCABA", 
            4, "BCBA"
        ),
        (
            "Worst-Case Tie Collision (Interleaved)", 
            "ABABABABAB", "BABABABABA", 
            9, "ABABABABA"
        ),
        (
            "Disjoint Strings (Zero LCS)", 
            "AAAAA", "BBBBB", 
            0, ""
        ),
        (
            "Identical Strings", 
            "DYNAMIC", "DYNAMIC", 
            7, "DYNAMIC"
        ),
        (
            "One Empty String", 
            "", "NONEMPTY", 
            0, ""
        ),
        (
            "Repeated Single Character Difference", 
            "AAAAA", "AAA", 
            3, "AAA"
        ),
        (
            "Tie-Break Order Verification", 
            "AB", "BA", 
            1, "A"  # 'A' preferred due to advancing in s1 over 'B'
        )
    ]
    
    print(f"{'Test Case':<38} | {'Status':<6} | {'Length':<6} | {'Reconstructed LCS'}")
    print("-" * 75)
    
    for name, s1, s2, exp_len, exp_str in test_cases:
        length, result = lcs_with_reconstruction(s1, s2)
        passed = (length == exp_len) and (result == exp_str)
        status = "PASS" if passed else "FAIL"
        print(f"{name:<38} | {status:<6} | {length:<6} | '{result}'")


if __name__ == "__main__":
    run_tests()