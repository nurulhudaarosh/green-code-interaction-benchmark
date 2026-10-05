def optimal_string_alignment_distance(s: str, t: str) -> int:
    """
    Computes the edit distance between strings s and t using insertion,
    deletion, substitution, and adjacent transposition, each costing 1.
    """
    m, n = len(s), len(t)
    
    # Initialize DP table of size (m + 1) x (n + 1)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Base cases: transforming to/from empty strings
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
        
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s[i - 1] == t[j - 1] else 1
            
            # Standard Levenshtein transitions
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # Deletion
                dp[i][j - 1] + 1,       # Insertion
                dp[i - 1][j - 1] + cost # Substitution / Match
            )
            
            # Adjacent transposition transition
            if i > 1 and j > 1 and s[i - 1] == t[j - 2] and s[i - 2] == t[j - 1]:
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)
                
    return dp[m][n]


if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("ca", "abc", 3),       # Delete 'c', insert 'b', insert 'c' OR transpose + insert
        ("ab", "ba", 1),        # Single swap / transposition
        ("kitten", "sitting", 3), # 2 substitutions + 1 insertion
        ("", "abc", 3),         # 3 insertions
        ("abc", "", 3),         # 3 deletions
        ("a cat", "an act", 2), # 1 insertion ('n') + 1 transposition ('ca' -> 'ac')
    ]
    
    for s_in, t_in, expected in test_cases:
        res = optimal_string_alignment_distance(s_in, t_in)
        assert res == expected, f"Failed for '{s_in}' -> '{t_in}': expected {expected}, got {res}"
    
    print("All test assertions passed successfully.")