def subset_sum_min_card_lex_indices(nums, target):
    n = len(nums)
    INF = float('inf')
    # suffix DP: suf[i][s] = min items to reach sum s using items i..n-1
    # We'll use a list of lists, but to save memory we can use 1D and iterate backwards?
    # But we need suf[i+1][...] for reconstruction, so we need all layers.
    # So 2D array of size (n+1) x (target+1)
    suf = [[INF] * (target + 1) for _ in range(n + 1)]
    suf[n][0] = 0
    for i in range(n - 1, -1, -1):
        x = nums[i]
        for s in range(target + 1):
            # skip item i
            best = suf[i + 1][s]
            # take item i
            if s >= x and suf[i + 1][s - x] != INF:
                cand = 1 + suf[i + 1][s - x]
                if cand < best:
                    best = cand
            suf[i][s] = best

    if suf[0][target] == INF:
        return None  # no solution

    # reconstruction
    remaining = target
    count = suf[0][target]
    res = []
    for i in range(n):
        if count == 0:
            break
        x = nums[i]
        if x <= remaining and suf[i + 1][remaining - x] == count - 1:
            res.append(i)
            remaining -= x
            count -= 1
    return res


# Example usage:
if __name__ == "__main__":
    nums = [3, 34, 4, 12, 5, 2]
    target = 9
    print(subset_sum_min_card_lex_indices(nums, target))  # Expected: [0, 4, 5]? Let's check: 3+4+2=9 (indices 0,2,5) count 3; 3+5+? no; 4+5=9 (indices 2,4) count 2 -> minimal count 2, lex smallest indices: [2,4]? Actually [2,4] vs [0,?] 0+? no. 3+? 3+? no. So [2,4] is lex smallest? Check [0,?] 3+?=9 -> need 6, not available. So [2,4] is correct.
    # Let's test:
    nums = [3, 34, 4, 12, 5, 2]
    target = 9
    print(subset_sum_min_card_lex_indices(nums, target))  # Should be [2, 4] (4+5=9)
    nums = [1, 2, 3, 4, 5]
    target = 5
    print(subset_sum_min_card_lex_indices(nums, target))  # [4]? 5 alone count 1, index 4. Also [1,3]? 2+3=5 count 2. So [4] is min count 1, lex smallest? Only [4] has count 1. So [4].
    # Another: target=5, nums=[5,1,2,3,4] -> [0] count 1, lex smallest index 0.
    print(subset_sum_min_card_lex_indices([5,1,2,3,4], 5))  # [0]
    # Test lex: nums=[2,3,1,4], target=5. Possible: 2+3=5 (0,1), 1+4=5 (2,3). Both count 2. Lex smallest: [0,1] vs [2,3] -> [0,1] is smaller. So output [0,1].
    print(subset_sum_min_card_lex_indices([2,3,1,4], 5))  # [0,1]
    # Test where taking smaller index prevents minimal cardinality: nums=[1,2,3,4], target=6. Min count? 2+4=6 (1,3) count 2; 1+2+3=6 (0,1,2) count 3; 3+? no. So min count 2. Lex smallest indices: [1,3] vs [0,?] 0+?=6 -> need 5, not available. So [1,3] is only count 2. Output [1,3].
    print(subset_sum_min_card_lex_indices([1,2,3,4], 6))  # [1,3]