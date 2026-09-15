def lexicographically_smallest_lis(arr: list[int]) -> list[int]:
    """
    Finds the strictly increasing subsequence of maximum length from `arr`.
    Breaks ties by returning the subsequence corresponding to the 
    lexicographically smallest 0-based index sequence.
    """
    n = len(arr)
    if n == 0:
        return []

    dp = [1] * n
    parent = [-1] * n

    # Helper function to reconstruct index path ending at index `idx`
    def get_index_path(idx: int) -> list[int]:
        path = []
        curr = idx
        while curr != -1:
            path.append(curr)
            curr = parent[curr]
        return path[::-1]

    # Populate DP and parent tables
    for i in range(n):
        for j in range(i):
            if arr[j] < arr[i]:
                cand_len = dp[j] + 1
                if cand_len > dp[i]:
                    dp[i] = cand_len
                    parent[i] = j
                elif cand_len == dp[i]:
                    # Tie-breaking for predecessor choice at index i:
                    # Choose j if its index path is lexicographically smaller
                    path_j = get_index_path(j)
                    path_prev = get_index_path(parent[i])
                    if path_j < path_prev:
                        parent[i] = j

    # Find the maximum LIS length
    max_len = max(dp)

    # Gather all candidate ending indices that achieve max_len
    best_end_idx = -1
    best_path = None

    for i in range(n):
        if dp[i] == max_len:
            path = get_index_path(i)
            if best_path is None or path < best_path:
                best_path = path
                best_end_idx = i

    # Reconstruct and return the element values from the best index path
    return [arr[i] for i in best_path]


# Example Usage & Verification
if __name__ == "__main__":
    test_arr = [3, 1, 4, 1, 5, 9, 2, 6, 5]
    result = lexicographically_smallest_lis(test_arr)
    print("Input Array:", test_arr)
    print("Lexicographically Smallest LIS:", result)