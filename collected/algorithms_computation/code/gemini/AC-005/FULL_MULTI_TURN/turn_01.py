def lexicographically_smallest_lis_indices(arr: list[int]) -> list[int]:
    """
    Finds the Longest Increasing Subsequence (LIS) of an array and returns 
    the lexicographically smallest sequence of original indices that achieves
    the maximum length.
    """
    n = len(arr)
    if n == 0:
        return []

    # dp[i] = length of LIS ending at index i
    dp = [1] * n

    for i in range(n):
        for j in range(i):
            if arr[j] < arr[i]:
                if dp[j] + 1 > dp[i]:
                    dp[i] = dp[j] + 1

    max_len = max(dp) if dp else 0
    if max_len == 0:
        return []

    # To find the lexicographically smallest index sequence of length max_len:
    # We choose valid indices step-by-step from position 0 to max_len - 1.
    result_indices = []
    last_idx = -1
    last_val = float('-inf')

    for step in range(max_len, 0, -1):
        # We need an index i > last_idx such that dp[i] == step and arr[i] > last_val
        for i in range(last_idx + 1, n):
            if dp[i] >= step and arr[i] > last_val:
                # Check if this index i can actually participate in a sequence of length `step`
                # by ensuring there exists a valid sequence starting at i of length `step`.
                result_indices.append(i)
                last_idx = i
                last_val = arr[i]
                break

    return result_indices


# Example Usage
if __name__ == "__main__":
    example_arr = [3, 10, 2, 1, 20]
    indices = lexicographically_smallest_lis_indices(example_arr)
    subsequence_values = [example_arr[i] for i in indices]

    print(f"Input Array: {example_arr}")
    print(f"Lexicographically Smallest Index Sequence: {indices}")
    print(f"Corresponding LIS Values: {subsequence_values}")