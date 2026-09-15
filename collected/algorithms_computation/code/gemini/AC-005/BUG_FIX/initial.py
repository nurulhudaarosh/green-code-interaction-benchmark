def lexicographically_smallest_lis_indices(arr: list[int]) -> list[int]:
    """
    Finds the lexicographically smallest index sequence corresponding to 
    a strictly increasing subsequence of maximum length.
    
    Time Complexity: O(n^2)
    Space Complexity: O(n^2)
    """
    n = len(arr)
    if n == 0:
        return []

    dp = [1] * n
    best_path = [(i,) for i in range(n)]

    for i in range(n):
        for j in range(i):
            if arr[j] < arr[i]:
                candidate_length = dp[j] + 1
                candidate_path = best_path[j] + (i,)

                if candidate_length > dp[i]:
                    dp[i] = candidate_length
                    best_path[i] = candidate_path
                elif candidate_length == dp[i]:
                    if candidate_path < best_path[i]:
                        best_path[i] = candidate_path

    max_len = max(dp)
    optimal_path = None

    for i in range(n):
        if dp[i] == max_len:
            if optimal_path is None or best_path[i] < optimal_path:
                optimal_path = best_path[i]

    return list(optimal_path)


# Example usage
if __name__ == "__main__":
    nums = [10, 22, 9, 33, 21, 50, 41, 60, 80]
    indices = lexicographically_smallest_lis_indices(nums)
    values = [nums[i] for i in indices]
    
    print(f"Original Array: {nums}")
    print(f"Optimal Indices: {indices}")
    print(f"Subsequence Values: {values}")