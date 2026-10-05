def osa_distance(s1: str, s2: str) -> int:
    """
    Computes the edit distance using insertion, deletion, substitution,
    and adjacent transposition, each costing 1 (Optimal String Alignment distance).
    """
    m, n = len(s1), len(s2)
    
    # Initialize DP table of size (m + 1) x (n + 1)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Base cases: cost of transforming to/from empty prefixes
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
        
    # Populate the DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            
            # Standard Levenshtein transitions
            dp[i][j] = min(
                dp[i - 1][j] + 1,        # Deletion
                dp[i][j - 1] + 1,        # Insertion
                dp[i - 1][j - 1] + cost  # Substitution / Match
            )
            
            # Adjacent transposition transition
            if (
                i > 1 
                and j > 1 
                and s1[i - 1] == s2[j - 2] 
                and s1[i - 2] == s2[j - 1]
            ):
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)
                
    return dp[m][n]


if __name__ == "__main__":
    test_cases = [
        ("kitten", "sitting"),   # Standard substitution + insertion: 3
        ("ca", "abc"),           # Transposition + insertion: 2
        ("abcd", "abdc"),        # Adjacent swap: 1
        ("hello", "hello"),      # Exact match: 0
        ("", "abc"),             # All insertions: 3
        ("abc", ""),             # All deletions: 3
    ]
    for s1, s2 in test_cases:
        print(f"dist('{s1}', '{s2}') = {osa_distance(s1, s2)}")