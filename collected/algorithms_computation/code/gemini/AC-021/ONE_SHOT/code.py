def min_subset_sum_indices(nums: list[int], target: int) -> list[int] | None:
    """
    Finds a subset of indices summing to target with:
    1. Minimum subset size.
    2. Lexicographically smallest list of indices.
    """
    if target == 0:
        return []
    
    # DP array initialized to infinity for element count
    # dp[s] = (count, index_tuple)
    dp = [(float('inf'), None)] * (target + 1)
    dp[0] = (0, ())
    
    for i, num in enumerate(nums):
        if num > target:
            continue
            
        for s in range(target, num - 1, -1):
            prev_count, prev_indices = dp[s - num]
            
            if prev_count != float('inf'):
                candidate_count = prev_count + 1
                candidate_indices = prev_indices + (i,)
                
                curr_count, curr_indices = dp[s]
                
                # Check if candidate is strictly better
                if candidate_count < curr_count:
                    dp[s] = (candidate_count, candidate_indices)
                elif candidate_count == curr_count:
                    if curr_indices is None or candidate_indices < curr_indices:
                        dp[s] = (candidate_count, candidate_indices)

    result_count, result_indices = dp[target]
    return list(result_indices) if result_count != float('inf') else None


# Example usage & validation
if __name__ == "__main__":
    A = [3, 34, 4, 12, 5, 2]
    T = 9
    
    indices = min_subset_sum_indices(A, T)
    print(f"Array: {A}, Target: {T}")
    print(f"Optimal Indices: {indices}")  # Output: [2, 4] -> A[2] + A[4] = 4 + 5 = 9 (size 2)