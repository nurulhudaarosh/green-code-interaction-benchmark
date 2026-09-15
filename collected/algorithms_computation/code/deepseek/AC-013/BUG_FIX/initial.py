def build_prefix_sum(matrix):
    """Build 2D prefix sum table for O(1) sum queries."""
    if not matrix or not matrix[0]:
        return []
    
    rows, cols = len(matrix), len(matrix[0])
    # Create (rows+1) x (cols+1) table with padding
    prefix = [[0] * (cols + 1) for _ in range(rows + 1)]
    
    for i in range(rows):
        for j in range(cols):
            prefix[i + 1][j + 1] = (
                matrix[i][j] 
                + prefix[i][j + 1] 
                + prefix[i + 1][j] 
                - prefix[i][j]
            )
    
    return prefix


def query_sum(prefix, r1, c1, r2, c2):
    """Get sum of rectangle using inclusion-exclusion in O(1)."""
    return (
        prefix[r2 + 1][c2 + 1]
        - prefix[r1][c2 + 1]
        - prefix[r2 + 1][c1]
        + prefix[r1][c1]
    )


def query_min_max(matrix, r1, c1, r2, c2):
    """Scan rectangle directly for min and max in O(area)."""
    min_val = float('inf')
    max_val = float('-inf')
    
    for i in range(r1, r2 + 1):
        for j in range(c1, c2 + 1):
            val = matrix[i][j]
            if val < min_val:
                min_val = val
            if val > max_val:
                max_val = val
    
    return min_val, max_val


def process_queries(matrix, queries):
    """
    Process multiple rectangle queries.
    
    Args:
        matrix: 2D list of integers
        queries: List of tuples (r1, c1, r2, c2)
    
    Returns:
        List of tuples (sum, min, max) for each query
    """
    if not matrix or not matrix[0]:
        return []
    
    # Preprocess: build prefix sum table
    prefix = build_prefix_sum(matrix)
    
    results = []
    for r1, c1, r2, c2 in queries:
        # Validate coordinates
        rows, cols = len(matrix), len(matrix[0])
        if not (0 <= r1 <= r2 < rows and 0 <= c1 <= c2 < cols):
            raise ValueError(f"Invalid query coordinates: ({r1}, {c1}, {r2}, {c2})")
        
        # Get sum in O(1)
        rect_sum = query_sum(prefix, r1, c1, r2, c2)
        
        # Get min/max by scanning
        rect_min, rect_max = query_min_max(matrix, r1, c1, r2, c2)
        
        results.append((rect_sum, rect_min, rect_max))
    
    return results


def main():
    """Demonstrate the solution with test cases."""
    # Test matrix
    matrix = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9, 10, 11, 12],
        [13, 14, 15, 16]
    ]
    
    # Test queries: (r1, c1, r2, c2) inclusive
    queries = [
        (0, 0, 1, 1),   # Top-left 2x2
        (1, 1, 2, 2),   # Middle 2x2
        (0, 0, 3, 3),   # Entire matrix
        (2, 0, 3, 1),   # Bottom-left 2x2
        (0, 3, 3, 3),   # Rightmost column
    ]
    
    print("Matrix:")
    for row in matrix:
        print(row)
    print()
    
    results = process_queries(matrix, queries)
    
    print("Query Results:")
    print("-" * 60)
    for (r1, c1, r2, c2), (s, mn, mx) in zip(queries, results):
        print(f"Rect ({r1},{c1}) to ({r2},{c2}):")
        print(f"  Sum = {s}, Min = {mn}, Max = {mx}")
    
    # Verify with brute force
    print("\n" + "=" * 60)
    print("Verification with brute force:")
    print("-" * 60)
    
    for (r1, c1, r2, c2), (s, mn, mx) in zip(queries, results):
        # Brute force calculation
        brute_sum = 0
        brute_min = float('inf')
        brute_max = float('-inf')
        
        for i in range(r1, r2 + 1):
            for j in range(c1, c2 + 1):
                val = matrix[i][j]
                brute_sum += val
                brute_min = min(brute_min, val)
                brute_max = max(brute_max, val)
        
        assert s == brute_sum, f"Sum mismatch: {s} != {brute_sum}"
        assert mn == brute_min, f"Min mismatch: {mn} != {brute_min}"
        assert mx == brute_max, f"Max mismatch: {mx} != {brute_max}"
        
        print(f"✓ Query ({r1},{c1},{r2},{c2}) verified")
    
    print("\nAll queries verified successfully!")
    
    # Performance demonstration
    print("\n" + "=" * 60)
    print("Performance characteristics:")
    print("-" * 60)
    print("• Preprocessing: O(rows × cols) for prefix sum table")
    print("• Sum query: O(1) using prefix sum inclusion-exclusion")
    print("• Min/Max query: O(area) direct scan")
    print("• Space: O(rows × cols) for prefix sum table")


if __name__ == "__main__":
    main()