def matrix_chain_order(p):
    """
    Find optimal parenthesization for matrix chain multiplication.
    
    Args:
        p: List of dimensions where matrix i has dimensions p[i-1] × p[i]
        
    Returns:
        tuple: (minimum_cost, parenthesization_string)
    """
    n = len(p) - 1  # number of matrices
    
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
    
    if n == 0:
        return 0, ""
    elif n == 1:
        return 0, "M1"
    
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


# Example usage and test cases
if __name__ == "__main__":
    # Test case 1: Example from problem
    p1 = [10, 100, 5, 50]
    print("Test 1:", matrix_chain_multiply(p1))
    # Expected: 7500, ((M1M2)M3) or (M1(M2M3))? 
    # Let's check: dimensions 10x100, 100x5, 5x50
    # Option 1: (M1M2)M3: 10*100*5 + 10*5*50 = 5000 + 2500 = 7500
    # Option 2: M1(M2M3): 100*5*50 + 10*100*50 = 25000 + 50000 = 75000
    # So optimal is 7500 with split at k=1
    
    # Test case 2: Multiple optimal solutions
    p2 = [30, 35, 15, 5, 10, 20, 25]
    print("Test 2:", matrix_chain_multiply(p2))
    
    # Test case 3: Single matrix
    p3 = [10, 20]
    print("Test 3:", matrix_chain_multiply(p3))
    
    # Test case 4: Three matrices with equal costs
    # Dimensions: 2x3, 3x4, 4x2
    # Cost (M1M2)M3: 2*3*4 + 2*4*2 = 24 + 16 = 40
    # Cost M1(M2M3): 3*4*2 + 2*3*2 = 24 + 12 = 36
    # Not equal, let's find equal case
    # Try: 2x3, 3x1, 1x4
    # (M1M2)M3: 2*3*1 + 2*1*4 = 6 + 8 = 14
    # M1(M2M3): 3*1*4 + 2*3*4 = 12 + 24 = 36
    # Not equal
    # Try: 5x4, 4x3, 3x2
    # (M1M2)M3: 5*4*3 + 5*3*2 = 60 + 30 = 90
    # M1(M2M3): 4*3*2 + 5*4*2 = 24 + 40 = 64
    # Different
    # Equal case: a=2, b=3, c=4, d=2
    # (M1M2)M3: 2*3*4 + 2*4*2 = 24+16=40
    # M1(M2M3): 3*4*2 + 2*3*2 = 24+12=36
    # Still different
    # For equal costs: p0*p1*p2 + p0*p2*p3 = p1*p2*p3 + p0*p1*p3
    # p0*p2*(p1+p3) = p1*p3*(p2+p0)
    # Try p=[1,2,3,1]: (M1M2)M3: 1*2*3 + 1*3*1 = 6+3=9
    # M1(M2M3): 2*3*1 + 1*2*1 = 6+2=8
    # Try p=[2,3,2,3]: (M1M2)M3: 2*3*2 + 2*2*3 = 12+12=24
    # M1(M2M3): 3*2*3 + 2*3*3 = 18+18=36
    # Still different
    # Try p=[3,4,3,4]: (M1M2)M3: 3*4*3 + 3*3*4 = 36+36=72
    # M1(M2M3): 4*3*4 + 3*4*4 = 48+48=96
    # Try p=[2,4,1,3]: (M1M2)M3: 2*4*1 + 2*1*3 = 8+6=14
    # M1(M2M3): 4*1*3 + 2*4*3 = 12+24=36
    # Let's try a systematic approach: p=[a,b,c,d]
    # Equal when: a*b*c + a*c*d = b*c*d + a*b*d
    # a*c*(b+d) = b*d*(c+a)
    # Try a=2,b=3,c=5,d=3: 2*5*(3+3)=60, 3*3*(5+2)=63 close
    # a=2,b=6,c=3,d=4: 2*3*(6+4)=60, 6*4*(3+2)=120 no
    # a=3,b=6,c=2,d=4: 3*2*(6+4)=60, 6*4*(2+3)=120 no
    # I'll use a known equal case: p=[1,2,4,8,16] - not equal
    
    # Let's test with p=[1, 2, 3, 4] (we saw not equal)
    # Let's find equal case numerically:
    # Need: a*c*(b+d) = b*d*(a+c)
    # Try a=2,b=3,c=5,d=2: 2*5*(3+2)=50, 3*2*(5+2)=42 no
    # Try a=3,b=4,c=6,d=3: 3*6*(4+3)=126, 4*3*(6+3)=108 no
    # Try a=4,b=5,c=10,d=4: 4*10*(5+4)=360, 5*4*(10+4)=280 no
    # This is taking too long, let's use a simpler equal case
    
    # Equal case: p=[2, 3, 6, 4]
    # (M1M2)M3: 2*3*6 + 2*6*4 = 36 + 48 = 84
    # M1(M2M3): 3*6*4 + 2*3*4 = 72 + 24 = 96
    # Not equal
    
    # p=[3, 4, 6, 8]
    # (M1M2)M3: 3*4*6 + 3*6*8 = 72 + 144 = 216
    # M1(M2M3): 4*6*8 + 3*4*8 = 192 + 96 = 288
    
    # I'll use a known case where multiple optimal splits exist
    # p=[1, 2, 4, 8] gives: (1*2*4 + 1*4*8) = 8+32=40, (2*4*8 + 1*2*8) = 64+16=80
    # p=[2, 3, 6, 9]: (2*3*6 + 2*6*9) = 36+108=144, (3*6*9 + 2*3*9) = 162+54=216
    
    # Actually, let's create a proper equal case:
    # Need: p0*p2*(p1+p3) = p1*p3*(p0+p2)
    # Let p0=2, p2=3: 6*(p1+p3) = p1*p3*5
    # Try p1=4, p3=6: 6*10 = 60, 4*6*5=120 no
    # p1=6, p3=3: 6*9=54, 6*3*5=90 no
    # p1=3, p3=12: 6*15=90, 3*12*5=180 no
    # Let's solve: 6*(p1+p3) = 5*p1*p3
    # p1+p3 = (5/6)*p1*p3
    # 6p1+6p3 = 5p1p3
    # Let p1=2: 12+6p3 = 10p3 => 12 = 4p3 => p3=3
    # So p=[2, 2, 3, 3]
    # Check: (M1M2)M3: 2*2*3 + 2*3*3 = 12+18=30
    # M1(M2M3): 2*3*3 + 2*2*3 = 18+12=30
    # Equal! And smallest split is k=1, so should choose (M1M2)M3
    
    p_equal = [2, 2, 3, 3]
    print("Test 4 (equal costs):", matrix_chain_multiply(p_equal))
    # Should output: 30\n((M1M2)M3)\n
    
    # Test with 4 matrices where multiple optimal splits exist
    # p=[2, 3, 4, 3, 4] 
    # We'll test another case
    
    # More extensive test
    p5 = [5, 4, 6, 2, 7]
    print("Test 5:", matrix_chain_multiply(p5))