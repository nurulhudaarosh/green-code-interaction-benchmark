def matrix_chain_order(p):
    """
    Find optimal parenthesization for matrix chain multiplication.
    
    Args:
        p: List of dimensions where matrix i has dimensions p[i-1] × p[i]
        
    Returns:
        tuple: (minimum_cost, parenthesization_string)
    """
    n = len(p) - 1  # number of matrices
    
    if n == 0:
        return 0, ""
    if n == 1:
        return 0, "M1"
    
    # dp[i][j] = minimum cost to multiply matrices i..j (1-indexed)
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    split = [[0] * (n + 1) for _ in range(n + 1)]
    
    # length of chain to consider
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1
            dp[i][j] = float('inf')
            
            # Try all possible split positions
            for k in range(i, j):
                cost = dp[i][k] + dp[k+1][j] + p[i-1] * p[k] * p[j]
                
                # Choose smaller cost, or if equal, choose smaller k
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    split[i][j] = k
                elif cost == dp[i][j] and k < split[i][j]:
                    split[i][j] = k
    
    # Build parenthesization string
    def build_parenthesization(i, j):
        if i == j:
            return f"M{i}"
        k = split[i][j]
        left = build_parenthesization(i, k)
        right = build_parenthesization(k+1, j)
        return f"({left}{right})"
    
    min_cost = dp[1][n]
    parenthesization = build_parenthesization(1, n)
    
    return min_cost, parenthesization


def matrix_chain_multiply(p):
    """
    Wrapper function that returns the formatted output.
    
    Args:
        p: List of dimensions
        
    Returns:
        str: Formatted output string
    """
    if len(p) < 2:
        return "0\n"
    
    cost, paren = matrix_chain_order(p)
    return f"{cost}\n{paren}\n"


# Comprehensive test suite for difficult cases
if __name__ == "__main__":
    print("=" * 80)
    print("MATRIX CHAIN PLANNER - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    # Test 1: Equal costs at top level - should choose smallest split
    # p = [2, 2, 3, 3]
    # Both (M1(M2M3)) and ((M1M2)M3) cost 30
    # Smallest split index is k=1, so should output (M1(M2M3))
    p1 = [2, 2, 3, 3]
    print("\nTest 1 - Equal costs at top level:")
    print("Input:", p1)
    print("Expected: 30\n(M1(M2M3))")
    print("Output:")
    print(matrix_chain_multiply(p1))
    print("-" * 80)
    
    # Test 2: Equal costs at multiple levels
    # p = [1, 2, 4, 8, 16]
    # Multiple optimal solutions exist at different levels
    p2 = [1, 2, 4, 8, 16]
    print("\nTest 2 - Equal costs at multiple levels:")
    print("Input:", p2)
    print("Output:")
    print(matrix_chain_multiply(p2))
    print("-" * 80)
    
    # Test 3: Repeated values creating ties
    # p = [2, 3, 2, 3, 2]
    # Creates symmetrical structure with multiple optimal solutions
    p3 = [2, 3, 2, 3, 2]
    print("\nTest 3 - Repeated values with ties:")
    print("Input:", p3)
    print("Output:")
    print(matrix_chain_multiply(p3))
    print("-" * 80)
    
    # Test 4: All equal dimensions
    # p = [5, 5, 5, 5, 5, 5]
    # Highly symmetrical, many optimal solutions
    p4 = [5, 5, 5, 5, 5, 5]
    print("\nTest 4 - All equal dimensions:")
    print("Input:", p4)
    print("Output:")
    print(matrix_chain_multiply(p4))
    print("-" * 80)
    
    # Test 5: Classic example with unique optimal
    p5 = [10, 100, 5, 50]
    print("\nTest 5 - Classic example (unique optimal):")
    print("Input:", p5)
    print("Expected: 7500\n((M1M2)M3)")
    print("Output:")
    print(matrix_chain_multiply(p5))
    print("-" * 80)
    
    # Test 6: Larger chain with repeated values
    # Creates complex tie scenarios
    p6 = [3, 4, 6, 8, 3, 4, 6, 8]
    print("\nTest 6 - Larger chain with repeated values:")
    print("Input:", p6)
    print("Output:")
    print(matrix_chain_multiply(p6))
    print("-" * 80)
    
    # Test 7: Equal costs at multiple split positions
    # Need to verify smallest k is chosen at each level
    # p = [2, 3, 6, 9, 2] creates multiple equal-cost scenarios
    p7 = [2, 3, 6, 9, 2]
    print("\nTest 7 - Multiple equal split positions:")
    print("Input:", p7)
    print("Output:")
    print(matrix_chain_multiply(p7))
    print("-" * 80)
    
    # Test 8: Single matrix
    p8 = [10, 20]
    print("\nTest 8 - Single matrix:")
    print("Input:", p8)
    print("Expected: 0\nM1")
    print("Output:")
    print(matrix_chain_multiply(p8))
    print("-" * 80)
    
    # Test 9: Two matrices
    p9 = [10, 20, 30]
    print("\nTest 9 - Two matrices:")
    print("Input:", p9)
    print("Expected: 6000\n(M1M2)")
    print("Output:")
    print(matrix_chain_multiply(p9))
    print("-" * 80)
    
    # Test 10: Empty input
    p10 = []
    print("\nTest 10 - Empty input:")
    print("Input:", p10)
    print("Expected: 0")
    print("Output:")
    print(matrix_chain_multiply(p10))
    print("-" * 80)
    
    # Test 11: Textbook example with 6 matrices
    p11 = [30, 35, 15, 5, 10, 20, 25]
    print("\nTest 11 - Textbook example (6 matrices):")
    print("Input:", p11)
    print("Expected: 15125\n((M1(M2M3))((M4M5)M6))")
    print("Output:")
    print(matrix_chain_multiply(p11))
    print("-" * 80)
    
    # Test 12: Case with exact mathematical equality at multiple levels
    # p = [2, 3, 4, 6, 9] creates ties at different levels
    p12 = [2, 3, 4, 6, 9]
    print("\nTest 12 - Mathematical equality at multiple levels:")
    print("Input:", p12)
    print("Output:")
    print(matrix_chain_multiply(p12))
    print("-" * 80)
    
    # Test 13: All equal with 7 matrices
    p13 = [3, 3, 3, 3, 3, 3, 3, 3]
    print("\nTest 13 - All equal with 7 matrices:")
    print("Input:", p13)
    print("Output:")
    print(matrix_chain_multiply(p13))
    print("-" * 80)
    
    # Test 14: Alternating values creating ties
    p14 = [4, 2, 4, 2, 4, 2, 4]
    print("\nTest 14 - Alternating values:")
    print("Input:", p14)
    print("Output:")
    print(matrix_chain_multiply(p14))
    print("-" * 80)
    
    # Test 15: Large dimensions with repeated patterns
    p15 = [100, 50, 100, 50, 100, 50, 100]
    print("\nTest 15 - Large dimensions with repeated patterns:")
    print("Input:", p15)
    print("Output:")
    print(matrix_chain_multiply(p15))
    print("-" * 80)
    
    print("=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)