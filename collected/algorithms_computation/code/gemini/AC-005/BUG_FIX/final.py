def lexicographically_smallest_lis_indices(arr: list[int]) -> list[int]:
    """
    Finds the lexicographically smallest index sequence corresponding to 
    a strictly increasing subsequence of maximum length using quadratic 
    dynamic programming with explicit index-sequence tie breaking.
    
    Time Complexity: O(n^2)
    Space Complexity: O(n^2)
    """
    n = len(arr)
    if n == 0:
        return []

    # dp[i] stores the max length of LIS ending at index i
    dp = [1] * n
    # best_path[i] stores the lexicographically smallest index tuple for LIS ending at i
    best_path = [(i,) for i in range(n)]

    for i in range(n):
        for j in range(i):
            if arr[j] < arr[i]:
                candidate_len = dp[j] + 1
                candidate_path = best_path[j] + (i,)

                if candidate_len > dp[i]:
                    dp[i] = candidate_len
                    best_path[i] = candidate_path
                elif candidate_len == dp[i]:
                    if candidate_path < best_path[i]:
                        best_path[i] = candidate_path

    # Find maximum subsequence length across all ending indices
    max_len = max(dp)
    
    # Pick the lexicographically smallest path among all paths achieving max_len
    optimal_path = min(
        best_path[i] for i in range(n) if dp[i] == max_len
    )

    return list(optimal_path)


if __name__ == "__main__":
    # Test Example
    test_arr = [2, 1, 3, 2, 4]
    indices = lexicographically_smallest_lis_indices(test_arr)
    print(f"Input Array: {test_arr}")
    print(f"Optimal Index Sequence: {indices}")
    print(f"Corresponding Subsequence: {[test_arr[i] for i in indices]}")