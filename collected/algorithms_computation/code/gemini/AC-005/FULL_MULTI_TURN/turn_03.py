from typing import Union, Dict, List, Any

def lexicographically_smallest_lis_indices(
    arr: List[int], 
    include_summary: bool = False
) -> Union[List[int], Dict[str, Any]]:
    """
    Finds the Longest Increasing Subsequence (LIS) of an array and returns 
    the lexicographically smallest sequence of original 0-based indices.

    :param arr: Input list of integers.
    :param include_summary: If True, returns a dict with 'indices' and 'operation_summary'.
                            If False, returns only the list of indices.
    """
    n = len(arr)
    comparisons = 0
    dp_updates = 0
    reconstruction_steps = 0

    if n == 0:
        result_indices = []
        if include_summary:
            return {
                "indices": result_indices,
                "operation_summary": {
                    "comparisons": comparisons,
                    "dp_updates": dp_updates,
                    "reconstruction_steps": reconstruction_steps
                }
            }
        return result_indices

    # suf_dp[i] = length of LIS starting at index i
    suf_dp = [1] * n

    # Suffix Dynamic Programming (O(n^2))
    for i in range(n - 1, -1, -1):
        for j in range(i + 1, n):
            comparisons += 1
            if arr[j] > arr[i]:
                if suf_dp[j] + 1 > suf_dp[i]:
                    suf_dp[i] = suf_dp[j] + 1
                    dp_updates += 1

    max_len = max(suf_dp) if suf_dp else 0
    result_indices = []
    
    if max_len > 0:
        last_idx = -1
        last_val = float('-inf')

        # Reconstruction Stage
        for req_len in range(max_len, 0, -1):
            for i in range(last_idx + 1, n):
                reconstruction_steps += 1
                comparisons += 1
                if arr[i] > last_val and suf_dp[i] >= req_len:
                    result_indices.append(i)
                    last_idx = i
                    last_val = arr[i]
                    break

    if include_summary:
        return {
            "indices": result_indices,
            "operation_summary": {
                "comparisons": comparisons,
                "dp_updates": dp_updates,
                "reconstruction_steps": reconstruction_steps
            }
        }

    return result_indices


# Example Demonstration
if __name__ == "__main__":
    example_arr = [10, 20, 1, 30]

    # Original requirement (backward-compatible)
    indices_only = lexicographically_smallest_lis_indices(example_arr)
    print("Standard Call Output:", indices_only)

    # Feature enabled
    full_output = lexicographically_smallest_lis_indices(example_arr, include_summary=True)
    print("\nWith Summary Call Output:")
    print("Indices:", full_output["indices"])
    print("Operation Summary:", full_output["operation_summary"])