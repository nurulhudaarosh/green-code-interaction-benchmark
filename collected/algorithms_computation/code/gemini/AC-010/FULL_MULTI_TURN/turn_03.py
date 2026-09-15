def matrix_chain_order(p, include_summary=False):
    """
    Computes minimum scalar multiplication cost and optimal parenthesization
    for a matrix chain with dimensions given by sequence p.
    
    Tie-breaking: Uses the smallest split index k when equal costs occur.
    
    :param p: Sequence of dimensions where matrix A_i has shape p[i-1] x p[i].
    :param include_summary: If True, returns a dict with 'cost', 'parenthesization',
                            and 'operation_summary'. Otherwise returns (cost, parenthesization).
    """
    if not p or len(p) < 2:
        res_cost, res_str = 0, ""
        if include_summary:
            return {
                "cost": res_cost,
                "parenthesization": res_str,
                "operation_summary": {
                    "matrices_count": 0,
                    "split_evaluations": 0
                }
            }
        return res_cost, res_str

    n = len(p) - 1  # Number of matrices

    if n == 1:
        res_cost, res_str = 0, "A1"
        if include_summary:
            return {
                "cost": res_cost,
                "parenthesization": res_str,
                "operation_summary": {
                    "matrices_count": 1,
                    "split_evaluations": 0
                }
            }
        return res_cost, res_str

    # m[i][j]: minimum scalar multiplication cost for A_i..A_j
    # s[i][j]: optimal split point k for subchain A_i..A_j
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    split_evaluations_count = 0

    # Interval DP over chain length l
    for l in range(2, n + 1):
        for i in range(1, n - l + 2):
            j = i + l - 1
            m[i][j] = float('inf')
            
            # Evaluate each split index k strictly in ascending order
            for k in range(i, j):
                split_evaluations_count += 1
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                
                # Strict inequality ensures smallest k is selected on tie
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k

    # Reconstruct parenthesization
    def build_string(i, j):
        if i == j:
            return f"A{i}"
        k = s[i][j]
        left = build_string(i, k)
        right = build_string(k + 1, j)
        return f"({left}{right})"

    min_cost = m[1][n]
    parenthesization = build_string(1, n)

    if include_summary:
        return {
            "cost": min_cost,
            "parenthesization": parenthesization,
            "operation_summary": {
                "matrices_count": n,
                "split_evaluations": split_evaluations_count,
                "subproblems_solved": (n * (n - 1)) // 2
            }
        }

    return min_cost, parenthesization


# Verification
if __name__ == "__main__":
    dimensions = [10, 30, 5, 60, 10]
    
    # Standard call (backward compatible)
    cost, string_fmt = matrix_chain_order(dimensions)
    print("Standard Output:")
    print(f"  Cost: {cost}")
    print(f"  Structure: {string_fmt}\n")

    # Feature call with summary
    result_with_summary = matrix_chain_order(dimensions, include_summary=True)
    print("Extended Output with Operation Summary:")
    print(f"  Cost: {result_with_summary['cost']}")
    print(f"  Structure: {result_with_summary['parenthesization']}")
    print(f"  Summary: {result_with_summary['operation_summary']}")