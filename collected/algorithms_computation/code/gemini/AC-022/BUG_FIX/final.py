def edit_distance_with_transposition(s: str, t: str) -> tuple[int, list[str]]:
    """
    Computes the edit distance (OSA) and a deterministic path of operations.
    Tie breaking priority: Match > Transpose > Substitute > Insert > Delete.
    """
    m, n = len(s), len(t)
    
    # 1. Build DP Table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
        
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s[i - 1] == t[j - 1] else 1
            
            # Standard transitions
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # Delete
                dp[i][j - 1] + 1,       # Insert
                dp[i - 1][j - 1] + cost # Substitute / Match
            )
            
            # Explicit adjacent transposition transition
            if i > 1 and j > 1 and s[i - 1] == t[j - 2] and s[i - 2] == t[j - 1]:
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)
                
    # 2. Traceback with Deterministic Tie Handling
    i, j = m, n
    ops = []
    
    while i > 0 or j > 0:
        moves = {}
        
        # Check Substitution / Match
        if i > 0 and j > 0:
            cost = 0 if s[i - 1] == t[j - 1] else 1
            if dp[i][j] == dp[i - 1][j - 1] + cost:
                if cost == 0:
                    moves[0] = ('Match', i - 1, j - 1)
                else:
                    moves[2] = (f"Substitute '{s[i-1]}' with '{t[j-1]}'", i - 1, j - 1)
                    
        # Check Transposition
        if i > 1 and j > 1 and s[i - 1] == t[j - 2] and s[i - 2] == t[j - 1]:
            if dp[i][j] == dp[i - 2][j - 2] + 1:
                moves[1] = (f"Transpose '{s[i-2]}{s[i-1]}'", i - 2, j - 2)
                
        # Check Insertion
        if j > 0:
            if dp[i][j] == dp[i][j - 1] + 1:
                moves[3] = (f"Insert '{t[j-1]}'", i, j - 1)
                
        # Check Deletion
        if i > 0:
            if dp[i][j] == dp[i - 1][j] + 1:
                moves[4] = (f"Delete '{s[i-1]}'", i - 1, j)
                
        # Enforce deterministic tie-breaker by selecting the lowest priority integer
        best_priority = min(moves.keys())
        op_desc, next_i, next_j = moves[best_priority]
        
        # Omit 'Match' from final explicit script to focus on actual edits, 
        # or include it if requested. Here we include all for traceability.
        ops.append(op_desc)
        i, j = next_i, next_j
        
    ops.reverse()
    return dp[m][n], ops


if __name__ == "__main__":
    # Example demonstrating the deterministic tie break handling
    distance, path = edit_distance_with_transposition("ab", "bc")
    
    print(f"Distance: {distance}")
    print("Deterministic Path:")
    for step in path:
        print(f" - {step}")