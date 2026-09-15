from typing import List, Tuple

def min_sse_clustering(points: List[float], k: int) -> Tuple[float, List[int]]:
    """
    Sorts 1D points and partitions them into k contiguous clusters 
    minimizing total SSE.
    
    Returns:
        (min_cost, boundary_indices)
    """
    if not points or k <= 0:
        return 0.0, []
    
    sorted_x = sorted(points)
    n = len(sorted_x)
    k = min(k, n)
    
    # 1. Compute Prefix Sums for O(1) interval cost calculations
    P = [0.0] * (n + 1)   # Prefix sum of x
    P2 = [0.0] * (n + 1)  # Prefix sum of x^2
    for i in range(n):
        P[i + 1] = P[i] + sorted_x[i]
        P2[i + 1] = P2[i] + sorted_x[i] ** 2

    def get_cost(i: int, j: int) -> float:
        """Returns SSE for sorted_x[i...j] inclusive."""
        count = j - i + 1
        sum_x = P[j + 1] - P[i]
        sum_x2 = P2[j + 1] - P2[i]
        return sum_x2 - (sum_x ** 2) / count

    # 2. DP Table Initialization
    # dp[c][j]: min cost to partition sorted_x[0...j] into c clusters
    dp = [[float('inf')] * n for _ in range(k + 1)]
    split = [[-1] * n for _ in range(k + 1)]

    # Base case: 1 cluster
    for j in range(n):
        dp[1][j] = get_cost(0, j)
        split[1][j] = -1

    # DP Transitions
    for c in range(2, k + 1):
        for j in range(c - 1, n):
            # Try all possible split points m for the last cluster
            for m in range(c - 2, j):
                cost = dp[c - 1][m] + get_cost(m + 1, j)
                if cost < dp[c][j]:
                    dp[c][j] = cost
                    split[c][j] = m

    # 3. Reconstruct cluster boundaries
    boundaries = [0] * k
    curr = n - 1
    for c in range(k, 0, -1):
        boundaries[c - 1] = curr
        curr = split[c][curr]

    min_cost = dp[k][n - 1]
    return min_cost, boundaries


# Example Usage:
if __name__ == "__main__":
    data = [10.0, 2.0, 1.0, 12.0, 3.0, 20.0, 22.0]
    num_clusters = 3
    
    cost, boundaries = min_sse_clustering(data, num_clusters)
    sorted_data = sorted(data)
    
    print(f"Sorted Points: {sorted_data}")
    print(f"Minimum SSE Cost: {cost:.4f}")
    print(f"End Boundary Indices: {boundaries}")
    
    # Print out the explicit clusters
    start = 0
    for idx, end in enumerate(boundaries):
        cluster = sorted_data[start : end + 1]
        print(f" Cluster {idx + 1}: {cluster} (End Index: {end})")
        start = end + 1