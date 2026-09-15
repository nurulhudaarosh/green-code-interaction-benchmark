def lexicographically_smallest_lis_indices(arr: list[int]) -> list[int]:
    """
    Finds the Longest Increasing Subsequence (LIS) of an array and returns 
    the lexicographically smallest sequence of original 0-based indices 
    that achieves the maximum length using quadratic dynamic programming.
    """
    n = len(arr)
    if n == 0:
        return []

    # suf_dp[i] = length of LIS starting at index i
    suf_dp = [1] * n

    for i in range(n - 1, -1, -1):
        for j in range(i + 1, n):
            if arr[j] > arr[i]:
                if suf_dp[j] + 1 > suf_dp[i]:
                    suf_dp[i] = suf_dp[j] + 1

    max_len = max(suf_dp) if suf_dp else 0
    if max_len == 0:
        return []

    result_indices = []
    last_idx = -1
    last_val = float('-inf')

    for req_len in range(max_len, 0, -1):
        # Pick the smallest index i that can complete a sequence of length req_len
        for i in range(last_idx + 1, n):
            if arr[i] > last_val and suf_dp[i] >= req_len:
                result_indices.append(i)
                last_idx = i
                last_val = arr[i]
                break

    return result_indices


# Verification on Defect Example
if __name__ == "__main__":
    example_arr = [10, 20, 1, 30]
    indices = lexicographically_smallest_lis_indices(example_arr)
    subsequence_values = [example_arr[i] for i in indices]

    print(f"Input Array: {example_arr}")
    print(f"Correct Lexicographically Smallest Indices: {indices}")
    print(f"Corresponding LIS Values: {subsequence_values}")