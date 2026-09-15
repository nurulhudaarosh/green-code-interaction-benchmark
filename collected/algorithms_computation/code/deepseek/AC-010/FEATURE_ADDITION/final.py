import sys

def matrix_chain_order(dims, include_summary=False):
    """
    Find the minimum scalar multiplication cost and optimal parenthesization
    for multiplying matrices with dimensions p0..pn.
    
    Args:
        dims: List of dimensions [p0, p1, ..., pn] where matrix i has dimensions p[i-1] x p[i]
        include_summary: If True, return operation summary; if False, return only original fields
    
    Returns:
        If include_summary is False:
            (min_cost, parenthesization_string)
        If include_summary is True:
            (min_cost, parenthesization_string, operation_summary)
    """
    n = len(dims) - 1  # number of matrices
    
    # dp[i][j] = minimum cost to multiply matrices i through j (0-indexed)
    dp = [[0] * n for _ in range(n)]
    
    # split[i][j] = optimal split index for matrices i through j
    split = [[0] * n for _ in range(n)]
    
    # Track computational operations
    comparisons = 0  # number of cost comparisons made
    
    # length is the chain length (number of matrices in the subproblem)
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float('inf')
            
            # Try all possible split points k from i to j-1
            for k in range(i, j):
                cost = dp[i][k] + dp[k+1][j] + dims[i] * dims[k+1] * dims[j+1]
                comparisons += 1  # each potential split requires a comparison
                
                # Use smaller split index when costs are equal (strictly less for deterministic)
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    split[i][j] = k
    
    # Build parenthesization string
    def build_parenthesization(i, j):
        if i == j:
            return f"M{i+1}"
        else:
            k = split[i][j]
            left = build_parenthesization(i, k)
            right = build_parenthesization(k+1, j)
            return f"({left}{right})"
    
    # Prepare operation summary if requested
    operation_summary = None
    if include_summary:
        # Total number of subproblems solved
        subproblems_solved = 0
        for length in range(2, n + 1):
            subproblems_solved += (n - length + 1)
        
        # Major computational decisions:
        # - Number of subproblems evaluated
        # - Number of cost comparisons made
        # - Number of split decisions made (where cost < dp[i][j])
        # - Total split points considered
        operation_summary = {
            "subproblems_solved": subproblems_solved,
            "cost_comparisons": comparisons,
            "split_decisions_made": n * (n - 1) // 2,  # each subproblem has one split decision
            "total_split_points_considered": sum(range(1, n))  # sum of (length-1) for each length
        }
    
    # Handle edge cases
    if n == 0:
        result = (0, "")
    elif n == 1:
        result = (0, "M1")
    else:
        result = (dp[0][n-1], build_parenthesization(0, n-1))
    
    # Return appropriate result
    if include_summary:
        return result[0], result[1], operation_summary
    else:
        return result

def main():
    # Read input
    input_data = sys.stdin.read().strip().split()
    if not input_data:
        return
    
    # Parse arguments: first number is n, next n+1 numbers are dimensions
    # Optional third argument: if "summary" is present, include operation summary
    n = int(input_data[0])
    dims = list(map(int, input_data[1:n+2]))
    
    # Check if summary is requested (checking if any token is "summary")
    include_summary = False
    if len(input_data) > n + 2 and input_data[n+2].lower() == "summary":
        include_summary = True
    
    # Verify we have the correct number of dimensions
    if len(dims) != n + 1:
        print("Error: Invalid input format")
        return
    
    # Find optimal multiplication order
    if include_summary:
        min_cost, parenthesization, summary = matrix_chain_order(dims, include_summary=True)
        
        # Output results with summary
        print(f"Minimum scalar multiplications: {min_cost}")
        print(f"Optimal parenthesization: {parenthesization}")
        print(f"Operation summary:")
        print(f"  - Subproblems solved: {summary['subproblems_solved']}")
        print(f"  - Cost comparisons: {summary['cost_comparisons']}")
        print(f"  - Split decisions made: {summary['split_decisions_made']}")
        print(f"  - Total split points considered: {summary['total_split_points_considered']}")
    else:
        min_cost, parenthesization = matrix_chain_order(dims, include_summary=False)
        
        # Output original fields only
        print(f"Minimum scalar multiplications: {min_cost}")
        print(f"Optimal parenthesization: {parenthesization}")

if __name__ == "__main__":
    main()