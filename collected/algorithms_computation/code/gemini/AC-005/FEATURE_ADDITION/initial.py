def longest_increasing_subsequence_indices(arr: list[int]) -> list[int]:
    """
    Finds the strictly increasing subsequence of maximum length and returns
    the lexicographically smallest sequence of original 0-based indices.
    
    Time Complexity: O(n^2)
    Space Complexity: O(n^2) for explicit index sequence path comparisons.
    """
    n = len(arr)
    if n == 0:
        return []

    # dp[i] stores the length of the LIS ending at index i
    dp = [1] * n
    
    # path[i] stores the complete 0-based index sequence ending at i
    path = [[i] for i in range(n)]

    for i in range(n):
        for j in range(i):
            if arr[j] < arr[i]:
                candidate_len = dp[j] + 1
                candidate_path = path[j] + [i]
                
                # Update if we find a strictly longer sequence, or a sequence
                # of equal length with a lexicographically smaller index path.
                if candidate_len > dp[i]:
                    dp[i] = candidate_len
                    path[i] = candidate_path
                elif candidate_len == dp[i] and candidate_path < path[i]:
                    path[i] = candidate_path

    # Find maximum LIS length
    max_len = max(dp)
    
    # Among all paths achieving max_len, pick the lexicographically smallest index path
    best_path = None
    for i in range(n):
        if dp[i] == max_len:
            if best_path is None or path[i] < best_path:
                best_path = path[i]

    return best_path if best_path is not None else []


# Example Usage
if __name__ == "__main__":
    nums = [10, 22, 9, 33, 21, 50, 41, 60, 80]
    result_indices = longest_increasing_subsequence_indices(nums)
    result_values = [nums[idx] for idx in result_indices]
    
    print(f"Input Array: {nums}")
    print(f"Lexicographically Smallest Index Path: {result_indices}")
    print(f"Corresponding LIS Values: {result_values}")