def optimal_string_alignment_distance(s1: str, s2: str) -> int:
    """
    Computes the edit distance between s1 and s2 with operations:
    - insertion (cost 1)
    - deletion (cost 1)
    - substitution (cost 1)
    - adjacent transposition (cost 1)
    
    Uses dynamic programming with an explicit transposition transition.
    """
    m, n = len(s1), len(s2)
    
    # Initialize DP table of size (m + 1) x (n + 1)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Base cases: transforming prefixes to/from empty strings
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
        
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            
            # Standard operations: deletion, insertion, substitution
            dp[i][j] = min(
                dp[i - 1][j] + 1,        # Deletion
                dp[i][j - 1] + 1,        # Insertion
                dp[i - 1][j - 1] + cost   # Match or Substitution
            )
            
            # Adjacent transposition
            if i > 1 and j > 1 and s1[i - 1] == s2[j - 2] and s1[i - 2] == s2[j - 1]:
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)
                
    return dp[m][n]


if __name__ == "__main__":
    # Test cases
    test_pairs = [
        ("kitten", "sitting"),   # 3 (sub k->s, sub e->i, insert g)
        ("rosettacode", "raisethysword"), # 8
        ("ca", "abc"),           # 3 under OSA (transpose 'ca' -> 'ac', then insert 'b')
        ("ab", "ba"),           # 1 (transposition)
        ("", "abc"),            # 3 (insertions)
        ("abcdef", "abcdef"),   # 0
    ]
    
    for str1, str2 in test_pairs:
        dist = optimal_string_alignment_distance(str1, str2)
        print(f"dist('{str1}', '{str2}') = {dist}")