def get_lexicographically_smallest_lis_indices(arr: list[int]) -> list[int]:
    """
    Finds a strictly increasing subsequence of maximum length from `arr`
    and returns the lexicographically smallest sequence of original indices.
    
    Time Complexity: O(N^2)
    Space Complexity: O(N^2)
    """
    n = len(arr)
    if n == 0:
        return []

    dp = [1] * n
    # Stores the optimal predecessor path for each index to reconstruct the sequence easily
    paths = [[i] for i in range(n)]

    for i in range(n):
        for j in range(i):
            if arr[j] < arr[i]:
                candidate_path = paths[j] + [i]
                candidate_len = len(candidate_path)

                if candidate_len > dp[i]:
                    dp[i] = candidate_len
                    paths[i] = candidate_path
                elif candidate_len == dp[i]:
                    # Tie-breaking: keep the lexicographically smaller index path
                    if candidate_path < paths[i]:
                        paths[i] = candidate_path

    # Find the maximum LIS length
    max_len = max(dp)

    # Gather all candidate paths that achieve max_len and pick the lexicographically smallest
    best_path = min(path for path in paths if len(path) == max_len)

    return best_path


# Example usage
if __name__ == "__main__":
    sample_input = [10, 22, 9, 33, 21, 50, 41, 60, 80]
    indices = get_lexicographically_smallest_lis_indices(sample_input)
    values = [sample_input[i] for i in indices]
    
    print(f"Input Array: {sample_input}")
    print(f"Optimal Original Indices: {indices}")
    print(f"Corresponding Subsequence Values: {values}")