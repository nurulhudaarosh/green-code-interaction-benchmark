def longest_increasing_subsequence_indices(arr):
    n = len(arr)
    if n == 0:
        return []
    
    # dp[i] = length of LIS ending at i
    dp = [1] * n
    # seq[i] = tuple of indices (0-based) of the lexicographically smallest LIS ending at i
    seq = [None] * n
    for i in range(n):
        seq[i] = (i,)
    
    for i in range(n):
        for j in range(i):
            if arr[j] < arr[i]:
                if dp[j] + 1 > dp[i]:
                    dp[i] = dp[j] + 1
                    seq[i] = seq[j] + (i,)
                elif dp[j] + 1 == dp[i]:
                    # Compare lexicographically the index sequences
                    candidate = seq[j] + (i,)
                    if candidate < seq[i]:
                        seq[i] = candidate
    
    # Find max length
    max_len = max(dp)
    # Find the lexicographically smallest index sequence among those with max_len
    best_seq = None
    for i in range(n):
        if dp[i] == max_len:
            if best_seq is None or seq[i] < best_seq:
                best_seq = seq[i]
    
    # Convert to 1-based indices
    return [idx + 1 for idx in best_seq]


# Example usage:
if __name__ == "__main__":
    # Example: arr = [1, 3, 2, 4]
    # LIS length = 3, possible: [1,3,4] (indices 1,2,4) and [1,2,4] (indices 1,3,4)
    # Lexicographically smallest index sequence: [1,2,4] or [1,3,4]? Compare: (1,2,4) < (1,3,4) => choose (1,2,4)
    arr = [1, 3, 2, 4]
    print(longest_increasing_subsequence_indices(arr))  # Output: [1, 2, 4]
    
    arr2 = [2, 1, 3]
    # LIS length 2, possible: [2,3] (indices 1,3) and [1,3] (indices 2,3) -> lexicographically smallest: [1,3]? Wait: index seq (1,3) vs (2,3) => (1,3) is smaller
    print(longest_increasing_subsequence_indices(arr2))  # [1, 3]
    
    arr3 = [3, 2, 1]
    print(longest_increasing_subsequence_indices(arr3))  # [1] (or [2] or [3]? All length 1, lexicographically smallest: [1])